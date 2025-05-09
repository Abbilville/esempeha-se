from django.shortcuts import render
from django.conf import settings
from .opensearch_utils import get_opensearch_client, search_documents
from .llm_utils import get_llm_summary
import logging

logger = logging.getLogger(__name__)

def show_main(request):
    query = request.GET.get('query', '')
    search_results = []
    llm_summary = ""
    error_message = ""

    if query:
        try:
            client = get_opensearch_client()
            if not client.ping():
                error_message = "Could not connect to Search Engine. Please try again later."
            else:
                search_results = search_documents(client, settings.OPENSEARCH_INDEX_NAME, query)
                if search_results:
                    # Get LLM summary for top N results
                    llm_summary = get_llm_summary(query, search_results[:3]) # Summarize top 3
                elif not error_message: # if no error message yet and no results
                    error_message = "No results found for your query."

        except Exception as e:
            logger.error(f"Error in search view: {e}", exc_info=True)
            error_message = f"An error occurred during the search: {str(e)}"

    context = {
        'query': query,
        'search_results': search_results,
        'llm_summary': llm_summary,
        'error_message': error_message,
        'search_engine_name': "ESEMPEHA Search" 
    }
    return render(request, "index.html", context)
