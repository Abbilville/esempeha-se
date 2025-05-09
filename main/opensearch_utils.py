import os
from opensearchpy import OpenSearch, RequestsHttpConnection, exceptions
from django.conf import settings
import ir_datasets
import logging

logger = logging.getLogger(__name__)

def get_opensearch_client():
    """Initializes and returns an OpenSearch client."""
    client = OpenSearch(
        hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
        http_conn_class=RequestsHttpConnection,
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )
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
                    "text": {"type": "text", "analyzer": "english"},
                    "url": {"type": "keyword"}
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

def index_nfcorpus_data(client, index_name, max_docs=None):
    """Loads nfcorpus data and indexes it into OpenSearch."""
    logger.info("Loading nfcorpus dataset...")
    try:
        dataset = ir_datasets.load("nfcorpus")
    except Exception as e:
        logger.error(f"Failed to load ir_datasets 'nfcorpus': {e}. Ensure it's downloaded or network is available.")
        return

    create_index_if_not_exists(client, index_name)
    
    logger.info("Starting document indexing...")
    
    num_processed_successfully = 0
    num_read_attempts = 0
    num_skipped_due_to_error = 0

    doc_iterator = dataset.docs_iter()

    while True:
        doc = None
        try:
            num_read_attempts += 1 # Increment for each attempt to call next()
            doc = next(doc_iterator)
        except StopIteration:
            logger.info("Finished iterating through all documents in the dataset.")
            num_read_attempts -=1 # Correct count as the last attempt yielded no document
            break 
        except UnicodeDecodeError as ude:
            logger.warning(f"UnicodeDecodeError at document read attempt {num_read_attempts}: {ude}. Skipping this document.")
            num_skipped_due_to_error += 1
            continue 
        except Exception as ex: 
            logger.error(f"Unexpected error fetching document at read attempt {num_read_attempts}: {ex}. Skipping this document.")
            num_skipped_due_to_error += 1
            continue

        # If max_docs is set and we have processed enough documents
        if max_docs and num_processed_successfully >= max_docs:
            logger.info(f"Reached max_docs limit of {max_docs}. Stopping indexing.")
            num_read_attempts -=1
            break
        
        # NFCorpusDoc has doc_id, url, title, abstract
        title = doc.title
        content = doc.abstract # Use abstract as the main text content

        document_data = {
            "doc_id": doc.doc_id,
            "title": title,
            "text": content,
            "url": doc.url
        }
        index_document(client, index_name, doc.doc_id, document_data)
        num_processed_successfully += 1
        
        if num_processed_successfully > 0 and num_processed_successfully % 1000 == 0: 
            logger.info(f"Successfully indexed {num_processed_successfully} documents...")
            logger.info(f"(Total read attempts: {num_read_attempts}, Skipped due to errors: {num_skipped_due_to_error})")
    
    logger.info(f"Finished indexing. "
                f"Successfully processed: {num_processed_successfully} documents. "
                f"Skipped due to errors: {num_skipped_due_to_error} documents. "
                f"Total documents read from iterator: {num_read_attempts}.")

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

