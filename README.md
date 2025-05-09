# Esempeha Search - Science Facts Information Retrieval System

## Team: ESEMPEHA

### Member:

1. Abbilhaidar Farras Zulfikar (2206026012)
2. Ravie Hasan Abud (2206031864)
3. Steven Faustin Orginata (2206030855)

---

## System Overview

Esempeha Search is a Django-based web application that functions as a specialized search engine for science facts information. It utilizes OpenSearch for efficient indexing and searching of documents and integrates a Large Language Model (LLM) via the HuggingFace Inference API to provide AI-generated summaries for search queries.

### Architecture

1.  **Frontend**: Django templates with Tailwind CSS for user interface.
2.  **Backend**: Django framework handling HTTP requests, business logic.
3.  **Search**: OpenSearch is used as the search engine backend. Documents are indexed and queried using the `opensearch-py` library.
4.  **LLM Integration**: A HuggingFace Inference API (e.g., Meta-Llama-3-8B-Instruct) is used to generate summaries from the top search results.
5.  **Dataset**: The system uses the `BeIR/scifact` dataset (corpus component) from Hugging Face, loaded using the `datasets` library. This dataset contains scientific documents.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- An active OpenSearch instance (local or remote).
- HuggingFace API Key (for LLM summarization).

## Setting Up the Environment

### 1. Clone the Repository

```bash
git clone https://github.com/Abbilville/esempeha-se TK
cd TK
```

### 2. Set Up a Virtual Environment

#### On Windows:

```bash
# Create a virtual environment
python -m venv env

# Activate the virtual environment
env\Scripts\activate
```

#### On macOS/Linux:

```bash
# Create a virtual environment
python -m venv env

# Activate the virtual environment
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root (TK/) with the following content:

```env
OPENSEARCH_HOST=your_opensearch_host_ip_or_domain # e.g., localhost
OPENSEARCH_PORT=your_opensearch_port              # e.g., 9200
HUGGINGFACE_API_KEY=your_huggingface_api_key      # e.g., hf_xxxxxxxxxxxxxxx
```

Replace placeholders with your actual OpenSearch and HuggingFace details.

### 5. Set Up OpenSearch

Ensure your OpenSearch instance is running on Docker (e.g., localhost:9200) and accessible from the application. The application will attempt to create the necessary index (`scifact_index`) if it doesn't exist during the data indexing step.

## Running the Project

### 1. Index Data into OpenSearch

Before running the application for the first time, or when you want to update the search index, run the following management command:

```bash
python manage.py index_data
```

This command will download the `BeIR/scifact` dataset using the Hugging Face `datasets` library (if not already cached), process its corpus, and index it into OpenSearch. This might take a significant amount of time and disk space, especially on the first run.

You can limit the number of documents indexed for testing purposes:

```bash
python manage.py index_data --max-docs 1000
```

### 2. Start the Development Server

```bash
python manage.py runserver
```

This will start the server, typically at http://127.0.0.1:8000/

### 3. Access the Application

- Main application: http://127.0.0.1:8000/
- Admin interface: http://127.0.0.1:8000/admin/ (Default Django admin)

## Technologies Used

- **Backend**: Django
- **Frontend**: HTML, Tailwind CSS
- **Search Engine**: OpenSearch
- **Dataset**: `BeIR/scifact` (corpus) (from Hugging Face, loaded via `datasets` library)
- **LLM**: HuggingFace Inference API (e.g., Meta-Llama-3-8B-Instruct)
- **Python Libraries**: `opensearch-py`, `datasets`, `huggingface_hub`, `django`, `python-dotenv`, `ir_datasets` (may still be present if other functionalities use it, or can be removed if fully replaced).

## Project Structure (Key Components)

```
TK/
├── esempeha/            # Main project directory
│   ├── settings.py      # Project settings (incl. OpenSearch, API keys)
│   └── urls.py          # Project URL configuration
├── main/                # Main application directory
│   ├── opensearch_utils.py # Utilities for OpenSearch interaction
│   ├── llm_utils.py     # Utilities for LLM interaction
│   ├── views.py         # View functions (search logic)
│   ├── urls.py          # App-specific URL patterns
│   ├── templates/       # HTML templates (index.html, base.html)
│   └── management/
│       └── commands/
│           └── index_data.py # Django command for data indexing
├── static/              # Static files (CSS, JS, images)
├── templates/           # Global templates (e.g., 404.html)
├── .env                 # Environment variables (MUST BE CREATED)
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Common Tasks & Troubleshooting

(Refer to the original README section, and add specifics if any arise for OpenSearch or LLM)

### OpenSearch Connection Issues

- Ensure OpenSearch is running and accessible at the host/port specified in `.env`.
- Check OpenSearch logs for any errors.
- Verify firewall rules if OpenSearch is on a different machine/network.

### LLM Summarization Issues

- Ensure `HUGGINGFACE_API_KEY` is correctly set in `.env`.
- Check for rate limits on the HuggingFace Inference API (free tier has limitations).
- Verify network connectivity to `api-inference.huggingface.co`.

## Contact

If you have any questions or issues, please contact:

- Abbilhaidar Farras Zulfikar: abbilhaidar.farras@ui.ac.id
- Ravie Hasan Abud: ravie.hasan@ui.ac.id
- Steven Faustin Orginata: steven.faustin@ui.ac.id
