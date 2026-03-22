# ResumeSense AI

ResumeSense AI is an intelligent platform that comprehensively analyzes resumes and matches them to the most relevant job postings. It features advanced text processing that analyzes the full content of resumes without truncation, extracts detailed skills, and semantically matches candidates using high-quality vector embeddings.

## Features

- **Deep Resume Analysis**: Processes the entire text of complex resumes (PDF/DOCX) with increased character limits and file sizes to ensure no detail is missed.
- **Skill Extraction**: Accurately extracts a candidate's key skills using Gemini models.
- **Semantic Job Matching**: Employs Sentence Transformers and ChromaDB to semantically match extracted skills with job descriptions in our dataset.
- **Background Processing**: Uses Celery and Redis to handle long-running AI tasks asynchronously, ensuring a responsive user experience.
- **Modern UI**: Built with React and Vite for a fast, responsive frontend.

## Tech Stack

- **Backend**: Python, FastAPI, Celery, Redis, ChromaDB, Sentence Transformers, Gemini, pdfplumber, python-docx
- **Frontend**: React, Vite, Recharts, Lucide Icons

## Local Development Setup

Since this project runs natively (no Docker), follow these steps to run it locally.

### Prerequisites
- Python 3.10+
- Node.js 18+
- Redis (installed and running locally on port 6379, or provide a cloud Redis URL)

### 1. Backend Setup

Open a terminal and navigate to the backend directory:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

Set up your environment variables:
```bash
cp .env.example .env
```
*Note: Make sure to fill in `GEMINI_API_KEY` and verify `REDIS_URL` in the `.env` file.*

Seed the jobs database (required on first run to populate ChromaDB):
```bash
python jobs_dataset/seed_embeddings.py
```

Start the Celery worker (in a separate terminal window, activated venv):
```bash
# On Windows, you might need to use eventlet or gevent:
# pip install eventlet
# celery -A tasks worker -l info -P eventlet
celery -A tasks worker --loglevel=info
```

Start the FastAPI backend server:
```bash
uvicorn main:app --reload --port 10000
```
*(Alternatively, you can run `bash startup.sh` on Unix-like environments).*

### 2. Frontend Setup

Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Start the development server:
```bash
npm run dev
```

### 3. Access the Application
Visit [http://localhost:5173](http://localhost:5173) in your browser.
