# Cambios Requeridos

## 1. Eliminar función Overlay

### Backend: `backend/main.py`

**Eliminar función completa (líneas 469-491)**:
```python
def mjpeg_overlay_stream(scale: float = 0.6, quality: int = 70, alpha: float = 0.5):
    while True:
        try:
            live = state.last_frames.get("live")
            master = state.last_frames.get("master")
            if live is None or master is None:
                time.sleep(0.1)
                continue
            if scale and scale > 0 and scale < 1:
                h, w = live.shape[:2]
                live = cv2.resize(live, (int(w * scale), int(h * scale)))
                master = cv2.resize(master, (int(w * scale), int(h * scale)))
            overlay = cv2.addWeighted(master, 1 - alpha, live, alpha, 0)
            success, encoded = cv2.imencode(".jpg", overlay, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
            if not success:
                continue
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n")
            time.sleep(0.04)
        except Exception as e:
            print(f"Overlay stream error: {e}")
            time.sleep(0.2)
```

**Eliminar endpoint (líneas 865-867)**:
```python
@app.get("/stream/overlay.mjpg")
def stream_overlay(scale: float = 0.6, quality: int = 70, alpha: float = 0.5):
    return StreamingResponse(mjpeg_overlay_stream(scale=scale, quality=quality, alpha=alpha), media_type="multipart/x-mixed-replace; boundary=frame")
```

### Frontend: `frontend/src/components/ComparisonView.jsx`

**Cambiar línea 3**:
```jsx
// Antes:
const ComparisonView = ({ masterSrc, liveSrc, heatmapSrc, overlaySrc, defects }) => {

// Después:
const ComparisonView = ({ masterSrc, liveSrc, heatmapSrc, defects }) => {
```

**Cambiar línea 4**:
```jsx
// Antes:
const [viewMode, setViewMode] = useState('split'); // 'split', 'overlay', 'heatmap'

// Después:
const [viewMode, setViewMode] = useState('split'); // 'split', 'heatmap'
```

**Eliminar botón Overlay (línea 80)**:
```jsx
// Eliminar esta línea:
<button className={viewMode === 'overlay' ? 'active' : ''} onClick={() => setViewMode('overlay')}>Overlay</button>
```

**Eliminar sección overlay completa (líneas 122-142)**:
```jsx
// Eliminar todo este bloque:
{viewMode === 'overlay' && (
    <div className="overlay-view">
        <div className="img-wrapper overlay-stack">
            {overlaySrc ? (
                <img className="overlay-img" src={overlaySrc} alt="Overlay stream" />
            ) : (
                masterSrc && liveSrc ? (
                    <>
                        <img className="overlay-img" src={masterSrc} alt="Master overlay" />
                        <img className="overlay-img overlay-top" src={liveSrc} alt="Live overlay" style={{ opacity }} />
                    </>
                ) : renderPlaceholder('Load a master and start inspection')
            )}
        </div>
        <div className="overlay-controls">
            {!overlaySrc && (
                <input className="range" type="range" min="0" max="1" step="0.1" value={opacity} onChange={e => setOpacity(parseFloat(e.target.value))} />
            )}
        </div>
    </div>
)}
```

### Frontend: `frontend/src/App.jsx`

**Eliminar prop overlaySrc (línea 604)**:
```jsx
// Antes:
<ComparisonView
    masterSrc={masterSrc}
    liveSrc={useStream ? `${API_URL}/stream/live.mjpg?scale=0.6&quality=70` : liveSrc}
    heatmapSrc={useStream ? `${API_URL}/stream/heatmap.mjpg?scale=0.6&quality=70` : heatmapSrc}
    overlaySrc={useStream ? `${API_URL}/stream/overlay.mjpg?scale=0.6&quality=70&alpha=0.5` : null}
    defects={defects}
/>

// Después:
<ComparisonView
    masterSrc={masterSrc}
    liveSrc={useStream ? `${API_URL}/stream/live.mjpg?scale=0.6&quality=70` : liveSrc}
    heatmapSrc={useStream ? `${API_URL}/stream/heatmap.mjpg?scale=0.6&quality=70` : heatmapSrc}
    defects={defects}
/>
```

