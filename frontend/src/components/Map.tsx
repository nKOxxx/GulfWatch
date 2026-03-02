import { useState, useEffect, useCallback, useRef } from 'react';
import type { Incident, UserLocation } from '../App';

// Type for Mapbox events
interface ViewStateChangeEvent {
  viewState: {
    longitude: number;
    latitude: number;
    zoom: number;
    bearing?: number;
    pitch?: number;
    padding?: any;
  };
}

// Try to import Mapbox, fallback to Leaflet if it fails
let MapboxMap: any = null;
let MapboxMarker: any = null;
let MapboxPopup: any = null;
let MapboxSource: any = null;
let MapboxLayer: any = null;
let mapboxAvailable = false;

try {
  const reactMapGL = await import('react-map-gl');
  MapboxMap = reactMapGL.default;
  MapboxMarker = reactMapGL.Marker;
  MapboxPopup = reactMapGL.Popup;
  MapboxSource = reactMapGL.Source;
  MapboxLayer = reactMapGL.Layer;
  mapboxAvailable = true;
} catch (e) {
  console.log('Mapbox not available, will use Leaflet fallback');
}

// Leaflet imports (for fallback)
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet default icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Use environment variable or demo token
const MAPBOX_TOKEN = import.meta.env?.VITE_MAPBOX_TOKEN || 'pk.eyJ1IjoiZGVtb3Rva2VuIiwiYSI6ImNscTIybzZhdjA5dXgya3BrcnBzamxxa3QifQ.demo_token';

interface TacticalMapProps {
  incidents: Incident[];
  userLocation: UserLocation | null;
  selectedIncident: Incident | null;
  onSelectIncident: (incident: Incident | null) => void;
  mapRef?: React.RefObject<any>;
}

// Threat level colors
const THREAT_COLORS = {
  confirmed: '#ef4444', // Red
  probable: '#f97316',  // Orange
  watch: '#eab308',     // Yellow
  user: '#22c55e',      // Green
};

// Calculate distance between two coordinates in km
function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

function getThreatColor(status: string): string {
  const s = status.toLowerCase();
  if (s === 'confirmed' || s === 'active') return THREAT_COLORS.confirmed;
  if (s === 'probable' || s === 'investigating') return THREAT_COLORS.probable;
  return THREAT_COLORS.watch;
}

function getThreatLevel(status: string): number {
  const s = status.toLowerCase();
  if (s === 'confirmed' || s === 'active') return 3;
  if (s === 'probable' || s === 'investigating') return 2;
  return 1;
}

