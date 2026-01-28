from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, StreamingResponse
from pydantic import BaseModel, validator
import random
import uvicorn
import fitz  # PyMuPDF
import numpy as np
import cv2
import io
import os
import base64
import time
import json
import math
from datetime import datetime
from collections import deque
import uuid
from typing import Optional
from PIL import Image, ImageDraw
import hashlib
import logging
from logging.handlers import RotatingFileHandler

from inspection import Inspector
from simulator import DefectSimulator
from camera import CameraService
from auth import AuthService, LoginRequest
from diagnostics import Diagnostics
from recipes import RecipeManager, Recipe
from color_module import ColorMonitor, ColorTarget
from defects import DefectClassifier, DefectType, DefectSeverity
from alarms import AlarmEngine, AlarmRule, TriggerType, ActionType, Action
from storage import ensure_db, insert_job, insert_roll, close_roll, insert_defect, insert_color_event, insert_frame

def configure_logging():
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_format = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)

    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setFormatter(log_format)
    error_handler.setLevel(logging.ERROR)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).propagate = True

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/login")
def login(req: LoginRequest):
    try:
        return state.auth_service.login(req)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in memory for MVP)
class SystemState:
    master_image: np.ndarray = None
    master_image_bytes: bytes = None
    master_pyramid = []
    master_meta = {}
    inspector = Inspector()
    simulator = DefectSimulator()
    camera = CameraService()
    recipe_manager = RecipeManager()
    
    # Point 5: Color Monitor
    color_monitor = ColorMonitor()
    
    # Point 6: Defect Classifier
    defect_classifier = DefectClassifier()
    
    # Point 7: Alarm Engine
    alarm_engine = AlarmEngine()
    
    use_simulator: bool = True

    # Line orchestration and traceability state
    events = deque(maxlen=500)
    alarms = {}
    alarm_history = deque(maxlen=500)
    actions = deque(maxlen=500)
    trace_entries = deque(maxlen=2000)
    evidence = deque(maxlen=2000)
    roll_reports = deque(maxlen=200)
    report_queue = deque(maxlen=200)
    wfl_queue = deque(maxlen=200)
    retention_policy = {
        "thumbnails_days": 30,
        "evidence_days": 90,
        "video_days": 14
    }
    frame_history = deque(maxlen=500)
    defect_events = deque(maxlen=2000)
    color_events = deque(maxlen=2000)

    alarm_rules = {
        "critical_defect_area": 500.0,
        "defect_rate_per_frame": 3,
        "brightness_min": 10.0,
        "brightness_max": 245.0
    }
    alarm_actions = {
        "critical_defect": ["tower_red", "buzzer", "plc_signal", "stop_line", "mark_segment"],
        "defect_rate": ["tower_red", "plc_signal", "mark_segment"],
        "deltae_out": ["tower_red", "buzzer", "plc_signal", "mark_segment"],
        "registration_lost": ["tower_red", "buzzer", "plc_signal", "stop_line"],
        "sensor_signal_lost": ["tower_red", "buzzer", "plc_signal", "stop_line"],
        "cmark_missing": ["tower_red", "buzzer", "plc_signal"],
        "cmark_double": ["tower_red", "buzzer", "plc_signal"],
        "cmark_jitter": ["tower_red", "plc_signal"]
    }
    alarm_last_raised = {}
    alarm_cooldown_sec = 2.0

    # Job and roll info
    job_id: str = ""
    sku: str = ""
    roll_id: str = ""
    active_recipe: str = ""
    roll_started_at: float = None
    current_mm: float = 0.0
    segment_length_m: float = 100.0
    segment_index: int = 0
    roll_sequence: int = 1
    last_frame_ts: float = None
    encoder_ticks: int = 0
    label_index: int = 0
    counters = {
        "total_frames": 0,
        "total_defects": 0,
        "deltae_sum": 0.0,
        "deltae_count": 0
    }
    settings = {
        "use_simulator": True,
        "camera_id": None,
        "exposure": -5.0,
        "gain": None,
        "roll_diameter_mm": 600.0,
        "core_diameter_mm": 76.0,
        "material_thickness_mm": 0.05,
        "start_with_last_job": False,
        "simulated_speed_mpm": 30.0,
        "plc_enabled": False,
        "plc_ip": "",
        "plc_port": 502,
        "plc_unit_id": 1,
        "plc_protocol": "modbus_tcp",
        "plc_timeout_ms": 1000,
        "plc_tower_red": "",
        "plc_tower_yellow": "",
        "plc_tower_green": "",
        "plc_buzzer": "",
        "plc_stop_line": ""
    }
    sensor_config = {
        "label_pitch_m": 0.0,
        "cmark_enabled": False,
        "jitter_tolerance_ms": 20,
        "fallback_encoder": True,
        "encoder_pitch_m": 0.0,
        "mm_per_tick": 0.0,
        "repeat_mm": 0.0
    }
    sensor_status = {
        "last_label_ts": None,
        "last_cmark_ts": None,
        "last_cmark_interval_ms": None,
        "last_cmark_missing_ts": None
    }
    sensor_counters = {
        "label_count": 0,
        "cmark_count": 0,
        "cmark_missing_count": 0,
        "cmark_double_count": 0,
        "encoder_count": 0
    }
    recipe_lane_count: int = 1
    last_frames = {
        "live": None,
        "aligned": None,
        "heatmap": None,
        "master": None
    }
    uptime_start = time.time()
    
    # Current Job Info
    client: str = ""
    job_number: str = ""
    roll_number: str = ""

state = SystemState()
state.auth_service = AuthService()
CONFIG_PATH = "config.json"

# Initialize a default target for demo purposes
state.color_monitor.add_target(ColorTarget(
    name="Demo Red",
    l_target=53.24, # Approx Red
    a_target=80.09,
    b_target=67.20,
    tolerance_warning=3.0,
    tolerance_critical=6.0
))

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def log_event(event_type: str, severity: str, message: str, data=None):
    event = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "type": event_type,
        "severity": severity,
        "message": message,
        "data": data or {}
    }
    state.events.append(event)
    return event

def record_action(action_type: str, target: str, reason: str, data=None):
    action = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "action": action_type,
        "target": target,
        "reason": reason,
        "data": data or {}
    }
    state.actions.append(action)
    return action

def trigger_actions(alarm_code: str, severity: str, data=None):
    actions = state.alarm_actions.get(alarm_code, [])
    for action_type in actions:
        payload = {"alarm_code": alarm_code, "severity": severity}
        if data:
            payload.update(data)
        record_action(action_type, "line", "alarm_triggered", payload)
        if action_type == "mark_segment":
            record_action(
                "mark_segment",
                "segment",
                "alarm_triggered",
                {
                    "segment_index": state.segment_index,
            "meter": round(state.current_mm / 1000.0, 2),
                    "alarm_code": alarm_code
                }
            )

def raise_alarm(code: str, severity: str, message: str, data=None):
    now_ts = time.time()
    existing = state.alarms.get(code)
    last_raised = state.alarm_last_raised.get(code)
    if last_raised and (now_ts - last_raised) < state.alarm_cooldown_sec:
        if existing:
            existing["last_seen"] = now_iso()
            existing["data"] = data or {}
            return existing
    if existing and existing.get("active"):
        existing["last_seen"] = now_iso()
        existing["data"] = data or {}
        return existing
    alarm = {
        "code": code,
        "severity": severity,
        "message": message,
        "active": True,
        "acknowledged": False,
        "raised_at": now_iso(),
        "last_seen": now_iso(),
        "data": data or {}
    }
    state.alarms[code] = alarm
    state.alarm_history.append(alarm)
    state.alarm_last_raised[code] = now_ts
    log_event("alarm_raised", severity, message, {"code": code, "data": data or {}})
    trigger_actions(code, severity, data)
    return alarm

def clear_alarm(code: str):
    alarm = state.alarms.get(code)
    if alarm and alarm.get("active"):
        alarm["active"] = False
        log_event("alarm_cleared", alarm.get("severity", "info"), alarm.get("message", ""), {"code": code})
    return alarm

def reset_roll_counters():
    state.counters = {
        "total_frames": 0,
        "total_defects": 0,
        "deltae_sum": 0.0,
        "deltae_count": 0
    }
    state.current_mm = 0.0
    state.segment_index = 0
    state.last_frame_ts = None
    state.roll_started_at = time.time()
    state.settings["roll_diameter_mm"] = state.settings.get("core_diameter_mm", 76.0)
    state.encoder_ticks = 0
    state.label_index = 0

def _defect_bucket(area: float) -> str:
    if area >= state.alarm_rules["critical_defect_area"]:
        return "critical"
    if area >= 200:
        return "medium"
    return "small"

