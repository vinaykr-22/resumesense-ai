#!/bin/bash
set -e

if [ "${AUTO_SEED_JOBS:-false}" = "true" ]; then
	python jobs_dataset/seed_embeddings.py
fi

exec uvicorn main:app --host 0.0.0.0 --port $PORT
