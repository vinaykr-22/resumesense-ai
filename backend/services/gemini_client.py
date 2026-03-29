import os
import time
import json
import logging
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from google.api_core.exceptions import ResourceExhausted, RetryError

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Client for interacting with Gemini 1.5 Flash API for advanced resume processing.
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables.")
            
        genai.configure(api_key=api_key)
        # Using 1.5 Flash latest for fast, cost-effective processing
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
    def generate_summary(self, resume_text: str) -> str:
        """
        Generates a tight, professional 3-4 sentence summary based on the resume text.
        """
        if not resume_text or not resume_text.strip():
            return ""
            
        prompt = f"""
        Based on the following resume text, write a highly professional, compelling 3-4 sentence 
        career summary. Focus on core strengths, major achievements, and the candidate's primary value proposition.
        Do not use first-person pronouns (I, me, my). Make it ATS-friendly.
        
        Resume text:
        {resume_text[:15000]}
        """
        
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            logger.error(f"Error generating summary via Gemini: {str(e)}")
            return ""

    def rewrite_bullet(self, bullet: str) -> str:
        """
        Rewrites a single weak bullet into a more quantifiable, action-oriented phrase.
        """
        if not bullet or not bullet.strip():
            return ""
            
        prompt = f"""
        Rewrite the following resume bullet point to make it much stronger. 
        Start with a powerful action verb. If possible given the context, imply quantifiable impact.
        Keep it to exactly ONE single sentence. Do not add conversational text, just return the bullet point.
        
        Original: {bullet}
        """
        
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                # Clean up any potential markdown bullet characters if Gemini included them
                cleaned = response.text.strip()
                if cleaned.startswith("- "):
                    cleaned = cleaned[2:]
                elif cleaned.startswith("* "):
                    cleaned = cleaned[2:]
                return cleaned.strip()
            return bullet
        except Exception as e:
            logger.error(f"Error rewriting bullet via Gemini: {str(e)}")
            return bullet

    def rewrite_bullets_batch(self, bullets: List[str]) -> List[str]:
        """
        Batch processes a list of bullets using chunking and rate limits.
        Falls back to original bullets on failure to ensure safety.
        """
        if not bullets:
            return []
            
        rewritten = []
        chunk_size = 5 # Process 5 bullets per chunk to stay well within limits context-wise
        
        for i in range(0, len(bullets), chunk_size):
            chunk = bullets[i:i + chunk_size]
            
            # Formulate a JSON prompt to ensure order and exact output matching
            prompt = """
            You are an expert resume writer. Rewrite the following resume bullet points to make them significantly stronger,
            starting with powerful action verbs and sounding highly professional. 
            
            Return the result EXACTLY as a valid JSON array of strings, in the exact same order.
            Do NOT include any markdown formatting like ```json or newlines outside the array. 
            Return ONLY the valid JSON array starting with [ and ending with ].
            
            Original bullets:
            """
            for idx, b in enumerate(chunk):
                prompt += f"\n[{idx}] {b}"
                
            retries = 3
            backoff = 2
            
            for attempt in range(retries):
                try:
                    response = self.model.generate_content(prompt)
                    text = response.text.strip()
                    
                    # Clean markdown if present
                    if text.startswith("```json"):
                        text = text.replace("```json", "", 1)
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                        
                    parsed_chunk = json.loads(text)
                    
                    if isinstance(parsed_chunk, list) and len(parsed_chunk) == len(chunk):
                        rewritten.extend(parsed_chunk)
                        break # Success, break out of retry loop
                    else:
                        raise ValueError("Gemini returned anomalous JSON response length")
                        
                except ResourceExhausted:
                    logger.warning(f"Rate limited by Gemini on chunk {i}. Retrying in {backoff}s...")
                    time.sleep(backoff)
                    backoff *= 2 # Exponential backoff
                except Exception as e:
                    logger.error(f"Failed to process chunk {i} via Gemini: {str(e)}")
                    # On failure, append the original bullets to avoid data loss
                    if attempt == retries - 1:
                        rewritten.extend(chunk)
                    time.sleep(1) # Small sleep before retry just in case it's a transient net issue
            
            # Small rate limiting sleep between chunks to smooth out RPM
            if i + chunk_size < len(bullets):
                time.sleep(1.5)
                
        # Final safety check
        if len(rewritten) != len(bullets):
            logger.error("Length mismatch in batch rewriting. Falling back to originals.")
            return bullets
            
        return rewritten

