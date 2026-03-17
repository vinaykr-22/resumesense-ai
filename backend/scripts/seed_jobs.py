import sys
import os

# Add backend directory to Python path so we can import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.chroma_client import jobs_collection
from services.embedding_service import generate_embedding as generate
import uuid

def seed_database():
    print("Seeding Jobs Database...")
    
    if jobs_collection is None:
        print("Error: ChromaDB Collection is not initialized.")
        return
        
    jobs = [
        {
            "title": "Senior Python Backend Engineer",
            "description": "Looking for an experienced backend developer with strong Python, FastAPI, Postgres, and Docker skills. Experience with Celery and Redis is a huge plus. You will be building scalable APIs and distributed systems.",
            "skills": "python fastapi postgresql docker celery redis api backend"
        },
        {
            "title": "Frontend React Developer",
            "description": "We need a UI specialist who loves React, Next.js, and Tailwind CSS. You should have a sharp eye for design and performance. Familiarity with TypeScript and Redux is expected.",
            "skills": "react nextjs tailwindcss typescript redux frontend ui design html css"
        },
        {
            "title": "Data Scientist / ML Engineer",
            "description": "Join our AI team to build predictive models. Required: Python, PyTorch/TensorFlow, Pandas, and scikit-learn. Experience with NLP, vector databases (ChromaDB, Pinecone), and LLMs (OpenAI, HuggingFace) is highly desired.",
            "skills": "python pytorch tensorflow pandas scikit-learn nlp llm openai huggingface machine learning ai"
        },
        {
            "title": "DevOps Engineer",
            "description": "Seeking a DevOps wizard to manage our AWS infrastructure. Must know Kubernetes, Terraform, CI/CD pipelines (GitHub Actions), and monitoring tools (Prometheus, Grafana).",
            "skills": "aws kubernetes terraform github actions ci cd prometheus grafana devops infrastructure"
        },
        {
            "title": "Full Stack Engineer (MERN)",
            "description": "Full stack developer needed for a fast-paced startup. MongoDB, Express, React, and Node.js. Experience building RESTful APIs and connecting them to modern frontends.",
            "skills": "mongodb express react node javascript typescript fullstack api"
        }
    ]

    print(f"Generating embeddings and inserting {len(jobs)} jobs...")
    
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for job in jobs:
        # We generate the embedding based on the skills string to ensure high keyword match relevance
        job_embedding = generate(job["skills"])
        
        job_id = str(uuid.uuid4())
        ids.append(job_id)
        embeddings.append(job_embedding)
        # Store the full description as the document
        documents.append(job["description"])
        # Store title and skills as metadata
        metadatas.append({"title": job["title"], "skills": job["skills"]})
        
        print(f"Prepared: {job['title']}")
        
    try:
        jobs_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print("\nSuccess! Database seeded.")
    except Exception as e:
        print(f"\nFailed to insert into ChromaDB: {e}")

if __name__ == "__main__":
    seed_database()
