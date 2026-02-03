# MVP Industrial Inspection System - Architecture Implementation

## EXECUTIVE SUMMARY

This document describes the implementation of a modular, industrial-grade inspection system for flexographic printing (narrow web 330-350mm) with encoder synchronization, defect detection, color monitoring, PLC integration, and full traceability.

**Status**: MVP Foundation Complete ✅  
**Schema Version**: 1.0.0  
**Test Coverage**: 16 unit tests passing  
**CI/CD**: GitHub Actions configured  

---

## 1. MODULAR ARCHITECTURE IMPLEMENTED

### Folder Structure Created

```
backend/
├── acquisition/          # Camera control, buffering, timestamps
├── sync/                 # ✅ Encoder synchronization (IMPLEMENTED)
│   └── encoder.py       # EncoderSync, EncoderSimulator
├── preprocess/           # Flat-field, shading, denoise, normalization
├── inspection/           # Defect detection, alignment, clear-on-clear
├── color/                # Delta-E monitoring, Lab conversion
├── decision/             # Severity evaluation, stop rules, hysteresis, audit mode
├── plc_io/               # PLC integration, fail-safe mode
├── storage/              # Event persistence, 7-day retention
├── hmi/                  # Dashboard, trending, alarmsInterface modules
├── reporting/            # PDF/CSV generation, defect maps
├── ops/                  # Logging, metrics, health checks, watchdog
├── simulator/            # ✅ Replay simulator (STARTED)
│   └── replay.py        # ReplayDataset, ReplaySimulator, DatasetRecorder
└── tests/                # ✅ Test infrastructure (COMPLETE)
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    ├── fixtures/         # Test data
    └── datasets/         # Replay datasets
```

---

## 2. INTERFACES & CONTRACTS (interfaces.py)

### Protocols Defined

All modules implement Protocol interfaces for decoupling:

- **IAcquisitionService**: Camera control, frame acquisition
- **ISyncService**: ✅ Encoder synchronization, position tracking
- **IPreprocessService**: Image preprocessing
- **IInspectionService**: Defect detection, alignment
- **IColorService**: Color monitoring, Delta-E
- **IDecisionService**: Severity evaluation, stop rules
- **IPLCService**: PLC communication, fail-safe
- **IStorageService**: Event persistence
- **IReportingService**: Report generation
- **IOpsService**: Operational monitoring

**Benefits**:
- Testable in isolation
- Swappable implementations
- Clear contracts between modules
- Type-safe interfaces

---

## 3. DATA SCHEMAS (schemas.py) ✅

### Core Schemas Implemented

#### DefectEvent
```python
id: str                    # Unique ID (def_YYYYMMDD_HHMMSS_ffffff)
type: DefectType           # scratch, hole, color_shift, clear_on_clear, etc.
severity: SeverityLevel    # CRITICAL, MAJOR, MINOR
x, y: float                # Pixel coordinates
area: float                # Defect area in px²
meters: float              # Position from roll start (mm)
label_index: int           # Label in web (0-7 for 8-up)
timestamp: datetime        # Detection time
confidence: float          # Optional detection confidence
roi_name: str              # Optional ROI name
image_path: str            # Path to evidence image
job_id, roll_id: str       # Traceability
schema_version: str        # For migrations (1.0.0)
```

#### ColorEvent
```python
id: str
roi_name: str              # e.g., "cyan_patch"
lab_l, lab_a, lab_b: float # Lab color values
target_lab_*: float        # Target values
delta_e: float             # Color difference
meters: float              # Position
label_index: int
timestamp: datetime
in_tolerance: bool         # Pass/fail
```

#### AlarmEvent
```python
id: str
alarm_type: str            # defect_critical, defect_density, color_out_of_spec, etc.
severity: SeverityLevel
message: str               # Human-readable
actions_taken: List[str]   # ["stop_line", "buzzer", "tower_red"]
timestamp: datetime
hysteresis_window_ms: int  # Confirmation window
confirmation_count: int    # Confirmations before trigger
related_defect_ids: List   # Linked events
```

#### JobConfig (with Versioning)
```python
name: str
client: str
master_image_path: str
exposure, gain: float
tolerances: ToleranceConfig
defect_thresholds: DefectThresholdConfig
color_targets: List[ColorTargetConfig]
stop_rules: StopRuleConfig
audit_mode: AuditModeConfig
retention_days_images: int (default 7)
retention_days_events: int (default 90)
config_hash: str           # SHA256 for change detection
config_version: str        # Schema version
```

