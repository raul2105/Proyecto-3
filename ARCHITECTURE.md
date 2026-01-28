# Arquitectura del Sistema - Flexo Inspection

## 1. Visión General del Sistema

El sistema **Flexo Inspection** es una solución completa de inspección visual basada en IA para procesos de impresión flexográfica. El sistema captura imágenes en tiempo real de rollos de material impreso, detecta defectos, compara contra un patrón maestro y proporciona retroalimentación a través de señales de control (PLC) para detener la línea en caso de defectos críticos.

### Componentes Principales:
- **Backend FastAPI**: Servidor de procesamiento de imágenes y lógica de negocio
- **Frontend React+Vite**: Interfaz de usuario interactiva para operarios
- **Base de Datos**: Trazabilidad de eventos, defectos y reportes
- **Integración PLC**: Comunicación con sistemas de control industrial

---

## 2. Arquitectura Backend

### 2.1 Stack Tecnológico
- **FastAPI**: Framework web asincrónico (velocidad, auto-documentación)
- **OpenCV**: Procesamiento de imágenes (detección, alineación, análisis)
- **NumPy**: Operaciones matriciales y cálculos numéricos
- **Pydantic**: Validación de datos y serialización
- **SQLite/PostgreSQL**: Persistencia de datos (trazabilidad)

### 2.2 Estructura de Módulos

```
backend/
├── main.py              # Punto de entrada, rutas API, orquestación
├── auth.py              # Autenticación y gestión de sesiones
├── camera.py            # Control de cámaras (OpenCV, videocaptura)
├── inspection.py        # Motor de detección y alineación de defectos
├── simulator.py         # Generador de defectos sintéticos (testing)
├── color_module.py      # Monitor de color y deltaE
├── diagnostics.py       # Monitoreo de salud del sistema
├── recipes.py           # Gestión de recetas (configuraciones de trabajos)
├── storage.py           # Persistencia de datos y trazabilidad
├── config.json          # Configuración del sistema
├── requirements.txt     # Dependencias Python
└── recipes/             # Almacenamiento de recetas JSON
```

### 2.3 Flujo de Procesamiento Principal

```
1. CAPTURA DE IMAGEN
   └─> CameraService.get_frame() → imagen en vivo

2. ALINEACIÓN
   └─> Inspector.align_images(master, live) → homografía

3. DETECCIÓN DE DEFECTOS
   └─> Inspector.detect_defects(aligned) → lista de defectos

4. ANÁLISIS DE COLOR
   └─> ColorMonitor.measure_color(roi) → Lab, deltaE

5. EVALUACIÓN DE ALARMAS
   └─> Evaluar reglas de alarma → generar eventos

6. PERSISTENCIA
   └─> storage.insert_defect() → base de datos

7. RESPUESTA PLC
   └─> plc.send_signal() → detener línea si es crítico
```

### 2.4 Modelos de Datos Principales

#### SystemState (Global)
```python
- master_image: np.ndarray         # Imagen de referencia
- inspector: Inspector             # Motor de detección
- camera: CameraService            # Controlador de cámara
- recipe_manager: RecipeManager    # Gestor de recetas
- events: deque(maxlen=500)       # Historial de eventos
- alarms: Dict                    # Alarmas activas
- defect_events: deque            # Eventos de defectos
```

#### Recipe
```python
- name: str                       # Nombre único
- client: str                     # Cliente
- exposure: float                 # Exposición de cámara
- tolerances: Dict                # Tolerancias de registro
- defect_thresholds: Dict         # Umbrales de defectos
- color_targets: List[ColorTarget] # Objetivos de color
- retention_days_images: int      # Retención de imágenes
```

#### Defect
```python
- type: str                       # Tipo (scratch, hole, color_shift)
- area: float                     # Área en píxeles²
- x, y: float                     # Posición
- severity: str                   # Crítico, Mayor, Menor
- timestamp: datetime             # Cuándo se detectó
```

---

## 3. Arquitectura Frontend

### 3.1 Stack Tecnológico
- **React 19**: Framework UI
- **Vite**: Build tool moderno
- **Recharts**: Visualización de datos
- **ESLint**: Linting

### 3.2 Estructura de Componentes

