/**
 * ============================================================
 * FILE: js/app.js  —  Sahaay Clinic Core Application Logic
 * ============================================================
 * THIS FILE HANDLES:
 *   1. IndexedDB setup — the local offline database
 *   2. CRUD operations — Create, Read, Update, Delete patient data
 *   3. Offline queue — saving data locally when no internet
 *   4. Sync — pushing queued data to server when back online
 *   5. QR Code generation — creating a shareable QR Health ID
 *   6. QR Code scanning — reading a QR code via the camera
 *   7. Service Worker registration — enabling offline mode
 *   8. Online/offline status detection
 *   9. Shared UI helpers (toasts, loading states, tabs)
 *
 * FOR BEGINNERS:
 *   IndexedDB = a database built INTO the browser (like localStorage
 *   but much more powerful). Data stored here survives page refresh
 *   and works completely offline.
 * ============================================================
 */

'use strict'; // Strict mode catches common JS mistakes early

// ============================================================
// SECTION 1: SERVICE WORKER REGISTRATION
// ============================================================

/**
 * Registers the service worker (sw.js) with the browser.
 * Must be called once on every page load.
 * The SW runs in the background and enables offline caching.
 */
function registerServiceWorker() {
  // Check if the browser supports Service Workers
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker
        .register('/sw.js')
        .then(function (registration) {
          console.log('[App] Service Worker registered. Scope:', registration.scope);
        })
        .catch(function (error) {
          console.error('[App] Service Worker registration failed:', error);
        });
    });
  } else {
    console.warn('[App] Service Workers are not supported in this browser.');
  }
}

// ============================================================
// SECTION 2: INDEXEDDB DATABASE SETUP
// ============================================================

/**
 * Database configuration constants.
 * Change DB_VERSION when you add/remove object stores (tables).
 */
const DB_NAME    = 'SahaayClinicDB';
const DB_VERSION = 2;

// "Object Store" = table in IndexedDB
const STORE_PATIENTS   = 'patients';   // stores patient records
const STORE_QUEUE      = 'offlineQueue'; // stores pending sync records
const STORE_SESSIONS   = 'sessions';   // stores login session

/**
 * Opens (or creates) the IndexedDB database.
 * Returns a Promise that resolves with the database object (db).
 *
 * Think of this like "connecting" to a database in MySQL/PostgreSQL.
 */
function openDatabase() {
  return new Promise(function (resolve, reject) {
    // indexedDB.open(name, version) opens or upgrades the DB
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    // onupgradeneeded fires when DB is created for the first time
    // or when DB_VERSION is bumped. This is where we define our "tables".
    request.onupgradeneeded = function (event) {
      const db = event.target.result;
      console.log('[DB] Upgrading database to version', DB_VERSION);

      // Create "patients" store with auto-incrementing id
      if (!db.objectStoreNames.contains(STORE_PATIENTS)) {
        const patientStore = db.createObjectStore(STORE_PATIENTS, {
          keyPath: 'patientId' // "patientId" is the primary key / unique ID
        });
        // Indexes = ways to search/filter data (like SQL WHERE clause)
        patientStore.createIndex('name',      'name',      { unique: false });
        patientStore.createIndex('phone',     'phone',     { unique: false });
        patientStore.createIndex('createdAt', 'createdAt', { unique: false });
        console.log('[DB] Created "patients" store.');
      }

      // Create "offlineQueue" store for pending sync records
      if (!db.objectStoreNames.contains(STORE_QUEUE)) {
        const queueStore = db.createObjectStore(STORE_QUEUE, {
          keyPath: 'queueId',
          autoIncrement: true // auto-numbering: 1, 2, 3, ...
        });
        queueStore.createIndex('type',      'type',      { unique: false });
        queueStore.createIndex('createdAt', 'createdAt', { unique: false });
        console.log('[DB] Created "offlineQueue" store.');
      }

      // Create "sessions" store for current login
      if (!db.objectStoreNames.contains(STORE_SESSIONS)) {
        db.createObjectStore(STORE_SESSIONS, { keyPath: 'id' });
        console.log('[DB] Created "sessions" store.');
      }
    };

    request.onsuccess = function (event) {
      console.log('[DB] Database opened successfully.');
      resolve(event.target.result);
    };

    request.onerror = function (event) {
      console.error('[DB] Failed to open database:', event.target.error);
      reject(event.target.error);
    };
  });
}

// ============================================================
// SECTION 3: PATIENT CRUD OPERATIONS
// ============================================================

