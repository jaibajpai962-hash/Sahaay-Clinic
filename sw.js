/**
 * ============================================================
 * FILE: sw.js  —  Sahaay Clinic Service Worker
 * ============================================================
 * WHAT IS A SERVICE WORKER?
 * A Service Worker is a JavaScript file that runs in the
 * background (separate from the main browser page). It can:
 *   1. Cache files so the app works OFFLINE
 *   2. Intercept network requests and serve cached responses
 *
 * HOW IT WORKS (simple version):
 *   [Install]  → Download & store all app files in a cache
 *   [Activate] → Delete old caches if we released a new version
 *   [Fetch]    → When any file is requested, serve from cache first
 * ============================================================
 */

// ----------------------------------------------------------
// CACHE CONFIGURATION
// Change CACHE_VERSION whenever you update any cached file.
// This forces old caches to be cleared on next visit.
// ----------------------------------------------------------
const CACHE_VERSION = 'sahaay-v2.0.0';

// List of files that form the "App Shell" — the minimum set
// of files needed to show the UI even with zero internet.
const APP_SHELL_FILES = [
  '/',
  '/index.html',
  '/intake.html',
  '/firstaid.html',
  '/doctor.html',
  '/profile.html',
  '/css/style.css',
  '/js/app.js',
  '/js/api.js',
  '/data/protocols.json',
  '/manifest.json'
];

// ----------------------------------------------------------
// EVENT: INSTALL
// Fired once when the browser first registers this SW.
// We use this to pre-cache all App Shell files.
// ----------------------------------------------------------
self.addEventListener('install', function (event) {
  console.log('[SW] Installing Service Worker, version:', CACHE_VERSION);

  // waitUntil() keeps the SW in "installing" state until the
  // promise resolves — this ensures caching finishes before SW activates.
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      console.log('[SW] Caching App Shell files...');
      return cache.addAll(APP_SHELL_FILES);
    }).then(function () {
      console.log('[SW] All App Shell files cached successfully.');
      // skipWaiting() activates the new SW immediately, without
      // waiting for old tabs to close.
      return self.skipWaiting();
    }).catch(function (error) {
      console.error('[SW] Cache install failed:', error);
    })
  );
});

// ----------------------------------------------------------
// EVENT: ACTIVATE
// Fired after install, once the SW takes control.
// We use this to delete old/outdated caches.
// ----------------------------------------------------------
self.addEventListener('activate', function (event) {
  console.log('[SW] Activating Service Worker, version:', CACHE_VERSION);

  event.waitUntil(
    // caches.keys() returns an array of ALL cache names
    caches.keys().then(function (cacheNames) {
      return Promise.all(
        cacheNames.map(function (cacheName) {
          // If a cache name doesn't match our current version, delete it
          if (cacheName !== CACHE_VERSION) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function () {
      console.log('[SW] Old caches cleared. SW is active.');
      // clients.claim() makes the SW take control of all open pages immediately
      return self.clients.claim();
    })
  );
});

// ----------------------------------------------------------
// EVENT: FETCH
// Fired every time the page requests ANY resource (HTML, CSS,
// JS, JSON, API calls, images, etc.)
//
// STRATEGY: "Cache First, Network Fallback"
//   → Try the cache first (fast, offline-friendly)
//   → If not in cache, fetch from network
//   → API calls (/api/*) always go to the network
// ----------------------------------------------------------
self.addEventListener('fetch', function (event) {
  const requestUrl = new URL(event.request.url);

  // API requests should NEVER be served from cache.
  // They need live data from the Flask backend.
  if (requestUrl.pathname.startsWith('/api/')) {
    // Just pass the request straight to the network.
    // event.respondWith() is NOT called — browser handles it normally.
    return;
  }

  // For all other requests (App Shell files, assets):
  // Try cache first → fallback to network
  event.respondWith(
    caches.match(event.request).then(function (cachedResponse) {
      if (cachedResponse) {
        // Found in cache — return it immediately (works offline!)
        return cachedResponse;
      }

      // Not in cache — fetch from network
      return fetch(event.request).then(function (networkResponse) {
        // Optionally cache this new response for future offline use
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_VERSION).then(function (cache) {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(function () {
        // Network also failed — return a simple offline fallback page
        // Guard: accept header can be null on some requests (e.g. prefetch)
        const acceptHeader = event.request.headers.get('accept') || '';
        if (acceptHeader.includes('text/html')) {
          return caches.match('/index.html');
        }
      });
    })
  );
});
