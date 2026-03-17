# ResumeSense AI

## Quick start
1. `cp backend/.env.example backend/.env` (fill in keys)
2. `docker-compose up`
3. `cd frontend && npm install && npm run dev`
4. Visit http://localhost:5173
5. Seed jobs: `docker-compose exec backend python jobs_dataset/seed_embeddings.py`
