from datetime import datetime, timedelta, timezone
import pytest
from shared.models import GeoPoint, RouteStop
from app.route_optimizer import (
    nearest_neighbor_route,
    two_opt_optimize,
    validate_route_schedule,
)


def test_route_precedence_violation():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    start_pos = GeoPoint(latitude=12.9716, longitude=77.5946)

    # Deliver before pick up
    delivery = RouteStop(
        stop_id="del_1",
        stop_type="delivery",
        listing_id="list_1",
        target_name="Shelter 1",
        location=GeoPoint(latitude=12.9784, longitude=77.6408),
        estimated_arrival=now + timedelta(minutes=30),
        deadline=now + timedelta(hours=3),
    )
    pickup = RouteStop(
        stop_id="pick_1",
        stop_type="pickup",
        listing_id="list_1",
        target_name="Restaurant 1",
        location=GeoPoint(latitude=12.9750, longitude=77.6100),
        estimated_arrival=now + timedelta(minutes=15),
        deadline=now + timedelta(hours=2),
    )

    # Invalid sequence: delivery first!
    valid, _, _, _, reason = validate_route_schedule(start_pos, now, [delivery, pickup])
    assert valid is False
    assert "Precedence violation" in reason


def test_deadline_violation_check():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    start_pos = GeoPoint(latitude=12.9716, longitude=77.5946)

    # Stop is 15 km away, but deadline is in 2 minutes -> impossible
    impossible_stop = RouteStop(
        stop_id="pick_urgent",
        stop_type="pickup",
        listing_id="list_urgent",
        target_name="Far Hotel",
        location=GeoPoint(latitude=13.1000, longitude=77.6000),
        estimated_arrival=now + timedelta(minutes=5),
        deadline=now + timedelta(minutes=2),
    )

    valid, _, _, _, reason = validate_route_schedule(start_pos, now, [impossible_stop])
    assert valid is False
    assert "Deadline violation" in reason


def test_nearest_neighbor_and_two_opt_improvement():
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    start_pos = GeoPoint(latitude=12.9716, longitude=77.5946)

    # 2 donations: A and B with respective pickups and deliveries
    stops = [
        RouteStop(
            stop_id="pA",
            stop_type="pickup",
            listing_id="listA",
            target_name="Caterer A",
            location=GeoPoint(latitude=12.9740, longitude=77.6050),
            estimated_arrival=now,
            deadline=now + timedelta(hours=3),
        ),
        RouteStop(
            stop_id="dA",
            stop_type="delivery",
            listing_id="listA",
            target_name="Shelter A",
            location=GeoPoint(latitude=12.9800, longitude=77.6400),
            estimated_arrival=now,
            deadline=now + timedelta(hours=4),
        ),
        RouteStop(
            stop_id="pB",
            stop_type="pickup",
            listing_id="listB",
            target_name="Bakery B",
            location=GeoPoint(latitude=12.9720, longitude=77.6010),
            estimated_arrival=now,
            deadline=now + timedelta(hours=3),
        ),
        RouteStop(
            stop_id="dB",
            stop_type="delivery",
            listing_id="listB",
            target_name="Community Fridge B",
            location=GeoPoint(latitude=12.9820, longitude=77.6450),
            estimated_arrival=now,
            deadline=now + timedelta(hours=4),
        ),
    ]

    nn_route = nearest_neighbor_route(start_pos, now, stops)
    assert len(nn_route) == 4

    # Optimize with 2-Opt
    opt_route, final_dist, final_dur = two_opt_optimize(start_pos, now, nn_route)
    assert len(opt_route) == 4
    assert final_dist > 0.0

    # Ensure all pickups precede deliveries in final route
    visited_pickups = set()
    for s in opt_route:
        if s.stop_type == "pickup":
            visited_pickups.add(s.listing_id)
        elif s.stop_type == "delivery":
            assert s.listing_id in visited_pickups

    # Ensure all ETAs are before deadlines
    for s in opt_route:
        assert s.estimated_arrival <= s.deadline
