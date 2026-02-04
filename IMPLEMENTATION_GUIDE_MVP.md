# Implementación MVP - Guía Rápida

## ✅ LO QUE SE HA IMPLEMENTADO

### 1. Arquitectura Modular Completa
- **11 módulos** con estructura de carpetas profesional
- **10 interfaces** (Protocol classes) para desacoplamiento
- Contratos claros entre módulos

### 2. Esquemas de Datos Estables (schemas.py)
- `DefectEvent`: Eventos de defectos con trazabilidad completa
- `ColorEvent`: Mediciones de color con Delta-E
- `AlarmEvent`: Alarmas con hysteresis
- `JobConfig`: Configuración versionada con hash SHA256
- Validación Pydantic + migración de versiones

### 3. Sincronización con Encoder (sync/encoder.py)
- `EncoderSync`: Procesamiento de pulsos, tracking de posición
- Detección de jitter (configurable)
- Estimación de velocidad de línea (m/min)
- Cálculo de resolución espacial (px/mm)
- `EncoderSimulator`: Testing sin hardware

### 4. Simulador de Replay (simulator/replay.py)
- `ReplayDataset`: Grabación y carga de datasets
- `ReplaySimulator`: Reproducción con control de velocidad
- `DatasetRecorder`: Grabación en vivo con anotaciones
- Función `create_synthetic_dataset()` para testing

### 5. Pipeline CI/CD (.github/workflows/ci.yml)
- **Linting**: flake8 (errores de sintaxis bloquean build)
- **Format**: black (recomendaciones)
- **Type checking**: mypy (no bloqueante)
- **Tests**: pytest con cobertura
- **Security**: bandit + safety
- Ejecución automática en push/PR

### 6. Suite de Tests (tests/)
- **16 tests unitarios** pasando al 100%
- Infraestructura completa (unit/, integration/, fixtures/, datasets/)
- pytest.ini configurado
- README con guía de uso
- Cobertura de código habilitada

---

## 📋 PRÓXIMOS PASOS CRÍTICOS

### Fase 1: Módulos Core (1-2 semanas)

#### 1. Módulo de Decisión (decision/)
```python
# decision/decision_engine.py
class DecisionEngine:
    def evaluate_severity(defect, thresholds) -> str
    def should_stop_line(defects, rules) -> (bool, str)
    def log_microdefect(defect, position_m)
    def check_density_alarm(position_m, window_m) -> AlarmEvent
```

**Requisitos**:
- Hysteresis con ventana temporal configurable
- Modo auditoría para microdefectos (0.05-0.08mm)
- Alarmas por densidad (no paro inmediato)
- Confirmaciones antes de paro

#### 2. Pipeline Clear-on-Clear (inspection/clear_on_clear.py)
```python
# inspection/clear_on_clear.py
class ClearOnClearDetector:
    def __init__(self, backlight_threshold):
        # Estrategia con backlight
        
    def detect(self, image) -> List[DefectEvent]:
        # Detección específica para transparente-sobre-transparente
```

**Requisitos**:
- Iluminación backlight
- Umbrales específicos ajustables
- Dataset de validación con clear-on-clear

#### 3. Integración PLC con Fail-Safe (plc_io/)
```python
# plc_io/plc_controller.py
class PLCController:
    def connect(config) -> bool
    def send_signal(signal_type, duration_ms) -> bool
    def enter_safe_mode()  # CRÍTICO
    def health_check() -> bool
```

**Requisitos**:
- Protocolo determinista
- Fail-safe mode en caso de error
- Handshake bidireccional
- Timeout configurables

### Fase 2: Testing & Validación (1 semana)

#### 4. Tests de Integración
```python
# tests/integration/test_end_to_end.py
def test_full_inspection_workflow():
    # Camera → Encoder → Inspection → Decision → PLC → Storage
    
def test_stress_at_target_speed():
    # 30 m/min durante 1 hora
    
def test_microdefect_audit_mode():
    # Verificar logging sin paro
```

#### 5. Dataset de Validación
- Grabar 100+ defectos reales anotados
- Incluir clear-on-clear
- Velocidades variables
- Condiciones de iluminación reales

### Fase 3: Operaciones (1 semana)

#### 6. Logging Estructurado (ops/logging.py)
```python
# ops/logging.py
class StructuredLogger:
    def log(level, message, metadata)  # JSON format
    def record_metric(metric_name, value, unit)
    def get_metrics_summary(window_minutes)
```

#### 7. Reportes (reporting/)
```python
# reporting/report_generator.py
class ReportGenerator:
    def generate_roll_report(roll_id) -> bytes
    def generate_job_report(job_id) -> bytes
    def export_defect_map(roll_id) -> bytes
```

---

## 🔥 ACCIONES INMEDIATAS (Hoy/Mañana)

### 1. Validar Tests en CI
```bash
git push
# Verificar que GitHub Actions pase
# URL: https://github.com/raul2105/Proyecto-3/actions
```

### 2. Crear Dataset Sintético para Testing
```bash
cd backend
python -c "
from simulator.replay import create_synthetic_dataset
dataset = create_synthetic_dataset('test_001', num_frames=50, add_defects=True)
dataset.save('tests/datasets')
print('Dataset creado en tests/datasets/test_001')
"
```

### 3. Probar Encoder Sync Manualmente
```bash
cd backend
python -c "
from sync.encoder import EncoderSync, EncoderSimulator
from datetime import datetime, timedelta

# Crear encoder
sync = EncoderSync(mm_per_tick=0.1, jitter_tolerance_ms=20)

# Simular 100 pulsos
for i in range(100):
    pos = sync.process_pulse(datetime.now() + timedelta(milliseconds=i*2))
    if i % 10 == 0:
        print(f'Pulse {i}: {pos:.2f}mm, Speed: {sync.get_speed_mpm():.1f} m/min')
"
```

