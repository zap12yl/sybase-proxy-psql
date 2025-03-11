import React, { useState } from 'react';
import MigrationWizard from './components/MigrationWizard';
import StatusMonitor from './components/StatusMonitor';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
  const [progress, setProgress] = useState(null);

  return (
    <div className="container mt-5">
      <h1 className="mb-4">Database Migration Portal</h1>
      <div className="card">
        <div className="card-body">
          <MigrationWizard onUpdate={setProgress} />
          {progress && <StatusMonitor progress={progress} />}
        </div>
      </div>
    </div>
  );
}

export default App;