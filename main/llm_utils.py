import os
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_llm_summary(query: str, documents: list, max_doc_length=500):
    """
    Generates a summary using HuggingFace Inference API based on the query and document snippets.
    """
    api_key = settings.HUGGINGFACE_API_KEY
    model_id = settings.LLM_MODEL_ID
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"

    if not api_key:
        logger.warning("HUGGINGFACE_API_KEY not found. LLM summarization disabled.")
        return "LLM summarization is unavailable (API key missing)."

    if not documents:
        return "No documents provided for summarization."

    headers = {"Authorization": f"Bearer {api_key}"}
    
    context_parts = []
    for i, doc in enumerate(documents[:3]): # Use top 3 documents
        doc_text = doc.get('text', '') # 'text' field now contains the abstract
        doc_title = doc.get('title', 'Document')
        # Ensure snippet is not empty and is a string
        snippet_text = str(doc_text) if doc_text else "No abstract available."
        snippet = snippet_text[:max_doc_length] + "..." if len(snippet_text) > max_doc_length else snippet_text
        context_parts.append(f"Document {i+1} (Title: {doc_title}):\n{snippet}")
    
    context_str = "\n\n".join(context_parts)

    # Refined prompt for better instruction following
    prompt = (
        f"Given the following query and document excerpts, provide a concise answer or summary directly addressing the query. "
        f"Focus on information relevant to the query from the provided texts. "
        f"If the documents do not contain relevant information to answer the query, explicitly state that. "
        f"Do not invent information not present in the excerpts.\n\n"
        f"User Query: \"{query}\"\n\n"
        f"Document Excerpts:\n{context_str}\n\n"
        f"Concise Answer/Summary:"
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200, # Increased slightly for potentially more comprehensive answers
            "temperature": 0.5,    # Lowered for more factual, less creative responses
            "return_full_text": False,
            "wait_for_model": True, # Explicitly wait for model if it's loading
        },
        "options": {
            "use_cache": False # Disable cache for more up-to-date responses during testing
        }
    }

    try:
        logger.info(f"Sending request to LLM: {model_id} with query: {query}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=45) # Increased timeout
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                summary = result[0]["generated_text"].strip()
                logger.info(f"LLM summary received for query '{query}': {summary[:100]}...")
                return summary
            else:
                logger.error(f"Unexpected LLM API response format for query '{query}': {result}")
                return "Could not generate summary due to API response format."
        else:
            error_content = response.text
            logger.error(
                f"LLM API request failed for query '{query}' with status {response.status_code}: {error_content}"
            )
            if response.status_code == 401:
                return "LLM API request failed: Unauthorized (check API key)."
            elif response.status_code == 429:
                 return "LLM service is currently busy (rate limit exceeded). Please try again later."
            elif response.status_code >= 500:
                 return f"LLM service unavailable (server error {response.status_code}). Please try again later."
            return f"Failed to get summary from LLM (HTTP {response.status_code})."

    except requests.exceptions.Timeout:
        logger.error(f"LLM API request timed out for query '{query}'.")
        return "LLM request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API request failed for query '{query}': {e}")
        return "Failed to get summary from LLM due to a connection or API error."
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting LLM summary for query '{query}': {e}", exc_info=True)
        return "An unexpected error occurred while generating the summary."

