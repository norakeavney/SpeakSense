'use client';

import { useState, useEffect } from 'react';
import { getUserReports, deleteReport, getReportDetail } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

const UserReports = ({ onSelectReport }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState({});
  const { user } = useAuth();

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const response = await getUserReports();
      setReports(response.reports || []);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setError('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async (jobId) => {
    if (!confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
      return;
    }

    try {
      setDeleteLoading(prev => ({ ...prev, [jobId]: true }));
      await deleteReport(jobId);
      setReports(prev => prev.filter(report => report.job_id !== jobId));
    } catch (error) {
      console.error('Error deleting report:', error);
      alert('Failed to delete report');
    } finally {
      setDeleteLoading(prev => ({ ...prev, [jobId]: false }));
    }
  };

  const handleViewReport = async (jobId) => {
    try {
      const reportData = await getReportDetail(jobId);
      onSelectReport(reportData);
    } catch (error) {
      console.error('Error fetching report details:', error);
      alert('Failed to load report details');
    }
  };

  const formatStatus = (status) => {
    const statusMap = {
      'queued': { label: 'Queued', color: 'bg-yellow-100 text-yellow-800' },
      'processing': { label: 'Processing', color: 'bg-blue-100 text-blue-800' },
      'done': { label: 'Complete', color: 'bg-green-100 text-green-800' },
      'failed': { label: 'Failed', color: 'bg-red-100 text-red-800' }
    };
    
    return statusMap[status] || { label: status, color: 'bg-gray-100 text-gray-800' };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading your reports...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchReports}
          className="mt-2 px-4 py-2 bg-black text-white rounded hover:bg-gray-800"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Your Reports</h2>
        <p className="text-gray-600">{reports.length} total reports</p>
      </div>

      {reports.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No reports yet</h3>
          <p className="text-gray-600">Upload your first audio file to start analyzing speech patterns</p>
        </div>
      ) : (
        <div className="bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            {reports.map((report) => {
              const statusInfo = formatStatus(report.status);
              
              return (
                <li key={report.job_id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-lg font-medium text-gray-900 truncate">
                          {report.audio_info?.title || 'Untitled'}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                      </div>
                      
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        <span>{report.audio_info?.filename || 'Unknown file'}</span>
                        <span>{formatFileSize(report.audio_info?.size)}</span>
                        <span>Created {formatDate(report.created_at)}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      {report.status === 'done' && (
                        <button
                          onClick={() => handleViewReport(report.job_id)}
                          className="px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800"
                        >
                          View Results
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDeleteReport(report.job_id)}
                        disabled={deleteLoading[report.job_id]}
                        className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                      >
                        {deleteLoading[report.job_id] ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
};

export default UserReports;