```
src/
├── App.jsx                    # Componente raíz, orquestación
├── App.css                    # Estilos globales
├── main.jsx                   # Punto de entrada
├── components/
│   ├── LoginModal.jsx         # Autenticación
│   ├── Dashboard.jsx          # KPIs y resumen
│   ├── InspectionView.jsx     # Vista de inspección en vivo
│   ├── DefectExplorer.jsx     # Exploración de defectos
│   ├── CameraSettings.jsx     # Configuración de cámara
│   ├── ColorDashboard.jsx     # Monitor de color
│   ├── RecipeManager.jsx      # Gestión de recetas
│   ├── ROIEditor.jsx          # Editor de regiones de interés
│   ├── AlarmEventsPanel.jsx   # Panel de alarmas
│   ├── DiagnosticsPanel.jsx   # Diagnósticos del sistema
│   ├── ReportsPanel.jsx       # Reportes
│   ├── JobSetup.jsx           # Configuración de trabajo
│   ├── SensorPanel.jsx        # Estado de sensores
│   ├── SetupWizard.jsx        # Asistente de configuración
│   └── ComparisonView.jsx     # Vista de comparación maestro/vivo
```

### 3.3 Flujo de Estado Global (App.jsx)

```
User & Auth
├── user: { username, role, token }
└── view: 'login' | 'dashboard' | 'inspection' | 'reports' | ...

Inspection Data
├── liveFrame: base64 string
├── masterFrame: base64 string
├── heatmapFrame: base64 string
├── defects: Array<Defect>
└── stats: { speed_m_min, yield_pct, defect_count }

Configuration
├── jobId: string
├── rollId: string
├── activeRecipe: string
└── cameraSettings: { exposure, gain, ... }

Monitoring
├── alarms: Array<Alarm>
├── events: Array<Event>
├── sensorStatus: Object
└── apiStatus: 'online' | 'offline'
```

### 3.4 Ciclos de Actualización

#### Loop de Inspección (Tiempo Real)
```javascript
useEffect(() => {
  if (!isInspecting) return
  
  const interval = setInterval(async () => {
    // Cada 1000ms (1s) o 250ms según useStream
    const res = await fetch('/inspection-frame')
    const data = res.json()
    
    setLiveFrame(data.live_image)
    setMasterFrame(data.master_image)
    setHeatmapFrame(data.heatmap_image)
    setDefects(data.defects)
    setStats(data.stats)
  }, useStream ? 1000 : 250)
  
  return () => clearInterval(interval)
}, [isInspecting])
```

#### Loop de Monitoreo de Sistema (Cada 2 segundos)
```javascript
useEffect(() => {
  const interval = setInterval(() => {
    // Actualizar alarmas
    fetch('/alarms').then(res => res.json()).then(setAlarms)
    
    // Actualizar eventos
    fetch('/events').then(res => res.json()).then(setEvents)
    
    // Actualizar sensores
    fetch('/sensors/status').then(res => res.json()).then(setSensorStatus)
    
    // Actualizar estado de línea
    fetch('/line/status').then(res => res.json()).then(setLineStatus)
  }, 2000)
  
  return () => clearInterval(interval)
}, [])
```

---

## 4. Flujo de Datos API

### 4.1 Endpoints Principales

#### Autenticación
```
POST /login
  Body: { username, password }
  Response: { token, role, username }
```

#### Inspección en Vivo
```
GET /inspection-frame
  Params: format=jpg|png, quality=0-100, scale=0-1
  Response: {
    live_image: base64,
    master_image: base64,
    heatmap_image: base64,
    defects: [{type, area, x, y, severity, ...}],
    stats: {speed_m_min, yield_pct, defect_count},
    color_measurement: {name, lab, deltaE, ...}
  }
```

#### Gestión de Recetas
```
GET /recipes
  Response: { recipes: ['Recipe1', 'Recipe2', ...] }

GET /recipes/{name}
  Response: Recipe (JSON)

POST /recipes
  Body: Recipe
  Response: { status, name }
```

#### Trazabilidad
```
GET /traceability/roll/{rollId}/defects
  Response: [{id, type, timestamp, severity, ...}]

GET /reports/history
  Params: limit=50
  Response: [Report, ...]

GET /reports/{reportId}
  Response: Report (con evidencia)
```

#### Control PLC
```
POST /plc/signal
  Body: { signal: 'stop_line' | 'tower_red' | 'buzzer', duration_ms: 500 }
  Response: { status: 'sent' }

GET /plc/status
  Response: { connected: bool, last_signal: timestamp }
```

---

## 5. Integración con PLC

### 5.1 Arquitectura de Comunicación