// Leaflet-based map component (fallback)
function LeafletMap({ 
  incidents, 
  userLocation, 
  selectedIncident, 
  onSelectIncident 
}: TacticalMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const [viewState, setViewState] = useState({
    longitude: 54.5,
    latitude: 24.5,
    zoom: 6
  });

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [viewState.latitude, viewState.longitude],
      zoom: viewState.zoom,
      zoomControl: false,
      attributionControl: false
    });

    // Add dark tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map);

    // Add zoom control at bottom right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update view when user location or selected incident changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    if (selectedIncident?.latitude && selectedIncident?.longitude) {
      mapInstanceRef.current.setView(
        [selectedIncident.latitude, selectedIncident.longitude],
        10,
        { animate: true }
      );
    } else if (userLocation) {
      mapInstanceRef.current.setView(
        [userLocation.latitude, userLocation.longitude],
        8,
        { animate: true }
      );
    }
  }, [userLocation, selectedIncident]);

  // Add/update markers
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    const map = mapInstanceRef.current;

    // Add user location marker
    if (userLocation) {
      const userIcon = L.divIcon({
        className: 'custom-user-marker',
        html: `
          <div style="position: relative; width: 20px; height: 20px;">
            <div style="position: absolute; width: 20px; height: 20px; background: rgba(34, 197, 94, 0.3); border-radius: 50%; animation: pulse 2s infinite;"></div>
            <div style="position: absolute; top: 5px; left: 5px; width: 10px; height: 10px; background: #22c55e; border-radius: 50%;"></div>
          </div>
        `,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });
      const userMarker = L.marker([userLocation.latitude, userLocation.longitude], { icon: userIcon }).addTo(map);
      userMarker.bindPopup('Your Position');
      markersRef.current.push(userMarker);
    }

    // Add incident markers
    incidents.forEach(incident => {
      if (!incident.latitude || !incident.longitude) return;

      const color = getThreatColor(incident.status);
      const level = getThreatLevel(incident.status);
      const isSelected = selectedIncident?.id === incident.id;

      const iconHtml = `
        <div style="position: relative; width: ${isSelected ? 30 : 24}px; height: ${isSelected ? 30 : 24}px;">
          <div style="position: absolute; width: 100%; height: 100%; background: ${color}40; border-radius: 50%; animation: pulse ${2/level}s infinite;"></div>
          <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: ${isSelected ? 14 : 10}px; height: ${isSelected ? 14 : 10}px; background: ${color}; border: 2px solid white; border-radius: 50%;"></div>
        </div>
      `;

      const icon = L.divIcon({
        className: 'custom-incident-marker',
        html: iconHtml,
        iconSize: [isSelected ? 30 : 24, isSelected ? 30 : 24],
        iconAnchor: [isSelected ? 15 : 12, isSelected ? 15 : 12]
      });

      const marker = L.marker([incident.latitude, incident.longitude], { icon }).addTo(map);
      
      const popupContent = `
        <div style="min-width: 200px; padding: 8px; font-family: system-ui, sans-serif;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            <div style="width: 8px; height: 8px; background: ${color}; border-radius: 50%;"></div>
            <h4 style="margin: 0; font-size: 14px; font-weight: 600;">${incident.event_type}</h4>
          </div>
          <p style="margin: 0 0 4px 0; font-size: 12px; color: #666;">${incident.location_name}</p>
          <span style="display: inline-block; padding: 2px 8px; background: ${color}; color: white; font-size: 11px; font-weight: 600; border-radius: 4px;">${incident.status.toUpperCase()}</span>
          ${userLocation ? `
            <p style="margin: 8px 0 0 0; font-size: 11px; color: #888;">
              ${calculateDistance(userLocation.latitude, userLocation.longitude, incident.latitude, incident.longitude).toFixed(1)} km away
            </p>
          ` : ''}
        </div>
      `;

      marker.bindPopup(popupContent);
      marker.on('click', () => onSelectIncident(incident));
      markersRef.current.push(marker);
    });
  }, [incidents, userLocation, selectedIncident, onSelectIncident]);

  return (
    <div className="tactical-map-container">
      <div 
        ref={mapContainerRef} 
        style={{ width: '100%', height: '100%', minHeight: '400px' }}
      />
      
      {/* Tactical Map Overlay UI */}
      <div className="map-overlay top-left">
        <div className="coordinate-readout">
          <span className="coord-label">LAT</span>
          <span className="coord-value">{viewState.latitude.toFixed(4)}°N</span>
        </div>
        <div className="coordinate-readout">
          <span className="coord-label">LON</span>
          <span className="coord-value">{viewState.longitude.toFixed(4)}°E</span>
        </div>
      </div>

      <div className="map-overlay bottom-right">
        <div className="zoom-readout">
          ZOOM {viewState.zoom.toFixed(1)}
        </div>
      </div>

      <div className="map-overlay top-right">
        <div className="map-legend">
          <div className="legend-title">THREAT LEVEL</div>
          <div className="legend-item">
            <span className="legend-dot confirmed"></span>
            <span>CONFIRMED</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot probable"></span>
            <span>PROBABLE</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot watch"></span>
            <span>WATCH</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot user"></span>
            <span>YOUR POS</span>
          </div>
        </div>
      </div>

      {/* Leaflet Attribution */}
      <div style={{ position: 'absolute', bottom: '5px', left: '5px', fontSize: '10px', color: '#666' }}>
        © OpenStreetMap © CARTO
      </div>
    </div>
  );
}

