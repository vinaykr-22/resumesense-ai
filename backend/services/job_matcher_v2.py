import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

try:
    from services.skill_extractor_v2 import SkillExtractor
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from services.skill_extractor_v2 import SkillExtractor


class JobMatcher:
    """
    Dynamically compares candidate skills against raw Job Description (JD) text
    to compute an exact match percentage and identify precise skill gaps.
    """
    
    def __init__(self):
        # We reuse the robust SkillExtractor to parse raw JD strings
        self.extractor = SkillExtractor()

    def extract_jd_skills(self, jd_text: str) -> List[str]:
        """
        Parses raw job description text to find what skills the employer actually requires.
        """
        if not jd_text or not jd_text.strip():
            return []
            
        extracted = self.extractor.extract_skills_from_text(jd_text)
        return extracted.get("all_skills", [])

    def match_resume_to_jd(self, resume_skills: List[str], jd_text: str) -> Dict[str, Any]:
        """
        Computes the match percentage and skill gaps based on the required JD skills.
        
        Args:
            resume_skills: List of skills the candidate possesses.
            jd_text: Raw string pasted from a job board.
            
        Returns:
            Dict containing match_percentage, matched_skills, and missing_skills.
        """
        # 1. Parse JD dynamically
        required_skills = self.extract_jd_skills(jd_text)
        
        # Guard clause for empty JDs or unrecognizable JD skills
        if not required_skills:
            return {
                "match_percentage": 0.0,
                "matched_skills": [],
                "missing_skills": []
            }
            
        # 2. Case-insensitive comparison
        resume_set_lower = {s.lower() for s in resume_skills}
        
        matched = []
        missing = []
        
        for req_skill in required_skills:
            if req_skill.lower() in resume_set_lower:
                matched.append(req_skill)
            else:
                missing.append(req_skill)
                
        # 3. Compute 0.0 to 100.0 score safely
        total_req = len(required_skills)
        match_pct = round((len(matched) / total_req) * 100, 1) if total_req > 0 else 0.0
        
        return {
            "match_percentage": match_pct,
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing)
        }

