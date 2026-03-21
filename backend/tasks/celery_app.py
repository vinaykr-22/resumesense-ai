import os
import json
from celery import Celery
from database.redis_client import store_status, redis_client
from services import skill_extractor, embedding_service, job_matcher

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "resumesense",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    task_track_started=True,
    accept_content=['json']
)

@celery_app.task(bind=True)
def process_resume(self, resume_id: str, text: str, target_role: str = None):
    """Celery task wrapper — delegates to the shared processing function."""
    return _process_resume_sync(resume_id, text, target_role)


def _process_resume_sync(resume_id: str, text: str, target_role: str = None):
    """
    Core resume processing logic. Can be called from both Celery tasks
    and FastAPI BackgroundTasks.
    """
    try:
        # 1. Update status to "parsing"
        status_obj = {
            "status": "parsing",
            "stage_label": "Extracting skills from resume",
            "progress": 10,
            "result": None,
            "error": None
        }
        store_status(resume_id, status_obj)
        
        # 2. Run skill extraction (execute async function synchronously)
        import asyncio
        parsed_skills = asyncio.run(skill_extractor.extract_skills(text))
        flat_skills_list = parsed_skills.get("all_skills", [])
        
        # 2b. Cache skills so /resume/skills endpoint can find them
        redis_client.setex(f"skills:{resume_id}", 24 * 3600, json.dumps(parsed_skills))
        
        # 3. Update status to "embedding"
        status_obj.update({
            "status": "embedding",
            "stage_label": "Generating semantic embeddings",
            "progress": 40
        })
        store_status(resume_id, status_obj)
        
        # 4. Generate embedding using the flattened list of skills
        embedding = embedding_service.generate_embedding(" ".join(flat_skills_list))
        
        # 5. Update status to "matching"
        status_obj.update({
            "status": "matching",
            "stage_label": "Matching against job database",
            "progress": 70
        })
        store_status(resume_id, status_obj)
        
        # 6. Run job matching
        match_result = job_matcher.match(resume_id, target_role)
        
        # 7. Store final result in Redis
        final_result = {
            "resume_id": resume_id,
            "skills": parsed_skills,
            "matches": match_result
        }
        redis_client.setex(f"result:{resume_id}", 3600, json.dumps(final_result))
        
        # 8. Set status to "completed"
        status_obj.update({
            "status": "completed",
            "stage_label": "Processing complete",
            "progress": 100,
            "result": final_result
        })
        store_status(resume_id, status_obj)
        
        return final_result
        
    except Exception as e:
        error_msg = str(e)
        status_obj = {
            "status": "failed",
            "stage_label": "Processing failed",
            "progress": 0,
            "result": None,
            "error": error_msg
        }
        store_status(resume_id, status_obj)
        raise e