---

## 2. Agregar Encoder simulado en modo REAL (cámara)

### Backend: `backend/main.py`

En la función `start_inspection` necesitas actualizar `current_mm` y `speed_mpm` incluso cuando uses cámara real.

**Buscar la función `start_inspection` y asegurar que actualiza encoder:**

Agregar después de `acquire_live_frame()` (aproximadamente línea 1685):

```python
# Simular encoder cuando no hay encoder real
if not state.use_simulator:
    # En modo cámara real, simular movimiento del encoder
    elapsed = time.time() - state.last_frame_ts if state.last_frame_ts else 0.05
    state.last_frame_ts = time.time()
    
    # Velocidad simulada en modo manual: 30 m/min
    simulated_speed_mpm = state.settings.get("simulated_speed_mpm", 30.0)
    distance_m = (simulated_speed_mpm / 60.0) * elapsed  # metros recorridos
    state.current_mm += distance_m * 1000.0  # convertir a mm
    state.speed_mpm = simulated_speed_mpm
    state.encoder_ticks += int(distance_m * 100)  # 100 ticks por metro
```

---

## 3. Agregar botón "Stop Job" en Settings

### Frontend: `frontend/src/components/CameraSettings.jsx`

Agregar botón después de los controles de cámara:

```jsx
<div className="form-group">
    <h4>Job Control</h4>
    <button 
        className="btn-stop-job"
        onClick={async () => {
            if (window.confirm('¿Detener trabajo actual? Se generará reporte final.')) {
                try {
                    const response = await fetch(`${API_URL}/job/stop`, { method: 'POST' });
                    if (response.ok) {
                        alert('Trabajo detenido exitosamente');
                    }
                } catch (error) {
                    console.error('Error stopping job:', error);
                    alert('Error al detener trabajo');
                }
            }
        }}
    >
        Stop Job
    </button>
</div>
```

Agregar CSS en `frontend/src/App.css`:

```css
.btn-stop-job {
    background: #e74c3c;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    width: 100%;
    margin-top: 10px;
}

.btn-stop-job:hover {
    background: #c0392b;
}
```

---

## 4. Agregar configuración de velocidad simulada

### Backend: `backend/main.py`

En `state.settings` (línea 139 aprox), agregar:

```python
"simulated_speed_mpm": 30.0,  # Velocidad simulada en modo cámara real
```

### Frontend: Agregar control de velocidad en Settings

En `CameraSettings.jsx`, agregar slider de velocidad:

```jsx
<div className="form-group">
    <label>Simulated Speed (m/min)</label>
    <input 
        type="range" 
        min="10" 
        max="100" 
        step="5"
        defaultValue={30}
        onChange={async (e) => {
            try {
                await fetch(`${API_URL}/settings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ simulated_speed_mpm: parseFloat(e.target.value) })
                });
            } catch (error) {
                console.error('Error updating speed:', error);
            }
        }}
    />
    <span>{speedValue} m/min</span>
</div>
```

---

## Resumen de Archivos a Modificar

1. **backend/main.py**
   - Eliminar `mjpeg_overlay_stream()` (líneas 469-491)
   - Eliminar endpoint `/stream/overlay.mjpg` (líneas 865-867)
   - Agregar actualización de encoder en modo cámara real en `start_inspection`
   - Agregar `simulated_speed_mpm` en settings

2. **frontend/src/components/ComparisonView.jsx**
   - Remover prop `overlaySrc`
   - Remover botón Overlay
   - Remover sección viewMode === 'overlay'
   - Cambiar comentario de viewMode

3. **frontend/src/App.jsx**
   - Remover prop `overlaySrc` en ComparisonView

4. **frontend/src/components/CameraSettings.jsx**
   - Agregar botón "Stop Job"
   - Agregar slider de velocidad simulada

5. **frontend/src/App.css**
   - Agregar estilos para `.btn-stop-job`