### Schema Features
- ✅ Pydantic validation
- ✅ Stable serialization (`.to_dict_stable()`)
- ✅ Version tracking for migrations
- ✅ Hash-based change detection
- ✅ Timestamp tracking (created_at, updated_at)

---

## 4. ENCODER SYNCHRONIZATION MODULE ✅

### Implementation (sync/encoder.py)

#### EncoderSync Class
```python
mm_per_tick: float         # Linear distance per encoder pulse
jitter_tolerance_ms: float # Max acceptable timing variation

Methods:
- process_pulse(timestamp) → float    # Update position, return mm
- get_position_mm() → float           # Current position
- get_position_m() → float            # Current position in meters
- calculate_px_per_mm(image_width, web_width) → float
- is_valid_pulse(dt_ms) → bool        # Jitter detection
- get_speed_mpm() → float             # Line speed in m/min
- get_jitter_statistics() → dict     # Diagnostic info
- reset()                              # Reset position tracking
```

#### Features Implemented
✅ Position tracking (mm and meters)  
✅ Jitter detection (configurable tolerance)  
✅ Speed estimation from pulse intervals  
✅ Spatial resolution calculation (px/mm)  
✅ Statistics for diagnostics  
✅ EncoderSimulator for testing without hardware  

#### Test Coverage
- ✅ Basic initialization
- ✅ Pulse processing
- ✅ Position tracking
- ✅ Jitter detection
- ✅ Speed estimation
- ✅ px/mm calculation
- ✅ Reset functionality
- ✅ Simulator functionality

**Registration Error Target**: < 1mm (testable with encoder sync)

---

## 5. REPLAY SIMULATOR MODULE (simulator/replay.py) 🔄

### Components

#### ReplayDataset
- Stores frames, timestamps, encoder positions
- Saves to disk with compression (JPEG frames + pickle metadata)
- Supports defect annotations

#### ReplaySimulator
- Plays back recorded datasets
- Variable speed control (0.1x to 10x)
- Loop mode support
- Frame-by-frame or position-based access

#### DatasetRecorder
- Records live camera feed
- Annotates defects during recording
- Saves for later replay

### Usage
```python
# Create synthetic dataset
dataset = create_synthetic_dataset("test_run_001", num_frames=100)
dataset.save("/path/to/datasets")

# Load and replay
simulator = ReplaySimulator()
simulator.load_dataset("/path/to/datasets", "test_run_001")
simulator.set_speed(2.0)  # 2x speed
simulator.start()

while True:
    result = simulator.get_next_frame()
    if result is None:
        break
    frame, timestamp, position_mm = result
    # Process frame...
```

---

## 6. CI/CD PIPELINE ✅

### GitHub Actions Workflow (.github/workflows/ci.yml)

#### Jobs Configured

**1. lint-and-test**
- Python 3.10 setup
- Dependency caching
- Linting: flake8 (syntax errors stop build)
- Format check: black
- Type check: mypy (non-blocking)
- Unit tests: pytest with coverage
- Integration tests: pytest (non-blocking)
- Coverage report upload

**2. security-scan**
- Security scanning: bandit
- Dependency vulnerability check: safety
- Non-blocking (review required)

