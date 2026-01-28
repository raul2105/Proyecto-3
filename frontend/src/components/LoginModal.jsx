import React, { useState } from 'react';

const LoginModal = ({ onLogin, apiUrl = 'http://127.0.0.1:8001' }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);

    const [loading, setLoading] = useState(false);

    const handleLogin = async () => {
        setLoading(true);
        setError(null);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 sec timeout

        try {
            console.log('Attempting login...');
            const res = await fetch(`${apiUrl}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            console.log('Login response:', res.status);
            if (res.ok) {
                const data = await res.json();
                onLogin(data);
            } else {
                const errData = await res.json().catch(() => ({}));
                setError(errData.detail || 'Invalid credentials');
            }
        } catch (err) {
            console.error('Login Error:', err);
            if (err.name === 'AbortError') {
                setError('Login timed out. Server unresponsive.');
            } else {
                setError('Connection failed. Is backend running?');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content login-modal">
                <h2>Operator Login</h2>
                {error && <div className="error-msg">{error}</div>}

                <div className="form-group">
                    <label>Username</label>
                    <input value={username} onChange={e => setUsername(e.target.value)} />
                </div>
                <div className="form-group">
                    <label>Password</label>
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
                </div>

                <button className="btn-primary" onClick={handleLogin} disabled={loading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>
            </div>
        </div>
    );
};

export default LoginModal;
