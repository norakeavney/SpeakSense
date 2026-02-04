'use client';

import { useState, useEffect } from 'react';

export default function AnalysisProgress({ jobId }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!jobId) return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/analysis/${jobId}/status/`);
        if (!response.ok) throw new Error('Failed to fetch status');
        const data = await response.json();
        setStatus(data);

        // Stop polling if done or failed
        if (data.status === 'done' || data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (err) {
        setError(err.message);
        clearInterval(interval);
      }
    };

    // Poll immediately, then every 2 seconds
    pollStatus();
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  if (!status) {
    return (
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-blue-700">Loading analysis status...</p>
      </div>
    );
  }

  const getStatusColor = (s) => {
    if (s === 'done') return 'text-green-600';
    if (s === 'processing') return 'text-blue-600 animate-pulse';
    if (s === 'failed') return 'text-red-600';
    return 'text-gray-500';
  };

  const getStatusIcon = (s) => {
    if (s === 'done') return '✅';
    if (s === 'processing') return '⏳';
    if (s === 'failed') return '❌';
    return '⏸️';
  };

  return (
    <div className="mt-6 space-y-4">
      {/* Overall Status */}
      <div className={`p-4 rounded-lg border-2 ${
        status.status === 'done' ? 'bg-green-50 border-green-200' :
        status.status === 'failed' ? 'bg-red-50 border-red-200' :
        'bg-blue-50 border-blue-200'
      }`}>
        <h3 className="text-lg font-semibold mb-2">
          Analysis Status: <span className="capitalize">{status.status}</span>
        </h3>
        <p className="text-sm text-gray-600">Job ID: {status.job_id}</p>
      </div>

      {/* Steps Progress */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <h4 className="font-semibold mb-3">Analysis Steps:</h4>
        <div className="space-y-2">
          {Object.entries(status.steps).map(([step, stepStatus]) => (
            <div key={step} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
              <span className="font-medium capitalize">
                {step.replace('_', ' ')}
              </span>
              <span className={`font-semibold ${getStatusColor(stepStatus)}`}>
                {getStatusIcon(stepStatus)} {stepStatus}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Results (if available) */}
      {status.results && Object.keys(status.results).length > 0 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h4 className="font-semibold mb-3">Results:</h4>
          <div className="space-y-3 text-sm">
            
            {/* Transcription */}
            {status.results.transcription && (
              <div className="p-3 bg-blue-50 rounded">
                <h5 className="font-semibold text-blue-900 mb-2">📝 Transcription</h5>
                <p className="text-gray-700">{status.results.transcription.text}</p>
              </div>
            )}

            {/* Speaker Metrics */}
            {status.results.speaker_metrics && (
              <div className="p-3 bg-purple-50 rounded">
                <h5 className="font-semibold text-purple-900 mb-2">👥 Speaker Metrics</h5>
                <p><strong>Duration:</strong> {status.results.speaker_metrics.total_duration_seconds}s</p>
                <p><strong>WPM:</strong> {status.results.speaker_metrics.words_per_minute}</p>
                <p><strong>Speakers:</strong> {status.results.speaker_metrics.speakers_detected}</p>
              </div>
            )}

            {/* Emotion */}
            {status.results.emotion && (
              <div className="p-3 bg-yellow-50 rounded">
                <h5 className="font-semibold text-yellow-900 mb-2">😊 Emotion</h5>
                <p><strong>Overall:</strong> {status.results.emotion.overall_sentiment}</p>
              </div>
            )}

            {/* Topics */}
            {status.results.topics && (
              <div className="p-3 bg-green-50 rounded">
                <h5 className="font-semibold text-green-900 mb-2">💡 Topics</h5>
                <p><strong>Keywords:</strong> {status.results.topics.keywords?.join(', ')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      {status.error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700"><strong>Error:</strong> {status.error}</p>
        </div>
      )}
    </div>
  );
}
