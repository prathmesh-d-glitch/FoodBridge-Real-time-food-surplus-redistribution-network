import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

# Base URLs
LISTING_URL = "http://localhost:8001"
MATCHING_URL = "http://localhost:8002"
LOGISTICS_URL = "http://localhost:8004"
ANALYTICS_URL = "http://localhost:8005"


def run_scenario(scenario_path: Path, speed_multiplier: float = 1.0):
    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    print("==================================================================")
    print(f"      FOODBRIDGE SCENARIO SIMULATOR: {scenario['scenario_name'].upper()}")
    print(f"      Description: {scenario.get('description')}")
    print(f"      Speed Multiplier: {speed_multiplier}x")
    print("==================================================================\n")

    created_listings = []
    created_offers = []

    for idx, ev in enumerate(scenario.get("events", [])):
        delay = ev.get("delay_seconds", 1) / max(0.1, speed_multiplier)
        time.sleep(delay)

        event_type = ev.get("event_type")
        data = ev.get("data", {})
        now = datetime.now(timezone.utc)

        if event_type == "post_listing":
            prep_mins = data.get("prepared_minutes_ago", 30)
            payload = {
                "title": data.get("title"),
                "description": data.get("description"),
                "category": data.get("category", "cooked_meals"),
                "storage_condition": data.get("storage_condition", "hot_hold"),
                "dietary_type": data.get("dietary_type", "veg"),
                "quantity_kg": float(data.get("quantity_kg", 25.0)),
                "portions": int(data.get("portions", 80)),
                "prepared_at": (now - timedelta(minutes=prep_mins)).isoformat(),
                "location": data.get("location", {"latitude": 12.9716, "longitude": 77.5946}),
            }

            try:
                res = requests.post(
                    f"{LISTING_URL}/listings",
                    json=payload,
                    headers={"Authorization": "Bearer mock-donor-token"},
                    timeout=5,
                )
                if res.status_code == 201:
                    listing_obj = res.json()
                    created_listings.append(listing_obj)
                    print(
                        f"  [DONOR POST] {listing_obj['title']} "
                        f"({listing_obj['portions']} portions, {listing_obj['quantity_kg']}kg) "
                        f"-> safe_until: {listing_obj['safe_until'][11:19]}"
                    )
                else:
                    print(f"  [ERROR] Posting listing failed: {res.text}")
            except Exception as e:
                print(f"  [ERROR] Listing service connection error: {e}")

        elif event_type == "simulate_ngo_response":
            ngo_id = ev.get("target_ngo", "ngo_robin_hood")
            action = ev.get("action", "accept")
            try:
                # Find pending offer for this NGO
                res = requests.get(f"{MATCHING_URL}/offers/ngo/{ngo_id}", timeout=5)
                offers = res.json() if res.status_code == 200 else []
                open_offers = [o for o in offers if o.get("status") == "offered"]

                if open_offers:
                    target_offer = open_offers[0]
                    offer_id = target_offer["id"]
                    if action == "accept":
                        acc_res = requests.post(
                            f"{MATCHING_URL}/offers/{offer_id}/accept",
                            headers={"Authorization": f"mock:ngo:{ngo_id}:ShelterOps"},
                            timeout=5,
                        )
                        print(f"  [NGO ACCEPT] {ngo_id} ACCEPTED Offer {offer_id} (Score: {target_offer.get('score', 0):.2f})")
                    else:
                        dec_res = requests.post(
                            f"{MATCHING_URL}/offers/{offer_id}/decline",
                            json={"reason": ev.get("reason", "Declined")},
                            headers={"Authorization": f"mock:ngo:{ngo_id}:ShelterOps"},
                            timeout=5,
                        )
                        print(f"  [NGO DECLINE] {ngo_id} DECLINED Offer {offer_id} -> Triggered auto-cascade escalation!")
                else:
                    print(f"  [INFO] No pending offers currently awaiting response for {ngo_id}")
            except Exception as e:
                print(f"  [ERROR] Matching service connection error: {e}")

        elif event_type == "simulate_handover":
            if created_listings:
                latest_listing = created_listings[-1]
                temp = ev.get("temperature_celsius", 66.5)
                try:
                    h_res = requests.post(
                        f"{LOGISTICS_URL}/handovers",
                        json={
                            "listing_id": latest_listing["id"],
                            "donor_id": latest_listing["donor_id"],
                            "ngo_id": "ngo_robin_hood",
                            "temperature_celsius": temp,
                            "notes": ev.get("notes", "Handover inspected"),
                            "is_pickup": False,
                        },
                        headers={"Authorization": "Bearer mock-volunteer-token"},
                        timeout=5,
                    )
                    print(f"  [HANDOVER COMPLETED] Delivered {latest_listing['title']} &bull; Verified Temp: {temp}°C")
                except Exception as e:
                    print(f"  [ERROR] Logistics handover error: {e}")

    # Check live impact metrics after simulation run
    try:
        imp_res = requests.get(f"{ANALYTICS_URL}/analytics/impact", timeout=5)
        if imp_res.status_code == 200:
            imp = imp_res.json()
            print("\n==================================================================")
            print("                 LIVE TELEMETRY AFTER SIMULATION                  ")
            print(f"  Total Meals Saved:     {imp.get('total_meals_saved')} meals")
            print(f"  Total Food Diverted:   {imp.get('total_kg_diverted')} kg")
            print(f"  CO2e Avoided:          {imp.get('total_co2e_avoided_kg')} kg CO2e")
            print(f"  Rescues Completed:     {imp.get('completed_deliveries')}")
            print("==================================================================\n")
    except Exception as e:
        print(f"  Could not fetch live impact: {e}")


def main():
    parser = argparse.ArgumentParser(description="FoodBridge Real-Time Scenario Simulator")
    parser.add_argument("--scenario", default="simulator/scenarios/wedding_rush.json", help="Path to scenario JSON")
    parser.add_argument("--speed", type=float, default=5.0, help="Simulation speed multiplier")
    args = parser.parse_args()

    scenario_file = Path(args.scenario)
    if not scenario_file.exists():
        # check relative to foodbridge
        scenario_file = Path("simulator") / args.scenario
    if not scenario_file.exists():
        print(f"Scenario file not found: {args.scenario}")
        sys.exit(1)

    run_scenario(scenario_file, speed_multiplier=args.speed)


if __name__ == "__main__":
    main()
