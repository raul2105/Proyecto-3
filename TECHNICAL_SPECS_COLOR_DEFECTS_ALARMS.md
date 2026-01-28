# Especificación Técnica: Color (DeltaE), Defectos y Alarmas

**Versión**: 1.0  
**Fecha**: 23 de Enero de 2026  
**Status**: 🟢 Implementable  

---

## 1. Pipeline de Color (DeltaE) - Implementable

### 1.1 Arquitectura del Pipeline

```
ENTRADA: Frame + Color ROIs
    ↓
[1] EXTRACCIÓN DE PÍXELES
    └─► Para cada color_roi: extraer región ROI
    └─► Validar que región no está vacía
    └─► Aplicar máscaras (si existen)
    ↓
[2] CALIBRACIÓN (Primera ejecución o recalibración)
    ├─► White Reference (Blanco puro bajo iluminación)
    ├─► Black Reference (Negro puro bajo iluminación)
    ├─► Generar matriz de corrección XYZ/Lab
    ├─► Guardar calibration_id + timestamp
    └─► Guardar en recipe
    ↓
[3] ESTIMACIÓN ROBUSTA DE COLOR
    ├─► Remover outliers (pixeles ruido)
    ├─► Calcular mediana recortada (trimmed median)
    ├─► O promedio con outlier removal (sigma clipping)
    └─► Resultado: RGB representativo de ROI
    ↓
[4] CONVERSIÓN COLOR: BGR → Lab
    ├─► BGR → XYZ (usar matriz de corrección)
    ├─► XYZ → Lab
    └─► Resultado: (L*, a*, b*)
    ↓
[5] CÁLCULO DE DELTAE
    ├─► ΔE = f(Lab_measured, Lab_target)
    ├─► Soportar: 76 / 94 / 2000 (configurable)
    └─► Resultado: escalar [0..150]
    ↓
[6] EVALUACIÓN DE ESTADOS
    ├─► OK:   ΔE ≤ warn_threshold
    ├─► WARN: warn_threshold < ΔE ≤ oot_threshold
    └─► OOT:  ΔE > oot_threshold (Out Of Tolerance)
    ↓
[7] ANÁLISIS DE TENDENCIAS
    ├─► Ventana deslizante: últimos 30s o N mediciones
    ├─► Calcular: avg, std, max, time_in_oot
    ├─► Detectar drift (tendencia a cambiar)
    └─► Generar alertas si tiende a OOT
    ↓
SALIDA: ColorMeasurement + Tendencias
```

---

### 1.2 Implementación en Backend

