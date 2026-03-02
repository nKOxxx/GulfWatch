import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import './App.css'
import TacticalMap from './components/Map'

const API_URL = (import.meta as any).env?.VITE_API_URL || 'https://gulf-watch-api.onrender.com'

export interface Incident {
  id: string
  status: string
  event_type: string
  location_name: string
  description?: string
  detected_at: string
  latitude?: number
  longitude?: number
  source_name?: string
  source_type?: string
}

export interface UserLocation {
  latitude: number
  longitude: number
  accuracy?: number
  timestamp: number
}

interface ThreatStats {
  confirmed: number
  probable: number
  watch: number
  total: number
}

function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
  return R * c
}

function getThreatColor(status: string): string {
  const s = status.toLowerCase()
  if (s === 'confirmed' || s === 'active') return '#ef4444'
  if (s === 'probable' || s === 'investigating') return '#f97316'
  return '#eab308'
}

function getThreatLevel(status: string): 'critical' | 'elevated' | 'low' {
  const s = status.toLowerCase()
  if (s === 'confirmed' || s === 'active') return 'critical'
  if (s === 'probable' || s === 'investigating') return 'elevated'
  return 'low'
}

function formatDistance(km: number): string {
  if (km < 1) return `${(km * 1000).toFixed(0)}m`
  return `${km.toFixed(1)}km`
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`
  return `${Math.floor(diff/86400)}d ago`
}

export default function App() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null)
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)
  
  const mapRef = useRef<any>(null)
  const updateInterval = useRef<ReturnType<typeof setInterval> | null>(null)

  // Fetch incidents
  const fetchIncidents = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/incidents`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setIncidents(data)
      setLastUpdate(new Date())
      setError(null)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // Get user location
  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation not supported')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setUserLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        })
      },
      (err) => {
        setLocationError(`Location: ${err.message}`)
        // Default to Dubai
        setUserLocation({
          latitude: 25.2048,
          longitude: 55.2708,
          timestamp: Date.now()
        })
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    )
  }, [])

  // Initial fetch and polling
  useEffect(() => {
    fetchIncidents()
    updateInterval.current = setInterval(fetchIncidents, 30000)
    return () => {
      if (updateInterval.current) clearInterval(updateInterval.current)
    }
  }, [fetchIncidents])

  // Calculate threat stats
  const threatStats: ThreatStats = useMemo(() => {
    const stats = { confirmed: 0, probable: 0, watch: 0, total: incidents.length }
    incidents.forEach(i => {
      const s = i.status.toLowerCase()
      if (s === 'confirmed' || s === 'active') stats.confirmed++
      else if (s === 'probable' || s === 'investigating') stats.probable++
      else stats.watch++
    })
    return stats
  }, [incidents])

  // Determine overall threat level
  const overallThreat = useMemo(() => {
    if (threatStats.confirmed > 0) return { level: 'CRITICAL', color: '#ef4444', pulse: 'critical' }
    if (threatStats.probable > 0) return { level: 'ELEVATED', color: '#f97316', pulse: 'elevated' }
    return { level: 'NORMAL', color: '#22c55e', pulse: 'normal' }
  }, [threatStats])

  // Sort incidents by threat level and distance
  const sortedIncidents = useMemo(() => {
    return [...incidents].sort((a, b) => {
      // First by threat level
      const threatOrder = { 'confirmed': 3, 'active': 3, 'probable': 2, 'investigating': 2, 'watch': 1, 'resolved': 0 }
      const threatDiff = (threatOrder[b.status.toLowerCase() as keyof typeof threatOrder] || 0) - 
                        (threatOrder[a.status.toLowerCase() as keyof typeof threatOrder] || 0)
      if (threatDiff !== 0) return threatDiff
      
      // Then by distance if user location available
      if (userLocation && a.latitude && a.longitude && b.latitude && b.longitude) {
        const distA = calculateDistance(userLocation.latitude, userLocation.longitude, a.latitude, a.longitude)
        const distB = calculateDistance(userLocation.latitude, userLocation.longitude, b.latitude, b.longitude)
        return distA - distB
      }
      
      return new Date(b.detected_at).getTime() - new Date(a.detected_at).getTime()
    })
  }, [incidents, userLocation])

  const handleIncidentClick = useCallback((incident: Incident) => {
    setSelectedIncident(incident)
    setIsMobileMenuOpen(false)
  }, [])

  const handleRefresh = useCallback(() => {
    setLoading(true)
    fetchIncidents()
  }, [fetchIncidents])

  return (
    <div className="command-center">
      {/* Top Status Bar */}
      <header className="status-bar">
        <div className="status-left">
          <div className="logo">
            <span className="logo-icon">◈</span>
            <span className="logo-text">GULF WATCH</span>
            <span className="logo-version">TAC-v1.0</span>
          </div>
          <div className={`threat-indicator ${overallThreat.pulse}`}>
            <span className="threat-pulse"></span>
            <span className="threat-label" style={{ color: overallThreat.color }}>
              {overallThreat.level}
            </span>
          </div>
        </div>
        
        <div className="status-center">
          <div className="stat-item">
            <span className="stat-value critical">{threatStats.confirmed}</span>
            <span className="stat-label">CONFIRMED</span>
          </div>
          <div className="stat-item">
            <span className="stat-value elevated">{threatStats.probable}</span>
            <span className="stat-label">PROBABLE</span>
          </div>
          <div className="stat-item">
            <span className="stat-value watch">{threatStats.watch}</span>
            <span className="stat-label">WATCH</span>
          </div>
        </div>
        
        <div className="status-right">
          <div className="system-status">
            <span className="status-dot active"></span>
            <span className="status-text">SYSTEM ACTIVE</span>
          </div>
          <div className="timestamp">
            {lastUpdate.toLocaleTimeString('en-US', { hour12: false })}
          </div>
          <button className="refresh-btn" onClick={handleRefresh} disabled={loading}>
            {loading ? '◐' : '↻'}
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="command-main">
        {/* Tactical Map */}
        <div className="map-panel">
          <TacticalMap
            incidents={incidents}
            userLocation={userLocation}
            selectedIncident={selectedIncident}
            onSelectIncident={setSelectedIncident}
            mapRef={mapRef}
          />
          
          {/* Mobile Menu Toggle */}
          <button 
            className="mobile-menu-toggle"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? '✕' : '☰'} INCIDENTS
          </button>
        </div>

        {/* Side Panel - Incident Feed */}
        <aside className={`side-panel ${isMobileMenuOpen ? 'open' : ''}`}>
          <div className="panel-header">
            <h2>INCIDENT FEED</h2>
            <span className="incident-count">{incidents.length} TOTAL</span>
          </div>

          {locationError && (
            <div className="location-warning">
              <span className="warning-icon">⚠</span>
              <span>{locationError}</span>
            </div>
          )}

          <div className="incident-list">
            {loading && incidents.length === 0 ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <span>ACQUIRING DATA...</span>
              </div>
            ) : error ? (
              <div className="error-state">
                <span className="error-icon">✕</span>
                <span>CONNECTION ERROR</span>
                <button onClick={handleRefresh}>RETRY</button>
              </div>
            ) : sortedIncidents.length === 0 ? (
              <div className="empty-state">
                <span className="empty-icon">◈</span>
                <span>NO ACTIVE THREATS</span>
                <span className="empty-sub">All sectors clear</span>
              </div>
            ) : (
              sortedIncidents.map(incident => {
                const threatLevel = getThreatLevel(incident.status)
                const color = getThreatColor(incident.status)
                const isSelected = selectedIncident?.id === incident.id
                
                let distanceText = ''
                if (userLocation && incident.latitude && incident.longitude) {
                  const km = calculateDistance(
                    userLocation.latitude, 
                    userLocation.longitude,
                    incident.latitude, 
                    incident.longitude
                  )
                  distanceText = `${formatDistance(km)} from your location`
                }
                
                return (
                  <div 
                    key={incident.id}
                    className={`incident-card ${threatLevel} ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleIncidentClick(incident)}
                  >
                    <div className="card-header">
                      <span 
                        className="threat-badge"
                        style={{ backgroundColor: color }}
                      >
                        {incident.status.toUpperCase()}
                      </span>
                      <span className="time-stamp">
                        {formatTimeAgo(incident.detected_at)}
                      </span>
                    </div>
                    
                    <h3 className="incident-type">{incident.event_type}</h3>
                    
                    <div className="incident-location">
                      <span className="location-icon">⌖</span>
                      <span>{incident.location_name}</span>
                    </div>
                    
                    {distanceText && (
                      <div className="distance-badge">
                        <span className="distance-icon">⟿</span>
                        <span>{distanceText}</span>
                      </div>
                    )}
                    
                    {incident.source_name && (
                      <div className="source-line">
                        <span className="source-label">SRC:</span>
                        <span className="source-name">{incident.source_name}</span>
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>

          {/* Panel Footer */}
          <div className="panel-footer">
            <div className="update-info">
              <span>LAST UPDATE: {lastUpdate.toLocaleTimeString('en-US', { hour12: false })}</span>
            </div>
          </div>
        </aside>
      </main>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <div className="modal-overlay" onClick={() => setSelectedIncident(null)}>
          <div className="incident-modal" onClick={e => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedIncident(null)}>✕</button>
            
            <div className="modal-header">
              <span 
                className="modal-threat-badge"
                style={{ backgroundColor: getThreatColor(selectedIncident.status) }}
              >
                {selectedIncident.status.toUpperCase()}
              </span>
              <h2>{selectedIncident.event_type}</h2>
            </div>
            
            <div className="modal-body">
              <div className="detail-row">
                <span className="detail-label">LOCATION</span>
                <span className="detail-value">{selectedIncident.location_name}</span>
              </div>
              
              <div className="detail-row">
                <span className="detail-label">DETECTED</span>
                <span className="detail-value">
                  {new Date(selectedIncident.detected_at).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                  })}
                </span>
              </div>
              
              {userLocation && selectedIncident.latitude && selectedIncident.longitude && (
                <div className="detail-row">
                  <span className="detail-label">DISTANCE</span>
                  <span className="detail-value">
                    {formatDistance(calculateDistance(
                      userLocation.latitude,
                      userLocation.longitude,
                      selectedIncident.latitude,
                      selectedIncident.longitude
                    ))} from your position
                  </span>
                </div>
              )}
              
              {selectedIncident.source_name && (
                <div className="detail-row">
                  <span className="detail-label">SOURCE</span>
                  <span className="detail-value">{selectedIncident.source_name}</span>
                </div>
              )}
              
              {selectedIncident.description && (
                <div className="detail-section">
                  <span className="detail-label">DESCRIPTION</span>
                  <p className="detail-description">{selectedIncident.description}</p>
                </div>
              )}
              
              {selectedIncident.latitude && selectedIncident.longitude && (
                <div className="coordinates-box">
                  <span className="coord-tag">
                    {selectedIncident.latitude.toFixed(4)}°N, {selectedIncident.longitude.toFixed(4)}°E
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tactical Grid Overlay */}
      <div className="tactical-overlay">
        <div className="grid-corner tl"></div>
        <div className="grid-corner tr"></div>
        <div className="grid-corner bl"></div>
        <div className="grid-corner br"></div>
      </div>
    </div>
  )
}
