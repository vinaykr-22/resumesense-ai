import json
import os
import sys

def seed_jobs():
    """Seed jobs into ChromaDB using OpenAI embeddings for consistency."""
    print("Seeding job dataset...")

    # Load dotenv so OPENAI_API_KEY is available
    from dotenv import load_dotenv
    load_dotenv()

    jobs_path = os.path.join(os.path.dirname(__file__), "jobs.json")
    with open(jobs_path, "r") as f:
        jobs = json.load(f)

    # Use the project's embedding service (OpenAI-powered)
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from services.embedding_service import generate_embeddings_batch, get_chroma_client

    # Prepare documents for embedding
    documents = [
        job["title"] + " " + " ".join(job["required_skills"]) + " " + job.get("description", "")
        for job in jobs
    ]

    # Batch embed all jobs in a single API call (fast!)
    print(f"Generating embeddings for {len(jobs)} jobs via OpenAI...")
    embeddings = generate_embeddings_batch(documents)
    print("Embeddings generated.")

    # Store in ChromaDB
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="jobs",
        metadata={"hnsw:space": "cosine"}
    )

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

    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"Seeded {len(jobs)} jobs into ChromaDB successfully")

if __name__ == "__main__":
    seed_jobs()