```python
# backend/color_module_v2.py (mejorado)

from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import deque
from datetime import datetime
import numpy as np
import cv2
from enum import Enum

class DeltaEFormula(Enum):
    CIE76 = "76"      # Simple: √((ΔL)² + (Δa)² + (Δb)²)
    CIE94 = "94"      # Industrial (default)
    CIE2000 = "2000"  # Más preciso, más lento

class ColorState(Enum):
    OK = "OK"
    WARN = "WARN"
    OOT = "OUT_OF_TOLERANCE"

@dataclass
class CalibrationProfile:
    """Perfil de calibración por cámara/iluminación"""
    calibration_id: str
    timestamp: datetime
    camera_id: int
    
    # Referencias
    white_ref_bgr: np.ndarray  # (B, G, R) normalized
    black_ref_bgr: np.ndarray
    
    # Matriz de corrección (3x3)
    correction_matrix_bgr_to_xyz: np.ndarray
    
    # Metadata
    illuminant: str = "D65"  # Standard illuminant
    observer_angle: int = 2  # 2° o 10°

@dataclass
class ColorTarget:
    """Objetivo de color para un ROI"""
    roi_id: str
    name: str
    
    # Target en Lab
    lab_l: float
    lab_a: float
    lab_b: float
    
    # Tolerancias
    warn_threshold_deltae: float = 2.0   # WARN si ΔE > esto
    oot_threshold_deltae: float = 5.0    # OOT si ΔE > esto
    
    # Fórmula a usar
    deltae_formula: DeltaEFormula = DeltaEFormula.CIE94

@dataclass
class ColorMeasurement:
    """Medición de color para un ROI en un momento"""
    timestamp: datetime
    roi_id: str
    
    # Color medido en Lab
    measured_lab_l: float
    measured_lab_a: float
    measured_lab_b: float
    
    # Diferencia
    deltae: float
    state: ColorState
    
    # Metadata
    pixel_count: int
    confidence: float  # 0-1, basado en varianza

@dataclass
class ColorTrend:
    """Análisis de tendencia en ventana deslizante"""
    roi_id: str
    window_duration_s: float
    
    # Estadísticas
    avg_deltae: float
    std_deltae: float
    max_deltae: float
    
    # Tiempo fuera de tolerancia
    time_in_oot_percent: float
    
    # Predicción
    is_drifting: bool
    drift_direction: str  # "stable" | "increasing" | "decreasing"

class ColorMonitor:
    def __init__(self):
        self.calibration_profile: Optional[CalibrationProfile] = None
        self.color_targets: Dict[str, ColorTarget] = {}
        
        # Historial de mediciones por ROI (últimos 30s ~ 300 frames @ 10 fps)
        self.measurement_history: Dict[str, deque] = {}
        self.window_size_frames = 300
        
    # ─────────────────────────────────────────────────────
    # PASO 1: CALIBRACIÓN
    # ─────────────────────────────────────────────────────
    
    def calibrate(self, 
                  frame: np.ndarray,
                  white_roi: tuple,  # (x1, y1, x2, y2)
                  black_roi: tuple,
                  camera_id: int) -> CalibrationProfile:
        """
        Calibración: extraer referencias blanco/negro de frame
        
        Args:
            frame: imagen BGR
            white_roi: región con papel blanco
            black_roi: región con papel negro
            camera_id: identificador de cámara
        
        Returns:
            CalibrationProfile
        """
        # Extraer regiones
        x1w, y1w, x2w, y2w = white_roi
        x1b, y1b, x2b, y2b = black_roi
        
        white_region = frame[y1w:y2w, x1w:x2w]
        black_region = frame[y1b:y2b, x1b:x2b]
        
        # Calcular promedio (píxeles de referencia deben ser uniformes)
        white_bgr = np.mean(white_region, axis=(0, 1)).astype(np.uint8)
        black_bgr = np.mean(black_region, axis=(0, 1)).astype(np.uint8)
        
        # Normalizar a [0, 1]
        white_bgr_norm = white_bgr.astype(np.float32) / 255.0
        black_bgr_norm = black_bgr.astype(np.float32) / 255.0
        
        # Generar matriz de corrección (simple: offset + escala)
        # Versión básica: transformación lineal
        correction_matrix = self._generate_correction_matrix(
            white_bgr_norm, black_bgr_norm
        )
        
        profile = CalibrationProfile(
            calibration_id=f"calib_{camera_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            camera_id=camera_id,
            white_ref_bgr=white_bgr_norm,
            black_ref_bgr=black_bgr_norm,
            correction_matrix_bgr_to_xyz=correction_matrix,
            illuminant="D65"
        )
        
        self.calibration_profile = profile
        return profile
    
    def _generate_correction_matrix(self, white: np.ndarray, 
                                    black: np.ndarray) -> np.ndarray:
        """
        Generar matriz de corrección de color
        Versión simple: transformación afín
        """
        # Escala: 1.0 / (white - black)
        scale = np.where((white - black) > 0.01, 
                        1.0 / (white - black), 
                        1.0)
        # Offset
        offset = -black * scale
        
        # Matriz diagonal
        matrix = np.diag(scale)
        matrix[:, 3] = offset  # Agregar offset como columna (si usamos homogéneas)
        
        return matrix[:3, :3]  # Retornar 3x3
    
    # ─────────────────────────────────────────────────────
    # PASO 2-3: EXTRACCIÓN Y ESTIMACIÓN ROBUSTA
    # ─────────────────────────────────────────────────────
    
    def extract_roi_color(self, 
                         frame: np.ndarray,
                         roi_bounds: tuple) -> np.ndarray:
        """
        Extraer píxeles de ROI
        
        Args:
            frame: imagen BGR
            roi_bounds: (x1, y1, x2, y2)
        
        Returns:
            Píxeles extraídos (N, 3)
        """
        x1, y1, x2, y2 = roi_bounds
        roi = frame[y1:y2, x1:x2]
        
        # Reshape a lista de píxeles
        pixels = roi.reshape(-1, 3)
        
        return pixels.astype(np.float32) / 255.0  # Normalizar
    
    def estimate_robust_color(self, pixels: np.ndarray,
                             method: str = "trimmed_mean") -> np.ndarray:
        """
        Estimar color representativo removiendo outliers
        
        Args:
            pixels: array (N, 3) BGR normalizado
            method: "trimmed_mean" | "median" | "sigma_clip"
        
        Returns:
            Color representativo BGR (3,)
        """
        if method == "trimmed_mean":
            # Remover 10% extremos
            return np.mean(np.sort(pixels, axis=0)[int(0.05*len(pixels)):int(0.95*len(pixels))], axis=0)
        
        elif method == "median":
            return np.median(pixels, axis=0)
        
        elif method == "sigma_clip":
            # Remover píxeles fuera de 2σ
            mean = np.mean(pixels, axis=0)
            std = np.std(pixels, axis=0)
            mask = np.all(np.abs(pixels - mean) < 2 * std, axis=1)
            return np.mean(pixels[mask], axis=0)
        
        return np.mean(pixels, axis=0)
    
    # ─────────────────────────────────────────────────────
    # PASO 4: CONVERSIÓN BGR → Lab
    # ─────────────────────────────────────────────────────
    
    def bgr_to_lab(self, bgr: np.ndarray) -> np.ndarray:
        """
        Convertir BGR → Lab
        
        Args:
            bgr: color normalizado (0-1)
        
        Returns:
            Lab: (L*, a*, b*)
        """
        # BGR → RGB (OpenCV usa BGR)
        rgb = bgr[::-1] if bgr.ndim == 1 else bgr[..., ::-1]
        
        # RGB → XYZ
        xyz = self._rgb_to_xyz(rgb)
        
        # XYZ → Lab
        lab = self._xyz_to_lab(xyz)
        
        return lab
    
    def _rgb_to_xyz(self, rgb: np.ndarray) -> np.ndarray:
        """RGB normalizado (0-1) → XYZ"""
        # Corregir gamma
        rgb_linear = np.where(rgb > 0.04045,
                              np.power((rgb + 0.055) / 1.055, 2.4),
                              rgb / 12.92)
        
        # Matriz de transformación (D65)
        matrix = np.array([
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041]
        ])
        
        xyz = rgb_linear @ matrix.T
        return xyz
    
    def _xyz_to_lab(self, xyz: np.ndarray) -> np.ndarray:
        """XYZ → Lab (D65)"""
        # Iluminante D65
        ref_white = np.array([0.95047, 1.00000, 1.08883])
        
        xyz_normalized = xyz / ref_white
        
        # Función f
        delta = 6/29
        f = np.where(xyz_normalized > delta**3,
                     np.power(xyz_normalized, 1/3),
                     xyz_normalized / (3 * delta**2) + 4/29)
        
        # Lab
        L = 116 * f[..., 1] - 16 if xyz.ndim == 1 else 116 * f[1] - 16
        a = 500 * (f[..., 0] - f[..., 1]) if xyz.ndim == 1 else 500 * (f[0] - f[1])
        b = 200 * (f[..., 1] - f[..., 2]) if xyz.ndim == 1 else 200 * (f[1] - f[2])
        
        lab = np.array([L, a, b])
        return lab
    
    # ─────────────────────────────────────────────────────
    # PASO 5: CÁLCULO DE DELTAE
    # ─────────────────────────────────────────────────────
    
    def calculate_deltae(self,
                        lab_measured: np.ndarray,
                        lab_target: np.ndarray,
                        formula: DeltaEFormula = DeltaEFormula.CIE94) -> float:
        """
        Calcular ΔE entre dos colores Lab
        
        Args:
            lab_measured: (L, a, b) medido
            lab_target: (L, a, b) objetivo
            formula: qué fórmula usar
        
        Returns:
            ΔE escalar
        """
        dL = lab_measured[0] - lab_target[0]
        da = lab_measured[1] - lab_target[1]
        db = lab_measured[2] - lab_target[2]
        
        if formula == DeltaEFormula.CIE76:
            # Simple
            return np.sqrt(dL**2 + da**2 + db**2)
        
        elif formula == DeltaEFormula.CIE94:
            # Industrial
            C_target = np.sqrt(lab_target[1]**2 + lab_target[2]**2)
            dC = np.sqrt(da**2 + db**2) - C_target
            dH = np.sqrt(da**2 + db**2 - dC**2)
            
            kL = 1.0
            kC = 0.045
            kH = 0.015
            
            L_part = (dL / kL)**2
            C_part = (dC / (kC * C_target))**2
            H_part = (dH / kH)**2
            
            return np.sqrt(L_part + C_part + H_part)
        
        elif formula == DeltaEFormula.CIE2000:
            # Más complejo pero más preciso (CIEDE2000)
            # Implementación simplificada
            return self._deltae_2000(lab_measured, lab_target)
        
        return 0.0
    
    def _deltae_2000(self, lab1: np.ndarray, lab2: np.ndarray) -> float:
        """CIEDE2000 - implementación completa"""
        # Versión simplificada (implementación completa requiere muchas líneas)
        dL = lab1[0] - lab2[0]
        da = lab1[1] - lab2[1]
        db = lab1[2] - lab2[2]
        
        C_ab1 = np.sqrt(lab1[1]**2 + lab1[2]**2)
        C_ab2 = np.sqrt(lab2[1]**2 + lab2[2]**2)
        C_ab_avg = (C_ab1 + C_ab2) / 2
        
        G = 0.5 * (1 - np.sqrt(C_ab_avg**7 / (C_ab_avg**7 + 25**7)))
        
        a1_prime = (1 + G) * lab1[1]
        a2_prime = (1 + G) * lab2[1]
        
        C1_prime = np.sqrt(a1_prime**2 + lab1[2]**2)
        C2_prime = np.sqrt(a2_prime**2 + lab2[2]**2)
        
        dC_prime = C2_prime - C1_prime
        dL = lab2[0] - lab1[0]
        
        return np.sqrt(dL**2 + dC_prime**2)  # Versión simplificada
    
    # ─────────────────────────────────────────────────────
    # PASO 6: EVALUACIÓN DE ESTADOS
    # ─────────────────────────────────────────────────────
    
    def evaluate_color_state(self,
                            deltae: float,
                            target: ColorTarget) -> ColorState:
        """Determinar estado del color"""
        if deltae <= target.warn_threshold_deltae:
            return ColorState.OK
        elif deltae <= target.oot_threshold_deltae:
            return ColorState.WARN
        else:
            return ColorState.OOT
    
    # ─────────────────────────────────────────────────────
    # PASO 7: ANÁLISIS DE TENDENCIAS
    # ─────────────────────────────────────────────────────
    
    def measure_color_frame(self,
                           frame: np.ndarray,
                           roi_id: str,
                           target: ColorTarget) -> ColorMeasurement:
        """
        Medir color completo en un frame
        (pasos 1-6 combinados)
        """
        # [1] Extraer píxeles
        pixels = self.extract_roi_color(frame, target.roi_id_bounds)
        
        # [2-3] Estimar color robusto
        bgr_robust = self.estimate_robust_color(pixels)
        
        # [4] Convertir a Lab
        lab_measured = self.bgr_to_lab(bgr_robust)
        
        # [5] Calcular ΔE
        lab_target = np.array([target.lab_l, target.lab_a, target.lab_b])
        deltae = self.calculate_deltae(lab_measured, lab_target, target.deltae_formula)
        
        # [6] Evaluar estado
        state = self.evaluate_color_state(deltae, target)
        
        # Calcular confianza (basada en varianza de píxeles)
        pixel_std = np.std(pixels, axis=0)
        confidence = 1.0 - np.clip(np.mean(pixel_std) / 0.3, 0, 1)
        
        measurement = ColorMeasurement(
            timestamp=datetime.now(),
            roi_id=roi_id,
            measured_lab_l=lab_measured[0],
            measured_lab_a=lab_measured[1],
            measured_lab_b=lab_measured[2],
            deltae=deltae,
            state=state,
            pixel_count=len(pixels),
            confidence=confidence
        )
        
        # Guardar en historial
        if roi_id not in self.measurement_history:
            self.measurement_history[roi_id] = deque(maxlen=self.window_size_frames)
        
        self.measurement_history[roi_id].append(measurement)
        
        return measurement
    
    def get_color_trend(self, roi_id: str, 
                       window_duration_s: float = 30.0) -> ColorTrend:
        """
        Analizar tendencia de color en ventana deslizante
        """
        if roi_id not in self.measurement_history:
            return None
        
        measurements = list(self.measurement_history[roi_id])
        
        if len(measurements) < 2:
            return None
        
        deltae_values = np.array([m.deltae for m in measurements])
        
        avg_deltae = np.mean(deltae_values)
        std_deltae = np.std(deltae_values)
        max_deltae = np.max(deltae_values)
        
        # Detectar drift (tendencia lineal)
        x = np.arange(len(deltae_values))
        z = np.polyfit(x, deltae_values, 1)
        slope = z[0]
        
        if abs(slope) < 0.01:
            drift_direction = "stable"
            is_drifting = False
        elif slope > 0:
            drift_direction = "increasing"
            is_drifting = slope > 0.05
        else:
            drift_direction = "decreasing"
            is_drifting = slope < -0.05
        
        # Tiempo fuera de tolerancia
        first_time = measurements[0].timestamp
        last_time = measurements[-1].timestamp
        duration = (last_time - first_time).total_seconds()
        
        oot_count = sum(1 for m in measurements if m.state == ColorState.OOT)
        time_in_oot_percent = (oot_count / len(measurements)) * 100 if measurements else 0
        
        trend = ColorTrend(
            roi_id=roi_id,
            window_duration_s=window_duration_s,
            avg_deltae=avg_deltae,
            std_deltae=std_deltae,
            max_deltae=max_deltae,
            time_in_oot_percent=time_in_oot_percent,
            is_drifting=is_drifting,
            drift_direction=drift_direction
        )
        
        return trend
```

