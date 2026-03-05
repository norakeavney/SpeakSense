import React from 'react';

export default function SpeakerAnalysis({ results }) {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-2">Enhanced Speaker Analysis</h3>
        <p className="text-gray-600 text-sm">Component loaded successfully - Features coming soon!</p>
        <div className="mt-4">
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-40">
            {JSON.stringify(results?.speaker_metrics, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}