import React from 'react';

const RollDiameterMap = ({ diameterMm, defects }) => {
    const size = 220;
    const radius = 90;
    const center = size / 2;
    const safeDefects = Array.isArray(defects) ? defects : [];
    const circumferenceM = Math.PI * (diameterMm / 1000);

    const pointForMeter = (meter) => {
        if (!circumferenceM) return { x: center, y: center };
        const angle = ((meter % circumferenceM) / circumferenceM) * Math.PI * 2;
        return {
            x: center + Math.cos(angle) * radius,
            y: center + Math.sin(angle) * radius
        };
    };

    const colorForSeverity = (severity) => {
        if (severity === 'critical') return 'var(--bad)';
        if (severity === 'warning') return 'var(--warn)';
        return 'var(--accent)';
    };

    return (
        <div className="roll-map">
            <h3>Roll Diameter Map</h3>
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                <circle cx={center} cy={center} r={radius} fill="none" stroke="#cfc7bc" strokeWidth="8" />
                <circle cx={center} cy={center} r={radius - 18} fill="none" stroke="#e6dfd4" strokeWidth="2" />
                {safeDefects.map((d, idx) => {
                    const meter = d.meter || 0;
                    const point = pointForMeter(meter);
                    return (
                        <circle
                            key={`${meter}-${idx}`}
                            cx={point.x}
                            cy={point.y}
                            r="4"
                            fill={colorForSeverity(d.severity)}
                        />
                    );
                })}
            </svg>
            <p className="muted">Diameter: {diameterMm} mm</p>
        </div>
    );
};

export default RollDiameterMap;