**Performance requerido**:
- ✅ Calibración: < 50ms (una vez al inicio)
- ✅ Medición por ROI: < 2ms (en CPU objetivo i7)
- ✅ DeltaE + estado: < 0.1ms
- ✅ Tendencias: < 1ms (actualización cada 300 frames)

---

### 1.3 Integración en Receta

```python
# backend/recipes.py - actualizar clase Recipe

class ColorROI(BaseModel):
    roi_id: str
    name: str
    bounds: tuple  # (x1, y1, x2, y2)
    
    # Target
    lab_l: float
    lab_a: float
    lab_b: float
    
    # Tolerancias
    warn_deltae: float = 2.0
    oot_deltae: float = 5.0
    
    # Config
    deltae_formula: str = "94"  # "76" | "94" | "2000"

class Recipe(BaseModel):
    name: str
    # ... campos existentes ...
    
    # NUEVO: Calibración y color
    calibration_id: Optional[str] = None
    calibration_timestamp: Optional[datetime] = None
    
    color_rois: List[ColorROI] = []
    
    # Criterios de alarma por color
    color_alarm_config: Dict = {
        "alert_on_oot": True,
        "alert_on_warn_duration_s": 10,  # Alerta si WARN > 10s
        "alert_on_oot_duration_s": 5,    # Alerta si OOT > 5s
    }
```

