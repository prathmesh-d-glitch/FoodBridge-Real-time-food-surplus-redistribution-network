import json
import os
import re
from typing import Optional
from shared.config import settings
from shared.logging_setup import setup_logger
from shared.models import PhotoAnalysisResult

logger = setup_logger("vision_service")


def heuristic_fallback_analysis(
    photo_hint: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
) -> PhotoAnalysisResult:
    """Deterministic, rule-based fallback when Gemini API key is absent or unreachable.
    Evaluates text keywords and food indicators to assign realistic categories and safety flags.
    """
    hint = (photo_hint or "").lower()

    if any(k in hint for k in ["bread", "roti", "naan", "bun", "cake", "pastry"]):
        food_type = "Bakery & Breads"
        portions = 30
        shelf_life_hours = 24.0
        safety_flags = ["Keep sealed in dry ambient storage", "Inspect for moisture damage"]
    elif any(k in hint for k in ["fruit", "vegetable", "salad", "apple", "banana"]):
        food_type = "Fresh Produce"
        portions = 25
        shelf_life_hours = 36.0
        safety_flags = ["Wash thoroughly before consumption", "Discard bruised items"]
    elif any(k in hint for k in ["milk", "paneer", "yogurt", "curd", "cheese"]):
        food_type = "Dairy Products"
        portions = 20
        shelf_life_hours = 8.0
        safety_flags = ["Maintain refrigerated below 5°C", "Perform sniff/curdle test"]
    elif any(k in hint for k in ["sweet", "dessert", "gulab jamun", "halwa", "kheer"]):
        food_type = "Sweets & Desserts"
        portions = 40
        shelf_life_hours = 12.0
        safety_flags = ["Keep covered", "Consume within 12 hours of preparation"]
    else:
        # Default cooked meals / bulk catering
        food_type = "Cooked Catering Meals (Rice/Curry/Entrees)"
        portions = 45
        shelf_life_hours = 4.0
        safety_flags = [
            "Hot holding verified above 63°C recommended",
            "Consume within 3-4 hours of preparation",
            "Ensure sealed stainless steel or food-grade containers",
        ]

    return PhotoAnalysisResult(
        food_type=food_type,
        estimated_portions=portions,
        shelf_life_hours_hint=shelf_life_hours,
        safety_flags=safety_flags,
        confidence=0.82,
        source="heuristic_fallback",
    )


def analyze_food_photo(
    image_bytes: Optional[bytes] = None,
    photo_url: Optional[str] = None,
    photo_hint: Optional[str] = None,
) -> PhotoAnalysisResult:
    """Analyzes a food surplus photo using Google Gemini API with graceful heuristic fallback."""
    api_key = os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY

    # If no Gemini API key provided, degrade gracefully to rule-based engine
    if not api_key:
        logger.info("No GEMINI_API_KEY detected. Using deterministic rule-based vision engine.")
        return heuristic_fallback_analysis(photo_hint, image_bytes)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            "Analyze this food surplus image for an NGO redistribution platform. "
            "Output strictly valid JSON with the following schema: "
            '{"food_type": string, "estimated_portions": integer, '
            '"shelf_life_hours_hint": float, "safety_flags": [string], "confidence": float}. '
            "Safety flags must highlight any perishable risks, temperature controls, or hygiene cautions. "
            f"User context hint: {photo_hint or 'None'}"
        )

        content_parts = [prompt]
        if image_bytes:
            content_parts.append({
                "mime_type": "image/jpeg",
                "data": image_bytes,
            })

        response = model.generate_content(content_parts)
        text = response.text.strip()

        # Extract JSON from code blocks if present
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
            return heuristic_fallback_analysis(photo_hint, image_bytes)

    except Exception as e:
        logger.error(f"Gemini API invocation failed ({e}); falling back to heuristic engine", exc_info=True)
        return heuristic_fallback_analysis(photo_hint, image_bytes)