#### Triggers
- Push to: main, develop, copilot/**
- Pull requests to: main, develop

#### Artifacts
- Test results (HTML coverage report)
- Coverage XML
- Bandit security report

---

## 7. TEST SUITE ✅

### Structure
```
tests/
├── unit/                 # 16 tests passing
│   ├── test_schemas.py  # 6 tests
│   ├── test_encoder.py  # 8 tests
│   └── test_encoder_simple.py # 2 tests
├── integration/          # Empty (to be filled)
├── fixtures/             # Test fixtures
└── datasets/             # Replay datasets
```

### Test Infrastructure
- ✅ pytest.ini configured
- ✅ Test markers (unit, integration, slow)
- ✅ Coverage tracking
- ✅ README with usage guide

### Running Tests
```bash
cd backend
pytest                    # All tests
pytest tests/unit -v      # Unit tests
pytest --cov=.           # With coverage
```

### Test Results
```
tests/unit/test_schemas.py::test_defect_event_creation PASSED
tests/unit/test_schemas.py::test_defect_event_validation PASSED
tests/unit/test_schemas.py::test_color_event_creation PASSED
tests/unit/test_schemas.py::test_alarm_event_creation PASSED
tests/unit/test_schemas.py::test_job_config_hash PASSED
tests/unit/test_schemas.py::test_id_generation PASSED
tests/unit/test_encoder.py::* (8 tests) PASSED
tests/unit/test_encoder_simple.py::* (2 tests) PASSED
```

---

## 8. CRITICAL ASSUMPTIONS & QUESTIONS

### Assumptions Made (ASSUMPTION)

**A1: Line Speed**
- Assumed: 5-100 m/min (nominal 30 m/min)
- Target FPS: 15 fps for nominal speed
- **Question**: ¿Cuál es la velocidad máxima real de producción?

**A2: Encoder Specifications**
- Assumed: Incremental encoder, 1000 PPR (pulses per revolution)
- mm_per_tick configurable
- **Question**: ¿Tienen encoder instalado? ¿Especificaciones exactas?

**A3: Camera Resolution**
- Assumed: Line-scan camera or area scan ≥1280x720
- Web width: 330-350mm
- Spatial resolution: ~3.8 px/mm
- **Question**: ¿Qué resolución espacial necesitan (mm/píxel)?

**A4: Microdefect Resolution**
- Assumed: 0.05-0.08mm detectable with appropriate optics
- **Question**: ¿Es realista esta resolución con su setup actual?

**A5: Clear-on-Clear Detection**
- Assumed: Backlight illumination available
- **Question**: ¿Tienen backlight instalado o planificado?

**A6: PLC Protocol**
- Assumed: Modbus TCP as default
- **Question**: ¿Marca y modelo exacto del PLC?

**A7: False Negative Rate**
- Proposed: FNR < 5% for CRITICAL defects
- **Question**: ¿Cuál es el FNR objetivo aceptable?

**A8: Storage**
- Assumed: 7 days retention for high-res images
- Estimated: ~100GB for 7 days at 30 m/min
- **Question**: ¿Storage disponible? ¿Requisitos legales?

---

## 9. MVP ACCEPTANCE CRITERIA STATUS

| Criterion | Target | Status |
|-----------|--------|--------|
| **A) Sincronía correcta** | Error < 1mm | ✅ Infrastructure ready, needs testing |
| **B) Defectos críticos** | FNR < 5% (proposed) | ⚠️ Needs validation dataset |
| **C) Microdefectos** | Logging per meter | 📋 Planned in decision module |
| **D) Clear-on-clear** | Pipeline ready | 📋 Planned in inspection module |
| **E) Integración PLC** | Deterministic, fail-safe | 📋 Planned in plc_io module |
| **F) Reportes** | PDF/CSV export | 📋 Planned in reporting module |
| **G) Rendimiento** | <100ms latency, 15 FPS | 🔄 Needs performance testing |

Legend:
- ✅ Complete
- 🔄 In progress
- ⚠️ Blocked/needs input
- 📋 Planned

---

## 10. NEXT IMMEDIATE STEPS

### Phase 1: Core Detection (Priority P0)
1. **Implement Decision Module** [L]
   - Hysteresis logic for stop rules
   - Audit mode for microdefects
   - Density-based alarms
   
2. **Enhance Inspection Module** [L]
   - Clear-on-clear detection pipeline
   - Improved alignment with registration metrics
   - ROI-based inspection

3. **Implement Preprocessing** [M]
   - Flat-field correction
   - Shading correction
   - Denoise filters

### Phase 2: Integration & Testing (Priority P1)
4. **PLC Integration** [M]
   - Implement plc_io module
   - Fail-safe mode
   - Handshake protocol
   
5. **Create Test Datasets** [M]
   - Record real production data
   - Annotate defects
   - Validation set creation

6. **Integration Tests** [M]
   - End-to-end workflows
   - Performance benchmarking
   - Stress testing at target speed

### Phase 3: Operations (Priority P2)
7. **Structured Logging** [S]
   - JSON-formatted logs
   - Metrics collection
   - Watchdog implementation

8. **Reporting Module** [M]
   - PDF report generation
   - Defect map by meter
   - Roll and job summaries

---

## 11. TECHNICAL DEBT & IMPROVEMENTS

### Immediate Fixes Needed
1. **Pydantic V2 Migration**: Update decorators (@validator → @field_validator)
2. **Type Hints**: Add comprehensive type hints for mypy compliance
3. **Error Handling**: Add try-catch blocks in critical paths

### Code Quality
- ✅ Modular structure implemented
- ✅ Interface protocols defined
- ✅ Test infrastructure ready
- ⚠️ Coverage needs improvement (target: >80%)
- ⚠️ Integration tests missing

### Performance Optimizations Pending
- **GPU Acceleration**: Migrate ORB to CUDA (-30ms latency)
- **Differential Transmission**: WebSocket with frame diff (-20ms, -70% bandwidth)
- **Color Cache**: Multi-level cache (-15% CPU)
- **DB Partitioning**: PostgreSQL migration (+40% write throughput)

---

## 12. INDUSTRIAL REQUIREMENTS CHECKLIST

### Safety & Reliability
- [ ] Fail-safe mode implementation
- [ ] Watchdog timer
- [ ] Graceful degradation
- [ ] Error recovery procedures

### Performance
- [ ] <100ms total latency (capture → PLC)
- [ ] 15+ FPS sustained
- [ ] <70% CPU usage
- [ ] <500MB RAM usage

### Traceability
- [x] Stable event schemas
- [x] Version tracking
- [ ] 7-day image retention
- [ ] 90-day event retention
- [ ] Roll/job correlation

### Quality Assurance
- [x] Unit test infrastructure
- [ ] Integration tests
- [ ] Stress tests
- [ ] Metrological validation
- [ ] FNR measurement

---

## 13. METRICS TO TRACK

### Operational Metrics (to implement in ops/)
```python
- fps: float                    # Frames per second
- latency_ms: float             # Total processing latency
- dropped_frames: int           # Frames skipped
- defect_rate_per_m: float      # Defects per meter
- cpu_usage_pct: float          # CPU utilization
- memory_mb: float              # RAM usage
- encoder_jitter_violations: int # Timing issues
- plc_response_ms: float        # PLC communication latency
```

### Quality Metrics
```python
- total_defects: int
- critical_defects: int
- false_positive_rate: float    # Requires validation
- false_negative_rate: float    # Requires validation
- yield_pct: float              # Good labels %
```

---

## 14. CONFIGURATION MANAGEMENT

### Job Configuration Structure
```yaml
# Example job configuration
name: "Client_ABC_SKU_123"
client: "Client ABC"
master_image_path: "/masters/ABC_123.png"

camera:
  exposure: -5.0
  gain: null

encoder:
  mm_per_tick: 0.1
  jitter_tolerance_ms: 20

tolerances:
  position_x_mm: 1.0
  position_y_mm: 1.0
  rotation_deg: 2.0
  scale_pct: 2.0

defect_thresholds:
  min_area_px: 10.0
  sensitivity: 0.5
  critical_area_threshold_px: 500.0
  major_area_threshold_px: 100.0

color_targets:
  - name: "cyan_patch"
    roi: {x: 100, y: 100, width: 50, height: 50}
    target_lab_l: 50.0
    target_lab_a: 25.0
    target_lab_b: -30.0
    tolerance_delta_e: 2.0

stop_rules:
  enable_stop_on_critical: true
  enable_stop_on_density: true
  max_defects_per_frame: 3
  density_threshold_per_meter: 10
  hysteresis_window_ms: 2000
  confirmation_count: 2

audit_mode:
  enabled: true
  micro_defect_min_size_mm: 0.05
  micro_defect_max_size_mm: 0.08
  log_interval_m: 1.0
  density_alarm_threshold: 50

retention:
  images_days: 7
  events_days: 90
```

---

## 15. DEPLOYMENT CHECKLIST

### Pre-Production
- [ ] Validate encoder connection and calibration
- [ ] Calibrate camera (exposure, focus, alignment)
- [ ] Test PLC communication
- [ ] Create master images for test jobs
- [ ] Record validation datasets
- [ ] Performance benchmark at target speed
- [ ] Stress test for 8-hour run

### Production
- [ ] Install watchdog service
- [ ] Configure log rotation
- [ ] Set up backup procedures
- [ ] Train operators on HMI
- [ ] Document troubleshooting procedures
- [ ] Establish maintenance schedule

---

## 16. DOCUMENTATION PROVIDED

- ✅ `backend/interfaces.py` - Interface contracts
- ✅ `backend/schemas.py` - Data schemas
- ✅ `backend/sync/encoder.py` - Encoder synchronization
- ✅ `backend/simulator/replay.py` - Replay simulator
- ✅ `backend/tests/README.md` - Test guide
- ✅ `backend/pytest.ini` - Test configuration
- ✅ `.github/workflows/ci.yml` - CI/CD pipeline
- ✅ This document - Architecture & implementation guide

---

## 17. CONTACTS & SUPPORT

For questions on:
- **Architecture decisions**: Review this document
- **Schema changes**: Check `schemas.py` version and migration guide
- **Testing**: See `tests/README.md`
- **CI/CD**: Check GitHub Actions logs

---

**Document Version**: 1.0.0  
**Last Updated**: 2026-02-03  
**Schema Version**: 1.0.0  
**Test Status**: 16/16 passing  
**CI Status**: Configured, pending first run
