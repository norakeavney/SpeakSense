'use client';

import { useState, useEffect } from 'react';

export default function AnalysisProgress({ jobId, onComplete }) {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    let interval;

    const pollStatus = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/analysis/${jobId}/status/`
        );

        if (!response.ok) throw new Error('Failed to fetch status');

        const data = await response.json();
        setStatus(data);

        if (data.status === 'done') {
          clearInterval(interval);

          if (onComplete) {
            onComplete(data); // send full analysis results upward
          }
        }

        if (data.status === 'failed') {
          clearInterval(interval);
        }

      } catch (err) {
        clearInterval(interval);
      }
    };

    pollStatus();
    interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);

  }, [jobId, onComplete]);

  if (!status) {
    return (
      <div className="p-6 bg-white border rounded-lg shadow-sm">
        <p className="text-gray-600">Initializing analysis...</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white border rounded-lg shadow-sm">
      <h3 className="font-semibold text-lg mb-2">
        Processing Analysis
      </h3>

      <div className="space-y-2">
        {Object.entries(status.steps || {}).map(([step, stepStatus]) => (
          <div
            key={step}
            className="flex justify-between text-sm border-b py-1"
          >
            <span className="capitalize">{step.replace('_', ' ')}</span>
            <span className="font-medium capitalize">{stepStatus}</span>
          </div>
        ))}
      </div>
    </div>
  );
}