from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from .opensearch_utils import get_opensearch_client, search_documents
from .llm_utils import get_llm_summary
from .query_correction import query_corrector
from .semantic_search import semantic_engine
import logging

logger = logging.getLogger(__name__)

def show_main(request):
    query = request.GET.get('query', '').strip()
    use_semantic = request.GET.get('semantic', 'false').lower() == 'true'
    search_results = []
    llm_summary = ""
    error_message = ""
    query_suggestions = []

    if query:
        try:
            client = get_opensearch_client()
            if not client.ping():
                error_message = "Could not connect to Search Engine. Please try again later."
            else:
                # Perform search with original query first
                search_results = search_documents(
                    client, 
                    settings.OPENSEARCH_INDEX_NAME, 
                    query, 
                    use_semantic=use_semantic
                )
                
                # Get query corrections - always get them for potential display
                corrections = query_corrector.suggest_corrections(query)
                
                # Show corrections if:
                # 1. We have corrections that are different from the original query
                # 2. AND either we have no results OR very few results
                if corrections and any(correction.lower() != query.lower() for correction in corrections):
                    if len(search_results) <= 2:  # Show suggestions when few or no results
                        query_suggestions = corrections
                        logger.info(f"Showing query corrections for '{query}' (found {len(search_results)} results): {corrections}")
                        
                        # If no results with original query, try the first correction
                        if len(search_results) == 0 and corrections:
                            logger.info(f"No results for '{query}', trying correction '{corrections[0]}'")
                            corrected_results = search_documents(
                                client, 
                                settings.OPENSEARCH_INDEX_NAME, 
                                corrections[0], 
                                use_semantic=use_semantic
                            )
                            if corrected_results:
                                search_results = corrected_results
                                logger.info(f"Found {len(corrected_results)} results with correction")
                
                if search_results:
                    # Get LLM summary for top results
                    llm_summary = get_llm_summary(query, search_results[:3])
                elif not error_message:
                    error_message = "No results found for your query."

        except Exception as e:
            logger.error(f"Error in search view: {e}", exc_info=True)
            error_message = f"An error occurred during the search: {str(e)}"

    context = {
        'query': query,
        'search_results': search_results,
        'llm_summary': llm_summary,
        'error_message': error_message,
        'query_suggestions': query_suggestions,
        'use_semantic': use_semantic,
        'search_engine_name': "ESEMPEHA Search" 
    }
    return render(request, "index.html", context)

def autocomplete_suggestions(request):
    """API endpoint for query autocompletion"""
    partial_query = request.GET.get('q', '').strip()
    
    logger.info(f"Autocomplete request for: '{partial_query}'")
    
    if len(partial_query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        suggestions = query_corrector.get_query_suggestions(partial_query)
        logger.info(f"Returning {len(suggestions)} suggestions: {suggestions}")
        return JsonResponse({'suggestions': suggestions})
    except Exception as e:
        logger.error(f"Error getting autocomplete suggestions: {e}")
        return JsonResponse({'suggestions': [], 'error': str(e)})

def query_corrections_api(request):
    """API endpoint for query spell corrections"""
    query = request.GET.get('q', '').strip()
    
    logger.info(f"Query corrections request for: '{query}'")
    
    if len(query) < 2:
        return JsonResponse({'corrections': []})
    
    try:
        corrections = query_corrector.suggest_corrections(query)
        logger.info(f"Returning {len(corrections)} corrections: {corrections}")
        return JsonResponse({'corrections': corrections})
    except Exception as e:
        logger.error(f"Error getting query corrections: {e}")
        return JsonResponse({'corrections': [], 'error': str(e)})
