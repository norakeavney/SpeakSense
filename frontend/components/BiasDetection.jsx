'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LineChart, Line, CartesianGrid, Legend } from 'recharts';

export default function BiasDetection({ biasAnalysis = {} }) {
  if (!biasAnalysis || !biasAnalysis.overall_bias_score) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-xl font-semibold mb-4">Bias Detection Analysis</h3>
        <p className="text-gray-400 text-sm">No bias analysis data available.</p>
      </div>
    );
  }

  const {
    overall_bias_score,
    bias_level,
    bias_description,
    bias_factors,
    moderator,
    candidates,
    time_distribution,
    question_distribution,
    fairness_metrics,
  } = biasAnalysis;

  // Color coding for bias levels
  const biasColors = {
    'MINIMAL': { bg: '#d1fae5', border: '#6ee7b7', text: '#059669', score: '#10b981' },
    'LOW': { bg: '#dbeafe', border: '#93c5fd', text: '#2563eb', score: '#3b82f6' },
    'MODERATE': { bg: '#fef3c7', border: '#fcd34d', text: '#d97706', score: '#f59e0b' },
    'HIGH': { bg: '#fed7aa', border: '#fdba74', text: '#c2410c', score: '#f97316' },
    'SEVERE': { bg: '#fecaca', border: '#fca5a5', text: '#b91c1c', score: '#ef4444' }
  };

  const colorScheme = biasColors[bias_level] || biasColors['MODERATE'];

  // Prepare chart data
  const timeDistributionData = Object.entries(time_distribution || {}).map(([speaker, percentage]) => ({
    name: speaker.replace('_', ' '),
    value: percentage,
    color: '#3b82f6'
  }));

  const questionDistributionData = Object.entries(question_distribution || {}).map(([speaker, percentage]) => ({
    name: speaker.replace('_', ' '),
    value: percentage,
    color: '#10b981'
  }));

  const candidateMetrics = candidates ? Object.values(candidates) : [];

  return (
    <div className="space-y-6">
      {/* Overall Bias Score Card */}
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
        <div className="p-8" style={{ backgroundColor: colorScheme.bg, borderBottom: `3px solid ${colorScheme.border}` }}>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-2xl font-bold mb-2" style={{ color: colorScheme.text }}>
                Bias Score: {overall_bias_score}%
              </h3>
              <p className="text-lg font-semibold mb-4" style={{ color: colorScheme.text }}>
                {bias_level} BIAS DETECTED
              </p>
              <p className="text-sm text-gray-700 max-w-2xl leading-relaxed">
                {bias_description}
              </p>
            </div>
            <div
              className="w-32 h-32 rounded-full flex items-center justify-center text-4xl font-bold"
              style={{ backgroundColor: `${colorScheme.score}30`, color: colorScheme.score }}
            >
              {overall_bias_score}
            </div>
          </div>

          {/* Bias Factors Breakdown */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t" style={{ borderTopColor: colorScheme.border }}>
            <div>
              <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Time Variance</p>
              <p className="text-2xl font-bold" style={{ color: colorScheme.score }}>
                {((bias_factors?.speaking_time_variance || 0) * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Question Variance</p>
              <p className="text-2xl font-bold" style={{ color: colorScheme.score }}>
                {((bias_factors?.question_distribution_variance || 0) * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Moderator Sentiment</p>
              <p className="text-2xl font-bold" style={{ color: colorScheme.score }}>
                {(bias_factors?.moderator_sentiment_bias || 0).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 uppercase font-semibold mb-2">Leading Questions</p>
              <p className="text-2xl font-bold" style={{ color: colorScheme.score }}>
                {((bias_factors?.leading_questions_ratio || 0) * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Moderator Profile */}
      {moderator && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h4 className="text-lg font-semibold mb-4">Moderator Profile</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-xs text-gray-600 uppercase mb-2">Name</p>
              <p className="text-lg font-semibold">{moderator.speaker.replace('_', ' ')}</p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-xs text-gray-600 uppercase mb-2">Speaking Time</p>
              <p className="text-lg font-semibold">{Math.round(moderator.speaking_time)}s</p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-xs text-gray-600 uppercase mb-2">Questions Asked</p>
              <p className="text-lg font-semibold">{moderator.questions_asked}</p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-xs text-gray-600 uppercase mb-2">Leading Questions</p>
              <p className="text-lg font-semibold text-red-600">{moderator.leading_questions_count} ({(moderator.leading_questions_ratio * 100).toFixed(0)}%)</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm text-gray-600 mb-2">Moderator Sentiment</p>
            <div className="flex items-center">
              <div
                className="px-3 py-1 rounded-full text-xs font-semibold"
                style={{
                  backgroundColor: moderator.sentiment_score > 0.1 ? '#d1fae5' : moderator.sentiment_score < -0.1 ? '#fee2e2' : '#f3f4f6',
                  color: moderator.sentiment_score > 0.1 ? '#065f46' : moderator.sentiment_score < -0.1 ? '#7f1d1d' : '#374151'
                }}
              >
                {moderator.sentiment_label.toUpperCase()} ({moderator.sentiment_score.toFixed(2)})
              </div>
              <p className="text-xs text-gray-600 ml-3">
                {moderator.sentiment_score > 0.1 ? 'Moderator expressed positive sentiment' : moderator.sentiment_score < -0.1 ? 'Moderator expressed negative sentiment' : 'Moderator maintained neutral tone'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Speaking Time Distribution */}
      {timeDistributionData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h4 className="text-lg font-semibold mb-4">Speaking Time Distribution (%)</h4>
            {fairness_metrics && (
              <p className="text-xs text-gray-600 mb-4">
                Balance: {(fairness_metrics.time_balance * 100).toFixed(0)}% balanced | Spread: {fairness_metrics.time_spread_percent}%
              </p>
            )}
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={timeDistributionData} layout="vertical">
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => `${value}%`} />
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 8, 8, 0]}>
                  {timeDistributionData.map((entry, index) => (
                    <Cell key={`time-${index}`} fill="#3b82f6" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Questions Distribution */}
          {questionDistributionData.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h4 className="text-lg font-semibold mb-4">Questions Asked Distribution (%)</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={questionDistributionData} layout="vertical">
                  <XAxis type="number" />
                  <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Bar dataKey="value" fill="#10b981" radius={[0, 8, 8, 0]}>
                    {questionDistributionData.map((entry, index) => (
                      <Cell key={`question-${index}`} fill="#10b981" />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Candidate Analysis */}
      {candidateMetrics.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h4 className="text-lg font-semibold mb-4">Candidate Fairness Metrics</h4>
          <div className="space-y-4">
            {candidateMetrics.map((candidate) => (
              <div key={candidate.speaker} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <h5 className="font-semibold text-lg">{candidate.speaker.replace('_', ' ')}</h5>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    candidate.sentiment_score > 0.1 ? 'bg-green-100 text-green-800' :
                    candidate.sentiment_score < -0.1 ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {candidate.sentiment_label.toUpperCase()}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-600">Speaking Time</p>
                    <p className="font-semibold">{Math.round(candidate.speaking_time)}s</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Total Words</p>
                    <p className="font-semibold">{candidate.words}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Questions Asked</p>
                    <p className="font-semibold">{candidate.questions_asked}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Interruptions Made</p>
                    <p className="font-semibold text-orange-600">{candidate.interruptions_made}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Times Interrupted</p>
                    <p className="font-semibold text-orange-600">{candidate.interrupted_count}</p>
                  </div>
                </div>

                {/* Sentiment bar */}
                <div>
                  <p className="text-xs text-gray-600 mb-2">Sentiment Bias Indicator</p>
                  <div className="relative w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        candidate.sentiment_score > 0.1 ? 'bg-green-500' :
                        candidate.sentiment_score < -0.1 ? 'bg-red-500' :
                        'bg-yellow-500'
                      }`}
                      style={{ width: `${Math.abs(candidate.sentiment_score) * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{candidate.sentiment_score.toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Findings */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h4 className="font-semibold text-blue-900 mb-3">Key Findings</h4>
        <ul className="space-y-2 text-sm text-blue-800">
          {fairness_metrics?.time_spread_percent > 0 && (
            <li>• Speaking time spread: {fairness_metrics.time_spread_percent}% (higher = more unequal)</li>
          )}
          {fairness_metrics?.time_most_given_to && (
            <li>• Most speaking time given to: <strong>{fairness_metrics.time_most_given_to.replace('_', ' ')}</strong></li>
          )}
          {fairness_metrics?.time_least_given_to && (
            <li>• Least speaking time given to: <strong>{fairness_metrics.time_least_given_to.replace('_', ' ')}</strong></li>
          )}
          {moderator?.leading_questions_count > 0 && (
            <li>• {moderator.leading_questions_count} leading questions detected ({(moderator.leading_questions_ratio * 100).toFixed(0)}% of all questions)</li>
          )}
          {overall_bias_score >= 50 && (
            <li className="text-red-700 font-semibold">⚠️ Significant bias indicators present - recommend detailed review</li>
          )}
        </ul>
      </div>
    </div>
  );
}
