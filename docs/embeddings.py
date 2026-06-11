import ollama

EMBED_MODEL = "nomic-embed-text"

def get_embedding(text):
    result = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return result["embedding"]