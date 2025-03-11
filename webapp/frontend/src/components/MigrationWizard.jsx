import React, { useState, useEffect } from 'react';
import api from '../api';

const MigrationWizard = () => {
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);

  const startMigration = async () => {
    try {
      const response = await api.post('/api/migration/start');
      setTaskId(response.data.task_id);
      setStatus('running');
    } catch (error) {
      setStatus('error');
    }
  };

  useEffect(() => {
    const interval = setInterval(async () => {
      if (taskId) {
        const response = await api.get(`/api/migration/status/${taskId}`);
        setStatus(response.data.status);
        if (response.data.status === 'completed') {
          clearInterval(interval);
        }
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <div className="migration-wizard">
      <h2>Database Migration</h2>
      <button onClick={startMigration} disabled={status === 'running'}>
        {status === 'running' ? 'Migrating...' : 'Start Migration'}
      </button>
      <div className="progress-bar">
        <div style={{ width: `${progress}%` }}></div>
      </div>
      <p>Status: {status}</p>
    </div>
  );
};

export default MigrationWizard;