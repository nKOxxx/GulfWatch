import { useState, useEffect } from 'react'
import './App.css'

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
    distance: 15,
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
    distance: 120,
    description: 'Reports of explosion, awaiting confirmation',
    timestamp: '17:30',
    source: 'Multiple sources',
    isOfficial: false
  }
]

// Status color mapping
const STATUS_COLORS = {
  CONFIRMED: '#ef4444',    // Red
  LIKELY: '#f97316',       // Orange  
  PROBABLE: '#eab308',     // Yellow
  UNCONFIRMED: '#6b7280'   // Gray
}

const STATUS_LABELS = {
  CONFIRMED: '🔴 CONFIRMED',
  LIKELY: '🟠 LIKELY',
  PROBABLE: '🟡 PROBABLE',
  UNCONFIRMED: '⚪ UNCONFIRMED'
}

function App() {
  const [activeTab, setActiveTab] = useState<'status' | 'tracking' | 'official'>('status')
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [incidents] = useState<Incident[]>(MOCK_INCIDENTS)
  const [userLocation] = useState({ lat: 25.2048, lng: 55.2708, name: 'Dubai Downtown' })

  // Filter to show only active/confirmed near user first
  const activeIncidents = incidents.filter(i => i.status === 'CONFIRMED' || i.status === 'LIKELY')
  const watchIncidents = incidents.filter(i => i.status === 'PROBABLE' || i.status === 'UNCONFIRMED')

  // Determine user safety
  const nearestThreat = activeIncidents.length > 0 
    ? activeIncidents.reduce((prev, curr) => (prev.distance || 999) < (curr.distance || 999) ? prev : curr)
    : null
  
  const userIsSafe = !nearestThreat || (nearestThreat.distance || 0) > 50

  if (selectedIncident) {
    return <IncidentDetail incident={selectedIncident} onBack={() => setSelectedIncident(null)} userLocation={userLocation} />
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
          <TrackingView />
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
  userLocation: { name: string }
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
              <span className="safety-sub">No confirmed threats near you</span>
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
          {activeIncidents.map(incident => (
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
              {incident.distance && (
                <p className="incident-distance">
                  {incident.distance} km from {userLocation.name}
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
          {watchIncidents.map(incident => (
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
  userLocation: { name: string; lat: number; lng: number }
}) {
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
      <div className="your-location-card">
        <h3>Your Location</h3>
        <p>{userLocation.name}</p>
        {incident.distance && (
          <>
            <p className="distance">{incident.distance} km from incident</p>
            <p className={`safety-indicator ${incident.distance > 20 ? 'safe' : 'caution'}`}>
              {incident.distance > 20 ? '🟢 You are outside affected zone' : '🟡 Monitor situation'}
            </p>
          </>
        )}
      </div>

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
function TrackingView() {
  const [filters, setFilters] = useState({
    aircraft: false,
    ships: false,
    drones: true,
    impacts: true,
    defenses: true
  })

  return (
    <div className="tracking-view">
      <div className="tracking-map-placeholder">
        <p>🗺️ Interactive Map</p>
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
          <span className="legend-item"><span className="dot blue"></span> You are here</span>
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
