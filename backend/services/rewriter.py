import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from services.gemini_client import GeminiClient
    from utils.data_loader import get_action_verbs
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from services.gemini_client import GeminiClient
    from utils.data_loader import get_action_verbs

class Rewriter:
    """
    Combines LLM and rule-based strategies to optimize resume bullets.
    """
    
    def __init__(self):
        self.gemini = GeminiClient()
        verbs_data = get_action_verbs()
        
        # Pre-load strong verbs for fast O(1) checking
        self.strong_verbs = set()
        for category, verbs in verbs_data.get("strong_verbs", {}).items():
            self.strong_verbs.update([v.lower() for v in verbs])
            
        self.weak_verbs = set([v.lower() for v in verbs_data.get("weak_verbs", [])])
        
        # Normalizing replacements explicitly to lowercase for searching
        self.replacements = { k.lower(): v for k, v in verbs_data.get("replacements", {}).items() }

    def rewrite_bullet(self, bullet: str) -> str:
        """
        Executes the 4-stage rewriting pipeline safely.
        """
        if not bullet or not bullet.strip():
            return bullet
            
        cleaned_bullet = bullet.strip()
        
        # Stage 1: Pre-check
        if self._is_already_strong(cleaned_bullet):
            return cleaned_bullet
            
        # Stage 2: LLM Call
        rewritten = self.gemini.rewrite_bullet(cleaned_bullet)
        
        # Stage 3: Validation
        if self._is_valid_rewrite(cleaned_bullet, rewritten):
            return rewritten
            
        # Stage 4: Rule-based fallback if LLM failed validation or timing out
        return self._rule_based_fallback(cleaned_bullet)

    def rewrite_bullets_batch(self, bullets: List[str]) -> List[str]:
        """
        Processes an array of bullets, keeping strong ones intact while routing weak ones to batch LLM.
        """
        if not bullets:
            return []
            
        final_bullets = [b for b in bullets]
        # Identify weak targets
        indices_to_rewrite = []
        weak_bullets = []
        
        for i, b in enumerate(bullets):
            clean = b.strip()
            if clean and not self._is_already_strong(clean):
                indices_to_rewrite.append(i)
                weak_bullets.append(clean)
                
        if not weak_bullets:
            return final_bullets
            
        # Call batch AI
        rewritten_weak = self.gemini.rewrite_bullets_batch(weak_bullets)
        
        # Merge back with validation & specific error handling
        for idx, orig_idx in enumerate(indices_to_rewrite):
            orig_bullet = weak_bullets[idx]
            proposed = rewritten_weak[idx]
            
            if self._is_valid_rewrite(orig_bullet, proposed):
                final_bullets[orig_idx] = proposed
            else:
                final_bullets[orig_idx] = self._rule_based_fallback(orig_bullet)
                
        return final_bullets

    def _is_already_strong(self, bullet: str) -> bool:
        """
        A bullet is strong if it starts with a strong action verb AND contains quantifiable metrics.
        """
        words = [w.strip() for w in re.split(r'\W+', bullet) if w.strip()]
        if not words:
            return False
            
        first_word = words[0].lower()
        has_strong_start = first_word in self.strong_verbs
        
        # Allow up to third word to be the verb (e.g. "Successfully designed")
        if not has_strong_start and len(words) > 1 and words[1].lower() in self.strong_verbs:
            has_strong_start = True
            
        has_metrics = bool(re.search(r"\d+|\%", bullet))
        
        # It's strong enough to keep originally to lower Gemini costs and save time
        return has_strong_start and has_metrics

    def _is_valid_rewrite(self, original: str, rewritten: str) -> bool:
        """
        Guards against LLM hallucinations, conversational boundaries, or empty results.
        """
        if not rewritten or rewritten == original:
            return False
            
        # Penalize if it's too suspiciously long (e.g., LLM explained the rewrite instead of doing it)
        if len(rewritten) > max(len(original) * 3, 250):
            return False
            
        # Penalize if conversational conversational prefixes appear
        lower_r = rewritten.lower()
        conversational_flags = [
            "here is a rewrite", "here's the rewritten", "sure,", "okay,", 
            "i rewrote", "the stronger version"
        ]
        if any(lower_r.startswith(flag) for flag in conversational_flags):
            return False
            
        return True

    def _rule_based_fallback(self, bullet: str) -> str:
        """
        Safest execution tier. Brute-replaces weak verbs matched from the JSON replacement dictionary.
        """
        fallback_target = bullet
        lower_bullet = bullet.lower()
        
        # Check mapping replacement phrases
        for weak_phrase, strong_verb_options in self.replacements.items():
            if lower_bullet.startswith(weak_phrase):
                # Apply replacement retaining capitals. Handling if dataset provides a list.
                strong_verb = strong_verb_options[0] if isinstance(strong_verb_options, list) else strong_verb_options
                return str(strong_verb).capitalize() + fallback_target[len(weak_phrase):]
                
        # Fallback to single word check
        words = [w.strip() for w in re.split(r'\W+', fallback_target) if w.strip()]
        if words and words[0].lower() in self.weak_verbs:
            # We don't magically know the strong equivalent if it's not mapped,
            # but we can try to find a mapping recursively, otherwise return the original.
            pass
            
        return fallback_target

