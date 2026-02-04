"""
Interfaces and Contracts for Flexo Inspection System Modules
Defines protocols for decoupling and testability
"""
from typing import Protocol, List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from schemas import DefectEvent, ColorEvent, AlarmEvent, JobConfig


class IAcquisitionService(Protocol):
    """Interface for image acquisition (camera control, buffering, timestamps)"""
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize acquisition hardware/simulator"""
        ...
    
    def get_frame(self) -> Tuple[np.ndarray, datetime]:
        """Get next frame with timestamp"""
        ...
    
    def set_exposure(self, exposure: float) -> None:
        """Set camera exposure"""
        ...
    
    def set_gain(self, gain: float) -> None:
        """Set camera gain"""
        ...
    
    def release(self) -> None:
        """Release acquisition resources"""
        ...


class ISyncService(Protocol):
    """Interface for encoder synchronization and position tracking"""
    
    def initialize(self, mm_per_tick: float, jitter_tolerance_ms: float) -> None:
        """Initialize encoder parameters"""
        ...
    
    def process_pulse(self, timestamp: datetime) -> float:
        """Process encoder pulse and return position in mm"""
        ...
    
    def get_position_mm(self) -> float:
        """Get current position in mm"""
        ...
    
    def calculate_px_per_mm(self, image_width_px: int, web_width_mm: float) -> float:
        """Calculate spatial resolution"""
        ...
    
    def is_valid_pulse(self, dt_ms: float) -> bool:
        """Check if pulse timing is within jitter tolerance"""
        ...


class IPreprocessService(Protocol):
    """Interface for image preprocessing (flat-field, shading, denoise)"""
    
    def apply_flat_field_correction(self, image: np.ndarray) -> np.ndarray:
        """Apply flat-field correction"""
        ...
    
    def apply_shading_correction(self, image: np.ndarray) -> np.ndarray:
        """Apply shading correction"""
        ...
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Apply denoising"""
        ...
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """Normalize image intensity"""
        ...


class IInspectionService(Protocol):
    """Interface for defect detection and comparison vs master"""
    
    def set_master(self, master_image: np.ndarray) -> None:
        """Set reference master image"""
        ...
    
    def align_images(self, live_image: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """Align live image to master, return aligned image and registration metrics"""
        ...
    
    def detect_defects(self, aligned_image: np.ndarray, tolerances: Dict[str, float]) -> List[DefectEvent]:
        """Detect defects in aligned image"""
        ...
    
    def detect_clear_on_clear(self, image: np.ndarray) -> List[DefectEvent]:
        """Specialized detection for clear-on-clear defects"""
        ...


class IColorService(Protocol):
    """Interface for color monitoring and Delta-E calculation"""
    
    def measure_color(self, image: np.ndarray, roi: Dict[str, Any]) -> ColorEvent:
        """Measure color in specified ROI and return Lab values and Delta-E"""
        ...
    
    def set_color_targets(self, targets: List[Dict[str, Any]]) -> None:
        """Set target color values for comparison"""
        ...
    
    def calculate_delta_e(self, lab1: Tuple[float, float, float], 
                         lab2: Tuple[float, float, float]) -> float:
        """Calculate Delta-E between two Lab colors"""
        ...


class IDecisionService(Protocol):
    """Interface for severity evaluation, stop rules, audit mode"""
    
    def evaluate_defect_severity(self, defect: DefectEvent, 
                                 thresholds: Dict[str, Any]) -> str:
        """Evaluate defect severity (CRITICAL, MAJOR, MINOR)"""
        ...
    
    def should_stop_line(self, defects: List[DefectEvent], 
                        rules: Dict[str, Any]) -> Tuple[bool, str]:
        """Determine if line should stop based on rules and hysteresis"""
        ...
    
    def log_microdefect(self, defect: DefectEvent, position_m: float) -> None:
        """Log microdefect for audit/trending (no immediate stop)"""
        ...
    
    def check_density_alarm(self, position_m: float, window_m: float) -> Optional[AlarmEvent]:
        """Check if microdefect density exceeds threshold"""
        ...


class IPLCService(Protocol):
    """Interface for PLC/IO integration"""
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """Connect to PLC"""
        ...
    
    def send_signal(self, signal_type: str, duration_ms: int) -> bool:
        """Send signal to PLC (tower_light, buzzer, stop_line, mark_segment)"""
        ...
    
    def read_inputs(self) -> Dict[str, bool]:
        """Read PLC inputs (job_start, job_end, splice, EOR)"""
        ...
    
    def enter_safe_mode(self) -> None:
        """Enter fail-safe mode on critical error"""
        ...
    
    def disconnect(self) -> None:
        """Disconnect from PLC"""
        ...


class IStorageService(Protocol):
    """Interface for event persistence and traceability"""
    
    def insert_defect(self, defect: DefectEvent, job_id: str, roll_id: str) -> str:
        """Insert defect event and return event ID"""
        ...
    
    def insert_color_event(self, color_event: ColorEvent, job_id: str, roll_id: str) -> str:
        """Insert color measurement event"""
        ...
    
    def insert_alarm(self, alarm: AlarmEvent, job_id: str, roll_id: str) -> str:
        """Insert alarm event"""
        ...
    
    def query_defects(self, job_id: Optional[str], roll_id: Optional[str],
                     start_time: Optional[datetime], end_time: Optional[datetime]) -> List[DefectEvent]:
        """Query defects with filters"""
        ...
    
    def cleanup_retention(self, retention_days: int) -> int:
        """Clean up old data based on retention policy, return number of records deleted"""
        ...


class IReportingService(Protocol):
    """Interface for report generation"""
    
    def generate_roll_report(self, roll_id: str) -> bytes:
        """Generate PDF/CSV report for a roll"""
        ...
    
    def generate_job_report(self, job_id: str) -> bytes:
        """Generate PDF/CSV report for a job"""
        ...
    
    def export_defect_map(self, roll_id: str) -> bytes:
        """Export defect map by meter"""
        ...


class IOpsService(Protocol):
    """Interface for operational monitoring (logging, health checks, watchdog)"""
    
    def log_structured(self, level: str, message: str, metadata: Dict[str, Any]) -> None:
        """Log structured message with metadata"""
        ...
    
    def record_metric(self, metric_name: str, value: float, unit: str) -> None:
        """Record a metric (FPS, latency, etc.)"""
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """Return system health status"""
        ...
    
    def watchdog_ping(self) -> None:
        """Ping watchdog to indicate system is alive"""
        ...
    
    def get_metrics_summary(self, window_minutes: int) -> Dict[str, Any]:
        """Get aggregated metrics for time window"""
        ...
