"""Shared Google Gemini API client helpers for CyberSahak AI features."""
import logging

from config import Config
from services.ai_provider_errors import AIConfigurationError, AIProviderError

log = logging.getLogger(__name__)


def generate_text(contents, system_instruction, max_output_tokens):
    if not Config.GEMINI_API_KEY:
        raise AIConfigurationError(
            "Gemini is not configured. Add GEMINI_API_KEY to backend/.env and restart the API."
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=max_output_tokens,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise AIProviderError("Gemini returned an empty reply. Please try again.")
        return text
    except AIProviderError:
        raise
    except Exception as error:
        status = getattr(error, "code", None)
        log.warning("Gemini request failed (type=%s, status=%s)", type(error).__name__, status)
        if status == 429:
            raise AIProviderError(
                "Gemini's free-tier quota may be reached. Wait for the quota to reset, then try again."
            ) from error
        if status in (401, 403):
            raise AIProviderError(
                "Gemini rejected the API key or project. Check the key in backend/.env and its AI Studio access."
            ) from error
        raise AIProviderError(
            "Gemini could not complete the request. Check the API key, model access, and internet connection."
        ) from error