/**
 * Saves a new patient record to IndexedDB (local database).
 * This works completely offline.
 *
 * @param {Object} patientData - The patient's intake form data
 * @returns {Promise<string>} - Resolves with the new patientId
 */
async function savePatientLocally(patientData) {
  // Generate a unique ID using timestamp + random number
  // Format: SAH-1704067200000-XY7  (SAH = Sahaay prefix)
  const patientId = 'SAH-' + Date.now() + '-' + Math.random().toString(36).substr(2, 3).toUpperCase();

  const record = {
    ...patientData,           // spread all intake form fields
    patientId: patientId,
    createdAt: new Date().toISOString(),
    syncStatus: 'pending',    // 'pending' | 'synced' | 'failed'
    source: 'local'
  };

  const db = await openDatabase();

  return new Promise(function (resolve, reject) {
    // A "transaction" groups database operations atomically.
    // 'readwrite' = we want to write, not just read.
    const transaction = db.transaction([STORE_PATIENTS], 'readwrite');
    const store = transaction.objectStore(STORE_PATIENTS);
    const request = store.put(record); // put() = insert or update

    request.onsuccess = function () {
      console.log('[DB] Patient saved locally with ID:', patientId);
      resolve(patientId);
    };

    request.onerror = function (e) {
      console.error('[DB] Failed to save patient:', e.target.error);
      reject(e.target.error);
    };
  });
}

/**
 * Retrieves a single patient by their patientId.
 *
 * @param {string} patientId
 * @returns {Promise<Object|null>} - Patient object or null if not found
 */
async function getPatientById(patientId) {
  const db = await openDatabase();

  return new Promise(function (resolve, reject) {
    const transaction = db.transaction([STORE_PATIENTS], 'readonly');
    const store = transaction.objectStore(STORE_PATIENTS);
    const request = store.get(patientId); // .get(key) fetches by primary key

    request.onsuccess = function () {
      resolve(request.result || null);
    };

    request.onerror = function (e) {
      reject(e.target.error);
    };
  });
}

/**
 * Retrieves all patients stored in local IndexedDB.
 *
 * @returns {Promise<Array>} - Array of all patient objects
 */
async function getAllLocalPatients() {
  const db = await openDatabase();

  return new Promise(function (resolve, reject) {
    const transaction = db.transaction([STORE_PATIENTS], 'readonly');
    const store = transaction.objectStore(STORE_PATIENTS);
    const request = store.getAll(); // .getAll() returns all records

    request.onsuccess = function () {
      resolve(request.result || []);
    };

    request.onerror = function (e) {
      reject(e.target.error);
    };
  });
}

/**
 * Updates an existing patient record in IndexedDB.
 *
 * @param {Object} updatedData - Must include patientId
 */
async function updatePatientLocally(updatedData) {
  const existing = await getPatientById(updatedData.patientId);
  if (!existing) throw new Error('Patient not found: ' + updatedData.patientId);

  const merged = { ...existing, ...updatedData, updatedAt: new Date().toISOString() };
  const db = await openDatabase();

  return new Promise(function (resolve, reject) {
    const transaction = db.transaction([STORE_PATIENTS], 'readwrite');
    const store = transaction.objectStore(STORE_PATIENTS);
    const request = store.put(merged);

    request.onsuccess = () => resolve(merged);
    request.onerror   = (e) => reject(e.target.error);
  });
}

// ============================================================
// SECTION 4: OFFLINE QUEUE MANAGEMENT
// ============================================================

/**
 * Adds a record to the offline sync queue.
 * Called when an action fails because the device is offline.
 *
 * @param {string} type   - Action type, e.g., 'register_patient', 'submit_assessment'
 * @param {Object} payload - The data to sync later
 */
async function addToOfflineQueue(type, payload) {
  const db = await openDatabase();

  const queueRecord = {
    type:      type,
    payload:   payload,
    createdAt: new Date().toISOString(),
    attempts:  0  // track how many times we've tried to sync this
  };

  return new Promise(function (resolve, reject) {
    const transaction = db.transaction([STORE_QUEUE], 'readwrite');
    const store = transaction.objectStore(STORE_QUEUE);
    const request = store.add(queueRecord);

    request.onsuccess = function () {
      console.log('[Queue] Added to offline queue:', type);
      updateOfflineQueueBadge(); // update the floating badge counter
      resolve(request.result);
    };

    request.onerror = function (e) {
      reject(e.target.error);
    };
  });
}

