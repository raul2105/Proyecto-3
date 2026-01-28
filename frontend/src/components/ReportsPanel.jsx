import React from 'react';

const ReportsPanel = ({ reports, reportDetail, onSelectReport, apiUrl }) => {
    const safeReports = Array.isArray(reports) ? reports : [];

    return (
        <div className="reports-grid">
            <div className="card">
                <h3>Report History</h3>
                {safeReports.length === 0 ? (
                    <p className="muted">No reports yet.</p>
                ) : (
                    <ul className="report-list">
                        {safeReports.slice().reverse().map((r) => (
                            <li key={r.id}>
                                <div>
                                    <strong>{r.roll_id}</strong>
                                    <span className="muted"> {r.ts}</span>
                                </div>
                                <div className="row gap">
                                    <button className="btn-secondary" onClick={() => onSelectReport(r)}>View</button>
                                    <a className="btn-muted" href={`${apiUrl}/reports/roll/${r.roll_id}?format=pdf`} target="_blank" rel="noreferrer">PDF</a>
                                    <a className="btn-muted" href={`${apiUrl}/reports/roll/${r.roll_id}?format=csv`} target="_blank" rel="noreferrer">CSV</a>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            <div className="card">
                <h3>Report Detail</h3>
                {!reportDetail ? (
                    <p className="muted">Select a report to preview.</p>
                ) : (
                    <div className="report-detail">
                        <div><strong>Roll:</strong> {reportDetail.roll_id}</div>
                        <div><strong>Job:</strong> {reportDetail.job_id || '-'}</div>
                        <div><strong>Yield:</strong> {reportDetail.yield_pct}%</div>
                        <div><strong>Defects:</strong> {JSON.stringify(reportDetail.defects_by_bucket)}</div>
                        <div><strong>Segments:</strong> {Object.keys(reportDetail.defect_map_by_segment || {}).length}</div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReportsPanel;
