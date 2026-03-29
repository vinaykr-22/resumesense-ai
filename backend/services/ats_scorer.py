import re
from typing import List, Dict, Any, Optional

try:
    from utils.data_loader import get_action_verbs
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from utils.data_loader import get_action_verbs

try:
    from models.schemas import ATSScoreBreakdown
except ImportError:
    # Fallback structure if schemas aren't loaded correctly in standalone testing
    class ATSScoreBreakdown:
        def __init__(self, keyword_score=0.0, section_completeness=0.0, bullet_strength=0.0, formatting_score=0.0):
            self.keyword_score = keyword_score
            self.section_completeness = section_completeness
            self.bullet_strength = bullet_strength
            self.formatting_score = formatting_score


class ATSScorer:
    """
    Calculates an ATS compatibility score based on 4 rubrics:
    - Keywords (40 points)
    - Section completeness (30 points)
    - Bullet strength (20 points)
    - Formatting (10 points)
    """

    def __init__(self):
        # Load strong verbs dynamically
        verbs_data = get_action_verbs()
        self.strong_verbs = set()
        for category, verbs in verbs_data.get("strong_verbs", {}).items():
            self.strong_verbs.update([v.lower() for v in verbs])

        self.weak_verbs = set([v.lower() for v in verbs_data.get("weak_verbs", [])])

    def score_resume(self, text: str, extracted_skills: List[str], target_skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Main scoring function returning a breakdown and total score.
        """
        if not text:
            return {
                "total_score": 0.0,
                "breakdown": ATSScoreBreakdown().dict() if hasattr(ATSScoreBreakdown, "dict") else ATSScoreBreakdown().__dict__
            }

        keyword_score = self._score_keywords(extracted_skills, target_skills)
        section_score = self._score_sections(text)
        bullet_score = self._score_bullets(text)
        formatting_score = self._score_formatting(text)

        total_score = round(keyword_score + section_score + bullet_score + formatting_score, 1)

        breakdown = {
            "keyword_score": round(keyword_score, 1),
            "section_completeness": round(section_score, 1),
            "bullet_strength": round(bullet_score, 1),
            "formatting_score": round(formatting_score, 1)
        }

        # Keep output strictly compatible with the V2 ATSScoreBreakdown model format
        return {
            "total_score": total_score,
            "breakdown": breakdown
        }

    def _score_keywords(self, extracted_skills: List[str], target_skills: Optional[List[str]]) -> float:
        """Max 40 points."""
        if not extracted_skills:
            return 0.0

        if target_skills:
            # Score based on overlap with target skills
            target_set = {s.lower() for s in target_skills}
            extracted_set = {s.lower() for s in extracted_skills}
            overlap = target_set.intersection(extracted_set)
            
            if not target_set:
                return 40.0
                
            coverage_ratio = len(overlap) / len(target_set)
            return min(40.0, coverage_ratio * 40.0)
        else:
            # Asses based on a baseline count (assuming 15 dense technical/soft skills is excellent)
            skill_count = len(extracted_skills)
            score = (skill_count / 15.0) * 40.0
            return min(40.0, score)

    def _score_sections(self, text: str) -> float:
        """
        Max 30 points. Looks for 4 primary structural sections.
        """
        score = 0.0
        lower_text = "\n" + text.lower() + "\n"

        # Look for headers. Using liberal boundaries to handle both raw text and newlines.
        patterns = {
            "education": r"\n\s*(education|academic background|studies)\b",
            "experience": r"\n\s*(experience|work history|employment|professional experience)\b",
            "skills": r"\n\s*(skills|technical skills|core competencies)\b",
            "summary": r"\n\s*(summary|profile|objective|about me)\b"
        }

        points_per_section = 30.0 / len(patterns)  # 7.5 per section
        
        for key, pattern in patterns.items():
            if re.search(pattern, lower_text):
                score += points_per_section

        return min(30.0, score)

    def _score_bullets(self, text: str) -> float:
        """
        Max 20 points. Evaluates bullet points for strong action verbs and quantified metrics.
        """
        bullets = self._extract_bullet_lines(text)
        if not bullets:
            return 0.0  # No bullets found = 0 on this scale.

        strong_verb_count = 0
        quantified_count = 0

        for bullet in bullets:
            # Check for numbers or percentages
            if re.search(r"\d+|\%", bullet):
                quantified_count += 1
                
            # Check for strong verb initiating the bullet (simplistic check on first few words)
            words = [w.strip() for w in re.split(r'\W+', bullet) if w.strip()]
            if words:
                first_word = words[0].lower()
                if first_word in self.strong_verbs and first_word not in self.weak_verbs:
                    strong_verb_count += 1
                # Check up to third word incase of 'Successfully developed' etc
                elif len(words) > 1 and words[1].lower() in self.strong_verbs:
                    strong_verb_count += 1

        strong_verb_ratio = strong_verb_count / len(bullets)
        quantified_ratio = quantified_count / len(bullets)

        # 10 points for strong verbs, 10 points for metrics
        verb_score = min(10.0, (strong_verb_ratio / 0.7) * 10.0)  # capped at 70% strong verbs
        metrics_score = min(10.0, (quantified_ratio / 0.4) * 10.0) # capped at 40% quantified bullets

        return verb_score + metrics_score

    def _score_formatting(self, text: str) -> float:
        """
        Max 10 points. Checks overall length and bullet lengths.
        """
        score = 0.0
        text_len = len(text)
        
        # Overall length (5 points)
        # Ideally 1-2 pages (approx 1000 - 8000 chars)
        if 1000 <= text_len <= 8000:
            score += 5.0
        elif 600 <= text_len <= 10000:
            score += 3.0
            
        # Bullet readability (5 points)
        bullets = self._extract_bullet_lines(text)
        if bullets:
            avg_len = sum(len(b) for b in bullets) / len(bullets)
            # Ideal bullet is 50-250 characters (1-2 lines)
            if 50 <= avg_len <= 250:
                score += 5.0
            elif 30 <= avg_len <= 400:
                score += 2.5
        else:
            # Without bullets, they miss these 5 points
            score += 0.0

        return score

    def _extract_bullet_lines(self, text: str) -> List[str]:
        """Extracts lines that resemble bullet points."""
        bullets = []
        lines = text.split("\n")
        # Matches common bullet chars: -, *, •, or alphanumeric lists like 1., a)
        bullet_pattern = r"^\s*([\-\*\•\>]|\d+\.|\w\))\s+(.+)"
        
        for line in lines:
            match = re.match(bullet_pattern, line)
            if match:
                bullets.append(match.group(2).strip())
                
        return bullets

