import { useState, useEffect } from 'react'
import './App.css'

const API_URL = 'https://gulf-watch-api.onrender.com'

interface Incident {
  id: string
  status: 'CONFIRMED' | 'LIKELY' | 'PROBABLE' | 'UNCONFIRMED'
  event_type: string
  location_name: string
  lat: number
  lng: number
  description?: string
  detected_at: string
}

function App() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [selected, setSelected] = useState<Incident | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_URL}/incidents`)
      .then(r => r.json())
      .then(data => {
        setIncidents(data)
        setLoading(false)
      })
  }, [])

  const confirmed = incidents.filter(i => i.status === 'CONFIRMED')
  const probable = incidents.filter(i => i.status === 'PROBABLE')

  return (
    <div className="tac-container">
      {/* Header */}
      <header className="tac-header">
        <div className="tac-title">
          <span className="tac-shield">🛡️</span>
          <span>GULF WATCH</span>
          <span className="tac-version">TAC-v1.0</span>
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
        <span className="tac-active">SYSTEM ACTIVE</span>
        <div className="tac-stats">
          <span className="stat-red">{confirmed.length} Confirmed</span>
          <span className="stat-amber">{probable.length} Probable</span>
          <span className="stat-green">{incidents.filter(i => i.status === 'UNCONFIRMED').length} Watch</span>
        </div>
      </div>

      {/* Main Content */}
      <main className="tac-main">
        {/* Map Area */}
        <div className="tac-map-area">
          <div className="tac-map-placeholder">
            <div className="grid-overlay" />
            <div className="map-label">TACTICAL DISPLAY</div>
            
            {/* Incident markers on map */}
            {incidents.map((inc, idx) => (
              <div 
                key={inc.id}
                className={`map-marker ${inc.status.toLowerCase()}`}
                style={{ 
                  left: `${20 + (idx * 25)}%`, 
                  top: `${30 + (idx * 15)}%` 
                }}
                onClick={() => setSelected(inc)}
              >
                <div className="marker-pulse" />
                <div className="marker-dot" />
              </div>
            ))}
            
            {/* User position */}
            <div className="user-position">
              <div className="user-marker" />
              <span>YOU</span>
            </div>
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
                  onClick={() => setSelected(inc)}
                >
                  <div className="feed-status">{inc.status}</div>
                  <div className="feed-type">{inc.event_type}</div>
                  <div className="feed-location">📍 {inc.location_name}</div>
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
            <p className="modal-location">📍 {selected.location_name}</p>
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
        <span>UAE • SAUDI • QATAR • BAHRAIN • KUWAIT • OMAN</span>
        <span className="tac-classified">CONFIDENTIAL</span>
      </footer>
    </div>
  )
}

export default App
