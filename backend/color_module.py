"""
Point 5: Color/DeltaE Pipeline Implementation
- Calibración con referencias blanco/negro
- Medición robusta por ROI
- Conversión BGR → Lab
- Cálculo de DeltaE (CIE76/94/2000)
- Análisis de tendencias
"""

import numpy as np
from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict
from datetime import datetime
from skimage import color
from collections import deque
from enum import Enum
from dataclasses import dataclass, field
import cv2
import logging

logger = logging.getLogger(__name__)


class DeltaEFormula(Enum):
    """Fórmulas de DeltaE soportadas"""
    CIE76 = "76"      # Simple
    CIE94 = "94"      # Industrial (default)
    CIE2000 = "2000"  # Más preciso


class ColorState(Enum):
    """Estados del color en medición"""
    OK = "ok"
    WARN = "warn"
    OOT = "out_of_tolerance"


class ColorTarget(BaseModel):
    """Target de color para un ROI - Compatible con versiones anteriores"""
    name: str                                          # e.g. "Coca-Cola Red"
    l_target: float
    a_target: float
    b_target: float
    
    # Tolerancias (soporta ambos nombres para compatibilidad)
    tolerance_warning: Optional[float] = None          # Nombre anterior
    tolerance_critical: Optional[float] = None         # Nombre anterior
    warn_threshold_deltae: float = 2.0                 # Nuevo nombre
    oot_threshold_deltae: float = 5.0                  # Nuevo nombre
    
    # Point 5 enhancements (opcional)
    roi_id: Optional[str] = None                       # ROI identifier
    bounds: Optional[Tuple[int, int, int, int]] = None # (x1, y1, x2, y2)
    deltae_formula: str = "94"                         # "76" | "94" | "2000"
    
    def __init__(self, **data):
        # Compatibilidad: si viene con tolerance_warning/critical, mapear a nuevos nombres
        if 'tolerance_warning' in data and 'warn_threshold_deltae' not in data:
            data['warn_threshold_deltae'] = data.get('tolerance_warning', 2.0)
        if 'tolerance_critical' in data and 'oot_threshold_deltae' not in data:
            data['oot_threshold_deltae'] = data.get('tolerance_critical', 5.0)
        super().__init__(**data)


class ColorMeasurement(BaseModel):
    """Medición de color en un instante"""
    timestamp: datetime
    roi_id: str
    
    # Color medido en Lab
    l_value: float
    a_value: float
    b_value: float
    
    # Análisis
    delta_e: float
    state: str  # "ok" | "warn" | "out_of_tolerance"
    
    # Metadata
    pixel_count: int = 0
    confidence: float = 0.5  # 0-1 basado en varianza
    
    # Deprecated (compatibilidad)
    is_warning: bool = False
    is_critical: bool = False


@dataclass  # Falta importar
class CalibrationProfile:
    """Perfil de calibración por cámara"""
    calibration_id: str
    timestamp: datetime
    camera_id: int
    
    # Referencias
    white_ref_bgr: np.ndarray  # (B, G, R) normalizado
    black_ref_bgr: np.ndarray
    
    # Matriz de corrección
    correction_matrix: np.ndarray  # 3x3
    
    # Metadata
    illuminant: str = "D65"


class ColorTrend(BaseModel):
    """Análisis de tendencia en ventana deslizante"""
    roi_id: str
    window_duration_s: float
    
    # Estadísticas
    avg_deltae: float
    std_deltae: float
    max_deltae: float
    
    # Duración fuera de tolerancia
    time_in_oot_percent: float
    
    # Análisis de drift
    is_drifting: bool
    drift_direction: str  # "stable" | "increasing" | "decreasing"


