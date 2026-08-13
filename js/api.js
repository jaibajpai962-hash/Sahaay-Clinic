/**
 * ============================================================
 * FILE: js/api.js  —  Sahaay Clinic API Communication Layer
 * ============================================================
 * All fetch() calls to the Flask backend go here.
 * Routes are RELATIVE (/api/v1/...) — no hardcoded domains.
 * All responses are expected in JSON format.
 * ============================================================
 */

const API_BASE = '/api/v1';
const REQUEST_TIMEOUT_MS = 25000; // 25 seconds
const AUTH_REFRESH_SKEW_MS = 60 * 1000;

// ----------------------------------------------------------
// TOKEN HELPERS — retrieve JWT stored in IndexedDB session
// ----------------------------------------------------------
async function _getAuthToken() {
  try {
    if (typeof getSession !== 'function') return null;
    const session = await getSession();
    if (!session || !session.token || session.token === 'demo') return null;

    // If we know the access-token expiry, refresh it before it expires.
    if (session.accessTokenExpiresAt && Date.now() + AUTH_REFRESH_SKEW_MS >= session.accessTokenExpiresAt && session.refreshToken) {
      const refreshed = await _refreshAccessToken(session.refreshToken);
      if (refreshed) return refreshed;
    }
    return session.token;
  } catch (e) {
    return null;
  }
}