```
Flexo Inspection
     │
     ├─► PLC Gateway (Protocolo específico del PLC)
     │
     └─► PLC Industrial (Siemens/Mitsubishi/Allen-Bradley/Keyence)
            │
            ├─► Tower Light (Rojo/Amarillo/Verde)
            ├─► Buzzer
            ├─► Motor de parada
            ├─► Sistema de marcación
            └─► Sensores (Encoder, Foto-sensores)
```

### 5.2 Opciones de Integración PLC

#### A. **Siemens S7-1200/1500**
- Protocolo: Snap7 / RFC 1006
- Biblioteca Python: `python-snap7`
- Tiempo de respuesta: ~50ms
- Puerto: TCP 102

#### B. **Mitsubishi**
- Protocolo: MEWTOCOL (Serie) o MC Protocol (Ethernet)
- Biblioteca Python: `pymodbus` (Modbus TCP)
- Tiempo de respuesta: ~30ms
- Puerto: TCP 502 (Modbus)

#### C. **Allen-Bradley CompactLogix**
- Protocolo: EtherNet/IP
- Biblioteca Python: `pycomm3`
- Tiempo de respuesta: ~20ms
- Puerto: TCP 2222

#### D. **Keyence**
- Protocolo: Profi-Net o Ethernet/IP
- Biblioteca Python: `pymodbus`
- Tiempo de respuesta: ~25ms
- Puerto: TCP 502

### 5.3 Flujo de Control de Alarma

```
Defect Detected
    │
    ├─► Evaluate Rules
    │   - defect.severity == 'CRITICAL'?
    │   - defect.area > threshold?
    │   - defect_rate > max_per_frame?
    │
    ├─► YES → Raise Alarm
    │   - alarm_id generado
    │   - timestamp registrado
    │   - actions = alarm_actions[alarm_type]
    │
    ├─► Execute Actions
    │   ├─► Tower Red: plc.signal('tower_red')
    │   ├─► Buzzer: plc.signal('buzzer', duration=500ms)
    │   ├─► Stop Line: plc.signal('stop_line')
    │   ├─► Mark Segment: plc.signal('mark_segment')
    │   └─► Store Evidence: storage.insert_evidence()
    │
    └─► Cooldown
        - Evitar alertas duplicadas por 2 segundos
        - Permitir reset manual
```

---

## 6. Manejo de Errores y Resiliencia

### 6.1 Estrategias de Tolerancia a Fallos

| Escenario | Acción |
|-----------|--------|
| **Cámara Desconectada** | Cambiar a simulator, mantener línea en pausa, alerta |
| **PLC No Responde** | Log error, retry con backoff exponencial, alerta crítica |
| **Registro Fallido** | Usar transform anterior, log warning |
| **API Backend Caída** | Frontend muestra "Offline", reconecta cada 5s |
| **Base de Datos Llena** | Limpiar según retention_policy, archivar |
| **Memoria Insuficiente** | Limitar tamaño de deques, purgar caché |

### 6.2 Monitoreo de Salud (Diagnostics)

```python
Monitored Metrics:
- CPU Usage: % de utilización
- Memory: MB usado / disponible
- Camera FPS: frames por segundo
- Processing Latency: ms desde captura a análisis
- PLC Latency: ms desde señal enviada a confirmación
- DB Size: MB de base de datos
- Event Queue: # eventos pendientes
- Error Rate: # errores en últimos 5 min
```

---

## 7. Seguridad

### 7.1 Autenticación
- **Roles**: admin, operator, supervisor, quality
- **Tokens**: Generados en login, válidos por sesión
- **Contraseñas**: Plain-text en MVP → debe cambiar a hashing (bcrypt) en producción

### 7.2 Autorización
- Admin: Acceso total
- Operator: Inspección, dashboard
- Supervisor: Reportes, revisión de alarmas
- Quality: Solo lectura

### 7.3 API Security
- CORS configurado (actualmente permisivo, ajustar en producción)
- Validación de entrada con Pydantic
- Rate limiting: NO IMPLEMENTADO (agregar)
- HTTPS: NO IMPLEMENTADO (agregar para producción)

---

## 8. Persistencia de Datos

### 8.1 Estructura de Base de Datos

