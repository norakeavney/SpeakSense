import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"];

export default function SpeakerAnalysis({ results }) {
  const speakerMetrics = results?.speaker_metrics || {};
  const questionsAnalysis = speakerMetrics?.questions_analysis || {};
  const agreementAnalysis = speakerMetrics?.agreement_analysis || {};
  const sentimentAnalysis = speakerMetrics?.sentiment_analysis || {};
  const leadingQuestions = speakerMetrics?.leading_questions || {};
  const interruptions = speakerMetrics?.interruptions || {};

  // Check if we have any analysis data
  const hasQuestionsData = Object.keys(questionsAnalysis).length > 0;
  const hasAgreementData = Object.keys(agreementAnalysis).length > 0;
  const hasSentimentData = Object.keys(sentimentAnalysis).length > 0;
  const hasLeadingQuestionsData = Object.keys(leadingQuestions).length > 0;
  const hasInterruptionData = interruptions?.total_interruptions > 0;

  if (!speakerMetrics || !Object.keys(speakerMetrics).length) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold mb-4">Enhanced Speaker Analysis</h3>
        <p className="text-gray-400">No speaker analysis data available.</p>
      </div>
    );
  }

  // Safely prepare data for visualizations
  const questionData = hasQuestionsData ? Object.entries(questionsAnalysis).map(([speaker, data]) => {
    const safeData = data || {};
    return {
      name: speaker,
      questions: safeData.questions || 0,
      statements: safeData.statements || 0,
      questionRatio: Math.round((safeData.question_ratio || 0) * 100),
      role: safeData.likely_role || 'unknown'
    };
  }) : [];

  const agreementData = hasAgreementData ? Object.entries(agreementAnalysis).map(([speaker, data]) => {
    const safeData = data || {};
    return {
      name: speaker,
      agreements: safeData.agreements || 0,
      disagreements: safeData.disagreements || 0,
      confrontationScore: Math.round((safeData.confrontation_score || 0) * 100),
      style: safeData.communication_style || 'neutral'
    };
  }) : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-100 border border-blue-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Enhanced Speaker Analysis</h3>
            <p className="text-gray-600 text-sm">Comprehensive communication pattern insights</p>
          </div>
        </div>
      </div>

      {/* Questions vs Statements Analysis */}
      {hasQuestionsData && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 className="text-base font-medium text-gray-900">Questions vs Statements</h4>
          </div>
          
          <div className="space-y-6">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={questionData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value, name) => [value, name === 'questions' ? 'Questions' : 'Statements']}
                  contentStyle={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                />
                <Bar dataKey="questions" fill="#3b82f6" name="questions" radius={[4, 4, 0, 0]} />
                <Bar dataKey="statements" fill="#10b981" name="statements" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {questionData.map((speaker, index) => (
                <div key={speaker.name} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-medium text-sm text-gray-900">{speaker.name}</h5>
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
                  <div className="mt-3 text-center">
                    <div className="text-xs text-gray-500">Question Ratio</div>
                    <div className="text-lg font-bold text-gray-900">{speaker.questionRatio}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Agreement/Disagreement Analysis */}
      {hasAgreementData && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <h4 className="text-base font-medium text-gray-900">Agreement & Disagreement Patterns</h4>
          </div>
          
          <div className="space-y-6">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={agreementData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value, name) => [value, name === 'agreements' ? 'Agreements' : 'Disagreements']}
                  contentStyle={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                />
                <Bar dataKey="agreements" fill="#10b981" name="agreements" radius={[4, 4, 0, 0]} />
                <Bar dataKey="disagreements" fill="#ef4444" name="disagreements" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agreementData.map((speaker, index) => (
                <div key={speaker.name} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-medium text-sm text-gray-900">{speaker.name}</h5>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      speaker.style === 'confrontational' 
                        ? 'bg-red-100 text-red-800'
                        : speaker.style === 'questioning'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {speaker.style}
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
                  <div className="mt-3 text-center">
                    <div className="text-xs text-gray-500">Confrontation Score</div>
                    <div className="text-lg font-bold text-gray-900">{speaker.confrontationScore}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Leading Questions & Bias Detection */}
      {hasLeadingQuestionsData && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h4 className="text-base font-medium text-gray-900">Bias & Leading Questions</h4>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(leadingQuestions).map(([speaker, data], index) => {
              const safeData = data || {};
              const biasScore = Math.round((safeData.bias_score || 0) * 100);
              return (
                <div key={speaker} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-medium text-sm text-gray-900">{speaker}</h5>
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
                          className={`h-2 rounded-full transition-all duration-300 ${
                            biasScore > 30 ? 'bg-red-500' :
                            biasScore > 10 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(biasScore, 100)}%` }}
                        >
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Interruption Analysis */}
      {hasInterruptionData && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 16a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v12a2 2 0 01-2 2H8z" />
              </svg>
            </div>
            <h4 className="text-base font-medium text-gray-900">Interruption Analysis</h4>
          </div>
          
          <div className="mb-6 p-4 bg-orange-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-medium text-orange-800">
                Total interruptions detected: {interruptions.total_interruptions}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(interruptions.speaker_stats || {}).map(([speaker, stats], index) => {
              const safeStats = stats || {};
              const dominanceScore = Math.round((safeStats.dominance_score || 0) * 100);
              return (
                <div key={speaker} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <h5 className="font-medium text-sm text-gray-900 mb-3">{speaker}</h5>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Interruptions made:</span>
                      <span className="font-medium text-red-600">{safeStats.interruptions_made || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Was interrupted:</span>
                      <span className="font-medium text-blue-600">{safeStats.interrupted_by_others || 0}</span>
                    </div>
                    <div className="pt-2">
                      <div className="flex justify-between mb-1">
                        <span className="text-gray-600">Dominance:</span>
                        <span className="font-medium">{dominanceScore}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            dominanceScore > 70 ? 'bg-red-500' :
                            dominanceScore > 40 ? 'bg-yellow-500' : 'bg-blue-500'
                          }`}
                          style={{ width: `${Math.min(dominanceScore, 100)}%` }}
                        >
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Summary Card */}
      <div className="bg-gradient-to-r from-gray-50 to-slate-100 border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h4 className="text-base font-medium text-gray-900">Analysis Summary</h4>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-blue-600">{Object.keys(questionsAnalysis).length}</div>
            <div className="text-xs text-gray-600">Speakers Analyzed</div>
          </div>
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-green-600">
              {questionData.reduce((sum, s) => sum + s.questions, 0)}
            </div>
            <div className="text-xs text-gray-600">Total Questions</div>
          </div>
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-red-600">{interruptions?.total_interruptions || 0}</div>
            <div className="text-xs text-gray-600">Interruptions</div>
          </div>
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-purple-600">
              {Object.values(leadingQuestions).reduce((sum, data) => sum + (data?.leading_questions || 0), 0)}
            </div>
            <div className="text-xs text-gray-600">Leading Questions</div>
          </div>
        </div>
      </div>
    </div>
  );
}