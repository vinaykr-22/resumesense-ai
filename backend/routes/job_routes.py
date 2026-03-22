import os
import json
from typing import Optional
from fastapi import APIRouter, Query, HTTPException

router = APIRouter()

def _load_jobs():
    jobs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs_dataset", "jobs.json")
    try:
        with open(jobs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Jobs dataset not found. Have you seeded the data?")

@router.get("/list")
async def list_jobs(
    category: Optional[str] = Query(None, description="Filter by job category"),
    level: Optional[str] = Query(None, description="Filter by job level"),
    limit: int = Query(20, description="Max number of results to return", ge=1, le=50)
):
    jobs = _load_jobs()
    
    # Apply filters
    if category:
        jobs = [j for j in jobs if j.get("category") == category.lower()]
    if level:
        jobs = [j for j in jobs if j.get("level") == level.lower()]
        
    # Return paginated snippet
    return {
        "total_matches": len(jobs),
        "jobs": jobs[:limit]
    }

from pydantic import BaseModel
from fastapi import Depends
from services.auth import get_current_user
from database.redis_client import redis_client
from datetime import datetime, timezone

class JobMatchRequest(BaseModel):
    resume_id: str
    top_k: int = 10

@router.post("/match")
async def match_jobs_endpoint(
    req: JobMatchRequest,
    current_user: str = Depends(get_current_user)
):
    resume_id = req.resume_id
    cache_key = f"match:{resume_id}:{req.top_k}"
    
    # 1. Check cache first
    cached = redis_client.get(cache_key)
    if cached:
        cached_obj = json.loads(cached)
        cached_matches = cached_obj.get("matches", []) if isinstance(cached_obj, dict) else []
        if isinstance(cached_matches, list) and len(cached_matches) > 0:
            return cached_obj
        
    # 2. Fetch original resume text from Redis
    resume_data_str = redis_client.get(f"resume:{resume_id}")
    if not resume_data_str:
        raise HTTPException(status_code=404, detail="Resume text not found. The resume may have expired.")
        
    resume_data = json.loads(resume_data_str)
    if resume_data.get("user_email") and resume_data.get("user_email") != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to view this resume.")

    text = resume_data.get("text", "")
    if not text:
        raise HTTPException(status_code=500, detail="Resume text is empty.")
        
    try:
        from services import job_matcher
        matches = job_matcher.match_jobs(text, req.top_k)
        
        result = {
            "resume_id": resume_id,
            "matches": matches,
            "total": len(matches),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 3. Cache the result for 1 hour
        redis_client.setex(cache_key, 3600, json.dumps(result))
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match jobs: {str(e)}")

class SkillGapRequest(BaseModel):
    resume_id: str
    job_role: str

@router.post("/skill-gap")
async def get_skill_gap(
    req: SkillGapRequest,
    current_user: str = Depends(get_current_user)
):
    resume_id = req.resume_id
    cache_key = f"skills:{resume_id}"
    
    cached_skills = redis_client.get(cache_key)
    if cached_skills:
        skills_data = json.loads(cached_skills)
    else:
        resume_data_str = redis_client.get(f"resume:{resume_id}")
        if not resume_data_str:
            raise HTTPException(status_code=404, detail="Resume text not found. The resume may have expired.")
            
        resume_data = json.loads(resume_data_str)
        text = resume_data.get("text", "")
        if not text:
            raise HTTPException(status_code=500, detail="Resume text is empty.")
            
        try:
            from services import skill_extractor
            skills_data = await skill_extractor.extract_skills(text)
            redis_client.setex(cache_key, 24 * 3600, json.dumps(skills_data))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to extract skills: {str(e)}")
            
    resume_skills = skills_data.get("all_skills", [])
    
    try:
        from services import job_matcher
        gap_analysis = job_matcher.analyze_skill_gap(resume_skills, req.job_role)
        return gap_analysis
    except Exception as e:
        from fastapi import HTTPException
        # If it's already an HTTPException (like 404), re-raise it
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to analyze skill gap: {str(e)}")