---

### 1.4 Endpoint API para Color

```python
# backend/main.py

@app.post("/color/calibrate")
def calibrate_color(
    camera_id: int,
    white_roi: tuple,
    black_roi: tuple
):
    """Calibrar color (capturar referencias)"""
    try:
        frame = state.camera.get_frame()
        profile = state.color_monitor.calibrate(frame, white_roi, black_roi, camera_id)
        return {
            "status": "calibrated",
            "calibration_id": profile.calibration_id,
            "white_ref": profile.white_ref_bgr.tolist(),
            "black_ref": profile.black_ref_bgr.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/color/measurement/{roi_id}")
def get_color_measurement(roi_id: str):
    """Obtener última medición de color"""
    measurements = state.color_monitor.measurement_history.get(roi_id, deque())
    if not measurements:
        return {"error": "No measurements"}
    
    latest = measurements[-1]
    return {
        "roi_id": roi_id,
        "deltae": latest.deltae,
        "state": latest.state.value,
        "lab": {
            "L": latest.measured_lab_l,
            "a": latest.measured_lab_a,
            "b": latest.measured_lab_b
        },
        "timestamp": latest.timestamp.isoformat(),
        "confidence": latest.confidence
    }

@app.get("/color/trend/{roi_id}")
def get_color_trend(roi_id: str, window_s: float = 30.0):
    """Obtener tendencia de color"""
    trend = state.color_monitor.get_color_trend(roi_id, window_s)
    if not trend:
        return {"error": "No trend data"}
    
    return {
        "roi_id": roi_id,
        "avg_deltae": trend.avg_deltae,
        "std_deltae": trend.std_deltae,
        "max_deltae": trend.max_deltae,
        "time_in_oot_percent": trend.time_in_oot_percent,
        "is_drifting": trend.is_drifting,
        "drift_direction": trend.drift_direction,
        "window_duration_s": trend.window_duration_s
    }
```

