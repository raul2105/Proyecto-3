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
  setMmPerTick,
  encoderWatchdogMs,
  setEncoderWatchdogMs
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
    <div className="form-group">
      <label>Encoder Watchdog (ms)</label>
      <input
        type="number"
        min="0"
        value={encoderWatchdogMs}
        onChange={(e) => setEncoderWatchdogMs(clampNonNegative(toInt(e.target.value, 1000), 1000))}
      />
    </div>
  </>
)

const MicroDefectFields = ({
  microWindowM,
  setMicroWindowM,
  microStepM,
  setMicroStepM,
  microRateYellow,
  setMicroRateYellow,
  microRateRed,
  setMicroRateRed,
  microRateStop,
  setMicroRateStop,
  microCountStop,
  setMicroCountStop,
  microMinAlarmM,
  setMicroMinAlarmM,
  microMinMm,
  setMicroMinMm,
  microMaxMm,
  setMicroMaxMm,
  pixelsPerMm,
  setPixelsPerMm,
  microMaxAreaPx,
  setMicroMaxAreaPx
}) => (
  <div className="card">
    <h4>Micro Defect Rules</h4>
    <div className="grid-two">
      <div className="form-group">
        <label>Window (m)</label>
        <input
          type="number"
          min="0"
          step="0.1"
          value={microWindowM}
          onChange={(e) => setMicroWindowM(clampNonNegative(toFloat(e.target.value, 20), 20))}
        />
      </div>
      <div className="form-group">
        <label>Step Update (m)</label>
        <input
          type="number"
          min="0"
          step="0.05"
          value={microStepM}
          onChange={(e) => setMicroStepM(clampNonNegative(toFloat(e.target.value, 0.5), 0.5))}
        />
      </div>
      <div className="form-group">
        <label>Min Length for Alarm (m)</label>
        <input
          type="number"
          min="0"
          step="0.1"
          value={microMinAlarmM}
          onChange={(e) => setMicroMinAlarmM(clampNonNegative(toFloat(e.target.value, 10), 10))}
        />
      </div>
      <div className="form-group">
        <label>Yellow Rate (/m)</label>
        <input
          type="number"
          min="0"
          step="0.1"
          value={microRateYellow}
          onChange={(e) => setMicroRateYellow(clampNonNegative(toFloat(e.target.value, 8), 8))}
        />
      </div>
      <div className="form-group">
        <label>Red Rate (/m)</label>
        <input
          type="number"
          min="0"
          step="0.1"
          value={microRateRed}
          onChange={(e) => setMicroRateRed(clampNonNegative(toFloat(e.target.value, 15), 15))}
        />
      </div>
      <div className="form-group">
        <label>Stop Rate (/m)</label>
        <input
          type="number"
          min="0"
          step="0.1"
          value={microRateStop}
          onChange={(e) => setMicroRateStop(clampNonNegative(toFloat(e.target.value, 25), 25))}
        />
      </div>
      <div className="form-group">
        <label>Stop Count (window)</label>
        <input
          type="number"
          min="0"
          value={microCountStop}
          onChange={(e) => setMicroCountStop(clampNonNegative(toInt(e.target.value, 400), 400))}
        />
      </div>
      <div className="form-group">
        <label>Micro Min Size (mm)</label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={microMinMm}
          onChange={(e) => setMicroMinMm(clampNonNegative(toFloat(e.target.value, 0.05), 0.05))}
        />
      </div>
      <div className="form-group">
        <label>Micro Max Size (mm)</label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={microMaxMm}
          onChange={(e) => setMicroMaxMm(clampNonNegative(toFloat(e.target.value, 0.08), 0.08))}
        />
      </div>
      <div className="form-group">
        <label>Pixels per mm</label>
        <input
          type="number"
          min="0"
          step="0.1"
          value={pixelsPerMm}
          onChange={(e) => setPixelsPerMm(clampNonNegative(toFloat(e.target.value, 0), 0))}
        />
      </div>
      <div className="form-group">
        <label>Max Area Fallback (px²)</label>
        <input
          type="number"
          min="0"
          value={microMaxAreaPx}
          onChange={(e) => setMicroMaxAreaPx(clampNonNegative(toFloat(e.target.value, 120), 120))}
        />
      </div>
    </div>
  </div>
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
  encoderWatchdogMs,
  setEncoderWatchdogMs,
  encoderIntervalMs,
  setEncoderIntervalMs,
  encoderRunning,
  setEncoderRunning,
  microWindowM,
  setMicroWindowM,
  microStepM,
  setMicroStepM,
  microRateYellow,
  setMicroRateYellow,
  microRateRed,
  setMicroRateRed,
  microRateStop,
  setMicroRateStop,
  microCountStop,
  setMicroCountStop,
  microMinAlarmM,
  setMicroMinAlarmM,
  microMinMm,
  setMicroMinMm,
  microMaxMm,
  setMicroMaxMm,
  pixelsPerMm,
  setPixelsPerMm,
  microMaxAreaPx,
  setMicroMaxAreaPx,
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
      encoderWatchdogMs={encoderWatchdogMs}
      setEncoderWatchdogMs={setEncoderWatchdogMs}
    />
    <MicroDefectFields
      microWindowM={microWindowM}
      setMicroWindowM={setMicroWindowM}
      microStepM={microStepM}
      setMicroStepM={setMicroStepM}
      microRateYellow={microRateYellow}
      setMicroRateYellow={setMicroRateYellow}
      microRateRed={microRateRed}
      setMicroRateRed={setMicroRateRed}
      microRateStop={microRateStop}
      setMicroRateStop={setMicroRateStop}
      microCountStop={microCountStop}
      setMicroCountStop={setMicroCountStop}
      microMinAlarmM={microMinAlarmM}
      setMicroMinAlarmM={setMicroMinAlarmM}
      microMinMm={microMinMm}
      setMicroMinMm={setMicroMinMm}
      microMaxMm={microMaxMm}
      setMicroMaxMm={setMicroMaxMm}
      pixelsPerMm={pixelsPerMm}
      setPixelsPerMm={setPixelsPerMm}
      microMaxAreaPx={microMaxAreaPx}
      setMicroMaxAreaPx={setMicroMaxAreaPx}
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
  encoderWatchdogMs,
  setEncoderWatchdogMs,
  microWindowM,
  setMicroWindowM,
  microStepM,
  setMicroStepM,
  microRateYellow,
  setMicroRateYellow,
  microRateRed,
  setMicroRateRed,
  microRateStop,
  setMicroRateStop,
  microCountStop,
  setMicroCountStop,
  microMinAlarmM,
  setMicroMinAlarmM,
  microMinMm,
  setMicroMinMm,
  microMaxMm,
  setMicroMaxMm,
  pixelsPerMm,
  setPixelsPerMm,
  microMaxAreaPx,
  setMicroMaxAreaPx,
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
      encoderWatchdogMs={encoderWatchdogMs}
      setEncoderWatchdogMs={setEncoderWatchdogMs}
    />
    <MicroDefectFields
      microWindowM={microWindowM}
      setMicroWindowM={setMicroWindowM}
      microStepM={microStepM}
      setMicroStepM={setMicroStepM}
      microRateYellow={microRateYellow}
      setMicroRateYellow={setMicroRateYellow}
      microRateRed={microRateRed}
      setMicroRateRed={setMicroRateRed}
      microRateStop={microRateStop}
      setMicroRateStop={setMicroRateStop}
      microCountStop={microCountStop}
      setMicroCountStop={setMicroCountStop}
      microMinAlarmM={microMinAlarmM}
      setMicroMinAlarmM={setMicroMinAlarmM}
      microMinMm={microMinMm}
      setMicroMinMm={setMicroMinMm}
      microMaxMm={microMaxMm}
      setMicroMaxMm={setMicroMaxMm}
      pixelsPerMm={pixelsPerMm}
      setPixelsPerMm={setPixelsPerMm}
      microMaxAreaPx={microMaxAreaPx}
      setMicroMaxAreaPx={setMicroMaxAreaPx}
    />
    <button onClick={onSave} className="btn-primary">Save Line Settings</button>
  </div>
)
