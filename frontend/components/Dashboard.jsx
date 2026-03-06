'use client';

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import SpeakerAnalysis from './SpeakerAnalysis';

const COLORS = [
  '#2563eb',
  '#16a34a',
  '#dc2626',
  '#9333ea',
  '#f59e0b',
  '#0ea5e9',
];

export default function Dashboard({ data }) {
  if (!data || !data.results) {
    return (
      <div className="p-10 text-center text-gray-500">
        No analysis data available.
      </div>
    );
  }

  const results = data.results;

  // POLITICAL ALIGNMENT
  const politicalData = results.political_alignment?.speakers || {};
  const politicalSpeakers = Object.entries(politicalData);

  // EMOTION → PIE DATA
  const emotionDistribution = results.emotion?.emotion_distribution || {};
  const pieData = Object.entries(emotionDistribution).map(
    ([emotion, value]) => ({
      name: emotion,
      value: Number((value * 100).toFixed(1)),
    })
  );

  // SPEAKER → BAR DATA
  const speakerMetrics = results.speaker_metrics?.speakers || {};
  const barData = Object.entries(speakerMetrics).map(
    ([speaker, metrics]) => ({
      name: speaker,
      value: metrics.speaking_time_seconds,
    })
  );

  // DOMINANCE CALCULATION
  const totalSpeakingTime = barData.reduce((sum, s) => sum + s.value, 0);
  const maxSpeakerTime =
    barData.length > 0 ? Math.max(...barData.map((s) => s.value)) : 0;
  const dominancePercent = totalSpeakingTime
    ? Math.round((maxSpeakerTime / totalSpeakingTime) * 100)
    : 0;

  // KPI CALCULATIONS
  const totalWords = Object.values(speakerMetrics).reduce(
    (sum, s) => sum + (s.total_words || 0),
    0
  );
  const avgWPM =
    Object.keys(speakerMetrics).length > 0
      ? Math.round(
          Object.values(speakerMetrics).reduce(
            (sum, s) => sum + (s.words_per_minute || 0),
            0
          ) / Object.keys(speakerMetrics).length
        )
      : 0;
  const speakerCount = Object.keys(speakerMetrics).length;
  const duration =
    results.diarization?.transcript?.length > 0
      ? `${Math.round(
          results.diarization.transcript[
            results.diarization.transcript.length - 1
          ].end
        )}s`
      : 'N/A';

  // FILE NAME (IF AVAILABLE)
  const fileName = data.filename || data.job_id || 'analysed Audio';

  // RENDER
  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-10">
      <div className="grid grid-cols-12 gap-6">
        {/* HEADER / BIAS OVERVIEW */}
        <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center">
            <div>
              <h2 className="text-xl font-semibold">{fileName}</h2>
              <p className="text-sm text-gray-500 mt-1">
                Bias Index — Speaking Time Dominance
              </p>
            </div>
            <div className="ml-auto w-64">
              <p className="text-sm text-gray-500 mb-2 text-right">
                Dominance Level
              </p>
              <div className="w-full bg-gray-200 h-3 rounded-full overflow-hidden">
                <div
                  className="h-3 bg-blue-600 transition-all duration-500"
                  style={{ width: `${dominancePercent || 0}%` }}
                />
              </div>
              <p className="text-right text-sm mt-1 font-medium">
                {dominancePercent}%
              </p>
            </div>
          </div>
        </div>

        {/* KPI CARDS */}
        {[
          { label: 'Speakers', value: speakerCount },
          { label: 'Duration', value: duration },
          { label: 'Total Words', value: totalWords },
          { label: 'Avg WPM', value: avgWPM },
        ].map((item, i) => (
          <div
            key={i}
            className="col-span-12 sm:col-span-6 lg:col-span-3 bg-white border border-gray-200 rounded-xl p-6 shadow-sm"
          >
            <p className="text-sm text-gray-500 uppercase tracking-wide">
              {item.label}
            </p>
            <p className="text-2xl font-semibold mt-2">{item.value}</p>
          </div>
        ))}

        {/* EMOTION PIE */}
        <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-medium mb-6">Emotion Distribution</h3>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={110}
                >
                  {pieData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-sm">
              No emotion data available.
            </p>
          )}
        </div>

        {/* SPEAKER ACTIVITY BAR */}
        <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-medium mb-6">
            Speaker Activity (Speaking Time)
          </h3>
          {barData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={barData}>
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-400 text-sm">
              No speaker metrics available.
            </p>
          )}
        </div>

        {/* TOPICS */}
        <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-medium mb-6">Topics</h3>
          {results.topics?.keywords?.length ? (
            <div className="flex flex-wrap gap-2">
              {results.topics.keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-gray-100 text-sm rounded-full border"
                >
                  {keyword}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">
              No topic data available.
            </p>
          )}
        </div>

        {/* POLITICAL ALIGNMENT */}
        <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-medium mb-6">Political Alignment</h3>
          {politicalSpeakers.length > 0 ? (
            <div className="space-y-8">
              {politicalSpeakers.map(([speaker, data], index) => {
                const econ = data.two_dimensional?.economic;
                const social = data.two_dimensional?.social;
                const ideology = data.one_dimensional?.top_label;

                return (
                  <div key={index} className="border-b pb-6 last:border-none">
                    <div className="flex items-center mb-4">
                      <h4 className="text-lg font-semibold">{speaker}</h4>
                      {ideology && (
                        <span className="ml-4 px-3 py-1 text-xs rounded-full bg-blue-100 text-blue-700">
                          {ideology}
                        </span>
                      )}
                    </div>

                    {/* ECONOMIC AXIS */}
                    <div className="mb-4">
                      <p className="text-sm text-gray-500 mb-2">
                        Economic Axis
                      </p>
                      <div className="w-full bg-gray-200 h-3 rounded-full">
                        <div 
                          className={`h-3 rounded-full ${
                            econ?.axis >= 0 ? 'bg-red-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.abs(social?.axis || 0) * 50}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {econ?.axis < 0
                          ? 'Progressive'
                          : econ?.axis > 0
                          ? 'Conservative'
                          : 'Neutral'}
                      </p>
                    </div>

                    {/* SOCIAL AXIS */}
                    <div>
                      <p className="text-sm text-gray-500 mb-2">
                        Social Axis
                      </p>
                      <div className="relative w-full bg-gray-200 h-3 rounded-full overflow-hidden">
                        <div
                          className={`absolute top-0 h-3 ${
                            social?.axis >= 0 ? 'bg-red-500' : 'bg-blue-500'
                          }`}
                          style={{
                            width: `${Math.min(Math.max(Math.abs(social?.axis || 0) * 100, 0), 100)}%`,
                            [social?.axis < 0 ? 'left' : 'right']: '50%',
                          }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {social?.axis < 0
                          ? 'Liberal'
                          : social?.axis > 0
                          ? 'Conservative'
                          : 'Neutral'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">
              No political alignment data available.
            </p>
          )}
        </div>

        {/* ENHANCED SPEAKER ANALYSIS */}
        <div className="col-span-12">
          <SpeakerAnalysis results={results} />
        </div>
      </div>
    </div>
  );
}
