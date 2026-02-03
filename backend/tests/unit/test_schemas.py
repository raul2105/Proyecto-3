"""
Unit tests for data schemas
"""
import pytest
from datetime import datetime
from schemas import (
    DefectEvent, ColorEvent, AlarmEvent, JobConfig, SeverityLevel, DefectType,
    generate_defect_id, generate_color_event_id, generate_alarm_id
)


def test_defect_event_creation():
    """Test DefectEvent schema creation"""
    timestamp = datetime.now()
    defect = DefectEvent(
        id="def_001",
        type=DefectType.SCRATCH,
        severity=SeverityLevel.CRITICAL,
        x=100.0,
        y=200.0,
        area=150.5,
        meters=5.5,
        label_index=2,
        timestamp=timestamp
    )
    
    assert defect.id == "def_001"
    assert defect.type == DefectType.SCRATCH
    assert defect.severity == SeverityLevel.CRITICAL
    assert defect.x == 100.0
    assert defect.meters == 5.5


def test_defect_event_validation():
    """Test DefectEvent validation"""
    timestamp = datetime.now()
    
    # Negative area should raise validation error
    with pytest.raises(ValueError):
        DefectEvent(
            id="def_002",
            type=DefectType.HOLE,
            severity=SeverityLevel.MAJOR,
            x=50.0,
            y=60.0,
            area=-10.0,  # Invalid
            meters=1.0,
            label_index=0,
            timestamp=timestamp
        )


def test_color_event_creation():
    """Test ColorEvent schema creation"""
    timestamp = datetime.now()
    color_event = ColorEvent(
        id="col_001",
        roi_name="cyan_patch",
        lab_l=50.0,
        lab_a=25.0,
        lab_b=-30.0,
        target_lab_l=51.0,
        target_lab_a=24.0,
        target_lab_b=-29.0,
        delta_e=1.5,
        meters=10.0,
        label_index=3,
        timestamp=timestamp,
        in_tolerance=True
    )
    
    assert color_event.roi_name == "cyan_patch"
    assert color_event.delta_e == 1.5
    assert color_event.in_tolerance is True


def test_alarm_event_creation():
    """Test AlarmEvent schema creation"""
    timestamp = datetime.now()
    alarm = AlarmEvent(
        id="alm_001",
        alarm_type="defect_critical",
        severity=SeverityLevel.CRITICAL,
        message="Critical defect detected",
        actions_taken=["stop_line", "buzzer"],
        timestamp=timestamp,
        hysteresis_window_ms=2000,
        confirmation_count=2
    )
    
    assert alarm.alarm_type == "defect_critical"
    assert "stop_line" in alarm.actions_taken
    assert alarm.hysteresis_window_ms == 2000


def test_job_config_hash():
    """Test JobConfig hash calculation"""
    config = JobConfig(
        name="TestJob",
        client="TestClient",
        exposure=-5.0
    )
    
    # Calculate initial hash
    config.update_hash()
    hash1 = config.config_hash
    assert hash1 is not None
    
    # Change a value
    config.exposure = -6.0
    config.update_hash()
    hash2 = config.config_hash
    
    # Hash should be different
    assert hash1 != hash2


def test_id_generation():
    """Test ID generation functions"""
    timestamp = datetime.now()
    
    defect_id = generate_defect_id(timestamp)
    assert defect_id.startswith("def_")
    
    color_id = generate_color_event_id(timestamp)
    assert color_id.startswith("col_")
    
    alarm_id = generate_alarm_id(timestamp)
    assert alarm_id.startswith("alm_")
