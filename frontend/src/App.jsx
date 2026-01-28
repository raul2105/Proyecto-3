import { useState, useEffect } from 'react'
import ComparisonView from './components/ComparisonView'
import CameraSettings from './components/CameraSettings'
import JobControl from './components/JobControl'
import ROIEditor from './components/ROIEditor'
import ColorDashboard from './components/ColorDashboard'
import SetupWizard from './components/SetupWizard'
import RecipeManager from './components/RecipeManager'
import Dashboard from './components/Dashboard'
import DefectExplorer from './components/DefectExplorer'
import DiagnosticsPanel from './components/DiagnosticsPanel'
import LoginModal from './components/LoginModal'
import AlarmEventsPanel from './components/AlarmEventsPanel'
import ReportsPanel from './components/ReportsPanel'
import SensorPanel from './components/SensorPanel'
import { SimulationLineSettings, LiveLineSettings } from './components/LineSettings'
import './App.css'

function App() {
  // Auth & View State
  const [user, setUser] = useState(null) // { username, role, token }
  const [view, setView] = useState('login') // login, dashboard, inspection, defects, settings, reports
  const [settingsTab, setSettingsTab] = useState('camera') // camera, job, line, installer, retention

  // System State
  const [masterId, setMasterId] = useState(null)
  const [isInspecting, setIsInspecting] = useState(false)
  const [isSimulating, setIsSimulating] = useState(true)

  // Data State
  const [liveFrame, setLiveFrame] = useState(null)
  const [masterFrame, setMasterFrame] = useState(null)
  const [heatmapFrame, setHeatmapFrame] = useState(null)
  const [defects, setDefects] = useState([])
  const [stats, setStats] = useState({ speed_m_min: 0, yield_pct: 100, defect_count: 0 })
  const [diagnostics, setDiagnostics] = useState(null)

  // Color Module State
  const [colorTarget, setColorTarget] = useState(null)
  const [colorHistory, setColorHistory] = useState([])
  const [latestColorMeas, setLatestColorMeas] = useState(null)

  // Tools State
  const [showRoiEditor, setShowRoiEditor] = useState(false)
  const [rois, setRois] = useState([])
  const [showWizard, setShowWizard] = useState(false)
  const [showRecipeMgr, setShowRecipeMgr] = useState(false)
  const [activeRecipe, setActiveRecipe] = useState('Default')
  const [jobId, setJobId] = useState('')
  const [rollId, setRollId] = useState('')
  const [cameraId, setCameraId] = useState('')
  const [cameraExposure, setCameraExposure] = useState(-5)
  const [rollDiameter, setRollDiameter] = useState(600)
  const [coreDiameter, setCoreDiameter] = useState(76)
  const [materialThickness, setMaterialThickness] = useState(0.05)
  const [labelPitch, setLabelPitch] = useState(0)
  const [cmarkEnabled, setCmarkEnabled] = useState(false)
  const [jitterTolerance, setJitterTolerance] = useState(20)
  const [fallbackEncoder, setFallbackEncoder] = useState(true)
  const [encoderPitch, setEncoderPitch] = useState(0)
  const [encoderIntervalMs, setEncoderIntervalMs] = useState(200)
  const [encoderRunning, setEncoderRunning] = useState(false)
  const [mmPerTick, setMmPerTick] = useState(0)
  const [repeatMm, setRepeatMm] = useState(0)

  // Installer / PLC Settings
  const [plcEnabled, setPlcEnabled] = useState(false)
  const [plcIp, setPlcIp] = useState('')
  const [plcPort, setPlcPort] = useState(502)
  const [plcUnitId, setPlcUnitId] = useState(1)
  const [plcProtocol, setPlcProtocol] = useState('modbus_tcp')
  const [plcTimeoutMs, setPlcTimeoutMs] = useState(1000)
  const [plcTowerRed, setPlcTowerRed] = useState('')
  const [plcTowerYellow, setPlcTowerYellow] = useState('')
  const [plcTowerGreen, setPlcTowerGreen] = useState('')
  const [plcBuzzer, setPlcBuzzer] = useState('')
  const [plcStopLine, setPlcStopLine] = useState('')

  const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001'
  const [apiStatus, setApiStatus] = useState('unknown') // unknown, online, offline
  const [alarms, setAlarms] = useState([])
  const [events, setEvents] = useState([])
  const [retention, setRetention] = useState({ thumbnails_days: 30, evidence_days: 90, video_days: 14 })
  const [reportHistory, setReportHistory] = useState([])
  const [reportDetail, setReportDetail] = useState(null)
  const [rollDefects, setRollDefects] = useState([])
  const [useStream, setUseStream] = useState(true)
  const [sensorStatus, setSensorStatus] = useState(null)
  const [lineStatus, setLineStatus] = useState(null)

  // Initial Data Load
  useEffect(() => {
    fetch(`${API_URL}/color/target`)
      .then(res => res.json())
      .then(data => {
        if (data.name) setColorTarget(data)
        setApiStatus('online')
      })
      .catch(err => {
        setApiStatus('offline')
        console.error('Failed to load color target', err)
      })
  }, [API_URL])

  useEffect(() => {
    fetch(`${API_URL}/settings`)
      .then(res => res.json())
      .then(data => {
        if (data.settings) {
          if (typeof data.settings.use_simulator === 'boolean') {
            setIsSimulating(data.settings.use_simulator)
          }
          if (data.settings.camera_id !== null && data.settings.camera_id !== undefined) {
            setCameraId(String(data.settings.camera_id))
          }
          if (typeof data.settings.exposure === 'number') {
            setCameraExposure(data.settings.exposure)
          }
          if (typeof data.settings.roll_diameter_mm === 'number') {
            setRollDiameter(data.settings.roll_diameter_mm)
          }
          if (typeof data.settings.core_diameter_mm === 'number') {
            setCoreDiameter(data.settings.core_diameter_mm)
          }
          if (typeof data.settings.material_thickness_mm === 'number') {
            setMaterialThickness(data.settings.material_thickness_mm)
          }
          if (typeof data.settings.plc_enabled === 'boolean') {
            setPlcEnabled(data.settings.plc_enabled)
          }
          if (typeof data.settings.plc_ip === 'string') {
            setPlcIp(data.settings.plc_ip)
          }
          if (typeof data.settings.plc_port === 'number') {
            setPlcPort(data.settings.plc_port)
          }
          if (typeof data.settings.plc_unit_id === 'number') {
            setPlcUnitId(data.settings.plc_unit_id)
          }
          if (typeof data.settings.plc_protocol === 'string') {
            setPlcProtocol(data.settings.plc_protocol)
          }
          if (typeof data.settings.plc_timeout_ms === 'number') {
            setPlcTimeoutMs(data.settings.plc_timeout_ms)
          }
          if (typeof data.settings.plc_tower_red === 'string') {
            setPlcTowerRed(data.settings.plc_tower_red)
          }
          if (typeof data.settings.plc_tower_yellow === 'string') {
            setPlcTowerYellow(data.settings.plc_tower_yellow)
          }
          if (typeof data.settings.plc_tower_green === 'string') {
            setPlcTowerGreen(data.settings.plc_tower_green)
          }
          if (typeof data.settings.plc_buzzer === 'string') {
            setPlcBuzzer(data.settings.plc_buzzer)
          }
          if (typeof data.settings.plc_stop_line === 'string') {
            setPlcStopLine(data.settings.plc_stop_line)
          }
        }
        if (data.retention_policy) {
          setRetention(data.retention_policy)
        }
      })
      .catch(err => console.error('Failed to load settings', err))
  }, [API_URL])

  useEffect(() => {
    fetch(`${API_URL}/sensors/status`)
      .then(res => res.json())
      .then(data => {
        if (data.sensor_config) {
          setLabelPitch(data.sensor_config.label_pitch_m || 0)
          setCmarkEnabled(Boolean(data.sensor_config.cmark_enabled))
          setJitterTolerance(data.sensor_config.jitter_tolerance_ms || 20)
          setFallbackEncoder(Boolean(data.sensor_config.fallback_encoder))
          setEncoderPitch(data.sensor_config.encoder_pitch_m || 0)
          setMmPerTick(data.sensor_config.mm_per_tick || 0)
          setRepeatMm(data.sensor_config.repeat_mm || 0)
        }
      })
      .catch(err => console.error('Failed to load sensor config', err))
  }, [API_URL])


  useEffect(() => {
    if (!encoderRunning) return
    const safeInterval = Math.max(50, Number.isFinite(encoderIntervalMs) ? encoderIntervalMs : 200)
    const interval = setInterval(() => {
      fetch(`${API_URL}/sensors/encoder/pulse`, { method: 'POST' })
        .catch(err => console.error('Encoder pulse failed', err))
    }, safeInterval)
    return () => clearInterval(interval)
  }, [API_URL, encoderRunning, encoderIntervalMs])

  useEffect(() => {
    if (!isSimulating && encoderRunning) {
      setEncoderRunning(false)
    }
  }, [isSimulating, encoderRunning])

  const handleLogin = (userData) => {
    setUser(userData)
    setView('dashboard')
  }

  // Inspection Loop
  useEffect(() => {
    let interval
    let inFlight = false
    if (isInspecting && masterId) {
      interval = setInterval(async () => {
        if (inFlight) return
        inFlight = true
        try {
          const res = await fetch(`${API_URL}/inspection-frame?format=jpg&quality=70&scale=0.6`)
          const data = await res.json()
          if (data.error) return // Handle error gracefully
          setApiStatus('online')

          const prefix = 'data:image/jpeg;base64,'
          setLiveFrame(prefix + data.live_image)
          setMasterFrame(prefix + data.master_image)
          setHeatmapFrame(prefix + data.heatmap_image)

          setDefects(data.defects || [])
          setStats(data.stats || { speed_m_min: 0, yield_pct: 100, defect_count: 0 })
          if (data.stats?.roll_diameter_mm) {
            setRollDiameter(data.stats.roll_diameter_mm)
          }
          setDiagnostics(data.diagnostics)

          if (data.color_measurement) {
            setLatestColorMeas(data.color_measurement)
            setColorHistory(prev => {
              const newHist = [...prev, data.color_measurement]
              return newHist.length > 50 ? newHist.slice(newHist.length - 50) : newHist
            })
          }
        } catch (err) {
          setApiStatus('offline')
          console.error('Inspection error', err)
        } finally {
          inFlight = false
        }
      }, useStream ? 1000 : 250)
    }
    return () => clearInterval(interval)
  }, [API_URL, isInspecting, masterId, useStream])

  useEffect(() => {
    if (!rollId || view !== 'dashboard') return
    fetch(`${API_URL}/traceability/roll/${rollId}/defects?limit=500`)
      .then(res => res.json())
      .then(data => setRollDefects(data))
      .catch(err => console.error('Failed to load roll defects', err))
  }, [API_URL, rollId, view])

  useEffect(() => {
    if (view !== 'reports') return
    fetch(`${API_URL}/reports/history?limit=50`)
      .then(res => res.json())
      .then(data => setReportHistory(data))
      .catch(err => console.error('Failed to load report history', err))
  }, [API_URL, view])

  useEffect(() => {
    fetch(`${API_URL}/toggle-source?use_simulator=${isSimulating}`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        setApiStatus('online')
        if (typeof data.use_simulator === 'boolean' && data.use_simulator !== isSimulating) {
          setIsSimulating(data.use_simulator)
        }
      })
      .catch(err => {
        setApiStatus('offline')
        console.error('Failed to toggle source', err)
      })
  }, [API_URL, isSimulating])

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_URL}/alarms`)
        .then(res => res.json())
        .then(data => setAlarms(data))
        .catch(err => console.error('Failed to load alarms', err))
      fetch(`${API_URL}/events?limit=50`)
        .then(res => res.json())
        .then(data => setEvents(data))
        .catch(err => console.error('Failed to load events', err))
      fetch(`${API_URL}/sensors/status`)
        .then(res => res.json())
        .then(data => setSensorStatus(data))
        .catch(err => console.error('Failed to load sensors status', err))
      fetch(`${API_URL}/line/status`)
        .then(res => res.json())
        .then(data => setLineStatus(data))
        .catch(err => console.error('Failed to load line status', err))
    }, 2000)
    return () => clearInterval(interval)
  }, [API_URL])

  useEffect(() => {
    if (!lineStatus) return
    if (typeof lineStatus.job_id === 'string' && lineStatus.job_id !== jobId) {
      setJobId(lineStatus.job_id)
    }
    if (typeof lineStatus.roll_id === 'string' && lineStatus.roll_id !== rollId) {
      setRollId(lineStatus.roll_id)
    }
    if (typeof lineStatus.active_recipe === 'string' && lineStatus.active_recipe !== activeRecipe) {
      setActiveRecipe(lineStatus.active_recipe)
    }
    if (typeof lineStatus.master_loaded === 'boolean') {
      setMasterId(lineStatus.master_loaded ? 'loaded' : null)
    }
  }, [lineStatus])

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${API_URL}/upload-master`, { method: 'POST', body: formData })
      if (res.ok) {
        alert('Master loaded!')
        setMasterId('loaded')
        // Load and display the master image immediately
        const masterRes = await fetch(`${API_URL}/master-image`)
        const blob = await masterRes.blob()
        const url = URL.createObjectURL(blob)
        setMasterFrame(url)
      }
    } catch (err) {
      alert('Error uploading master')
    }
  }

  const handleAckAlarm = async (code, clear = false) => {
    await fetch(`${API_URL}/alarms/ack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, clear })
    })
  }

  const handleStartJob = async () => {
    if (!jobId) return
    if (isInspecting) {
      alert('Stop inspection before starting a new job.')
      return
    }
    if (!activeRecipe) {
      alert('Select a recipe before starting a job.')
      return
    }
    const res = await fetch(`${API_URL}/job/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, recipe: activeRecipe })
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      alert(data.detail || 'Failed to start job')
    }
  }

  const handleStartRoll = async () => {
    if (!rollId) return
    const res = await fetch(`${API_URL}/roll/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ roll_id: rollId })
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      alert(data.detail || 'Failed to start roll')
    }
  }

  const handleAutoRoll = async () => {
    const res = await fetch(`${API_URL}/roll/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ roll_id: '' })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      alert(data.detail || data.error || 'Failed to start roll')
      return false
    }
    setRollId(data.roll_id || '')
    return true
  }

  const handleStartInspection = async () => {
    if (isInspecting) {
      setIsInspecting(false)
      return
    }
    const statusRes = await fetch(`${API_URL}/line/status`).catch(() => null)
    const status = statusRes && statusRes.ok ? await statusRes.json() : null
    const resolvedJobId = status?.job_id || jobId
    const resolvedRecipe = status?.active_recipe || activeRecipe
    const masterLoaded = status?.master_loaded ?? Boolean(masterId)
    const resolvedRollId = status?.roll_id || rollId

    if (!resolvedRecipe) {
      alert('Load a recipe before starting inspection.')
      return
    }
    if (!masterLoaded) {
      alert('Load a master before starting inspection.')
      return
    }

    const autoJobId = `JOB-${new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15)}`
    const jobIdToUse = resolvedJobId || autoJobId

    if (!status?.job_id) {
      const jobRes = await fetch(`${API_URL}/job/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobIdToUse, recipe: resolvedRecipe })
      })
      if (!jobRes.ok) {
        const data = await jobRes.json().catch(() => ({}))
        alert(data.detail || data.error || 'Failed to start job')
        return
      }
      setJobId(jobIdToUse)
    }
    if (!resolvedRollId) {
      const ok = await handleAutoRoll()
      if (!ok) return
    } else if (resolvedRollId !== rollId) {
      setRollId(resolvedRollId)
    }
    setIsInspecting(true)
  }

  const handleEndRoll = async () => {
    const res = await fetch(`${API_URL}/roll/end`, { method: 'POST' })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      alert(data.detail || 'Failed to end roll')
    }
  }

  const handleRetentionSave = async () => {
    await fetch(`${API_URL}/retention-policy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(retention)
    })
  }

  const handleBindMaster = async () => {
    if (!activeRecipe) return
    await fetch(`${API_URL}/recipes/${activeRecipe}/bind-master`, { method: 'POST' })
  }

  const handleLoadRecipe = async (name) => {
    if (!name) return
    const res = await fetch(`${API_URL}/load-recipe/${name}`)
    if (res.ok) {
      setActiveRecipe(name)
      setMasterId('loaded')
    }
  }

  const handleSaveLineSettings = async () => {
    const clampNonNegative = (value, fallback = 0) => {
      const number = Number(value)
      if (!Number.isFinite(number) || number < 0) return fallback
      return number
    }
    const clampInt = (value, fallback = 0) => {
      const number = clampNonNegative(value, fallback)
      return Math.max(0, Math.round(number))
    }
    await fetch(`${API_URL}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        use_simulator: isSimulating,
        camera_id: cameraId ? parseInt(cameraId) : null,
        exposure: cameraExposure,
        roll_diameter_mm: clampNonNegative(rollDiameter, 0),
        core_diameter_mm: clampNonNegative(coreDiameter, 0),
        material_thickness_mm: clampNonNegative(materialThickness, 0)
      })
    })
    await fetch(`${API_URL}/sensors/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        label_pitch_m: clampNonNegative(labelPitch, 0),
        cmark_enabled: cmarkEnabled,
        jitter_tolerance_ms: clampInt(jitterTolerance, 20),
        fallback_encoder: fallbackEncoder,
        encoder_pitch_m: clampNonNegative(encoderPitch, 0),
        mm_per_tick: clampNonNegative(mmPerTick, 0),
        repeat_mm: clampNonNegative(repeatMm, 0)
      })
    })
  }

  const handleSaveInstallerSettings = async () => {
    await fetch(`${API_URL}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        use_simulator: isSimulating,
        plc_enabled: plcEnabled,
        plc_ip: plcIp,
        plc_port: plcPort,
        plc_unit_id: plcUnitId,
        plc_protocol: plcProtocol,
        plc_timeout_ms: plcTimeoutMs,
        plc_tower_red: plcTowerRed,
        plc_tower_yellow: plcTowerYellow,
        plc_tower_green: plcTowerGreen,
        plc_buzzer: plcBuzzer,
        plc_stop_line: plcStopLine
      })
    })
  }

  const handleSelectReport = async (roll) => {
    setReportDetail(null)
    const res = await fetch(`${API_URL}/reports/roll/${roll.roll_id}`)
    if (res.ok) {
      const data = await res.json()
      setReportDetail(data)
    }
  }

  const canStartRoll = Boolean(lineStatus?.job_id || jobId) && Boolean(lineStatus?.active_recipe || activeRecipe)

  // Render Helpers
  const renderSidebar = () => (
    <aside className="sidebar controls">
      <div className="user-info card">
        <strong>{user?.username}</strong>
        <small className="muted">{user?.role}</small>
        <button
          onClick={() => { setUser(null); setView('login') }}
          className="btn-muted"
        >
          Logout
        </button>
      </div>

      <nav className="main-nav">
        <button className={view === 'dashboard' ? 'active' : ''} onClick={() => setView('dashboard')}>Dashboard</button>
        <button className={view === 'inspection' ? 'active' : ''} onClick={() => setView('inspection')}>Inspection</button>
        <button className={view === 'defects' ? 'active' : ''} onClick={() => setView('defects')}>Defects</button>
        <button className={view === 'settings' ? 'active' : ''} onClick={() => setView('settings')}>Settings</button>
        <button className={view === 'reports' ? 'active' : ''} onClick={() => setView('reports')}>Reports</button>
      </nav>

      <hr className="divider" />

      <div className="card">
        <h4>Job Control</h4>
        <div className="status-row">
          <span className="label">Recipe</span>
          <strong>{activeRecipe}</strong>
        </div>
        {user?.role !== 'operator' && (
          <button onClick={() => setShowRecipeMgr(true)} className="btn-secondary">Manage Recipes</button>
        )}
        <button onClick={handleBindMaster} className="btn-muted">Bind Master to Recipe</button>
      </div>

      <div className="card">
        <button
          disabled={!(lineStatus?.master_loaded ?? masterId) || !(lineStatus?.active_recipe || activeRecipe)}
          onClick={handleStartInspection}
          className={isInspecting ? 'btn-stop' : 'btn-start'}
        >
          {isInspecting ? 'STOP' : 'START'}
        </button>
        <button onClick={() => setShowWizard(true)} disabled={isInspecting} className="btn-primary">
          Wizard Start
        </button>
      </div>

      <div className="card">
        <h4>Master</h4>
        <div className="status-row">
          <span className="label">Status</span>
          <span className={`pill ${masterId ? 'good' : 'warn'}`}>{masterId ? 'Loaded' : 'Missing'}</span>
        </div>
        <input className="input-file" type="file" accept=".pdf" onChange={handleFileUpload} />
        <button onClick={() => setShowRoiEditor(true)} disabled={!masterId}>
          Edit ROIs
        </button>
      </div>

      <div className="card">
        <h4>Source</h4>
        <div className="toggle-row">
          <button
            className={isSimulating ? 'btn-toggle active' : 'btn-toggle'}
            onClick={() => setIsSimulating(true)}
          >
            Simulated
          </button>
          <button
            className={!isSimulating ? 'btn-toggle active' : 'btn-toggle'}
            onClick={() => setIsSimulating(false)}
          >
            Live
          </button>
        </div>
        <p className="help-text">Switching updates the backend image source.</p>
      </div>

      <DiagnosticsPanel diagnostics={diagnostics} />
    </aside>
  )

  if (!user) return <LoginModal onLogin={handleLogin} apiUrl={API_URL} />

  return (
    <div className="container">
      {renderSidebar()}

      <main className="main-content">

        {/* Top Header */}
        <header className="header">
          <h2>Flexo Inspection: {view.toUpperCase()}</h2>
          <div className="status-bar">
            <span className={isInspecting ? 'badge good' : 'badge warn'}>{isInspecting ? 'RUNNING' : 'STOPPED'}</span>
            <span className={`badge ${apiStatus === 'online' ? 'good' : apiStatus === 'offline' ? 'bad' : 'neutral'}`}>
              API: {apiStatus.toUpperCase()}
            </span>
            <span className="badge neutral">SOURCE: {isSimulating ? 'SIM' : 'LIVE'}</span>
            {latestColorMeas && (
              <span className="status-value">
                Delta E: <span className={latestColorMeas.is_critical ? 'bad' : 'good'}>{latestColorMeas.delta_e.toFixed(2)}</span>
              </span>
            )}
          </div>
        </header>

        {/* View Content */}
        <div className="view-content">

          {view === 'dashboard' && (
            <div className="stack">
              <Dashboard stats={stats} defects={defects} rollDefects={rollDefects} rollDiameter={rollDiameter} />
              <SensorPanel sensorStatus={sensorStatus} />
              <AlarmEventsPanel
                alarms={alarms}
                events={events}
                onAck={(code) => handleAckAlarm(code, false)}
                onClear={(code) => handleAckAlarm(code, true)}
              />
              <div className="card">
                <h3>Color Trend</h3>
                <ColorDashboard currentMeasurement={latestColorMeas} history={colorHistory} target={colorTarget} />
              </div>
            </div>
          )}

          {view === 'inspection' && (
            <div className="stack">
              <div className="card">
                <h3>Line Control</h3>
                <div className="status-row">
                  <span className="label">Recipe</span>
                  <span>{lineStatus?.active_recipe || activeRecipe || '---'}</span>
                </div>
                <div className="status-row">
                  <span className="label">Job</span>
                  <span>{lineStatus?.job_id || jobId || '---'}</span>
                </div>
                <div className="status-row">
                  <span className="label">Roll</span>
                  <span>{lineStatus?.roll_id || rollId || '---'}</span>
                </div>
                <div className="row gap">
                  <button className="btn-secondary" onClick={handleAutoRoll} disabled={isInspecting || !canStartRoll}>
                    New Roll
                  </button>
                  <button className="btn-muted" onClick={handleEndRoll} disabled={isInspecting}>End Roll</button>
                </div>
              </div>
              <div className="card">
                <div className="row gap">
                  <label className="label">Live Stream</label>
                  <button
                    className={useStream ? 'btn-secondary' : 'btn-muted'}
                    onClick={() => setUseStream(!useStream)}
                  >
                    {useStream ? 'On' : 'Off'}
                  </button>
                </div>
                <p className="muted">Streaming improves smoothness; defects still update on interval.</p>
              </div>
              <ComparisonView
                masterSrc={masterFrame}
                liveSrc={useStream ? `${API_URL}/stream/live.mjpg?scale=0.6&quality=70` : liveFrame}
                heatmapSrc={useStream ? `${API_URL}/stream/heatmap.mjpg?scale=0.6&quality=70` : heatmapFrame}
                defects={defects}
              />
            </div>
          )}

          {view === 'defects' && (
            <DefectExplorer defects={defects} />
          )}

          {view === 'settings' && (
            <div className="stack">
              <div className="tabs">
                <button className={settingsTab === 'camera' ? 'active' : ''} onClick={() => setSettingsTab('camera')}>Camera</button>
                <button className={settingsTab === 'job' ? 'active' : ''} onClick={() => setSettingsTab('job')}>Job Control</button>
                <button className={settingsTab === 'line' ? 'active' : ''} onClick={() => setSettingsTab('line')}>Line</button>
                <button className={settingsTab === 'installer' ? 'active' : ''} onClick={() => setSettingsTab('installer')}>Installer</button>
                <button className={settingsTab === 'retention' ? 'active' : ''} onClick={() => setSettingsTab('retention')}>Retention</button>
              </div>

              {settingsTab === 'camera' && (
                <CameraSettings
                  apiUrl={API_URL}
                  onSettingsChange={setIsSimulating}
                  cameraId={cameraId}
                  setCameraId={setCameraId}
                  useSim={isSimulating}
                  setUseSim={setIsSimulating}
                  exposure={cameraExposure}
                  setExposure={setCameraExposure}
                />
              )}

              {settingsTab === 'job' && (
                <JobControl apiUrl={API_URL} activeRecipe={activeRecipe} />
              )}

              {settingsTab === 'line' && (
                <>
                  <div className="card">
                    <h3>Line Settings</h3>
                    <div className="grid-two">
                      <div className="form-group">
                        <label>Roll Diameter (mm)</label>
                        <input
                          type="number"
                          min="0"
                          value={rollDiameter}
                          onChange={(e) => setRollDiameter(parseFloat(e.target.value || '0'))}
                        />
                      </div>
                      <div className="form-group">
                        <label>Core Diameter (mm)</label>
                        <input
                          type="number"
                          min="0"
                          value={coreDiameter}
                          onChange={(e) => setCoreDiameter(parseFloat(e.target.value || '0'))}
                        />
                      </div>
                      <div className="form-group">
                        <label>Material Thickness (mm)</label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={materialThickness}
                          onChange={(e) => setMaterialThickness(parseFloat(e.target.value || '0'))}
                        />
                      </div>
                    </div>
                  </div>
                  {isSimulating ? (
                    <SimulationLineSettings
                      labelPitch={labelPitch}
                      setLabelPitch={setLabelPitch}
                      repeatMm={repeatMm}
                      setRepeatMm={setRepeatMm}
                      cmarkEnabled={cmarkEnabled}
                      setCmarkEnabled={setCmarkEnabled}
                      jitterTolerance={jitterTolerance}
                      setJitterTolerance={setJitterTolerance}
                      fallbackEncoder={fallbackEncoder}
                      setFallbackEncoder={setFallbackEncoder}
                      encoderPitch={encoderPitch}
                      setEncoderPitch={setEncoderPitch}
                      mmPerTick={mmPerTick}
                      setMmPerTick={setMmPerTick}
                      encoderIntervalMs={encoderIntervalMs}
                      setEncoderIntervalMs={setEncoderIntervalMs}
                      encoderRunning={encoderRunning}
                      setEncoderRunning={setEncoderRunning}
                      onSave={handleSaveLineSettings}
                    />
                  ) : (
                    <LiveLineSettings
                      labelPitch={labelPitch}
                      setLabelPitch={setLabelPitch}
                      repeatMm={repeatMm}
                      setRepeatMm={setRepeatMm}
                      cmarkEnabled={cmarkEnabled}
                      setCmarkEnabled={setCmarkEnabled}
                      jitterTolerance={jitterTolerance}
                      setJitterTolerance={setJitterTolerance}
                      fallbackEncoder={fallbackEncoder}
                      setFallbackEncoder={setFallbackEncoder}
                      encoderPitch={encoderPitch}
                      setEncoderPitch={setEncoderPitch}
                      mmPerTick={mmPerTick}
                      setMmPerTick={setMmPerTick}
                      onSave={handleSaveLineSettings}
                    />
                  )}
                </>
              )}

              {settingsTab === 'installer' && (
                <div className="card">
                  <h3>Installer / PLC</h3>
                  <div className="form-group">
                    <label>Enable PLC</label>
                    <select value={plcEnabled ? 'yes' : 'no'} onChange={(e) => setPlcEnabled(e.target.value === 'yes')}>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>
                  <div className="grid-two">
                    <div className="form-group">
                      <label>PLC IP</label>
                      <input value={plcIp} onChange={(e) => setPlcIp(e.target.value)} placeholder="192.168.0.10" />
                    </div>
                    <div className="form-group">
                      <label>PLC Port</label>
                      <input type="number" value={plcPort} onChange={(e) => setPlcPort(parseInt(e.target.value || '0', 10))} />
                    </div>
                    <div className="form-group">
                      <label>PLC Unit ID</label>
                      <input type="number" value={plcUnitId} onChange={(e) => setPlcUnitId(parseInt(e.target.value || '0', 10))} />
                    </div>
                    <div className="form-group">
                      <label>Protocol</label>
                      <select value={plcProtocol} onChange={(e) => setPlcProtocol(e.target.value)}>
                        <option value="modbus_tcp">Modbus TCP</option>
                        <option value="opc_ua">OPC UA</option>
                        <option value="s7">S7</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>Timeout (ms)</label>
                      <input type="number" value={plcTimeoutMs} onChange={(e) => setPlcTimeoutMs(parseInt(e.target.value || '0', 10))} />
                    </div>
                  </div>
                  <h4>Signals</h4>
                  <div className="grid-two">
                    <div className="form-group">
                      <label>Tower Red Address</label>
                      <input value={plcTowerRed} onChange={(e) => setPlcTowerRed(e.target.value)} placeholder="DB1.DBX0.0" />
                    </div>
                    <div className="form-group">
                      <label>Tower Yellow Address</label>
                      <input value={plcTowerYellow} onChange={(e) => setPlcTowerYellow(e.target.value)} placeholder="DB1.DBX0.1" />
                    </div>
                    <div className="form-group">
                      <label>Tower Green Address</label>
                      <input value={plcTowerGreen} onChange={(e) => setPlcTowerGreen(e.target.value)} placeholder="DB1.DBX0.2" />
                    </div>
                    <div className="form-group">
                      <label>Buzzer Address</label>
                      <input value={plcBuzzer} onChange={(e) => setPlcBuzzer(e.target.value)} placeholder="DB1.DBX0.3" />
                    </div>
                    <div className="form-group">
                      <label>Stop Line Address</label>
                      <input value={plcStopLine} onChange={(e) => setPlcStopLine(e.target.value)} placeholder="DB1.DBX0.4" />
                    </div>
                  </div>
                  <button onClick={handleSaveInstallerSettings} className="btn-primary">Save Installer Settings</button>
                </div>
              )}

              {settingsTab === 'retention' && (
                <div className="card">
                  <h3>Retention</h3>
                  <div className="grid-two">
                    <div className="form-group">
                      <label>Thumbs (days)</label>
                      <input
                        type="number"
                        value={retention.thumbnails_days}
                        onChange={(e) => setRetention({ ...retention, thumbnails_days: parseInt(e.target.value || '0', 10) })}
                      />
                    </div>
                    <div className="form-group">
                      <label>Evidence (days)</label>
                      <input
                        type="number"
                        value={retention.evidence_days}
                        onChange={(e) => setRetention({ ...retention, evidence_days: parseInt(e.target.value || '0', 10) })}
                      />
                    </div>
                    <div className="form-group">
                      <label>Video (days)</label>
                      <input
                        type="number"
                        value={retention.video_days}
                        onChange={(e) => setRetention({ ...retention, video_days: parseInt(e.target.value || '0', 10) })}
                      />
                    </div>
                  </div>
                  <button onClick={handleRetentionSave} className="btn-primary">Save Retention</button>
                </div>
              )}
            </div>
          )}

          {view === 'reports' && (
            <ReportsPanel
              reports={reportHistory}
              reportDetail={reportDetail}
              onSelectReport={handleSelectReport}
              apiUrl={API_URL}
            />
          )}
        </div>

      </main>

      {/* Modals */}
      {showRoiEditor && (
        <ROIEditor
          masterImageStr={`${API_URL}/master-image`}
          initialRois={rois}
          onClose={() => setShowRoiEditor(false)}
          onSave={(newRois) => { setRois(newRois); setShowRoiEditor(false) }}
        />
      )}
      {showWizard && (
        <SetupWizard
          apiUrl={API_URL}
          onCancel={() => setShowWizard(false)}
          onComplete={() => { setShowWizard(false); setIsInspecting(true) }}
        />
      )}
      {showRecipeMgr && (
        <div className="modal-overlay">
          <div className="modal-frame">
            <RecipeManager
              apiUrl={API_URL}
              onSelectRecipe={(name) => { handleLoadRecipe(name); setShowRecipeMgr(false) }}
              onClose={() => setShowRecipeMgr(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default App
