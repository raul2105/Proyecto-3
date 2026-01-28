import React from 'react';

const DiagnosticsPanel = ({ diagnostics }) => {
    if (!diagnostics) return <div>No diagnostics data...</div>;

    const { brightness, blur_score, contrast } = diagnostics;

    const getStatus = (val, type) => {
        // Simple heuristic thresholds
        if (type === 'blur' && val < 50) return 'bad'; // Too blurry
        if (type === 'brightness' && (val < 20 || val > 240)) return 'bad';
        return 'good';
    };

    return (
        <div className="diagnostics-panel">
            <h3>Image Quality Diagnostics</h3>

            <div className="diag-metrics">
                <div className={`metric ${getStatus(blur_score, 'blur')}`}>
                    <label>Focus (Blur Score)</label>
                    <div className="value">{blur_score.toFixed(1)}</div>
                    <div className="desc">Higher is sharper</div>
                </div>

                <div className={`metric ${getStatus(brightness, 'brightness')}`}>
                    <label>Brightness</label>
                    <div className="value">{brightness.toFixed(1)}</div>
                    <div className="desc">Target: ~120-130</div>
                </div>

                <div className="metric">
                    <label>Contrast</label>
                    <div className="value">{contrast.toFixed(1)}</div>
                </div>
            </div>
        </div>
    );
};

export default DiagnosticsPanel;
