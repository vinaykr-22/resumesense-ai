#!/bin/bash
python jobs_dataset/seed_embeddings.py
uvicorn main:app --host 0.0.0.0 --port $PORT
