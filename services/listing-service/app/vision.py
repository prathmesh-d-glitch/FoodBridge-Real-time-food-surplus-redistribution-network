import json
import os
import re
import base64
import urllib.request
import urllib.error
from typing import Optional
from shared.config import settings
from shared.logging_setup import setup_logger
from shared.models import PhotoAnalysisResult

logger = setup_logger("vision_service")

# Use REST API directly for Gemini models
GEMINI_REST_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MODEL = "gemini-3-flash-preview"


def _call_gemini_rest(api_key: str, prompt: str, image_bytes: Optional[bytes] = None) -> str:
    """Calls Gemini REST API directly. Returns the generated text."""
    url = GEMINI_REST_URL.format(model=GEMINI_MODEL)

    parts = [{"text": prompt}]
    if image_bytes:
        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": b64_data,
            }
        })

    body = json.dumps({
        "contents": [{"parts": parts}]
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    return data["candidates"][0]["content"]["parts"][0]["text"]


def analyze_food_photo(
    image_bytes: Optional[bytes] = None,
    photo_url: Optional[str] = None,
    photo_hint: Optional[str] = None,
) -> Optional[PhotoAnalysisResult]:
    """Analyzes a food surplus photo using Google Gemini.
    Returns None if API key is missing or Gemini call fails — no rule-based fallback.
    """
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY

    if not api_key:
        logger.warning("No GEMINI_API_KEY set. AI analysis disabled.")
        return None

    try:
        prompt = (
            "Analyze this food surplus for an NGO food redistribution platform. "
            "Output ONLY strictly valid JSON with no markdown, no code blocks, no explanation. "
            "Use this exact schema: "
            '{"food_type": "string", "estimated_portions": integer, '
            '"shelf_life_hours_hint": float, "safety_flags": ["string"], "confidence": float}. '
            "confidence must be between 0.0 and 1.0. "
            "safety_flags must highlight perishable risks, temperature controls, or hygiene cautions. "
            f"User context hint: {photo_hint or 'food surplus donation'}"
        )

        text = _call_gemini_rest(api_key, prompt, image_bytes)
        logger.info(f"Gemini raw response: {text[:200]}")

        # Extract JSON — strip markdown code blocks if model wraps in them
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text.strip())

        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            return PhotoAnalysisResult(
                food_type=data.get("food_type", "Prepared Food"),
                estimated_portions=int(data.get("estimated_portions", 30)),
                shelf_life_hours_hint=float(data.get("shelf_life_hours_hint", 4.0)),
                safety_flags=data.get("safety_flags", ["Inspect upon delivery"]),
                confidence=min(1.0, max(0.1, float(data.get("confidence", 0.90)))),
                source="gemini",
            )
        else:
            logger.warning(f"Could not parse JSON from Gemini response: {text}")
            return None

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Gemini API HTTP {e.code}: {body[:300]}", exc_info=False)
        return None
    except Exception as e:
        logger.error(f"Gemini API invocation failed: {e}", exc_info=True)
        return None
