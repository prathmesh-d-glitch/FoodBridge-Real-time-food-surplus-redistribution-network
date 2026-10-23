import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { BANGALORE_CENTER } from '../lib/geo';

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  title: string;
  description?: string;
  type: 'donor' | 'ngo' | 'volunteer';
  portions?: number;
  safeUntil?: string;
}

interface MapViewProps {
  markers?: MapMarker[];
  routes?: Array<[number, number]>;
  center?: [number, number];
  zoom?: number;
  height?: string;
}

export const MapView: React.FC<MapViewProps> = ({
  markers = [],
  routes = [],
  center = BANGALORE_CENTER,
  zoom = 12,
  height = '480px',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current).setView(center, zoom);

      // Standard OpenStreetMap tiles (free, crisp, no API key watermark)
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;
      layerGroupRef.current = L.layerGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!layerGroup || !map) return;

    layerGroup.clearLayers();

    // Apple Maps style vector callout pins
    const createCustomIcon = (type: string) => {
      const color = type === 'donor' ? '#1b7a43' : type === 'ngo' ? '#0071e3' : '#b25e00';
      const svgIcon =
        type === 'donor'
          ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2v6a3 3 0 0 1-3 3 3 3 0 0 1-3-3V2"/><path d="M15 11v11"/><path d="M6 2v20"/><path d="M6 7h4"/></svg>`
          : type === 'ngo'
          ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>`
          : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/></svg>`;

      return L.divIcon({
        className: 'custom-leaflet-marker',
        html: `
          <div style="
            background: #ffffff;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid ${color};
            box-shadow: 0 2px 6px rgba(0,0,0,0.16);
          ">
            ${svgIcon}
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });
    };

    markers.forEach((m) => {
      const marker = L.marker([m.lat, m.lng], {
        icon: createCustomIcon(m.type),
      });

      const popupContent = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif; padding: 4px; color: #1d1d1f;">
          <h4 style="margin: 0 0 4px 0; font-weight: 600; font-size: 13.5px; letter-spacing: -0.01em;">${m.title}</h4>
          ${m.portions ? `<p style="margin: 0 0 4px 0; font-size: 12px; color: #1b7a43; font-weight: 500;">${m.portions} portions available</p>` : ''}
          ${m.description ? `<p style="margin: 0; font-size: 12px; color: #6e6e73; line-height: 1.4;">${m.description}</p>` : ''}
          <div style="margin-top: 6px; font-size: 10.5px; text-transform: uppercase; font-weight: 600; color: #86868b; letter-spacing: 0.04em;">Role: ${m.type}</div>
        </div>
      `;
      marker.bindPopup(popupContent);
      layerGroup.addLayer(marker);
    });

    // Draw route polylines if present
    if (routes.length >= 2) {
      const polyline = L.polyline(routes, {
        color: '#1b7a43',
        weight: 3.5,
        dashArray: '6, 6',
        opacity: 0.9,
      });
      layerGroup.addLayer(polyline);
    }
  }, [markers, routes, center, zoom]);

  return (
    <div className="glass-panel" style={{ height, position: 'relative', overflow: 'hidden' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />
    </div>
  );
};
