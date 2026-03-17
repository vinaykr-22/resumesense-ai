import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

def seed_database():
    print("Loading jobs dataset...")
    jobs_path = os.path.join(os.path.dirname(__file__), "jobs.json")
    
    with open(jobs_path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
        
    print(f"Loaded {len(jobs)} jobs. Initializing ChromaDB and embedding model...")
    
    # Initialize Persistent ChromaDB
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name="jobs",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Initialize inexpensive local embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Prepare data for upsertion
    ids = []
    documents = []
    metadatas = []
    
    for job in jobs:
        # Create a rich text representation for embedding (Title + Skills + Description)
        doc_text = f"{job['title']} " + " ".join(job['required_skills']) + f" {job['description']}"
        
        # Format metadata explicitly
        metadata = {
            "id": job["id"],
            "title": job["title"],
            "category": job["category"],
            "level": job["level"],
            "required_skills": ", ".join(job["required_skills"])
        }
        
        ids.append(job["id"])
        documents.append(doc_text)
        metadatas.append(metadata)
        
    print("Generating embeddings... this might take a moment.")
    embeddings = model.encode(documents).tolist()
    
    print("Upserting into ChromaDB collection...")
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"Success! Seeded {len(jobs)} jobs into ChromaDB.")

if __name__ == "__main__":
    seed_database()
