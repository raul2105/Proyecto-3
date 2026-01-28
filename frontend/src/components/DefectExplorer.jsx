import React, { useState } from 'react';

const DefectExplorer = ({ defects }) => {
    const [filterType, setFilterType] = useState('all');
    const safeDefects = Array.isArray(defects) ? defects : [];

    const filteredDefects = filterType === 'all'
        ? safeDefects
        : safeDefects.filter(d => d.type === filterType);

    const types = ['all', ...new Set(safeDefects.map(d => d.type))];

    return (
        <div className="defect-explorer card">
            <div className="explorer-header">
                <h3>Defect Explorer ({filteredDefects.length})</h3>
                <div className="filters">
                    <label>Type:</label>
                    <select value={filterType} onChange={e => setFilterType(e.target.value)}>
                        {types.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>
            </div>

            <div className="defect-table-container">
                <table className="defect-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Type</th>
                            <th>Area (px^2)</th>
                            <th>Position (x,y)</th>
                            <th>Cavity</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredDefects.map((d, i) => (
                            <tr key={i}>
                                <td>#{i + 1}</td>
                                <td><span className="badge">{d.type}</span></td>
                                <td>{d.area.toFixed(0)}</td>
                                <td>{d.x}, {d.y}</td>
                                <td>{d.cavity_index || '-'}</td>
                                <td>{(d.confidence || 0.95).toFixed(2)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default DefectExplorer;
