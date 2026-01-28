import React from 'react';

const SensorPanel = ({ sensorStatus }) => {
    if (!sensorStatus) {
        return (
            <div className="card">
                <h3>Sensors</h3>
                <p className="muted">No sensor data yet.</p>
            </div>
        );
    }

    const { sensor_config, sensor_status, sensor_counters } = sensorStatus;

    return (
        <div className="card">
            <h3>Sensors</h3>
            <div className="sensor-grid">
                <div>
                    <div className="label">Label Pitch (m)</div>
                    <div>{sensor_config?.label_pitch_m || 0}</div>
                </div>
                <div>
                    <div className="label">CMark Enabled</div>
                    <div>{sensor_config?.cmark_enabled ? 'Yes' : 'No'}</div>
                </div>
                <div>
                    <div className="label">Last Label</div>
                    <div>{sensor_status?.last_label_ts ? 'OK' : '---'}</div>
                </div>
                <div>
                    <div className="label">Last CMark</div>
                    <div>{sensor_status?.last_cmark_ts ? 'OK' : '---'}</div>
                </div>
                <div>
                    <div className="label">CMark Interval (ms)</div>
                    <div>{sensor_status?.last_cmark_interval_ms || 0}</div>
                </div>
                <div>
                    <div className="label">Jitter Tol (ms)</div>
                    <div>{sensor_config?.jitter_tolerance_ms || 0}</div>
                </div>
            </div>
            <div className="sensor-counters">
                <div className="pill neutral">Labels: {sensor_counters?.label_count || 0}</div>
                <div className="pill neutral">CMarks: {sensor_counters?.cmark_count || 0}</div>
                <div className="pill neutral">Encoder: {sensor_counters?.encoder_count || 0}</div>
                <div className="pill neutral">Ticks: {sensorStatus?.encoder_ticks || 0}</div>
                <div className="pill neutral">Label Index: {sensorStatus?.label_index || 0}</div>
                <div className="pill warn">Missing: {sensor_counters?.cmark_missing_count || 0}</div>
                <div className="pill warn">Double: {sensor_counters?.cmark_double_count || 0}</div>
            </div>
        </div>
    );
};

export default SensorPanel;
