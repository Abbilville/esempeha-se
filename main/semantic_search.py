import numpy as np
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None
import pickle
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.embeddings_cache = {}
        self.embeddings_file = os.path.join(settings.BASE_DIR, 'data', 'document_embeddings.pkl')
        self.load_model()
    
    def load_model(self):
        """Load sentence transformer model"""
        if not SentenceTransformer:
            logger.warning("SentenceTransformers not available")
            return
            
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded semantic model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load semantic model: {e}")
            self.model = None
    
    def encode_texts(self, texts):
        """Encode texts to embeddings"""
        if not self.model:
            return None
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            return None
    
    def build_document_embeddings(self):
        """Build embeddings for all documents in the index"""
        if not self.model:
            logger.warning("Semantic model not available for embedding generation")
            return False
        
        try:
            from .opensearch_utils import get_opensearch_client
            
            client = get_opensearch_client()
            
            # Get all documents
            search_body = {
                "query": {"match_all": {}},
                "size": 1000,
                "_source": ["doc_id", "title", "text"]
            }
            
            response = client.search(index=settings.OPENSEARCH_INDEX_NAME, body=search_body)
            
            documents = []
            doc_ids = []
            
            for hit in response["hits"]["hits"]:
                doc_id = hit["_source"]["doc_id"]
                title = hit["_source"].get("title", "")
                text = hit["_source"].get("text", "")
                
                # Combine title and text
                combined_text = f"{title} {text}".strip()
                
                if combined_text:
                    documents.append(combined_text)
                    doc_ids.append(doc_id)
            
            if documents:
                logger.info(f"Generating embeddings for {len(documents)} documents...")
                embeddings = self.encode_texts(documents)
                
                if embeddings is not None:
                    # Save embeddings
                    embedding_data = {
                        'embeddings': embeddings,
                        'doc_ids': doc_ids,
                        'model_name': self.model_name
                    }
                    
                    os.makedirs(os.path.dirname(self.embeddings_file), exist_ok=True)
                    with open(self.embeddings_file, 'wb') as f:
                        pickle.dump(embedding_data, f)
                    
                    logger.info(f"Saved embeddings for {len(documents)} documents")
                    return True
            
        except Exception as e:
            logger.error(f"Error building document embeddings: {e}")
            return False
    
    def load_document_embeddings(self):
        """Load pre-computed document embeddings"""
        if os.path.exists(self.embeddings_file):
            try:
                with open(self.embeddings_file, 'rb') as f:
                    data = pickle.load(f)
                
                if data.get('model_name') == self.model_name:
                    self.embeddings_cache = data
                    logger.info(f"Loaded embeddings for {len(data['doc_ids'])} documents")
                    return True
                else:
                    logger.warning("Embeddings model mismatch, need to rebuild")
            except Exception as e:
                logger.error(f"Error loading embeddings: {e}")
        
        return False
    
    def semantic_search(self, query, top_k=10):
        """Perform semantic search using embeddings"""
        if not self.model or not cosine_similarity:
            return []
        
        # Load embeddings if not cached
        if not self.embeddings_cache and not self.load_document_embeddings():
            logger.warning("No document embeddings available")
            return []
        
        try:
            # Encode query
            query_embedding = self.encode_texts([query])
            if query_embedding is None:
                return []
            
            # Calculate similarities
            doc_embeddings = self.embeddings_cache['embeddings']
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
            
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:
                    results.append({
                        'doc_id': self.embeddings_cache['doc_ids'][idx],
                        'similarity': float(similarities[idx])
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def expand_query(self, query, num_expansions=3):
        """Expand query with semantically similar terms"""
        expanded_queries = [query]
        
        # Add some domain-specific expansions
        expansions = {
            'virus': ['viral', 'pathogen', 'microorganism'],
            'bacteria': ['bacterial', 'microbe', 'prokaryote'],
            'protein': ['enzyme', 'peptide', 'amino acid'],
            'cell': ['cellular', 'cytoplasm', 'membrane'],
            'gene': ['genetic', 'dna', 'allele'],
            'disease': ['illness', 'disorder', 'condition'],
            'treatment': ['therapy', 'cure', 'medication'],
            'immune': ['immunity', 'antibody', 'defense']
        }
        
        query_words = query.lower().split()
        for word in query_words:
            if word in expansions:
                for expansion in expansions[word][:num_expansions]:
                    expanded_query = query.replace(word, expansion)
                    if expanded_query not in expanded_queries:
                        expanded_queries.append(expanded_query)
        
        return expanded_queries[:num_expansions + 1]

# Global semantic search engine
semantic_engine = SemanticSearchEngine()
