import React from 'react';
import RollDiameterMap from './RollDiameterMap';

const Dashboard = ({ stats, defects, rollDefects, rollDiameter }) => {

    // Safety check for stats
    const speed = stats?.speed_m_min || 0;
    const yieldPct = stats?.yield_pct || 100;
    const defectCount = stats?.defect_count || 0;
    const safeDefects = Array.isArray(defects) ? defects : [];

    const yieldClass = yieldPct > 98 ? 'value good' : 'value warn';
    const defectClass = defectCount > 0 ? 'value bad' : 'value';

    return (
        <div className="dashboard">
            <div className="kpi-grid">
                <div className="kpi-card">
                    <h3>Speed</h3>
                    <div className="value">{speed.toFixed(1)} <small>m/min</small></div>
                </div>
                <div className="kpi-card">
                    <h3>Yield</h3>
                    <div className={yieldClass}>
                        {yieldPct.toFixed(1)} <small>%</small>
                    </div>
                </div>
                <div className="kpi-card">
                    <h3>Defects</h3>
                    <div className={defectClass}>
                        {defectCount}
                    </div>
                </div>
            </div>

            <div className="card">
                <h3>Recent Defects</h3>
                {safeDefects.length === 0 ? (
                    <p className="muted">No defects detected.</p>
                ) : (
                    <ul className="defect-list-small">
                        {safeDefects.slice(-5).reverse().map((d, i) => (
                            <li key={i}>
                                <span className="type">{d.type}</span>
                                <span className="area">{d.area.toFixed(0)} px^2</span>
                                <span className="coords">({d.x}, {d.y})</span>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            <div className="card">
                <RollDiameterMap diameterMm={rollDiameter} defects={rollDefects} />
            </div>
        </div>
    );
};

export default Dashboard;
