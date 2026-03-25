'use client';

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import AuthFlow from '../components/AuthFlow';
import AuthenticatedLayout from '../components/AuthenticatedLayout';
import AudioUpload from '../components/AudioUpload';
import AnalysisProgress from '../components/AnalysisProgress';
import Dashboard from '../components/Dashboard';
import UserReports from '../components/UserReports';
import Settings from '../components/Settings';

export default function HomePage() {
  const { isLoggedIn, loading } = useAuth();
  const [currentPage, setCurrentPage] = useState('upload');
  const [stage, setStage] = useState('upload');
  const [jobId, setJobId] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [autoDownloadRequested, setAutoDownloadRequested] = useState(false);

  // Handle page changes in authenticated view
  const handlePageChange = (page) => {
    setCurrentPage(page);
    // Reset upload flow state when switching pages
    if (page === 'upload') {
      setStage('upload');
      setJobId(null);
      setAnalysisData(null);
      setAutoDownloadRequested(false);
    }
  };

  // Handle selecting a report from UserReports
  const handleSelectReport = (reportData, options = {}) => {
    setAnalysisData(reportData.report);
    setAutoDownloadRequested(Boolean(options.autoDownload));
    setStage('dashboard');
    setCurrentPage('upload'); // Switch to upload page to show dashboard
  };

  // Show loading spinner during auth check
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading SpeakSense...</p>
        </div>
      </div>
    );
  }

  // Show auth flow for unauthenticated users
  if (!isLoggedIn) {
    return <AuthFlow onSuccess={() => setCurrentPage('upload')} />;
  }

  // Show authenticated interface
  return (
    <AuthenticatedLayout currentPage={currentPage} onPageChange={handlePageChange}>
      {currentPage === 'upload' && (
        <>
          {stage === 'upload' && (
            <AudioUpload
              onUploadComplete={(response) => {
                setJobId(response.job_id);
                setStage('processing');
              }}
            />
          )}

          {stage === 'processing' && (
            <AnalysisProgress
              jobId={jobId}
              onComplete={(data) => {
                console.log('ANALYSIS COMPLETE:', data);
                setAnalysisData(data);
                setStage('dashboard');
              }}
            />
          )}

          {stage === 'dashboard' && (
            <Dashboard
              data={analysisData}
              autoDownloadRequested={autoDownloadRequested}
              onAutoDownloadHandled={() => setAutoDownloadRequested(false)}
              onStartNew={() => {
                setStage('upload');
                setJobId(null);
                setAnalysisData(null);
                setAutoDownloadRequested(false);
              }}
            />
          )}
        </>
      )}

      {currentPage === 'reports' && (
        <UserReports onSelectReport={handleSelectReport} />
      )}

      {currentPage === 'settings' && (
        <Settings />
      )}
    </AuthenticatedLayout>
  );
}