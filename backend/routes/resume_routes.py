import os
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Path, Depends, UploadFile, File, status, BackgroundTasks
from services.auth import get_current_user
from database.redis_client import get_status, redis_client
from services.resume_parser import extract_text
from tasks.celery_app import process_resume
from services.rate_limiter import RateLimiter

router = APIRouter()

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "5"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

@router.post("/upload")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    rate_limit: bool = Depends(RateLimiter("upload_resume", max_requests=5, window_seconds=3600))
):
    # 1. Validate file extension
    filename = file.filename or ""
    ext = filename.lower().split('.')[-1]
    if ext not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
        
    # 2. Validate file size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_MB}MB"
        )
        
    # 3. Read file bytes and try extraction
    try:
        extracted_text = extract_text(file_bytes, filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract text. {str(e)}"
        )
        
    # 4. Generate resume UUID
    resume_id = "res_" + uuid.uuid4().hex[:10]
    
    # 5. Store in Redis
    resume_data = {
        "text": extracted_text,
        "user_email": current_user,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    # Keep original text around for a bit (e.g. 7 days)
    redis_client.setex(f"resume:{resume_id}", 7 * 24 * 3600, json.dumps(resume_data))
    
    # Initialize the tracking status so the frontend doesn't get a 404 before Celery starts
    from database.redis_client import store_status
    store_status(resume_id, {"status": "queued", "progress": 5})
    
    # 6. Dispatch Background Task
    # TODO: Replace with Celery on paid tier.
    background_tasks.add_task(process_resume, resume_id, extracted_text)
    
    # 7. Return status
    return {
        "resume_id": resume_id,
        "job_id": resume_id,
        "filename": filename,
        "char_count": len(extracted_text),
        "status": "processing",
        "message": "Resume received. Analysis starting..."
    }

@router.get("/status/{job_id}")
def get_resume_status(job_id: str = Path(..., description="The ID of the resume/job to check")):
    status_obj = get_status(job_id)
    if not status_obj:
        raise HTTPException(status_code=404, detail="Status not found")
    return status_obj

from pydantic import BaseModel

class ResumeSkillsRequest(BaseModel):
    resume_id: str

@router.post("/skills")
async def get_skills(
    req: ResumeSkillsRequest,
    current_user: str = Depends(get_current_user)
):
    resume_id = req.resume_id
    cache_key = f"skills:{resume_id}"
    
    # 1. Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
        
    # 2. Fetch original resume text from Redis
    resume_data_str = redis_client.get(f"resume:{resume_id}")
    if not resume_data_str:
        raise HTTPException(status_code=404, detail="Resume text not found. It may have expired.")
        
    resume_data = json.loads(resume_data_str)
    text = resume_data.get("text", "")
    if not text:
        raise HTTPException(status_code=500, detail="Resume text is empty.")
        
    # 3. Call async extractor
    try:
        from services import skill_extractor
        skills = await skill_extractor.extract_skills(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract skills: {str(e)}")
        
    # 4. Cache the result for 24 hours
    redis_client.setex(cache_key, 24 * 3600, json.dumps(skills))
    
    return skills

class GenerateEmbeddingRequest(BaseModel):
    resume_id: str

@router.post("/embedding/generate")
async def generate_resume_embedding(
    req: GenerateEmbeddingRequest,
    current_user: str = Depends(get_current_user)
):
    resume_id = req.resume_id
    
    # Fetch original resume text from Redis
    resume_data_str = redis_client.get(f"resume:{resume_id}")
    if not resume_data_str:
        raise HTTPException(status_code=404, detail="Resume text not found. Cannot generate embedding.")
        
    resume_data = json.loads(resume_data_str)
    text = resume_data.get("text", "")
    if not text:
        raise HTTPException(status_code=500, detail="Resume text is empty.")
        
    try:
        from services import embedding_service
        import hashlib
        
        # Determine if we will hit the cache
        cleaned_text = " ".join(text.split())
        text_hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()
        is_cached = redis_client.exists(f"emb:{text_hash}") > 0
        
        # Leverage the service to generate (or pull from cache) and store in ChromaDB
        stored_id = embedding_service.store_resume_embedding(resume_id, text)
        
        return {
            "embedding_id": stored_id,
            "vector_length": 384,  # dimensionality of all-MiniLM-L6-v2
            "cached": is_cached
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

class ResumeSuggestionsRequest(BaseModel):
    resume_id: str
    target_role: str

@router.post("/suggestions")
async def get_resume_suggestions(
    req: ResumeSuggestionsRequest,
    current_user: str = Depends(get_current_user),
    rate_limit: bool = Depends(RateLimiter("resume_suggestions", max_requests=15, window_seconds=60))
):
    resume_id = req.resume_id
    target_role = req.target_role
    cache_key = f"suggestions:{resume_id}:{target_role}"
    
    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
        
    # Fetch resume text
    resume_data_str = redis_client.get(f"resume:{resume_id}")
    if not resume_data_str:
        raise HTTPException(status_code=404, detail="Resume text not found. The resume may have expired.")
        
    resume_data = json.loads(resume_data_str)
    # Check authorization (optional but good practice)
    if resume_data.get("user_email") and resume_data.get("user_email") != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to view this resume.")
        
    text = resume_data.get("text", "")
    if not text:
        raise HTTPException(status_code=500, detail="Resume text is empty.")
        
    # Attempt to fetch missing skills from gap analysis cache
    missing_skills = []
    gap_cache = redis_client.get(f"gap:{resume_id}:{target_role}")
    if gap_cache:
        try:
            gap_data = json.loads(gap_cache)
            missing_skills = gap_data.get("missing_skills", [])
        except Exception:
            pass
            
    system_prompt = """You are a professional resume coach. Analyze the resume and give specific,
actionable improvement suggestions for the target role. Return ONLY valid JSON.
Shape: {
  'overall_score': 1-10,
  'summary': 'One sentence assessment',
  'suggestions': [
    {
      'category': 'achievements|formatting|skills|experience|keywords',
      'priority': 'high|medium|low',
      'issue': 'What is wrong',
      'fix': 'Exactly what to do',
      'example': 'Before → After example if applicable'
    }
  ],
  'ats_tips': ['tip1', 'tip2', 'tip3'],
  'strengths': ['strength1', 'strength2']
}"""

    user_prompt = f"Resume text:\n{text[:2500]}\n\nTarget role: {target_role}\nMissing skills: {missing_skills}"
    
    try:
        from services.llm_provider import LLMProvider
        llm = LLMProvider()
        suggestions_json = await llm.extract_json(user_prompt, system_prompt)
        
        # Cache for 2 hours
        redis_client.setex(cache_key, 2 * 3600, json.dumps(suggestions_json))
        return suggestions_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")

@router.get("/history")
async def get_resume_history(current_user: str = Depends(get_current_user)):
    # Scan Redis for resume keys
    # Note: In a production environment with millions of keys, SCAN is better than KEYS
    # For MVP, we can use SCAN to find keys starting with resume:res_
    cursor = '0'
    resume_keys = []
    while cursor != 0:
        # redis-py returns cursor as int or bytes, and keys as list of bytes
        cursor, keys = redis_client.scan(cursor=cursor, match="resume:res_*", count=100)
        resume_keys.extend(keys)
        # break if cursor returns to 0
        if cursor == 0 or cursor == b'0':
            break
            
    # Remove duplicates
    resume_keys = list(set(resume_keys))
    
    history = []
    for key in resume_keys:
        try:
            data_str = redis_client.get(key)
            if data_str:
                data = json.loads(data_str)
                if data.get("user_email") == current_user:
                    # decode key (it's bytes usually)
                    if isinstance(key, bytes):
                        key_str = key.decode("utf-8")
                    else:
                        key_str = str(key)
                        
                    resume_id = key_str.replace("resume:", "")
                    
                    history.append({
                        "resume_id": resume_id,
                        "filename": data.get("filename", "Unknown"),
                        "uploaded_at": data.get("uploaded_at"),
                        "has_analysis": True # Assuming it will be analyzed
                    })
        except Exception:
            continue
            
    # Sort by uploaded_at descending
    history.sort(key=lambda x: x.get("uploaded_at") or "", reverse=True)
    
    # Return top 10
    return history[:10]
