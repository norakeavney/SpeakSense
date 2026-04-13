'use client';

import React, { useState } from 'react';

export default function TopicSentimentAnalysis({ topicSentiment = {}, speakersAvailable = [] }) {
  const [expandedTopic, setExpandedTopic] = useState(null);

  if (!topicSentiment || Object.keys(topicSentiment).length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-medium mb-4">Topic Sentiment Analysis</h3>
        <p className="text-gray-400 text-sm">No topic sentiment data available.</p>
      </div>
    );
  }

  const safeReplace = (text) => {
    if (!text) return "Unknown";
    return String(text).replace(/_/g, " ");
  };

  const topicEntries = Object.entries(topicSentiment).sort((a, b) => b[1].mentions - a[1].mentions);

  const getSentimentColor = (sentiment) => {
    if (sentiment >= 0.1) return 'from-green-100 to-green-50';
    if (sentiment <= -0.1) return 'from-red-100 to-red-50';
    return 'from-gray-100 to-gray-50';
  };

  const getSentimentLabel = (sentiment) => {
    if (sentiment >= 0.1) return 'Positive';
    if (sentiment <= -0.1) return 'Negative';
    return 'Neutral';
  };

  const getSentimentBadgeColor = (label) => {
    if (label === 'Positive') return 'bg-green-100 text-green-800';
    if (label === 'Negative') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-4">
      {topicEntries.map(([topic, data]) => (
        <div
          key={topic}
          className={`bg-gradient-to-r ${getSentimentColor(data.average_sentiment)} border border-gray-200 rounded-lg p-4 cursor-pointer transition-all hover:shadow-md`}
          onClick={() => setExpandedTopic(expandedTopic === topic ? null : topic)}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-semibold text-gray-800">{topic}</h4>
              <p className="text-sm text-gray-600 mt-1">
                Mentioned <span className="font-medium">{data.mentions}</span> time(s)
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getSentimentBadgeColor(getSentimentLabel(data.average_sentiment))}`}>
                {getSentimentLabel(data.average_sentiment)}
              </span>
              <span className="text-sm font-medium text-gray-700">
                {(data.average_sentiment).toFixed(2)}
              </span>
            </div>
          </div>

          {/* Sentiment breakdown */}
          <div className="mt-3 flex gap-2">
            {data.positive_mentions > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-12 h-2 bg-green-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500"
                    style={{ width: `${(data.positive_mentions / data.mentions) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-green-700">{data.positive_mentions}</span>
              </div>
            )}
            {data.neutral_mentions > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-12 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gray-500"
                    style={{ width: `${(data.neutral_mentions / data.mentions) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-700">{data.neutral_mentions}</span>
              </div>
            )}
            {data.negative_mentions > 0 && (
              <div className="flex items-center gap-1">
                <div className="w-12 h-2 bg-red-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-red-500"
                    style={{ width: `${(data.negative_mentions / data.mentions) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-red-700">{data.negative_mentions}</span>
              </div>
            )}
          </div>

          {/* Expanded details */}
          {expandedTopic === topic && (
            <div className="mt-4 pt-4 border-t border-gray-300 space-y-3">
              {/* Per-speaker breakdown */}
              {data.per_speaker && Object.keys(data.per_speaker).length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase text-gray-600 mb-2">
                    Per-Speaker Sentiment:
                  </p>
                  <div className="space-y-2">
                    {Object.entries(data.per_speaker).map(([speaker, speakerData]) => (
                      <div key={speaker} className="ml-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700 font-medium">{safeReplace(speaker)}</span>
                          <span className="text-gray-600">
                            {speakerData.mentions} mention{speakerData.mentions !== 1 ? 's' : ''}
                          </span>
                        </div>
                        <div className="flex gap-1 mt-1">
                          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-green-500"
                              style={{ width: `${speakerData.positive_pct || 0}%` }}
                            />
                          </div>
                          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gray-500"
                              style={{ width: `${speakerData.neutral_pct || 0}%` }}
                            />
                          </div>
                          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-red-500"
                              style={{ width: `${speakerData.negative_pct || 0}%` }}
                            />
                          </div>
                        </div>
                        <div className="flex gap-2 mt-1 text-xs text-gray-500">
                          <span>+{speakerData.positive_pct?.toFixed(0) || 0}%</span>
                          <span>~{speakerData.neutral_pct?.toFixed(0) || 0}%</span>
                          <span>-{speakerData.negative_pct?.toFixed(0) || 0}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Example passages */}
              {data.example_passages && data.example_passages.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase text-gray-600 mb-2">
                    Example Passages:
                  </p>
                  <div className="space-y-2">
                    {data.example_passages.map((passage, idx) => (
                      <div key={idx} className="ml-2 p-2 bg-white bg-opacity-60 rounded border border-gray-300 text-xs">
                        <div className="flex items-start justify-between mb-1">
                          <span className="font-medium text-gray-700">{passage.speaker}</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            passage.sentiment === 'positive' ? 'bg-green-100 text-green-800' :
                            passage.sentiment === 'negative' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {passage.sentiment}
                          </span>
                        </div>
                        <p className="text-gray-700 italic">{passage.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