/**
 * Gets all pending items from the offline queue.
 * @returns {Promise<Array>}
 */
async function getOfflineQueue() {
  const db = await openDatabase();

  return new Promise(function (resolve, reject) {
    const transaction = db.transaction([STORE_QUEUE], 'readonly');
    const store = transaction.objectStore(STORE_QUEUE);
    // IMPORTANT: call getAll() only once and bind both handlers to the same request object
    const request = store.getAll();
    request.onsuccess = (e) => resolve(e.target.result || []);
    request.onerror   = (e) => reject(e.target.error);
  });
}

/**
 * Removes a successfully-synced item from the offline queue.
 * @param {number} queueId - The auto-incremented queue record ID
 */
async function removeFromOfflineQueue(queueId) {
  const db = await openDatabase();

  return new Promise(function (resolve, reject) {
    const transaction = db.transaction([STORE_QUEUE], 'readwrite');
    const store = transaction.objectStore(STORE_QUEUE);
    const request = store.delete(queueId);

    request.onsuccess = () => resolve();
    request.onerror   = (e) => reject(e.target.error);
  });
}

/**
 * Attempts to sync all pending offline queue items to the server.
 * Triggered automatically when the device comes back online.
 */
async function syncOfflineQueue() {
  if (!navigator.onLine) {
    console.log('[Sync] Still offline. Skipping sync.');
    return;
  }

  const queue = await getOfflineQueue();
  if (queue.length === 0) {
    console.log('[Sync] Offline queue is empty. Nothing to sync.');
    return;
  }

  console.log('[Sync] Syncing', queue.length, 'offline records...');
  showToast(`Syncing ${queue.length} offline record(s)…`, 'info');

  let successCount = 0;
  let failCount    = 0;

  for (const item of queue) {
    try {
      // apiSyncOfflineQueue is defined in api.js
      await apiSyncOfflineQueue([item]);
      await removeFromOfflineQueue(item.queueId);
      successCount++;
    } catch (error) {
      console.error('[Sync] Failed to sync item:', item.queueId, error);
      failCount++;
    }
  }

  updateOfflineQueueBadge();

  if (successCount > 0) {
    showToast(`✅ Synced ${successCount} record(s) successfully.`, 'success');
  }
  if (failCount > 0) {
    showToast(`⚠️ ${failCount} record(s) failed to sync. Will retry later.`, 'warning');
  }
}

// ============================================================
// SECTION 5: QR CODE GENERATION (Snap & Sync Health ID)
// ============================================================

/**
 * Generates an offline QR Health ID for a patient.
 * The QR encodes the patient's ID as a URL that the clinic
 * can scan even without internet.
 *
 * HOW IT WORKS:
 *   1. We create a canvas element
 *   2. We use a tiny QR library included via CDN on intake.html
 *   3. The QR encodes: sahaay://patient?id=SAH-xxxxx
 *   4. Any device with a camera can scan and lookup the patient
 *
 * @param {string} patientId  - The patient's unique ID
 * @param {string} canvasId   - The ID of the <canvas> element to draw on
 */
function generatePatientQR(patientId, canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.error('[QR] Canvas element not found:', canvasId);
    return;
  }

  // The data encoded in the QR code
  // Using a custom protocol so clinic devices can deep-link to the patient
  const qrData = `sahaay://patient?id=${patientId}&clinic=sahaay&ts=${Date.now()}`;

  // QRious is a lightweight QR library (loaded via CDN in intake.html)
  // It draws a QR code directly onto a <canvas> element.
  if (typeof QRious === 'undefined') {
    console.error('[QR] QRious library not loaded. Add it to your HTML.');
    canvas.getContext('2d').fillText('QR Error: Library not loaded', 10, 50);
    return;
  }

  // Create the QR code on the canvas
  new QRious({
    element: canvas,  // the canvas to draw on
    value:   qrData,  // the text/URL to encode
    size:    220,     // pixel dimensions
    background: '#ffffff',  // white background (required for scanning)
    foreground: '#0d1117',  // dark dots (our app's dark theme)
    level:   'H'      // 'H' = high error correction (scannable even if dirty)
  });

  console.log('[QR] Generated QR code for patient:', patientId);
  return qrData;
}

// ============================================================
// SECTION 6: QR CODE SCANNING (Camera-based lookup)
// ============================================================

// Stores the video stream so we can stop it later
let _scannerStream = null;

