"""
V2 Data Loader
==============
Utility to load and cache JSON data files from backend/data/.
Uses functools.lru_cache so each file is read from disk at most once.
"""

import os
import json
from functools import lru_cache
from typing import Dict, Any, List


_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@lru_cache(maxsize=1)
def get_skills_database() -> Dict[str, Any]:
    """Load the comprehensive skills database."""
    return _load_json("skills_database.json")


@lru_cache(maxsize=1)
def get_action_verbs() -> Dict[str, Any]:
    """Load the strong/weak action verbs database."""
    return _load_json("action_verbs.json")


@lru_cache(maxsize=1)
def get_courses_mapping() -> Dict[str, Any]:
    """Load the courses & certifications mapping."""
    return _load_json("courses_mapping.json")


def get_all_technical_skills() -> List[str]:
    """Return a flat, deduplicated list of every technical skill."""
    db = get_skills_database()
    technical = db.get("technical_skills", {})
    skills: List[str] = []
    for category_skills in technical.values():
        if isinstance(category_skills, list):
            skills.extend(category_skills)
    return list(dict.fromkeys(skills))  # dedupe, preserve order


def get_all_soft_skills() -> List[str]:
    """Return the full list of soft skills."""
    db = get_skills_database()
    return db.get("soft_skills", [])


def get_weak_verbs() -> List[str]:
    """Return the list of weak action verbs to flag."""
    verbs = get_action_verbs()
    return verbs.get("weak_verbs", [])


def get_verb_replacements() -> Dict[str, List[str]]:
    """Return weak-verb → strong-verb replacement suggestions."""
    verbs = get_action_verbs()
    return verbs.get("replacements", {})


def get_courses_for_skill(skill: str, level: str = "beginner") -> List[Dict[str, Any]]:
    """Look up course recommendations for a specific skill and level."""
    mapping = get_courses_mapping()
    skills_map = mapping.get("skills", {})
    # case-insensitive lookup
    skill_lower = skill.lower()
    for k, v in skills_map.items():
        if k.lower() == skill_lower:
            return v.get(level, [])
    return []


def get_certifications_for_category(category: str) -> List[Dict[str, Any]]:
    """Look up certifications for a skill category (e.g. 'AWS', 'Kubernetes')."""
    mapping = get_courses_mapping()
    certs_map = mapping.get("certifications", {})
    # case-insensitive lookup
    cat_lower = category.lower()
    for k, v in certs_map.items():
        if k.lower() == cat_lower:
            return v
    return []


# ── internal ───────────────────────────────────

def _load_json(filename: str) -> Dict[str, Any]:
    """Load a JSON file from the data directory."""
    filepath = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
