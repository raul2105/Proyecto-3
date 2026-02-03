"""
Data Schemas for Flexo Inspection System
Stable, versionable data structures for defects, events, and configurations
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum
import hashlib
import json


# Schema version for migration tracking
SCHEMA_VERSION = "1.0.0"


class SeverityLevel(str, Enum):
    """Defect severity levels"""
    CRITICAL = "CRITICAL"  # Stop line immediately
    MAJOR = "MAJOR"        # Log and alert, consider stopping
    MINOR = "MINOR"        # Log only, trending


class DefectType(str, Enum):
    """Taxonomy of defect types"""
    SCRATCH = "scratch"
    HOLE = "hole"
    COLOR_SHIFT = "color_shift"
    MISALIGNMENT = "misalignment"
    SPOT = "spot"
    EDGE_DAMAGE = "edge_damage"
    CLEAR_ON_CLEAR = "clear_on_clear"
    MICRO_DEFECT = "micro_defect"
    OTHER = "other"


class DefectEvent(BaseModel):
    """
    Defect event schema with complete traceability
    All defects logged must use this schema
    """
    # Identification
    id: str = Field(..., description="Unique defect ID (e.g., def_20260203_123456_001)")
    schema_version: str = Field(default=SCHEMA_VERSION, description="Schema version for migrations")
    
    # Classification
    type: DefectType = Field(..., description="Type of defect")
    severity: SeverityLevel = Field(..., description="Severity level")
    
    # Spatial information
    x: float = Field(..., description="X coordinate in pixels")
    y: float = Field(..., description="Y coordinate in pixels")
    area: float = Field(..., description="Defect area in pixels²")
    width: Optional[float] = Field(None, description="Defect width in pixels")
    height: Optional[float] = Field(None, description="Defect height in pixels")
    
    # Position tracking
    meters: float = Field(..., description="Position in meters from roll start")
    label_index: int = Field(..., description="Label index in web (0-7 for 8-up)")
    
    # Temporal information
    timestamp: datetime = Field(..., description="Detection timestamp")
    
    # Additional metadata
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Detection confidence")
    roi_name: Optional[str] = Field(None, description="ROI where defect was detected")
    image_path: Optional[str] = Field(None, description="Path to evidence image")
    
    # Job context
    job_id: Optional[str] = Field(None, description="Job ID")
    roll_id: Optional[str] = Field(None, description="Roll ID")
    
    class Config:
        use_enum_values = True
    
    @validator('area')
    def validate_area(cls, v):
        if v < 0:
            raise ValueError('Area must be non-negative')
        return v
    
    def to_dict_stable(self) -> Dict[str, Any]:
        """Stable dictionary representation for storage"""
        return self.dict(exclude_none=True)


class ColorEvent(BaseModel):
    """
    Color measurement event schema
    Records Lab values and Delta-E for quality monitoring
    """
    # Identification
    id: str = Field(..., description="Unique color event ID")
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    # Color measurement
    roi_name: str = Field(..., description="ROI name (e.g., 'cyan_patch')")
    lab_l: float = Field(..., ge=0, le=100, description="Lab L* value")
    lab_a: float = Field(..., description="Lab a* value")
    lab_b: float = Field(..., description="Lab b* value")
    
    # Comparison
    target_lab_l: Optional[float] = Field(None, description="Target Lab L*")
    target_lab_a: Optional[float] = Field(None, description="Target Lab a*")
    target_lab_b: Optional[float] = Field(None, description="Target Lab b*")
    delta_e: Optional[float] = Field(None, ge=0, description="Delta-E from target")
    
    # Position tracking
    meters: float = Field(..., description="Position in meters")
    label_index: int = Field(..., description="Label index")
    
    # Temporal
    timestamp: datetime = Field(...)
    
    # Context
    job_id: Optional[str] = Field(None)
    roll_id: Optional[str] = Field(None)
    
    # Status
    in_tolerance: bool = Field(..., description="Whether color is within tolerance")
    
    def to_dict_stable(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class AlarmEvent(BaseModel):
    """
    Alarm event schema
    Records all alarms with severity and actions taken
    """
    # Identification
    id: str = Field(..., description="Unique alarm ID")
    schema_version: str = Field(default=SCHEMA_VERSION)
    
    # Classification
    alarm_type: Literal["defect_critical", "defect_density", "color_out_of_spec", 
                       "registration_error", "system_error"] = Field(...)
    severity: SeverityLevel = Field(...)
    
    # Description
    message: str = Field(..., description="Human-readable alarm message")
    
    # Actions taken
    actions_taken: List[str] = Field(default_factory=list, 
                                     description="Actions executed (e.g., ['stop_line', 'buzzer'])")
    
    # Temporal
    timestamp: datetime = Field(...)
    acknowledged_at: Optional[datetime] = Field(None)
    acknowledged_by: Optional[str] = Field(None)
    
    # Context
    job_id: Optional[str] = Field(None)
    roll_id: Optional[str] = Field(None)
    
    # Related events
    related_defect_ids: List[str] = Field(default_factory=list)
    related_color_event_ids: List[str] = Field(default_factory=list)
    
    # Hysteresis tracking
    hysteresis_window_ms: Optional[int] = Field(None, description="Hysteresis window in ms")
    confirmation_count: int = Field(default=1, description="Number of confirmations before triggering")
    
    def to_dict_stable(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class ToleranceConfig(BaseModel):
    """Tolerance configuration for registration and alignment"""
    position_x_mm: float = Field(default=1.0, description="Max X position error in mm")
    position_y_mm: float = Field(default=1.0, description="Max Y position error in mm")
    rotation_deg: float = Field(default=2.0, description="Max rotation error in degrees")
    scale_pct: float = Field(default=2.0, description="Max scale error in percent")


class DefectThresholdConfig(BaseModel):
    """Defect detection thresholds"""
    min_area_px: float = Field(default=10.0, description="Minimum defect area in pixels")
    sensitivity: float = Field(default=0.5, ge=0, le=1, description="Detection sensitivity")
    critical_area_threshold_px: float = Field(default=500.0, description="Area threshold for critical severity")
    major_area_threshold_px: float = Field(default=100.0, description="Area threshold for major severity")


class ColorTargetConfig(BaseModel):
    """Color target configuration for monitoring"""
    name: str = Field(..., description="Target name")
    roi: Dict[str, int] = Field(..., description="ROI coordinates {x, y, width, height}")
    target_lab_l: float = Field(...)
    target_lab_a: float = Field(...)
    target_lab_b: float = Field(...)
    tolerance_delta_e: float = Field(default=2.0, description="Max acceptable Delta-E")


class StopRuleConfig(BaseModel):
    """Stop rules configuration with hysteresis"""
    enable_stop_on_critical: bool = Field(default=True)
    enable_stop_on_density: bool = Field(default=True)
    max_defects_per_frame: int = Field(default=3, description="Max defects before stop")
    density_threshold_per_meter: int = Field(default=10, description="Max defects per meter")
    hysteresis_window_ms: int = Field(default=2000, description="Confirmation window in ms")
    confirmation_count: int = Field(default=2, description="Confirmations needed before stop")


class AuditModeConfig(BaseModel):
    """Audit mode configuration for micro-defect trending"""
    enabled: bool = Field(default=True)
    micro_defect_min_size_mm: float = Field(default=0.05)
    micro_defect_max_size_mm: float = Field(default=0.08)
    log_interval_m: float = Field(default=1.0, description="Logging interval in meters")
    density_alarm_threshold: int = Field(default=50, description="Micro-defects per meter to trigger alarm")


class JobConfig(BaseModel):
    """
    Complete job configuration
    Versionable and auditable
    """
    # Metadata
    config_version: str = Field(default="1.0.0", description="Config schema version")
    config_hash: Optional[str] = Field(None, description="SHA256 hash for change detection")
    
    # Identification
    name: str = Field(..., description="Job/Recipe name")
    client: str = Field(default="", description="Client name")
    description: Optional[str] = Field(None)
    
    # Master image
    master_image_path: Optional[str] = Field(None)
    
    # Camera settings
    exposure: float = Field(default=-5.0)
    gain: Optional[float] = Field(None)
    
    # Tolerances
    tolerances: ToleranceConfig = Field(default_factory=ToleranceConfig)
    
    # Defect detection
    defect_thresholds: DefectThresholdConfig = Field(default_factory=DefectThresholdConfig)
    
    # Color monitoring
    color_targets: List[ColorTargetConfig] = Field(default_factory=list)
    
    # Decision rules
    stop_rules: StopRuleConfig = Field(default_factory=StopRuleConfig)
    
    # Audit mode
    audit_mode: AuditModeConfig = Field(default_factory=AuditModeConfig)
    
    # Retention
    retention_days_images: int = Field(default=7)
    retention_days_events: int = Field(default=90)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(None)
    
    def calculate_hash(self) -> str:
        """Calculate SHA256 hash of configuration for change tracking"""
        # Exclude metadata fields from hash
        config_dict = self.dict(exclude={'config_hash', 'created_at', 'updated_at', 'created_by'})
        config_str = json.dumps(config_dict, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def update_hash(self):
        """Update the config hash"""
        self.config_hash = self.calculate_hash()
        self.updated_at = datetime.now()
    
    def to_dict_stable(self) -> Dict[str, Any]:
        return self.dict()


class MetricRecord(BaseModel):
    """System metric record for operational monitoring"""
    metric_name: str = Field(...)
    value: float = Field(...)
    unit: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.now)
    tags: Dict[str, str] = Field(default_factory=dict)


# Helper functions for ID generation
def generate_defect_id(timestamp: datetime) -> str:
    """Generate unique defect ID"""
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
    return f"def_{ts_str}"


def generate_color_event_id(timestamp: datetime) -> str:
    """Generate unique color event ID"""
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
    return f"col_{ts_str}"


def generate_alarm_id(timestamp: datetime) -> str:
    """Generate unique alarm ID"""
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
    return f"alm_{ts_str}"
