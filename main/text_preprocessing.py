import re
import string
import nltk
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
import logging

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {e}")

# Load spaCy model
nlp = None
if SPACY_AVAILABLE:
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
        nlp = None
else:
    logger.warning("spaCy not installed. Install with: pip install spacy && python -m spacy download en_core_web_sm")

class TextPreprocessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()
        
        # Scientific domain specific stopwords
        self.scientific_stopwords = {
            'study', 'research', 'findings', 'results', 'conclusion', 'abstract',
            'introduction', 'method', 'methodology', 'discussion', 'analysis',
            'paper', 'article', 'journal', 'publication', 'author', 'authors'
        }
        
        # Common scientific terms that should not be corrected
        self.scientific_terms = {
            'covid', 'sars', 'dna', 'rna', 'mrna', 'pcr', 'elisa', 'hiv', 'aids',
            'bacteria', 'virus', 'viruses', 'bacterial', 'viral', 'pathogen',
            'protein', 'proteins', 'enzyme', 'enzymes', 'peptide', 'amino',
            'genome', 'genetic', 'gene', 'genes', 'allele', 'chromosome',
            'mutation', 'evolution', 'species', 'organism', 'cell', 'cellular',
            'immune', 'immunity', 'antibody', 'antigen', 'vaccine', 'vaccination'
        }
        
        # Combine stopwords
        self.all_stopwords = self.stop_words.union(self.scientific_stopwords)
    
    def clean_text(self, text):
        """Basic text cleaning"""
        if not text:
            return ""
        
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize_and_normalize(self, text):
        """Tokenize and normalize text"""
        if not text:
            return []
        
        # Clean text first
        text = self.clean_text(text)
        
        # Tokenize
        try:
            tokens = word_tokenize(text)
        except:
            tokens = text.split()
        
        tokens = [token for token in tokens if token.isalpha()]
        tokens = [token for token in tokens if token not in self.all_stopwords]
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def stem_tokens(self, tokens):
        """Apply stemming to tokens"""
        return [self.stemmer.stem(token) for token in tokens]
    
    def lemmatize_tokens(self, tokens):
        """Apply lemmatization to tokens"""
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def spacy_preprocessing(self, text):
        """Advanced preprocessing using spaCy"""
        if not nlp or not text:
            return []
        
        text = self.clean_text(text)
        doc = nlp(text)
        
        tokens = []
        for token in doc:
            # Skip stopwords, punctuation, spaces, and single characters
            if (not token.is_stop and not token.is_punct and 
                not token.is_space and len(token.text) > 1 and
                token.text not in self.scientific_stopwords):
                
                tokens.append(token.lemma_.lower())
        
        return tokens
    
    def preprocess_for_indexing(self, text, method='spacy'):
        """
        Comprehensive preprocessing for document indexing
        method: 'spacy', 'nltk_stem', 'nltk_lemma'
        """
        if method == 'spacy' and nlp:
            return ' '.join(self.spacy_preprocessing(text))
        elif method == 'nltk_stem':
            tokens = self.tokenize_and_normalize(text)
            stemmed = self.stem_tokens(tokens)
            return ' '.join(stemmed)
        elif method == 'nltk_lemma':
            tokens = self.tokenize_and_normalize(text)
            lemmatized = self.lemmatize_tokens(tokens)
            return ' '.join(lemmatized)
        else:
            # Fallback to basic cleaning
            return self.clean_text(text)
    
    def preprocess_query(self, query, method='spacy'):
        """
        Preprocess search query with same method as indexing
        """
        return self.preprocess_for_indexing(query, method)
    
    def extract_entities(self, text):
        """Extract named entities using spaCy"""
        if not nlp or not text:
            return []
        
        doc = nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        return entities

# Global preprocessor instance
preprocessor = TextPreprocessor()