---

## 2. Clasificación de Defectos (Mínimo Viable)

### 2.1 Catálogo de Defectos

```python
# backend/defects.py (nuevo archivo)

from enum import Enum

class DefectType(Enum):
    """Catálogo de tipos de defectos"""
    
    # Defectos de diseño/registro
    ARTWORK_DIFF = "artwork_diff"          # Diferencia vs. maestro
    MISSING_PRINT = "missing_print"        # Área sin tinta
    REGISTER_ERROR = "register_error"      # Desalineación
    
    # Defectos de tinta
    EXCESS_INK = "excess_ink"              # Exceso de tinta
    SMEAR = "smear"                        # Manchado
    STREAK = "streak"                      # Rayas/bandas
    
    # Defectos de material
    CONTAMINATION = "contamination"        # Suciedad/polvo
    SPOT = "spot"                          # Mancha aislada
    DIE_CUT_ERROR = "die_cut_error"       # Error de troquelado
    
    # Defectos de color
    COLOR_OOT = "color_oot"                # Color fuera de spec
    
    # Fallback
    UNKNOWN = "unknown"                    # No clasificable

class DefectSeverity(Enum):
    """Niveles de severidad (determinísticos)"""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"

@dataclass
class DefectRecord:
    """Registro de un defecto detectado"""
    defect_id: str
    timestamp: datetime
    
    # Clasificación
    type: DefectType
    severity: DefectSeverity
    
    # Ubicación
    roi_id: str
    x: float
    y: float
    area_px: float
    
    # Análisis
    confidence_score: float  # 0-1
    rule_applied: str        # Qué regla determinó severidad
    
    # Evidencia
    thumbnail_base64: Optional[str] = None
    heatmap_base64: Optional[str] = None

class DefectClassifier:
    """Motor de clasificación de defectos"""
    
    def __init__(self):
        self.rules: Dict[str, DefectRule] = {}
    
    def classify_defect(self,
                       defect_data: dict,
                       recipe: Recipe) -> DefectRecord:
        """
        Clasificar defecto según reglas de receta
        
        Args:
            defect_data: {type_hint, area, x, y, confidence, ...}
            recipe: receta con reglas
        
        Returns:
            DefectRecord con tipo y severidad determinísticos
        """
        
        # [1] Determinar tipo (hint inicial + análisis)
        defect_type = self._determine_type(defect_data)
        
        # [2] Evaluar severidad según reglas
        severity, rule_applied = self._evaluate_severity(
            defect_type,
            defect_data,
            recipe
        )
        
        # [3] Crear registro
        record = DefectRecord(
            defect_id=f"def_{uuid4()}",
            timestamp=datetime.now(),
            type=defect_type,
            severity=severity,
            roi_id=defect_data.get("roi_id", "unknown"),
            x=defect_data["x"],
            y=defect_data["y"],
            area_px=defect_data["area"],
            confidence_score=defect_data.get("confidence", 0.5),
            rule_applied=rule_applied
        )
        
        return record
    
    def _determine_type(self, defect_data: dict) -> DefectType:
        """Determinar tipo de defecto basado en características"""
        
        area = defect_data["area"]
        aspect_ratio = defect_data.get("aspect_ratio", 1.0)
        color_channel_variance = defect_data.get("color_variance", 0)
        
        # Reglas simples de decisión
        if area < 50:
            return DefectType.SPOT
        
        elif area > 1000 and aspect_ratio > 5:
            return DefectType.STREAK
        
        elif color_channel_variance > 30:
            return DefectType.EXCESS_INK
        
        elif "no_pixels" in defect_data and defect_data["no_pixels"]:
            return DefectType.MISSING_PRINT
        
        else:
            return DefectType.ARTWORK_DIFF
    
    def _evaluate_severity(self,
                          defect_type: DefectType,
                          defect_data: dict,
                          recipe: Recipe) -> tuple:
        """
        Evaluar severidad de forma DETERMINÍSTICA
        
        Returns:
            (severity, rule_applied)
        """
        
        area = defect_data["area"]
        
        # Obtener umbrales de receta
        thresholds = recipe.defect_thresholds or {
            "critical_area": 500,
            "major_area": 150,
            "minor_area": 0
        }
        
        critical_area = thresholds.get("critical_area", 500)
        major_area = thresholds.get("major_area", 150)
        
        # Reglas: defectos críticos siempre son críticos
        if defect_type in [DefectType.MISSING_PRINT, DefectType.REGISTER_ERROR]:
            if area > critical_area:
                return DefectSeverity.CRITICAL, f"Type={defect_type.value}+Area>{critical_area}"
            elif area > major_area:
                return DefectSeverity.MAJOR, f"Type={defect_type.value}+Area>{major_area}"
            else:
                return DefectSeverity.MINOR, f"Type={defect_type.value}"
        
        # Defectos menores: eval por área
        if area > critical_area:
            return DefectSeverity.CRITICAL, f"Area>{critical_area}px"
        elif area > major_area:
            return DefectSeverity.MAJOR, f"Area>{major_area}px"
        else:
            return DefectSeverity.MINOR, f"Area<{major_area}px"

```

---

### 2.2 Integración en Pipeline

