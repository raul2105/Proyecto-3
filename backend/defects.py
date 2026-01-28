"""
Point 6: Defect Classification System
- Catálogo de defectos determinístico
- Severidad auditable por reglas
- Logging de decisiones
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class DefectType(Enum):
    """Catálogo completo de tipos de defectos"""
    
    # Defectos de diseño/registro
    ARTWORK_DIFF = "artwork_diff"              # Diferencia vs. maestro
    MISSING_PRINT = "missing_print"            # Área sin tinta
    REGISTER_ERROR = "register_error"          # Desalineación
    
    # Defectos de tinta
    EXCESS_INK = "excess_ink"                  # Exceso de tinta
    SMEAR = "smear"                            # Manchado
    STREAK = "streak"                          # Rayas/bandas
    
    # Defectos de material
    CONTAMINATION = "contamination"            # Suciedad/polvo
    SPOT = "spot"                              # Mancha aislada
    DIE_CUT_ERROR = "die_cut_error"           # Error de troquelado
    
    # Defectos de color
    COLOR_OOT = "color_oot"                    # Color fuera de spec
    
    # Fallback
    UNKNOWN = "unknown"                        # No clasificable


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
    confidence_score: float                    # 0-1
    rule_applied: str                          # Qué regla determinó severidad
    
    # Evidencia (opcional)
    thumbnail_base64: Optional[str] = None
    heatmap_base64: Optional[str] = None
    
    # Metadata
    frame_number: int = 0
    properties: Dict = field(default_factory=dict)  # aspect_ratio, color_variance, etc


class DefectClassifier:
    """
    Motor determinístico de clasificación de defectos
    - Tipo de defecto basado en características
    - Severidad por reglas auditables
    """
    
    def __init__(self):
        self.classification_log: List[Dict] = []
    
    def classify_defect(self,
                       defect_data: dict,
                       recipe_thresholds: Optional[dict] = None) -> DefectRecord:
        """
        Clasificar defecto de forma DETERMINÍSTICA
        
        Args:
            defect_data: {
                'x': float, 'y': float, 'area': float,
                'aspect_ratio': float (optional),
                'color_variance': float (optional),
                'no_pixels': bool (optional),
                'confidence': float (optional),
                'roi_id': str,
                'frame_number': int
            }
            recipe_thresholds: {
                'critical_area': int,
                'major_area': int,
                'critical_defect_types': List[str]
            }
        
        Returns:
            DefectRecord con tipo y severidad determinísticos
        """
        
        # Thresholds por defecto
        if recipe_thresholds is None:
            recipe_thresholds = {
                "critical_area": 500,
                "major_area": 150,
                "critical_defect_types": ["missing_print", "register_error"]
            }
        
        # [1] Determinar TIPO
        defect_type = self._determine_type(defect_data)
        
        # [2] Evaluar SEVERIDAD según reglas
        severity, rule_applied = self._evaluate_severity(
            defect_type,
            defect_data,
            recipe_thresholds
        )
        
        # [3] Crear registro
        record = DefectRecord(
            defect_id=f"def_{uuid4().hex[:8]}",
            timestamp=datetime.now(),
            type=defect_type,
            severity=severity,
            roi_id=defect_data.get("roi_id", "unknown"),
            x=defect_data.get("x", 0.0),
            y=defect_data.get("y", 0.0),
            area_px=defect_data.get("area", 0.0),
            confidence_score=defect_data.get("confidence", 0.5),
            rule_applied=rule_applied,
            frame_number=defect_data.get("frame_number", 0),
            properties={
                "aspect_ratio": defect_data.get("aspect_ratio", 1.0),
                "color_variance": defect_data.get("color_variance", 0.0)
            }
        )
        
        # Log para auditoría
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "defect_id": record.defect_id,
            "type": record.type.value,
            "severity": record.severity.value,
            "area": record.area_px,
            "confidence": record.confidence_score,
            "rule": rule_applied,
            "roi_id": record.roi_id
        }
        self.classification_log.append(log_entry)
        
        logger.info(
            f"Defect classified: {record.defect_id} "
            f"type={record.type.value} severity={record.severity.value} "
            f"area={record.area_px:.0f}px rule='{rule_applied}'"
        )
        
        return record
    
    def _determine_type(self, defect_data: dict) -> DefectType:
        """
        Determinar tipo de defecto basado en características
        Reglas heurísticas pero DETERMINÍSTICAS
        """
        
        area = defect_data.get("area", 0)
        aspect_ratio = defect_data.get("aspect_ratio", 1.0)
        color_variance = defect_data.get("color_variance", 0.0)
        no_pixels = defect_data.get("no_pixels", False)
        
        # Regla 1: Muy pequeño → SPOT
        if area < 50:
            return DefectType.SPOT
        
        # Regla 2: Muy alargado → STREAK
        if area > 1000 and aspect_ratio > 5:
            return DefectType.STREAK
        
        # Regla 3: Sin píxeles en ROI esperado → MISSING_PRINT
        if no_pixels:
            return DefectType.MISSING_PRINT
        
        # Regla 4: Varianza de color alta → EXCESS_INK
        if color_variance > 30:
            return DefectType.EXCESS_INK
        
        # Regla 5: Área mediana, aspecto regular → ARTWORK_DIFF (por defecto)
        if 50 <= area <= 1000 and 0.5 < aspect_ratio < 5:
            return DefectType.ARTWORK_DIFF
        
        # Fallback
        return DefectType.UNKNOWN
    
    def _evaluate_severity(self,
                          defect_type: DefectType,
                          defect_data: dict,
                          thresholds: dict) -> tuple:
        """
        Evaluar severidad de forma DETERMINÍSTICA y AUDITABLE
        
        Returns:
            (DefectSeverity, str con regla aplicada)
        """
        
        area = defect_data.get("area", 0)
        critical_area = thresholds.get("critical_area", 500)
        major_area = thresholds.get("major_area", 150)
        critical_types = thresholds.get("critical_defect_types", [])
        
        # ─────────────────────────────────────────────────────
        # REGLA 1: Tipos críticos siempre evalúan por área
        # ─────────────────────────────────────────────────────
        if defect_type.value in critical_types:
            if area > critical_area:
                rule = f"Type={defect_type.value}+Area({area:.0f}px)>{critical_area}px"
                return DefectSeverity.CRITICAL, rule
            elif area > major_area:
                rule = f"Type={defect_type.value}+Area({area:.0f}px)>{major_area}px"
                return DefectSeverity.MAJOR, rule
            else:
                rule = f"Type={defect_type.value}+Area({area:.0f}px)<{major_area}px"
                return DefectSeverity.MINOR, rule
        
        # ─────────────────────────────────────────────────────
        # REGLA 2: Otros tipos se evalúan por área
        # ─────────────────────────────────────────────────────
        if area > critical_area:
            rule = f"Area({area:.0f}px)>{critical_area}px"
            return DefectSeverity.CRITICAL, rule
        elif area > major_area:
            rule = f"Area({area:.0f}px)>{major_area}px"
            return DefectSeverity.MAJOR, rule
        else:
            rule = f"Area({area:.0f}px)<{major_area}px"
            return DefectSeverity.MINOR, rule
    
    def get_classification_log(self) -> List[Dict]:
        """Retornar historial de clasificaciones (para auditoría)"""
        return self.classification_log
    
    def clear_log(self) -> None:
        """Limpiar historial"""
        self.classification_log.clear()
    
    def get_summary(self) -> Dict:
        """Resumen estadístico de clasificaciones"""
        if not self.classification_log:
            return {
                "total": 0,
                "by_type": {},
                "by_severity": {}
            }
        
        by_type = {}
        by_severity = {}
        
        for entry in self.classification_log:
            # Por tipo
            defect_type = entry["type"]
            by_type[defect_type] = by_type.get(defect_type, 0) + 1
            
            # Por severidad
            severity = entry["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total": len(self.classification_log),
            "by_type": by_type,
            "by_severity": by_severity
        }
