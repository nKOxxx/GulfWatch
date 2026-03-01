import { useState, useEffect, useCallback } from 'react'
import './App.css'

// User location type
interface UserLocation {
  lat: number
  lng: number
  name: string
  accuracy?: number
  isManual?: boolean
}

// Simplified incident type
interface Incident {
  id: string
  status: 'CONFIRMED' | 'LIKELY' | 'PROBABLE' | 'UNCONFIRMED'
  type: string
  location: string
  lat: number
  lng: number
  distance?: number
  description: string
  timestamp: string
  source: string
  isOfficial: boolean
}

// Mock data for demo
const MOCK_INCIDENTS: Incident[] = [
  {
    id: '1',
    status: 'CONFIRMED',
    type: 'Air Defense',
    location: 'Dubai Marina',
    lat: 25.0765,
    lng: 55.1404,
    description: 'Air defense systems activated over Dubai',
    timestamp: '17:43',
    source: '@WAMnews',
    isOfficial: true
  },
  {
    id: '2',
    status: 'PROBABLE',
    type: 'Explosion',
    location: 'Abu Dhabi',
    lat: 24.4539,
    lng: 54.3773,
    description: 'Reports of explosion, awaiting confirmation',
    timestamp: '17:30',
    source: 'Multiple sources',
    isOfficial: false
  },
  {
    id: '3',
    status: 'LIKELY',
    type: 'Drone Activity',
    location: 'Doha, Qatar',
    lat: 25.2854,
    lng: 51.5310,
    description: 'Multiple reports of drone sightings',
    timestamp: '17:15',
    source: 'Social media',
    isOfficial: false
  }
]

// Gulf region bounds
const GULF_BOUNDS = {
  north: 30.0,
  south: 22.0,
  east: 57.0,
  west: 47.0
}

// Status color mapping
const STATUS_COLORS = {
  CONFIRMED: '#ef4444',
  LIKELY: '#f97316',
  PROBABLE: '#eab308',
  UNCONFIRMED: '#6b7280'
}

const STATUS_LABELS = {
  CONFIRMED: '🔴 CONFIRMED',
  LIKELY: '🟠 LIKELY',
  PROBABLE: '🟡 PROBABLE',
  UNCONFIRMED: '⚪ UNCONFIRMED'
}

// Haversine distance calculation
function calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371 // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLng = (lng2 - lng1) * Math.PI / 180
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng/2) * Math.sin(dLng/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return Math.round(R * c)
}

// Get location name from coordinates (simplified)
function getLocationName(lat: number, lng: number): string {
  // Simple region detection
  if (lat > 24.8 && lat < 25.5 && lng > 54.5 && lng < 56.0) return 'Dubai, UAE'
  if (lat > 24.0 && lat < 25.0 && lng > 54.0 && lng < 55.0) return 'Abu Dhabi, UAE'
  if (lat > 26.0 && lat < 26.5 && lng > 50.0 && lng < 51.0) return 'Manama, Bahrain'
  if (lat > 24.5 && lat < 26.5 && lng > 50.5 && lng < 52.0) return 'Doha, Qatar'
  if (lat > 24.0 && lat < 25.0 && lng > 46.0 && lng < 47.0) return 'Riyadh, Saudi Arabia'
  return 'Gulf Region'
}

