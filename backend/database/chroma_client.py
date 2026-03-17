import chromadb
from chromadb.config import Settings

# Initialize the ChromaDB client specifying a local directory to store data persistently
chroma_client = chromadb.PersistentClient(path="./chroma_db", settings=Settings(allow_reset=True))

# Create or get the collection for storing job embeddings
try:
    jobs_collection = chroma_client.get_or_create_collection(
        name="jobs_collection",
        metadata={"hnsw:space": "cosine"} # Use cosine similarity for text embeddings
    )
except Exception as e:
    print(f"Error initializing ChromaDB collection: {e}")
    jobs_collection = None
