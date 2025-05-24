import os
import pickle
from collections import Counter
try:
    from symspellpy import SymSpell, Verbosity
except ImportError:
    SymSpell = None
    Verbosity = None
import textdistance
from django.conf import settings
from .opensearch_utils import get_opensearch_client
import logging

logger = logging.getLogger(__name__)

class QueryCorrector:
    def __init__(self):
        self.sym_spell = None
        if SymSpell:
            self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        self.dictionary_path = os.path.join(settings.BASE_DIR, 'data', 'frequency_dictionary_en_82_765.txt')
        self.custom_dict_path = os.path.join(settings.BASE_DIR, 'data', 'custom_terms.pkl')
        self.term_frequencies = {}
        self.load_dictionaries()
    
    def load_dictionaries(self):
        """Load spelling correction dictionaries"""
        if not self.sym_spell:
            logger.warning("SymSpell not available, spell checking disabled")
            return
            
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        if os.path.exists(self.dictionary_path):
            self.sym_spell.load_dictionary(self.dictionary_path, term_index=0, count_index=1)
            logger.info(f"Loaded standard dictionary from {self.dictionary_path}")
        else:
            logger.info("Standard dictionary not found, will build from index")
        
        self._load_or_build_custom_terms()
    
    def _load_or_build_custom_terms(self):
        """Load custom terms or build them from the index"""
        if os.path.exists(self.custom_dict_path):
            try:
                with open(self.custom_dict_path, 'rb') as f:
                    self.term_frequencies = pickle.load(f)
                    
                if self.sym_spell:
                    for term, frequency in self.term_frequencies.items():
                        self.sym_spell.create_dictionary_entry(term, frequency)
                
                logger.info(f"Loaded {len(self.term_frequencies)} custom terms from cache")
                return
            except Exception as e:
                logger.error(f"Error loading custom terms: {e}")
        
        self.build_custom_dictionary_from_index()
    
    def build_custom_dictionary_from_index(self):
        """Build custom dictionary from indexed documents"""
        try:
            from .text_preprocessing import preprocessor
            client = get_opensearch_client()
            
            # Search for all documents
            search_body = {
                "query": {"match_all": {}},
                "size": 1000,
                "_source": ["title", "text"]
            }
            
            response = client.search(index=settings.OPENSEARCH_INDEX_NAME, body=search_body)
            
            term_frequencies = Counter()
            
            for hit in response["hits"]["hits"]:
                title = hit["_source"].get("title", "")
                text = hit["_source"].get("text", "")
                
                # Process title and text
                for content in [title, text]:
                    if content:
                        words = content.lower().split()
                        clean_words = []
                        for word in words:
                            # Remove punctuation and keep only alphabetic words
                            clean_word = ''.join(c for c in word if c.isalpha())
                            if len(clean_word) > 2:
                                clean_words.append(clean_word)
                        
                        term_frequencies.update(clean_words)
            
            self.term_frequencies = {
                term: freq for term, freq in term_frequencies.items()
                if freq >= 2 and len(term) > 2 and term.isalpha()
            }
            
            with open(self.custom_dict_path, 'wb') as f:
                pickle.dump(self.term_frequencies, f)
            
            if self.sym_spell:
                for term, frequency in self.term_frequencies.items():
                    self.sym_spell.create_dictionary_entry(term, frequency)
            
            logger.info(f"Built custom dictionary with {len(self.term_frequencies)} terms")
            
        except Exception as e:
            logger.error(f"Error building custom dictionary: {e}")
            self._create_fallback_terms()
    
    def _create_fallback_terms(self):
        """Create fallback terms when index is not available"""
        fallback_terms = {
            "virus": 100, "bacteria": 100, "protein": 100, "cell": 100, "gene": 100,
            "dna": 100, "rna": 100, "immune": 100, "vaccine": 100, "infection": 100,
            "research": 100, "study": 100, "analysis": 100, "experiment": 100,
            "cancer": 100, "tumor": 100, "therapy": 100, "treatment": 100,
            "covid": 100, "coronavirus": 100, "pandemic": 100, "disease": 100
        }
        
        self.term_frequencies = fallback_terms
        
        if self.sym_spell:
            for term, frequency in fallback_terms.items():
                self.sym_spell.create_dictionary_entry(term, frequency)
        
        logger.info("Created fallback dictionary with basic scientific terms")
    
    def suggest_corrections(self, query, max_suggestions=3):
        """Get spelling correction suggestions for query"""
        suggestions = []
        
        # Don't suggest corrections for very short queries
        if len(query.strip()) < 3:
            return suggestions
        
        if self.sym_spell:
            suggestions.extend(self._symspell_corrections(query, max_suggestions))
        
        if len(suggestions) < max_suggestions:
            suggestions.extend(self._textdistance_corrections(query, max_suggestions - len(suggestions)))
        
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion.lower() not in seen and suggestion.lower() != query.lower():
                seen.add(suggestion.lower())
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:max_suggestions]
    
    def _symspell_corrections(self, query, max_suggestions):
        """Get corrections using SymSpell"""
        suggestions = []
        
        try:
            # Get suggestions for the entire query
            symspell_suggestions = self.sym_spell.lookup_compound(
                query, 
                max_edit_distance=2,
                transfer_casing=True
            )
            
            for suggestion in symspell_suggestions[:max_suggestions]:
                if suggestion.term != query and suggestion.distance > 0:
                    suggestions.append(suggestion.term)
                    logger.info(f"SymSpell correction: '{query}' -> '{suggestion.term}' (distance: {suggestion.distance})")
        
        except Exception as e:
            logger.error(f"Error in SymSpell corrections: {e}")
        
        return suggestions
    
    def _textdistance_corrections(self, query, max_suggestions):
        """Get corrections using textdistance and custom terms"""
        suggestions = []
        
        if not self.term_frequencies:
            return suggestions
        
        try:
            query_words = query.lower().split()
            
            for query_word in query_words:
                if len(query_word) < 3:
                    continue
                
                # Find similar terms
                similar_terms = []
                for term in self.term_frequencies.keys():
                    if len(term) < 3:
                        continue
                    
                    # Calculate similarity
                    similarity = textdistance.jaro_winkler(query_word, term)
                    if 0.7 <= similarity < 1.0:
                        similar_terms.append((term, similarity, self.term_frequencies[term]))
                
                # Sort by similarity and frequency
                similar_terms.sort(key=lambda x: (x[1], x[2]), reverse=True)
                
                # Create corrected query
                for term, similarity, freq in similar_terms[:2]:  # Top 2 for each word
                    corrected_query = query.replace(query_word, term)
                    if corrected_query not in suggestions:
                        suggestions.append(corrected_query)
                        logger.info(f"TextDistance correction: '{query_word}' -> '{term}' (similarity: {similarity:.3f})")
        
        except Exception as e:
            logger.error(f"Error in textdistance corrections: {e}")
        
        return suggestions[:max_suggestions]
    
    def get_query_suggestions(self, partial_query, max_suggestions=5):
        """Get auto-completion suggestions for partial query"""
        suggestions = set()
        
        if len(partial_query) < 2:
            return []
        
        partial_lower = partial_query.lower()
        
        # Use custom terms for suggestions
        if self.term_frequencies:
            for term, freq in self.term_frequencies.items():
                if term.lower().startswith(partial_lower) and len(term) > len(partial_query):
                    suggestions.add(term)
                
                elif partial_lower in term.lower() and len(term) > len(partial_query):
                    suggestions.add(term)
        
        # Sort by length and frequency, prioritizing exact prefix matches
        suggestions_list = list(suggestions)
        suggestions_list.sort(key=lambda x: (
            not x.lower().startswith(partial_lower),  # Prefix matches first
            len(x),
            -self.term_frequencies.get(x, 0)  # Higher frequency first
        ))
        
        logger.info(f"Generated {len(suggestions_list)} suggestions for '{partial_query}': {suggestions_list[:3]}")
        return suggestions_list[:max_suggestions]

# Global corrector instance
query_corrector = QueryCorrector()
