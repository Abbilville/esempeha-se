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
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "doc_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "text": {"type": "text", "analyzer": "english"}
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

            document_data = {
                "doc_id": doc_id,
                "title": title,
                "text": text_content,
            }
            index_document(client, index_name, doc_id, document_data)
            num_processed_successfully += 1
            
            if num_processed_successfully > 0 and num_processed_successfully % 1000 == 0: 
                logger.info(f"Successfully indexed {num_processed_successfully} BeIR/scifact documents...")
                logger.info(f"(Total documents iterated: {num_read_attempts}, Skipped due to errors: {num_skipped_due_to_error})")
        
        except KeyError as ke:
            logger.warning(f"Document at attempt {num_read_attempts} is missing a key: {ke}. Document: {doc}. Skipping.")
            num_skipped_due_to_error += 1
            continue
        except Exception as ex: 
            logger.error(f"Unexpected error processing document at attempt {num_read_attempts}: {ex}. Document: {doc}. Skipping.")
            num_skipped_due_to_error += 1
            continue
    
    logger.info(f"Finished BeIR/scifact indexing. "
                f"Successfully processed: {num_processed_successfully} documents. "
                f"Skipped due to errors: {num_skipped_due_to_error} documents. "
                f"Total documents iterated from dataset: {num_read_attempts}.")

def search_documents(client, index_name, query_text, size=10):
    """Performs a search query against the OpenSearch index."""
    search_body = {
        "query": {
            "multi_match": {
                "query": query_text,
                "fields": ["title^2", "text"] # Query matches against 'title' and 'text' (abstract)
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

