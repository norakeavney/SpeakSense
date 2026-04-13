'use client';

import { useState, useEffect } from 'react';
import { getAnalysisStatus } from '../lib/api';

export default function AnalysisProgress({ jobId, onComplete }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const safeReplace = (text) => {
    if (!text) return "Unknown";
    return String(text).replace(/_/g, " ");
  };

  useEffect(() => {
    if (!jobId) return;

    let interval;

    const pollStatus = async () => {
      try {
        const data = await getAnalysisStatus(jobId);
        setStatus(data);

        if (data.status === 'done') {
          clearInterval(interval);
          if (onComplete) {
            onComplete(data); // send full analysis results upward
          }
        }

        if (data.status === 'failed') {
          clearInterval(interval);
          setError(data.error || 'Analysis failed');
        }

      } catch (err) {
        clearInterval(interval);
        setError('Failed to fetch analysis status');
      }
    };

    pollStatus();
    interval = setInterval(pollStatus, 5000);

    return () => clearInterval(interval);

  }, [jobId, onComplete]);

  if (error) {
    return (
      <div className="p-6 bg-white border rounded-lg shadow-sm">
        <div className="text-center">
          <div className="text-red-600 mb-2">Analysis Failed</div>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

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
            <span className="capitalize">{safeReplace(step)}</span>
            <span className="font-medium capitalize">{stepStatus}</span>
          </div>
        ))}
      </div>
    </div>
  );
}