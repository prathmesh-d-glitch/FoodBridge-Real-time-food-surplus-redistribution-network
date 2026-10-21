from typing import Any, Dict


def template_match_offered(data: Dict[str, Any]) -> Dict[str, str]:
    timeout_mins = int(data.get("timeout_seconds", 300) / 60)
    return {
        "title": "⚡ Urgent Food Surplus Match Offer",
        "body": (
            f"Match rank #{data.get('rank', 1)}: Surplus food offered to {data.get('ngo_name', 'your organization')}! "
            f"Score: {data.get('score', 0.0):.2f}. Action required within {timeout_mins} minutes."
        ),
        "sms": f"[FoodBridge] Urgent surplus offered to {data.get('ngo_name')}. Respond within {timeout_mins} mins: https://foodbridge.org/offers/{data.get('offer_id')}",
    }


def template_offer_accepted(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        "title": "🎉 Offer Accepted & Volunteer Mobilized",
        "body": (
            f"Listing {data.get('listing_id')} was accepted by {data.get('ngo_id')}. "
            f"{data.get('portions', 'Surplus')} portions secured for redistribution!"
        ),
        "sms": f"[FoodBridge] Offer accepted! {data.get('portions')} portions claimed. Route generation underway.",
    }


def template_route_assigned(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        "title": "🚚 New Volunteer Pickup Route",
        "body": (
            f"You have been assigned route {data.get('route_id')}. "
            f"{data.get('stops_count', 2)} stops planned. Please complete before earliest safety deadline."
        ),
        "sms": f"[FoodBridge] New pickup assigned to volunteer. View your turn-by-turn itinerary: https://foodbridge.org/routes/{data.get('route_id')}",
    }


def template_listing_expired(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        "title": "⚠️ Surplus Listing Expired",
        "body": f"Listing {data.get('listing_id')} reached its safe consumption deadline without pickup.",
        "sms": f"[FoodBridge] Notice: Listing {data.get('listing_id')} reached safety deadline.",
    }


def template_admin_escalation(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        "title": "🚨 System Escalation Alert",
        "body": f"Listing {data.get('listing_id')} could not be matched within safe radius. Admin review requested.",
        "sms": f"[FoodBridge Admin Alert] Listing {data.get('listing_id')} requires manual review.",
    }
