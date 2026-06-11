import chromadb
from django.conf import settings
from pathlib import Path

CHROMA_DIR = Path(settings.BASE_DIR) / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

def get_collection(doc_id):
    return client.get_or_create_collection(name=f"doc_{doc_id}")

def reset_collection(doc_id):
    name = f"doc_{doc_id}"
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return client.get_or_create_collection(name=name)
