import { useState, useEffect } from 'react'
import { Activity, Flame, ShieldAlert, Cpu, CheckCircle, AlertTriangle, Layers, Clock } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'
import './index.css'

const BACKEND_URL = 'http://localhost:8000'

function App() {
  const [summary, setSummary] = useState(null)
  const [detections, setDetections] = useState([])
  const [incidents, setIncidents] = useState([])
  const [zoneStats, setZoneStats] = useState([])
  const [isBackendOnline, setIsBackendOnline] = useState(false)

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthRes, sumRes, detRes, incRes, zoneRes] = await Promise.all([
          fetch(`${BACKEND_URL}/api/health`).catch(() => null),
          fetch(`${BACKEND_URL}/api/dashboard/summary`).catch(() => null),
          fetch(`${BACKEND_URL}/api/detections`).catch(() => null),
          fetch(`${BACKEND_URL}/api/incidents`).catch(() => null),
          fetch(`${BACKEND_URL}/api/dashboard/incidents-by-zone`).catch(() => null)
        ])

        setIsBackendOnline(!!healthRes && healthRes.ok)
        
        if (sumRes && sumRes.ok) setSummary(await sumRes.json())
        if (detRes && detRes.ok) setDetections(await detRes.json())
        if (incRes && incRes.ok) setIncidents(await incRes.json())
        if (zoneRes && zoneRes.ok) setZoneStats(await zoneRes.json())

      } catch (error) {
        setIsBackendOnline(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [])

  const handleResolve = async (id) => {
    await fetch(`${BACKEND_URL}/api/incidents/${id}/status?status=resolved`, { method: 'PATCH' })
  }

  const latestDetection = detections.length > 0 ? detections[detections.length - 1] : null
  const latestIncident = incidents.length > 0 ? incidents[incidents.length - 1] : null

  return (
    <div className="dashboard-container">
      {/* HEADER */}
      <header>
        <div className="logo-section">
          <h1><Flame color="#ef4444" size={32} /> FireWatch AI</h1>
        </div>
        <div className={`status-badge ${isBackendOnline ? 'online' : 'offline'}`}>
          <div className="pulse-dot"></div>
          {isBackendOnline ? 'SYSTEM ACTIVE' : 'SYSTEM OFFLINE'}
        </div>
      </header>

      {/* METRICS ROW */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title"><AlertTriangle size={18} /> Total Detections</div>
          <div className={`metric-value ${summary?.total_detections > 0 ? 'alert' : ''}`}>
            {summary?.total_detections || 0}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-title"><ShieldAlert size={18} /> Active Incidents</div>
          <div className="metric-value">
            {summary?.active_incidents || 0}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-title"><Layers size={18} /> Monitored Zones</div>
          <div className="metric-value">
            {summary?.total_zones || 0}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-title"><Clock size={18} /> Last Alert</div>
          <div className="metric-value" style={{ fontSize: '1.8rem', paddingTop: '0.5rem' }}>
            {summary?.last_detection ? summary.last_detection.substring(11, 19) : 'None'}
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="main-grid">
        {/* CAMERA FEED */}
        <div className="panel">
          <div className="panel-header">
            <h2><Activity size={20} /> Live Detection Feed</h2>
            {latestDetection && (
              <span style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>
                Zone {latestDetection.zone_id}
              </span>
            )}
          </div>
          <div className="camera-container">
            {latestDetection ? (
              <img 
                src={`${BACKEND_URL}/images/${latestDetection.image_filename}`} 
                alt="Detection" 
                className="camera-feed"
              />
            ) : (
              <div className="no-feed">
                <Activity size={48} strokeWidth={1} />
                <p>Waiting for detection events...</p>
              </div>
            )}
          </div>
        </div>

        {/* AGENT REASONING */}
        <div className="panel">
          <div className="panel-header">
            <h2><Cpu size={20} /> Agentic Reasoning</h2>
          </div>
          <div className="reasoning-content">
            {latestIncident ? (
              <>
                <div className="decision-box">
                  <div className="decision-row">
                    <span className="decision-label">Action Taken</span>
                    <span className="decision-value">{latestIncident.action_taken}</span>
                  </div>
                  <div className="decision-row">
                    <span className="decision-label">Suppression</span>
                    <span className="decision-value">{latestIncident.sprinkler_type}</span>
                  </div>
                  <div className="reasoning-text">
                    {latestIncident.agent_reasoning}
                  </div>
                </div>

                <div className="actions-grid">
                  <button onClick={() => handleResolve(latestIncident.incident_id)}>
                    <CheckCircle size={18} /> Mark Resolved
                  </button>
                  <button className="primary">
                    <ShieldAlert size={18} /> Manual Override
                  </button>
                </div>
              </>
            ) : (
              <div className="no-feed">
                <Cpu size={48} strokeWidth={1} />
                <p>Agent is monitoring the system...</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* CHARTS */}
      <div className="charts-grid">
        <div className="panel">
          <div className="panel-header">
            <h2><BarChart size={20} /> Zone Activity</h2>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={zoneStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="zone_name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" allowDecimals={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                />
                <Bar dataKey="incident_count" radius={[4, 4, 0, 0]}>
                  {zoneStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.incident_count > 0 ? '#ef4444' : '#3f3f46'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

    </div>
  )
}

export default App
