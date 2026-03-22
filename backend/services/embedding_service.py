import os
import json
import hashlib
from datetime import datetime, timezone
import httpx
import chromadb
from database.redis_client import redis_client

GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "3072"))


def _normalize_model_name(model_name: str) -> str:
    value = (model_name or "").strip()
    if value.startswith("models/"):
        return value[len("models/"):]
    return value


def _get_gemini_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY is not set")
    return key


def get_chroma_client():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    return chromadb.PersistentClient(path=db_path)


def generate_embedding(text: str) -> list[float]:
    """Generates an embedding vector via Gemini API, with Redis caching."""
    model_name = _normalize_model_name(GEMINI_EMBEDDING_MODEL)
    cleaned_text = " ".join(text.split())
    if not cleaned_text:
        return [0.0] * EMBEDDING_DIMENSIONS

    # Check cache
    text_hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()
    cache_key = f"emb:{text_hash}"
    cached_emb = redis_client.get(cache_key)

    if cached_emb:
        return json.loads(cached_emb)

    # Cache miss: call Gemini Embeddings API
    api_key = _get_gemini_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:embedContent?key={api_key}"
    
    payload = {
        "model": f"models/{model_name}",
        "content": {
            "parts": [{"text": cleaned_text[:2000]}]
        },
        "taskType": "RETRIEVAL_DOCUMENT"
    }
    
    response = httpx.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    vector = data["embedding"]["values"]

    # Store in Redis (expires in 7 days)
    redis_client.setex(cache_key, 7 * 24 * 3600, json.dumps(vector))

    return vector


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts.

    Uses batch endpoint when available; falls back to per-item embed calls for
    models that do not support batch embedding.
    """
    model_name = _normalize_model_name(GEMINI_EMBEDDING_MODEL)
    api_key = _get_gemini_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:batchEmbedContents?key={api_key}"
    
    cleaned = [" ".join(t.split())[:2000] for t in texts]
    
    requests_list = [
        {
            "model": f"models/{model_name}",
            "content": {"parts": [{"text": text}]},
            "taskType": "RETRIEVAL_DOCUMENT"
        }
        for text in cleaned
    ]
    
    payload = {"requests": requests_list}
    
    try:
        response = httpx.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        vectors = [item["values"] for item in data["embeddings"]]
    except Exception:
        # Fallback for models that only support embedContent.
        vectors = [generate_embedding(text) for text in cleaned]

    # Cache each one
    for text, vector in zip(cleaned, vectors):
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_key = f"emb:{text_hash}"
        redis_client.setex(cache_key, 7 * 24 * 3600, json.dumps(vector))

    return vectors


def store_resume_embedding(resume_id: str, text: str) -> str:
    """Generates and stores the embedding for a resume directly into ChromaDB."""
    vector = generate_embedding(text)

    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="resumes",
        metadata={"hnsw:space": "cosine"}
    )

    collection.upsert(
        ids=[resume_id],
        embeddings=[vector],
        metadatas=[{
            "resume_id": resume_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }]
    )

    return resume_id
