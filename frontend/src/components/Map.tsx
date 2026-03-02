import { useState, useEffect, useCallback } from 'react';
import Map, { Marker, Popup, Source, Layer } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { Incident, UserLocation } from '../App';

const MAPBOX_TOKEN = 'pk.eyJ1IjoiZGVtb3Rva2VuIiwiYSI6ImNscTIybzZhdjA5dXgya3BrcnBzamxxa3QifQ.demo_token';

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

export default function TacticalMap({ 
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

  const gridLayer = {
    id: 'grid-layer',
    type: 'circle' as const,
    source: 'grid',
    paint: {
      'circle-radius': 0
    }
  };

  return (
    <div className="tactical-map-container">
      <Map
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        mapStyle="mapbox://styles/mapbox/dark-v11"
        mapboxAccessToken={MAPBOX_TOKEN}
        style={{ width: '100%', height: '100%' }}
        attributionControl={false}
        ref={mapRef}
      >
        {/* Tactical Grid Overlay */}
        <Source id="grid" type="geojson" data={gridLines}>
          <Layer
            id="grid-lines"
            type="line"
            paint={{
              'line-color': 'rgba(239, 68, 68, 0.1)',
              'line-width': 1,
              'line-dasharray': [2, 2]
            }}
          />
        </Source>

        {/* User Location Marker */}
        {userLocation && (
          <Marker
            longitude={userLocation.longitude}
            latitude={userLocation.latitude}
            anchor="center"
          >
            <div className="user-location-marker">
              <div className="user-marker-pulse"></div>
              <div className="user-marker-core"></div>
            </div>
          </Marker>
        )}

        {/* Incident Markers */}
        {incidents.map((incident) => {
          if (!incident.latitude || !incident.longitude) return null;
          
          const color = getThreatColor(incident.status);
          const level = getThreatLevel(incident.status);
          const isSelected = selectedIncident?.id === incident.id;
          
          return (
            <Marker
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
            </Marker>
          );
        })}

        {/* Popup for selected incident */}
        {popupInfo && (
          <Popup
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
          </Popup>
        )}
      </Map>

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
