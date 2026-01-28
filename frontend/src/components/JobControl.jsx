import React, { useState, useEffect } from 'react';

const JobControl = ({ apiUrl = 'http://127.0.0.1:8001', activeRecipe = '' }) => {
    const [jobStatus, setJobStatus] = useState({
        job_id: '',
        roll_id: '',
        active_recipe: '',
        master_loaded: false
    });
    const [newJobId, setNewJobId] = useState('');
    const [newSku, setNewSku] = useState('');
    const [newClient, setNewClient] = useState('');
    const [newRecipe, setNewRecipe] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadJobStatus();
        const interval = setInterval(loadJobStatus, 3000);
        return () => clearInterval(interval);
    }, [apiUrl]);

    const loadJobStatus = async () => {
        try {
            const res = await fetch(`${apiUrl}/line/status`);
            if (res.ok) {
                const data = await res.json();
                setJobStatus(data);
                return data;
            }
        } catch (error) {
            console.error('Failed to load job status:', error);
        }
        return null;
    };

    const getEffectiveRecipe = () => newRecipe.trim() || jobStatus.active_recipe || activeRecipe || '';

    const handleStartJob = async () => {
        if (!newJobId.trim()) {
            alert('Job ID is required');
            return;
        }

        const status = await loadJobStatus();
        if (status?.job_id) {
            alert('A job is already active. Stop it before starting a new one.');
            return;
        }
        const effectiveRecipe = getEffectiveRecipe();
        if (!effectiveRecipe) {
            alert('Recipe is required. Load or type a recipe before starting the job.');
            return;
        }
        if (status?.roll_id) {
            const confirmEnd = window.confirm('There is an active roll. End it before starting a new job?');
            if (!confirmEnd) return;
            const endRes = await fetch(`${apiUrl}/roll/end`, { method: 'POST' });
            if (!endRes.ok) {
                const endErr = await endRes.json().catch(() => ({}));
                alert(`Error: ${endErr.detail || endErr.error || 'Failed to end roll'}`);
                return;
            }
            await loadJobStatus();
        }

        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/job/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: newJobId,
                    sku: newSku,
                    client: newClient,
                    recipe: effectiveRecipe
                })
            });

            if (res.ok) {
                const data = await res.json();
                alert(`Job started: ${data.job_id}`);
                setNewJobId('');
                setNewSku('');
                setNewClient('');
                setNewRecipe('');
                loadJobStatus();
                return true;
            } else {
                const error = await res.json().catch(() => ({}));
                alert(`Error: ${error.detail || error.error || error.message || 'Failed to start job'}`);
            }
        } catch (error) {
            console.error('Error starting job:', error);
            alert('Error starting job');
        } finally {
            setLoading(false);
        }
        return false;
    };

    const handleStartRoll = async () => {
        const status = await loadJobStatus();
        if (!status?.job_id) {
            alert('No active job. Start a job first.');
            return;
        }
        const effectiveRecipe = getEffectiveRecipe();
        if (!status?.active_recipe && !effectiveRecipe) {
            alert('Recipe is required. Load or select a recipe before starting a roll.');
            return;
        }
        if (status?.roll_id) {
            alert('Active roll in progress. End current roll first.');
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/roll/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ roll_id: '' })
            });

            if (res.ok) {
                const data = await res.json();
                alert(`Roll started: ${data.roll_id}`);
                loadJobStatus();
            } else {
                const error = await res.json().catch(() => ({}));
                alert(`Error: ${error.detail || error.error || error.message || 'Failed to start roll'}`);
            }
        } catch (error) {
            console.error('Error starting roll:', error);
            alert('Error starting roll');
        } finally {
            setLoading(false);
        }
    };

    const handleStartJobAndRoll = async () => {
        const started = await handleStartJob();
        if (!started) return;
        await handleStartRoll();
    };

    const handleEndRoll = async () => {
        if (!jobStatus.roll_id) {
            alert('No active roll');
            return;
        }

        if (!window.confirm('End current roll and generate report?')) {
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/roll/end`, {
                method: 'POST'
            });
            
            if (res.ok) {
                const data = await res.json();
                alert('Roll ended successfully');
                console.log('Roll report:', data.report);
                loadJobStatus();
            } else {
                const error = await res.json().catch(() => ({}));
                alert(`Error: ${error.detail || error.error || error.message || 'Failed to end roll'}`);
            }
        } catch (error) {
            console.error('Error ending roll:', error);
            alert('Error ending roll');
        } finally {
            setLoading(false);
        }
    };

    const handleStopJob = async () => {
        if (!jobStatus.job_id && !jobStatus.roll_id) {
            alert('No active job or roll');
            return;
        }

        if (!window.confirm('Stop current job? This will end any active roll and generate final reports.')) {
            return;
        }

        setLoading(true);
        try {
            const res = await fetch(`${apiUrl}/job/stop`, {
                method: 'POST'
            });
            
            if (res.ok) {
                const data = await res.json();
                alert('Job stopped successfully');
                console.log('Job stopped:', data);
                loadJobStatus();
            } else {
                const error = await res.json().catch(() => ({}));
                alert(`Error: ${error.detail || error.error || error.message || 'Failed to stop job'}`);
            }
        } catch (error) {
            console.error('Error stopping job:', error);
            alert('Error stopping job');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="job-control-container">
            <div className="card">
                <h3>Current Job Status</h3>
                <div className="status-grid">
                    <div className="status-item">
                        <span className="label">Job ID:</span>
                        <span className="value">{jobStatus.job_id || '--'}</span>
                    </div>
                    <div className="status-item">
                        <span className="label">Roll ID:</span>
                        <span className="value">{jobStatus.roll_id || '--'}</span>
                    </div>
                    <div className="status-item">
                        <span className="label">Recipe:</span>
                        <span className="value">{jobStatus.active_recipe || '--'}</span>
                    </div>
                    <div className="status-item">
                        <span className="label">Master:</span>
                        <span className={`pill ${jobStatus.master_loaded ? 'good' : 'neutral'}`}>
                            {jobStatus.master_loaded ? 'LOADED' : 'NOT LOADED'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="card">
                <h3>Start New Job</h3>
                <div className="form-group">
                    <label>Job ID *</label>
                    <input
                        type="text"
                        value={newJobId}
                        onChange={(e) => setNewJobId(e.target.value)}
                        placeholder="e.g., JOB-001"
                        disabled={loading || jobStatus.job_id}
                    />
                </div>
                <div className="form-group">
                    <label>SKU / Product Code</label>
                    <input
                        type="text"
                        value={newSku}
                        onChange={(e) => setNewSku(e.target.value)}
                        placeholder="e.g., PROD-12345"
                        disabled={loading || jobStatus.job_id}
                    />
                </div>
                <div className="form-group">
                    <label>Client</label>
                    <input
                        type="text"
                        value={newClient}
                        onChange={(e) => setNewClient(e.target.value)}
                        placeholder="e.g., Acme Corp"
                        disabled={loading || jobStatus.job_id}
                    />
                </div>
                <div className="form-group">
                    <label>Recipe (Optional)</label>
                    <input
                        type="text"
                        value={newRecipe}
                        onChange={(e) => setNewRecipe(e.target.value)}
                        placeholder="e.g., Test"
                        disabled={loading || jobStatus.job_id}
                    />
                </div>
                <div className="button-group">
                    <button
                        className="btn-start"
                        onClick={handleStartJobAndRoll}
                        disabled={loading || jobStatus.job_id}
                    >
                        {loading ? 'Starting...' : 'Start Job + Roll'}
                    </button>
                    <button
                        className="btn-secondary"
                        onClick={handleStartJob}
                        disabled={loading || jobStatus.job_id}
                    >
                        Start Job Only
                    </button>
                </div>
                <p className="help-text">
                    Tip: If a recipe is already loaded, you can leave the recipe field blank.
                </p>
            </div>

            <div className="card">
                <h3>Roll Control</h3>
                <div className="button-group">
                    <button
                        className="btn-primary"
                        onClick={handleStartRoll}
                        disabled={loading || !jobStatus.job_id || jobStatus.roll_id || !getEffectiveRecipe()}
                    >
                        Start Roll
                    </button>
                    <button
                        className="btn-secondary"
                        onClick={handleEndRoll}
                        disabled={loading || !jobStatus.roll_id}
                    >
                        End Roll
                    </button>
                </div>
            </div>

            <div className="card">
                <h3>Job Actions</h3>
                <button
                    className="btn-stop-job"
                    onClick={handleStopJob}
                    disabled={loading || (!jobStatus.job_id && !jobStatus.roll_id)}
                >
                    {loading ? 'Stopping...' : 'Stop Job'}
                </button>
                <p className="help-text">
                    This will end any active roll and stop the current job, generating final reports.
                </p>
            </div>
        </div>
    );
};

export default JobControl;
