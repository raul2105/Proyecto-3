# 📖 Guía Rápida de Uso: Puntos 5, 6, 7

**Para desarrolladores** - Referencia rápida de APIs

---

## 🎨 Point 5: Color Monitoring

### Uso Básico

```python
from color_module import ColorMonitor, ColorTarget

# Inicializar
monitor = ColorMonitor()

# Crear target
target = ColorTarget(
    roi_id="color_1",
    name="Coca-Cola Red",
    bounds=(100, 100, 200, 200),
    l_target=40.5,
    a_target=72.3,
    b_target=28.1,
    warn_deltae=2.0,
    oot_deltae=5.0,
    deltae_formula="94"
)

# Agregar target
monitor.add_target(target)

# Calibrar
calibration_id = monitor.calibrate(frame, white_roi, black_roi, camera_id=0)

# Medir
measurement = monitor.measure_color_frame(frame, target)
print(f"ΔE: {measurement.delta_e:.1f} State: {measurement.state}")

# Obtener tendencia
trend = monitor.get_color_trend("color_1", window_duration_s=30.0)
print(f"Avg ΔE: {trend['avg_deltae']:.1f} Drift: {trend['drift_direction']}")
```

### Endpoints API

```bash
# Calibrar
curl -X POST "http://localhost:8000/color/calibrate?camera_id=0" \
  -H "Content-Type: application/json" \
  -d '{
    "white_roi": [100, 100, 200, 200],
    "black_roi": [300, 100, 400, 200]
  }'

# Obtener medición
curl "http://localhost:8000/color/measurement/color_1"

# Obtener tendencia
curl "http://localhost:8000/color/trend/color_1?window_s=30.0"
```

---

## 🔍 Point 6: Defect Classification

### Uso Básico

```python
from defects import DefectClassifier, DefectType, DefectSeverity

# Inicializar clasificador
classifier = DefectClassifier()

# Clasificar defecto
defect_data = {
    "x": 150.0,
    "y": 200.0,
    "area": 600.0,
    "aspect_ratio": 2.5,
    "color_variance": 15.0,
    "roi_id": "roi_1",
    "frame_number": 1234,
    "confidence": 0.92
}

recipe_thresholds = {
    "critical_area": 500,
    "major_area": 150,
    "critical_defect_types": ["missing_print", "register_error"]
}

classified = classifier.classify_defect(defect_data, recipe_thresholds)

print(f"ID: {classified.defect_id}")
print(f"Type: {classified.type.value}")
print(f"Severity: {classified.severity.value}")
print(f"Rule: {classified.rule_applied}")

# Obtener historial
log = classifier.get_classification_log()
summary = classifier.get_summary()
print(f"Total defects: {summary['total']}")
print(f"By severity: {summary['by_severity']}")
```

### Endpoints API

```bash
# Clasificar defecto
curl -X POST "http://localhost:8000/defects/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "x": 150.0,
    "y": 200.0,
    "area": 600.0,
    "aspect_ratio": 2.5,
    "roi_id": "roi_1",
    "frame_number": 1234
  }'

# Obtener historial
curl "http://localhost:8000/defects/classification-log"
```

---

## 🚨 Point 7: Alarm Rules & Actions

### Uso Básico

```python
from alarms import AlarmEngine, AlarmRule, TriggerType, ActionType, Action

# Inicializar motor
engine = AlarmEngine()

# Crear regla
rule = AlarmRule(
    rule_id="critical_defect",
    enabled=True,
    trigger_type=TriggerType.ON_DEFECT,
    trigger_config={"severity": "critical"},
    actions=[
        Action(
            action_type=ActionType.TOWER_LIGHT,
            color="red",
            duration_ms=1000
        ),
        Action(
            action_type=ActionType.PLC_WRITE,
            plc_address="stop_line",
            plc_value=1
        ),
        Action(
            action_type=ActionType.HMI_POPUP,
            popup_title="CRÍTICO",
            popup_message="Defecto detectado"
        )
    ],
    cooldown_ms=2000,
    description="Critical defect - stop and alert"
)

# Agregar regla
engine.add_rule(rule)

# Evaluar defecto (dispara alarma si cumple)
context = {
    "defect_rate_per_100m": 5.0,
    "color_measurements": []
}

triggered_rule = engine.evaluate_defect_alarm(defect, context)
if triggered_rule:
    print(f"✅ Alarma disparada: {triggered_rule}")

# Consultar estado de reglas
status = engine.get_rule_status("critical_defect")
print(f"Rule enabled: {status['enabled']}")
print(f"On cooldown: {status['on_cooldown']}")
print(f"Last triggered: {status['last_triggered']}")

# Obtener alarmas recientes
recent = engine.get_recent_alarms(count=5)
for alarm in recent:
    print(f"{alarm['alarm_id']}: {alarm['trigger_type']}")

# Estadísticas
stats = engine.get_alarm_statistics()
print(f"Total alarms: {stats['total_alarms']}")
```

### Endpoints API

