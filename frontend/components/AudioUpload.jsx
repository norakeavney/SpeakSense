'use client';

import { useState } from 'react';
import { uploadAudio } from '@/lib/api';
import { Tab } from '@headlessui/react';

export default function AudioUpload({ onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [url, setUrl] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles && droppedFiles.length > 0) {
      const selectedFile = droppedFiles[0];
      if (selectedFile.type.startsWith('audio/') || selectedFile.type.startsWith('video/')) {
        setFile(selectedFile);
        setError(null);
        setResult(null);
      } else {
        setError('Please drop an audio or video file');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file && !url) {
      setError('Please select a file or provide a YouTube URL');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = file
        ? await uploadAudio(file, title)
        : await uploadAudio(url, title);

      setResult(response);

      if (onUploadComplete) {
        onUploadComplete(response);
      }

      setFile(null);
      setUrl('');
      setTitle('');
      e.target.reset();
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto px-6 py-10">
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-8">

        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          SpeakSense Upload
        </h1>

        <p className="text-gray-500 mb-8">
          Upload audio/video or paste a YouTube link for analysis
        </p>

        <Tab.Group>

          <Tab.List className="flex bg-gray-100 rounded-lg p-1 mb-6">
            <Tab
              className={({ selected }) =>
                `flex-1 rounded-md py-2 text-sm font-medium transition ${selected ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`
              }
            >
              Upload File
            </Tab>

            <Tab
              className={({ selected }) =>
                `flex-1 rounded-md py-2 text-sm font-medium transition ${selected ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'}`
              }
            >
              YouTube URL
            </Tab>
          </Tab.List>

          <Tab.Panels>

            // File upload panel
            <Tab.Panel>

              <form onSubmit={handleSubmit} className="space-y-6">

                <div>

                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Audio or Video
                  </label>

                  <div className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:border-blue-400 transition bg-gray-50"
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    style={{
                      borderColor: dragActive ? '#3b82f6' : '#d1d5db',
                      backgroundColor: dragActive ? '#eff6ff' : '#f9fafb'
                    }}
                  >

                    <input
                      type="file"
                      accept="audio/*,video/*"
                      onChange={handleFileChange}
                      className="hidden"
                      id="file-upload"
                      disabled={uploading}
                    />

                    <label htmlFor="file-upload" className="cursor-pointer">

                      <div className="flex flex-col items-center gap-2">

                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="w-10 h-10 text-gray-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6H16a4 4 0 010 8h-1"
                          />
                        </svg>

                        <p className="text-gray-600 font-medium">
                          {dragActive ? 'Drop your file here' : 'Drag & drop your file here'}
                        </p>

                        <p className="text-xs text-gray-400">
                          or click to browse
                        </p>

                      </div>

                    </label>

                  </div>

                  {file && (
                    <p className="mt-3 text-sm text-gray-600">
                      {file.name} · {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  )}

                </div>

                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Optional title"
                  className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />

                <button
                  type="submit"
                  disabled={!file || uploading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium transition disabled:opacity-50"
                >
                  {uploading ? 'Uploading...' : 'Analyze Audio'}
                </button>

              </form>

            </Tab.Panel>


            // YouTube panel
            <Tab.Panel>

              <form onSubmit={handleSubmit} className="space-y-6">

                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://youtube.com/watch?v=..."
                  className="w-full bg-gray-800 border border-gray-600 text-white rounded-lg px-4 py-3 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent font-sans"
                />

                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Optional title"
                  className="w-full bg-gray-800 border border-gray-600 text-white rounded-lg px-4 py-3 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent font-sans"
                />

                <button
                  type="submit"
                  disabled={!url || uploading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium transition disabled:opacity-50"
                >
                  {uploading ? 'Processing...' : 'Analyze Video'}
                </button>

              </form>

            </Tab.Panel>

          </Tab.Panels>

        </Tab.Group>


        {result && (
          <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
            <strong>Upload successful</strong>
            <div>{result.filename}</div>
          </div>
        )}

        {error && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-800">
            {error}
          </div>
        )}

      </div>
    </div>
  );
}