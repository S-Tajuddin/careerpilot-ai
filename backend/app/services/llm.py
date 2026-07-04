"""
CareerPilot AI — LLM Service
Unified interface for Ollama (background) + Gemini Flash (interactive).
Auto-routes based on task type.
"""

import json
from typing import Optional

import httpx

from app.config import settings


class LLMService:
    """
    LLM service with smart routing:
    - Background tasks (scoring, dedup) → Ollama qwen3:8b (free, unlimited, slower)
    - Interactive tasks (resume, cover letter) → Gemini Flash (free, fast, 500 RPD)
    """

    def __init__(self):
        self.ollama_host = settings.ollama_host
        self.ollama_model = settings.ollama_chat_model
        self.gemini_api_key = settings.google_api_key
        self.gemini_model = settings.gemini_model

    # ─── Ollama ──────────────────────────────────────────────────────────────

    async def ollama_generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate text using Ollama qwen3:8b (CPU, background tasks).
        Returns the generated text, or empty string on error.
        """
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()
        except httpx.ConnectError:
            print("Ollama is not running — start with: ollama serve")
            return ""
        except httpx.TimeoutException:
            print("Ollama request timed out (model might be loading)")
            return ""
        except Exception as e:
            print(f"Ollama error: {e}")
            return ""

    async def ollama_chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Chat-style generation using Ollama.
        messages format: [{"role": "system"|"user"|"assistant", "content": "..."}]
        """
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.ollama_host}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "").strip()
        except Exception as e:
            print(f"Ollama chat error: {e}")
            return ""

    # ─── Gemini Flash ────────────────────────────────────────────────────────

    async def gemini_generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """
        Generate text using Gemini Flash API (interactive tasks).
        Fast (~2-3 seconds) but limited to 500 RPD.
        """
        if not self.gemini_api_key:
            print("Gemini API key not configured — falling back to Ollama")
            return await self.ollama_generate(prompt, system, temperature, max_tokens)

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.gemini_api_key)

            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            model = genai.GenerativeModel(
                model_name=self.gemini_model,
                system_instruction=system,
                generation_config=generation_config,
            )

            response = model.generate_content(prompt)
            return response.text.strip() if response.text else ""

        except Exception as e:
            print(f"Gemini error: {e} — falling back to Ollama")
            return await self.ollama_generate(prompt, system, temperature, max_tokens)

    # ─── Smart Routing ───────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        task_type: str = "background",  # "background" or "interactive"
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> tuple[str, str]:
        """
        Smart LLM routing:
        - background tasks → Ollama (free, unlimited)
        - interactive tasks → Gemini Flash (fast, 500 RPD)
        
        Returns: (generated_text, model_used)
        """
        if settings.llm_provider == "auto":
            if task_type == "interactive":
                text = await self.gemini_generate(prompt, system, temperature, max_tokens)
                model_used = f"gemini:{self.gemini_model}"
                if not text:
                    # Gemini failed, fallback to Ollama
                    text = await self.ollama_generate(prompt, system, temperature, max_tokens)
                    model_used = f"ollama:{self.ollama_model}"
            else:
                text = await self.ollama_generate(prompt, system, temperature, max_tokens)
                model_used = f"ollama:{self.ollama_model}"
        elif settings.llm_provider == "gemini":
            text = await self.gemini_generate(prompt, system, temperature, max_tokens)
            model_used = f"gemini:{self.gemini_model}"
        else:
            text = await self.ollama_generate(prompt, system, temperature, max_tokens)
            model_used = f"ollama:{self.ollama_model}"

        return text, model_used

    # ─── Ollama Status ──────────────────────────────────────────────────────

    async def get_ollama_status(self) -> dict:
        """Check Ollama status and loaded models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.ollama_host}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    return {
                        "status": "running",
                        "models": [
                            {
                                "name": m.get("name", "unknown"),
                                "size_mb": round(m.get("size", 0) / 1024 / 1024),
                            }
                            for m in models
                        ],
                    }
                return {"status": "error", "code": resp.status_code}
        except httpx.ConnectError:
            return {"status": "offline", "hint": "Start Ollama: ollama serve"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}


# Singleton
llm_service = LLMService()
