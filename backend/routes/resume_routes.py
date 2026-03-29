import os
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Path, Depends, UploadFile, File, status, BackgroundTasks
from services.auth import get_current_user
from database.redis_client import get_status, redis_client
from services.resume_parser import extract_text
from tasks.celery_app import _process_resume_sync
from services.rate_limiter import RateLimiter

router = APIRouter()

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
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
    
    # 4.5 Detect existing versions dynamically
    cursor = '0'
    version_count = 0
    while cursor != 0:
        cursor, keys = redis_client.scan(cursor=cursor, match="resume:res_*", count=100)
        for k in keys:
            try:
                data_str = redis_client.get(k)
                if data_str:
                    d = json.loads(data_str)
                    if d.get("user_email") == current_user:
                        version_count += 1
            except Exception:
                pass
        if cursor == 0 or cursor == b'0':
            break
            
    next_version = version_count + 1
    
    # 5. Store in Redis
    resume_data = {
        "text": extracted_text,
        "user_email": current_user,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "version": next_version,
        "parsed_content": {"raw_text": extracted_text}
    }
    # Keep original text around for a bit (e.g. 7 days)
    redis_client.setex(f"resume:{resume_id}", 7 * 24 * 3600, json.dumps(resume_data))
    
    # Initialize the tracking status so the frontend doesn't get a 404 before Celery starts
    from database.redis_client import store_status
    store_status(resume_id, {"status": "queued", "progress": 5})
    
    # 6. Dispatch Background Task (uses the plain function, NOT the Celery task)
    background_tasks.add_task(_process_resume_sync, resume_id, extracted_text)
    
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
        cached_obj = json.loads(cached)
        cached_all_skills = cached_obj.get("all_skills", []) if isinstance(cached_obj, dict) else []
        if isinstance(cached_all_skills, list) and len(cached_all_skills) > 0:
            return cached_obj
        
    # 2. Fetch original resume text from Redis
    resume_data_str = redis_client.get(f"resume:{resume_id}")
    if not resume_data_str:
        raise HTTPException(status_code=404, detail="Resume text not found. It may have expired.")
        
    resume_data = json.loads(resume_data_str)
    if resume_data.get("user_email") and resume_data.get("user_email") != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to view this resume.")

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
        vector = embedding_service.generate_embedding(text)
        
        return {
            "embedding_id": stored_id,
            "vector_length": len(vector),
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
    
    import hashlib
    short_key_val = hashlib.md5(target_role.encode()).hexdigest()
    cache_key = f"suggestions_v3:{resume_id}:{short_key_val}"
    
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
        
    try:
        from services.ats_scorer import ATSScorer
        from services.rewriter import Rewriter
        from services.course_recommender import CourseRecommender
        from services.job_matcher_v2 import JobMatcher as DynamicJobMatcher
        import re
        import asyncio

        # Fetch skills from redis to avoid re-extracting
        skills_cache = redis_client.get(f"skills:{resume_id}")
        flat_skills_list = []
        if skills_cache:
            skills_data = json.loads(skills_cache)
            flat_skills_list = skills_data.get("all_skills", [])
        
        # Job Matching V2 (Dynamic Match)
        job_match_data = {}
        learning_path = {}
        target_skills = []
        
        if target_role and len(target_role) > 10:
            jb_v2 = DynamicJobMatcher()
            job_match_data = jb_v2.match_resume_to_jd(flat_skills_list, target_role)
            target_skills = jb_v2.extract_jd_skills(target_role)
            
            missing = job_match_data.get("missing_skills", [])
            if missing:
                learning_path = CourseRecommender().generate_learning_path(missing, target_role)

        # ATS Scoring
        ats_score_res = ATSScorer().score_resume(text, flat_skills_list, target_skills)

        # Bullet Rewriting
        extracted_bullets = []
        for line in text.split("\n"):
            match = re.match(r"^\s*([\-\*\•\>]|\d+\.|\w\))\s+(.+)", line)
            if match:
                extracted_bullets.append(match.group(2).strip())
        
        weak_bullets = extracted_bullets[:5] if extracted_bullets else []
        
        # Run rewrite in thread to avoid blocking event loop
        rewritten_bullets = await asyncio.to_thread(Rewriter().rewrite_bullets_batch, weak_bullets) if weak_bullets else []

        suggestions_json = {
            "ats_score": ats_score_res.get("total_score", 0.0),
            "ats_breakdown": ats_score_res.get("breakdown", {}),
            "weak_bullets": weak_bullets,
            "rewritten_bullets": rewritten_bullets,
            "job_match_data": job_match_data,
            "learning_path": learning_path
        }
        
        # Cache for 2 hours
        # using the same cache key instantiated at the top
        redis_client.setex(cache_key, 2 * 3600, json.dumps(suggestions_json))
        return suggestions_json

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

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

# ==========================================
# V2 Endpoints: Resume Versions & Comparison
# ==========================================

@router.get("/versions")
async def get_resume_versions(current_user: str = Depends(get_current_user)):
    """Fetches all uploaded iterations of a user's resume alongside their computed ATS scores."""
    cursor = '0'
    resume_keys = set()
    while cursor != 0:
        cursor, keys = redis_client.scan(cursor=cursor, match="resume:res_*", count=100)
        resume_keys.update(keys)
        if cursor == 0 or cursor == b'0':
            break
            
    versions = []
    for k in resume_keys:
        key_str = k.decode('utf-8') if isinstance(k, bytes) else str(k)
        
        try:
            r_data_str = redis_client.get(key_str)
            if not r_data_str:
                continue
                
            r_data = json.loads(r_data_str)
            if r_data.get("user_email") == current_user:
                res_id = key_str.replace("resume:", "")
                
                # Fetch ATS score from result payload
                score = 0.0
                res_str = redis_client.get(f"result:{res_id}")
                if res_str:
                    try:
                        res_json = json.loads(res_str)
                        score = res_json.get("analysis_data", {}).get("ats_score", 0.0)
                    except Exception:
                        pass
                        
                versions.append({
                    "resume_id": res_id,
                    "filename": r_data.get("filename", "Unknown"),
                    "uploaded_at": r_data.get("uploaded_at"),
                    "version": r_data.get("version", 1),
                    "ats_score": score
                })
        except Exception:
            continue
            
    # Sort newest first
    versions.sort(key=lambda x: x.get("uploaded_at") or "", reverse=True)
    return {"versions": versions}


@router.get("/compare")
async def compare_versions(v1: str, v2: str, current_user: str = Depends(get_current_user)):
    """Compares two distinct resume IDs and calculates the delta in scores and skills."""
    res1_str = redis_client.get(f"result:{v1}")
    res2_str = redis_client.get(f"result:{v2}")
    
    if not res1_str or not res2_str:
        raise HTTPException(
            status_code=404, 
            detail="One or both resume versions not found or haven't finished processing."
        )
        
    try:
        r1 = json.loads(res1_str)
        r2 = json.loads(res2_str)
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupted result data in database.")
        
    # Extract scores and skills from the V2 schema analysis_data
    score1 = r1.get("analysis_data", {}).get("ats_score", 0.0)
    score2 = r2.get("analysis_data", {}).get("ats_score", 0.0)
    
    skills1 = set([s.lower() for s in r1.get("analysis_data", {}).get("extracted_skills", [])])
    skills2 = set([s.lower() for s in r2.get("analysis_data", {}).get("extracted_skills", [])])
    
    new_skills = sorted(list(skills2 - skills1))
    dropped_skills = sorted(list(skills1 - skills2))
    score_diff = round(score2 - score1, 1)
    
    return {
        "v1": {
            "resume_id": v1,
            "ats_score": score1,
            "skills_count": len(skills1)
        },
        "v2": {
            "resume_id": v2,
            "ats_score": score2,
            "skills_count": len(skills2)
        },
        "improvements": {
            "score_diff": f"+{score_diff}" if score_diff > 0 else str(score_diff),
            "new_skills": new_skills,
            "dropped_skills": dropped_skills
        }
    }

