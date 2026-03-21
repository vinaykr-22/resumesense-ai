import json
import chromadb
import os

def seed_jobs():
    print("Seeding job dataset...")
    
    jobs_path = os.path.join(os.path.dirname(__file__), "jobs.json")
    with open(jobs_path, "r") as f:
        jobs = json.load(f)
    
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection("jobs")
    
    # Store jobs as documents WITHOUT embeddings
    # ChromaDB will use its built-in embedding function
    ids = [job["id"] for job in jobs]
    documents = [
        job["title"] + " " + " ".join(job["required_skills"]) + " " + job.get("description", "")
        for job in jobs
    ]
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
    
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Seeded {len(jobs)} jobs into ChromaDB successfully")

if __name__ == "__main__":
    seed_jobs()