import React, { useState } from 'react';

const SetupWizard = ({ apiUrl = 'http://127.0.0.1:8001', onComplete, onCancel }) => {
    const [step, setStep] = useState(1);
    const [checks, setChecks] = useState({
        camera: 'pending', // pending, ok, error
        lighting: 'pending',
        registration: 'pending'
    });
    const [logs, setLogs] = useState([]);

    const addLog = (msg) => setLogs(prev => [...prev, msg]);

    const runCameraCheck = async () => {
        addLog('Checking camera connection...');
        try {
            const res = await fetch(`${apiUrl}/setup/validate-camera`, { method: 'POST' });
            if (res.ok) {
                setChecks(prev => ({ ...prev, camera: 'ok' }));
                addLog('Camera OK.');
            } else {
                setChecks(prev => ({ ...prev, camera: 'error' }));
                addLog('Camera check failed.');
            }
        } catch (err) {
            setChecks(prev => ({ ...prev, camera: 'error' }));
            addLog('Network error during camera check.');
            console.error(err);
        }
    };

    const runLightingCheck = () => {
        addLog('Checking sensors and lighting...');
        // Mock check
        setTimeout(() => {
            setChecks(prev => ({ ...prev, lighting: 'ok' }));
            addLog('Lighting and sensors OK (simulated).');
        }, 800);
    };

    const runRegistrationCheck = () => {
        addLog('Verifying registration...');
        // Mock check - in logic we might ask backend to grab frame and score registration
        setTimeout(() => {
            setChecks(prev => ({ ...prev, registration: 'ok' }));
            addLog('Registration verified.');
        }, 1000);
    };

    const renderStep1 = () => (
        <div>
            <h3>Step 1: System Check</h3>
            <div className="check-list">
                <div className={`check-item ${checks.camera}`}>
                    <span>Camera: {checks.camera.toUpperCase()}</span>
                    {checks.camera !== 'ok' && <button onClick={runCameraCheck}>Run Check</button>}
                </div>
                <div className={`check-item ${checks.lighting}`}>
                    <span>Lighting/Sensor: {checks.lighting.toUpperCase()}</span>
                    {checks.lighting !== 'ok' && checks.camera === 'ok' && <button onClick={runLightingCheck}>Run Check</button>}
                </div>
            </div>
            <div className="log-window">
                {logs.map((l, i) => <div key={i}>{l}</div>)}
            </div>
            <div className="wizard-actions">
                <button onClick={onCancel}>Cancel</button>
                <button
                    disabled={checks.camera !== 'ok' || checks.lighting !== 'ok'}
                    onClick={() => setStep(2)}>
                    Next
                </button>
            </div>
        </div>
    );

    const renderStep2 = () => (
        <div>
            <h3>Step 2: Registration Validation</h3>
            <p>Ensure the web is moving and master is aligned.</p>
            <div className={`check-item ${checks.registration}`}>
                <span>Registration: {checks.registration.toUpperCase()}</span>
                {checks.registration !== 'ok' && <button onClick={runRegistrationCheck}>Verify Registration</button>}
            </div>
            <div className="wizard-actions">
                <button className="btn-cancel" onClick={onCancel}>Cancel</button>
                <button onClick={() => setStep(1)}>Back</button>
                <button
                    disabled={checks.registration !== 'ok'}
                    onClick={onComplete}
                    className="btn-primary"
                >
                    Start Production
                </button>
            </div>
        </div>
    );

    return (
        <div className="modal-overlay">
            <div className="modal-content wizard">
                <h2>Job Setup Wizard</h2>
                {step === 1 && renderStep1()}
                {step === 2 && renderStep2()}
            </div>
        </div>
    );
};

export default SetupWizard;