def build_roll_report(roll_id: str):
    report = next((r for r in state.roll_reports if r.get("roll_id") == roll_id), None)
    if not report:
        return None

    defects = [t for t in state.trace_entries if t.get("roll_id") == roll_id and t.get("type") == "defect"]
    by_bucket = {"small": 0, "medium": 0, "critical": 0}
    defect_map = {}
    for d in defects:
        area = d.get("defect", {}).get("area", 0)
        bucket = _defect_bucket(area)
        by_bucket[bucket] += 1
        meter = d.get("meter", 0)
        bin_key = int(meter // state.segment_length_m)
        defect_map[bin_key] = defect_map.get(bin_key, 0) + 1

    total_defects = report.get("total_defects", 0)
    yield_pct = max(0.0, 100.0 - (total_defects * 0.1))
    color_trend = [
        {"ts": m.timestamp, "delta_e": m.delta_e}
        for m in state.color_monitor.measurements
    ][-200:]

    return {
        "report_id": report.get("id"),
        "job_id": report.get("job_id"),
        "roll_id": roll_id,
        "yield_pct": round(yield_pct, 2),
        "defects_by_bucket": by_bucket,
        "defect_map_by_segment": defect_map,
        "color_trend": color_trend,
        "metrics": report
    }

def report_to_csv(report: dict) -> str:
    lines = [
        "roll_id,yield_pct,defects_small,defects_medium,defects_critical,total_defects,meters_processed"
    ]
    metrics = report.get("metrics", {})
    buckets = report.get("defects_by_bucket", {})
    lines.append(
        f"{report.get('roll_id')},{report.get('yield_pct')},{buckets.get('small',0)},{buckets.get('medium',0)},{buckets.get('critical',0)},{metrics.get('total_defects',0)},{metrics.get('meters_processed',0)}"
    )
    lines.append("")
    lines.append("segment_index,defect_count")
    for seg, count in sorted(report.get("defect_map_by_segment", {}).items()):
        lines.append(f"{seg},{count}")
    lines.append("")
    lines.append("timestamp,delta_e")
    for item in report.get("color_trend", []):
        lines.append(f"{item.get('ts')},{item.get('delta_e')}")
    return "\n".join(lines)

def report_to_pdf_bytes(report: dict) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    text = [
        f"Roll Report: {report.get('roll_id')}",
        f"Job: {report.get('job_id')}",
        f"Yield: {report.get('yield_pct')}%",
        f"Defects (small/medium/critical): {report.get('defects_by_bucket')}",
        f"Meters: {report.get('metrics', {}).get('meters_processed', 0)}"
    ]
    page.insert_text((72, 72), "\n".join(text))

    diameter_mm = state.settings.get("roll_diameter_mm", 600.0)
    size = 240
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    center = size // 2
    radius = size // 2 - 12
    draw.ellipse((center - radius, center - radius, center + radius, center + radius), outline=(180, 180, 180), width=4)
    circumference_m = (diameter_mm / 1000.0) * np.pi
    defects = [t for t in state.trace_entries if t.get("roll_id") == report.get("roll_id") and t.get("type") == "defect"]
    for item in defects:
        meter = item.get("meter", 0) or 0
        if circumference_m > 0:
            angle = (meter % circumference_m) / circumference_m * 2 * np.pi
        else:
            angle = 0
        x = center + int(np.cos(angle) * (radius - 6))
        y = center + int(np.sin(angle) * (radius - 6))
        sev = item.get("severity")
        color = (196, 59, 47) if sev == "critical" else (208, 138, 31) if sev == "warning" else (15, 138, 123)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    rect = fitz.Rect(72, 200, 72 + size, 200 + size)
    page.insert_image(rect, stream=img_bytes.read())
    return doc.tobytes()


def persist_roll_report(report: dict) -> dict:
    """Persist roll report to disk under data/{job}/{roll}/"""
    job_id = report.get("job_id") or "unknown"
    roll_id = report.get("roll_id") or "roll"
    base_dir = os.path.join("data", job_id, roll_id)
    os.makedirs(base_dir, exist_ok=True)

    csv_path = os.path.join(base_dir, "report.csv")
    pdf_path = os.path.join(base_dir, "report.pdf")

    with open(csv_path, "w", encoding="utf-8") as fh:
        fh.write(report_to_csv(report))
    with open(pdf_path, "wb") as fh:
        fh.write(report_to_pdf_bytes(report))

    report["csv_path"] = csv_path
    report["pdf_path"] = pdf_path
    return report

def build_wfl_package(roll_id: str):
    defects = [t for t in state.trace_entries if t.get("roll_id") == roll_id and t.get("type") == "defect"]
    return {
        "roll_id": roll_id,
        "job_id": state.job_id,
        "sku": state.sku,
        "segment_length_m": state.segment_length_m,
        "defect_map": [
            {
                "meter": d.get("meter"),
                "segment_index": d.get("segment_index"),
                "severity": d.get("severity"),
                "defect": d.get("defect")
            }
            for d in defects
        ],
        "meta": {
            "encoder_resets": 0,
            "notes": ""
        }
    }

def acquire_live_frame():
    try:
        if state.use_simulator:
            if state.master_image is not None:
                live_img = state.master_image.copy()
                live_img = state.simulator.add_defects(live_img, count=random.randint(1, 3))
            else:
                live_img = np.zeros((720, 1280, 3), dtype=np.uint8)
                cv2.putText(live_img, "No master loaded", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
            return live_img
        return state.camera.get_frame()
    except Exception as e:
        # Fallback automático a simulador si la cámara se pierde en runtime
        state.use_simulator = True
        state.settings["use_simulator"] = True
        save_config()
        raise HTTPException(status_code=503, detail=f"Camera unavailable, switched to simulator: {e}")

def mjpeg_stream(scale: float = 0.6, quality: int = 70):
    while True:
        try:
            frame = acquire_live_frame()
            if scale and scale > 0 and scale < 1:
                h, w = frame.shape[:2]
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            success, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
            if not success:
                continue
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n")
            time.sleep(0.04)
        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(0.2)

def mjpeg_heatmap_stream(scale: float = 0.6, quality: int = 70):
    while True:
        try:
            heatmap = state.last_frames.get("heatmap")
            if heatmap is None:
                time.sleep(0.1)
                continue
            if scale and scale > 0 and scale < 1:
                h, w = heatmap.shape[:2]
                heatmap = cv2.resize(heatmap, (int(w * scale), int(h * scale)))
            success, encoded = cv2.imencode(".jpg", heatmap, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
            if not success:
                continue
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n")
            time.sleep(0.04)
        except Exception as e:
            print(f"Heatmap stream error: {e}")
            time.sleep(0.2)

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return
    except Exception as e:
        print(f"Config load error: {e}")
        return
    state.settings.update(data.get("settings", {}))
    state.retention_policy.update(data.get("retention_policy", {}))
    state.alarm_rules.update(data.get("alarm_rules", {}))
    state.sensor_config.update(data.get("sensor_config", {}))
    if state.settings.get("start_with_last_job") and data.get("last_job_id"):
        state.job_id = data.get("last_job_id")
        state.active_recipe = data.get("last_recipe", "")
    if "use_simulator" in state.settings:
        state.use_simulator = bool(state.settings.get("use_simulator"))

def save_config():
    data = {
        "settings": state.settings,
        "retention_policy": state.retention_policy,
        "alarm_rules": state.alarm_rules,
        "sensor_config": state.sensor_config,
        "last_job_id": state.job_id,
        "last_recipe": state.active_recipe
    }
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception as e:
        print(f"Config save error: {e}")

load_config()
ensure_db()

class CameraConfig(BaseModel):
    camera_id: int

class CameraSettings(BaseModel):
    exposure: float = None
    gain: float = None

class JobStart(BaseModel):
    job_id: str
    sku: str = ""
    client: str = ""
    recipe: str = ""

class RollStart(BaseModel):
    roll_id: str = ""

class AlarmAck(BaseModel):
    code: str
    clear: bool = False

class RetentionPolicy(BaseModel):
    thumbnails_days: int = 30
    evidence_days: int = 90
    video_days: int = 14

class EvidenceIn(BaseModel):
    kind: str
    uri: str
    defect_id: str = ""
    notes: str = ""

class AppSettings(BaseModel):
    use_simulator: bool = True
    camera_id: int = None
    exposure: float = None
    gain: float = None
    roll_diameter_mm: float = None
    start_with_last_job: bool = None
    core_diameter_mm: float = None
    material_thickness_mm: float = None
    plc_enabled: Optional[bool] = None
    plc_ip: Optional[str] = None
    plc_port: Optional[int] = None
    plc_unit_id: Optional[int] = None
    plc_protocol: Optional[str] = None
    plc_timeout_ms: Optional[int] = None
    plc_tower_red: Optional[str] = None
    plc_tower_yellow: Optional[str] = None
    plc_tower_green: Optional[str] = None
    plc_buzzer: Optional[str] = None
    plc_stop_line: Optional[str] = None
    plc_enabled: bool = None
    plc_ip: str = None
    plc_port: int = None
    plc_unit_id: int = None
    plc_protocol: str = None
    plc_timeout_ms: int = None
    plc_tower_red: str = None
    plc_tower_yellow: str = None
    plc_tower_green: str = None
    plc_buzzer: str = None
    plc_stop_line: str = None

class SensorConfig(BaseModel):
    label_pitch_m: float = 0.0
    cmark_enabled: bool = False
    jitter_tolerance_ms: int = 20
    fallback_encoder: bool = True
    encoder_pitch_m: float = 0.0
    mm_per_tick: float = 0.0
    repeat_mm: float = 0.0

    @validator("label_pitch_m", "encoder_pitch_m", "mm_per_tick", "repeat_mm", pre=True)
    def clamp_non_negative_float(cls, value):
        if value is None:
            return 0.0
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not math.isfinite(number) or number < 0:
            return 0.0
        return number

    @validator("jitter_tolerance_ms", pre=True)
    def clamp_jitter_tolerance(cls, value):
        if value is None:
            return 20
        try:
            number = int(float(value))
        except (TypeError, ValueError):
            return 20
        return max(0, number)

class FrameEnvelope(BaseModel):
    frame_id: str
    ts_utc_ms: int
    web_pos_mm: int
    speed_mpm: float
    lane_id: int
    label_index: Optional[int] = None
    image_uri: str = ""
    exposure_us: int = 0


class RecipeIn(BaseModel):
    name: str
    version: str = "1.0"
    json_blob: dict
    approved_by: Optional[str] = None


class RecipeApprove(BaseModel):
    approved_by: str
    illumination_state: dict = {}

class DefectEvent(BaseModel):
    defect_id: str
    job_id: str
    roll_id: str
    ts_utc_ms: int
    web_pos_mm: int
    lane_id: int
    label_index: Optional[int] = None
    defect_type: str
    severity: str
    score: float
    bbox: list
    crop_uri: str = ""
    frame_uri: str = ""
    master_diff_uri: str = ""
    notes: str = ""

class ColorEvent(BaseModel):
    color_event_id: str
    job_id: str
    roll_id: str
    ts_utc_ms: int
    web_pos_mm: int
    lane_id: int
    roi_id: str
    lab_measured: dict
    lab_target: dict
    delta_e: float
    status: str
    trend_window: dict = {}

class ReportRequest(BaseModel):
    roll_id: str
    format: str = "csv"  # csv or pdf

class DispatchRequest(BaseModel):
    report_id: str
    channel: str  # email, smb, ftp
    destination: str

class WflDispatch(BaseModel):
    roll_id: str
    target: str = ""

def array_to_bytes(img_array: np.ndarray, fmt=".png") -> bytes:
    success, encoded = cv2.imencode(fmt, img_array)
    if not success:
        raise ValueError("Could not encode image")
    return encoded.tobytes()

def build_master_pyramid(img: np.ndarray, levels: int = 3):
    pyramid = [img]
    current = img
    for _ in range(levels - 1):
        current = cv2.pyrDown(current)
        pyramid.append(current)
    return pyramid

def apply_recipe(name: str):
    data = state.recipe_manager.load_recipe(name)
    state.client = data.get("client", "")
    state.job_number = data.get("job_number", "")
    state.recipe_lane_count = int(data.get("lane_count", 1) or 1)
    state.active_recipe = name
    state.sensor_config["repeat_mm"] = float(data.get("repeat_mm", 0.0) or 0.0)
    if data.get("alarm_rules"):
        state.alarm_rules.update(data.get("alarm_rules"))

    # Apply camera settings if hardware is connected
    if not state.use_simulator:
        state.camera.set_settings(exposure=data.get("exposure", -5.0))

    master_file = data.get("master_file")
    if master_file:
        try:
            img = cv2.imread(master_file)
            if img is not None:
                state.master_image = img
                state.master_image_bytes = array_to_bytes(img)
        except Exception as e:
            print(f"Failed to load master from recipe: {e}")
    return data

@app.post("/upload-master")
async def upload_master(file: UploadFile = File(...), dpi: int = 150, page_index: int = 0):
    """Uploads a PDF, converts first page to image, and sets as Master."""
    try:
        contents = await file.read()
        master_hash = hashlib.sha256(contents).hexdigest()
        doc = fitz.open(stream=contents, filetype="pdf")
        if doc.page_count < 1:
            raise HTTPException(status_code=400, detail="PDF has no pages")
        
        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=dpi) # Moderate DPI for performance
        
        # Convert to numpy array (RGB)
        img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n >= 3:
            img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
        else:
             img = cv2.cvtColor(img_data, cv2.COLOR_GRAY2BGR)
             
        state.master_image = img
        state.master_image_bytes = array_to_bytes(img)
        state.master_pyramid = build_master_pyramid(img, levels=3)
        state.master_meta = {
            "page_index": page_index,
            "dpi": dpi,
            "pixel_size_mm": 25.4 / dpi,
            "color_space": "sRGB",
            "master_hash": master_hash
        }
        
        return {"width": pix.width, "height": pix.height, "message": "Master loaded successfully", "master_hash": master_hash}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/master-image")
def get_master_image():
    if state.master_image_bytes is None:
        raise HTTPException(status_code=404, detail="No master image loaded")
    return Response(content=state.master_image_bytes, media_type="image/png")

@app.get("/cameras")
def get_cameras():
    return state.camera.list_cameras()

@app.post("/connect-camera")
def connect_camera(config: CameraConfig):
    try:
        result = state.camera.connect(config.camera_id, fallback_to_virtual=True)
        state.use_simulator = False
        state.settings["use_simulator"] = False
        state.settings["camera_id"] = result["camera_id"]
        save_config()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/camera-settings")
def update_camera_settings(settings: CameraSettings):
    try:
        state.camera.set_settings(exposure=settings.exposure, gain=settings.gain)
        if settings.exposure is not None:
            state.settings["exposure"] = settings.exposure
        if settings.gain is not None:
            state.settings["gain"] = settings.gain
        save_config()
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recipes/{name}/bind-master")
def bind_master_to_recipe(name: str):
    if state.master_image is None:
        raise HTTPException(status_code=400, detail="No master loaded")
    try:
        data = state.recipe_manager.load_recipe(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    master_path = f"recipes/master_{name}.png"
    success = cv2.imwrite(master_path, state.master_image)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save master image")
    data["master_file"] = master_path
    try:
        recipe = Recipe(**data)
        state.recipe_manager.save_recipe(recipe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update recipe: {e}")
    return {"status": "ok", "master_file": master_path}

@app.get("/recipes")
def list_recipes():
    return state.recipe_manager.list_recipes()

@app.post("/save-recipe")
def save_recipe(recipe: Recipe):
    return state.recipe_manager.save_recipe(recipe)

@app.get("/load-recipe/{name}")
def load_recipe(name: str):
    try:
        data = apply_recipe(name)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/recipes/{name}/clone")
def clone_recipe(name: str, new_name: str):
    try:
        return state.recipe_manager.clone_recipe(name, new_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/setup/validate-camera")
def validate_setup_camera():
    """
    Simple check to see if a camera (or virtual) is connected and readable.
    """
    try:
        if state.use_simulator:
            return {"status": "ok", "message": "Simulator active"}

        # Check if connected
        if state.camera.cap is None:
             raise Exception("No camera connected")
        
        # Try to read a frame
        frame = state.camera.get_frame()
        if frame is None:
             raise Exception("Failed to grab frame")
             
        return {"status": "ok", "message": "Camera operational"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/toggle-source")
def toggle_source(use_simulator: bool):
    if not use_simulator:
        if state.camera.cap is None and state.settings.get("camera_id") is not None:
            try:
                state.camera.connect(state.settings["camera_id"])
            except Exception as e:
                state.use_simulator = True
                state.settings["use_simulator"] = True
                save_config()
                return {"use_simulator": True, "error": f"Camera connect failed: {e}"}
        if state.camera.cap is None:
            state.use_simulator = True
            state.settings["use_simulator"] = True
            save_config()
            return {"use_simulator": True, "error": "No camera connected"}
    state.use_simulator = use_simulator
    state.settings["use_simulator"] = use_simulator
    save_config()
    return {"use_simulator": state.use_simulator}

@app.get("/stream/live.mjpg")
def stream_live(scale: float = 0.6, quality: int = 70):
    return StreamingResponse(mjpeg_stream(scale=scale, quality=quality), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/stream/heatmap.mjpg")
def stream_heatmap(scale: float = 0.6, quality: int = 70):
    return StreamingResponse(mjpeg_heatmap_stream(scale=scale, quality=quality), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/job/start")
def start_job(payload: JobStart):
    if state.roll_id:
        if not state.job_id:
            # Stale roll without active job, attempt cleanup
            try:
                end_roll()
            except Exception as e:
                log_event("stale_roll_cleanup", "warning", "Failed to end stale roll, clearing state", {"error": str(e)})
                state.roll_id = ""
                reset_roll_counters()
        else:
            raise HTTPException(status_code=400, detail="Active roll in progress")
    if state.job_id and state.job_id != payload.job_id:
        raise HTTPException(status_code=400, detail="Job already active")
    if not payload.recipe and not state.active_recipe:
        raise HTTPException(status_code=400, detail="Recipe required")
    if payload.recipe:
        try:
            apply_recipe(payload.recipe)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Recipe load failed: {e}")
    state.job_id = payload.job_id
    state.sku = payload.sku
    state.client = payload.client
    state.job_number = payload.job_id
    save_config()
    insert_job(state.job_id, state.active_recipe, payload.sku, "", "running")
    log_event("job_started", "info", "Job started", payload.dict())
    return {"status": "ok", "job_id": state.job_id, "recipe": state.active_recipe}

@app.post("/roll/start")
def start_roll(payload: RollStart):
    if not state.job_id or not state.active_recipe:
        raise HTTPException(status_code=400, detail="Job and recipe required")
    if state.roll_id:
        raise HTTPException(status_code=400, detail="Active roll in progress")
    if payload.roll_id:
        state.roll_id = payload.roll_id
        auto = False
    else:
        state.roll_id = f"ROLL-{state.roll_sequence:04d}"
        state.roll_sequence += 1
        auto = True
    reset_roll_counters()
    insert_roll(state.roll_id, state.job_id)
    log_event("roll_started", "info", "Roll started", {"roll_id": state.roll_id, "auto": auto})
    return {"status": "ok", "roll_id": state.roll_id, "auto": auto}

@app.post("/roll/end")
def end_roll():
    if not state.roll_id:
        raise HTTPException(status_code=400, detail="No active roll")
    duration_sec = int(time.time() - state.roll_started_at) if state.roll_started_at else 0
    avg_deltae = (
        state.counters["deltae_sum"] / state.counters["deltae_count"]
        if state.counters["deltae_count"] > 0 else 0.0
    )
    report = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "job_id": state.job_id,
        "roll_id": state.roll_id,
        "duration_sec": duration_sec,
        "total_frames": state.counters["total_frames"],
        "total_defects": state.counters["total_defects"],
        "avg_deltae": round(avg_deltae, 3),
            "meters_processed": round(state.current_mm / 1000.0, 2)
    }
    try:
        report = persist_roll_report(report)
    except Exception as e:
        log_event("roll_report_error", "error", "Failed to persist roll report", {"error": str(e)})
        report["csv_path"] = ""
        report["pdf_path"] = ""
    state.roll_reports.append(report)
    try:
        close_roll(state.roll_id, report.get("meters_processed", 0), 0.0)
    except Exception as e:
        log_event("roll_close_error", "error", "Failed to close roll in storage", {"error": str(e)})
    log_event("eor", "info", "End of roll", report)
    state.roll_id = ""
    reset_roll_counters()
    return {"status": "ok", "report": report}


@app.post("/job/stop")
def stop_job():
    # If a roll is active, close it first
    closed_report = None
    try:
        if state.roll_id:
            roll_result = end_roll()
            closed_report = roll_result.get("report") if isinstance(roll_result, dict) else None
    except HTTPException as e:
        # If roll is already ended or invalid, just log it
        log_event("stop_job_warning", "warn", f"Could not end roll: {e.detail}", {})
    except Exception as e:
        log_event("stop_job_error", "error", f"Error ending roll: {str(e)}", {})

    if not state.job_id:
        return {"status": "ok", "message": "No active job", "job_id": "", "report": closed_report}
    
    job_id = state.job_id
    state.job_id = ""
    state.active_recipe = ""
    save_config()
    log_event("job_stopped", "info", "Job stopped", {"job_id": job_id})
    return {"status": "ok", "job_id": job_id, "report": closed_report}

@app.get("/line/status")
def line_status():
    return {
        "job_id": state.job_id,
        "roll_id": state.roll_id,
        "active_recipe": state.active_recipe,
        "master_loaded": state.master_image is not None
    }


# ─────────────────────────────────────────────────────
# REST API (9.x spec)
# ─────────────────────────────────────────────────────

@app.post("/api/jobs")
def api_jobs_create(payload: JobStart):
    return start_job(payload)


@app.post("/api/jobs/{job_id}/start")
def api_jobs_start(job_id: str, payload: JobStart):
    if payload.job_id != job_id:
        raise HTTPException(status_code=400, detail="job_id mismatch")
    return start_job(payload)


@app.post("/api/jobs/{job_id}/stop")
def api_jobs_stop(job_id: str):
    if state.job_id != job_id:
        raise HTTPException(status_code=404, detail="Job not active")
    return stop_job()


@app.get("/api/jobs/{job_id}/status")
def api_jobs_status(job_id: str):
    if state.job_id != job_id:
        raise HTTPException(status_code=404, detail="Job not active")
    return {
        "job_id": state.job_id,
        "roll_id": state.roll_id,
        "fps": state.fps,
        "speed_mpm": state.speed_mpm,
        "alarms": list(state.alarms.values())
    }


@app.get("/api/rolls/{roll_id}/defects")
def api_roll_defects(roll_id: str, from_mm: float = 0.0, to_mm: float = 1e9, severity: str = None, type: str = None):
    items = [t for t in state.trace_entries if t.get("roll_id") == roll_id and t.get("type") == "defect"]
    out = []
    for item in items:
        meter = item.get("meter", 0) * 1000.0  # convert m to mm if stored in m
        if meter < from_mm or meter > to_mm:
            continue
        defect = item.get("defect", {})
        if severity and defect.get("severity") != severity:
            continue
        if type and defect.get("label") != type:
            continue
        out.append(item)
    return {"items": out}


@app.get("/api/rolls/{roll_id}/color")
def api_roll_color(roll_id: str, roi_id: str = None, from_mm: float = 0.0, to_mm: float = 1e9):
    # Using stored measurements (no position available here), return latest N filtered by ROI
    measurements = state.color_monitor.measurements[-500:]
    out = []
    for m in measurements:
        if roi_id and m.roi_id != roi_id:
            continue
        out.append(m.dict())
    return {"items": out}


@app.post("/api/recipes")
def api_recipes_create(recipe: RecipeIn):
    # Persist recipe JSON to filesystem
    os.makedirs("recipes", exist_ok=True)
    path = os.path.join("recipes", f"{recipe.name}_{recipe.version}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(recipe.json_blob, fh, indent=2)
    return {"status": "saved", "path": path}


@app.get("/api/recipes")
def api_recipes_list():
    os.makedirs("recipes", exist_ok=True)
    files = [f for f in os.listdir("recipes") if f.lower().endswith(".json")]
    return {"recipes": files}


@app.post("/api/recipes/{recipe_id}/approve")
def api_recipes_approve(recipe_id: str, payload: RecipeApprove):
    # Minimal stub approval log
    log_event("recipe_approved", "info", "Recipe approved", {"recipe_id": recipe_id, "approved_by": payload.approved_by})
    return {"status": "approved", "recipe_id": recipe_id}


@app.post("/api/masters/import")
def api_masters_import(path: str = Body(..., embed=True)):
    # Stub: store path reference
    return {"status": "imported", "path": path}


@app.get("/api/reports/{roll_id}")
def api_reports_roll(roll_id: str):
    report = build_roll_report(roll_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report = persist_roll_report(report)
    return report

@app.get("/events")
def list_events(limit: int = 100):
    return list(state.events)[-limit:]

@app.get("/alarms")
def list_alarms():
    return [a for a in state.alarms.values() if a.get("active")]

@app.post("/alarms/ack")
def ack_alarm(payload: AlarmAck):
    alarm = state.alarms.get(payload.code)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    alarm["acknowledged"] = True
    if payload.clear:
        clear_alarm(payload.code)
    log_event("alarm_ack", "info", "Alarm acknowledged", {"code": payload.code, "clear": payload.clear})
    return {"status": "ok"}

@app.get("/actions")
def list_actions(limit: int = 100):
    return list(state.actions)[-limit:]

@app.post("/actions/mark-segment")
def mark_segment():
    action = record_action(
        "mark_segment",
        "segment",
        "manual",
        {"segment_index": state.segment_index, "meter": round(state.current_meter, 2)}
    )
    log_event("segment_marked", "info", "Segment marked", action)
    return {"status": "ok", "action": action}

@app.get("/retention-policy")
def get_retention_policy():
    return state.retention_policy

@app.post("/retention-policy")
def set_retention_policy(payload: RetentionPolicy):
    state.retention_policy = payload.dict()
    log_event("retention_updated", "info", "Retention policy updated", state.retention_policy)
    save_config()
    return {"status": "ok", "policy": state.retention_policy}

@app.get("/settings")
def get_settings():
    return {
        "settings": state.settings,
        "retention_policy": state.retention_policy
    }

@app.post("/settings")
def update_settings(payload: AppSettings):
    state.settings["use_simulator"] = payload.use_simulator
    if payload.camera_id is not None:
        state.settings["camera_id"] = payload.camera_id
    if payload.exposure is not None:
        state.settings["exposure"] = payload.exposure
    if payload.gain is not None:
        state.settings["gain"] = payload.gain
    if payload.roll_diameter_mm is not None:
        state.settings["roll_diameter_mm"] = payload.roll_diameter_mm
    if payload.core_diameter_mm is not None:
        state.settings["core_diameter_mm"] = payload.core_diameter_mm
    if payload.material_thickness_mm is not None:
        state.settings["material_thickness_mm"] = payload.material_thickness_mm
    if payload.start_with_last_job is not None:
        state.settings["start_with_last_job"] = payload.start_with_last_job
    if payload.plc_enabled is not None:
        state.settings["plc_enabled"] = payload.plc_enabled
    if payload.plc_ip is not None:
        state.settings["plc_ip"] = payload.plc_ip
    if payload.plc_port is not None:
        state.settings["plc_port"] = payload.plc_port
    if payload.plc_unit_id is not None:
        state.settings["plc_unit_id"] = payload.plc_unit_id
    if payload.plc_protocol is not None:
        state.settings["plc_protocol"] = payload.plc_protocol
    if payload.plc_timeout_ms is not None:
        state.settings["plc_timeout_ms"] = payload.plc_timeout_ms
    if payload.plc_tower_red is not None:
        state.settings["plc_tower_red"] = payload.plc_tower_red
    if payload.plc_tower_yellow is not None:
        state.settings["plc_tower_yellow"] = payload.plc_tower_yellow
    if payload.plc_tower_green is not None:
        state.settings["plc_tower_green"] = payload.plc_tower_green
    if payload.plc_buzzer is not None:
        state.settings["plc_buzzer"] = payload.plc_buzzer
    if payload.plc_stop_line is not None:
        state.settings["plc_stop_line"] = payload.plc_stop_line
    state.use_simulator = payload.use_simulator
    save_config()
    return {"status": "ok", "settings": state.settings}

@app.get("/traceability/query")
def query_traceability(
    job_id: str = "",
    roll_id: str = "",
    severity: str = "",
    date_from: str = "",
    date_to: str = ""
):
    items = list(state.trace_entries)
    if job_id:
        items = [i for i in items if i.get("job_id") == job_id]
    if roll_id:
        items = [i for i in items if i.get("roll_id") == roll_id]
    if severity:
        items = [i for i in items if i.get("severity") == severity]
    if date_from:
        items = [i for i in items if i.get("ts", "") >= date_from]
    if date_to:
        items = [i for i in items if i.get("ts", "") <= date_to]
    return items

@app.get("/traceability/roll/{roll_id}/defects")
def list_roll_defects(roll_id: str, limit: int = 500):
    items = [
        {
            "meter": t.get("meter"),
            "segment_index": t.get("segment_index"),
            "severity": t.get("severity"),
            "defect": t.get("defect"),
            "cavity_index": t.get("cavity_index")
        }
        for t in state.trace_entries
        if t.get("roll_id") == roll_id and t.get("type") == "defect"
    ]
    return items[-limit:]

@app.post("/evidence")
def add_evidence(payload: EvidenceIn):
    evidence = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "job_id": state.job_id,
        "roll_id": state.roll_id,
        "kind": payload.kind,
        "uri": payload.uri,
        "defect_id": payload.defect_id,
        "notes": payload.notes
    }
    state.evidence.append(evidence)
    log_event("evidence_added", "info", "Evidence added", evidence)
    return {"status": "ok", "evidence": evidence}

@app.post("/reports/generate")
def generate_report(payload: ReportRequest):
    report = build_roll_report(payload.roll_id)
    if not report:
        raise HTTPException(status_code=404, detail="Roll report not found")
    report_id = report.get("report_id") or str(uuid.uuid4())
    item = {
        "id": report_id,
        "roll_id": payload.roll_id,
        "format": payload.format,
        "created_at": now_iso()
    }
    state.report_queue.append(item)
    log_event("report_generated", "info", "Report generated", item)
    return {"status": "ok", "report_id": report_id}

@app.get("/reports/roll/{roll_id}")
def get_report(roll_id: str, format: str = "json"):
    report = build_roll_report(roll_id)
    if not report:
        raise HTTPException(status_code=404, detail="Roll report not found")
    if format == "csv":
        csv_data = report_to_csv(report)
        return Response(content=csv_data, media_type="text/csv")
    if format == "pdf":
        pdf_bytes = report_to_pdf_bytes(report)
        return Response(content=pdf_bytes, media_type="application/pdf")
    return report

@app.post("/reports/dispatch")
def dispatch_report(payload: DispatchRequest):
    item = {
        "id": payload.report_id,
        "channel": payload.channel,
        "destination": payload.destination,
        "status": "queued",
        "queued_at": now_iso()
    }
    state.report_queue.append(item)
    log_event("report_dispatch_queued", "info", "Report dispatch queued", item)
    return {"status": "ok", "dispatch": item}

@app.get("/reports/queue")
def list_report_queue():
    return list(state.report_queue)

@app.get("/reports/history")
def list_report_history(limit: int = 50):
    return list(state.roll_reports)[-limit:]

@app.get("/system/status")
def system_status():
    return {
        "uptime_sec": int(time.time() - state.uptime_start),
        "use_simulator": state.use_simulator,
        "job_id": state.job_id,
        "roll_id": state.roll_id
    }

@app.get("/logs/export")
def export_logs():
    return {
        "events": list(state.events),
        "alarms": list(state.alarms.values()),
        "actions": list(state.actions)
    }

@app.get("/config/backup")
def backup_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = fh.read()
    except FileNotFoundError:
        data = "{}"
    return Response(content=data, media_type="application/json")

@app.post("/sensors/config")
def update_sensor_config(payload: SensorConfig):
    state.sensor_config = payload.dict()
    save_config()
    log_event("sensor_config", "info", "Sensor config updated", state.sensor_config)
    return {"status": "ok", "sensor_config": state.sensor_config}

@app.get("/sensors/status")
def get_sensor_status():
    return {
        "sensor_config": state.sensor_config,
        "sensor_status": state.sensor_status,
        "sensor_counters": state.sensor_counters,
        "encoder_ticks": state.encoder_ticks,
        "label_index": state.label_index
    }

@app.post("/sensors/label/pulse")
def sensor_label_pulse():
    now_ts = time.time()
    state.sensor_status["last_label_ts"] = now_ts
    state.sensor_counters["label_count"] += 1
    state.label_index += 1
    repeat_mm = state.sensor_config.get("repeat_mm", 0.0)
    if repeat_mm > 0:
        state.current_mm = state.label_index * repeat_mm
    elif state.sensor_config.get("label_pitch_m", 0) > 0:
        state.current_mm += state.sensor_config["label_pitch_m"] * 1000.0
    state.segment_index = int((state.current_mm / 1000.0) // state.segment_length_m)
    log_event("label_pulse", "info", "Label pulse received", {"web_pos_mm": round(state.current_mm, 2)})
    return {"status": "ok"}

@app.post("/sensors/cmark/pulse")
def sensor_cmark_pulse():
    now_ts = time.time()
    last_ts = state.sensor_status.get("last_cmark_ts")
    jitter_tol = state.sensor_config.get("jitter_tolerance_ms", 20)
    if last_ts:
        interval_ms = int((now_ts - last_ts) * 1000)
        state.sensor_status["last_cmark_interval_ms"] = interval_ms
        if interval_ms < jitter_tol:
            raise_alarm("cmark_double", "warning", "Double mark detected", {"interval_ms": interval_ms})
            state.sensor_counters["cmark_double_count"] += 1
        else:
            clear_alarm("cmark_double")
    state.sensor_status["last_cmark_ts"] = now_ts
    state.sensor_counters["cmark_count"] += 1
    log_event("cmark_pulse", "info", "CMark pulse received", {"interval_ms": state.sensor_status.get("last_cmark_interval_ms")})
    return {"status": "ok"}

@app.post("/sensors/encoder/pulse")
def sensor_encoder_pulse():
    now_ts = time.time()
    state.sensor_counters["encoder_count"] += 1
    state.encoder_ticks += 1
    mm_per_tick = state.sensor_config.get("mm_per_tick", 0.0)
    if mm_per_tick > 0:
        state.current_mm += mm_per_tick
    elif state.sensor_config.get("encoder_pitch_m", 0.0) > 0:
        state.current_mm += state.sensor_config["encoder_pitch_m"] * 1000.0
    state.segment_index = int((state.current_mm / 1000.0) // state.segment_length_m)
    state.sensor_status["last_label_ts"] = now_ts
    log_event("encoder_pulse", "info", "Encoder pulse received", {"web_pos_mm": round(state.current_mm, 2)})
    return {"status": "ok"}

@app.get("/wfl/package/{roll_id}")
def get_wfl_package(roll_id: str):
    return build_wfl_package(roll_id)

@app.post("/wfl/enqueue")
def enqueue_wfl(payload: WflDispatch):
    pkg = build_wfl_package(payload.roll_id)
    item = {
        "id": str(uuid.uuid4()),
        "roll_id": payload.roll_id,
        "target": payload.target,
        "status": "queued",
        "queued_at": now_iso(),
        "package": pkg
    }
    state.wfl_queue.append(item)
    log_event("wfl_enqueued", "info", "WFL package queued", {"id": item["id"], "roll_id": payload.roll_id})
    return {"status": "ok", "item": item}

@app.get("/wfl/queue")
def list_wfl_queue():
    return list(state.wfl_queue)

@app.post("/wfl/retry/{item_id}")
def retry_wfl(item_id: str):
    for item in state.wfl_queue:
        if item.get("id") == item_id:
            item["status"] = "queued"
            item["queued_at"] = now_iso()
            log_event("wfl_retry", "warning", "WFL retry queued", {"id": item_id})
            return {"status": "ok", "item": item}
    raise HTTPException(status_code=404, detail="WFL item not found")

# --- Color Module Endpoints ---

@app.post("/color/target")
def set_color_target(target: ColorTarget):
    state.color_monitor.add_target(target)
    state.color_monitor.set_active_target(target.name)
    return {"status": "ok", "active_target": target.name}

@app.get("/color/target")
def get_color_target():
    target = state.color_monitor.get_active_target()
    if not target:
        # Return a dummy if none set, to avoid frontend crash on initial load
        return {}
    return target

@app.get("/color/measurements")
def get_color_measurements():
    return state.color_monitor.measurements

# ─────────────────────────────────────────────────────
# Point 5: Color Calibration & Measurement Endpoints
# ─────────────────────────────────────────────────────

@app.post("/color/calibrate")
def calibrate_color(camera_id: int, white_roi: tuple, black_roi: tuple):
    """
    Calibración: capturar referencias blanco/negro
    """
    try:
        frame = state.camera.get_frame() if not state.use_simulator else state.master_image
        if frame is None:
            raise HTTPException(status_code=400, detail="No frame available")
        
        calibration_id = state.color_monitor.calibrate(frame, white_roi, black_roi, camera_id)
        
        return {
            "status": "calibrated",
            "calibration_id": calibration_id,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Calibration error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/color/measurement/{roi_id}")
def get_color_measurement(roi_id: str):
    """Obtener última medición de color para un ROI"""
    if roi_id not in state.color_monitor.measurement_history:
        return {"error": "No measurements for ROI"}
    
    measurements = list(state.color_monitor.measurement_history[roi_id])
    if not measurements:
        return {"error": "No measurements"}
    
    latest = measurements[-1]
    return {
        "roi_id": roi_id,
        "deltae": latest.delta_e,
        "state": latest.state,
        "lab": {
            "L": latest.l_value,
            "a": latest.a_value,
            "b": latest.b_value
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
    
    return trend

# ─────────────────────────────────────────────────────
# Point 6: Defect Classification Endpoints
# ─────────────────────────────────────────────────────

@app.post("/defects/classify")
def classify_defect(defect_data: dict):
    """Clasificar un defecto detectado"""
    try:
        recipe_thresholds = None
        if state.active_recipe:
            try:
                # Load actual recipe data (active_recipe is a string name)
                recipe_data = state.recipe_manager.load_recipe(state.active_recipe)
                recipe_thresholds = {
                    "critical_area": recipe_data.get("defect_thresholds", {}).get("critical_area", 500),
                    "major_area": recipe_data.get("defect_thresholds", {}).get("major_area", 150),
                    "critical_defect_types": ["missing_print", "register_error"]
                }
            except Exception as recipe_err:
                logger.warning(f"Could not load recipe for classification: {recipe_err}")
                # Use defaults if recipe load fails
                recipe_thresholds = None
        
        classified = state.defect_classifier.classify_defect(defect_data, recipe_thresholds)
        
        return {
            "defect_id": classified.defect_id,
            "type": classified.type.value,
            "severity": classified.severity.value,
            "area": classified.area_px,
            "confidence": classified.confidence_score,
            "rule": classified.rule_applied,
            "timestamp": classified.timestamp.isoformat()
        }
    except Exception as e:
        logger.error(f"Defect classification error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/defects/classification-log")
def get_classification_log():
    """Obtener historial de clasificaciones (auditoría)"""
    return {
        "log": state.defect_classifier.get_classification_log(),
        "summary": state.defect_classifier.get_summary()
    }

# ─────────────────────────────────────────────────────
# Point 7: Alarm Rules & Actions Endpoints
# ─────────────────────────────────────────────────────

@app.post("/alarms/rule")
def add_alarm_rule(rule_data: dict):
    """Agregar nueva regla de alarma"""
    try:
        # Construir objetos de acción
        actions = []
        for action_data in rule_data.get("actions", []):
            action = Action(
                action_type=ActionType[action_data.get("action_type", "LOG_ONLY")],
                duration_ms=action_data.get("duration_ms", 500),
                color=action_data.get("color", "red"),
                plc_address=action_data.get("plc_address"),
                plc_value=action_data.get("plc_value"),
                popup_title=action_data.get("popup_title", ""),
                popup_message=action_data.get("popup_message", ""),
                email_to=action_data.get("email_to", [])
            )
            actions.append(action)
        
        # Crear regla
        rule = AlarmRule(
            rule_id=rule_data.get("rule_id", f"rule_{uuid.uuid4().hex[:8]}"),
            enabled=rule_data.get("enabled", True),
            trigger_type=TriggerType[rule_data.get("trigger_type", "ON_DEFECT")],
            trigger_config=rule_data.get("trigger_config", {}),
            actions=actions,
            cooldown_ms=rule_data.get("cooldown_ms", 2000),
            description=rule_data.get("description", "")
        )
        
        state.alarm_engine.add_rule(rule)
        
        return {
            "status": "rule_added",
            "rule_id": rule.rule_id,
            "enabled": rule.enabled,
            "actions": len(rule.actions)
        }
    except Exception as e:
        logger.error(f"Alarm rule error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/alarms/recent")
def get_recent_alarms(count: int = 10):
    """Obtener últimas N alarmas disparadas"""
    return {
        "alarms": state.alarm_engine.get_recent_alarms(count)
    }

@app.get("/alarms/rules/status")
def get_all_rules_status():
    """Obtener estado de todas las reglas"""
    return state.alarm_engine.get_all_rules_status()

@app.get("/alarms/rules/{rule_id}/status")
def get_rule_status(rule_id: str):
    """Obtener estado de una regla específica"""
    status = state.alarm_engine.get_rule_status(rule_id)
    if not status:
        raise HTTPException(status_code=404, detail="Rule not found")
    return status

@app.post("/alarms/rules/{rule_id}/enable")
def enable_rule(rule_id: str):
    """Habilitar una regla de alarma"""
    success = state.alarm_engine.enable_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "enabled", "rule_id": rule_id}

@app.post("/alarms/rules/{rule_id}/disable")
def disable_rule(rule_id: str):
    """Deshabilitar una regla de alarma"""
    success = state.alarm_engine.disable_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "disabled", "rule_id": rule_id}

@app.get("/alarms/statistics")
def get_alarm_statistics():
    """Estadísticas de alarmas disparadas"""
    return state.alarm_engine.get_alarm_statistics()

# ─────────────────────────────────────────────────────

@app.get("/inspection-frame")
def get_inspection_frame(format: str = "jpg", quality: int = 70, scale: float = 0.6):
    """
    Returns a processed frame.
    """
    if not state.job_id or not state.active_recipe:
        log_event("inspection_start_blocked", "warning", "Job and recipe required", {"job_id": state.job_id, "active_recipe": state.active_recipe})
        raise HTTPException(status_code=400, detail="Job and recipe required")
    if state.master_image is None:
        log_event("inspection_start_blocked", "warning", "Master not loaded", {})
        raise HTTPException(status_code=400, detail="Master not loaded")
    if state.settings.get("camera_id") is not None and state.camera.cap is None and not state.use_simulator:
        try:
            state.camera.connect(state.settings["camera_id"])
        except Exception as e:
            print(f"Camera reconnect error: {e}")
            state.use_simulator = True
            state.settings["use_simulator"] = True
            save_config()
    if state.job_id and not state.roll_id:
        state.roll_id = f"ROLL-{state.roll_sequence:04d}"
        state.roll_sequence += 1
        reset_roll_counters()
        log_event("roll_started", "info", "Roll started (auto)", {"roll_id": state.roll_id, "auto": True})
    now_ts = time.time()

    try:
        active_recipe = state.recipe_manager.load_recipe(state.active_recipe)
    except Exception:
        active_recipe = {}

    # 1. Acquire Image
    try:
        if state.use_simulator:
            live_img = state.master_image.copy()
            live_img = state.simulator.add_defects(live_img, count=random.randint(1, 5))
            # Add slight misalignment for realism
            rows, cols, _ = live_img.shape
            M = np.float32([[1, 0, random.randint(-5, 5)], [0, 1, random.randint(-5, 5)]])
            live_img = cv2.warpAffine(live_img, M, (cols, rows))
        else:
             # Real Camera
             live_img = state.camera.get_frame()
             # Resize if necessary to match master or vice versa? 
             # For MVP assuming similar aspect ratio or letting alignment handle it.
    except Exception as e:
        # Fallback if camera fails
        print(f"Camera error: {e}")
        state.use_simulator = True
        state.settings["use_simulator"] = True
        save_config()
        log_event("camera_fallback", "warning", "Camera error, switched to simulator", {"error": str(e)})
        return {"error": str(e)}

    # 2. Inspect
    tolerances = active_recipe.get("tolerances", {}) if active_recipe else {}
    diff_threshold = int(tolerances.get("diff_threshold", 30))
    min_blob_area = int(tolerances.get("min_blob_area_px", 50))
    max_shift = float(tolerances.get("max_allowed_shift_px", 20))
    allowed_rotation = float(tolerances.get("allowed_rotation_deg", 1.0))
    allowed_stretch_ppm = float(tolerances.get("allowed_stretch_ppm", 500.0))

    aligned, transform = state.inspector.align_images(state.master_image, live_img)
    diff, thresh, heatmap, defects = state.inspector.compare_images(
        state.master_image,
        aligned,
        diff_threshold=diff_threshold,
        min_blob_area=min_blob_area
    )

    # Registration checks
    dx = abs(transform.get("dx", 0.0))
    dy = abs(transform.get("dy", 0.0))
    rot = abs(transform.get("rotation_deg", 0.0))
    scale_x = transform.get("scale_x", 1.0)
    stretch_ppm = abs(scale_x - 1.0) * 1_000_000
    if dx > max_shift or dy > max_shift or rot > allowed_rotation or stretch_ppm > allowed_stretch_ppm:
        state.inspector.last_registration_ok = False

    # Apply ROIs (include/exclude) from recipe if present
    rois = active_recipe.get("inspection_rois") or active_recipe.get("rois") or []
    exclude_rois = active_recipe.get("exclude_rois") or []
    if rois:
        includes = [r for r in rois if r.get("type") == "include" or "type" not in r]
        if includes:
            filtered = []
            for d in defects:
                cx = d.get("x", 0) + d.get("w", 0) / 2
                cy = d.get("y", 0) + d.get("h", 0) / 2
                if any(cx >= r.get("x", 0) and cy >= r.get("y", 0) and cx <= r.get("x", 0) + r.get("w", 0) and cy <= r.get("y", 0) + r.get("h", 0) for r in includes):
                    filtered.append(d)
            defects = filtered
    if exclude_rois:
        filtered = []
        for d in defects:
            cx = d.get("x", 0) + d.get("w", 0) / 2
            cy = d.get("y", 0) + d.get("h", 0) / 2
            if not any(cx >= r.get("x", 0) and cy >= r.get("y", 0) and cx <= r.get("x", 0) + r.get("w", 0) and cy <= r.get("y", 0) + r.get("h", 0) for r in exclude_rois):
                filtered.append(d)
        defects = filtered
    lane_count = max(1, int(state.recipe_lane_count or 1))
    if lane_count > 1 and state.master_image is not None:
        width = state.master_image.shape[1]
        if width > 0:
            for d in defects:
                d["cavity_index"] = min(lane_count, max(1, int((d.get("x", 0) / width) * lane_count) + 1))
    
    # 3. Color Monitoring
    color_rois = active_recipe.get("color_rois") or []
    if color_rois:
        r = color_rois[0]
        x1 = int(r.get("x", 0))
        y1 = int(r.get("y", 0))
        w = int(r.get("w", 0))
        h = int(r.get("h", 0))
        x2 = min(aligned.shape[1], x1 + w)
        y2 = min(aligned.shape[0], y1 + h)
        color_roi = aligned[y1:y2, x1:x2]
    else:
        # For MVP, take a center crop
        h, w, _ = aligned.shape
        cy, cx = h // 2, w // 2
        roi_size = 50
        y1, y2 = max(0, cy-roi_size), min(h, cy+roi_size)
        x1, x2 = max(0, cx-roi_size), min(w, cx+roi_size)
        color_roi = aligned[y1:y2, x1:x2]
    
    # Calculate average RGB
    if color_roi.size > 0:
        avg_rgb = cv2.mean(color_roi)[:3] # Tuple (B, G, R, alpha) -> takes first 3
        # cv2.mean returns scalar per channel. 
        # Note: cv2 is BGR. 
        b, g, r = avg_rgb
        # Convert to Lab
        # Create a single pixel for conversion
        pixel_bgr = np.uint8([[[b, g, r]]])
        pixel_rgb = cv2.cvtColor(pixel_bgr, cv2.COLOR_BGR2RGB)
        
        l, a, b_lab = state.color_monitor.rgb_to_lab(pixel_rgb[0,0])
        
        # Record
        measurement = state.color_monitor.record_measurement(l, a, b_lab)
    else:
        measurement = None

    # Run Diagnostics
    diag_metrics = Diagnostics.calculate_image_quality(live_img)

    # Mock Production Stats
    if state.use_simulator:
        speed_m_min = 150.0 + random.uniform(-5, 5)
    else:
        # Simular encoder cuando se usa cámara real sin encoder físico
        elapsed = time.time() - state.last_frame_ts if state.last_frame_ts else 0.05
        state.last_frame_ts = time.time()
        
        # Velocidad simulada en modo cámara real
        simulated_speed_mpm = state.settings.get("simulated_speed_mpm", 30.0)
        distance_m = (simulated_speed_mpm / 60.0) * elapsed  # metros recorridos
        state.current_mm += distance_m * 1000.0  # convertir a mm
        state.speed_mpm = simulated_speed_mpm
        state.encoder_ticks += int(distance_m * 100)  # 100 ticks por metro
        speed_m_min = simulated_speed_mpm
    
    ts_ms = int(time.time() * 1000)

    # Update counters and meters
    state.counters["total_frames"] += 1
    state.counters["total_defects"] += len(defects)
    if measurement:
        state.counters["deltae_sum"] += measurement.delta_e
        state.counters["deltae_count"] += 1
        target = state.color_monitor.get_active_target()
        status = "OK"
        if measurement.is_critical:
            status = "OOT"
        elif measurement.is_warning:
            status = "WARN"
        color_event = ColorEvent(
            color_event_id=str(uuid.uuid4()),
            job_id=state.job_id,
            roll_id=state.roll_id,
            ts_utc_ms=ts_ms,
            web_pos_mm=int(state.current_mm),
            lane_id=1,
            roi_id="default",
            lab_measured={"L": measurement.l_value, "a": measurement.a_value, "b": measurement.b_value},
            lab_target={"L": target.l_target, "a": target.a_target, "b": target.b_target} if target else {"L": 0, "a": 0, "b": 0},
            delta_e=measurement.delta_e,
            status=status,
            trend_window={}
        )
        color_event_dict = color_event.dict()
        state.color_events.append(color_event_dict)
        insert_color_event(color_event_dict)
    if state.last_frame_ts is not None:
        dt = max(0.0, now_ts - state.last_frame_ts)
        meters_inc = (speed_m_min / 60.0) * dt
        state.current_mm += meters_inc * 1000.0
        if (state.current_mm / 1000.0) // state.segment_length_m > state.segment_index:
            state.segment_index = int((state.current_mm / 1000.0) // state.segment_length_m)
    state.last_frame_ts = now_ts

    # Update roll diameter from length (simple winding model)
    core_d = float(state.settings.get("core_diameter_mm", 76.0) or 76.0)
    thickness = float(state.settings.get("material_thickness_mm", 0.05) or 0.05)
    length_mm = max(0.0, state.current_mm)
    if thickness > 0 and core_d > 0:
        diameter = ((4 * thickness * length_mm / np.pi) + (core_d ** 2)) ** 0.5
        state.settings["roll_diameter_mm"] = round(diameter, 2)

    # Frame envelope
    frame_id = str(uuid.uuid4())
    lane_id = 1
    frame_env = FrameEnvelope(
        frame_id=frame_id,
        ts_utc_ms=ts_ms,
        web_pos_mm=int(state.current_mm),
        speed_mpm=float(speed_m_min),
        lane_id=lane_id,
        label_index=state.label_index,
        image_uri="memory://live",
        exposure_us=int(state.settings.get("exposure", -5.0) * 1000) if state.settings.get("exposure") else 0,
        illumination_state={}
    )
    frame_dict = frame_env.dict()
    state.frame_history.append(frame_dict)
    insert_frame(frame_dict)

    # Alarm rules
    critical_defect = any(d.get("area", 0) >= state.alarm_rules["critical_defect_area"] for d in defects)
    if critical_defect:
        raise_alarm("critical_defect", "critical", "Critical defect detected", {"count": len(defects)})
    else:
        clear_alarm("critical_defect")

    defect_rate_alarm = len(defects) >= state.alarm_rules["defect_rate_per_frame"]
    if defect_rate_alarm:
        raise_alarm("defect_rate", "warning", "High defect rate", {"count": len(defects)})
    else:
        clear_alarm("defect_rate")

    if measurement and (measurement.is_critical or measurement.is_warning):
        severity = "critical" if measurement.is_critical else "warning"
        raise_alarm("deltae_out", severity, "Delta E out of spec", {"delta_e": measurement.delta_e})
    else:
        clear_alarm("deltae_out")

    if not state.inspector.last_registration_ok:
        raise_alarm("registration_lost", "critical", "Registration lost", {"matches": state.inspector.last_match_count})
        defects = []
    else:
        clear_alarm("registration_lost")

    if not diag_metrics or diag_metrics.get("brightness", 0) < state.alarm_rules["brightness_min"] or diag_metrics.get("brightness", 0) > state.alarm_rules["brightness_max"]:
        raise_alarm("sensor_signal_lost", "critical", "Sensor signal lost", {"brightness": diag_metrics.get("brightness", None) if diag_metrics else None})
    else:
        clear_alarm("sensor_signal_lost")

    # Sensor mark logic
    if state.sensor_config.get("cmark_enabled"):
        expected_interval_ms = None
        if state.sensor_config.get("label_pitch_m", 0) > 0 and speed_m_min > 0:
            expected_interval_ms = int((state.sensor_config["label_pitch_m"] / (speed_m_min / 60.0)) * 1000)
        last_cmark_ts = state.sensor_status.get("last_cmark_ts")
        if expected_interval_ms and last_cmark_ts:
            since_ms = int((now_ts - last_cmark_ts) * 1000)
            if since_ms > expected_interval_ms * 2:
                raise_alarm("cmark_missing", "warning", "CMark missing", {"since_ms": since_ms})
                last_missing = state.sensor_status.get("last_cmark_missing_ts")
                if last_missing is None or now_ts - last_missing > (expected_interval_ms / 1000.0):
                    state.sensor_counters["cmark_missing_count"] += 1
                    state.sensor_status["last_cmark_missing_ts"] = now_ts
                if state.sensor_config.get("fallback_encoder"):
                    log_event("cmark_fallback", "warning", "Fallback to encoder", {"since_ms": since_ms})
            else:
                clear_alarm("cmark_missing")
            interval_ms = state.sensor_status.get("last_cmark_interval_ms")
            if interval_ms and abs(interval_ms - expected_interval_ms) > state.sensor_config.get("jitter_tolerance_ms", 20):
                raise_alarm("cmark_jitter", "warning", "CMark jitter detected", {"interval_ms": interval_ms})
            else:
                clear_alarm("cmark_jitter")

    # Traceability entries
    for d in defects:
        area = d.get("area", 0)
        rules = active_recipe.get("defect_rules", {})
        crit_area = rules.get("critical_area_px", state.alarm_rules["critical_defect_area"])
        major_area = rules.get("major_area_px", 200)
        if area >= crit_area:
            severity = "critical"
        elif area >= major_area:
            severity = "major"
        else:
            severity = "minor"
        lane_count = max(1, int(state.recipe_lane_count or 1))
        cavity_index = None
        if lane_count > 1 and state.master_image is not None:
            width = state.master_image.shape[1]
            if width > 0:
                cavity_index = min(lane_count, max(1, int((d.get("x", 0) / width) * lane_count) + 1))
        entry = {
            "id": str(uuid.uuid4()),
            "ts": now_iso(),
            "job_id": state.job_id,
            "roll_id": state.roll_id,
            "segment_index": state.segment_index,
            "meter": round(state.current_mm / 1000.0, 2),
            "severity": severity,
            "type": "defect",
            "defect": d,
            "cavity_index": cavity_index
        }
        state.trace_entries.append(entry)

        crop_uri = ""
        if active_recipe.get("store_full_frame_on_defect") or defects:
            try:
                os.makedirs("evidence", exist_ok=True)
                x, y, w, h = d.get("x", 0), d.get("y", 0), d.get("w", 0), d.get("h", 0)
                crop = live_img[y:y + h, x:x + w]
                crop_path = f"evidence/defect_{frame_id}_{d.get('x',0)}_{d.get('y',0)}.png"
                if crop.size > 0:
                    cv2.imwrite(crop_path, crop)
                    crop_uri = crop_path
            except Exception as e:
                print(f"Crop save failed: {e}")

        defect_event = DefectEvent(
            defect_id=str(uuid.uuid4()),
            job_id=state.job_id,
            roll_id=state.roll_id,
            ts_utc_ms=ts_ms,
            web_pos_mm=int(state.current_mm),
            lane_id=cavity_index or 1,
            label_index=state.label_index,
            defect_type=rules.get("default_type", "OTHER"),
            severity="CRITICAL" if severity == "critical" else "MAJOR" if severity == "major" else "MINOR",
            score=1.0,
            bbox=[d.get("x", 0), d.get("y", 0), d.get("w", 0), d.get("h", 0)],
            crop_uri=crop_uri,
            frame_uri="memory://live",
            master_diff_uri="",
            notes=""
        )
        state.defect_events.append(defect_event.dict())
        insert_defect(defect_event.dict())
    
    # Store last frames for streaming
    state.last_frames["live"] = live_img
    state.last_frames["aligned"] = aligned
    state.last_frames["heatmap"] = heatmap
    state.last_frames["master"] = state.master_image

    # Encode images for display
    def encode_b64(img):
        img_out = img
        if scale and scale > 0 and scale < 1:
            h, w = img.shape[:2]
            img_out = cv2.resize(img, (int(w * scale), int(h * scale)))
        fmt = ".jpg" if format.lower() in ["jpg", "jpeg"] else ".png"
        if fmt == ".jpg":
            success, encoded = cv2.imencode(fmt, img_out, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        else:
            success, encoded = cv2.imencode(fmt, img_out)
        if not success:
            raise ValueError("Could not encode image")
        return base64.b64encode(encoded.tobytes()).decode("utf-8")

    return {
        "defects": defects,
        "live_image": encode_b64(live_img),
        "aligned_image": encode_b64(aligned),
        "heatmap_image": encode_b64(heatmap),
        "master_image": encode_b64(state.master_image), # Return master to ensure sync
        "frame_format": format,
        "defect_count": len(defects),
        "source": "simulator" if state.use_simulator else "camera",
        "color_measurement": measurement.dict() if measurement else None,
        "diagnostics": diag_metrics,
        "stats": {
            "speed_m_min": speed_m_min,
            "yield_pct": 98.5, 
            "defect_count": len(defects),
            "meters_processed": round(state.current_mm / 1000.0, 2),
            "web_pos_mm": round(state.current_mm, 2),
            "encoder_ticks": state.encoder_ticks,
            "label_index": state.label_index,
            "roll_diameter_mm": state.settings.get("roll_diameter_mm"),
            "registration_ok": state.inspector.last_registration_ok
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
