import { formatDistanceToNow } from 'date-fns'
import { AlertTriangle, Shield, Radio } from 'lucide-react'

interface Alert {
  id: string
  type: string
  severity: string
  title: string
  message: string
  timestamp: string
}

interface Region {
  id: string
  name: string
}

interface Props {
  alerts: Alert[]
  region: Region | null
}

export function AlertPanel({ alerts, region }: Props) {
  return (
    <div className="alert-panel">
      <h2>
        <Radio size={16} />
        Live Alerts
      </h2>
      
      {alerts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <Shield size={32} />
          </div>
          <p>No active alerts</p>
          <small>Monitoring {region?.name || 'region'}...</small>
        </div>
      ) : (
        <div className="alert-list">
          {alerts.map((alert) => (
            <div key={alert.id} className={`alert-item ${alert.severity}`}>
              <div className="alert-time">
                {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
              </div>
              <div className="alert-title">
                {alert.severity === 'critical' && <AlertTriangle size={14} />}
                {alert.title}
              </div>
              <div className="alert-message">{alert.message}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
