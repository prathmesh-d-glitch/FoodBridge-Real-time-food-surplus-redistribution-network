from app.vision import analyze_food_photo, heuristic_fallback_analysis


def test_heuristic_fallback_bakery():
    result = heuristic_fallback_analysis(photo_hint="Assorted bread and dinner rolls")
    assert result.food_type == "Bakery & Breads"
    assert result.shelf_life_hours_hint >= 24.0
    assert len(result.safety_flags) > 0
    assert result.source == "heuristic_fallback"


def test_heuristic_fallback_produce():
    result = heuristic_fallback_analysis(photo_hint="Fresh crates of fruits and bananas")
    assert result.food_type == "Fresh Produce"
    assert result.confidence > 0.7


def test_heuristic_fallback_cooked_meals():
    result = heuristic_fallback_analysis(photo_hint="Dal tadka and jeera rice")
    assert "Cooked Catering Meals" in result.food_type
    assert result.shelf_life_hours_hint <= 4.0
    assert any("temperature" in flag.lower() or "hot" in flag.lower() for flag in result.safety_flags)


def test_analyze_food_photo_without_key():
    # Without GEMINI_API_KEY, should gracefully degrade without crashing
    result = analyze_food_photo(photo_hint="Vegetable biryani containers")
    assert result is not None
    assert result.estimated_portions > 0
    assert result.shelf_life_hours_hint > 0
