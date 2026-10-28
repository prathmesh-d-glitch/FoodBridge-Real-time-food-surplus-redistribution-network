export interface LocationResult {
  latitude: number;
  longitude: number;
  placeName: string;
  formattedAddress: string;
  city?: string;
  suburb?: string;
  state?: string;
  accuracy?: number;
  source: 'gps' | 'fallback' | 'preset';
}

export function haversineDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth radius in km
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 10) / 10;
}

export const BANGALORE_CENTER: [number, number] = [12.9716, 77.5946];
export const GWALIOR_CENTER: [number, number] = [26.2183, 78.1828];

export const PRESET_LOCATIONS: Record<string, LocationResult> = {
  // ── Gwalior Presets ──
  gwalior_lashkar: {
    latitude: 26.2045,
    longitude: 78.1560,
    placeName: 'Jayaji Chowk, Lashkar, Gwalior',
    formattedAddress: 'Jayaji Chowk, Lashkar, Gwalior, Madhya Pradesh 474001, India',
    city: 'Gwalior',
    suburb: 'Lashkar',
    state: 'Madhya Pradesh',
    source: 'preset',
  },
  gwalior_city_center: {
    latitude: 26.2124,
    longitude: 78.1772,
    placeName: 'City Center, Gwalior',
    formattedAddress: 'Patel Nagar, City Center, Gwalior, Madhya Pradesh 474011, India',
    city: 'Gwalior',
    suburb: 'City Center',
    state: 'Madhya Pradesh',
    source: 'preset',
  },
  gwalior_morar: {
    latitude: 26.2289,
    longitude: 78.2254,
    placeName: 'Morar Cantt, Gwalior',
    formattedAddress: 'Mall Road, Morar, Gwalior, Madhya Pradesh 474006, India',
    city: 'Gwalior',
    suburb: 'Morar',
    state: 'Madhya Pradesh',
    source: 'preset',
  },
  gwalior_station: {
    latitude: 26.2198,
    longitude: 78.1820,
    placeName: 'Railway Station Road, Padav, Gwalior',
    formattedAddress: 'Station Road, Padav, Gwalior, Madhya Pradesh 474002, India',
    city: 'Gwalior',
    suburb: 'Padav',
    state: 'Madhya Pradesh',
    source: 'preset',
  },

  // ── Bangalore Presets ──
  mg_road: {
    latitude: 12.9716,
    longitude: 77.5946,
    placeName: 'Palace Grounds, MG Road',
    formattedAddress: 'MG Road, Central Business District, Bengaluru, Karnataka, India',
    city: 'Bengaluru',
    suburb: 'MG Road',
    state: 'Karnataka',
    source: 'preset',
  },
  indiranagar: {
    latitude: 12.9784,
    longitude: 77.6408,
    placeName: '100ft Road, Indiranagar',
    formattedAddress: '100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038, India',
    city: 'Bengaluru',
    suburb: 'Indiranagar',
    state: 'Karnataka',
    source: 'preset',
  },
  koramangala: {
    latitude: 12.9352,
    longitude: 77.6245,
    placeName: '4th Block, Koramangala',
    formattedAddress: 'Koramangala 4th Block, 80 Feet Road, Bengaluru, Karnataka 560034, India',
    city: 'Bengaluru',
    suburb: 'Koramangala',
    state: 'Karnataka',
    source: 'preset',
  },
  whitefield: {
    latitude: 12.9698,
    longitude: 77.7500,
    placeName: 'ITPB, Whitefield',
    formattedAddress: 'International Tech Park Bangalore, Whitefield, Bengaluru, Karnataka 560066, India',
    city: 'Bengaluru',
    suburb: 'Whitefield',
    state: 'Karnataka',
    source: 'preset',
  },
};

export function formatCoordinates(lat: number, lon: number): string {
  const latDir = lat >= 0 ? 'N' : 'S';
  const lonDir = lon >= 0 ? 'E' : 'W';
  return `${Math.abs(lat).toFixed(4)}° ${latDir}, ${Math.abs(lon).toFixed(4)}° ${lonDir}`;
}

