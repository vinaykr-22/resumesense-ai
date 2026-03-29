import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from utils.data_loader import get_courses_for_skill, get_certifications_for_category
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from utils.data_loader import get_courses_for_skill, get_certifications_for_category


class CourseRecommender:
    """
    Synthesizes missing skills into an actionable, phased learning roadmap.
    Utilizes V2 data mappings to serve direct course links and certifications.
    """

    def __init__(self):
        # A static heuristic logic for foundational vs advanced categorization.
        # In a real heavy-weight app, this would query a graph DB for dependency linking.
        self.foundational_skills = {
            "python", "javascript", "java", "c++", "c#", "ruby", "go",
            "sql", "mysql", "postgresql", "html", "css", "git", "linux",
            "communication", "teamwork", "problem solving"
        }

    def generate_learning_path(self, missing_skills: List[str], target_role: str = "") -> Dict[str, Any]:
        """
        Takes the skill gaps and outputs a detailed, skill-specific learning roadmap.
        Each skill gets a tiered roadmap from beginner to mastery.
        """
        if not missing_skills:
            return {
                "skill_roadmaps": []
            }

        skill_roadmaps = []
        
        for skill in missing_skills:
            beg_courses = get_courses_for_skill(skill, level="beginner")
            int_courses = get_courses_for_skill(skill, level="intermediate")
            adv_courses = get_courses_for_skill(skill, level="advanced")
            
            # Use general courses if no specific tiers exist (fallback)
            if not beg_courses and not int_courses and not adv_courses:
                beg_courses = get_courses_for_skill(skill, level="all")
            
            # If STILL no courses found, generate dynamic search URLs
            # so every skill always gets recommendations
            if not beg_courses and not int_courses and not adv_courses:
                import urllib.parse
                q = urllib.parse.quote_plus(skill)
                beg_courses = [
                    {
                        "title": f"Learn {skill} – Beginner Courses",
                        "provider": "Coursera",
                        "url": f"https://www.coursera.org/search?query={q}",
                        "duration_hours": None
                    },
                    {
                        "title": f"{skill} for Beginners",
                        "provider": "Udemy",
                        "url": f"https://www.udemy.com/courses/search/?q={q}",
                        "duration_hours": None
                    },
                    {
                        "title": f"{skill} Tutorials & Articles",
                        "provider": "GeeksforGeeks",
                        "url": f"https://www.geeksforgeeks.org/search/{q}/",
                        "duration_hours": None
                    }
                ]
                int_courses = [
                    {
                        "title": f"{skill} – Intermediate & Projects",
                        "provider": "YouTube",
                        "url": f"https://www.youtube.com/results?search_query={q}+tutorial",
                        "duration_hours": None
                    },
                    {
                        "title": f"{skill} Hands-On Learning",
                        "provider": "freeCodeCamp",
                        "url": f"https://www.freecodecamp.org/news/search/?query={q}",
                        "duration_hours": None
                    }
                ]
                adv_courses = [
                    {
                        "title": f"Advanced {skill} – Deep Dive",
                        "provider": "Pluralsight",
                        "url": f"https://www.pluralsight.com/search?q={q}",
                        "duration_hours": None
                    }
                ]

            certifications_list = []
            certs = get_certifications_for_category(skill)
            if certs:
                for c in certs:
                    if isinstance(c, dict):
                        certifications_list.append({
                            "name": c.get("name", "Unknown Certification"),
                            "url": c.get("url", "#"),
                            "provider": c.get("provider", "Unknown")
                        })
                    elif isinstance(c, str):
                        certifications_list.append({
                            "name": c,
                            "url": "#",
                            "provider": "Unknown"
                        })

            skill_roadmaps.append({
                "skill": skill,
                "beginner": beg_courses,
                "intermediate": int_courses,
                "advanced": adv_courses,
                "certifications": certifications_list
            })

        return {
            "skill_roadmaps": skill_roadmaps
        }