async function _refreshAccessToken(refreshToken) {
  try {
    const response = await fetch(API_BASE + '/auth/refresh', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${refreshToken}`, 'Accept': 'application/json' },
      signal: AbortSignal.timeout ? AbortSignal.timeout(10000) : undefined
    });
    const data = await response.json();
    if (!response.ok || !data.token) return null;
    const session = await getSession();
    if (!session) return null;
    session.token = data.token;
    session.accessTokenExpiresAt = Date.now() + (Number(data.expires_in || 86400) * 1000);
    await saveSession(session);
    return session.token;
  } catch (e) {
    return null;
  }
}

// ----------------------------------------------------------
// HELPER: makeRequest
// Generic wrapper with timeout, JWT injection, JSON parsing.
// ----------------------------------------------------------
async function makeRequest(endpoint, options = {}) {
  const fullUrl = API_BASE + endpoint;

  // Inject JWT token if we have one
  const token = await _getAuthToken();

  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const finalOptions = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {})
    }
  };

  const controller = new AbortController();
  finalOptions.signal = controller.signal;

  const timeoutId = setTimeout(() => {
    controller.abort();
    console.warn('[API] Request timed out:', fullUrl);
  }, REQUEST_TIMEOUT_MS);

  try {
    let response = await fetch(fullUrl, finalOptions);
    clearTimeout(timeoutId);

    // Access token expired: silently refresh using the device-persisted refresh token.
    if (response.status === 401 && typeof getSession === 'function') {
      const session = await getSession();
      if (session && session.refreshToken) {
        const refreshed = await _refreshAccessToken(session.refreshToken);
        if (refreshed) {
          finalOptions.headers = { ...(finalOptions.headers || {}), Authorization: `Bearer ${refreshed}` };
          response = await fetch(fullUrl, finalOptions);
        }
      }
    }

    const data = await response.json();

    if (!response.ok) {
      throw {
        message: data.message || `Server error (HTTP ${response.status})`,
        status: response.status,
        offline: false
      };
    }

    return data;

  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError' || !navigator.onLine) {
      console.warn('[API] Device is offline or request aborted.');
      return { success: false, offline: true, message: 'Device is offline. Data saved locally.' };
    }

    throw error;
  }
}

// ============================================================
// AUTH
// ============================================================

async function apiLogin(workerId, password) {
  return makeRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ worker_id: workerId, password: password, device_id: localStorage.getItem('sahaay_device_id') || '' })
  });
}

async function apiSignup(workerId, name, password, phone, district, email) {
  return makeRequest('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({
      worker_id: workerId,
      name: name,
      password: password,
      phone: phone || null,
      district: district || null,
      email: email || null
    })
  });
}

async function apiLogout() {
  return makeRequest('/auth/logout', { method: 'POST' });
}

/**
 * Request password reset email
 * POST /api/v1/doctor/reset_password
 */
async function apiRequestPasswordReset(email) {
  return makeRequest('/auth/request_password_reset', {
    method: 'POST',
    body: JSON.stringify({ email: email })
  });
}

async function apiResetPassword(token, password) {
  return makeRequest('/auth/reset_password', {
    method: 'POST',
    body: JSON.stringify({ token, password })
  });
}

// ============================================================
// PATIENTS
// ============================================================

async function apiGetQueue() {
  return makeRequest('/patients/queue', { method: 'GET' });
}

async function apiRegisterPatient(patientData) {
  return makeRequest('/patients/register', {
    method: 'POST',
    body: JSON.stringify(patientData)
  });
}

/**
 * Upload media files (images/videos/audio) as FormData.
 * POST /api/v1/patients/upload_media
 */
async function apiUploadMedia(formData) {
  const fullUrl = API_BASE + '/patients/upload_media';

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  // Inject token for multipart requests too
  const token = await _getAuthToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const response = await fetch(fullUrl, {
      method: 'POST',
      body: formData,
      headers,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    const data = await response.json();
    if (!response.ok) throw { message: data.message || 'Upload failed', status: response.status };
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError' || !navigator.onLine) {
      return { success: false, offline: true, message: 'Device is offline.' };
    }
    throw err;
  }
}

async function apiGetPatient(patientId) {
  return makeRequest(`/patients/${encodeURIComponent(patientId)}`, { method: 'GET' });
}

async function apiSaveVitals(patientId, vitals) {
  return makeRequest(`/patients/${encodeURIComponent(patientId)}/vitals`, {
    method: 'POST',
    body: JSON.stringify({ vitals })
  });
}

// ============================================================
// AI TRIAGE (GEMINI)
// ============================================================

async function apiSubmitAssessment(triageData) {
  return makeRequest('/assessment', {
    method: 'POST',
    body: JSON.stringify(triageData)
  });
}

// ============================================================
// FIRST AID AI
// ============================================================

/**
 * Analyze a new symptom with Gemini AI and get a first-aid protocol
 * POST /api/v1/firstaid/analyze
 */
async function apiFirstAidAnalyze(symptom) {
  return makeRequest('/firstaid/analyze', {
    method: 'POST',
    body: JSON.stringify({ symptom: symptom })
  });
}

/**
 * Save a new AI-generated first-aid protocol to protocols.json
 * POST /api/v1/firstaid/save
 */
async function apiFirstAidSave(protocol) {
  return makeRequest('/firstaid/save', {
    method: 'POST',
    body: JSON.stringify({ protocol: protocol })
  });
}

// ============================================================
// SYNC (OFFLINE QUEUE)
// ============================================================

async function apiSyncOfflineQueue(records) {
  return makeRequest('/sync/batch', {
    method: 'POST',
    body: JSON.stringify({ records: records })
  });
}

// ============================================================
// DOCTOR PORTAL
// ============================================================

async function apiGetPendingCases() {
  return makeRequest('/doctor/pending', { method: 'GET' });
}

async function apiDoctorVerify(caseId, verifyData) {
  return makeRequest('/doctor/verify', {
    method: 'POST',
    body: JSON.stringify({ case_id: caseId, ...verifyData })
  });
}

/**
 * Register a doctor for first-time verification
 * Accepts FormData (multipart) for file upload
 */
async function apiRegisterDoctor(formData) {
  const fullUrl = API_BASE + '/doctor/register';
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const token = await _getAuthToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const response = await fetch(fullUrl, {
      method: 'POST',
      body: formData,
      headers,
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    const data = await response.json();
    if (!response.ok) throw { message: data.message || 'Registration failed', status: response.status };
    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError' || !navigator.onLine) {
      return { success: false, offline: true, message: 'Device is offline.' };
    }
    throw err;
  }
}

/**
 * Check if a doctor email is already registered
 * GET /api/v1/doctor/check/<email>
 */
async function apiCheckDoctorEmail(email) {
  return makeRequest(`/doctor/check/${encodeURIComponent(email)}`, { method: 'GET' });
}

/**
 * Get dashboard statistics
 * GET /api/v1/doctor/dashboard_stats
 */
async function apiGetDashboardStats() {
  return makeRequest('/doctor/dashboard_stats', { method: 'GET' });
}

async function apiGetCurrentDoctor() {
  return makeRequest('/doctor/me', { method: 'GET' });
}

async function apiGetDoctorPatient(patientId) {
  return makeRequest(`/doctor/patient/${encodeURIComponent(patientId)}`, { method: 'GET' });
}

async function apiSearchDoctorPatients(query) {
  return makeRequest(`/doctor/patients/search?q=${encodeURIComponent(query)}`, { method: 'GET' });
}

// ============================================================
// TELECONSULT
// ============================================================

async function apiRequestTeleconsult(patientId, reason, priority) {
  return makeRequest('/teleconsult/request', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      reason: reason || '',
      priority: priority || 'routine'
    })
  });
}

async function apiGetRecentSessions() {
  return makeRequest('/teleconsult/sessions', { method: 'GET' });
}
