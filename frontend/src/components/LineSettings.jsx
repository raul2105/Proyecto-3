const toFloat = (value, fallback = 0) => {
  const number = parseFloat(value)
  return Number.isFinite(number) ? number : fallback
}

const toInt = (value, fallback = 0) => {
  const number = parseInt(value, 10)
  return Number.isFinite(number) ? number : fallback
}

const clampNonNegative = (value, fallback = 0) => {
  if (!Number.isFinite(value) || value < 0) return fallback
  return value
}

const SensorConfigFields = ({
  labelPitch,
  setLabelPitch,
  repeatMm,
  setRepeatMm,
  cmarkEnabled,
  setCmarkEnabled,
  jitterTolerance,
  setJitterTolerance,
  fallbackEncoder,
  setFallbackEncoder,
  encoderPitch,
  setEncoderPitch,
  mmPerTick,
  setMmPerTick
}) => (
  <>
    <div className="form-group">
      <label>Label Pitch (m)</label>
      <input
        type="number"
        min="0"
        step="0.001"
        value={labelPitch}
        onChange={(e) => setLabelPitch(clampNonNegative(toFloat(e.target.value, 0), 0))}
      />
    </div>
    <div className="form-group">
      <label>Repeat (mm)</label>
      <input
        type="number"
        min="0"
        value={repeatMm}
        onChange={(e) => setRepeatMm(clampNonNegative(toFloat(e.target.value, 0), 0))}
      />
    </div>
    <div className="form-group">
      <label>Enable CMark</label>
      <select value={cmarkEnabled ? 'yes' : 'no'} onChange={(e) => setCmarkEnabled(e.target.value === 'yes')}>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </div>
    <div className="form-group">
      <label>Jitter Tolerance (ms)</label>
      <input
        type="number"
        min="0"
        value={jitterTolerance}
        onChange={(e) => setJitterTolerance(clampNonNegative(toInt(e.target.value, 20), 20))}
      />
    </div>
    <div className="form-group">
      <label>Fallback to Encoder</label>
      <select value={fallbackEncoder ? 'yes' : 'no'} onChange={(e) => setFallbackEncoder(e.target.value === 'yes')}>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </div>
    <div className="form-group">
      <label>Encoder Pitch (m)</label>
      <input
        type="number"
        min="0"
        step="0.001"
        value={encoderPitch}
        onChange={(e) => setEncoderPitch(clampNonNegative(toFloat(e.target.value, 0), 0))}
      />
    </div>
    <div className="form-group">
      <label>mm per Tick</label>
      <input
        type="number"
        min="0"
        step="0.01"
        value={mmPerTick}
        onChange={(e) => setMmPerTick(clampNonNegative(toFloat(e.target.value, 0), 0))}
      />
    </div>
  </>
)

export const SimulationLineSettings = ({
  labelPitch,
  setLabelPitch,
  repeatMm,
  setRepeatMm,
  cmarkEnabled,
  setCmarkEnabled,
  jitterTolerance,
  setJitterTolerance,
  fallbackEncoder,
  setFallbackEncoder,
  encoderPitch,
  setEncoderPitch,
  mmPerTick,
  setMmPerTick,
  encoderIntervalMs,
  setEncoderIntervalMs,
  encoderRunning,
  setEncoderRunning,
  onSave
}) => (
  <div className="card">
    <h3>Simulation Mode</h3>
    <p className="muted">Use the encoder simulator to drive pulses without hardware.</p>
    <SensorConfigFields
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
    />
    <div className="form-group">
      <label>Encoder Simulator (ms)</label>
      <input
        type="number"
        min="50"
        value={encoderIntervalMs}
        onChange={(e) => setEncoderIntervalMs(Math.max(50, clampNonNegative(toInt(e.target.value, 200), 200)))}
      />
    </div>
    <div className="row gap">
      <button className="btn-secondary" onClick={() => setEncoderRunning(!encoderRunning)}>
        {encoderRunning ? 'Stop Encoder' : 'Start Encoder'}
      </button>
    </div>
    <button onClick={onSave} className="btn-primary">Save Line Settings</button>
  </div>
)

export const LiveLineSettings = ({
  labelPitch,
  setLabelPitch,
  repeatMm,
  setRepeatMm,
  cmarkEnabled,
  setCmarkEnabled,
  jitterTolerance,
  setJitterTolerance,
  fallbackEncoder,
  setFallbackEncoder,
  encoderPitch,
  setEncoderPitch,
  mmPerTick,
  setMmPerTick,
  onSave
}) => (
  <div className="card">
    <h3>Live Mode</h3>
    <p className="muted">Configure real sensor parameters for connected encoder hardware.</p>
    <SensorConfigFields
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
    />
    <button onClick={onSave} className="btn-primary">Save Line Settings</button>
  </div>
)
