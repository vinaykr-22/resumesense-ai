import json
import os
import sys

def seed_jobs():
    """Seed jobs into ChromaDB using Gemini embeddings for consistency."""
    print("Starting Global Job Database Sync...")

    # Load dotenv so GEMINI_API_KEY is available
    from dotenv import load_dotenv
    load_dotenv()

    # Use the project's embedding service (Gemini-powered)
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from services.embedding_service import generate_embeddings_batch, get_chroma_client
    from database.redis_client import redis_client

    # 1. Clear Redis Embedding Cache (ensure we don't use mismatching cached vectors)
    print("Flushing stale embedding cache from Redis...")
    keys = redis_client.keys("emb:*")
    if keys:
        redis_client.delete(*keys)
        print(f"Cleared {len(keys)} cached embeddings.")

    # 2. Re-initialize ChromaDB Collection
    client = get_chroma_client()
    try:
        client.delete_collection("jobs")
        print("Dropped existing 'jobs' collection to reset dimensions.")
    except Exception:
        pass

    collection = client.create_collection(
        name="jobs",
        metadata={"hnsw:space": "cosine"}
    )

    # 3. Load jobs and re-seed
    jobs_path = os.path.join(os.path.dirname(__file__), "jobs.json")
    with open(jobs_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # Prepare documents for embedding
    documents = [
        job["title"] + " " + " ".join(job["required_skills"]) + " " + job.get("description", "")
        for job in jobs
    ]

    # Batch embed (using current Gemini config)
    print(f"Generating NEW embeddings for {len(jobs)} jobs via Gemini...")
    embeddings = generate_embeddings_batch(documents)
    print(f"Embeddings generated (Dimension: {len(embeddings[0])}).")

    ids = [job["id"] for job in jobs]
    metadatas = [
        {
            "id": job["id"],
            "title": job["title"],
            "category": job["category"],
            "level": job["level"],
            "required_skills": ",".join(job["required_skills"])
        }
        for job in jobs
    ]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"Successfully synchronized {len(jobs)} jobs with {len(embeddings[0])} dimensions successfully")

if __name__ == "__main__":
    seed_jobs()