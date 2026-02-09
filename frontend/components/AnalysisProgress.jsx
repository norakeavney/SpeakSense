'use client';

import { useState, useEffect } from 'react';
import SpeakerIdentification from './SpeakerIdentification';

export default function AnalysisProgress({ jobId }) {
  const [status, setStatus] = useState(null);

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
    if (s === 'done') return '✓';
    if (s === 'processing') return '...';
    if (s === 'failed') return '✗';
    return '○';
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
            
            {/* Combined Transcript with Speakers */}
            {status.results.diarization && status.results.diarization.transcript && status.results.diarization.status === 'completed' ? (
              <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-indigo-200">
                <div className="flex items-center justify-between mb-3">
                  <h5 className="font-semibold text-indigo-900 text-lg">Transcript with Speakers</h5>
                  <div className="flex gap-2 items-center">
                    <span className="text-sm bg-indigo-200 px-3 py-1 rounded-full font-semibold">
                      {status.results.diarization.num_speakers} {status.results.diarization.num_speakers === 1 ? 'Speaker' : 'Speakers'}
                    </span>
                    {/* Show total duration if available */}
                    {status.results.diarization.transcript.length > 0 && (
                      <span className="text-xs bg-blue-100 px-2 py-1 rounded-full">
                        {Math.round(status.results.diarization.transcript[status.results.diarization.transcript.length - 1].end)}s duration
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Speaker-labeled transcript */}
                <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                  {status.results.diarization.transcript.map((turn, idx) => {
                    // Assign colors to speakers for visual distinction
                    const speakerColors = {
                      'SPEAKER_00': 'border-blue-400 bg-blue-50',
                      'SPEAKER_01': 'border-green-400 bg-green-50',
                      'SPEAKER_02': 'border-purple-400 bg-purple-50',
                      'SPEAKER_03': 'border-orange-400 bg-orange-50',
                    };
                    const colorClass = speakerColors[turn.speaker] || 'border-gray-400 bg-gray-50';
                    
                    return (
                      <div key={idx} className={`bg-white p-3 rounded shadow-sm border-l-4 ${colorClass}`}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-indigo-700 text-sm">
                            {turn.speaker}
                          </span>
                          <span className="text-xs text-gray-500">
                            {turn.start?.toFixed(1)}s - {turn.end?.toFixed(1)}s
                            <span className="ml-2 text-gray-400">
                              ({(turn.end - turn.start).toFixed(1)}s)
                            </span>
                          </span>
                        </div>
                        <p className="text-gray-800 leading-relaxed">{turn.text}</p>
                      </div>
                    );
                  })}
                </div>
                
                {/* Download transcript button */}
                <div className="mt-4 pt-3 border-t border-indigo-200">
                  <button
                    onClick={() => {
                      const transcriptText = status.results.diarization.transcript
                        .map(turn => `[${turn.start.toFixed(1)}s - ${turn.end.toFixed(1)}s] ${turn.speaker}:\n${turn.text}\n`)
                        .join('\n');
                      const blob = new Blob([transcriptText], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `transcript_${jobId}.txt`;
                      a.click();
                    }}
                    className="text-sm bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition"
                  >
                    Download Transcript
                  </button>
                </div>
              </div>
            ) : status.results.transcription ? (
              /* Fallback: Show plain transcription if diarization failed */
              <div className="p-3 bg-blue-50 rounded border-l-4 border-orange-400">
                <h5 className="font-semibold text-blue-900 mb-2">Transcription (No Speaker Labels)</h5>
                <p className="text-gray-700 leading-relaxed">{status.results.transcription.text}</p>
                {status.results.diarization?.error && (
                  <div className="mt-3 p-2 bg-orange-100 border border-orange-300 rounded">
                    <p className="text-xs text-orange-700">
                      <strong>Speaker identification unavailable:</strong> {status.results.diarization.error}
                    </p>
                  </div>
                )}
              </div>
            ) : null}

            {/* Speaker Metrics */}
            {status.results.speaker_metrics && (
              <div className="p-3 bg-purple-50 rounded">
                <h5 className="font-semibold text-purple-900 mb-2">Speaker Metrics</h5>
                
                {/* Summary */}
                {status.results.speaker_metrics.summary && (
                  <p className="text-gray-700 mb-3 whitespace-pre-line">
                    {status.results.speaker_metrics.summary}
                  </p>
                )}
                
                {/* Individual Speaker Stats */}
                {status.results.speaker_metrics.speakers && (
                  <div className="space-y-2 mt-3">
                    {Object.entries(status.results.speaker_metrics.speakers).map(([speaker, metrics]) => (
                      <div key={speaker} className="bg-white p-3 rounded border border-purple-200">
                        <h6 className="font-bold text-purple-700 mb-2">{speaker}</h6>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <p><strong>Speaking Time:</strong> {metrics.speaking_time_seconds}s</p>
                          <p><strong>WPM:</strong> {metrics.words_per_minute}</p>
                          <p><strong>Total Words:</strong> {metrics.total_words}</p>
                          <p><strong>Unique Words:</strong> {metrics.unique_words}</p>
                          <p><strong>Turns:</strong> {metrics.num_turns}</p>
                          <p><strong>Filler Words:</strong> {metrics.filler_words}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Comparative Stats */}
                {status.results.speaker_metrics.comparative && (
                  <div className="mt-3 p-3 bg-indigo-50 rounded border border-indigo-200">
                    <h6 className="font-semibold text-indigo-900 mb-2">Comparison</h6>
                    <p className="text-sm"><strong>Balance:</strong> {status.results.speaker_metrics.comparative.balance_interpretation}</p>
                    <p className="text-sm"><strong>Most Talkative:</strong> {status.results.speaker_metrics.comparative.most_talkative_speaker}</p>
                    <p className="text-sm"><strong>Fastest Speaker:</strong> {status.results.speaker_metrics.comparative.fastest_speaker}</p>
                  </div>
                )}
              </div>
            )}


            {/* Emotion */}
            {status.results.emotion && (
              <div className="p-3 bg-yellow-50 rounded">
                <h5 className="font-semibold text-yellow-900 mb-2">Emotion</h5>
                <p><strong>Overall:</strong> {status.results.emotion.overall_sentiment}</p>
              </div>
            )}

            {/* Topics */}
            {status.results.topics && (
              <div className="p-3 bg-green-50 rounded">
                <h5 className="font-semibold text-green-900 mb-2">Topics</h5>
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

      {/* Speaker Identification - Show when diarization is done */}
      {status.steps.diarization === 'done' && 
       status.results.diarization && 
       status.results.diarization.requires_user_confirmation &&
       !status.results.diarization.confirmed_speakers && (
        <SpeakerIdentification 
          jobId={jobId}
          onConfirm={(names) => {
            console.log('Speakers confirmed:', names);
            // Trigger a status refresh
            setStatus(prev => ({
              ...prev,
              results: {
                ...prev.results,
                diarization: {
                  ...prev.results.diarization,
                  confirmed_speakers: names
                }
              }
            }));
          }}
        />
      )}
    </div>
  );
}
