import asyncio
from services.llm_provider import llm

async def extract_skills(resume_text: str) -> dict:
    """
    Extracts structured skills from text using the unified LLM provider.
    """
    system = """You are a resume parser. Extract skills from resume text.
Return ONLY valid JSON, no markdown, no explanation.
JSON shape: {
  "technical_skills": [...],
  "programming_languages": [...],
  "frameworks_tools": [...],
  "soft_skills": [...],
  "experience_years": number or null,
  "education": { "degree": str, "field": str, "institution": str } or null
}
Be precise. Do not invent skills not mentioned. Normalize: "ML" -> "Machine Learning", "JS" -> "JavaScript"."""
    
    prompt = f"Extract skills from this resume:\n\n{resume_text[:3000]}"
    
    try:
        result = await llm.extract_json(prompt, system)
        
        if not isinstance(result, dict):
            result = {}
            
        # Flatten all skill lists into a single deduplicated list
        all_skills = []
        for category in ["technical_skills", "programming_languages", "frameworks_tools", "soft_skills"]:
            skills_list = result.get(category)
            if isinstance(skills_list, list):
                all_skills.extend(skills_list)
                
        # Deduplicate while preserving order
        seen = set()
        flat_all_skills = [x for x in all_skills if not (x in seen or seen.add(x))]
        
        result["all_skills"] = flat_all_skills
        return result
        
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return {
            "technical_skills": [],
            "programming_languages": [],
            "frameworks_tools": [],
            "soft_skills": [],
            "experience_years": None,
            "education": None,
            "all_skills": []
        }