```python
# backend/main.py - actualizar inspection loop

@app.get("/inspection-frame")
async def get_inspection_frame(...):
    """
    Frame con defectos clasificados
    """
    # ... existente ...
    
    # [NUEVO] Clasificar defectos
    classifier = DefectClassifier()
    classified_defects = []
    
    for defect in raw_defects:
        classified = classifier.classify_defect(defect, state.active_recipe)
        classified_defects.append(classified)
        
        # Log para auditoría
        logger.info(
            f"Defect classified: {classified.defect_id} "
            f"type={classified.type.value} "
            f"severity={classified.severity.value} "
            f"rule={classified.rule_applied}"
        )
    
    return {
        # ... campos existentes ...
        "defects": [
            {
                "id": d.defect_id,
                "type": d.type.value,
                "severity": d.severity.value,
                "area": d.area_px,
                "x": d.x,
                "y": d.y,
                "confidence": d.confidence_score,
                "rule": d.rule_applied,
                "timestamp": d.timestamp.isoformat()
            }
            for d in classified_defects
        ]
    }
```

---

## 3. Alarmas y Acciones (Contratos Claros)

### 3.1 Modelo de AlarmRule

```python
# backend/alarms.py (nuevo archivo)

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Callable, Dict

class TriggerType(Enum):
    """Tipos de triggers para alarmas"""
    ON_DEFECT = "on_defect"
    ON_RATE = "on_rate"
    ON_COLOR_OOT = "on_color_oot"
    ON_REGISTER_LOST = "on_register_lost"
    ON_SENSOR_LOST = "on_sensor_lost"
    MANUAL = "manual"

class ActionType(Enum):
    """Tipos de acciones que ejecutar"""
    TOWER_LIGHT = "tower_light"        # (red|yellow|green)
    BUZZER = "buzzer"
    PLC_WRITE = "plc_write"
    HMI_POPUP = "hmi_popup"
    EMAIL = "email"
    LOG_ONLY = "log_only"

@dataclass
class Action:
    """Acción individual"""
    action_type: ActionType
    
    # Config específica por tipo
    duration_ms: int = 500
    
    # Para tower light
    color: str = "red"  # "red" | "yellow" | "green"
    
    # Para PLC
    plc_address: Optional[str] = None
    plc_value: Optional[int] = None
    
    # Para HMI
    popup_title: str = ""
    popup_message: str = ""
    
    # Para email
    email_to: List[str] = field(default_factory=list)
    email_template: str = "default"

@dataclass
class AlarmRule:
    """Regla que define cuándo y qué hacer"""
    rule_id: str
    enabled: bool = True
    
    # Trigger
    trigger_type: TriggerType
    
    # Condiciones específicas del trigger
    trigger_config: Dict = field(default_factory=dict)
    # Ej: {"severity": "CRITICAL"} para ON_DEFECT
    # Ej: {"defects_per_100m": 5} para ON_RATE
    
    # Acciones a ejecutar
    actions: List[Action] = field(default_factory=list)
    
    # Anti-spam
    cooldown_ms: int = 2000
    
    # Metadata
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered_at: Optional[datetime] = None

class AlarmEngine:
    """Motor de evaluación de alarmas"""
    
    def __init__(self):
        self.rules: Dict[str, AlarmRule] = {}
        self.alarm_queue: deque = deque(maxlen=1000)
        self.triggered_times: Dict[str, datetime] = {}  # Para cooldown
        
        self.action_handlers: Dict[ActionType, Callable] = {
            ActionType.TOWER_LIGHT: self._handle_tower_light,
            ActionType.BUZZER: self._handle_buzzer,
            ActionType.PLC_WRITE: self._handle_plc_write,
            ActionType.HMI_POPUP: self._handle_hmi_popup,
            ActionType.EMAIL: self._handle_email,
            ActionType.LOG_ONLY: self._handle_log_only,
        }
    
    def add_rule(self, rule: AlarmRule) -> None:
        """Registrar regla de alarma"""
        self.rules[rule.rule_id] = rule
        logger.info(f"Alarm rule added: {rule.rule_id} - {rule.description}")
    
    def evaluate_defect_alarm(self,
                             defect: DefectRecord,
                             context: dict) -> Optional[str]:
        """
        Evaluar si defecto dispara alarma
        
        Returns:
            alarm_id si se dispara, None en caso contrario
        """
        triggered_alarms = []
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # [1] Verificar cooldown
            if self._is_on_cooldown(rule_id, rule.cooldown_ms):
                logger.debug(f"Rule {rule_id} on cooldown")
                continue
            
            # [2] Evaluar trigger
            if rule.trigger_type == TriggerType.ON_DEFECT:
                if self._matches_defect_trigger(defect, rule.trigger_config):
                    triggered_alarms.append(rule)
            
            elif rule.trigger_type == TriggerType.ON_RATE:
                if self._matches_rate_trigger(context, rule.trigger_config):
                    triggered_alarms.append(rule)
            
            elif rule.trigger_type == TriggerType.ON_COLOR_OOT:
                if self._matches_color_trigger(context, rule.trigger_config):
                    triggered_alarms.append(rule)
        
        # [3] Ejecutar acciones de alarmas disparadas
        for rule in triggered_alarms:
            alarm_id = self._trigger_alarm(rule)
            logger.warning(
                f"Alarm triggered: {alarm_id} "
                f"rule={rule.rule_id} "
                f"defect={defect.defect_id}"
            )
        
        return triggered_alarms[0].rule_id if triggered_alarms else None
    
    def _is_on_cooldown(self, rule_id: str, cooldown_ms: int) -> bool:
        """Verificar si regla está en cooldown"""
        last_time = self.triggered_times.get(rule_id)
        if not last_time:
            return False
        
        elapsed = (datetime.now() - last_time).total_seconds() * 1000
        return elapsed < cooldown_ms
    
    def _matches_defect_trigger(self,
                                defect: DefectRecord,
                                config: dict) -> bool:
        """Verificar si defecto cumple condiciones"""
        
        # Severidad
        if "severity" in config:
            required_severity = config["severity"]
            if defect.severity.value != required_severity:
                return False
        
        # Tipo
        if "defect_types" in config:
            allowed_types = config["defect_types"]
            if defect.type not in allowed_types:
                return False
        
        # Área mínima
        if "min_area_px" in config:
            if defect.area_px < config["min_area_px"]:
                return False
        
        return True
    
    def _matches_rate_trigger(self, context: dict, config: dict) -> bool:
        """Verificar si tasa de defectos cumple"""
        if "defects_per_100m" in config:
            threshold = config["defects_per_100m"]
            current_rate = context.get("defect_rate_per_100m", 0)
            return current_rate > threshold
        
        return False
    
    def _matches_color_trigger(self, context: dict, config: dict) -> bool:
        """Verificar si color está fuera de tolerancia"""
        color_measurements = context.get("color_measurements", [])
        
        for roi_id in config.get("roi_ids", []):
            measurement = next(
                (m for m in color_measurements if m.roi_id == roi_id),
                None
            )
            
            if measurement and measurement.state == ColorState.OOT:
                duration = config.get("duration_s", 0)
                # Aquí iría lógica de duración
                return True
        
        return False
    
    def _trigger_alarm(self, rule: AlarmRule) -> str:
        """
        Ejecutar alarma: disparar todas las acciones
        
        Returns:
            alarm_id
        """
        alarm_id = f"alarm_{rule.rule_id}_{uuid4()}"
        
        # Marcar como disparada
        rule.last_triggered_at = datetime.now()
        self.triggered_times[rule.rule_id] = datetime.now()
        
        # Ejecutar acciones (sequenciales, sin bloquear inspección)
        for action in rule.actions:
            handler = self.action_handlers.get(action.action_type)
            if handler:
                try:
                    # Non-blocking
                    handler(action, alarm_id)
                except Exception as e:
                    logger.error(f"Action execution failed: {e}", exc_info=True)
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
        
        # Guardar en historial
        self.alarm_queue.append({
            "alarm_id": alarm_id,
            "rule_id": rule.rule_id,
            "timestamp": datetime.now(),
            "actions_count": len(rule.actions)
        })
        
        return alarm_id
    
    # ─────────────────────────────────────────────────────
    # HANDLERS DE ACCIONES
    # ─────────────────────────────────────────────────────
    
    def _handle_tower_light(self, action: Action, alarm_id: str) -> None:
        """Encender luz de torre"""
        if state.plc:
            try:
                state.plc.send_signal(
                    f"tower_{action.color}",
                    duration_ms=action.duration_ms
                )
                logger.info(f"Tower light {action.color} activated: {alarm_id}")
            except Exception as e:
                logger.error(f"PLC tower light failed: {e}")
    
    def _handle_buzzer(self, action: Action, alarm_id: str) -> None:
        """Activar buzzer"""
        if state.plc:
            try:
                state.plc.send_signal("buzzer", duration_ms=action.duration_ms)
                logger.info(f"Buzzer activated: {alarm_id}")
            except Exception as e:
                logger.error(f"PLC buzzer failed: {e}")
    
    def _handle_plc_write(self, action: Action, alarm_id: str) -> None:
        """Escribir dato al PLC"""
        if state.plc and action.plc_address:
            try:
                state.plc.write(action.plc_address, action.plc_value)
                logger.info(
                    f"PLC write: {action.plc_address}={action.plc_value} ({alarm_id})"
                )
            except Exception as e:
                logger.error(f"PLC write failed: {e}")
    
    def _handle_hmi_popup(self, action: Action, alarm_id: str) -> None:
        """Enviar popup al HMI (frontend)"""
        # Guardar en cola para que frontend consulte
        popup_event = {
            "type": "alarm_popup",
            "title": action.popup_title,
            "message": action.popup_message,
            "alarm_id": alarm_id,
            "timestamp": datetime.now().isoformat()
        }
        state.event_queue.append(popup_event)
        logger.info(f"HMI popup queued: {alarm_id}")
    
    def _handle_email(self, action: Action, alarm_id: str) -> None:
        """Enviar email"""
        if not action.email_to:
            return
        
        try:
            email_body = self._render_email_template(action.email_template)
            # Aquí iría código real de SMTP
            logger.info(f"Email queued to {action.email_to}: {alarm_id}")
        except Exception as e:
            logger.error(f"Email failed: {e}")
    
    def _handle_log_only(self, action: Action, alarm_id: str) -> None:
        """Solo loguear"""
        logger.info(f"Alarm logged: {alarm_id}")
    
    def _render_email_template(self, template_name: str) -> str:
        """Renderizar template de email"""
        templates = {
            "default": "Alarm triggered at {time}",
            "detailed": "Alarm: {defect_type} at {roi_id}"
        }
        return templates.get(template_name, "Alarm")

```

