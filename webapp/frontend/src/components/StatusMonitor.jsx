import React from 'react';

const StatusMonitor = ({ progress }) => {
  return (
    <div className="status-monitor">
      <h3>Migration Progress</h3>
      <div className="progress-item">
        <span>Tables Migrated:</span>
        <span>{progress.tables || 0}</span>
      </div>
      <div className="progress-item">
        <span>Rows Transferred:</span>
        <span>{progress.rows || 0}</span>
      </div>
      <div className="progress-item">
        <span>Stored Procedures:</span>
        <span>{progress.sprocs || 0}</span>
      </div>
    </div>
  );
};

export default StatusMonitor;