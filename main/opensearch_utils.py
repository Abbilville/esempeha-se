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
        use_ssl=False, # Set to True if your OpenSearch uses SSL
        verify_certs=False, # Set to True in production with valid certs
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
                    "url": {"type": "keyword"} # NFCorpus docs have a URL
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
        dataset = ir_datasets.load("nfcorpus") # Consider nfcorpus/train for a smaller set initially
    except Exception as e:
        logger.error(f"Failed to load ir_datasets 'nfcorpus': {e}. Ensure it's downloaded or network is available.")
        return

    create_index_if_not_exists(client, index_name)
    
    logger.info("Starting document indexing...")
    
    raw_doc_attempt_count = 0
    processed_docs_count = 0

    # Wrapper for the iterator to safely handle decoding errors
    def safe_doc_iterator(base_iterator):
        nonlocal raw_doc_attempt_count
        while True:
            try:
                raw_doc_attempt_count += 1
                yield next(base_iterator)
            except UnicodeDecodeError as ude:
                logger.warning(f"UnicodeDecodeError at document attempt {raw_doc_attempt_count}: {ude}. Skipping this document.")
                # Continue to the next document
            except StopIteration:
                break # End of dataset
            except Exception as ex: # Catch other potential errors from iterator
                logger.error(f"Unexpected error fetching document at attempt {raw_doc_attempt_count}: {ex}. Skipping this document.")
                continue # Changed from break to continue

    for doc in safe_doc_iterator(dataset.docs_iter()):
        if max_docs and processed_docs_count >= max_docs:
            logger.info(f"Reached max_docs limit of {max_docs}. Stopping indexing.")
            break
        
        # NFCorpusDoc has doc_id, url, title, abstract
        title = doc.title
        content = doc.abstract # Use abstract as the main text content

        document_data = {
            "doc_id": doc.doc_id,
            "title": title,
            "text": content, # Store abstract in the 'text' field for consistency with mapping
            "url": doc.url
        }
        index_document(client, index_name, doc.doc_id, document_data)
        processed_docs_count += 1
        if processed_docs_count % 1000 == 0: # Log based on successfully processed docs
            logger.info(f"Indexed {processed_docs_count} documents...")
    
    logger.info(f"Finished indexing. Successfully processed {processed_docs_count} documents out of {raw_doc_attempt_count -1 if raw_doc_attempt_count > 0 else 0} attempts.")

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