function App() {
  const [activeTab, setActiveTab] = useState<'status' | 'tracking' | 'official'>('status')
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [incidents] = useState<Incident[]>(MOCK_INCIDENTS)
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null)
  const [isLocating, setIsLocating] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  const [showLocationPicker, setShowLocationPicker] = useState(false)

  // Calculate distances from user to all incidents
  const incidentsWithDistance = incidents.map(incident => ({
    ...incident,
    distance: userLocation 
      ? calculateDistance(userLocation.lat, userLocation.lng, incident.lat, incident.lng)
      : undefined
  }))

  // Auto-detect location on mount
  useEffect(() => {
    detectLocation()
  }, [])

  // Detect user location via multiple methods
  const detectLocation = useCallback(async () => {
    setIsLocating(true)
    setLocationError(null)

    // Method 1: Browser geolocation (most accurate)
    if (navigator.geolocation) {
      try {
        const position = await new Promise<GeolocationPosition>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
          })
        })
        
        const { latitude, longitude, accuracy } = position.coords
        setUserLocation({
          lat: latitude,
          lng: longitude,
          name: getLocationName(latitude, longitude),
          accuracy,
          isManual: false
        })
        setIsLocating(false)
        return
      } catch (error) {
        console.log('Browser geolocation failed, trying IP...')
      }
    }

    // Method 2: IP geolocation (fallback)
    try {
      const response = await fetch('https://ipapi.co/json/')
      if (response.ok) {
        const data = await response.json()
        if (data.latitude && data.longitude) {
          // Check if in Gulf region
          const inGulf = data.latitude >= GULF_BOUNDS.south && 
                        data.latitude <= GULF_BOUNDS.north &&
                        data.longitude >= GULF_BOUNDS.west && 
                        data.longitude <= GULF_BOUNDS.east
          
          setUserLocation({
            lat: data.latitude,
            lng: data.longitude,
            name: inGulf ? `${data.city}, ${data.country_name}` : 'Unknown Location',
            isManual: false
          })
          
          if (!inGulf) {
            setLocationError('Location outside Gulf region. Please select manually.')
            setShowLocationPicker(true)
          }
          setIsLocating(false)
          return
        }
      }
    } catch (error) {
      console.log('IP geolocation failed')
    }

    // Fallback: Default to Dubai
    setUserLocation({
      lat: 25.2048,
      lng: 55.2708,
      name: 'Dubai, UAE (Default)',
      isManual: false
    })
    setLocationError('Could not detect location. Showing default (Dubai).')
    setIsLocating(false)
  }, [])

  // Manual location selection
  const selectManualLocation = useCallback((lat: number, lng: number) => {
    setUserLocation({
      lat,
      lng,
      name: getLocationName(lat, lng),
      isManual: true
    })
    setShowLocationPicker(false)
    setLocationError(null)
  }, [])

  // Filter to show only active/confirmed near user first
  const activeIncidents = incidentsWithDistance.filter(i => i.status === 'CONFIRMED' || i.status === 'LIKELY')
  const watchIncidents = incidentsWithDistance.filter(i => i.status === 'PROBABLE' || i.status === 'UNCONFIRMED')

  // Determine user safety
  const nearestThreat = activeIncidents.length > 0 
    ? activeIncidents.reduce((prev, curr) => (prev.distance || 999) < (curr.distance || 999) ? prev : curr)
    : null
  
  const userIsSafe = !nearestThreat || (nearestThreat.distance || 0) > 50

  if (selectedIncident) {
    return (
      <IncidentDetail 
        incident={selectedIncident} 
        onBack={() => setSelectedIncident(null)} 
        userLocation={userLocation}
      />
    )
  }

  if (showLocationPicker) {
    return (
      <LocationPicker 
        onSelect={selectManualLocation}
        onCancel={() => setShowLocationPicker(false)}
        currentLocation={userLocation}
      />
    )
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="shield">🛡️</span>
            <h1>Gulf Watch</h1>
          </div>
          <div className="alert-badge">
            {activeIncidents.length > 0 ? (
              <span className="badge alert">⚠️ {activeIncidents.length} ACTIVE</span>
            ) : (
              <span className="badge safe">✓ ALL CLEAR</span>
            )}
          </div>
        </div>
        
        {/* Location Bar */}
        <div className="location-bar" onClick={() => setShowLocationPicker(true)}>
          {isLocating ? (
            <span className="locating">📍 Detecting location...</span>
          ) : userLocation ? (
            <span className="location">
              📍 {userLocation.name}
              {userLocation.isManual && <span className="manual-badge"> (Manual)</span>}
              <span className="change-btn">Change</span>
            </span>
          ) : (
            <span className="location unknown">📍 Location unknown</span>
          )}
        </div>
        
        {locationError && (
          <div className="location-error">
            {locationError}
            <button onClick={() => setShowLocationPicker(true)}>Select Location</button>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="main">
        {activeTab === 'status' && (
          <StatusView 
            userIsSafe={userIsSafe}
            nearestThreat={nearestThreat}
            activeIncidents={activeIncidents}
            watchIncidents={watchIncidents}
            userLocation={userLocation}
            onSelectIncident={setSelectedIncident}
          />
        )}
        
        {activeTab === 'tracking' && (
          <TrackingView 
            userLocation={userLocation}
            incidents={incidentsWithDistance}
            onSelectLocation={selectManualLocation}
          />
        )}
        
        {activeTab === 'official' && (
          <OfficialView />
        )}
      </main>

      {/* Bottom Navigation */}
      <nav className="bottom-nav">
        <button 
          className={`nav-btn ${activeTab === 'status' ? 'active' : ''}`}
          onClick={() => setActiveTab('status')}
        >
          <span className="nav-icon">🛡️</span>
          <span className="nav-label">Status</span>
        </button>
        <button 
          className={`nav-btn ${activeTab === 'tracking' ? 'active' : ''}`}
          onClick={() => setActiveTab('tracking')}
        >
          <span className="nav-icon">📡</span>
          <span className="nav-label">Tracking</span>
        </button>
        <button 
          className={`nav-btn ${activeTab === 'official' ? 'active' : ''}`}
          onClick={() => setActiveTab('official')}
        >
          <span className="nav-icon">🏛️</span>
          <span className="nav-label">Official</span>
        </button>
      </nav>
    </div>
  )
}

// Location Picker Component
function LocationPicker({ 
  onSelect, 
  onCancel,
  currentLocation 
}: { 
  onSelect: (lat: number, lng: number) => void
  onCancel: () => void
  currentLocation: UserLocation | null
}) {
  const [mapPosition, setMapPosition] = useState({ lat: 25.5, lng: 54.0, zoom: 6 })
  const [selectedPoint, setSelectedPoint] = useState<{lat: number, lng: number} | null>(null)

  // Quick location buttons
  const quickLocations = [
    { name: 'Dubai', lat: 25.2048, lng: 55.2708 },
    { name: 'Abu Dhabi', lat: 24.4539, lng: 54.3773 },
    { name: 'Manama', lat: 26.2285, lng: 50.5860 },
    { name: 'Doha', lat: 25.2854, lng: 51.5310 },
    { name: 'Riyadh', lat: 24.7136, lng: 46.6753 },
    { name: 'Kuwait City', lat: 29.3759, lng: 47.9774 },
    { name: 'Muscat', lat: 23.5859, lng: 58.4059 }
  ]

  return (
    <div className="location-picker">
      <div className="picker-header">
        <h2>Select Your Location</h2>
        <button className="close-btn" onClick={onCancel}>✕</button>
      </div>
      
      <div className="quick-locations">
        <h3>Quick Select</h3>
        <div className="location-buttons">
          {quickLocations.map(loc => (
            <button 
              key={loc.name}
              className="location-btn"
              onClick={() => onSelect(loc.lat, loc.lng)}
            >
              {loc.name}
            </button>
          ))}
        </div>
      </div>

      <div className="map-selection">
        <h3>Or Tap on Map</h3>
        <div className="simple-map">
          {/* Simple visual representation of Gulf */}
          <div className="gulf-map">
            <svg viewBox="0 0 400 300" className="region-svg">
              {/* Gulf outline - simplified */}
              <path 
                d="M 100,150 Q 150,100 200,120 Q 250,140 300,180 Q 320,220 280,250 Q 200,280 120,240 Q 80,200 100,150" 
                fill="rgba(59,130,246,0.2)" 
                stroke="#3b82f6"
                strokeWidth="2"
              />
              {/* Cities */}
              <circle cx="280" cy="180" r="6" fill="#ef4444" className="city-marker" onClick={() => onSelect(25.2048, 55.2708)}>
                <title>Dubai</title>
              </circle>
              <circle cx="260" cy="200" r="6" fill="#ef4444" className="city-marker" onClick={() => onSelect(24.4539, 54.3773)}>
                <title>Abu Dhabi</title>
              </circle>
              <circle cx="150" cy="220" r="6" fill="#ef4444" className="city-marker" onClick={() => onSelect(26.2285, 50.5860)}>
                <title>Manama</title>
              </circle>
              <circle cx="200" cy="180" r="6" fill="#ef4444" className="city-marker" onClick={() => onSelect(25.2854, 51.5310)}>
                <title>Doha</title>
              </circle>
              <circle cx="80" cy="120" r="6" fill="#ef4444" className="city-marker" onClick={() => onSelect(24.7136, 46.6753)}>
                <title>Riyadh</title>
              </circle>
              <circle cx="120" cy="60" r="6" fill="#ef4444" className="city-marker" onClick={() => onSelect(29.3759, 47.9774)}>
                <title>Kuwait City</title>
              </circle>
              <circle cx="350" cy="200" r="6" fill="#ef4444" className="city-marker" onClick={() => onSelect(23.5859, 58.4059)}>
                <title>Muscat</title>
              </circle>
              
              {/* Labels */}
              <text x="290" y="175" fill="white" fontSize="10">Dubai</text>
              <text x="230" y="195" fill="white" fontSize="10">Doha</text>
              <text x="140" y="235" fill="white" fontSize="10">Manama</text>
            </svg>
          </div>
          <p className="map-hint">Tap a city or select from quick list above</p>
        </div>
      </div>

      {currentLocation && (
        <div className="current-location">
          <p>Current: <strong>{currentLocation.name}</strong></p>
          {currentLocation.isManual && <span className="manual-tag">Manually set</span>}
        </div>
      )}
    </div>
  )
}

// Status View - Main dashboard
function StatusView({ 
  userIsSafe, 
  nearestThreat, 
  activeIncidents, 
  watchIncidents,
  userLocation,
  onSelectIncident 
}: {
  userIsSafe: boolean
  nearestThreat: Incident | null
  activeIncidents: Incident[]
  watchIncidents: Incident[]
  userLocation: UserLocation | null
  onSelectIncident: (i: Incident) => void
}) {
  return (
    <div className="status-view">
      {/* User Safety Status - BIG */}
      <div className={`safety-card ${userIsSafe ? 'safe' : 'unsafe'}`}>
        <div className="safety-status">
          {userIsSafe ? (
            <>
              <span className="safety-icon">🟢</span>
              <span className="safety-text">YOU ARE SAFE</span>
              <span className="safety-sub">
                {userLocation ? `Near ${userLocation.name}` : 'Location unknown'}
              </span>
            </>
          ) : (
            <>
              <span className="safety-icon">🔴</span>
              <span className="safety-text">THREAT DETECTED</span>
              <span className="safety-sub">
                {nearestThreat?.distance} km away - {nearestThreat?.location}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Active Incidents */}
      {activeIncidents.length > 0 && (
        <div className="section">
          <h2 className="section-title">Active Incidents</h2>
          {activeIncidents.sort((a, b) => (a.distance || 999) - (b.distance || 999)).map(incident => (
            <div 
              key={incident.id} 
              className="incident-card active"
              onClick={() => onSelectIncident(incident)}
            >
              <div className="incident-header">
                <span className="incident-status" style={{ color: STATUS_COLORS[incident.status] }}>
                  {STATUS_LABELS[incident.status]}
                </span>
                <span className="incident-time">{incident.timestamp}</span>
              </div>
              <h3 className="incident-type">{incident.type}</h3>
              <p className="incident-location">📍 {incident.location}</p>
              {incident.distance !== undefined && (
                <p className="incident-distance">
                  {incident.distance} km from you
                </p>
              )}
              {incident.isOfficial && (
                <span className="official-badge">✓ Official Source</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Watch List */}
      {watchIncidents.length > 0 && (
        <div className="section">
          <h2 className="section-title">Monitoring</h2>
          {watchIncidents.sort((a, b) => (a.distance || 999) - (b.distance || 999)).map(incident => (
            <div 
              key={incident.id} 
              className="incident-card watch"
              onClick={() => onSelectIncident(incident)}
            >
              <div className="incident-header">
                <span className="incident-status" style={{ color: STATUS_COLORS[incident.status] }}>
                  {STATUS_LABELS[incident.status]}
                </span>
                <span className="incident-time">{incident.timestamp}</span>
              </div>
              <p className="incident-location">📍 {incident.location}</p>
              {incident.distance !== undefined && (
                <p className="incident-distance">{incident.distance} km away</p>
              )}
              <p className="incident-desc">{incident.description}</p>
            </div>
          ))}
        </div>
      )}

      {/* No Incidents */}
      {activeIncidents.length === 0 && watchIncidents.length === 0 && (
        <div className="all-clear">
          <span className="all-clear-icon">✓</span>
          <p>No incidents reported in Gulf region</p>
          <p className="all-clear-sub">Last updated: Just now</p>
        </div>
      )}
    </div>
  )
}

// Incident Detail View
function IncidentDetail({ 
  incident, 
  onBack,
  userLocation 
}: { 
  incident: Incident
  onBack: () => void
  userLocation: UserLocation | null
}) {
  const distance = userLocation 
    ? calculateDistance(userLocation.lat, userLocation.lng, incident.lat, incident.lng)
    : null

  return (
    <div className="incident-detail">
      <div className="detail-header">
        <button className="back-btn" onClick={onBack}>← Back</button>
        <button className="share-btn">Share</button>
      </div>

      <div className="detail-status" style={{ color: STATUS_COLORS[incident.status] }}>
        {STATUS_LABELS[incident.status]}
      </div>
      
      <h1 className="detail-title">{incident.type}</h1>
      <p className="detail-location">📍 {incident.location}</p>

      {/* Your Location Context */}
      {userLocation && distance !== null && (
        <div className="your-location-card">
          <h3>Your Location</h3>
          <p>{userLocation.name}</p>
          <p className="distance">{distance} km from incident</p>
          <p className={`safety-indicator ${distance > 20 ? 'safe' : 'caution'}`}>
            {distance > 20 ? '🟢 You are outside affected zone' : '🟡 Monitor situation'}
          </p>
        </div>
      )}

      {/* What Happened */}
      <div className="detail-section">
        <h3>What Happened</h3>
        <p>{incident.description}</p>
        <div className="source-info">
          <p>Source: <strong>{incident.source}</strong></p>
          {incident.isOfficial && <span className="official-tag">Official Account</span>}
        </div>
      </div>

      {/* Official Guidance */}
      <div className="detail-section official-guidance">
        <h3>🏛️ Official Guidance</h3>
        <div className="guidance-box">
          <p>"Stay indoors. Away from windows. Follow official channels only."</p>
          <p className="guidance-source">— @uae_cd (Civil Defense) • 17:45</p>
        </div>
      </div>

      {/* Live Tracking */}
      <div className="detail-section">
        <h3>📡 Live Tracking</h3>
        <div className="tracking-grid">
          <div className="tracking-item">
            <span className="tracking-icon">✈️</span>
            <span className="tracking-label">Aircraft</span>
            <span className="tracking-status normal">Normal</span>
          </div>
          <div className="tracking-item">
            <span className="tracking-icon">🚢</span>
            <span className="tracking-label">Ships</span>
            <span className="tracking-status normal">Normal</span>
          </div>
          <div className="tracking-item">
            <span className="tracking-icon">🛸</span>
            <span className="tracking-label">Drones</span>
            <span className="tracking-status alert">Active</span>
          </div>
          <div className="tracking-item">
            <span className="tracking-icon">💥</span>
            <span className="tracking-label">Impact</span>
            <span className="tracking-status alert">Detected</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Tracking View - Live map and filters
function TrackingView({ 
  userLocation,
  incidents,
  onSelectLocation 
}: { 
  userLocation: UserLocation | null
  incidents: Incident[]
  onSelectLocation: (lat: number, lng: number) => void
}) {
  const [filters, setFilters] = useState({
    aircraft: false,
    ships: false,
    drones: true,
    impacts: true,
    defenses: true
  })

  return (
    <div className="tracking-view">
      {/* User can tap map to set location */}
      {userLocation && (
        <div className="set-location-hint">
          <p>📍 Showing incidents near: <strong>{userLocation.name}</strong></p>
          <p className="hint-sub">Tap anywhere on map to change location</p>
        </div>
      )}

      <div className="tracking-map-placeholder">
        <p>🗺️ Interactive Gulf Map</p>
        <div className="mini-map">
          <svg viewBox="0 0 400 300" className="region-svg interactive">
            {/* Gulf outline */}
            <path 
              d="M 100,150 Q 150,100 200,120 Q 250,140 300,180 Q 320,220 280,250 Q 200,280 120,240 Q 80,200 100,150" 
              fill="rgba(59,130,246,0.1)" 
              stroke="#3b82f6"
              strokeWidth="2"
            />
            {/* User location */}
            {userLocation && (
              <circle 
                cx={280 - (55.2708 - userLocation.lng) * 10}
                cy={180 + (25.2048 - userLocation.lat) * 20}
                r="8" 
                fill="#3b82f6"
                className="user-marker pulse"
              />
            )}
            {/* Incidents */}
            {incidents.map(inc => (
              <circle
                key={inc.id}
                cx={280 - (55.2708 - inc.lng) * 10}
                cy={180 + (25.2048 - inc.lat) * 20}
                r="6"
                fill={STATUS_COLORS[inc.status]}
                className="incident-marker"
              />
            ))}
          </svg>
        </div>
        <p className="map-sub">Gulf Region • Live Tracking</p>
      </div>

      <div className="filter-section">
        <h3>Show on Map</h3>
        <div className="filter-grid">
          <label className={`filter-item ${filters.aircraft ? 'active' : ''}`}>
            <input 
              type="checkbox" 
              checked={filters.aircraft}
              onChange={(e) => setFilters({...filters, aircraft: e.target.checked})}
            />
            <span className="filter-icon">✈️</span>
            <span>Aircraft</span>
          </label>
          <label className={`filter-item ${filters.ships ? 'active' : ''}`}>
            <input 
              type="checkbox" 
              checked={filters.ships}
              onChange={(e) => setFilters({...filters, ships: e.target.checked})}
            />
            <span className="filter-icon">🚢</span>
            <span>Ships</span>
          </label>
          <label className={`filter-item ${filters.drones ? 'active' : ''}`}>
            <input 
              type="checkbox" 
              checked={filters.drones}
              onChange={(e) => setFilters({...filters, drones: e.target.checked})}
            />
            <span className="filter-icon">🛸</span>
            <span>Drones</span>
          </label>
          <label className={`filter-item ${filters.impacts ? 'active' : ''}`}>
            <input 
              type="checkbox" 
              checked={filters.impacts}
              onChange={(e) => setFilters({...filters, impacts: e.target.checked})}
            />
            <span className="filter-icon">💥</span>
            <span>Impacts</span>
          </label>
        </div>
      </div>

      <div className="legend">
        <h3>Legend</h3>
        <div className="legend-items">
          <span className="legend-item"><span className="dot red"></span> Active incident</span>
          <span className="legend-item"><span className="dot yellow"></span> Watch/Unconfirmed</span>
          <span className="legend-item"><span className="dot green"></span> Safe zone</span>
          <span className="legend-item"><span className="dot blue pulse"></span> You are here</span>
        </div>
      </div>
    </div>
  )
}

// Official Statements View
function OfficialView() {
  const statements = [
    {
      source: '@WAMnews',
      text: 'Air defense systems activated over Dubai. All residents advised to remain indoors.',
      time: '17:43',
      country: 'UAE',
      type: 'official'
    },
    {
      source: '@uae_cd',
      text: 'Stay indoors, away from windows. Follow official channels only. Do not spread rumors.',
      time: '17:45',
      country: 'UAE',
      type: 'civil_defense'
    },
    {
      source: '@SaudiPressAgency',
      text: 'Monitoring situation in UAE. All Saudi air defense systems on heightened alert.',
      time: '17:50',
      country: 'Saudi Arabia',
      type: 'official'
    }
  ]

  return (
    <div className="official-view">
      <h2 className="view-title">🏛️ Official Statements</h2>
      
      {statements.map((stmt, i) => (
        <div key={i} className={`statement-card ${stmt.type}`}>
          <div className="statement-header">
            <span className="statement-country">{stmt.country}</span>
            <span className="statement-time">{stmt.time}</span>
          </div>
          <p className="statement-text">"{stmt.text}"</p>
          <p className="statement-source">— {stmt.source}</p>
          {stmt.type === 'civil_defense' && (
            <span className="statement-badge">Civil Defense</span>
          )}
          {stmt.type === 'official' && (
            <span className="statement-badge official">Official</span>
          )}
        </div>
      ))}
    </div>
  )
}

export default App
