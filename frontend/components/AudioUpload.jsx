'use client';

import { useState } from 'react';
import { uploadAudio } from '@/lib/api';
import AnalysisProgress from './AnalysisProgress';

export default function AudioUpload() {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select an audio file');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await uploadAudio(file, title);
      setResult(response);
      
      // Reset form
      setFile(null);
      setTitle('');
      e.target.reset();
      
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-2 text-gray-800">
          🎤 SpeakSense Upload
        </h1>
        <p className="text-gray-600 mb-6">
          Upload an audio file for speech analysis
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Audio File *
            </label>
            <input
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                cursor-pointer"
              disabled={uploading}
            />
            {file && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Title Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title (optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="My Recording"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg
                focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploading}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!file || uploading}
            className={`w-full py-3 px-4 rounded-lg font-semibold text-white
              transition-colors duration-200
              ${!file || uploading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
              }`}
          >
            {uploading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Uploading...
              </span>
            ) : (
              'Upload Audio'
            )}
          </button>
        </form>

        {/* Success Message */}
        {result && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="text-lg font-semibold text-green-800 mb-2">
              ✅ Upload Successful!
            </h3>
            <div className="text-sm text-green-700 space-y-1">
              <p><strong>Filename:</strong> {result.filename}</p>
              <p><strong>Size:</strong> {result.size}</p>
            </div>
          </div>
        )}

        {/* Analysis Progress - Show if we have a job_id */}
        {result?.job_id && (
          <AnalysisProgress jobId={result.job_id} />
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="text-lg font-semibold text-red-800 mb-2">
              ❌ Upload Failed
            </h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
