import os
from opensearchpy import OpenSearch, RequestsHttpConnection, exceptions
from django.conf import settings
from datasets import load_dataset # Changed import
import logging

logger = logging.getLogger(__name__)

def get_opensearch_client():
    """Initializes and returns an OpenSearch client."""
    client_args = {
        'hosts': [{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
        'http_conn_class': RequestsHttpConnection,
        'use_ssl': settings.OPENSEARCH_USE_SSL,
        'verify_certs': True,  # Set to False if you have issues with Bonsai's SSL certificate and don't have a CA bundle
        'ssl_show_warn': False,
    }
    if settings.OPENSEARCH_USERNAME and settings.OPENSEARCH_PASSWORD:
        client_args['http_auth'] = (settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD)

    client = OpenSearch(**client_args)
    return client

def create_index_if_not_exists(client, index_name):
    """Creates an OpenSearch index if it doesn't already exist."""
    if not client.indices.exists(index=index_name):
        index_body = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "default": {
                            "type": "standard"
                        },
                        "scientific_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "stop",
                                "snowball"
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "title": {
                        "type": "text", 
                        "analyzer": "scientific_analyzer",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "text": {
                        "type": "text", 
                        "analyzer": "scientific_analyzer",
                        "fields": {
                            "raw": {"type": "keyword"}
                        }
                    },
                    "title_processed": {"type": "text", "analyzer": "scientific_analyzer"},
                    "text_processed": {"type": "text", "analyzer": "scientific_analyzer"}
                }
            }
        }
        try:
            client.indices.create(index=index_name, body=index_body)
            logger.info(f"Index '{index_name}' created successfully.")
        except exceptions.RequestError as e:
            if e.error == 'resource_already_exists_exception':
                logger.info(f"Index '{index_name}' already exists.")
            else:
                logger.error(f"Error creating index '{index_name}': {e}")
                raise
    else:
        logger.info(f"Index '{index_name}' already exists.")

def index_document(client, index_name, doc_id, document_data):
    """Indexes a single document into OpenSearch."""
    try:
        client.index(index=index_name, id=doc_id, body=document_data)
    except Exception as e:
        logger.error(f"Error indexing document {doc_id}: {e}")

def index_beir_scifact_data(client, index_name, max_docs=None):
    """Loads BeIR/scifact data using Hugging Face datasets library and indexes it into OpenSearch."""
    logger.info("Loading BeIR/scifact dataset from Hugging Face...")
    try:
        from .text_preprocessing import preprocessor
        
        # Load the corpus part of the BeIR/scifact dataset
        # The "corpus" configuration directly loads the corpus documents.
        # The load_dataset function for BeIR/scifact with "corpus" config returns a Dataset object.
        hf_dataset = load_dataset("BeIR/scifact", "corpus", split="corpus")
    except Exception as e:
        logger.error(f"Failed to load 'BeIR/scifact' dataset using Hugging Face datasets library: {e}. Ensure 'datasets' library is installed and network is available.")
        return

    create_index_if_not_exists(client, index_name)
    
    logger.info("Starting document indexing for BeIR/scifact...")
    
    num_processed_successfully = 0
    num_read_attempts = 0
    num_skipped_due_to_error = 0

    for doc in hf_dataset: # Iterate directly over the Hugging Face Dataset object
        num_read_attempts += 1
        try:
            if max_docs and num_processed_successfully >= max_docs:
                logger.info(f"Reached max_docs limit of {max_docs}. Stopping indexing.")
                # Decrement num_read_attempts as this doc was fetched but not processed.
                num_read_attempts -=1 
                break
            
            # Access fields from the Hugging Face dataset dictionary
            doc_id = str(doc['_id'])
            title = doc.get('title', '') 
            text_content = doc.get('text', '')

            if not title and not text_content:
                logger.warning(f"Document {doc_id} has no title or text. Skipping.")
                num_skipped_due_to_error +=1
                continue

            # Preprocess text for better indexing
            title_processed = preprocessor.preprocess_for_indexing(title)
            text_processed = preprocessor.preprocess_for_indexing(text_content)

            document_data = {
                "doc_id": doc_id,
                "title": title,
                "text": text_content,
                "title_processed": title_processed,
                "text_processed": text_processed,
            }
            index_document(client, index_name, doc_id, document_data)
            num_processed_successfully += 1
            
            if num_processed_successfully > 0 and num_processed_successfully % 1000 == 0: 
                logger.info(f"Successfully indexed {num_processed_successfully} BeIR/scifact documents...")
                logger.info(f"(Total documents iterated: {num_read_attempts}, Skipped due to errors: {num_skipped_due_to_error})")
        
        except Exception as ex: 
            logger.error(f"Error processing document {num_read_attempts}: {ex}")
            num_skipped_due_to_error += 1
            continue
    
    logger.info(f"Finished indexing. Processed: {num_processed_successfully}, Skipped: {num_skipped_due_to_error}")

def search_documents(client, index_name, query_text, size=10, use_semantic=False):
    """Performs a search query against the OpenSearch index."""
    from .text_preprocessing import preprocessor
    from .semantic_search import semantic_engine
    
    # Preprocess query
    processed_query = preprocessor.preprocess_query(query_text)
    
    if use_semantic and semantic_engine.model:
        # Combine traditional and semantic search
        semantic_results = semantic_engine.semantic_search(query_text, top_k=size)
        
        if semantic_results:
            # Get documents by IDs from semantic search
            doc_ids = [result['doc_id'] for result in semantic_results]
            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "terms": {
                                    "doc_id": doc_ids
                                }
                            },
                            {
                                "multi_match": {
                                    "query": processed_query,
                                    "fields": ["title_processed^2", "text_processed", "title^1.5", "text"]
                                }
                            }
                        ]
                    }
                },
                "size": size
            }
        else:
            # Fallback to traditional search
            search_body = {
                "query": {
                    "multi_match": {
                        "query": processed_query,
                        "fields": ["title_processed^2", "text_processed", "title^1.5", "text"]
                    }
                },
                "size": size
            }
    else:
        # Traditional search with processed query
        search_body = {
            "query": {
                "multi_match": {
                    "query": processed_query,
                    "fields": ["title_processed^2", "text_processed", "title^1.5", "text"],
                    "fuzziness": "AUTO"
                }
            },
            "size": size
        }
    
    try:
        response = client.search(index=index_name, body=search_body)
        hits = [{"id": hit["_id"], **hit["_source"]} for hit in response["hits"]["hits"]]
        return hits
    except exceptions.NotFoundError:
        logger.warning(f"Index '{index_name}' not found during search.")
        return []
    except Exception as e:
        logger.error(f"Error during search: {e}")
        return []