// Mapbox-based map component (primary)
function MapboxMapComponent({ 
  incidents, 
  userLocation, 
  selectedIncident, 
  onSelectIncident,
  mapRef 
}: TacticalMapProps) {
  const [popupInfo, setPopupInfo] = useState<Incident | null>(null);
  const [viewState, setViewState] = useState({
    longitude: 54.5,
    latitude: 24.5,
    zoom: 6
  });

  // Center on user location when available
  useEffect(() => {
    if (userLocation) {
      setViewState(prev => ({
        ...prev,
        longitude: userLocation.longitude,
        latitude: userLocation.latitude,
        zoom: 8
      }));
    }
  }, [userLocation]);

  // Center on selected incident
  useEffect(() => {
    if (selectedIncident?.latitude && selectedIncident?.longitude) {
      setViewState(prev => ({
        ...prev,
        longitude: selectedIncident.longitude!,
        latitude: selectedIncident.latitude!,
        zoom: 10
      }));
    }
  }, [selectedIncident]);

  const handleMarkerClick = useCallback((incident: Incident) => {
    onSelectIncident(incident);
    setPopupInfo(incident);
  }, [onSelectIncident]);

  // Generate grid lines for tactical overlay
  const gridLines = {
    type: 'FeatureCollection' as const,
    features: [] as any[]
  };

  // Horizontal grid lines
  for (let lat = 20; lat <= 30; lat += 1) {
    gridLines.features.push({
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [[48, lat], [58, lat]]
      }
    });
  }

  // Vertical grid lines
  for (let lon = 48; lon <= 58; lon += 1) {
    gridLines.features.push({
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [[lon, 20], [lon, 30]]
      }
    });
  }

  return (
    <div className="tactical-map-container" style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapboxMap
        {...viewState}
        onMove={(evt: ViewStateChangeEvent) => setViewState(evt.viewState)}
        mapStyle="mapbox://styles/mapbox/dark-v11"
        mapboxAccessToken={MAPBOX_TOKEN}
        style={{ width: '100%', height: '100%', minHeight: '400px' }}
        attributionControl={false}
        ref={mapRef}
      >
        {/* Tactical Grid Overlay */}
        <MapboxSource id="grid" type="geojson" data={gridLines}>
          <MapboxLayer
            id="grid-lines"
            type="line"
            paint={{
              'line-color': 'rgba(239, 68, 68, 0.1)',
              'line-width': 1,
              'line-dasharray': [2, 2]
            }}
          />
        </MapboxSource>

        {/* User Location Marker */}
        {userLocation && (
          <MapboxMarker
            longitude={userLocation.longitude}
            latitude={userLocation.latitude}
            anchor="center"
          >
            <div className="user-location-marker">
              <div className="user-marker-pulse"></div>
              <div className="user-marker-core"></div>
            </div>
          </MapboxMarker>
        )}

        {/* Incident Markers */}
        {incidents.map((incident) => {
          if (!incident.latitude || !incident.longitude) return null;
          
          const color = getThreatColor(incident.status);
          const level = getThreatLevel(incident.status);
          const isSelected = selectedIncident?.id === incident.id;
          
          return (
            <MapboxMarker
              key={incident.id}
              longitude={incident.longitude}
              latitude={incident.latitude}
              anchor="center"
              onClick={() => handleMarkerClick(incident)}
            >
              <div 
                className={`incident-marker level-${level} ${isSelected ? 'selected' : ''}`}
                style={{ '--marker-color': color } as React.CSSProperties}
              >
                <div className="marker-pulse"></div>
                <div className="marker-core"></div>
              </div>
            </MapboxMarker>
          );
        })}

        {/* Popup for selected incident */}
        {popupInfo && (
          <MapboxPopup
            anchor="top"
            longitude={popupInfo.longitude!}
            latitude={popupInfo.latitude!}
            onClose={() => setPopupInfo(null)}
            closeButton={true}
            closeOnClick={false}
            className="tactical-popup"
          >
            <div className="popup-content">
              <div 
                className="popup-threat-indicator"
                style={{ backgroundColor: getThreatColor(popupInfo.status) }}
              />
              <h4>{popupInfo.event_type}</h4>
              <p className="popup-location">{popupInfo.location_name}</p>
              <span className={`popup-status status-${popupInfo.status.toLowerCase()}`}>
                {popupInfo.status.toUpperCase()}
              </span>
              {userLocation && popupInfo.latitude && popupInfo.longitude && (
                <p className="popup-distance">
                  {calculateDistance(
                    userLocation.latitude, 
                    userLocation.longitude,
                    popupInfo.latitude, 
                    popupInfo.longitude
                  ).toFixed(1)} km from your position
                </p>
              )}
            </div>
          </MapboxPopup>
        )}
      </MapboxMap>

      {/* Tactical Map Overlay UI */}
      <div className="map-overlay top-left">
        <div className="coordinate-readout">
          <span className="coord-label">LAT</span>
          <span className="coord-value">{viewState.latitude.toFixed(4)}°N</span>
        </div>
        <div className="coordinate-readout">
          <span className="coord-label">LON</span>
          <span className="coord-value">{viewState.longitude.toFixed(4)}°E</span>
        </div>
      </div>

      <div className="map-overlay bottom-right">
        <div className="zoom-readout">
          ZOOM {viewState.zoom.toFixed(1)}
        </div>
      </div>

      <div className="map-overlay top-right">
        <div className="map-legend">
          <div className="legend-title">THREAT LEVEL</div>
          <div className="legend-item">
            <span className="legend-dot confirmed"></span>
            <span>CONFIRMED</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot probable"></span>
            <span>PROBABLE</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot watch"></span>
            <span>WATCH</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot user"></span>
            <span>YOUR POS</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main export that decides which map to use
export default function TacticalMap(props: TacticalMapProps) {
  const [mapboxFailed, setMapboxFailed] = useState(false);

  // Check if Mapbox token is valid (basic check)
  useEffect(() => {
    if (!MAPBOX_TOKEN || MAPBOX_TOKEN.includes('demo_token')) {
      console.log('Mapbox token not configured, using Leaflet fallback');
      setMapboxFailed(true);
    }
  }, []);

  // If Mapbox failed or no token, use Leaflet
  if (mapboxFailed || !mapboxAvailable) {
    return <LeafletMap {...props} />;
  }

  // Try Mapbox, fallback on error
  try {
    return <MapboxMapComponent {...props} />;
  } catch (error) {
    console.error('Mapbox error, falling back to Leaflet:', error);
    setMapboxFailed(true);
    return <LeafletMap {...props} />;
  }
}