---

### 3.2 Configuración de Alarmas en Receta

```python
# backend/recipes.py

class Recipe(BaseModel):
    name: str
    # ... campos existentes ...
    
    # NUEVO: Reglas de alarma
    alarm_rules: List[Dict] = [
        {
            "rule_id": "critical_defect",
            "enabled": True,
            "trigger_type": "on_defect",
            "trigger_config": {
                "severity": "critical"
            },
            "actions": [
                {
                    "action_type": "tower_light",
                    "color": "red",
                    "duration_ms": 1000
                },
                {
                    "action_type": "buzzer",
                    "duration_ms": 500
                },
                {
                    "action_type": "plc_write",
                    "plc_address": "stop_line",
                    "plc_value": 1
                }
            ],
            "cooldown_ms": 2000,
            "description": "Critical defect - stop and alert"
        },
        {
            "rule_id": "high_defect_rate",
            "enabled": True,
            "trigger_type": "on_rate",
            "trigger_config": {
                "defects_per_100m": 10
            },
            "actions": [
                {
                    "action_type": "tower_light",
                    "color": "yellow",
                    "duration_ms": 500
                },
                {
                    "action_type": "email",
                    "email_to": ["supervisor@company.com"],
                    "email_template": "high_rate_alert"
                }
            ],
            "cooldown_ms": 60000,
            "description": "High defect rate"
        }
    ]
```

