'use client';

import { useState, useEffect } from 'react';

export default function SpeakerIdentification({ jobId, onConfirm }) {
  const [suggestions, setSuggestions] = useState(null);
  const [speakerNames, setSpeakerNames] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const fetchSuggestions = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/analysis/${jobId}/speakers/suggestions/`
        );
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to fetch suggestions');
        }

        const data = await response.json();
        setSuggestions(data);

        // Initialize speaker names with AI suggestions
        const initialNames = {};
        Object.entries(data.suggestions).forEach(([speakerId, suggestion]) => {
          initialNames[speakerId] = suggestion.suggested_name || speakerId;
        });
        setSpeakerNames(initialNames);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching speaker suggestions:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchSuggestions();
  }, [jobId]);

  const handleNameChange = (speakerId, newName) => {
    setSpeakerNames(prev => ({
      ...prev,
      [speakerId]: newName
    }));
  };

  const handleUseSuggestion = (speakerId, suggestedName) => {
    setSpeakerNames(prev => ({
      ...prev,
      [speakerId]: suggestedName
    }));
  };

  const handleConfirm = async () => {
    setConfirming(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/analysis/${jobId}/speakers/confirm/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            speakers: speakerNames
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to confirm speakers');
      }

      const data = await response.json();
      setConfirmed(true);
      
      // Notify parent component
      if (onConfirm) {
        onConfirm(speakerNames);
      }

      console.log('Speakers confirmed:', data);
      
    } catch (err) {
      console.error('Error confirming speakers:', err);
      setError(err.message);
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div className="mt-6 p-6 bg-purple-50 border-2 border-purple-200 rounded-lg">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
          <p className="text-purple-700 font-medium">
            🤖 AI is analyzing speakers...
          </p>
        </div>
      </div>
    );
  }

  if (error && !suggestions) {
    return (
      <div className="mt-6 p-6 bg-yellow-50 border-2 border-yellow-200 rounded-lg">
        <p className="text-yellow-800">
          ⚠️ Speaker identification not available yet. Please check back shortly.
        </p>
      </div>
    );
  }

  if (confirmed) {
    return (
      <div className="mt-6 p-6 bg-green-50 border-2 border-green-200 rounded-lg">
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-2xl">✅</span>
          <h3 className="text-xl font-bold text-green-800">
            Speakers Confirmed!
          </h3>
        </div>
        <div className="space-y-2">
          {Object.entries(speakerNames).map(([speakerId, name]) => (
            <div key={speakerId} className="flex items-center space-x-2 text-green-700">
              <span className="font-mono text-sm bg-green-100 px-2 py-1 rounded">
                {speakerId}
              </span>
              <span>→</span>
              <span className="font-semibold">{name}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 p-6 bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-300 rounded-lg shadow-lg">
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-2xl">🎭</span>
          <h3 className="text-2xl font-bold text-purple-900">
            Identify Speakers
          </h3>
        </div>
        <p className="text-gray-700">
          Our AI has detected <span className="font-bold text-purple-700">
            {suggestions?.num_speakers} speaker(s)
          </span> and made educated guesses. 
          Please confirm or correct the names below.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">⚠️ {error}</p>
        </div>
      )}

      <div className="space-y-6">
        {suggestions && Object.entries(suggestions.suggestions).map(([speakerId, suggestion]) => (
          <div 
            key={speakerId}
            className="bg-white p-5 rounded-lg border-2 border-purple-200 shadow-sm hover:shadow-md transition-shadow"
          >
            {/* Speaker Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-3xl">👤</span>
                <div>
                  <h4 className="text-lg font-bold text-gray-800">
                    {speakerId}
                  </h4>
                  <p className="text-sm text-gray-500">
                    {suggestion.suggested_role || 'Speaker'}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">Confidence:</span>
                <div className="flex items-center space-x-1">
                  {[...Array(5)].map((_, i) => (
                    <span 
                      key={i}
                      className={i < Math.round(suggestion.confidence * 5) 
                        ? 'text-yellow-400' 
                        : 'text-gray-300'}
                    >
                      ⭐
                    </span>
                  ))}
                </div>
                <span className="text-sm font-semibold text-purple-600">
                  {Math.round(suggestion.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* AI Reasoning */}
            <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
              <p className="text-sm font-semibold text-blue-900 mb-2">
                🧠 AI Analysis:
              </p>
              <ul className="text-sm text-blue-800 space-y-1">
                {suggestion.reasoning.map((reason, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Name Input */}
            <div className="space-y-3">
              <label className="block">
                <span className="text-sm font-semibold text-gray-700 mb-1 block">
                  Speaker Name:
                </span>
                <input
                  type="text"
                  value={speakerNames[speakerId] || ''}
                  onChange={(e) => handleNameChange(speakerId, e.target.value)}
                  placeholder="Enter speaker name..."
                  className="w-full px-4 py-2 border-2 border-purple-300 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
                />
              </label>

              {/* Quick Suggestions */}
              <div className="flex flex-wrap gap-2">
                <span className="text-xs font-semibold text-gray-600 py-2">
                  Quick fill:
                </span>
                <button
                  onClick={() => handleUseSuggestion(speakerId, suggestion.suggested_name)}
                  className="text-xs px-3 py-1 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-full transition-colors"
                >
                  ✨ {suggestion.suggested_name}
                </button>
                {suggestion.alternative_suggestions.slice(0, 3).map((alt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleUseSuggestion(speakerId, alt)}
                    className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
                  >
                    {alt}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Confirm Button */}
      <div className="mt-6 flex items-center justify-between">
        <p className="text-sm text-gray-600">
          💡 Tip: The AI suggestions are based on speaking patterns and context analysis
        </p>
        <button
          onClick={handleConfirm}
          disabled={confirming || Object.values(speakerNames).some(name => !name.trim())}
          className={`px-6 py-3 rounded-lg font-bold text-white transition-all transform hover:scale-105 ${
            confirming || Object.values(speakerNames).some(name => !name.trim())
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg'
          }`}
        >
          {confirming ? (
            <span className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              <span>Confirming...</span>
            </span>
          ) : (
            <span className="flex items-center space-x-2">
              <span>✓</span>
              <span>Confirm Speakers</span>
            </span>
          )}
        </button>
      </div>

      {Object.values(speakerNames).some(name => !name.trim()) && (
        <p className="mt-2 text-sm text-red-600 text-right">
          ⚠️ Please provide names for all speakers
        </p>
      )}
    </div>
  );
}