/**
 * Starts the device camera for QR code scanning.
 * Uses the browser's built-in MediaDevices API — NO external library needed.
 *
 * @param {string} videoId     - The ID of the <video> element to show camera feed
 * @param {Function} onResult  - Callback with the decoded QR text string
 */
async function startQRScanner(videoId, onResult) {
  const videoEl = document.getElementById(videoId);
  if (!videoEl) {
    console.error('[Scanner] Video element not found:', videoId);
    return;
  }

  try {
    // Request camera access (browser will ask user for permission)
    _scannerStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment', // use back camera on phones
        width:  { ideal: 1280 },
        height: { ideal: 720 }
      }
    });

    videoEl.srcObject = _scannerStream;
    videoEl.play();

    // Use BarcodeDetector if the browser supports it (Chrome, Edge)
    // This is a native browser API — no external library needed!
    if ('BarcodeDetector' in window) {
      const detector = new BarcodeDetector({ formats: ['qr_code'] });
      _scanInterval = setInterval(async function () {
        try {
          const barcodes = await detector.detect(videoEl);
          if (barcodes.length > 0) {
            clearInterval(_scanInterval);
            stopQRScanner();
            onResult(barcodes[0].rawValue);
          }
        } catch (e) {
          // Detection frame failed — just try again next interval
        }
      }, 500); // scan every 500ms
    } else {
      // Fallback: browser doesn't support BarcodeDetector
      // Show message to user
      showToast('⚠️ QR scanning not supported in this browser. Try Chrome.', 'warning');
      stopQRScanner();
    }

  } catch (error) {
    console.error('[Scanner] Camera access failed:', error);
    if (error.name === 'NotAllowedError') {
      showToast('❌ Camera permission denied. Please allow camera access.', 'error');
    } else {
      showToast('❌ Could not access camera: ' + error.message, 'error');
    }
  }
}

// Reference to the scanning interval timer
let _scanInterval = null;

/**
 * Stops the QR scanner and turns off the camera.
 */
function stopQRScanner() {
  if (_scanInterval) {
    clearInterval(_scanInterval);
    _scanInterval = null;
  }
  if (_scannerStream) {
    _scannerStream.getTracks().forEach(track => track.stop());
    _scannerStream = null;
  }
  console.log('[Scanner] QR scanner stopped.');
}

/**
 * Parses a Sahaay QR code value and extracts the patientId.
 *
 * @param {string} qrValue - The raw text decoded from the QR code
 * @returns {string|null}  - The patientId string, or null if invalid
 */
function parsePatientQR(qrValue) {
  try {
    // QR format: sahaay://patient?id=SAH-xxxxx&clinic=sahaay&ts=...
    if (!qrValue.startsWith('sahaay://patient')) {
      console.warn('[QR] Unrecognised QR format:', qrValue);
      return null;
    }
    // Extract the "id" query parameter
    const urlParams = new URLSearchParams(qrValue.split('?')[1]);
    return urlParams.get('id');
  } catch (e) {
    console.error('[QR] Failed to parse QR value:', e);
    return null;
  }
}

// ============================================================
// SECTION 7: ONLINE/OFFLINE STATUS MANAGEMENT
// ============================================================

/**
 * Sets up listeners for online/offline events.
 * When the device goes offline, we show a warning badge.
 * When it comes back online, we try to sync queued data.
 */
function initNetworkStatusListeners() {
  window.addEventListener('online', function () {
    console.log('[Network] Device is ONLINE');
    showToast('✅ Back online! Syncing queued records…', 'success');
    updateNetworkStatusUI(true);
    syncOfflineQueue(); // automatically sync when back online
  });

  window.addEventListener('offline', function () {
    console.log('[Network] Device is OFFLINE');
    showToast('⚠️ You are offline. Data will be saved locally.', 'warning');
    updateNetworkStatusUI(false);
  });

  // Set initial state
  updateNetworkStatusUI(navigator.onLine);
}

/**
 * Updates the navbar online/offline status indicator.
 * @param {boolean} isOnline
 */
function updateNetworkStatusUI(isOnline) {
  const indicator = document.getElementById('network-status');
  if (!indicator) return;

  if (isOnline) {
    indicator.className = 'status-indicator status-online';
    indicator.innerHTML = '<span class="status-dot"></span> Online';
  } else {
    indicator.className = 'status-indicator status-offline';
    indicator.innerHTML = '<span class="status-dot"></span> Offline';
  }
}

/**
 * Updates the floating badge that shows how many records
 * are waiting to be synced.
 */
