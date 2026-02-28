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

  /* =========================
     EMOTION → PIE DATA
  ========================== */

  const emotionDistribution =
    results.emotion?.emotion_distribution || {};

  const pieData = Object.entries(emotionDistribution).map(
    ([emotion, value]) => ({
      name: emotion,
      value: Number((value * 100).toFixed(1)),
    })
  );

  /* =========================
     SPEAKER → BAR DATA
  ========================== */

  const speakerMetrics =
    results.speaker_metrics?.speakers || {};

  const barData = Object.entries(speakerMetrics).map(
    ([speaker, metrics]) => ({
      name: speaker,
      value: metrics.speaking_time_seconds,
    })
  );

  /* =========================
     DOMINANCE CALCULATION
  ========================== */

  const totalSpeakingTime = barData.reduce(
    (sum, s) => sum + s.value,
    0
  );

  const maxSpeakerTime =
    barData.length > 0
      ? Math.max(...barData.map((s) => s.value))
      : 0;

  const dominancePercent = totalSpeakingTime
    ? Math.round((maxSpeakerTime / totalSpeakingTime) * 100)
    : 0;

  /* =========================
     KPI CALCULATIONS
  ========================== */

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

  /* =========================
     FILE NAME (IF AVAILABLE)
  ========================== */

  const fileName =
    data.filename ||
    data.job_id ||
    'analysed Audio';

  /* =========================
     RENDER
  ========================== */

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-10">
      <div className="grid grid-cols-12 gap-6">

        {/* HEADER / BIAS OVERVIEW */}
        <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center">
            <div>
              <h2 className="text-xl font-semibold">
                {fileName}
              </h2>
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
                  style={{ width: `${dominancePercent}%` }}
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
            <p className="text-2xl font-semibold mt-2">
              {item.value}
            </p>
          </div>
        ))}

        {/* EMOTION PIE */}
        <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-medium mb-6">
            Emotion Distribution
          </h3>

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
                      fill={
                        COLORS[index % COLORS.length]
                      }
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
                <Bar
                  dataKey="value"
                  fill="#2563eb"
                  radius={[4, 4, 0, 0]}
                />
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
          <h3 className="text-base font-medium mb-6">
            Topics
          </h3>

          {results.topics?.keywords?.length ? (
            <div className="flex flex-wrap gap-2">
              {results.topics.keywords.map(
                (keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-sm rounded-full border"
                  >
                    {keyword}
                  </span>
                )
              )}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">
              No topic data available.
            </p>
          )}
        </div>

      </div>
    </div>
  );
}