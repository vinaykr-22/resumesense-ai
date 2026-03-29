import json
import asyncio
import uuid
from dotenv import load_dotenv
load_dotenv('.env')

from tasks.celery_app import _process_resume_sync
from database.redis_client import redis_client

async def test_v2_pipeline():
    print("--- Starting Pipeline Test ---")
    resume_id = f"test_{uuid.uuid4().hex[:6]}"
    text = "Experience: Worked as a software developer using Python. Responsible for database help."
    jd = "Seeking a Senior Python Developer with experience in Docker, AWS, and SQL. Must have leadership skills."
    
    print(f"1. Processing resume {resume_id}...")
    try:
        result = _process_resume_sync(resume_id, text, jd)
        print("Success: Pipeline completed.")
        
        analysis = result.get("analysis_data", {})
        print("\n--- Analysis Data Summary ---")
        print(f"ATS Score: {analysis.get('ats_score')}")
        print(f"Weak Bullets Count: {len(analysis.get('weak_bullets', []))}")
        print(f"Rewritten Bullets Count: {len(analysis.get('rewritten_bullets', []))}")
        print(f"Skills Extracted: {analysis.get('extracted_skills')}")
        print(f"Matched Skills: {analysis.get('job_match_data', {}).get('matched_skills')}")
        print(f"Missing Skills: {analysis.get('job_match_data', {}).get('missing_skills')}")
        print(f"Learning Phase Count: {len(analysis.get('learning_path', {}).get('learning_phases', []))}")
        
        # Verify structure
        assert "ats_score" in analysis
        assert "job_match_data" in analysis
        assert "learning_path" in analysis
        print("\nCheck: Schema structure is CORRECT.")
        
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_v2_pipeline())