async function updateOfflineQueueBadge() {
  const badge = document.getElementById('offline-queue-badge');
  if (!badge) return;

  const queue = await getOfflineQueue();

  if (queue.length > 0 && !navigator.onLine) {
    badge.textContent = `📤 ${queue.length} records pending sync`;
    badge.classList.add('visible');
  } else {
    badge.classList.remove('visible');
  }
}

// ============================================================
// SECTION 8: UI HELPERS
// ============================================================

/**
 * Shows a toast notification (a small popup message at the bottom).
 * Automatically disappears after 4 seconds.
 *
 * @param {string} message - Text to display
 * @param {string} type    - 'success' | 'warning' | 'error' | 'info'
 */
function showToast(message, type = 'info') {
  // Create the toast container if it doesn't exist
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
      position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
      z-index: 9999; display: flex; flex-direction: column;
      align-items: center; gap: 8px; pointer-events: none;
    `;
    document.body.appendChild(container);
  }

  // Colour map for different toast types
  const colours = {
    success: { bg: '#0d2119', border: '#1a4731', color: '#56d364' },
    warning: { bg: '#271d0a', border: '#4d3510', color: '#e3b341' },
    error:   { bg: '#2d1111', border: '#551111', color: '#f85149' },
    info:    { bg: '#051d40', border: '#1158cc', color: '#388bfd' }
  };
  const c = colours[type] || colours.info;

  const toast = document.createElement('div');
  toast.style.cssText = `
    background: ${c.bg}; border: 1px solid ${c.border}; color: ${c.color};
    padding: 10px 18px; border-radius: 8px; font-size: 0.88rem;
    font-weight: 500; max-width: 380px; text-align: center;
    pointer-events: auto; font-family: var(--font-sans);
    transition: opacity 0.3s; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  `;
  toast.textContent = message;
  container.appendChild(toast);

  // Auto-remove after 4 seconds
  setTimeout(function () {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

/**
 * Activates a tab panel.
 * Hides all other panels in the same group, shows the selected one.
 *
 * HOW TO USE IN HTML:
 *   <button class="tab-btn" onclick="switchTab(this, 'panel-id')">Tab Name</button>
 *   <div id="panel-id" class="tab-panel active">...</div>
 *
 * @param {HTMLElement} clickedBtn  - The button that was clicked
 * @param {string}      panelId     - The ID of the panel to show
 */
function switchTab(clickedBtn, panelId) {
  // Find the <div class="tabs"> bar that contains the clicked button
  const tabsEl = clickedBtn.closest('.tabs');
  // Its sibling tab-panels live inside the same parent wrapper as the .tabs bar
  const parent  = tabsEl.parentElement;

  // Deactivate only the buttons inside THIS tabs bar (not nested ones)
  tabsEl.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

  // Hide only the DIRECT-CHILD tab-panels of this wrapper.
  // Iterating children instead of querySelectorAll prevents accidentally
  // closing panels that are nested inside a card inside another tab-panel.
  Array.from(parent.children).forEach(function (child) {
    if (child.classList.contains('tab-panel')) {
      child.classList.remove('active');
    }
  });

  // Activate the clicked button and the target panel
  clickedBtn.classList.add('active');
  const panel = document.getElementById(panelId);
  if (panel) panel.classList.add('active');
}

/**
 * Opens a modal dialog by its ID.
 * @param {string} modalId
 */
function openModal(modalId) {
  const overlay = document.getElementById(modalId);
  if (overlay) overlay.classList.add('open');
}

/**
 * Closes a modal dialog by its ID.
 * @param {string} modalId
 */
function closeModal(modalId) {
  const overlay = document.getElementById(modalId);
  if (overlay) overlay.classList.remove('open');
}

/**
 * Formats an ISO date string to a human-readable format.
 * e.g., "2025-01-15T10:30:00.000Z" → "15 Jan 2025, 10:30"
 *
 * @param {string} isoString
 * @returns {string}
 */
function formatDate(isoString) {
  if (!isoString) return 'N/A';
  const date = new Date(isoString);
  return date.toLocaleDateString('en-IN', {
    day:    '2-digit',
    month:  'short',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit'
  });
}

/**
 * Determines the urgency colour class based on a triage level string.
 * @param {string} urgency - 'critical' | 'high' | 'moderate' | 'low'
 * @returns {string} - CSS badge class
 */
function urgencyToBadgeClass(urgency) {
  const map = {
    'critical': 'badge-critical',
    'high':     'badge-critical',
    'moderate': 'badge-ai-draft',
    'low':      'badge-info'
  };
  return map[(urgency || '').toLowerCase()] || 'badge-muted';
}

// ============================================================
// SECTION 9: SESSION / AUTH HELPERS
// ============================================================

/**
 * Saves the logged-in worker's session to IndexedDB.
 * @param {Object} sessionData - { workerId, name, role, token }
 */
async function saveSession(sessionData) {
  const db = await openDatabase();
  return new Promise(function (resolve, reject) {
    const tx = db.transaction([STORE_SESSIONS], 'readwrite');
    tx.objectStore(STORE_SESSIONS).put({ id: 'current', deviceId: sessionData.deviceId || localStorage.getItem('sahaay_device_id') || '', savedAt: Date.now(), ...sessionData });
    tx.oncomplete = () => resolve();
    tx.onerror    = (e) => reject(e.target.error);
  });
}

/**
 * Retrieves the current session from IndexedDB.
 * @returns {Promise<Object|null>}
 */
async function getSession() {
  const db = await openDatabase();
  return new Promise(function (resolve, reject) {
    const tx = db.transaction([STORE_SESSIONS], 'readonly');
    const req = tx.objectStore(STORE_SESSIONS).get('current');
    req.onsuccess = () => resolve(req.result || null);
    req.onerror   = (e) => reject(e.target.error);
  });
}

/**
 * Clears the session (logout).
 */
async function clearSession() {
  const db = await openDatabase();
  return new Promise(function (resolve, reject) {
    const tx = db.transaction([STORE_SESSIONS], 'readwrite');
    tx.objectStore(STORE_SESSIONS).delete('current');
    tx.oncomplete = () => resolve();
    tx.onerror    = (e) => reject(e.target.error);
  });
}

/**
 * Redirects to login page if no session is found.
 * Call this at the top of every protected page.
 */
async function requireAuth() {
  const session = await getSession();
  if (!session) {
    window.location.href = '/index.html';
  }
  return session;
}

// ============================================================
// SECTION 10: INITIALISATION
// Call this once when any page loads.
// ============================================================

/**
 * Bootstraps the application.
 * Should be called in a DOMContentLoaded event on every page.
 */
async function initApp() {
  console.log('[App] Sahaay Clinic initialising…');

  // 1. Register the Service Worker for offline support
  registerServiceWorker();

  // 2. Open the database (creates it if it's the first visit)
  await openDatabase();

  // 3. Set up online/offline listeners
  initNetworkStatusListeners();

  // 4. Update the offline queue badge
  await updateOfflineQueueBadge();

  console.log('[App] Initialisation complete.');

  // intake.html owns its workflow. This historic duplicate flow uses
  // incompatible vital names and submits an empty AI assessment on save.
  if (false) {

    // Show pregnancy field only when gender is Female
    document.getElementById('patient-gender').addEventListener('change', function () {
      const pregField = document.getElementById('pregnancy-field');
      if (this.value === 'Female') {
        pregField.classList.remove('hidden');
      } else {
        pregField.classList.add('hidden');
      }
    });

    // Register form submit handler
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
      registerForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        try {
          const payload = {
            name: document.getElementById('patient-name').value.trim(),
            age: document.getElementById('patient-age').value,
            gender: document.getElementById('patient-gender').value,
            phone: document.getElementById('patient-phone').value.trim(),
            village: document.getElementById('patient-village').value.trim(),
            chiefComplaint: document.getElementById('chief-complaint').value.trim(),
            symptomDuration: document.getElementById('symptom-duration').value,
            knownConditions: document.getElementById('known-conditions').value.trim(),
            currentMedications: document.getElementById('current-medications').value.trim(),
            allergies: document.getElementById('allergies').value.trim(),
            pregnancyStatus: document.getElementById('pregnancy-status') ? document.getElementById('pregnancy-status').value : null,
            vitals: {} // will fill if media uploaded
          };

          // If there are attached media, upload them first
          if (attachedMedia.length > 0) {
            const uploadResp = await uploadAttachedMedia();
            if (uploadResp && uploadResp.success) {
              payload.vitals.media = uploadResp.files;
            }
          }

          // Call backend register
          const resp = await apiRegisterPatient(payload);
          if (resp && resp.success) {
            currentPatientId = resp.patientId;
            currentPatientName = payload.name;
            document.getElementById('vitals-patient-id').value = currentPatientId;
            document.getElementById('vitals-patient-name').textContent = `${currentPatientName} — ${currentPatientId}`;
            showToast('Patient registered. Continue to vitals.', 'success');
            // Switch to Vitals tab
            switchTab(document.querySelector('.tab-btn:nth-child(2)'), 'tab-vitals');
          } else {
            showToast(resp.message || 'Registration failed', 'error');
          }

        } catch (err) {
          console.error('Register error', err);
          showToast('Unable to register patient.', 'error');
        }
      });
    }

    // Vitals form submit handler
    const vitalsForm = document.getElementById('vitals-form');
    if (vitalsForm) {
      vitalsForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        try {
          const patientId = document.getElementById('vitals-patient-id').value || currentPatientId;
          if (!patientId) {
            showToast('No patient selected. Register or scan patient first.', 'warning');
            return;
          }

          const vitals = {
            temperature: parseFloat(document.getElementById('v-temp').value) || null,
            bp_sys: parseInt(document.getElementById('v-bp-sys').value) || null,
            bp_dia: parseInt(document.getElementById('v-bp-dia').value) || null,
            spo2: parseInt(document.getElementById('v-spo2').value) || null,
            pulse: parseInt(document.getElementById('v-pulse').value) || null,
            weight: parseFloat(document.getElementById('v-weight').value) || null,
            rr: parseInt(document.getElementById('v-rr').value) || null,
            notes: document.getElementById('v-notes').value.trim()
          };

          // If there are attached media (from register), upload and attach
          if (attachedMedia.length > 0) {
            const uploadResp = await uploadAttachedMedia();
            if (uploadResp && uploadResp.success) {
              vitals.media = uploadResp.files;
            }
          }

          // Submit as an assessment payload to AI later, for now save vitals by calling apiSubmitAssessment
          const triagePayload = {
            patientId: patientId,
            vitals: vitals,
            presentingSymptoms: [],
            notes: vitals.notes
          };

          const resp = await apiSubmitAssessment(triagePayload);
          if (resp && resp.success) {
            showToast('Vitals saved and sent for AI assessment (draft).', 'success');
            // Show AI result section if provided
            if (resp.assessment) {
              // populate result UI (simple mapping)
              document.getElementById('triage-result').classList.remove('hidden');
              document.getElementById('result-condition').textContent = resp.assessment.ai_condition || '—';
              document.getElementById('result-urgency').textContent = resp.assessment.ai_urgency || '—';
              document.getElementById('result-confidence').textContent = resp.assessment.ai_confidence || '—';
              // recommendations
              const recList = document.getElementById('result-recommendations');
              recList.innerHTML = '';
              (resp.assessment.ai_recommendations || []).forEach(r => {
                const li = document.createElement('li'); li.textContent = r; recList.appendChild(li);
              });
              document.getElementById('result-reasoning').textContent = resp.assessment.ai_reasoning || '';
            }
          } else {
            showToast(resp.message || 'Failed to save vitals.', 'error');
          }

        } catch (err) {
          console.error('Vitals submit error', err);
          showToast('Unable to save vitals.', 'error');
        }
      });
    }

    // Convert dataURL (base64) to Blob
    function dataURLToBlob(dataURL) {
      const parts = dataURL.split(',');
      const mime = parts[0].match(/:(.*?);/)[1];
      const binary = atob(parts[1]);
      const array = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) array[i] = binary.charCodeAt(i);
      return new Blob([array], { type: mime });
    }

    // Upload attachedMedia (base64 items) to backend via FormData
    async function uploadAttachedMedia() {
      if (attachedMedia.length === 0) return { success: true, files: [] };
      const formData = new FormData();
      attachedMedia.forEach((m, idx) => {
        try {
          const blob = dataURLToBlob(m.base64);
          formData.append('files', blob, m.name || `file_${Date.now()}_${idx}`);
        } catch (e) {
          console.warn('Failed to convert media to blob', e);
        }
      });

      const resp = await apiUploadMedia(formData);
      if (resp && resp.success) {
        // Clear attachedMedia after successful upload
        attachedMedia = [];
        renderMediaPreviews();
      }
      return resp;
    }
  }
}


// ============================================================
// SECTION 11: NATIVE LANGUAGE SELECTOR
// Builds a compact pill dropdown showing each language in its
// own script (हिंदी, اردو, தமிழ்…). On selection it triggers
// Google Translate's doGTranslate() function.
// ============================================================

const SAHAAY_LANGUAGES = [
  { code: 'en', label: 'English',   gtCode: 'en|en'  },
  { code: 'hi', label: 'हिंदी',     gtCode: 'en|hi'  },
  { code: 'ta', label: 'தமிழ்',     gtCode: 'en|ta'  },
  { code: 'bn', label: 'বাংলা',     gtCode: 'en|bn'  },
  { code: 'te', label: 'తెలుగు',    gtCode: 'en|te'  },
  { code: 'mr', label: 'मराठी',     gtCode: 'en|mr'  },
  { code: 'gu', label: 'ગુજરાતી',   gtCode: 'en|gu'  },
  { code: 'kn', label: 'ಕನ್ನಡ',     gtCode: 'en|kn'  },
  { code: 'ml', label: 'മലയാളം',   gtCode: 'en|ml'  },
  { code: 'pa', label: 'ਪੰਜਾਬੀ',    gtCode: 'en|pa'  },
  { code: 'ur', label: 'اردو',      gtCode: 'en|ur'  },
  { code: 'or', label: 'ଓଡ଼ିଆ',     gtCode: 'en|or'  },
  { code: 'as', label: 'অসমীয়া',   gtCode: 'en|as'  },
];

let _currentLangCode = localStorage.getItem('sahaay_lang') || 'en';

/**
 * Injects the language selector widget into every element with
 * the class "lang-selector-mount" found on the page.
 */
function initLangSelector() {
  document.querySelectorAll('.lang-selector-mount').forEach(function (mount) {
    mount.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'lang-selector-wrap';

    const current = SAHAAY_LANGUAGES.find(l => l.code === _currentLangCode) || SAHAAY_LANGUAGES[0];

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'lang-selector-btn';
    btn.setAttribute('aria-label', 'Change language');
    btn.innerHTML = `🌐 <span class="lang-label">${current.label}</span> <span class="lang-arrow">▾</span>`;
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      wrap.classList.toggle('open');
    });

    const dropdown = document.createElement('div');
    dropdown.className = 'lang-dropdown';

    SAHAAY_LANGUAGES.forEach(function (lang) {
      const opt = document.createElement('button');
      opt.type = 'button';
      opt.className = 'lang-option' + (lang.code === _currentLangCode ? ' active' : '');
      opt.textContent = lang.label;
      opt.addEventListener('click', function (e) {
        e.stopPropagation();
        _selectLang(lang, btn, dropdown);
        wrap.classList.remove('open');
      });
      dropdown.appendChild(opt);
    });

    wrap.appendChild(btn);
    wrap.appendChild(dropdown);
    mount.appendChild(wrap);

    // Close when clicking elsewhere
    document.addEventListener('click', function () {
      wrap.classList.remove('open');
    });
  });
}

/**
 * Applies a language choice via Google Translate.
 * Falls back to a cookie-based approach when GT is not loaded.
 */
function _selectLang(lang, btn, dropdown) {
  _currentLangCode = lang.code;
  localStorage.setItem('sahaay_lang', lang.code);

  // Update button label
  btn.innerHTML = `🌐 <span class="lang-label">${lang.label}</span> <span class="lang-arrow">▾</span>`;

  // Update active state
  dropdown.querySelectorAll('.lang-option').forEach(function (opt) {
    opt.classList.toggle('active', opt.textContent === lang.label);
  });

  // Trigger Google Translate
  try {
    if (typeof window.doGTranslate === 'function') {
      window.doGTranslate(lang.gtCode);
      return;
    }
    // Fallback: set the cookie that Google Translate reads
    const expiry = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toUTCString();
    document.cookie = `googtrans=/en/${lang.code};expires=${expiry};path=/`;
    document.cookie = `googtrans=/en/${lang.code};expires=${expiry};path=/;domain=.${location.hostname}`;
    if (lang.code !== 'en') location.reload();
  } catch (e) { /* ignore */ }
}

// Auto-restore saved language on page load
window.addEventListener('DOMContentLoaded', function () {
  initLangSelector();
  // If a non-English language was previously chosen, re-apply it
  if (_currentLangCode && _currentLangCode !== 'en') {
    const lang = SAHAAY_LANGUAGES.find(l => l.code === _currentLangCode);
    if (lang) {
      // Give GT widget 1s to initialise before triggering
      setTimeout(function () {
        try {
          if (typeof window.doGTranslate === 'function') window.doGTranslate(lang.gtCode);
        } catch (e) { /* ignore */ }
      }, 1000);
    }
  }
});
