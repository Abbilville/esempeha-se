# ESEMPEHA Search Engine

A comprehensive information retrieval system built with Django and OpenSearch, featuring advanced text preprocessing, semantic search capabilities, and LLM-powered summarization for scientific document retrieval.

## System Architecture

### Core Components

1. **OpenSearch Integration**: Document indexing and retrieval with advanced analyzers
2. **Text Preprocessing**: Multi-layered preprocessing with NLTK/spaCy support
3. **Semantic Search**: Vector-based similarity search using SentenceTransformers
4. **Query Enhancement**: Auto-correction and auto-completion features
5. **LLM Integration**: AI-powered summarization using HuggingFace models
6. **Caching System**: Response caching for improved performance

### Technology Stack

- **Backend**: Django 5.2.1, Python 3.8+
- **Search Engine**: OpenSearch
- **ML Libraries**:
  - SentenceTransformers (semantic search)
  - NLTK/spaCy (text preprocessing)
  - SymSpell (spell correction)
- **LLM**: Mistral-7B-Instruct via HuggingFace API
- **Frontend**: HTML, CSS (TailwindCSS), JavaScript
- **Dataset**: BeIR/SciFact corpus

## Features

### Search Capabilities

- **Traditional Search**: BM25-based retrieval with preprocessing
- **Semantic Search**: Vector similarity search for conceptual matching
- **Hybrid Search**: Combination of traditional and semantic approaches
- **Query Preprocessing**: Stemming, lemmatization, stopword removal
- **Fuzzy Matching**: Auto-correction for typos and spelling errors

### User Experience

- **Auto-completion**: Real-time query suggestions
- **Spell Correction**: "Did you mean?" suggestions
- **AI Summaries**: LLM-generated summaries for search results
- **Responsive Design**: Mobile-friendly interface

### Performance Optimization

- **Caching**: LLM response caching for faster subsequent searches
- **Preprocessing**: Optimized text processing pipeline
- **Indexing**: Scientific domain-specific analyzers

## Installation

### Prerequisites

- Python 3.8+
- OpenSearch 2.0+
- Git

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd esempeha
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install additional NLP models**

   ```bash
   python -m spacy download en_core_web_sm
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

5. **Setup environment variables**
   Create a `.env` file in the project root:

   ```env
   OPENSEARCH_HOST=localhost
   OPENSEARCH_PORT=9200
   OPENSEARCH_USERNAME=your_username  # Optional
   OPENSEARCH_PASSWORD=your_password  # Optional
   OPENSEARCH_USE_SSL=False
   HUGGINGFACE_API_KEY=your_hf_api_key
   ```

6. **Start OpenSearch**
   Follow OpenSearch installation guide for your platform

7. **Run Django migrations**

   ```bash
   python manage.py migrate
   ```

8. **Index the dataset**

   ```bash
   python manage.py index_data --max-docs 1000  # Optional limit
   ```

9. **Build semantic capabilities**

   ```bash
   python manage.py build_semantic_index
   ```

10. **Start the development server**
    ```bash
    python manage.py runserver
    ```

## Usage Examples

### Basic Search

Visit `http://localhost:8000` and enter search queries like:

- "virus infection"
- "protein structure"
- "immune response"

### API Endpoints

- **Search**: `GET /?query=your_query&semantic=true`
- **Autocomplete**: `GET /api/autocomplete/?q=partial_query`
- **Corrections**: `GET /api/corrections/?q=misspelled_query`

### Management Commands

#### Index Data

```bash
# Index all documents
python manage.py index_data

# Index limited documents
python manage.py index_data --max-docs 500
```

#### Build Semantic Index

```bash
# Build both embeddings and dictionary
python manage.py build_semantic_index

# Skip embeddings
python manage.py build_semantic_index --skip-embeddings

# Skip dictionary
python manage.py build_semantic_index --skip-dictionary
```

## Evaluation Framework

The system includes a comprehensive IR evaluation framework (`ir_eval.py`):

### Running Evaluations

1. **Comprehensive evaluation**

   ```bash
   python ir_eval.py --run-all
   ```

2. **Single query evaluation**

   ```bash
   python ir_eval.py --query "virus" --method semantic
   ```

3. **Create test queries**
   ```bash
   python ir_eval.py --create-test-queries
   ```

### Evaluation Metrics

- **Precision & Recall**: Standard IR metrics
- **F1 Score**: Harmonic mean of precision and recall
- **Average Precision (AP)**: Area under P-R curve
- **NDCG@k**: Normalized Discounted Cumulative Gain
- **Method Comparison**: Traditional vs Semantic search

## Configuration

### Text Preprocessing

Modify `settings.py`:

```python
TEXT_PREPROCESSING_METHOD = 'spacy'  # Options: 'spacy', 'nltk_stem', 'nltk_lemma'
```

### Cache Settings

```python
LLM_CACHE_TIMEOUT = 3600  # 1 hour
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 3600,
    }
}
```

### OpenSearch Index Settings

The system uses a custom analyzer with:

- Standard tokenization
- Lowercase filtering
- Stop word removal
- Snowball stemming

## Dataset Information

**Source**: BeIR/SciFact corpus from HuggingFace

- **Domain**: Scientific facts and claims
- **Size**: ~5,000 documents
- **Format**: Title and abstract pairs
- **Language**: English

**Citation**:

```
@article{scifact,
  title={SciFact: A Dataset for Scientific Claim Verification},
  author={Wadden, David and Lin, Shanchuan and Lo, Kyle and Wang, Lucy Lu and Groningen, Madeleine van and others},
  journal={EMNLP},
  year={2020}
}
```

## Performance Considerations

### Optimization Tips

1. **First Search Latency**: Initial LLM requests may be slow due to model loading
2. **Caching**: Subsequent identical queries are served from cache
3. **Semantic Search**: Requires pre-built embeddings (run `build_semantic_index`)
4. **Index Size**: Consider limiting documents for development

### Scaling Recommendations

- Use Redis for production caching
- Deploy OpenSearch cluster for high availability
- Consider Elasticsearch as alternative
- Implement query result pagination

## Troubleshooting

### Common Issues

1. **OpenSearch Connection Error**

   - Verify OpenSearch is running
   - Check connection settings in `.env`

2. **NLTK/spaCy Errors**

   - Download required models as shown in installation

3. **HuggingFace API Errors**

   - Verify API key in `.env`
   - Check rate limits for free tier

4. **Import Errors**

   - Install missing dependencies: `pip install -r requirements.txt`

5. **Semantic Search Not Working**
   - Run `python manage.py build_semantic_index`
   - Ensure SentenceTransformers is installed

## Development

### Project Structure

```
esempeha/
├── main/                    # Main Django app
│   ├── management/commands/ # Management commands
│   ├── templates/          # HTML templates
│   ├── opensearch_utils.py # OpenSearch integration
│   ├── text_preprocessing.py # Text processing
│   ├── semantic_search.py  # Vector search
│   ├── query_correction.py # Spell checking
│   └── llm_utils.py       # LLM integration
├── esempeha/              # Django project settings
├── ir_eval.py            # Evaluation framework
├── requirements.txt      # Dependencies
└── README.md            # This file
```

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

This project is developed for academic purposes as part of Information Retrieval coursework.

## Contact

For questions or issues, please create an issue in the repository or contact the development team.
