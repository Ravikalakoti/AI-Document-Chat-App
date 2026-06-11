# AI Document Chat App

A free, local-first Django-based AI document chat application. Users can upload documents, extract text, create vector embeddings, store them in a local vector database, and chat with the document using a local LLM.

## Features

- Upload DOC, DOCX, ODT, and similar office documents.
- Convert documents to HTML using LibreOffice in headless mode.
- Extract document text and split it into chunks.
- Generate embeddings using Ollama.
- Store embeddings in ChromaDB.
- Ask questions and get answers using RAG (Retrieval-Augmented Generation).
- Fully local and free to run on a MacBook.

## Tech Stack

- Python
- Django
- Django REST Framework
- SQLite or PostgreSQL
- ChromaDB
- Ollama
- LibreOffice
- BeautifulSoup

## How It Works

1. User uploads a document.
2. Django saves the file.
3. LibreOffice converts the file to HTML.
4. Text is extracted from the HTML.
5. Text is split into chunks.
6. Each chunk is embedded using Ollama embeddings.
7. Embeddings are stored in ChromaDB.
8. During chat, user query is embedded.
9. ChromaDB returns the most relevant chunks.
10. Ollama generates the final answer using retrieved context.

Ollama supports embedding models for RAG applications, and Chroma provides integration patterns for Ollama embeddings. LibreOffice’s command-line headless mode is suitable for document conversion workflows. [web:4][web:1][web:17]

## Prerequisites

Before starting, make sure you have:

- Python 3.10+
- Homebrew installed
- LibreOffice installed
- Ollama installed

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ai_doc_chat
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install system tools

```bash
brew install --cask libreoffice
brew install ollama
```

### 5. Pull Ollama models

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

Ollama documentation recommends embedding-specific models such as `nomic-embed-text` for text embeddings. [web:4][web:1]

## Environment Variables

Create a `.env` file if needed:

```env
DEBUG=True
SECRET_KEY=your-secret-key
```

## Project Setup

### 1. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create superuser

```bash
python manage.py createsuperuser
```

### 3. Start development server

```bash
python manage.py runserver
```

## API Endpoints

### Upload document

`POST /upload/`

Form-data:

- `title`: document title
- `file`: uploaded file

### Chat with document

`POST /api/chat/<doc_id>/`

JSON body:

```json
{
  "message": "What is this document about?"
}
```

### View document page

`GET /doc/<doc_id>/`

## Example Workflow

1. Open the upload endpoint.
2. Upload a document.
3. Wait for indexing to complete.
4. Open the document page.
5. Ask questions in the chat box.
6. Get AI-generated answers based on the uploaded document.

## Folder Structure

```bash
ai_doc_chat/
├── manage.py
├── README.md
├── requirements.txt
├── db.sqlite3
├── chroma_db/
├── media/
├── ai_doc_chat/
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
└── docs/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── utils.py
    ├── embeddings.py
    ├── vector_store.py
    └── templates/
        └── docs/
            └── document.html
```

## Notes

- This project is designed to run locally and free of cloud API costs.
- Large documents may take time to process.
- For production use, background jobs like Celery can be added later.
- You can replace ChromaDB with PostgreSQL + pgvector if you want a single-database setup.

## Future Improvements

- Add user authentication.
- Add chat history storage.
- Add support for PDFs.
- Add background task processing.
- Add streaming responses from Ollama.
- Add better file validation and error handling.

## License

MIT License

## Acknowledgements

- Django
- ChromaDB
- Ollama
- LibreOffice
