import React from 'react';

const AlarmEventsPanel = ({ alarms, events, onAck, onClear }) => {
    const safeAlarms = Array.isArray(alarms) ? alarms : [];
    const safeEvents = Array.isArray(events) ? events : [];

    return (
        <div className="alarm-events">
            <div className="card">
                <h3>Active Alarms</h3>
                {safeAlarms.length === 0 ? (
                    <p className="muted">No active alarms.</p>
                ) : (
                    <ul className="alarm-list">
                        {safeAlarms.map((a) => (
                            <li key={a.code}>
                                <div>
                                    <strong>{a.code}</strong>
                                    <span className={`pill ${a.severity === 'critical' ? 'warn' : 'good'}`}>{a.severity}</span>
                                </div>
                                <div className="muted">{a.message}</div>
                                <div className="row gap">
                                    <button onClick={() => onAck(a.code)} className="btn-secondary">Ack</button>
                                    <button onClick={() => onClear(a.code)} className="btn-muted">Clear</button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            <div className="card">
                <h3>Recent Events</h3>
                {safeEvents.length === 0 ? (
                    <p className="muted">No events yet.</p>
                ) : (
                    <ul className="event-list">
                        {safeEvents.slice().reverse().slice(0, 10).map((e) => (
                            <li key={e.id}>
                                <span className="label">{e.type}</span>
                                <span>{e.message}</span>
                                <span className="muted">{e.ts}</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

export default AlarmEventsPanel;
