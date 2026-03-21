import os
import json
import logging
import httpx
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.ollama_timeout_s = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
        
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

    async def complete(self, prompt: str, system: str = None) -> str:
        """Route to primary provider, fallback to secondary if it fails."""
        primary = self._ollama if self.provider == "ollama" else self._openai
        secondary = self._openai if self.provider == "ollama" else self._ollama
        
        try:
            logger.info(f"Attempting completion with primary provider: {primary.__name__}")
            result = await primary(prompt, system)
            return result
        except Exception as e:
            primary_error = f"{type(e).__name__}: {e}"
            logger.warning(
                f"Primary provider ({primary.__name__}) failed: {primary_error}. Falling back to secondary."
            )

            # If the fallback is OpenAI but we don't have a key, don't bother retrying.
            if secondary == self._openai and not self.openai_client:
                raise
            
            # If the fallback is Ollama and we're running with OpenAI as primary,
            # skip it — Ollama won't be available in cloud environments.
            if secondary == self._ollama and self.provider == "openai":
                raise RuntimeError(f"OpenAI failed: {primary_error}")

            try:
                result = await secondary(prompt, system)
                return result
            except Exception as e2:
                logger.error(f"Both LLM providers failed. Secondary error: {type(e2).__name__} {e2!r}")
                raise RuntimeError(f"All LLM providers failed. Last error: {e2}")

    async def _ollama(self, prompt: str, system: str = None) -> str:
        url = f"{self.ollama_base_url}/api/generate"
        wants_json = bool(system) and ("return only valid json" in system.lower() or "you must return only valid json" in system.lower())
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            # Keep local inference bounded so endpoints don't hang indefinitely.
            "options": {
                "num_predict": 512 if wants_json else 32,
                "temperature": 0.2,
            },
        }
        if system:
            payload["system"] = system
        if wants_json:
            # Ollama supports JSON mode for many models; if unsupported it may ignore it.
            payload["format"] = "json"
            
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=self.ollama_timeout_s)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Include body to make debugging Ollama failures feasible.
                logger.warning(f"Ollama HTTP error: {e.response.status_code} body={e.response.text[:500]!r}")
                raise
            data = response.json()
            return data.get("response", "")

    async def _openai(self, prompt: str, system: str = None) -> str:
        if not self.openai_client:
            raise ValueError("OPENAI_API_KEY is not set")
            
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        logger.info(f"Calling OpenAI {self.openai_model}...")
        response = await self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
        )
        return response.choices[0].message.content

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
