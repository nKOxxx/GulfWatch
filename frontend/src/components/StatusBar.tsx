import { Wifi, WifiOff } from 'lucide-react'

interface Props {
  isConnected: boolean
}

export function StatusBar({ isConnected }: Props) {
  return (
    <div className="status-bar">
      <div className="status-indicator">
        <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
        {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
        <span>{isConnected ? 'Live' : 'Offline'}</span>
      </div>
    </div>
  )
}
