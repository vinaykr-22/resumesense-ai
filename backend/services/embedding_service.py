import os
import json
import hashlib
from datetime import datetime, timezone
import chromadb
from database.redis_client import redis_client

_model = None

def get_model():
    """Lazy initialize the embedding model only when needed."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_chroma_client():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    return chromadb.PersistentClient(path=db_path)

def generate_embedding(text: str) -> list[float]:
    """Generates an embedding vector, utilizing a Redis cache for identical text."""
    # Clean text: strip whitespace
    cleaned_text = " ".join(text.split())
    # Note: SentenceTransformer naturally handles truncation internally
    
    # Check cache
    text_hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()
    cache_key = f"emb:{text_hash}"
    cached_emb = redis_client.get(cache_key)
    
    if cached_emb:
        return json.loads(cached_emb)
        
    # Cache miss: generate new embedding
    model = get_model()
    # SentenceTransformer returns NumPy array, we need standard float list
    vector = model.encode(cleaned_text).tolist()
    
    # Store in Redis (expires in 7 days)
    redis_client.setex(cache_key, 7 * 24 * 3600, json.dumps(vector))
    
    return vector

def store_resume_embedding(resume_id: str, text: str) -> str:
    """Generates and stores the embedding for a resume directly into ChromaDB."""
    vector = generate_embedding(text)
    
    # Get or create collection
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="resumes",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Upsert to ChromaDB
    collection.upsert(
        ids=[resume_id],
        embeddings=[vector],
        metadatas=[{
            "resume_id": resume_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }]
    )
    
    return resume_id
