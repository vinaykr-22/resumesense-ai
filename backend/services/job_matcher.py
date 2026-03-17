from typing import Optional, Dict, Any, List
from database.redis_client import redis_client
from services import embedding_service
import json

def match_jobs(resume_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Computes an embedding for the resume, queries ChromaDB's job collection,
    calculates a match score based on L2 distance, and returns sorted matches.
    """
    try:
        # 1. Generate embedding for resume
        resume_vector = embedding_service.generate_embedding(resume_text)
        
        # 2. Query ChromaDB "jobs" collection
        client = embedding_service.get_chroma_client()
        try:
            collection = client.get_collection(name="jobs")
        except Exception:
            # Collection might not exist yet if db isn't seeded
            return []
            
        results = collection.query(
            query_embeddings=[resume_vector],
            n_results=top_k,
            include=["metadatas", "distances"]
        )
        
        matches = []
        if results and "documents" in results or "metadatas" in results:
            if not results["metadatas"][0]:
                return []
                
            for i in range(len(results["metadatas"][0])):
                metadata = results["metadatas"][0][i]
                # ChromaDB with L2 distances returns smaller distance for closer match
                # Convert to percentage
                distance = results["distances"][0][i] if "distances" in results and results["distances"] else 1.0
                score = round((1 - distance) * 100, 1)
                
                # Ensure score boundaries
                score = max(0.0, min(100.0, score))
                
                # Split the joined skills back into a standard list
                req_skills_str = metadata.get("required_skills", "")
                req_skills = [s.strip() for s in req_skills_str.split(",")] if req_skills_str else []
                
                matches.append({
                    "job_id": metadata.get("id"),
                    "title": metadata.get("title"),
                    "category": metadata.get("category"),
                    "level": metadata.get("level"),
                    "match_score": score,
                    "required_skills": req_skills
                })
        
        # Sort manually descending to be absolutely sure
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)
        
    except Exception as e:
        print(f"Error querying ChromaDB: {e}")
        return []

# Legacy method wrapper to keep the celery task from crashing until it's updated
def match(resume_id: str, target_role: Optional[str] = None) -> Dict[str, Any]:
    """
    Legacy queue wrapper that reads the raw resume text from Redis by ID, 
    and passes it directly over to the underlying synchronous `match_jobs` function.
    """
    # We will fetch the resume text from redis to preserve the celery task signature temporarily
    try:
        resume_data_str = redis_client.get(f"resume:{resume_id}")
        if resume_data_str:
            text = json.loads(resume_data_str).get("text", "")
            return {"matched_jobs": match_jobs(text)}
    except Exception:
        pass
    return {"matched_jobs": [], "error": "Could not fetch resume text"}

def cosine_similarity(a: list, b: list) -> float:
    """Calculates the cosine similarity bounded between 0.0 and 1.0 for two numeric embedding vectors."""
    import numpy as np
    a, b = np.array(a), np.array(b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def analyze_skill_gap(resume_skills: list, job_role: str) -> dict:
    """
    Compares extracted candidate skills against a specific job role's required
    skills using dense embeddings and cosine similarity scoring. Returns the overlap.
    """
    import os
    from fastapi import HTTPException
    
    # 1. Load job from jobs.json
    jobs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs_dataset", "jobs.json")
    try:
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="jobs.json not found")
        
    job = next((j for j in jobs if j["title"].lower() == job_role.lower()), None)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job role '{job_role}' not found in database.")
        
    required_skills = job.get("required_skills", [])
    
    # 3. For each required skill, check if it's covered by resume_skills
    matched_skills = []
    missing_skills = []
    partial_matches = []
    
    # Pre-compute resume skill embeddings
    resume_skill_embs = []
    for rs in resume_skills:
        resume_skill_embs.append({
            "skill": rs,
            "emb": embedding_service.generate_embedding(rs)
        })
        
    for req_skill in required_skills:
        req_lower = req_skill.lower()
        exact_match = next((rs for rs in resume_skills if rs.lower() == req_lower), None)
        
        if exact_match:
            matched_skills.append({
                "job_skill": req_skill,
                "resume_skill": exact_match,
                "match_type": "exact",
                "similarity": 1.0
            })
            continue
            
        # Semantic match
        req_emb = embedding_service.generate_embedding(req_skill)
        best_sim = 0.0
        best_rs = None
        
        for r_item in resume_skill_embs:
            sim = cosine_similarity(req_emb, r_item["emb"])
            if sim > best_sim:
                best_sim = sim
                best_rs = r_item["skill"]
                
        if best_sim > 0.75:
            matched_skills.append({
                "job_skill": req_skill,
                "resume_skill": best_rs,
                "match_type": "semantic",
                "similarity": round(best_sim, 2)
            })
        elif best_sim >= 0.5:
            partial_matches.append({
                "job_skill": req_skill,
                "resume_skill": best_rs,
                "similarity": round(best_sim, 2)
            })
            missing_skills.append(req_skill)
        else:
            missing_skills.append(req_skill)
            
    total_req = len(required_skills)
    match_pct = round((len(matched_skills) / total_req) * 100, 1) if total_req > 0 else 100.0
    
    return {
        "job_role": job["title"],
        "total_required": total_req,
        "matched_count": len(matched_skills),
        "match_percentage": match_pct,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "partial_matches": partial_matches
    }
