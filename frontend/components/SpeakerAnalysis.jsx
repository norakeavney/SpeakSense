import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function SpeakerAnalysis({ results }) {
  const speakerMetrics = results?.speaker_metrics || {};
  const speakers = speakerMetrics?.speakers || {};
  const questionsAnalysis = speakerMetrics?.questions_analysis || {};
  const agreementAnalysis = speakerMetrics?.agreement_analysis || {};
  const sentimentAnalysis = speakerMetrics?.sentiment_analysis || {};
  const leadingQuestions = speakerMetrics?.leading_questions || {};
  const interruptions = speakerMetrics?.interruptions || {};

  if (!speakers || Object.keys(speakers).length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Speaker Analysis</h3>
        <p className="text-gray-400">No speaker data available.</p>
      </div>
    );
  }

  // Prepare chart data for questions vs statements
  const questionData = Object.entries(questionsAnalysis).map(([speaker, data]) => ({
    name: speaker,
    questions: data?.questions || 0,
    statements: data?.statements || 0,
    role: data?.likely_role || 'unknown'
  }));

  // Prepare chart data for agreement/disagreement
  const agreementData = Object.entries(agreementAnalysis).map(([speaker, data]) => ({
    name: speaker,
    agreements: data?.agreements || 0,
    disagreements: data?.disagreements || 0,
    style: { communicationStyle: data?.communication_style || 'neutral' } // Fixed style prop
  }));

  return (
    <div className="space-y-6">
      {/* Basic Speaker Metrics */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Basic Speaker Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(speakers).map(([speaker, metrics]) => (
            <div key={speaker} className="border border-gray-200 rounded-lg p-4">
              <h4 className="font-medium text-sm mb-3">{speaker}</h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">Speaking time:</span>
                  <span className="font-medium">{Math.round(metrics.speaking_time_seconds || 0)}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Words:</span>
                  <span className="font-medium">{metrics.total_words || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">WPM:</span>
                  <span className="font-medium">{Math.round(metrics.words_per_minute || 0)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Turns:</span>
                  <span className="font-medium">{metrics.num_turns || 0}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Questions vs Statements Analysis */}
      {Object.keys(questionsAnalysis).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Questions vs Statements</h3>
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={questionData}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value, name) => [value, name === 'questions' ? 'Questions' : 'Statements']}
                />
                <Bar dataKey="questions" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="statements" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {questionData.map((speaker) => (
              <div key={speaker.name} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-sm">{speaker.name}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    speaker.role === 'interviewer' 
                      ? 'bg-blue-100 text-blue-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {speaker.role}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="text-center p-2 bg-blue-50 rounded">
                    <div className="font-semibold text-blue-600">{speaker.questions}</div>
                    <div className="text-gray-600">Questions</div>
                  </div>
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="font-semibold text-green-600">{speaker.statements}</div>
                    <div className="text-gray-600">Statements</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Leading Questions & Bias Detection */}
      {Object.keys(leadingQuestions).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Leading Questions & Bias</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(leadingQuestions).map(([speaker, data]) => {
              const safeData = data || {};
              const biasScore = Math.round((safeData.bias_score || 0) * 100);
              return (
                <div key={speaker} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-sm">{speaker}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      safeData.bias_level === 'high' 
                        ? 'bg-red-100 text-red-800'
                        : safeData.bias_level === 'moderate' 
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {safeData.bias_level || 'low'} bias
                    </span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total questions:</span>
                      <span className="font-medium">{safeData.total_questions || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Leading questions:</span>
                      <span className="font-medium text-red-600">{safeData.leading_questions || 0}</span>
                    </div>
                    <div className="pt-2">
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-600">Bias score:</span>
                        <span className="font-medium">{biasScore}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            biasScore > 30 ? 'bg-red-500' :
                            biasScore > 10 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${biasScore || 0}%` }} // Ensured style is an object
                        />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Sentiment Analysis */}
      {Object.keys(sentimentAnalysis).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Sentiment Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(sentimentAnalysis).map(([speaker, data]) => {
              const safeData = data || {};
              const sentiment = safeData.overall_sentiment || {};
              const label = safeData.sentiment_label || 'unknown';
              
              return (
                <div key={speaker} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-sm">{speaker}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      label === 'positive' 
                        ? 'bg-green-100 text-green-800'
                        : label === 'negative'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {label}
                    </span>
                  </div>
                  
                  {sentiment.positive !== undefined ? (
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Positive:</span>
                        <span className="font-medium text-green-600">{Math.round((sentiment.positive || 0) * 100)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Negative:</span>
                        <span className="font-medium text-red-600">{Math.round((sentiment.negative || 0) * 100)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Neutral:</span>
                        <span className="font-medium text-gray-600">{Math.round((sentiment.neutral || 0) * 100)}%</span>
                      </div>
                    </div>
                  ) : sentiment.polarity !== undefined ? (
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Polarity:</span>
                        <span className="font-medium">{sentiment.polarity}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Subjectivity:</span>
                        <span className="font-medium">{sentiment.subjectivity}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500">{safeData.error || 'No sentiment data'}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Agreement/Disagreement Analysis */}
      {Object.keys(agreementAnalysis).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Agreement & Disagreement</h3>
          <div className="mb-6">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={agreementData}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value, name) => [value, name === 'agreements' ? 'Agreements' : 'Disagreements']}
                />
                <Bar dataKey="agreements" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="disagreements" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agreementData.map((speaker) => (
              <div key={speaker.name} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-sm">{speaker.name}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    speaker.style.communicationStyle === 'confrontational' 
                      ? 'bg-red-100 text-red-800'
                      : speaker.style.communicationStyle === 'questioning'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {speaker.style.communicationStyle}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="text-center p-2 bg-green-50 rounded">
                    <div className="font-semibold text-green-600">{speaker.agreements}</div>
                    <div className="text-gray-600">Agrees</div>
                  </div>
                  <div className="text-center p-2 bg-red-50 rounded">
                    <div className="font-semibold text-red-600">{speaker.disagreements}</div>
                    <div className="text-gray-600">Disagrees</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interruption Analysis */}
      {interruptions?.total_interruptions > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Interruption Analysis</h3>
          <div className="mb-4 p-4 bg-orange-50 rounded-lg">
            <p className="text-sm font-medium text-orange-800">
              Total interruptions detected: {interruptions.total_interruptions}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(interruptions.speaker_stats || {}).map(([speaker, stats]) => {
              const dominanceScore = Math.round((stats.dominance_score || 0) * 100);
              return (
                <div key={speaker} className="border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-sm mb-3">{speaker}</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Interruptions made:</span>
                      <span className="font-medium text-red-600">{stats.interruptions_made || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Was interrupted:</span>
                      <span className="font-medium text-blue-600">{stats.interrupted_by_others || 0}</span>
                    </div>
                    <div className="pt-2">
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-600">Dominance:</span>
                        <span className="font-medium">{dominanceScore}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            dominanceScore > 70 ? 'bg-red-500' :
                            dominanceScore > 40 ? 'bg-yellow-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${dominanceScore || 0}%` }} // Ensured style is an object
                        />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}