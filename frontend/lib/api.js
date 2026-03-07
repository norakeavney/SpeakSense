/**
 * API Service for SpeakSense Backend
 * Handles all communication with Django REST API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

/**
 * Upload audio file to backend
 * @param {File} file - Audio file to upload
 * @param {string} title - Optional title for the audio
 * @returns {Promise<Object>} Upload response with file_id, filename, size, title
 */
export const uploadAudio = async (input, title = '') => {
  const formData = new FormData();

  // If input is a File object
  if (input instanceof File) {
    formData.append('audio_file', input);
  } else {
    // Otherwise assume it's a YouTube URL
    formData.append('youtube_url', input);
  }

  if (title) {
    formData.append('title', title);
  }

  try {
    const response = await fetch(`${API_BASE_URL}/upload/`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Upload failed');
    }

    return await response.json();

  } catch (error) {
    console.error('Upload error:', error);
    throw error;
  }
};

/**
 * Check API health status
 * @returns {Promise<Object>} Health check response
 */
export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health/`);
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

/**
 * Get API information
 * @returns {Promise<Object>} API info
 */
export const getApiInfo = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/info/`);
    return await response.json();
  } catch (error) {
    console.error('API info error:', error);
    throw error;
  }
};
