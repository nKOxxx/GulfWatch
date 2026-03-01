import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { MapView } from './components/MapView'
import { RegionSelector } from './components/RegionSelector'
import { AlertPanel } from './components/AlertPanel'
import { StatusBar } from './components/StatusBar'
import './App.css'

interface Region {
  id: string
  name: string
  country: string
  code: string
  lat: number
  lng: number
}

function App() {
  const [regions, setRegions] = useState<Region[]>([])
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [alerts, setAlerts] = useState<any[]>([])

  // Fetch regions on load
  useEffect(() => {
    fetch('/api/regions')
      .then(res => res.json())
      .then(data => {
        setRegions(data.regions)
        // Default to Dubai if available
        const dubai = data.regions.find((r: Region) => r.code === 'DXB')
        if (dubai) setSelectedRegion(dubai)
      })
  }, [])

  // WebSocket connection
  useEffect(() => {
    if (!selectedRegion) return

    const ws = new WebSocket(`ws://${window.location.host}/ws`)
    
    ws.onopen = () => {
      setIsConnected(true)
      // Subscribe to region
      ws.send(JSON.stringify({ type: 'subscribe', regionId: selectedRegion.id }))
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'alert') {
        setAlerts(prev => [data, ...prev].slice(0, 50))
      }
    }
    
    ws.onclose = () => setIsConnected(false)
    
    return () => ws.close()
  }, [selectedRegion])

  return (
    <BrowserRouter>
      <div className="app">
        <header className="header">
          <div className="logo">
            <span className="shield">🛡️</span>
            <h1>Gulf Watch</h1>
          </div>
          <RegionSelector 
            regions={regions} 
            selected={selectedRegion} 
            onSelect={setSelectedRegion} 
          />
          <StatusBar isConnected={isConnected} />
        </header>

        <main className="main">
          <Routes>
            <Route path="/" element={
              <div className="dashboard">
                <div className="map-container">
                  <MapView region={selectedRegion} />
                </div>
                <div className="sidebar">
                  <AlertPanel alerts={alerts} region={selectedRegion} />
                </div>
              </div>
            } />
          </Routes>
        </main>

        <footer className="footer">
          <p>🛡️ Gulf Watch — Open Source Regional Intelligence</p>
          <p className="disclaimer">
            For verification and situational awareness only. 
            Follow official civil defense instructions.
          </p>
        </footer>
      </div>
    </BrowserRouter>
  )
}

export default App
