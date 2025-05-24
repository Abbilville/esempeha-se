# Temu-Balik Informasi Project: ESEMPEHA Search Engine

An advanced information retrieval system specialized for scientific facts, built with Django and OpenSearch.

## Team: ESEMPEHA
### Members:
1. Abbilhaidar Farras Zulfikar (2206026012)
2. Ravie Hasan Abud (2206031864)
3. Steven Faustin Orginata (2206030855)

### Deployment
Link Deployment: [https://esempeha-search.com](https://tart-honor-abbilville-e18670b6.koyeb.app/)

---

## Project Overview

ESEMPEHA Search Engine is a comprehensive information retrieval system designed for searching scientific facts. It uses the BeIR/scifact dataset to provide accurate and relevant search results for scientific queries.

### Key Features

1. **Traditional and Semantic Search**
   - Toggle between keyword-based and semantic (meaning-based) search
   - Semantic search powered by Sentence Transformers for finding conceptually similar documents

2. **Query Correction and Suggestions**
   - Automatic spelling correction for misspelled queries
   - "Did you mean" suggestions when few or no results are found
   - Real-time query autocompletion as users type

3. **AI-Generated Summaries**
   - Concise summaries of search results using Mistral-7B LLM
   - Summarizes content across multiple relevant documents

4. **Scientific Domain Optimization**
   - Custom analyzer optimized for scientific terminology
   - Domain-specific preprocessing and tokenization

5. **Responsive UI with Modern Features**
   - Clean interface built with Tailwind CSS
   - Real-time autocomplete suggestions
   - Expandable search results

6. **Comprehensive Evaluation Framework**
   - Built-in metrics like precision, recall, F1, and NDCG
   - Comparison tools for different search approaches

## System Architecture

The system consists of several key components:

1. **Frontend (Django + Tailwind CSS)**
   - Web interface for query input and result display
   - JavaScript for real-time features like autocompletion

2. **Backend (Django + OpenSearch)**
   - Search API endpoints
   - Document indexing and retrieval logic
   - Query processing and correction

3. **Semantic Engine**
   - Sentence Transformers for document and query embeddings
   - Vector similarity calculations

4. **Query Correction System**
   - Custom dictionary built from indexed scientific terms
   - Spell checking and suggestion algorithms

5. **LLM Integration**
   - Connection to Hugging Face's API for AI-generated summaries
   - Caching mechanism to optimize performance

---

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Docker (for OpenSearch)

### 1. Clone the Repository

```bash
git clone https://github.com/Abbilville/esempeha-se TK
cd TK
```

### 2. Set Up Environment

#### Using Conda (Recommended)
```bash
# Create a conda environment
conda create -n myenv python=3.10

# Activate the environment
conda activate myenv

# Install required packages
pip install -r requirements.txt
```

#### Using venv
```bash
# Create a virtual environment
python -m venv env

# Activate on Windows
env\Scripts\activate
# OR on macOS/Linux
source env/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Set Up OpenSearch

```bash
# Pull the OpenSearch Docker image
docker pull opensearchproject/opensearch:latest

# Run OpenSearch container
docker run -d -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" -e "plugins.security.disabled=true" -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=Esempeha123" opensearchproject/opensearch:latest
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
```

### 5. Index Data and Build Semantic Features

```bash
# Index data from BeIR/scifact dataset
python manage.py index_data

# Build semantic search capabilities
python manage.py build_semantic_index
```

### 6. Run the Application

```bash
python manage.py runserver
```

This will start the server at http://127.0.0.1:8000/

---

## Using the Search Engine

1. **Basic Search**: Enter a query in the search box and click "Search"
2. **Semantic Search**: Enable the "Use Semantic Search" checkbox for concept-based searching
3. **Autocomplete**: Start typing in the search box to see suggestions
4. **Result Navigation**: Use "See more" links to expand search results
5. **Query Correction**: Click on suggested corrections when available

## Evaluation

The project includes a comprehensive evaluation framework in `ir_eval.py`:

```bash
# Run complete evaluation
python ir_eval.py --run-all

# Evaluate a specific query
python ir_eval.py --query "virus" --method traditional

# Create test queries file
python ir_eval.py --create-test-queries
```

## Project Structure

```
TK/
├── esempeha/            # Main project directory
│   ├── __init__.py      # init
│   ├── asgi.py          # ASGI configuration
│   ├── settings.py      # Project settings
│   ├── urls.py          # URL configuration
│   └── wsgi.py          # WSGI configuration
├── main/                # App directory
│   ├── management/      # Custom management commands
│   ├── models.py        # Database models
│   ├── views.py         # View functions
│   ├── urls.py          # URL patterns for this app
│   ├── opensearch_utils.py # OpenSearch interface
│   ├── semantic_search.py  # Semantic search functionality
│   ├── llm_utils.py     # LLM integration
│   ├── query_correction.py # Query correction utilities
│   ├── text_preprocessing.py # Text preprocessing utilities
│   └── templates/       # HTML templates
├── static/              # Static files (CSS, JS, images)
├── templates/           # Base HTML templates
├── ir_eval.py           # Evaluation framework
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Troubleshooting

### OpenSearch Connection Issues

If you can't connect to OpenSearch:

```bash
# Check if the container is running
docker ps

# Restart the container if needed
docker restart <container_id>
```

### LLM Summary Generation Errors

If AI summaries aren't working:

1. Verify your Hugging Face API key in the `.env` file
2. Check network connectivity to Hugging Face API
3. Try a different model by changing `LLM_MODEL_ID` in settings.py

### Package Installation Problems

If you're having trouble with package installations:

```bash
# Update pip
pip install --upgrade pip

# Install specific problematic packages manually
pip install sentence-transformers
```

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Hugging Face Documentation](https://huggingface.co/docs)

## Contact

If you have any questions or issues, please contact:
- Abbilhaidar Farras Zulfikar: abbilhaidar.farras@ui.ac.id
- Ravie Hasan Abud: ravie.hasan@ui.ac.id
- Steven Faustin Orginata: steven.faustin@ui.ac.id
