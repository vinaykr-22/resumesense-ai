import os
import json
import hashlib
from datetime import datetime, timezone
import chromadb
from database.redis_client import redis_client
from openai import OpenAI

# OpenAI client for embeddings (uses the same OPENAI_API_KEY)
_openai_client = None

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536  # default for text-embedding-3-small


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def get_chroma_client():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    return chromadb.PersistentClient(path=db_path)


def generate_embedding(text: str) -> list[float]:
    """Generates an embedding vector via OpenAI API, with Redis caching."""
    cleaned_text = " ".join(text.split())
    if not cleaned_text:
        return [0.0] * EMBEDDING_DIMENSIONS

    # Check cache
    text_hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()
    cache_key = f"emb:{text_hash}"
    cached_emb = redis_client.get(cache_key)

    if cached_emb:
        return json.loads(cached_emb)

    # Cache miss: call OpenAI Embeddings API
    client = _get_openai_client()
    response = client.embeddings.create(
        input=cleaned_text[:8000],  # text-embedding-3-small supports 8k tokens
        model=EMBEDDING_MODEL,
    )
    vector = response.data[0].embedding

    # Store in Redis (expires in 7 days)
    redis_client.setex(cache_key, 7 * 24 * 3600, json.dumps(vector))

    return vector


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Batch-generate embeddings for multiple texts in a single API call."""
    cleaned = [" ".join(t.split())[:8000] for t in texts]

    client = _get_openai_client()
    response = client.embeddings.create(
        input=cleaned,
        model=EMBEDDING_MODEL,
    )

    vectors = [item.embedding for item in response.data]

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