/**
 * Reverse geocodes latitude and longitude into a human-readable place name.
 * Uses OpenStreetMap Nominatim with fallback to BigDataCloud reverse geocode.
 */
export async function reverseGeocode(
  lat: number,
  lon: number
): Promise<{ placeName: string; formattedAddress: string; city: string; suburb?: string }> {
  // Strategy 1: OpenStreetMap Nominatim reverse geocoding
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4500);

    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`,
      {
        headers: {
          'Accept-Language': 'en',
        },
        signal: controller.signal,
      }
    );
    clearTimeout(timeoutId);

    if (res.ok) {
      const data = await res.json();
      const addr = data.address || {};
      const suburb = addr.suburb || addr.neighbourhood || addr.residential || addr.quarter || '';
      const road = addr.road || addr.pedestrian || addr.amenity || '';
      const city = addr.city || addr.town || addr.village || addr.city_district || addr.county || 'Bengaluru';
      const state = addr.state || '';

      // Construct concise, meaningful place name
      const components = [road, suburb, city].filter(Boolean);
      const placeName = components.length > 0 ? components.slice(0, 2).join(', ') : data.name || `${city}`;
      const formattedAddress = data.display_name || `${placeName}, ${state}`;

      return {
        placeName: placeName || 'Detected Location',
        formattedAddress,
        city,
        suburb,
      };
    }
  } catch (err) {
    // Fallback to Strategy 2
  }

  // Strategy 2: Free BigDataCloud client reverse geocode
  try {
    const res = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`
    );
    if (res.ok) {
      const data = await res.json();
      const locality = data.locality || data.principalSubdivisionDistrict || '';
      const city = data.city || data.localityInfo?.administrative?.[2]?.name || 'Bengaluru';
      const state = data.principalSubdivision || '';

      const placeName = [locality, city].filter(Boolean).join(', ') || city;
      const formattedAddress = [placeName, state, data.countryName].filter(Boolean).join(', ');

      return {
        placeName,
        formattedAddress,
        city,
        suburb: locality,
      };
    }
  } catch (err) {
    // Network / offline fallback
  }

  // Fallback if offline or network blocks geocoding: Nearest known landmark
  let nearestName = 'Bengaluru City';
  let minDistance = Infinity;
  for (const preset of Object.values(PRESET_LOCATIONS)) {
    const dist = haversineDistance(lat, lon, preset.latitude, preset.longitude);
    if (dist < minDistance) {
      minDistance = dist;
      nearestName = `Near ${preset.placeName}`;
    }
  }

  return {
    placeName: nearestName,
    formattedAddress: `${nearestName} (${formatCoordinates(lat, lon)})`,
    city: 'Bengaluru',
  };
}

/**
 * Gets high-accuracy GPS coordinates from the browser Geolocation API
 * and converts them into an address and place name.
 */
export async function getCurrentLocationWithPlaceName(): Promise<LocationResult> {
  if (!navigator.geolocation) {
    throw new Error('Geolocation is not supported by your browser.');
  }

  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        try {
          const geo = await reverseGeocode(latitude, longitude);
          resolve({
            latitude,
            longitude,
            placeName: geo.placeName,
            formattedAddress: geo.formattedAddress,
            city: geo.city,
            suburb: geo.suburb,
            accuracy,
            source: 'gps',
          });
        } catch {
          resolve({
            latitude,
            longitude,
            placeName: `Detected Spot (${formatCoordinates(latitude, longitude)})`,
            formattedAddress: `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`,
            accuracy,
            source: 'gps',
          });
        }
      },
      (error) => {
        let msg = 'Could not get device location.';
        if (error.code === error.PERMISSION_DENIED) {
          msg = 'Location permission was denied. Please allow location access or select a preset location.';
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          msg = 'Location position is unavailable. Please check your GPS signal or internet.';
        } else if (error.code === error.TIMEOUT) {
          msg = 'Location request timed out. Please try again.';
        }
        reject(new Error(msg));
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 30000,
      }
    );
  });
}