class ColorMonitor:
    """Motor de monitoreo de color (Point 5 implementation)"""
    
    def __init__(self):
        self.targets: Dict[str, ColorTarget] = {}
        self.active_target_name: Optional[str] = None
        self.measurements: List[ColorMeasurement] = []
        self.measurement_history: Dict[str, deque] = {}  # Por ROI
        self.window_size_frames = 300  # ~30s @ 10fps
        
        # Calibración
        self.calibration_profile: Optional[CalibrationProfile] = None
        self.calibration_white: Optional[np.ndarray] = None  # Reference white
    
    # ─────────────────────────────────────────────────────
    # PASO 1: CALIBRACIÓN
    # ─────────────────────────────────────────────────────
    
    def calibrate(self,
                 frame: np.ndarray,
                 white_roi: tuple,
                 black_roi: tuple,
                 camera_id: int):
        """
        Calibración: extraer referencias blanco/negro
        
        Args:
            frame: imagen BGR
            white_roi: (x1, y1, x2, y2)
            black_roi: (x1, y1, x2, y2)
            camera_id: ID de cámara
        
        Returns:
            calibration_id
        """
        # Extraer regiones
        x1w, y1w, x2w, y2w = white_roi
        x1b, y1b, x2b, y2b = black_roi
        
        white_region = frame[y1w:y2w, x1w:x2w]
        black_region = frame[y1b:y2b, x1b:x2b]
        
        # Validar que regiones no estén vacías
        if white_region.size == 0 or black_region.size == 0:
            raise ValueError("ROI regions are empty")
        
        # Calcular promedio
        white_bgr = np.mean(white_region, axis=(0, 1)).astype(np.uint8)
        black_bgr = np.mean(black_region, axis=(0, 1)).astype(np.uint8)
        
        # Normalizar a [0, 1]
        white_bgr_norm = white_bgr.astype(np.float32) / 255.0
        black_bgr_norm = black_bgr.astype(np.float32) / 255.0
        
        # Generar matriz de corrección
        correction_matrix = self._generate_correction_matrix(white_bgr_norm, black_bgr_norm)
        
        from dataclasses import dataclass
        
        @dataclass
        class CalibrationProfile_:
            calibration_id: str
            timestamp: datetime
            camera_id: int
            white_ref_bgr: np.ndarray
            black_ref_bgr: np.ndarray
            correction_matrix: np.ndarray
            illuminant: str = "D65"
        
        profile = CalibrationProfile_(
            calibration_id=f"calib_{camera_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            camera_id=camera_id,
            white_ref_bgr=white_bgr_norm,
            black_ref_bgr=black_bgr_norm,
            correction_matrix=correction_matrix
        )
        
        self.calibration_profile = profile
        self.calibration_white = white_bgr_norm
        
        logger.info(f"Calibration completed: {profile.calibration_id}")
        return profile.calibration_id
    
    def _generate_correction_matrix(self,
                                   white: np.ndarray,
                                   black: np.ndarray) -> np.ndarray:
        """Generar matriz de corrección de color"""
        # Escala
        scale = np.where((white - black) > 0.01,
                        1.0 / (white - black),
                        1.0)
        # Matriz diagonal
        matrix = np.diag(scale)
        return matrix
    
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
            píxeles (N, 3) normalizado [0, 1]
        """
        x1, y1, x2, y2 = roi_bounds
        roi = frame[y1:y2, x1:x2]
        
        # Reshape a lista de píxeles
        pixels = roi.reshape(-1, 3)
        
        return pixels.astype(np.float32) / 255.0
    
    def estimate_robust_color(self,
                             pixels: np.ndarray,
                             method: str = "trimmed_mean") -> np.ndarray:
        """
        Estimar color robusto removiendo outliers
        
        Args:
            pixels: array (N, 3) BGR normalizado
            method: "trimmed_mean" | "median" | "sigma_clip"
        
        Returns:
            color representativo BGR (3,)
        """
        if len(pixels) == 0:
            return np.array([0.5, 0.5, 0.5])
        
        if method == "trimmed_mean":
            # Remover 10% extremos
            lower = int(0.05 * len(pixels))
            upper = int(0.95 * len(pixels))
            sorted_pixels = np.sort(pixels, axis=0)
            return np.mean(sorted_pixels[lower:upper], axis=0)
        
        elif method == "median":
            return np.median(pixels, axis=0)
        
        elif method == "sigma_clip":
            mean = np.mean(pixels, axis=0)
            std = np.std(pixels, axis=0)
            mask = np.all(np.abs(pixels - mean) < 2 * std, axis=1)
            if np.any(mask):
                return np.mean(pixels[mask], axis=0)
            else:
                return mean
        
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
        # BGR → RGB
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
        
        # Matriz de transformación D65
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
        L = 116 * f[..., 1] - 16
        a = 500 * (f[..., 0] - f[..., 1])
        b = 200 * (f[..., 1] - f[..., 2])
        
        lab = np.array([L, a, b])
        return lab
    
    # ─────────────────────────────────────────────────────
    # PASO 5: CÁLCULO DE DELTAE
    # ─────────────────────────────────────────────────────
    
    def calculate_delta_e(self,
                         lab_measured: np.ndarray,
                         lab_target: np.ndarray,
                         formula: str = "94") -> float:
        """
        Calcular ΔE entre dos colores Lab
        
        Args:
            lab_measured: (L, a, b) medido
            lab_target: (L, a, b) objetivo
            formula: "76" | "94" | "2000"
        
        Returns:
            ΔE escalar
        """
        dL = lab_measured[0] - lab_target[0]
        da = lab_measured[1] - lab_target[1]
        db = lab_measured[2] - lab_target[2]
        
        if formula == "76":
            return np.sqrt(dL**2 + da**2 + db**2)
        
        elif formula == "94":
            # CIE94 (Industrial)
            C_target = np.sqrt(lab_target[1]**2 + lab_target[2]**2)
            dC = np.sqrt(da**2 + db**2) - C_target
            dH = np.sqrt(da**2 + db**2 - dC**2) if (da**2 + db**2) >= dC**2 else 0
            
            kL = 1.0
            kC = 0.045
            kH = 0.015
            
            L_part = (dL / kL)**2
            C_part = (dC / (kC * C_target + 1e-6))**2
            H_part = (dH / kH)**2
            
            return np.sqrt(L_part + C_part + H_part)
        
        elif formula == "2000":
            # CIEDE2000 (simplificado)
            return self._deltae_2000(lab_measured, lab_target)
        
        return 0.0
    
    def _deltae_2000(self,
                    lab1: np.ndarray,
                    lab2: np.ndarray) -> float:
        """CIEDE2000 simplificado"""
        dL = lab2[0] - lab1[0]
        
        C_ab1 = np.sqrt(lab1[1]**2 + lab1[2]**2)
        C_ab2 = np.sqrt(lab2[1]**2 + lab2[2]**2)
        C_ab_avg = (C_ab1 + C_ab2) / 2
        
        G = 0.5 * (1 - np.sqrt(C_ab_avg**7 / (C_ab_avg**7 + 25**7)))
        
        a1_prime = (1 + G) * lab1[1]
        a2_prime = (1 + G) * lab2[1]
        
        C1_prime = np.sqrt(a1_prime**2 + lab1[2]**2)
        C2_prime = np.sqrt(a2_prime**2 + lab2[2]**2)
        
        dC_prime = C2_prime - C1_prime
        
        return np.sqrt(dL**2 + dC_prime**2)
    
    # ─────────────────────────────────────────────────────
    # PASO 6: EVALUACIÓN DE ESTADOS
    # ─────────────────────────────────────────────────────
    
    def evaluate_color_state(self,
                            deltae: float,
                            target: ColorTarget) -> str:
        """Determinar estado del color"""
        if deltae <= target.warn_threshold_deltae:
            return ColorState.OK.value
        elif deltae <= target.oot_threshold_deltae:
            return ColorState.WARN.value
        else:
            return ColorState.OOT.value
    
    # ─────────────────────────────────────────────────────
    # PASO 7: ANÁLISIS DE TENDENCIAS
    # ─────────────────────────────────────────────────────
    
    def measure_color_frame(self,
                           frame: np.ndarray,
                           target: ColorTarget) -> ColorMeasurement:
        """
        Medir color completo en un frame (pasos 1-6)
        
        Args:
            frame: imagen BGR
            target: ColorTarget definido
        
        Returns:
            ColorMeasurement con todos los campos
        """
        # [1] Extraer píxeles
        pixels = self.extract_roi_color(frame, target.bounds)
        
        if len(pixels) == 0:
            return ColorMeasurement(
                timestamp=datetime.now(),
                roi_id=target.roi_id,
                l_value=0, a_value=0, b_value=0,
                delta_e=0, state=ColorState.OOT.value,
                pixel_count=0, confidence=0
            )
        
        # [2-3] Estimar color robusto
        bgr_robust = self.estimate_robust_color(pixels)
        
        # [4] Convertir a Lab
        lab_measured = self.bgr_to_lab(bgr_robust)
        
        # [5] Calcular ΔE
        lab_target = np.array([target.l_target, target.a_target, target.b_target])
        deltae = self.calculate_delta_e(lab_measured, lab_target, target.deltae_formula)
        
        # [6] Evaluar estado
        state = self.evaluate_color_state(deltae, target)
        
        # Calcular confianza
        pixel_std = np.std(pixels, axis=0)
        confidence = 1.0 - np.clip(np.mean(pixel_std) / 0.3, 0, 1)
        
        measurement = ColorMeasurement(
            timestamp=datetime.now(),
            roi_id=target.roi_id,
            l_value=lab_measured[0],
            a_value=lab_measured[1],
            b_value=lab_measured[2],
            delta_e=deltae,
            state=state,
            pixel_count=len(pixels),
            confidence=confidence,
            is_warning=(state == ColorState.WARN.value),
            is_critical=(state == ColorState.OOT.value)
        )
        
        # Guardar en historial
        if target.roi_id not in self.measurement_history:
            self.measurement_history[target.roi_id] = deque(maxlen=self.window_size_frames)
        
        self.measurement_history[target.roi_id].append(measurement)
        self.measurements.append(measurement)
        
        # Keep only recent history
        if len(self.measurements) > 1000:
            self.measurements.pop(0)
        
        return measurement
    
    def get_color_trend(self,
                       roi_id: str,
                       window_duration_s: float = 30.0) -> Optional[Dict]:
        """
        Analizar tendencia de color en ventana deslizante
        """
        if roi_id not in self.measurement_history:
            return None
        
        measurements = list(self.measurement_history[roi_id])
        
        if len(measurements) < 2:
            return None
        
        deltae_values = np.array([m.delta_e for m in measurements])
        
        avg_deltae = float(np.mean(deltae_values))
        std_deltae = float(np.std(deltae_values))
        max_deltae = float(np.max(deltae_values))
        
        # Detectar drift
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
        oot_count = sum(1 for m in measurements if m.state == ColorState.OOT.value)
        time_in_oot_percent = (oot_count / len(measurements)) * 100 if measurements else 0
        
        return {
            "roi_id": roi_id,
            "avg_deltae": avg_deltae,
            "std_deltae": std_deltae,
            "max_deltae": max_deltae,
            "time_in_oot_percent": time_in_oot_percent,
            "is_drifting": is_drifting,
            "drift_direction": drift_direction,
            "window_duration_s": window_duration_s
        }
    
    # ─────────────────────────────────────────────────────
    # MÉTODOS COMPATIBILIDAD
    # ─────────────────────────────────────────────────────
    
    def add_target(self, target: ColorTarget):
        self.targets[target.name] = target
        if self.active_target_name is None:
            self.active_target_name = target.name
    
    def set_active_target(self, name: str):
        if name in self.targets:
            self.active_target_name = name
        else:
            raise ValueError(f"Target {name} not found")
    
    def get_active_target(self) -> Optional[ColorTarget]:
        if self.active_target_name:
            return self.targets[self.active_target_name]
        return None
    
    def rgb_to_lab(self, rgb_pixel: np.ndarray) -> Tuple[float, float, float]:
        """
        Convert a single RGB pixel to Lab (legacy method).
        """
        if rgb_pixel.shape == (3,):
            rgb_pixel = rgb_pixel.reshape(1, 1, 3)
        
        # Using cv2 for conversion
        lab = cv2.cvtColor((rgb_pixel * 255).astype(np.uint8), cv2.COLOR_RGB2Lab)
        l, a, b = lab[0, 0]
        
        # Scale to standard Lab
        l_std = l * 100.0 / 255.0
        a_std = a - 128.0
        b_std = b - 128.0
        
        return (l_std, a_std, b_std)
    
    def record_measurement(self, l: float, a: float, b: float) -> ColorMeasurement:
        """Legacy method"""
        target = self.get_active_target()
        if not target:
            diff = 0.0
            warn = False
            crit = False
        else:
            lab_target = np.array([target.l_target, target.a_target, target.b_target])
            lab_measured = np.array([l, a, b])
            diff = self.calculate_delta_e(lab_measured, lab_target, target.deltae_formula)
            warn = diff > target.warn_threshold_deltae
            crit = diff > target.oot_threshold_deltae
        
        measurement = ColorMeasurement(
            timestamp=datetime.now(),
            roi_id=(target.roi_id if target and target.roi_id else "default"),
            l_value=l,
            a_value=a,
            b_value=b,
            delta_e=diff,
            state=ColorState.WARN.value if warn else (ColorState.OOT.value if crit else ColorState.OK.value),
            pixel_count=0,
            confidence=0.8,
            is_warning=warn,
            is_critical=crit
        )
        self.measurements.append(measurement)
        
        if len(self.measurements) > 1000:
            self.measurements.pop(0)
        
        return measurement
