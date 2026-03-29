import spacy
from spacy.matcher import PhraseMatcher
from typing import Dict, List, Any

# Adjust path import if needed for the flat module structure
try:
    from utils.data_loader import get_all_technical_skills, get_all_soft_skills
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from utils.data_loader import get_all_technical_skills, get_all_soft_skills


class SkillExtractor:
    """
    V2 Skill Extractor using spaCy PhraseMatcher.
    Extracts and categorizes technical and soft skills directly from text based on
    the predefined skills database.
    """
    
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
        # We use attr="LOWER" for case-insensitive matching
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Load skills from data_loader
        self.technical_skills = get_all_technical_skills()
        self.soft_skills = get_all_soft_skills()
        
        # Create dictionaries for fast exact-case lookup later
        self._tech_map = {skill.lower(): skill for skill in self.technical_skills}
        self._soft_map = {skill.lower(): skill for skill in self.soft_skills}
        
        # Add patterns to matcher
        # To avoid adding excessive overhead, we limit phrase length if necessary,
        # but typical skills are 1-3 words.
        tech_patterns = list(self.nlp.tokenizer.pipe(self.technical_skills))
        self.matcher.add("TECHNICAL", tech_patterns)
        
        soft_patterns = list(self.nlp.tokenizer.pipe(self.soft_skills))
        self.matcher.add("SOFT", soft_patterns)


    def extract_skills_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts technical and soft skills from the provided text using spaCy.

        Args:
            text (str): The raw resume or job description text.

        Returns:
            dict: {
                "technical_skills": [...],
                "soft_skills": [...],
                "all_skills": [...]
            }
        """
        if not text or not text.strip():
            return {
                "technical_skills": [],
                "soft_skills": [],
                "all_skills": []
            }

        # Process text
        # If text is extremely large, might need to truncate (spaCy default limit is 1,000,000 chars)
        max_length = 1000000
        doc = self.nlp(text[:max_length])
        matches = self.matcher(doc)
        
        found_technical = set()
        found_soft = set()
        
        for match_id, start, end in matches:
            string_id = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            matched_text = span.text.lower().strip()
            
            if string_id == "TECHNICAL":
                # Find original casing from the mapping
                original_case = self._tech_map.get(matched_text)
                if original_case:
                    found_technical.add(original_case)
                    
            elif string_id == "SOFT":
                original_case = self._soft_map.get(matched_text)
                if original_case:
                    found_soft.add(original_case)
                    
        tech_list = sorted(list(found_technical))
        soft_list = sorted(list(found_soft))
        
        return {
            "technical_skills": tech_list,
            "soft_skills": soft_list,
            "all_skills": sorted(list(found_technical.union(found_soft)))
        }

