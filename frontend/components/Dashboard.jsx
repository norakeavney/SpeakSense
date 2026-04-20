'use client';

import React, { useRef, useState, useEffect } from 'react';
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
import WordCloud from './WordCloud';
import TopicSentimentAnalysis from './TopicSentimentAnalysis';
import PerSpeakerTopics from './PerSpeakerTopics';
import BiasDetection from './BiasDetection';

const COLORS = [
  '#2563eb',
  '#16a34a',
  '#dc2626',
  '#9333ea',
  '#f59e0b',
  '#0ea5e9',
];

const TAB_COLORS = {
  overview: { bg: '#eef2ff', border: '#c7d2fe', text: '#4338ca' },
  transcript: { bg: '#f0fdf4', border: '#bbf7d0', text: '#166534' },
};

const getSpeakerTabColor = (index) => {
  const speakerColors = [
    { bg: '#e8d5f2', border: '#b39ddb', text: '#6a1b9a' },
    { bg: '#d1f2eb', border: '#80cbc4', text: '#00796b' },
    { bg: '#fff3d5', border: '#ffe082', text: '#f57f17' },
    { bg: '#fce4ec', border: '#f48fb1', text: '#c2185b' },
    { bg: '#e0f2f1', border: '#80deea', text: '#00695c' },
    { bg: '#f3e5f5', border: '#ce93d8', text: '#512da8' },
  ];
  return speakerColors[index % speakerColors.length];
};

