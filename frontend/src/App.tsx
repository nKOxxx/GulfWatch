import { useState, useEffect } from 'react'
import './App.css'

// Read env at module level
const API_URL = (import.meta as any).env?.VITE_API_URL || 'https://gulf-watch-api.onrender.com'

interface Incident {
  id: string
  status: string
  event_type: string
  location_name: string
  description?: string
  detected_at: string
}

interface Source {
  id: string
  name: string
  handle: string
  platform: string
  source_type: string
  is_official: boolean
}

function App() {
  const [activeTab, setActiveTab] = useState<'status' | 'official'>('status')
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/incidents`)
      .then(res => res.json())
      .then(data => {
        setIncidents(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })

    fetch(`${API_URL}/sources/official`)
      .then(res => res.json())
      .then(data => setSources(data))
  }, [])

  return (
    <div className="app">
      <header className="header">
        <div className="logo">🛡️ Gulf Watch</div>
        <div className="status">
          {incidents.length > 0 ? `⚠️ ${incidents.length} Active` : '✓ All Clear'}
        </div>
      </header>

      <main className="main">
        {activeTab === 'status' && (
          <div className="status-view">
            <div className="safety-card safe">
              <div className="safety-status">
                <span className="safety-icon">🟢</span>
                <span className="safety-text">YOU ARE SAFE</span>
                <span className="safety-sub">No active threats in Gulf region</span>
              </div>
            </div>

            <div className="section">
              <h2>Active Incidents</h2>
              {loading ? (
                <p>Loading...</p>
              ) : error ? (
                <p>Error: {error}</p>
              ) : incidents.length === 0 ? (
                <p>No active incidents</p>
              ) : (
                incidents.map(i => (
                  <div key={i.id} className="incident-card">
                    <div className="incident-header">
                      <span className="incident-status">{i.status}</span>
                    </div>
                    <h3>{i.event_type}</h3>
                    <p>📍 {i.location_name}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'official' && (
          <div className="official-view">
            <h2>🏛️ Official UAE Sources</h2>
            {sources.map(s => (
              <div key={s.id} className="source-card">
                <h3>{s.name}</h3>
                <p>@{s.handle} ({s.platform})</p>
                <span className={s.is_official ? 'official-badge' : 'media-badge'}>
                  {s.is_official ? '✓ Official' : 'Media'}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>

      <nav className="bottom-nav">
        <button 
          className={activeTab === 'status' ? 'active' : ''}
          onClick={() => setActiveTab('status')}
        >
          🛡️ Status
        </button>
        <button 
          className={activeTab === 'official' ? 'active' : ''}
          onClick={() => setActiveTab('official')}
        >
          🏛️ Official
        </button>
      </nav>
    </div>
  )
}

export default App
