import os
import json
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

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
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        fallback_models_raw = os.getenv(
            "GEMINI_FALLBACK_MODELS",
            "gemini-2.0-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b",
        )
        self.gemini_fallback_models = [m.strip() for m in fallback_models_raw.split(",") if m.strip()]

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
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set")

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
            raise last_error
        raise RuntimeError("Gemini call failed after retries")

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