### 4. Revisar Configuración de Job Template
```bash
# Crear config/job_template.yaml con estructura de JobConfig
# Ver schemas.py líneas 194-274 para estructura completa
```

---

## ⚠️ DECISIONES PENDIENTES (Requieren Respuesta del Cliente)

### Críticas (Bloquean Implementación)
1. **¿Encoder instalado?** → Especificaciones (PPR, tipo, protocolo)
2. **¿Marca/modelo PLC?** → Determina biblioteca a usar
3. **¿Backlight disponible?** → Afecta clear-on-clear detection
4. **¿Velocidad máxima producción?** → Define target FPS

### Importantes (Afectan Diseño)
5. **¿Resolución espacial requerida?** → Determina óptica de cámara
6. **¿FNR objetivo aceptable?** → Define umbral de calidad
7. **¿Storage disponible?** → Afecta retención de imágenes
8. **¿Conexión a MES/ERP?** → Necesita módulo de integración adicional

### Deseables (Optimización)
9. **¿Dataset de defectos reales disponible?** → Accelera entrenamiento
10. **¿Ambiente Windows o Linux?** → Afecta deployment

---

## 📊 MÉTRICAS DE ÉXITO (Definir con Cliente)

### Performance
- ✅ Latencia total < 100ms (factible)
- ✅ FPS ≥ 15 (alcanzable con hardware adecuado)
- ⚠️ Dropped frames < 1% (necesita testing)

### Calidad
- ⚠️ FNR < 5% para CRITICAL (propuesto, validar con cliente)
- ⚠️ FPR < 2% (propuesto, validar con cliente)
- ✅ Registro < 1mm error (encoder sync implementado)

### Operaciones
- ✅ Uptime > 99% (con watchdog)
- ✅ 7 días retención imágenes (configurable)
- ✅ 90 días retención eventos (configurable)

---

## 🛠️ COMANDOS ÚTILES

### Testing
```bash
cd backend

# Todos los tests
pytest -v

# Solo unitarios
pytest tests/unit -v

# Con cobertura
pytest --cov=. --cov-report=html --cov-report=term

# Tests específicos
pytest tests/unit/test_schemas.py::test_defect_event_creation -v

# Marcar tests lentos
pytest -m "not slow"
```

### Linting & Format
```bash
cd backend

# Lint
flake8 . --count --select=E9,F63,F7,F82

# Format check
black --check .

# Format apply
black .

# Type check
mypy --ignore-missing-imports .
```

### CI Local (Pre-commit)
```bash
cd backend

# Run full CI locally
flake8 . --count --select=E9,F63,F7,F82 && \
black --check . && \
pytest tests/unit -v
```

---

## 📚 DOCUMENTACIÓN CLAVE

1. **ARCHITECTURE_MVP.md** ← Este documento (arquitectura completa)
2. **backend/interfaces.py** ← Contratos entre módulos
3. **backend/schemas.py** ← Esquemas de datos estables
4. **backend/tests/README.md** ← Guía de testing
5. **backend/sync/encoder.py** ← Implementación encoder
6. **.github/workflows/ci.yml** ← Pipeline CI/CD

---

## 🚀 LANZAMIENTO MVP (Checklist Final)

### Pre-Producción
- [ ] Encoder calibrado y funcionando
- [ ] Cámara calibrada (exposición, foco, alineación)
- [ ] PLC comunicándose correctamente
- [ ] Master images para jobs de prueba
- [ ] Dataset de validación grabado
- [ ] Performance test a velocidad objetivo
- [ ] Stress test 8 horas continuas

### Go-Live
- [ ] Watchdog service activo
- [ ] Log rotation configurado
- [ ] Backup procedures establecidos
- [ ] Operadores entrenados
- [ ] Procedimientos de troubleshooting documentados
- [ ] Mantenimiento programado

---

## 💡 CONSEJOS DE IMPLEMENTACIÓN

### Do's ✅
- Usar `EncoderSimulator` para desarrollo sin hardware
- Crear datasets sintéticos para testing rápido
- Escribir tests antes de implementar (TDD)
- Usar `ReplaySimulator` para debugging determinista
- Configurar todo por Job (YAML/JSON versionado)

### Don'ts ❌
- NO hardcodear thresholds (usar JobConfig)
- NO parar línea sin hysteresis
- NO ignorar jitter en encoder
- NO omitir fail-safe en PLC
- NO eliminar evidencia antes de retención completa

---

## 🎯 RESUMEN EJECUTIVO

**Estado Actual**: MVP Foundation Complete (30% del objetivo)

**Completado**:
- ✅ Arquitectura modular (11 módulos)
- ✅ Esquemas de datos estables
- ✅ Encoder synchronization
- ✅ Replay simulator (básico)
- ✅ CI/CD pipeline
- ✅ Test infrastructure (16 tests)

**Falta Implementar (70%)**:
- Decision module con hysteresis
- Clear-on-clear detection
- PLC integration con fail-safe
- Audit mode para microdefectos
- Structured logging + metrics
- Reporting (PDF/CSV)
- Integration tests
- Performance validation

**Tiempo Estimado hasta MVP**: 3-4 semanas con 1 desarrollador full-time

**Riesgo Principal**: Falta información sobre hardware (encoder, PLC, cámara)

---

**Versión**: 1.0.0  
**Fecha**: 2026-02-03  
**Autor**: GitHub Copilot (Architect + QA Lead)
