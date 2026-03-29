import os
import json
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)


def _normalize_model_name(model_name: str) -> str:
    value = (model_name or "").strip()
    if value.startswith("models/"):
        return value[len("models/"):]
    return value

class LLMProvider:
    def __init__(self):
        raw_provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
        provider_aliases = {
            "google": "gemini",
            "gemeni": "gemini",
        }
        normalized_provider = provider_aliases.get(raw_provider, raw_provider)
        if normalized_provider not in {"gemini", "ollama"}:
            logger.warning(f"Unsupported LLM_PROVIDER '{raw_provider}', defaulting to 'gemini'")
            normalized_provider = "gemini"
        self.provider = normalized_provider
        
        # Ollama (local dev)
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.ollama_timeout_s = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
        
        # Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = _normalize_model_name(os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        fallback_models_raw = os.getenv(
            "GEMINI_FALLBACK_MODELS",
            "gemini-2.0-flash-001,gemini-2.0-flash-lite-001,gemini-2.0-flash-lite",
        )
        self.gemini_fallback_models = [
            _normalize_model_name(m) for m in fallback_models_raw.split(",") if _normalize_model_name(m)
        ]

    async def complete(self, prompt: str, system: str = None) -> str:
        """Route to the configured provider."""
        providers = {
            "gemini": self._gemini,
            "ollama": self._ollama,
        }
        
        primary = providers.get(self.provider, self._gemini)
        
        try:
            logger.info(f"Attempting completion with provider: {self.provider}")
            result = await primary(prompt, system)
            return result
        except Exception as e:
            primary_error = f"{type(e).__name__}: {e}"
            logger.error(f"LLM provider ({self.provider}) failed: {primary_error}")
            raise RuntimeError(f"LLM failed ({self.provider}): {primary_error}")

    async def _gemini(self, prompt: str, system: str = None) -> str:
        if not self.gemini_api_key or self.gemini_api_key in ["YOUR_API_KEY", ""]:
            logger.warning("GEMINI_API_KEY is missing or invalid. Falling back to MOCK mode.")
            return self._get_mock_response(system)

        model_candidates = []
        for model in [self.gemini_model, *self.gemini_fallback_models]:
            if model and model not in model_candidates:
                model_candidates.append(model)
        
        # Build content parts
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system + "\n\n" + prompt}]})
        else:
            contents.append({"role": "user", "parts": [{"text": prompt}]})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            }
        }
        
        # If asking for JSON, enable JSON mode
        wants_json = bool(system) and ("return only valid json" in system.lower() or "you must return only valid json" in system.lower())
        if wants_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        last_error = None
        async with httpx.AsyncClient() as client:
            for model_name in model_candidates:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_api_key}"

                # Small retry loop for bursty 429 responses from Gemini.
                for attempt in range(3):
                    response = await client.post(url, json=payload, timeout=60)
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        status_code = e.response.status_code
                        if status_code == 404:
                            last_error = RuntimeError(
                                f"Gemini model '{model_name}' not found or not available for this key."
                            )
                            logger.warning(str(last_error))
                            break
                        if status_code == 429 and attempt < 2:
                            retry_after = e.response.headers.get("Retry-After")
                            wait_seconds = 1 + attempt
                            if retry_after and retry_after.isdigit():
                                wait_seconds = min(int(retry_after), 10)
                            await asyncio.sleep(wait_seconds)
                            continue
                        if status_code == 429:
                            last_error = RuntimeError(
                                f"Gemini rate limit or quota exceeded (HTTP 429) on model '{model_name}'. "
                                "Reduce request volume, or check quota/billing for GEMINI_API_KEY."
                            )
                            logger.warning(str(last_error))
                            break
                        raise

                    data = response.json()

                    # Extract text from Gemini response
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise ValueError(f"Gemini returned no candidates: {data}")

                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        raise ValueError(f"Gemini returned no parts: {data}")

                    if model_name != self.gemini_model:
                        logger.info(f"Gemini model fallback used: {model_name}")
                    self.gemini_model = model_name
                    return parts[0].get("text", "")

        if last_error:
            logger.warning(f"Using MOCK DATA because Gemini failed: {last_error}")
            return self._get_mock_response(system)
        
        logger.warning("Using MOCK DATA because Gemini retries exhausted.")
        return self._get_mock_response(system)

    def _get_mock_response(self, system: str = None) -> str:
        """Returns dummy data if the API key is missing or invalid."""
        sys_lower = (system or "").lower()
        if "resume coach" in sys_lower:
            return json.dumps({
                "overall_score": 7,
                "summary": "Mock Analysis: Your resume has good foundation but needs more quantified achievements.",
                "suggestions": [
                    {
                        "category": "achievements",
                        "priority": "high",
                        "issue": "Missing metrics",
                        "fix": "Add numbers to demonstrate scale.",
                        "example": "Led team of 5 -> Spearheaded cross-functional team of 5 engineers"
                    }
                ],
                "ats_tips": ["Use standard formatting", "Include target keywords"],
                "strengths": ["Clear structure", "Relevant experience"]
            })
        elif "resume parser" in sys_lower:
            return json.dumps({
                "technical_skills": ["Mocking", "Debugging"],
                "programming_languages": ["Python", "JavaScript"],
                "frameworks_tools": ["React", "FastAPI"],
                "soft_skills": ["Problem Solving"],
                "experience_years": 3,
                "education": None
            })
        elif "resume writer" in sys_lower:
            return json.dumps({
                "original": "Did some coding.",
                "improved": "Engineered scalable web applications resulting in 20% faster load times.",
                "reasoning": "Added action verbs and measurable impact."
            })
        elif "course recommendation" in sys_lower:
            return json.dumps({
                "learning_path": {
                    "beginner": [
                        {"title": "Intro to Target Role", "url": "https://coursera.org", "reason": "Foundational"}
                    ],
                    "advanced": [
                        {"title": "Advanced System Design", "url": "https://udemy.com", "reason": "Next step up"}
                    ]
                }
            })
        
        # Default JSON fallback
        return '{"message": "Mock response"}'

    async def _ollama(self, prompt: str, system: str = None) -> str:
        url = f"{self.ollama_base_url}/api/generate"
        wants_json = bool(system) and ("return only valid json" in system.lower() or "you must return only valid json" in system.lower())
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 512 if wants_json else 32,
                "temperature": 0.2,
            },
        }
        if system:
            payload["system"] = system
        if wants_json:
            payload["format"] = "json"
            
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=self.ollama_timeout_s)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def extract_json(self, prompt: str, system: str = None) -> dict:
        """Force the LLM to return JSON and parse it."""
        json_instruction = "\n\nYou MUST return ONLY valid JSON. Do not include any explanation or conversational text. Your response should start with '{' and end with '}'."
        full_system = (system or "") + json_instruction
        
        # Retry logic for JSON parsing
        for attempt in range(2):
            result = await self.complete(prompt, system=full_system)
            
            # Clean up markdown code blocks if present
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
                
            result = result.strip()
            
            try:
                return json.loads(result)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode failed on attempt {attempt + 1}: {e}\nRaw output: {result}")
                if attempt == 1:
                    raise ValueError(f"Failed to parse LLM output as JSON after 2 attempts: {e}")

# Export singleton
llm = LLMProvider()
