import { useState, useEffect, useRef } from 'react'
import './App.css'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

const API_URL = 'https://gulf-watch-api.onrender.com'

interface Incident {
  id: string
  status: 'CONFIRMED' | 'LIKELY' | 'PROBABLE' | 'UNCONFIRMED'
  event_type: string
  location_name: string
  country?: string
  lat: number
  lng: number
  description?: string
  detected_at: string
}

function App() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selected, setSelected] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)
  const mapRef = useRef<L.Map | null>(null)
  const markersRef = useRef<L.Marker[]>([])

  // Initialize map
  useEffect(() => {
    if (mapRef.current) return

    const map = L.map('tac-map', {
      center: [25.276987, 55.296249], // Dubai
      zoom: 6,
      minZoom: 4,
      maxZoom: 16,
      zoomControl: false
    })

    // Add Stamen Toner tile layer (grayscale land, black water - tactical)
    L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}.png', {
      attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map)

    // Add zoom control to bottom right
    L.control.zoom({ position: 'bottomright' }).addTo(map)

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Fetch incidents
  useEffect(() => {
    fetch(`${API_URL}/incidents`)
      .then(r => r.json())
      .then(data => {
        setIncidents(data)
        setLoading(false)
      })
  }, [])

  // Update markers when incidents change
  useEffect(() => {
    if (!mapRef.current) return

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove())
    markersRef.current = []

    // Add new markers
    incidents.forEach(inc => {
      const color = inc.status === 'CONFIRMED' ? '#ef4444' : 
                    inc.status === 'LIKELY' ? '#f59e0b' : '#22c55e'
      
      const icon = L.divIcon({
        className: 'tac-marker',
        html: `
          <div class="marker-container">
            <div class="marker-pulse" style="background: ${color}"></div>
            <div class="marker-dot" style="background: ${color}; border-color: ${color}"></div>
          </div>
        `,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      })

      const marker = L.marker([inc.lat, inc.lng], { icon })
        .addTo(mapRef.current!)
        .on('click', () => setSelected(inc))

      markersRef.current.push(marker)
    })

    // Fit bounds if we have incidents
    if (incidents.length > 0) {
      const bounds = L.latLngBounds(incidents.map(i => [i.lat, i.lng]))
      mapRef.current.fitBounds(bounds, { padding: [50, 50] })
    }
  }, [incidents])

  const confirmed = incidents.filter(i => i.status === 'CONFIRMED')
  const probable = incidents.filter(i => i.status === 'PROBABLE')

  return (
    <div className="tac-container">
      {/* Header */}
      <header className="tac-header">
        <div className="tac-title">
          <span className="tac-shield">🛡️</span>
          <span>GULF WATCH</span>
          <span className="tac-version">TAC-v1.1</span>
        </div>
        <div className="tac-coords">
          <span>LAT 25.2048°N</span>
          <span>LON 55.2708°E</span>
        </div>
        <div className="tac-time">{new Date().toLocaleTimeString()}</div>
      </header>

      {/* Status Bar */}
      <div className="tac-status">
        <div className="tac-indicator pulse-red" />
        <span className="tac-active">72H INTELLIGENCE</span>
        <div className="tac-stats">
          <span className="stat-red">{confirmed.length} Confirmed</span>
          <span className="stat-amber">{probable.length} Probable</span>
          <span className="stat-green">{incidents.length} Total Events</span>
        </div>
      </div>

      {/* Main Content */}
      <main className="tac-main">
        {/* Map Area - Real Leaflet Map */}
        <div className="tac-map-area">
          <div id="tac-map" className="tac-map"></div>
          <div className="map-overlay">
            <div className="map-label">TACTICAL DISPLAY</div>
          </div>
        </div>

        {/* Side Panel */}
        <aside className="tac-panel">
          <h3>INCIDENT FEED</h3>
          <div className="feed-count">{incidents.length} Total Events</div>
          
          {loading ? (
            <div className="loading">Loading intelligence...</div>
          ) : (
            <div className="incident-list">
              {incidents.map(inc => (
                <div 
                  key={inc.id} 
                  className={`feed-item ${inc.status.toLowerCase()} ${selected?.id === inc.id ? 'active' : ''}`}
                  onClick={() => {
                    setSelected(inc)
                    if (mapRef.current) {
                      mapRef.current.setView([inc.lat, inc.lng], 10)
                    }
                  }}
                >
                  <div className="feed-status">{inc.status}</div>
                  <div className="feed-type">{inc.event_type}</div>
                  <div className="feed-location">📍 {inc.location_name} {inc.country && <span className="feed-country">• {inc.country}</span>}</div>
                  <div className="feed-time">
                    {new Date(inc.detected_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>
      </main>

      {/* Detail Modal */}
      {selected && (
        <div className="tac-modal" onClick={() => setSelected(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className={`modal-header ${selected.status.toLowerCase()}`}>
              <span>{selected.status}</span>
              <button onClick={() => setSelected(null)}>×</button>
            </div>
            <h2>{selected.event_type}</h2>
            <p className="modal-location">📍 {selected.location_name} {selected.country && <span className="modal-country">({selected.country})</span>}</p>
            <p className="modal-coords">
              {selected.lat.toFixed(4)}°N, {selected.lng.toFixed(4)}°E
            </p>
            {selected.description && (
              <p className="modal-desc">{selected.description}</p>
            )}
            <div className="modal-time">
              Detected: {new Date(selected.detected_at).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="tac-footer">
        <span>UAE • SAUDI • QATAR • BAHRAIN • KUWAIT • OMAN • ISRAEL • IRAN</span>
        <span className="tac-classified">CONFIDENTIAL</span>
      </footer>
    </div>
  )
}

export default App