```sql
-- Trabajos
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    recipe_name TEXT,
    operator TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_defects INT,
    yield_pct FLOAT
);

-- Rollos
CREATE TABLE rolls (
    id TEXT PRIMARY KEY,
    job_id TEXT FOREIGN KEY,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    defects INT,
    length_m FLOAT
);

-- Defectos
CREATE TABLE defects (
    id TEXT PRIMARY KEY,
    roll_id TEXT FOREIGN KEY,
    type TEXT,
    area FLOAT,
    x FLOAT, y FLOAT,
    severity TEXT,
    timestamp TIMESTAMP
);

-- Eventos de Color
CREATE TABLE color_events (
    id TEXT PRIMARY KEY,
    roll_id TEXT FOREIGN KEY,
    roi_name TEXT,
    lab_l, lab_a, lab_b FLOAT,
    deltae FLOAT,
    timestamp TIMESTAMP
);

-- Alarmas
CREATE TABLE alarms (
    id TEXT PRIMARY KEY,
    type TEXT,
    severity TEXT,
    timestamp TIMESTAMP,
    actions TEXT,
    acknowledged BOOLEAN
);
```

---

## 9. Performance y Escalabilidad

### 9.1 Optimizaciones Implementadas
- Compresión JPEG de frames enviados a frontend
- Escalado de imágenes (60% de resolución)
- Deques con límite de tamaño (500-2000 elementos)
- ORB detector con nfeatures=5000 (balance velocidad/precisión)

### 9.2 Cuellos de Botella Identificados

| Cuello | Causa | Solución |
|--------|-------|----------|
| **Detección de Defectos** | Algoritmo ORB en cada frame | Usar GPU (CUDA/OpenCL) |
| **Transferencia de Imágenes** | Base64 + JSON grande | Enviar solo cambios (diff) |
| **Base de Datos** | SQLite en SSD lenta | Cambiar a PostgreSQL |
| **Procesamiento Color** | Cada ROI = análisis completo | Cache de resultados |

### 9.3 Objetivos de Performance

```
Latencia Total (Captura → Decisión PLC): < 100ms
FPS Inspección: 10-30 fps (según configuración)
CPU Backend: < 70%
Memoria Backend: < 500MB
Respuesta API: < 50ms (p95)
```

---

## 10. Flujos de Configuración

### 10.1 Setup Wizard
1. **Seleccionar Cámara**: Probar conexión, ajustar exposición
2. **Cargar Imagen Maestro**: PDF o imagen
3. **Definir ROIs**: Inspección, Color, Exclusión
4. **Tolerancias de Registro**: Posición, escala, rotación
5. **Umbrales de Defectos**: Área mínima, sensibilidad
6. **Configuración de PLC**: IP, puerto, tipo
7. **Guardar como Receta**

### 10.2 Ciclo de Vida de Inspección
1. **Pre-Inspección**: Cargar receta, configurar PLC
2. **Captura de Maestro**: Imagen de referencia clara
3. **Start Inspección**: Iniciar captura continua
4. **Monitoreo**: Detectar defectos, enviar señales PLC
5. **Stop Inspección**: Cerrar rollo, generar reporte
6. **Post-Análisis**: Revisar defectos, generar evidencia

---

## 11. Consideraciones Futuras

### 11.1 Escalabilidad
- [ ] Multi-cámara simultáneamente
- [ ] Procesamiento distribuido (múltiples workers)
- [ ] Cache distribuido (Redis)
- [ ] Message queue (RabbitMQ)

### 11.2 ML/IA Avanzada
- [ ] Deep Learning para detección (YOLO, Faster R-CNN)
- [ ] Clasificación automática de defectos
- [ ] Predicción de fallos
- [ ] Anomaly Detection

### 11.3 Integración Industrial
- [ ] Dashboard Grafana
- [ ] Logging centralizado (ELK Stack)
- [ ] OPC-UA gateway
- [ ] MES integration
- [ ] Mobile app

### 11.4 UX/UI
- [ ] Dark mode
- [ ] Multi-idioma
- [ ] Accesibilidad WCAG
- [ ] Responsive design mobile

---

## 12. Herramientas de Desarrollo

### 12.1 Testing
```bash
# Backend
pytest backend/ -v

# Frontend
npm test

# E2E
cypress run
```

### 12.2 Documentación
```bash
# API automática (FastAPI)
http://localhost:8001/docs

# Generación de PDFs
python generate_pdf.py
```

### 12.3 Debugging
```bash
# Backend logs
tail -f backend/logs/app.log

# Frontend DevTools
F12 en navegador

# PLC communication
Wireshark (capturar paquetes)
```

---

**Última Actualización**: 23 de Enero de 2026