export default function Dashboard({ data, onStartNew, autoDownloadRequested = false, onAutoDownloadHandled }) {
  const dashboardRef = useRef(null);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  
  const safeReplace = (text) => {
    if (!text) return "Unknown";
    return String(text).replace(/_/g, " ");
  };

  const filterTokens = (tokens = []) =>
    tokens
      .map((t) => String(t || '').trim().toLowerCase())
      .filter((t) => /^[a-zA-Z]+(?:\s[a-zA-Z]+){0,2}$/.test(t))
      .filter((t) => t.split(' ').every((word) => word.length >= 4));

  // Political alignment helpers
  const clamp = (value, min = -1, max = 1) => Math.min(Math.max(value, min), max);

  const getOverallAxisPosition = (oneDimensional = {}) => {
    const scores = oneDimensional?.scores || {};
    const left = Number(scores["left-wing politics"] || 0);
    const centre = Number(scores["centrist politics"] || 0);
    const right = Number(scores["right-wing politics"] || 0);

    const total = left + centre + right;
    if (!total) return 0;

    // left = -1, centre = 0, right = +1
    return clamp((right - left) / total);
  };

  const getOverallLeanLabel = (position) => {
    const abs = Math.abs(position);

    if (abs < 0.15) return "Broadly centrist";
    if (abs < 0.35) return position < 0 ? "Slightly left-leaning" : "Slightly right-leaning";
    if (abs < 0.65) return position < 0 ? "Moderately left-leaning" : "Moderately right-leaning";
    return position < 0 ? "Strongly left-leaning" : "Strongly right-leaning";
  };

  const getAxisPercentFromCentre = (position) => {
    return Math.round(Math.abs(position) * 100);
  };

  const describeEconomicAxis = (axis) => {
    if (axis == null) return "No estimate available";
    if (Math.abs(axis) < 0.2) return "Mixed / near centre";
    return axis < 0 ? "State / redistributive" : "Market / free economy";
  };

  const describeSocialAxis = (axis) => {
    if (axis == null) return "No estimate available";
    if (Math.abs(axis) < 0.2) return "Mixed / near centre";
    return axis < 0 ? "Liberal / progressive" : "Traditional / conservative";
  };

  const buildPoliticalSummary = (position, econAxis, socialAxis) => {
    return `${getOverallLeanLabel(position)}, economically ${describeEconomicAxis(econAxis).toLowerCase()}, and socially ${describeSocialAxis(socialAxis).toLowerCase()}.`;
  };

  const getGradientColor = (position) => {
    const normalized = Math.max(-1, Math.min(1, position));
    if (normalized < -0.3) {
      const intensity = (normalized + 1) / 1.7;
      return `rgb(${Math.round(37 + (intensity * 100))}, ${Math.round(99 + (intensity * 100))}, ${Math.round(235 + (intensity * 20))})`;
    } else if (normalized > 0.3) {
      const intensity = (normalized) / 1.7;
      return `rgb(${Math.round(239 + (intensity * 16))}, ${Math.round(68 + (intensity * 50))}, ${Math.round(68 + (intensity * 50))})`;
    } else {
      return '#9ca3af';
    }
  };

  const getPoliticalTraits = (position, econAxis, socialAxis) => {
    const traits = [];
    if (econAxis != null) {
      if (econAxis < -0.2) traits.push('Redistributive');
      else if (econAxis > 0.2) traits.push('Market-oriented');
      else traits.push('Mixed economy');
    }
    if (socialAxis != null) {
      if (socialAxis < -0.2) traits.push('Progressive');
      else if (socialAxis > 0.2) traits.push('Traditional');
      else traits.push('Moderate');
    }
    return traits;
  };

  if (!data || !data.results) {
    return (
      <div className="p-10 text-center text-gray-500">
        No analysis data available.
        {onStartNew && (
          <div className="mt-4">
            <button
              onClick={onStartNew}
              className="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800"
            >
              Start New Analysis
            </button>
          </div>
        )}
      </div>
    );
  }

  const results = data.results;
  const politicalData = results.political_analysis?.speakers || {};
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
  const speakers = Object.keys(speakerMetrics);
  const transcriptTurns = results.diarization?.transcript || [];
  const barData = Object.entries(speakerMetrics).map(
    ([speaker, metrics]) => ({
      name: speaker,
      value: metrics.speaking_time_seconds,
    })
  );
  const totalSpeakingTime = barData.reduce((sum, s) => sum + (s.value || 0), 0);

  const selectedSpeakerMetrics =
    activeTab !== 'overview' && activeTab !== 'transcript'
      ? speakerMetrics[activeTab]
      : null;
  const selectedSpeakerTurns =
    activeTab !== 'overview' && activeTab !== 'transcript'
      ? transcriptTurns.filter((turn) => turn.speaker === activeTab)
      : [];
  const selectedSentiment =
    activeTab !== 'overview' && activeTab !== 'transcript'
      ? results?.speaker_metrics?.sentiment_analysis?.[activeTab]
      : null;
  const selectedSpeakerEmotions =
    activeTab !== 'overview' && activeTab !== 'transcript'
      ? results?.emotion?.speakers?.[activeTab]
      : null;
  const questionsAnalysis = results?.speaker_metrics?.questions_analysis || {};

  const totalTurns = transcriptTurns.length;

  const realSpeakers = Object.entries(speakerMetrics).filter(
    ([_, s]) => (s.speaking_time_seconds || 0) > 0
  );

  // KPI CALCULATIONS
  const totalWords = realSpeakers.reduce(
    (sum, [_, s]) => sum + (s.total_words || 0),
    0
  );
  const avgWPM =
    realSpeakers.length > 0
      ? Math.round(
          realSpeakers.reduce(
            (sum, [_, s]) => sum + (s.words_per_minute || 0),
            0
          ) / realSpeakers.length
        )
      : 0;
  const speakerCount = realSpeakers.length;
  const duration =
    results.diarization?.transcript?.length > 0
      ? `${Math.round(
          results.diarization.transcript[
            results.diarization.transcript.length - 1
          ].end
        )}s`
      : 'N/A';

  // FILE NAME (IF AVAILABLE)
  const fileName =
    data.title ||
    data.audio_info?.title ||
    data.file_ref?.split('/').pop()?.split('.')[0] ||
    data.job_id?.slice(0, 8) ||
    'Analysed Audio';
  const displayName = fileName.includes('-')
    ? fileName.split('-').slice(0, 2).join(' ')
    : fileName;

  const handleDownloadPDF = () => {
    if (data?.status !== 'done') {
      alert('Report is still processing. Please wait until analysis is complete.');
      return;
    }

    setIsGeneratingPdf(true);
    window.print();
    setIsGeneratingPdf(false);
  };

  useEffect(() => {
    if (!autoDownloadRequested || isGeneratingPdf) {
      return;
    }

    const runExport = async () => {
      await handleDownloadPDF();
      if (onAutoDownloadHandled) {
        onAutoDownloadHandled();
      }
    };

    runExport();
  }, [autoDownloadRequested, isGeneratingPdf, data?.status]);

  const renderSpeakerSection = (speaker) => {
    const speakerIndex = speakers.indexOf(speaker);
    const speakerColor = getSpeakerTabColor(speakerIndex);
    const speakerMetricsForSpeaker = speakerMetrics[speaker];
    const speakerTurns = transcriptTurns.filter((turn) => turn.speaker === speaker);
    const speakerSentiment = results?.speaker_metrics?.sentiment_analysis?.[speaker];
    const speakerEmotions = results?.emotion?.speakers?.[speaker];
    const speakerQuestions = questionsAnalysis[speaker];
    const speakerTopics = results?.topics?.per_speaker_topics?.[speaker];
    const dominancePercentForSpeaker = totalSpeakingTime
      ? Math.round(((speakerMetricsForSpeaker?.speaking_time_seconds || 0) / totalSpeakingTime) * 100)
      : 0;

    return (
      <>
        <div
          className="col-span-12 bg-white rounded-xl p-6 shadow-sm"
          style={{
            border: `3px solid ${speakerColor.border}`,
          }}
        >
          <h3 className="text-base font-medium mb-4">{safeReplace(speaker || "Unknown")} Summary</h3>
          {speakerMetricsForSpeaker ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="border border-gray-200 rounded-lg p-4">
                <p className="text-xs text-gray-500">Speaking Time</p>
                <p className="text-lg font-semibold">{Math.round(speakerMetricsForSpeaker.speaking_time_seconds || 0)}s</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <p className="text-xs text-gray-500">Speaking Time Share</p>
                <p className="text-lg font-semibold">{dominancePercentForSpeaker}%</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <p className="text-xs text-gray-500">Total Words</p>
                <p className="text-lg font-semibold">{speakerMetricsForSpeaker.total_words || 0}</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <p className="text-xs text-gray-500">Words / Min</p>
                <p className="text-lg font-semibold">{Math.round(speakerMetricsForSpeaker.words_per_minute || 0)}</p>
              </div>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No speaker metrics available.</p>
          )}
        </div>

        {speakerSentiment?.overall_sentiment && (
          <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-base font-medium mb-4">Sentiment</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Positive', value: Math.round((speakerSentiment.overall_sentiment.positive || 0) * 100), color: '#10b981' },
                    { name: 'Negative', value: Math.round((speakerSentiment.overall_sentiment.negative || 0) * 100), color: '#ef4444' },
                    { name: 'Neutral', value: Math.round((speakerSentiment.overall_sentiment.neutral || 0) * 100), color: '#6b7280' },
                  ].filter(d => d.value > 0)}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={90}
                  isAnimationActive={!isGeneratingPdf}
                >
                  {[
                    { name: 'Positive', value: 0, color: '#10b981' },
                    { name: 'Negative', value: 0, color: '#ef4444' },
                    { name: 'Neutral', value: 0, color: '#6b7280' },
                  ].map((entry, index) => (
                    <Cell key={`sentiment-${speaker}-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {speakerEmotions && Object.keys(speakerEmotions).length > 0 && (
          <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-base font-medium mb-4">Emotions</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={Object.entries(speakerEmotions)
                    .map(([emotion, value]) => ({
                      name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
                      value: Math.round(Number(value) * 100),
                    }))
                    .filter(d => d.value > 0)}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={90}
                  isAnimationActive={!isGeneratingPdf}
                >
                  {['#ef4444', '#8b5cf6', '#06b6d4', '#fbbf24', '#6b7280', '#3b82f6', '#ec4899'].map((color, idx) => (
                    <Cell key={`emotion-${speaker}-${idx}`} fill={color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-medium mb-4">Topics & Keywords</h3>
          {speakerTopics?.topics?.length > 0 ? (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-600 mb-2">Main Topics</p>
              <div className="flex flex-wrap gap-2">
                {speakerTopics.topics.map((topic, idx) => (
                  <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 mb-4">No strong speaker-specific topics were extracted yet.</p>
          )}

          <p className="text-sm font-medium text-gray-600 mb-3">Keywords</p>
          {speakerTopics?.wordcloud_image ? (
            <img
              src={speakerTopics.wordcloud_image}
              alt={`${safeReplace(speaker)} topic word cloud`}
              className="w-full rounded-lg border border-gray-100"
            />
          ) : speakerTopics?.keywords?.length > 0 ? (
            <WordCloud
              words={filterTokens(speakerTopics.keywords).map((keyword) => ({
                word: keyword,
                score: speakerTopics.scores?.[keyword] || 0.5
              }))}
              height={280}
              maxWords={30}
            />
          ) : (
            <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-6 text-center">
              <p className="text-sm text-gray-500">Word cloud not available for this speaker yet.</p>
              <p className="text-xs text-gray-400 mt-1">Try a longer transcript or more speaker turns for richer topic extraction.</p>
            </div>
          )}
        </div>

        {speakerQuestions && (
          <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-base font-medium mb-4">Communication Style</h3>
            {speakerQuestions.questions + speakerQuestions.statements > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart
                    data={[
                      { name: 'Questions', value: speakerQuestions.questions, fill: '#3b82f6' },
                      { name: 'Statements', value: speakerQuestions.statements, fill: '#10b981' },
                    ]}
                  >
                    <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" isAnimationActive={!isGeneratingPdf} radius={[4, 4, 0, 0]}>
                      {[
                        { fill: '#3b82f6' },
                        { fill: '#10b981' },
                      ].map((entry, idx) => (
                        <Cell key={`comm-${speaker}-${idx}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-3 text-xs text-gray-600">
                  <p>Role: <span className="font-semibold">{speakerQuestions.likely_role || 'Unknown'}</span></p>
                </div>
              </>
            ) : (
              <p className="text-gray-400 text-sm">No communication data available.</p>
            )}
          </div>
        )}

        <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-medium mb-4">Transcript Turns</h3>
          {speakerTurns.length > 0 ? (
            <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1 print-expand">
              {speakerTurns.map((turn, index) => (
                <div key={`${speaker}-${turn.start}-${index}`} className="border border-gray-200 rounded-md p-3">
                  <p className="text-xs text-gray-500 mb-1">{Math.round(turn.start || 0)}s - {Math.round(turn.end || 0)}s</p>
                  <p className="text-sm text-gray-700">{turn.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No turns found for this speaker.</p>
          )}
        </div>
      </>
    );
  };

  // RENDER
  return (
    <>
    <div className="flex items-end gap-2 mb-6 border-b border-gray-300 no-print">

      {/* Overview */}
      <button
        onClick={() => setActiveTab("overview")}
        className={`px-5 py-2 rounded-t-xl text-sm font-medium transition-all duration-200 ${
          activeTab === "overview"
            ? `border-2 border-b-0 shadow-sm text-white`
            : "text-gray-600 hover:opacity-80 transition-opacity"
        }`}
        style={{
          backgroundColor: activeTab === "overview" ? TAB_COLORS.overview.border : TAB_COLORS.overview.bg,
          color: TAB_COLORS.overview.text,
        }}
      >
        Overview
      </button>

      {/* Transcript */}
      <button
        onClick={() => setActiveTab("transcript")}
        className={`px-5 py-2 rounded-t-xl text-sm font-medium transition-all duration-200 ${
          activeTab === "transcript"
            ? `border-2 border-b-0 shadow-sm`
            : "hover:opacity-80 transition-opacity"
        }`}
        style={{
          backgroundColor: activeTab === "transcript" ? TAB_COLORS.transcript.border : TAB_COLORS.transcript.bg,
          color: TAB_COLORS.transcript.text,
          borderColor: activeTab === "transcript" ? TAB_COLORS.transcript.border : "transparent",
        }}
      >
        Transcript
      </button>

      {/* Speakers */}
      {speakers.map((speaker, index) => {
        const speakerColor = getSpeakerTabColor(index);
        return (
          <button
            key={speaker}
            onClick={() => setActiveTab(speaker)}
            className={`px-5 py-2 rounded-t-xl text-sm font-medium transition-all duration-200 ${
              activeTab === speaker
                ? `border-2 border-b-0 shadow-sm`
                : "hover:opacity-80 transition-opacity"
            }`}
            style={{
              backgroundColor: activeTab === speaker ? speakerColor.border : speakerColor.bg,
              color: speakerColor.text,
              borderColor: activeTab === speaker ? speakerColor.border : "transparent",
            }}
          >
            {(speaker || "Unknown Speaker").replace("_", " ")}
          </button>
        );
      })}

    </div>
      <div ref={dashboardRef} className="w-full max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-12 gap-6">
        {/* HEADER / BIAS OVERVIEW */}
        <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center">
            <div>
              <h2 className="text-xl font-semibold">{displayName}</h2>
              <p className="text-sm text-gray-500 mt-1">
                Conversation Overview
              </p>
            </div>
            <div className="ml-auto flex items-center space-x-4">
              {onStartNew && (
                <button
                  onClick={onStartNew}
                  className="px-4 py-2 bg-black text-white text-sm rounded-lg hover:bg-gray-800 no-print"
                >
                  Start New Analysis
                </button>
              )}
              <button
                onClick={handleDownloadPDF}
                disabled={isGeneratingPdf}
                className="px-4 py-2 bg-gray-700 text-white text-sm rounded-lg hover:bg-gray-800 disabled:opacity-50 no-print"
              >
                {isGeneratingPdf ? 'Preparing Print...' : 'Print / Save PDF'}
              </button>
            </div>
          </div>
        </div>

        <div className={`tab-content col-span-12 ${activeTab === 'overview' ? 'block' : 'hidden'}`}>
          <div className="grid grid-cols-12 gap-6">
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
                <p className="text-sm text-gray-500 uppercase tracking-wide">{item.label}</p>
                <p className="text-2xl font-semibold mt-2">{item.value}</p>
              </div>
            ))}

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
                      isAnimationActive={!isGeneratingPdf}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-gray-400 text-sm">No emotion data available.</p>
              )}
            </div>

            <div className="col-span-12 lg:col-span-6 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-base font-medium mb-6">Speaker Activity (Speaking Time)</h3>
              {barData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={barData}>
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} isAnimationActive={!isGeneratingPdf} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-gray-400 text-sm">No speaker metrics available.</p>
              )}
            </div>

            {/* Bias Detection Box */}
            {results.speaker_metrics?.bias_analysis && (
              <div className="col-span-12">
                <BiasDetection biasAnalysis={results.speaker_metrics.bias_analysis} />
              </div>
            )}

            <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-base font-medium mb-6">Topics Word Cloud</h3>
              {results.topics?.wordcloud_image ? (
                <img
                  src={results.topics.wordcloud_image}
                  alt="Topic word cloud"
                  className="w-full rounded-lg border border-gray-100"
                />
              ) : results.topics?.keywords?.length ? (
                <WordCloud 
                  words={filterTokens(results.topics.keywords).map((keyword) => ({
                    word: keyword,
                    score: results.topics.scores?.[keyword] || 0.5
                  }))}
                  height={400}
                  maxWords={40}
                />
              ) : (
                <p className="text-gray-400 text-sm">No topic data available.</p>
              )}
            </div>

            {results.topics?.per_speaker_topics && Object.keys(results.topics.per_speaker_topics).length > 0 && (
              <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h3 className="text-base font-medium mb-6">Speaker Topics</h3>
                <PerSpeakerTopics 
                  perSpeakerTopics={results.topics.per_speaker_topics}
                  activeSpeaker={activeTab !== 'overview' && activeTab !== 'transcript' ? activeTab : null}
                  speakerColors={Object.fromEntries(
                    results.diarization?.speakers?.map((speaker, idx) => [
                      speaker,
                      getSpeakerTabColor(idx)
                    ]) || []
                  )}
                />
              </div>
            )}

            {results.topics?.topic_sentiment && Object.keys(results.topics.topic_sentiment).length > 0 && (
              <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                <h3 className="text-base font-medium mb-6">Topic Sentiment Analysis</h3>
                <TopicSentimentAnalysis 
                  topicSentiment={results.topics.topic_sentiment}
                  speakersAvailable={results.diarization?.speakers || []}
                />
              </div>
            )}

            <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-base font-medium mb-6">Political Alignment</h3>
              <p className="text-xs text-gray-500 mb-6">
                This section gives an estimated overview of each speaker's political tendency based on language patterns in the conversation.
                The top scale shows overall left–centre–right positioning, while the economic and social indicators below provide more detailed breakdowns.
              </p>
              {politicalSpeakers.length > 0 ? (
                <div className="space-y-8">
                {politicalSpeakers.map(([speaker, data], index) => {
                  const econ = data.two_dimensional?.economic;
                  const social = data.two_dimensional?.social;

                  const overallPosition = getOverallAxisPosition(data.one_dimensional);
                  const overallLabel = getOverallLeanLabel(overallPosition);
                  const overallPercent = getAxisPercentFromCentre(overallPosition);

                  // convert -1..1 to 0..100 for left-to-right positioning
                  const markerPosition = ((overallPosition + 1) / 2) * 100;

                    return (
                      <div key={index} className="border-b pb-6 last:border-none">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-lg font-semibold">{safeReplace(speaker)}</h4>
                          <span className="text-sm text-gray-600">
                            Overall: <span className="font-medium text-gray-800">{overallLabel}</span>
                          </span>
                        </div>

                        <div className="mb-5">
                          <p className="text-sm text-gray-500 mb-3">Overall Position</p>

                          <div className="relative px-2 pt-10 pb-8">
                            <div className="relative h-4 rounded-full bg-gradient-to-r from-blue-500 via-gray-300 to-red-500 overflow-visible">
                              {/* centre marker */}
                              <div className="absolute left-1/2 top-0 h-4 w-px bg-gray-600 -translate-x-1/2" />

                              {/* speaker dot */}
                              <div
                                className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
                                style={{ left: `${markerPosition}%` }}
                              >
                                <div className="absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-gray-800 px-2 py-1 text-xs font-medium text-white shadow-sm">
                                  {overallPercent}%
                                </div>
                                <div className="h-4 w-4 rounded-full border-2 border-white shadow" style={{ backgroundColor: getGradientColor(overallPosition) }} />
                              </div>
                            </div>

                            <div className="mt-3 flex justify-between text-xs text-gray-500">
                              <span>Left-wing</span>
                              <span>Centre</span>
                              <span>Right-wing</span>
                            </div>
                          </div>

                          <p className="text-sm text-gray-700">
                            <span className="font-medium">Summary:</span> {overallLabel}
                          </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-sm text-gray-500 mb-2">Economic Position</p>
                            <div className="relative h-3 rounded-full bg-gray-200">
                              <div className="absolute left-1/2 top-0 h-3 w-px bg-gray-400 -translate-x-1/2" />
                              <div
                                className="absolute top-0 h-3"
                                style={{
                                  width: `${Math.min(Math.abs(econ?.axis || 0) * 50, 50)}%`,
                                  [econ?.axis < 0 ? 'right' : 'left']: '50%',
                                  backgroundColor: getGradientColor(econ?.axis || 0),
                                }}
                              />
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                              {describeEconomicAxis(econ?.axis)}
                              <span className="ml-2">({econ?.axis?.toFixed(2)})</span>
                            </p>
                          </div>

                          <div>
                            <p className="text-sm text-gray-500 mb-2">Social Position</p>
                            <div className="relative h-3 rounded-full bg-gray-200">
                              <div className="absolute left-1/2 top-0 h-3 w-px bg-gray-400 -translate-x-1/2" />
                              <div
                                className="absolute top-0 h-3"
                                style={{
                                  width: `${Math.min(Math.abs(social?.axis || 0) * 50, 50)}%`,
                                  [social?.axis < 0 ? 'right' : 'left']: '50%',
                                  backgroundColor: getGradientColor(social?.axis || 0),
                                }}
                              />
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                              {describeSocialAxis(social?.axis)}
                              <span className="ml-2">({social?.axis?.toFixed(2)})</span>
                            </p>
                          </div>
                        </div>

                        <div className="bg-gradient-to-r from-blue-50 via-gray-50 to-red-50 border border-gray-200 rounded-lg p-3">
                          <p className="text-xs text-gray-500 mb-2 font-medium">Political Traits</p>
                          <div className="flex flex-wrap gap-2">
                            {getPoliticalTraits(overallPosition, econ?.axis, social?.axis).map((trait, idx) => (
                              <span key={idx} className="px-2 py-1 bg-white border border-gray-300 rounded-full text-xs font-medium text-gray-700">
                                {trait}
                              </span>
                            ))}
                          </div>
                        </div>

                        <p className="text-sm text-gray-700 mt-4">
                          <span className="font-medium">Summary:</span>{" "}
                          {buildPoliticalSummary(overallPosition, econ?.axis, social?.axis)}
                        </p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No political alignment data available.</p>
              )}
            </div>

            <div className="col-span-12">
              <SpeakerAnalysis results={results} />
            </div>
          </div>
        </div>

        <div className="page-break col-span-12"></div>

        <div className={`tab-content col-span-12 ${activeTab === 'transcript' ? 'block' : 'hidden'}`}>
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <h3 className="text-base font-medium mb-4">Transcript</h3>
              {transcriptTurns.length > 0 ? (
                <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1 print-expand">
                  {transcriptTurns.map((turn, index) => (
                    <div key={`${turn.speaker}-${turn.start}-${index}`} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-gray-800">{turn.speaker}</span>
                        <span className="text-xs text-gray-500">{Math.round(turn.start || 0)}s - {Math.round(turn.end || 0)}s</span>
                      </div>
                      <p className="text-sm text-gray-700">{turn.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">No transcript data available.</p>
              )}
            </div>
          </div>
        </div>

        <div className="page-break col-span-12"></div>

        {speakers.map((speaker, index) => (
          <React.Fragment key={speaker}>
            {index > 0 && <div className="page-break col-span-12"></div>}
            <div className={`tab-content col-span-12 ${activeTab === speaker ? 'block' : 'hidden'}`}>
              <div className="grid grid-cols-12 gap-6">
                {renderSpeakerSection(speaker)}
              </div>
            </div>
          </React.Fragment>
        ))}
        </div>
      </div>
    </>
  );
}
