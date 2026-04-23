/** Frontend API helpers (JWT auth + endpoints) */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const getAuthToken = () => {
  if (typeof window !== 'undefined') return localStorage.getItem('access_token');
  return null;
};

const setTokens = (accessToken, refreshToken) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }
};

const clearTokens = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};

const authenticatedFetch = async (url, options = {}) => {
  const token = getAuthToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let response = await fetch(url, { ...options, headers });

  // Try refresh on 401
  if (response.status === 401 && token) {
    const refreshed = await refreshToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${getAuthToken()}`;
      response = await fetch(url, { ...options, headers });
    }
  }

  return response;
};

const refreshToken = async () => {
  const refresh = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
  if (!refresh) {
    clearTokens();
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });

    if (response.ok) {
      const data = await response.json();
      setTokens(data.access, refresh);
      return true;
    }

    clearTokens();
    return false;
  } catch (err) {
    clearTokens();
    return false;
  }
};

// --- Authentication API ---

// Register a new user and persist returned tokens
export const register = async (userData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });

    const data = await response.json();
    if (response.ok) {
      setTokens(data.tokens.access, data.tokens.refresh);
      return { success: true, user: data.user };
    }

    return { success: false, errors: data };
  } catch (err) {
    return { success: false, errors: { detail: 'Network error' } };
  }
};

// Authenticate user and persist access/refresh tokens
export const login = async (credentials) => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    const data = await response.json();
    if (response.ok) {
      setTokens(data.tokens.access, data.tokens.refresh);
      return { success: true, user: data.user };
    }

    return { success: false, errors: data };
  } catch (err) {
    return { success: false, errors: { detail: 'Network error' } };
  }
};

// Logout (server request) and clear local tokens
export const logout = async () => {
  try {
    await authenticatedFetch(`${API_BASE_URL}/auth/logout/`, { method: 'POST' });
  } catch (err) {
    clearTokens();
  } finally {
    clearTokens();
  }
};

// Fetch authenticated user's profile
export const getUserProfile = async () => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/auth/profile/`);
    if (response.ok) return await response.json();
    throw new Error('Failed to fetch profile');
  } catch (err) {
    throw err;
  }
};

// Check whether an access token is present
export const isAuthenticated = () => !!getAuthToken();

// --- User reports ---

// Get the current user's analysis reports
export const getUserReports = async () => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/user/reports/`);
    if (response.ok) return await response.json();
    throw new Error('Failed to fetch reports');
  } catch (err) {
    throw err;
  }
};

// Get detailed data for a single report
export const getReportDetail = async (jobId) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/user/reports/${jobId}/`);
    if (response.ok) return await response.json();
    throw new Error('Failed to fetch report details');
  } catch (err) {
    throw err;
  }
};

// Delete a user report by job id
export const deleteReport = async (jobId) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/user/reports/${jobId}/delete/`, { method: 'DELETE' });
    if (response.ok) return await response.json();
    throw new Error('Failed to delete report');
  } catch (err) {
    throw err;
  }
};

// Update metadata (title/filename) for a report
export const renameReport = async (jobId, payload) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/user/reports/${jobId}/rename/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });

    if (response.ok) return await response.json();

    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to rename report');
  } catch (err) {
    throw err;
  }
};

/**
 * Upload audio file or YouTube URL.
 * - If `input` is a File, posts `audio_file`.
 * - Otherwise posts `youtube_url`.
 */
// Upload an audio file or a YouTube URL for analysis
export const uploadAudio = async (input, title = '') => {
  const formData = new FormData();
  if (input instanceof File) formData.append('audio_file', input);
  else formData.append('youtube_url', input);
  if (title) formData.append('title', title);

  try {
    const token = getAuthToken();
    if (!token) throw new Error('Authentication required');

    const response = await fetch(`${API_BASE_URL}/upload/`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Upload failed');
    }

    return await response.json();
  } catch (err) {
    throw err;
  }
};

// Fetch an analysis job's status and results
export const getAnalysisStatus = async (jobId) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/analysis/${jobId}/status/`);
    if (response.ok) return await response.json();
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch analysis status');
  } catch (err) {
    throw err;
  }
};

// Confirm or set speaker name mappings for a job
export const confirmSpeakers = async (jobId, speakers) => {
  try {
    const response = await authenticatedFetch(`${API_BASE_URL}/analysis/${jobId}/speakers/confirm/`, {
      method: 'POST',
      body: JSON.stringify({ speakers }),
    });
    if (response.ok) return await response.json();
    const error = await response.json();
    throw new Error(error.error || 'Failed to confirm speakers');
  } catch (err) {
    throw err;
  }
};

// Public health check endpoint
export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health/`);
    return await response.json();
  } catch (err) {
    throw err;
  }
};

// Public API information endpoint
export const getApiInfo = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/info/`);
    return await response.json();
  } catch (err) {
    throw err;
  }
};
