import ollama

EMBED_MODEL = "nomic-embed-text"

def get_embedding(text):
    try:
        print("TEXT:", text[:50])

        result = ollama.embeddings(
            model=EMBED_MODEL,
            prompt=text
        )

        print("RESULT:", result)  # 🔥 IMPORTANT

        emb = result.get("embedding", None)

        print("EMBED LEN:", len(emb) if emb else None)

        return emb

    except Exception as e:
        print("EMBED ERROR:", e)
        return None