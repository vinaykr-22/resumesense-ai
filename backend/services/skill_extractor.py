import os
import re
import json
from services.llm_provider import llm


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if not item:
            continue
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def _load_job_skill_vocab() -> list[str]:
    jobs_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs_dataset", "jobs.json")
    try:
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        vocab = []
        for job in jobs:
            for skill in job.get("required_skills", []):
                if isinstance(skill, str):
                    vocab.append(skill)
        return _dedupe_preserve_order(vocab)
    except Exception:
        return []


def _rule_based_extract(resume_text: str) -> dict:
    text = (resume_text or "").lower()
    if not text:
        return {
            "technical_skills": [],
            "programming_languages": [],
            "frameworks_tools": [],
            "soft_skills": [],
            "experience_years": None,
            "education": None,
            "all_skills": [],
        }

    common_vocab = [
        "python", "java", "javascript", "typescript", "sql", "c++", "c#", "go", "rust",
        "react", "node.js", "node", "fastapi", "django", "flask", "spring", "docker",
        "kubernetes", "aws", "azure", "gcp", "redis", "postgresql", "mongodb", "git",
        "machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "pandas",
        "numpy", "scikit-learn", "chroma", "chromadb", "llm", "huggingface", "langchain",
        "communication", "leadership", "teamwork", "problem solving", "critical thinking",
    ]
    vocab = _dedupe_preserve_order(common_vocab + _load_job_skill_vocab())

    found = []
    for skill in vocab:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            found.append(skill)

    languages_set = {
        "python", "java", "javascript", "typescript", "sql", "c++", "c#", "go", "rust",
    }
    soft_set = {
        "communication", "leadership", "teamwork", "problem solving", "critical thinking",
    }

    programming_languages = [s for s in found if s.lower() in languages_set]
    soft_skills = [s for s in found if s.lower() in soft_set]
    frameworks_tools = [s for s in found if s not in programming_languages and s not in soft_skills]

    result = {
        "technical_skills": _dedupe_preserve_order(found),
        "programming_languages": _dedupe_preserve_order(programming_languages),
        "frameworks_tools": _dedupe_preserve_order(frameworks_tools),
        "soft_skills": _dedupe_preserve_order(soft_skills),
        "experience_years": None,
        "education": None,
    }
    result["all_skills"] = _dedupe_preserve_order(
        result["technical_skills"]
        + result["programming_languages"]
        + result["frameworks_tools"]
        + result["soft_skills"]
    )
    return result

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
    
    prompt = f"Extract skills from this resume:\n\n{resume_text[:15000]}"
    
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
                
        flat_all_skills = _dedupe_preserve_order([str(x) for x in all_skills if isinstance(x, str)])
        
        result["all_skills"] = flat_all_skills

        # LLM can occasionally return empty/invalid lists; recover with deterministic extraction.
        if not result["all_skills"]:
            return _rule_based_extract(resume_text)
        return result
        
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return _rule_based_extract(resume_text)
