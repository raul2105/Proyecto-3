import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

const ColorDashboard = ({ currentMeasurement, history, target }) => {
    const safeHistory = Array.isArray(history) ? history : [];

    // Format data for chart
    const data = safeHistory.map(m => ({
        time: new Date(m.timestamp).toLocaleTimeString(),
        deltaE: m.delta_e,
        l: m.l_value,
        a: m.a_value || 0, // Fallback if missing
        b: m.b_value || 0
    }));

    if (!target) return <div>Loading target...</div>;

    const isAlarm = currentMeasurement?.is_critical;
    const isWarning = currentMeasurement?.is_warning;

    const indicatorColor = isAlarm ? 'var(--bad)' : (isWarning ? 'var(--warn)' : 'var(--good)');
    const indicatorText = isAlarm ? 'CRITICAL' : (isWarning ? 'WARNING' : 'OK');

    return (
        <div className="color-dashboard card">
            <h2>Color Monitor</h2>

            <div className="metrics-panel">
                <div className="metric-box" style={{ borderColor: indicatorColor }}>
                    <h3 style={{ margin: 0, color: indicatorColor }}>{indicatorText}</h3>
                    <div className="metric-value">
                        Delta E: {currentMeasurement?.delta_e?.toFixed(2) || '0.00'}
                    </div>
                </div>

                <div className="target-info">
                    <h4>Target: {target.name}</h4>
                    <div>L: {target.l_target.toFixed(2)}</div>
                    <div>a: {target.a_target.toFixed(2)}</div>
                    <div>b: {target.b_target.toFixed(2)}</div>
                    <div className="muted note">
                        Tol: {target.tolerance_warning} (Warn) / {target.tolerance_critical} (Crit)
                    </div>
                </div>

                <div className="current-info">
                    <h4>Measured</h4>
                    <div>L: {currentMeasurement?.l_value.toFixed(2) || '-'}</div>
                    <div>a: {currentMeasurement?.a_value.toFixed(2) || '-'}</div>
                    <div>b: {currentMeasurement?.b_value.toFixed(2) || '-'}</div>
                </div>
            </div>

            <div className="chart-frame">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="time" />
                        <YAxis domain={[0, 'auto']} />
                        <Tooltip />
                        <Legend />
                        <ReferenceLine y={target.tolerance_warning} label="Warning" stroke="var(--warn)" strokeDasharray="3 3" />
                        <ReferenceLine y={target.tolerance_critical} label="Critical" stroke="var(--bad)" strokeDasharray="3 3" />
                        <Line type="monotone" dataKey="deltaE" stroke="var(--accent)" strokeWidth={2} dot={false} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ColorDashboard;
