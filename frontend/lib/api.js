/**
 * API Service for SpeakSense Backend
 * Handles all communication with Django REST API with JWT authentication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

// ============================================
// AUTHENTICATION HELPERS
// ============================================

/**
 * Get JWT token from localStorage
 */
const getAuthToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

/**
 * Set tokens in localStorage
 */
const setTokens = (accessToken, refreshToken) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }
};

/**
 * Clear tokens from localStorage
 */
const clearTokens = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};

/**
 * Make authenticated API request with automatic token refresh
 */
const authenticatedFetch = async (url, options = {}) => {
  const token = getAuthToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(url, {
    ...options,
    headers,
  });

  // If token expired, try to refresh
  if (response.status === 401 && token) {
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry with new token
      headers['Authorization'] = `Bearer ${getAuthToken()}`;
      response = await fetch(url, {
        ...options,
        headers,
      });
    }
  }

  return response;
};

/**
 * Refresh JWT token
 */
const refreshToken = async () => {
  const refresh = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
  
  if (!refresh) {
    clearTokens();
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh: refresh,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      setTokens(data.access, refresh);
      return true;
    } else {
      clearTokens();
      return false;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
    clearTokens();
    return false;
  }
};

// ============================================
// AUTHENTICATION API
// ============================================

/**
 * User registration
 */
export const register = async (userData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();

    if (response.ok) {
      setTokens(data.tokens.access, data.tokens.refresh);
      return { success: true, user: data.user };
    } else {
      return { success: false, errors: data };
    }
  } catch (error) {
    console.error('Registration error:', error);
    return { success: false, errors: { detail: 'Network error' } };
  }
};

/**
 * User login
 */
export const login = async (credentials) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    const data = await response.json();

    if (response.ok) {
      setTokens(data.tokens.access, data.tokens.refresh);
      return { success: true, user: data.user };
    } else {
      return { success: false, errors: data };
    }
  } catch (error) {
    console.error('Login error:', error);
    return { success: false, errors: { detail: 'Network error' } };
  }
};

/**
 * User logout
 */
export const logout = async () => {
  try {
    await authenticatedFetch(`${API_BASE_URL}/auth/logout/`, {
      method: 'POST',
    });
  } catch (error) {
    console.error('Logout error:', error);
  } finally {
    clearTokens();
  }
};

/**
 * Get user profile
 */
export const getUserProfile = async () => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/auth/profile/`);
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch profile');
    }
  } catch (error) {
    console.error('Profile fetch error:', error);
    throw error;
  }
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  return !!getAuthToken();
};

// ============================================
// USER REPORTS API  
// ============================================

/**
 * Get user's analysis reports
 */
export const getUserReports = async () => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/user/reports/`);
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch reports');
    }
  } catch (error) {
    console.error('Reports fetch error:', error);
    throw error;
  }
};

/**
 * Get specific report details
 */
export const getReportDetail = async (jobId) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/user/reports/${jobId}/`);
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to fetch report details');
    }
  } catch (error) {
    console.error('Report detail fetch error:', error);
    throw error;
  }
};

/**
 * Delete user report
 */
export const deleteReport = async (jobId) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/user/reports/${jobId}/delete/`, {
      method: 'DELETE',
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Failed to delete report');
    }
  } catch (error) {
    console.error('Report delete error:', error);
    throw error;
  }
};

/**
 * Upload audio file to backend (requires authentication)
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
    const token = getAuthToken();
    
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${API_BASE_URL}/upload/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
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
 * Get analysis job status (requires authentication)
 * @param {string} jobId - Job ID to check
 * @returns {Promise<Object>} Job status and results
 */
export const getAnalysisStatus = async (jobId) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/analysis/${jobId}/status/`);
    
    if (response.ok) {
      return await response.json();
    } else {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch analysis status');
    }
  } catch (error) {
    console.error('Analysis status error:', error);
    throw error;
  }
};

/**
 * Confirm speaker names (requires authentication)
 * @param {string} jobId - Job ID
 * @param {Object} speakers - Speaker mappings {SPEAKER_00: "Name", ...}
 * @returns {Promise<Object>} Confirmation response
 */
export const confirmSpeakers = async (jobId, speakers) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/analysis/${jobId}/speakers/confirm/`, {
      method: 'POST',
      body: JSON.stringify({ speakers }),
    });
    
    if (response.ok) {
      return await response.json();
    } else {
      const error = await response.json();
      throw new Error(error.error || 'Failed to confirm speakers');
    }
  } catch (error) {
    console.error('Speaker confirmation error:', error);
    throw error;
  }
};

/**
 * Check API health status (public endpoint)
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
 * Get API information (public endpoint)
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
