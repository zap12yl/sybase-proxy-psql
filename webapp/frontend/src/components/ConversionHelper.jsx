import React, { useState } from 'react';
import api from '../api';

const ConversionHelper = () => {
  const [inputSql, setInputSql] = useState('');
  const [convertedSql, setConvertedSql] = useState('');
  const [warnings, setWarnings] = useState([]);

  const handleConvert = async () => {
    try {
      const response = await api.post('/api/convert', { sql: inputSql });
      setConvertedSql(response.data.converted);
      setWarnings(response.data.warnings);
    } catch (error) {
      setConvertedSql('Conversion failed');
    }
  };

  return (
    <div className="conversion-helper">
      <div className="editor-pane">
        <h3>Sybase SQL Input</h3>
        <textarea value={inputSql} onChange={(e) => setInputSql(e.target.value)} />
      </div>
      
      <button onClick={handleConvert}>Convert</button>
      
      <div className="result-pane">
        <h3>PostgreSQL Output</h3>
        <pre>{convertedSql}</pre>
        {warnings.map((warn, i) => (
          <div key={i} className="warning">
            ⚠️ {warn}
          </div>
        ))}
      </div>
    </div>
  );
};