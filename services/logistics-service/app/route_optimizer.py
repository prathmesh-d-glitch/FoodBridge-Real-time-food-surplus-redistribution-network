from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from shared.geo import estimate_travel_time_minutes, haversine_distance
from shared.logging_setup import setup_logger
from shared.models import GeoPoint, RouteStop

logger = setup_logger("route_optimizer")

# Fixed minutes spent at each stop (loading/unloading & temperature check)
STOP_SERVICE_MINUTES = 10.0


def validate_route_schedule(
    start_pos: GeoPoint,
    start_time: datetime,
    candidate_stops: List[RouteStop],
) -> Tuple[bool, List[datetime], float, float, str]:
    """Evaluates whether a sequence of stops satisfies precedence and deadline constraints.
    
    Hard constraints:
    1. Precedence: Pickup for listing X must occur BEFORE delivery for listing X.
    2. Deadlines: Arrival time at each stop must be <= stop.deadline.
    
    Returns:
      (is_valid, list_of_etas, total_distance_km, total_duration_mins, failure_reason)
    """
    if not candidate_stops:
        return True, [], 0.0, 0.0, "Empty route"

    curr_pos = start_pos
    curr_time = start_time
    total_dist = 0.0
    etas: List[datetime] = []
    picked_up_listings = set()

    for i, stop in enumerate(candidate_stops):
        # 1. Check Precedence
        if stop.stop_type == "delivery":
            if stop.listing_id not in picked_up_listings:
                return (
                    False,
                    [],
                    total_dist,
                    0.0,
                    f"Precedence violation: Delivery of {stop.listing_id} attempted before pickup",
                )
        elif stop.stop_type == "pickup":
            picked_up_listings.add(stop.listing_id)

        # 2. Travel calculation
        leg_dist = haversine_distance(
            curr_pos.latitude, curr_pos.longitude, stop.location.latitude, stop.location.longitude
        )
        travel_mins = estimate_travel_time_minutes(leg_dist)
        arrival_time = curr_time + timedelta(minutes=travel_mins)

        # 3. Hard Deadline Check: arrival_time must be <= stop.deadline
        if arrival_time > stop.deadline:
            slack_mins = (arrival_time - stop.deadline).total_seconds() / 60.0
            return (
                False,
                [],
                total_dist,
                0.0,
                f"Deadline violation at stop #{i + 1} ({stop.target_name}): Arrival {arrival_time.isoformat()} exceeds deadline {stop.deadline.isoformat()} by {slack_mins:.1f}m",
            )

        etas.append(arrival_time)
        total_dist += leg_dist
        # Add stop service duration
        curr_time = arrival_time + timedelta(minutes=STOP_SERVICE_MINUTES)
        curr_pos = stop.location

    total_duration_mins = (curr_time - start_time).total_seconds() / 60.0
    return True, etas, round(total_dist, 2), round(total_duration_mins, 1), "Valid"


def nearest_neighbor_route(
    start_pos: GeoPoint,
    start_time: datetime,
    stops: List[RouteStop],
) -> List[RouteStop]:
    """Constructs a greedy initial route starting from start_pos."""
    unvisited = list(stops)
    route: List[RouteStop] = []
    curr_pos = start_pos

    while unvisited:
        # Prioritize pickups over deliveries, and pick nearest
        best_stop = None
        best_dist = float("inf")

        for stop in unvisited:
            # Check delivery precedence
            if stop.stop_type == "delivery":
                # Ensure pickup for this listing is already in route
                if not any(r.listing_id == stop.listing_id and r.stop_type == "pickup" for r in route):
                    continue

            dist = haversine_distance(
                curr_pos.latitude, curr_pos.longitude, stop.location.latitude, stop.location.longitude
            )
            if dist < best_dist:
                best_dist = dist
                best_stop = stop

        if best_stop is None:
            # Fallback if remaining are unroutable
            best_stop = unvisited[0]

        route.append(best_stop)
        unvisited.remove(best_stop)
        curr_pos = best_stop.location

    return route


def two_opt_optimize(
    start_pos: GeoPoint,
    start_time: datetime,
    initial_stops: List[RouteStop],
    max_iterations: int = 50,
) -> Tuple[List[RouteStop], float, float]:
    """Iteratively reverses sub-routes (2-Opt) if it shortens distance AND satisfies all hard deadlines."""
    best_route = list(initial_stops)
    valid, _, best_dist, best_dur, _ = validate_route_schedule(start_pos, start_time, best_route)

    if not valid:
        logger.warning("Initial greedy route violates deadlines. Attempting heuristic repairs.")

    improved = True
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        for i in range(len(best_route) - 1):
            for j in range(i + 1, len(best_route)):
                # Proposed 2-opt swap: reverse slice between i and j
                candidate = best_route[:i] + list(reversed(best_route[i : j + 1])) + best_route[j + 1 :]
                is_valid, _, cand_dist, cand_dur, reason = validate_route_schedule(
                    start_pos, start_time, candidate
                )

                if is_valid and (cand_dist < best_dist - 0.01):
                    best_route = candidate
                    best_dist = cand_dist
                    best_dur = cand_dur
                    improved = True
                    break
            if improved:
                break

    # Final ETA calculation
    _, etas, final_dist, final_dur, _ = validate_route_schedule(start_pos, start_time, best_route)
    for idx, eta in enumerate(etas):
        best_route[idx].estimated_arrival = eta

    logger.info(
        f"2-Opt optimization completed: {len(best_route)} stops, {final_dist}km, {final_dur} mins in {iteration} iterations"
    )
    return best_route, final_dist, final_dur