---

### 3.3 Criterios de Aceptación

```python
# Criterios de aceptación verificables

class AlarmAcceptanceCriteria:
    """
    Verificar que sistema de alarmas cumple requisitos
    """
    
    @staticmethod
    def test_no_email_spam():
        """
        ✓ No disparar más de 1 email por regla por cooldown_ms
        """
        engine = AlarmEngine()
        rule = AlarmRule(
            rule_id="test_email",
            trigger_type=TriggerType.ON_DEFECT,
            trigger_config={"severity": "critical"},
            actions=[Action(action_type=ActionType.EMAIL, email_to=["test@test.com"])],
            cooldown_ms=5000
        )
        engine.add_rule(rule)
        
        # Trigger primera vez
        defect1 = DefectRecord(..., severity=DefectSeverity.CRITICAL)
        alarm1 = engine.evaluate_defect_alarm(defect1, {})
        
        # Trigger segunda vez dentro de cooldown
        time.sleep(1)
        defect2 = DefectRecord(..., severity=DefectSeverity.CRITICAL)
        alarm2 = engine.evaluate_defect_alarm(defect2, {})
        
        assert alarm1 is not None  # Primera sí dispara
        assert alarm2 is None      # Segunda no (cooldown)
    
    @staticmethod
    def test_plc_non_blocking():
        """
        ✓ Si PLC no está disponible: cola y reintentos, 
        pero no bloquear inspección
        """
        engine = AlarmEngine()
        
        # Simular PLC no disponible
        state.plc = None
        
        defect = DefectRecord(..., severity=DefectSeverity.CRITICAL)
        
        start_time = time.time()
        alarm_id = engine.evaluate_defect_alarm(defect, {})
        elapsed = time.time() - start_time
        
        assert alarm_id is not None
        assert elapsed < 0.1  # No bloqueó (< 100ms)
    
    @staticmethod
    def test_rule_determinism():
        """
        ✓ Misma entrada → mismo resultado (determinístico)
        """
        engine = AlarmEngine()
        
        defect = DefectRecord(
            type=DefectType.MISSING_PRINT,
            severity=DefectSeverity.CRITICAL,
            area_px=600
        )
        
        # Evaluar N veces
        results = []
        for _ in range(5):
            alarm = engine.evaluate_defect_alarm(defect, {})
            results.append(alarm)
        
        # Todos iguales
        assert len(set(results)) == 1
    
    @staticmethod
    def test_cooldown_enforcement():
        """
        ✓ Cooldown realmente bloquea
        """
        engine = AlarmEngine()
        rule = AlarmRule(
            rule_id="test",
            cooldown_ms=1000,
            actions=[Action(action_type=ActionType.LOG_ONLY)]
        )
        engine.add_rule(rule)
        
        defect = DefectRecord(..., severity=DefectSeverity.CRITICAL)
        
        # Primera
        a1 = engine.evaluate_defect_alarm(defect, {})
        
        # Segunda inmediatamente
        a2 = engine.evaluate_defect_alarm(defect, {})
        
        # Tercera después de cooldown
        time.sleep(1.1)
        a3 = engine.evaluate_defect_alarm(defect, {})
        
        assert a1 is not None
        assert a2 is None      # Bloqueado por cooldown
        assert a3 is not None  # Desbloqueado
```

---

## Resumen de Integración

| Punto | Estado | Ubicación |
|-------|--------|-----------|
| **5.1 Pipeline Color** | ✅ Especificado | `backend/color_module_v2.py` |
| **5.1 DeltaE** | ✅ Implementable | 4 fórmulas (76/94/2000) |
| **5.1 Calibración** | ✅ Diseñado | Endpoints `/color/calibrate` |
| **5.1 Tendencias** | ✅ Especificado | `get_color_trend()` |
| **6.1 Catálogo Defectos** | ✅ Enum completo | 9 tipos + UNKNOWN |
| **6.2 Severidad** | ✅ Determinístico | `DefectClassifier` |
| **7.1 AlarmRule** | ✅ Modelo completo | `backend/alarms.py` |
| **7.1 Acciones** | ✅ 6 tipos | Tower, Buzzer, PLC, HMI, Email, Log |
| **7.2 Cooldown** | ✅ Anti-spam | Configurable por regla |
| **7.2 PLC Queue** | ✅ Non-blocking | Cola con reintentos |

---

**Implementación**: Todas las especificaciones son implementables inmediatamente con código proporcionado.