```bash
# Agregar regla
curl -X POST "http://localhost:8000/alarms/rule" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "critical_defect",
    "enabled": true,
    "trigger_type": "on_defect",
    "trigger_config": {"severity": "critical"},
    "actions": [
      {
        "action_type": "TOWER_LIGHT",
        "color": "red",
        "duration_ms": 1000
      },
      {
        "action_type": "PLC_WRITE",
        "plc_address": "stop_line",
        "plc_value": 1
      }
    ],
    "cooldown_ms": 2000
  }'

# Obtener últimas alarmas
curl "http://localhost:8000/alarms/recent?count=10"

# Estado de todas las reglas
curl "http://localhost:8000/alarms/rules/status"

# Estado de regla específica
curl "http://localhost:8000/alarms/rules/critical_defect/status"

# Habilitar regla
curl -X POST "http://localhost:8000/alarms/rules/critical_defect/enable"

# Deshabilitar regla
curl -X POST "http://localhost:8000/alarms/rules/critical_defect/disable"

# Estadísticas
curl "http://localhost:8000/alarms/statistics"
```

---

## 🔧 Integración en Recetas

### Formato Recipe

```json
{
  "name": "Mi Receta",
  "client": "Acme Corp",
  "job_number": "2026-001",
  
  "color_rois": [
    {
      "roi_id": "color_1",
      "name": "Coca-Cola Red",
      "bounds": [100, 100, 200, 200],
      "lab_l": 40.5,
      "lab_a": 72.3,
      "lab_b": 28.1,
      "warn_deltae": 2.0,
      "oot_deltae": 5.0,
      "deltae_formula": "94"
    }
  ],
  
  "defect_thresholds": {
    "min_area": 50.0,
    "critical_area": 500.0,
    "major_area": 150.0,
    "sensitivity": 30.0
  },
  
  "alarm_rules": [
    {
      "rule_id": "critical_defect",
      "enabled": true,
      "trigger_type": "on_defect",
      "trigger_config": {
        "severity": "critical"
      },
      "actions": [
        {
          "action_type": "TOWER_LIGHT",
          "color": "red",
          "duration_ms": 1000
        },
        {
          "action_type": "PLC_WRITE",
          "plc_address": "stop_line",
          "plc_value": 1
        }
      ],
      "cooldown_ms": 2000,
      "description": "Critical defect"
    }
  ],
  
  "color_alarm_config": {
    "alert_on_oot": true,
    "alert_on_warn_duration_s": 10,
    "alert_on_oot_duration_s": 5
  }
}
```

---

## 📊 Enums de Referencia

### DefectType
```
ARTWORK_DIFF, MISSING_PRINT, REGISTER_ERROR,
EXCESS_INK, SMEAR, STREAK,
CONTAMINATION, SPOT, DIE_CUT_ERROR,
COLOR_OOT, UNKNOWN
```

### DefectSeverity
```
CRITICAL, MAJOR, MINOR
```

### TriggerType
```
ON_DEFECT, ON_RATE, ON_COLOR_OOT,
ON_REGISTER_LOST, ON_SENSOR_LOST, MANUAL
```

### ActionType
```
TOWER_LIGHT, BUZZER, PLC_WRITE,
HMI_POPUP, EMAIL, LOG_ONLY
```

### ColorState
```
OK, WARN, OUT_OF_TOLERANCE
```

### DeltaEFormula
```
"76" (CIE76)
"94" (CIE94 - default)
"2000" (CIE2000)
```

---

## ⚙️ Configuración Típica

### Thresholds de Color (Lab)
```
Coca-Cola Red:   L=40.5,  a=72.3,  b=28.1
Brand White:     L=95.0,  a=-1.0,  b=2.0
Process Yellow:  L=73.0,  a=10.0,  b=85.0
Process Cyan:    L=45.0,  a=-20.0, b=-30.0
```

### Tolerancias Recomendadas
```
Presión (critical): warn=1.5 ΔE, oot=3.0 ΔE
Tinta color:        warn=2.0 ΔE, oot=5.0 ΔE
Branding:           warn=2.5 ΔE, oot=6.0 ΔE
```

### Área de Defectos (px)
```
Critical:  > 500px
Major:     150-500px
Minor:     < 150px
```

---

## 🐛 Troubleshooting

### Color no calibra
```python
# Verificar que ROI no está vacío
if white_region.size == 0:
    raise ValueError("ROI regions are empty")
```

### DeltaE muy alto
```python
# Verificar fórmula: CIE94 es más restrictivo que CIE76
# Verificar conversi ón Lab: usar D65 illuminant
# Verificar referencia: white/black deben ser uniformes
```

### Alarmas no disparan
```python
# Verificar que regla está enabled
if not rule.enabled:
    print("Rule is disabled")

# Verificar cooldown
if engine._is_on_cooldown(rule_id, cooldown_ms):
    print("Rule is on cooldown")

# Verificar condiciones de trigger
print(f"Trigger config: {rule.trigger_config}")
```

---

**Última actualización**: 23 de Enero de 2026
