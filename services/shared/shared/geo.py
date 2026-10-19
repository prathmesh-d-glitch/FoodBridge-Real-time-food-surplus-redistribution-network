import math
from typing import List, Tuple
from shared.models import GeoPoint

# Base32 characters used in geohash encoding
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
BASE32_MAP = {c: i for i, c in enumerate(BASE32)}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers."""
    R = 6371.0  # Earth radius in km

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


def estimate_travel_time_minutes(distance_km: float, avg_speed_kmh: float = 25.0) -> float:
    """Estimate urban travel duration with a base buffer for traffic/signals.
    Defaults to 25 km/h urban velocity with a 5-minute fixed dispatch buffer.
    """
    if distance_km <= 0:
        return 5.0
    travel_time = (distance_km / avg_speed_kmh) * 60.0
    # Include traffic uncertainty buffer: +15% plus fixed 5 min dispatch/parking
    total_minutes = (travel_time * 1.15) + 5.0
    return round(total_minutes, 1)


def encode_geohash(lat: float, lon: float, precision: int = 6) -> str:
    """Encode latitude and longitude into a geohash string of given precision."""
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True

    while len(geohash) < precision:
        if even:
            mid = (lon_interval[0] + lon_interval[1]) / 2.0
            if lon > mid:
                ch |= bits[bit]
                lon_interval[0] = mid
            else:
                lon_interval[1] = mid
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2.0
            if lat > mid:
                ch |= bits[bit]
                lat_interval[0] = mid
            else:
                lat_interval[1] = mid

        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash.append(BASE32[ch])
            bit = 0
            ch = 0

    return "".join(geohash)


def decode_geohash(geohash: str) -> Tuple[float, float]:
    """Decode a geohash string into (latitude, longitude) center coordinates."""
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    even = True

    for c in geohash.lower():
        cd = BASE32_MAP.get(c, 0)
        for mask in [16, 8, 4, 2, 1]:
            if even:
                mid = (lon_interval[0] + lon_interval[1]) / 2.0
                if cd & mask:
                    lon_interval[0] = mid
                else:
                    lon_interval[1] = mid
            else:
                mid = (lat_interval[0] + lat_interval[1]) / 2.0
                if cd & mask:
                    lat_interval[0] = mid
                else:
                    lat_interval[1] = mid
            even = not even

    lat = (lat_interval[0] + lat_interval[1]) / 2.0
    lon = (lon_interval[0] + lon_interval[1]) / 2.0
    return round(lat, 6), round(lon, 6)


def get_geohash_neighbors(geohash: str) -> List[str]:
    """Calculate the 8 adjacent geohash cells plus the central cell for spatial range queries."""
    lat, lon = decode_geohash(geohash)
    # Estimate rough delta step for geohash precision ~6 (~1.2 km)
    precision = len(geohash)
    lat_delta = 180.0 / (2 ** ((precision * 5) // 2))
    lon_delta = 360.0 / (2 ** (precision * 5 - (precision * 5) // 2))

    neighbors = set()
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            n_lat = min(90.0, max(-90.0, lat + dy * lat_delta))
            n_lon = min(180.0, max(-180.0, lon + dx * lon_delta))
            neighbors.add(encode_geohash(n_lat, n_lon, precision))

    return sorted(list(neighbors))


def calculate_total_route_distance(points: List[GeoPoint]) -> float:
    """Calculate cumulative distance along a sequence of geo coordinates in km."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for i in range(len(points) - 1):
        total += haversine_distance(
            points[i].latitude,
            points[i].longitude,
            points[i + 1].latitude,
            points[i + 1].longitude,
        )
    return round(total, 3)
