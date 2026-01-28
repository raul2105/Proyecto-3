import os
import sqlite3
import json
from datetime import datetime

DB_PATH = "data/inspection.db"

def _ensure_column(conn, table: str, column: str, column_def: str):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    columns = {row[1] for row in cur.fetchall()}
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_def}")
        conn.commit()

def ensure_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            recipe_id TEXT,
            product_code TEXT,
            created_at TEXT,
            operator_id TEXT,
            status TEXT
        )
    """)
    _ensure_column(conn, "jobs", "recipe_id", "TEXT")
    _ensure_column(conn, "jobs", "product_code", "TEXT")
    _ensure_column(conn, "jobs", "created_at", "TEXT")
    _ensure_column(conn, "jobs", "operator_id", "TEXT")
    _ensure_column(conn, "jobs", "status", "TEXT")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rolls (
            roll_id TEXT PRIMARY KEY,
            job_id TEXT,
            start_ts TEXT,
            end_ts TEXT,
            length_m REAL,
            notes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS defects (
            defect_id TEXT PRIMARY KEY,
            roll_id TEXT,
            ts INTEGER,
            web_pos_mm REAL,
            lane_id INTEGER,
            label_index INTEGER,
            type TEXT,
            severity TEXT,
            score REAL,
            bbox_json TEXT,
            crop_uri TEXT,
            frame_uri TEXT,
            meta_json TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS color_events (
            color_event_id TEXT PRIMARY KEY,
            roll_id TEXT,
            ts INTEGER,
            web_pos_mm REAL,
            lane_id INTEGER,
            roi_id TEXT,
            L REAL,
            a REAL,
            b REAL,
            delta_e REAL,
            status TEXT,
            meta_json TEXT
        )
    """)
    _ensure_column(conn, "color_events", "ts", "INTEGER")
    _ensure_column(conn, "color_events", "web_pos_mm", "REAL")
    _ensure_column(conn, "color_events", "lane_id", "INTEGER")
    _ensure_column(conn, "color_events", "roi_id", "TEXT")
    _ensure_column(conn, "color_events", "L", "REAL")
    _ensure_column(conn, "color_events", "a", "REAL")
    _ensure_column(conn, "color_events", "b", "REAL")
    _ensure_column(conn, "color_events", "delta_e", "REAL")
    _ensure_column(conn, "color_events", "status", "TEXT")
    _ensure_column(conn, "color_events", "meta_json", "TEXT")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id TEXT PRIMARY KEY,
            name TEXT,
            version TEXT,
            json_blob TEXT,
            created_at TEXT,
            approved_by TEXT,
            approved_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS masters (
            master_id TEXT PRIMARY KEY,
            recipe_id TEXT,
            pdf_uri TEXT,
            render_dpi INTEGER,
            hash TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id TEXT PRIMARY KEY,
            ts TEXT,
            user_id TEXT,
            action TEXT,
            entity TEXT,
            entity_id TEXT,
            before_json TEXT,
            after_json TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS frames (
            frame_id TEXT PRIMARY KEY,
            ts_utc_ms INTEGER,
            web_pos_mm REAL,
            speed_mpm REAL,
            lane_id INTEGER,
            label_index INTEGER,
            image_uri TEXT,
            exposure_us INTEGER
        )
    """)
    conn.commit()
    conn.close()

def _connect():
    return sqlite3.connect(DB_PATH)

def insert_job(job_id: str, recipe_id: str, product_code: str = "", operator_id: str = "", status: str = "running"):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO jobs (job_id, recipe_id, product_code, created_at, operator_id, status) VALUES (?,?,?,?,?,?)",
        (job_id, recipe_id, product_code, datetime.utcnow().isoformat() + "Z", operator_id, status)
    )
    conn.commit()
    conn.close()

def insert_roll(roll_id: str, job_id: str, notes: str = ""):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO rolls (roll_id, job_id, start_ts, end_ts, length_m, notes) VALUES (?,?,?,NULL,0,?)",
        (roll_id, job_id, datetime.utcnow().isoformat() + "Z", notes)
    )
    conn.commit()
    conn.close()

def close_roll(roll_id: str, length_m: float, yield_pct: float = 0.0):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "UPDATE rolls SET end_ts=?, length_m=? WHERE roll_id=?",
        (datetime.utcnow().isoformat() + "Z", length_m, roll_id)
    )
    conn.commit()
    conn.close()

def insert_frame(frame: dict):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO frames (frame_id, ts_utc_ms, web_pos_mm, speed_mpm, lane_id, label_index, image_uri, exposure_us) VALUES (?,?,?,?,?,?,?,?)",
        (
            frame.get("frame_id"),
            frame.get("ts_utc_ms"),
            frame.get("web_pos_mm"),
            frame.get("speed_mpm"),
            frame.get("lane_id"),
            frame.get("label_index"),
            frame.get("image_uri"),
            frame.get("exposure_us")
        )
    )
    conn.commit()
    conn.close()

def insert_defect(defect: dict):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO defects (defect_id, roll_id, ts, web_pos_mm, lane_id, label_index, type, severity, score, bbox_json, crop_uri, frame_uri, meta_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            defect.get("defect_id"),
            defect.get("roll_id"),
            defect.get("ts"),
            defect.get("web_pos_mm"),
            defect.get("lane_id"),
            defect.get("label_index"),
            defect.get("type"),
            defect.get("severity"),
            defect.get("score"),
            json.dumps(defect.get("bbox")),
            defect.get("crop_uri"),
            defect.get("frame_uri"),
            json.dumps(defect.get("meta", {}))
        )
    )
    conn.commit()
    conn.close()

def insert_color_event(color_event: dict):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO color_events (color_event_id, roll_id, ts, web_pos_mm, lane_id, roi_id, L, a, b, delta_e, status, meta_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            color_event.get("color_event_id"),
            color_event.get("roll_id"),
            color_event.get("ts"),
            color_event.get("web_pos_mm"),
            color_event.get("lane_id"),
            color_event.get("roi_id"),
            color_event.get("L"),
            color_event.get("a"),
            color_event.get("b"),
            color_event.get("delta_e"),
            color_event.get("status"),
            json.dumps(color_event.get("meta", {}))
        )
    )
    conn.commit()
    conn.close()
