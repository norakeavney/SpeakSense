'use client';

import React, { useState } from 'react';
import WordCloud from './WordCloud';

export default function PerSpeakerTopics({ 
  perSpeakerTopics = {}, 
  activeSpeaker = null,
  speakerColors = {} 
}) {
  const [expandedSpeaker, setExpandedSpeaker] = useState(activeSpeaker);

  if (!perSpeakerTopics || Object.keys(perSpeakerTopics).length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-medium mb-4">Per-Speaker Topics</h3>
        <p className="text-gray-400 text-sm">No per-speaker topic data available.</p>
      </div>
    );
  }

  const speakers = Object.entries(perSpeakerTopics).sort((a, b) => {
    return (b[1].turn_count || 0) - (a[1].turn_count || 0);
  });

  const getSpeakerColor = (speaker) => {
    return speakerColors?.[speaker] || { bg: '#e5e7eb', border: '#9ca3af', text: '#374151' };
  };

  return (
    <div className="space-y-4">
      {speakers.map(([speaker, data]) => {
        const color = getSpeakerColor(speaker);
        const isExpanded = expandedSpeaker === speaker;
        const keywords = data.keywords || [];
        const topics = data.topics || [];
        const turnCount = data.turn_count || 0;
        const wordCloudData = keywords.map((keyword) => ({
          word: keyword,
          score: data.scores?.[keyword] || 0.5
        }));

        return (
          <div
            key={speaker}
            className="border-l-4 rounded-lg overflow-hidden"
            style={{ borderLeftColor: color.border }}
          >
            <button
              onClick={() => setExpandedSpeaker(isExpanded ? null : speaker)}
              className="w-full p-4 bg-white hover:bg-gray-50 transition-colors flex items-start justify-between"
              style={{
                backgroundColor: isExpanded ? color.bg : 'white',
              }}
            >
              <div className="text-left flex-1">
                <h4 
                  className="font-semibold"
                  style={{ color: color.text }}
                >
                  {speaker.replace('_', ' ')}
                </h4>
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">{topics.length}</span> main topic{topics.length !== 1 ? 's' : ''} • 
                  <span className="font-medium ml-1">{keywords.length}</span> keyword{keywords.length !== 1 ? 's' : ''} • 
                  <span className="font-medium ml-1">{turnCount}</span> turn{turnCount !== 1 ? 's' : ''}
                </p>
                {topics.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {topics.slice(0, 3).map((topic, idx) => (
                      <span 
                        key={idx}
                        className="px-2 py-1 rounded-full text-xs font-medium text-white"
                        style={{ backgroundColor: color.border }}
                      >
                        {topic}
                      </span>
                    ))}
                    {topics.length > 3 && (
                      <span 
                        className="px-2 py-1 rounded-full text-xs font-medium"
                        style={{ 
                          backgroundColor: color.bg,
                          color: color.text,
                          border: `1px solid ${color.border}`
                        }}
                      >
                        +{topics.length - 3} more
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div className="ml-4">
                <svg
                  className={`w-5 h-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
              </div>
            </button>

            {/* Expanded content */}
            {isExpanded && (
              <div className="p-4 bg-gray-50 border-t border-gray-200 space-y-4">
                {/* Word cloud */}
                {keywords.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700 mb-3">Topic Word Cloud</p>
                    <WordCloud 
                      words={wordCloudData}
                      height={200}
                      maxWords={20}
                    />
                  </div>
                )}

                {/* All topics */}
                {topics.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700 mb-2">Main Topics</p>
                    <div className="flex flex-wrap gap-2">
                      {topics.map((topic, idx) => (
                        <span 
                          key={idx}
                          className="px-3 py-1 rounded-full text-sm font-medium text-white"
                          style={{ backgroundColor: color.border }}
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Keywords with scores */}
                {keywords.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700 mb-2">Keywords (with relevance scores)</p>
                    <div className="grid grid-cols-2 gap-2">
                      {keywords.map((keyword, idx) => {
                        const score = data.scores?.[keyword] || 0.5;
                        const scorePercent = (score * 100).toFixed(0);
                        return (
                          <div key={idx} className="flex items-center justify-between bg-white p-2 rounded border border-gray-200">
                            <span className="text-sm text-gray-700">{keyword}</span>
                            <div className="flex items-center gap-1">
                              <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full rounded-full"
                                  style={{ 
                                    width: `${scorePercent}%`,
                                    backgroundColor: color.border
                                  }}
                                />
                              </div>
                              <span className="text-xs text-gray-500 w-6">{scorePercent}%</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
