import random
from datetime import datetime, timezone
from locust import HttpUser, between, task


class FoodBridgeUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_public_listings(self):
        """Browses available surplus listings."""
        self.client.get("/listings?status=available", name="/listings?status=available")

    @task(2)
    def view_impact_counters(self):
        """Simulates public impact counter requests."""
        # Query impact endpoint
        self.client.get("http://localhost:8005/analytics/impact", name="/analytics/impact")

    @task(1)
    def donor_posts_surplus(self):
        """Simulates commercial donor posting catering surplus."""
        categories = ["cooked_meals", "bakery_bread", "desserts"]
        storages = ["hot_hold", "ambient", "chilled"]
        now = datetime.now(timezone.utc)

        payload = {
            "title": f"Load Test Surplus #{random.randint(100, 999)}",
            "description": "Simulated banquet buffet surplus batch.",
            "category": random.choice(categories),
            "storage_condition": random.choice(storages),
            "dietary_type": "veg",
            "quantity_kg": round(random.uniform(10.0, 50.0), 1),
            "portions": random.randint(30, 150),
            "prepared_at": now.isoformat(),
            "location": {
                "latitude": 12.9716 + random.uniform(-0.05, 0.05),
                "longitude": 77.5946 + random.uniform(-0.05, 0.05),
                "address": "Bangalore Commercial Zone",
            },
        }

        self.client.post(
            "/listings",
            json=payload,
            headers={"Authorization": "Bearer mock-donor-token"},
            name="/listings (create)",
        )

    @task(2)
    def ngo_polls_offers(self):
        """Simulates NGO checking active match offers."""
        self.client.get(
            "http://localhost:8002/offers/ngo/ngo_robin_hood",
            name="/offers/ngo/{id}",
        )
