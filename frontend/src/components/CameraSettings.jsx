import React, { useState, useEffect } from 'react';

const CameraSettings = ({
    apiUrl = 'http://127.0.0.1:8001',
    onSettingsChange,
    cameraId,
    setCameraId,
    useSim,
    setUseSim,
    exposure,
    setExposure
}) => {
    const [cameras, setCameras] = useState([]);
    const [status, setStatus] = useState('idle');

    useEffect(() => {
        fetch(`${apiUrl}/cameras`)
            .then(res => res.json())
            .then(data => {
                setCameras(data);
                if (data.length > 0 && !cameraId) {
                    setCameraId(String(data[0].id));
                }
            })
            .catch(err => console.error('Failed to load cameras', err));
    }, [apiUrl, cameraId, setCameraId]);

    const handleConnect = async (id) => {
        if (!id) return;
        setCameraId(id);
        try {
            setStatus('connecting');
            const res = await fetch(`${apiUrl}/connect-camera`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_id: parseInt(id) })
            });
            if (!res.ok) {
                throw new Error('Connect failed');
            }
            setUseSim(false);
            setStatus('connected');
            onSettingsChange(false);
        } catch (err) {
            console.error(err);
            setStatus('error');
        }
    };

    const handleToggleSim = async (val) => {
        setUseSim(val);
        const res = await fetch(`${apiUrl}/toggle-source?use_simulator=${val}`, { method: 'POST' });
        const data = await res.json().catch(() => ({}));
        if (typeof data.use_simulator === 'boolean' && data.use_simulator !== val) {
            setUseSim(data.use_simulator);
        }
        setStatus(val ? 'simulator' : status);
        onSettingsChange(val);
    };

    const handleExposure = async (e) => {
        const val = parseFloat(e.target.value);
        setExposure(val);
        await fetch(`${apiUrl}/camera-settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exposure: val })
        });
    };

    return (
        <div className="card settings-panel">
            <h3>Camera</h3>

            <div className="setting-group">
                <label>Source Mode:</label>
                <div className="toggle-row">
                    <button
                        className={useSim ? 'btn-toggle active' : 'btn-toggle'}
                        onClick={() => handleToggleSim(true)}>
                        Simulator
                    </button>
                    <button
                        className={!useSim ? 'btn-toggle active' : 'btn-toggle'}
                        onClick={() => handleConnect(cameraId)}>
                        Camera
                    </button>
                </div>
            </div>

            <div className="status-row">
                <span className="label">Status</span>
                <span className={`pill ${status === 'connected' ? 'good' : status === 'error' ? 'warn' : 'neutral'}`}>
                    {status.toUpperCase()}
                </span>
            </div>

            {!useSim && (
                <>
                    <div className="setting-group">
                        <label>Device:</label>
                        <select onChange={(e) => setCameraId(e.target.value)} value={cameraId}>
                            {cameras.map(cam => (
                                <option key={cam.id} value={cam.id}>{cam.name}</option>
                            ))}
                            {cameras.length === 0 && <option>No cameras found</option>}
                        </select>
                        <button className="btn-secondary" onClick={() => handleConnect(cameraId)}>Connect</button>
                    </div>

                    <div className="setting-group">
                        <label>Exposure ({exposure}):</label>
                        <input
                            type="range"
                            min="-13" max="0" step="1"
                            value={exposure}
                            onChange={handleExposure}
                        />
                    </div>
                </>
            )}
        </div>
    );
};

export default CameraSettings;
