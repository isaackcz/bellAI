// PepperAI Service Worker for PWA functionality
const CACHE_NAME = 'pepperai-v1.1.0';
const STATIC_CACHE = 'pepperai-static-v1.1';
const DYNAMIC_CACHE = 'pepperai-dynamic-v1.1';
const RESULTS_CACHE = 'pepperai-results-v1.1';

// Files to cache for offline functionality
const STATIC_FILES = [
  '/',
  '/static/css/styles.css',
  '/static/css/new-analysis.css',
  '/static/css/advanced-styles.css',
  '/static/js/script.js',
  '/static/js/offline-storage.js',
  '/static/images/logo.svg',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install event - cache static files
self.addEventListener('install', (event) => {
  console.log('🔧 Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('📦 Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('✅ Service Worker: Installation complete');
        self.skipWaiting();
      })
      .catch((error) => {
        console.error('❌ Service Worker: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('🚀 Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE && cacheName !== RESULTS_CACHE) {
              console.log('🗑️ Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('✅ Service Worker: Activation complete');
        self.clients.claim();
      })
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Handle different types of requests
  if (request.method === 'GET') {
    event.respondWith(handleGetRequest(request, url));
  } else if (request.method === 'POST' && url.pathname === '/upload') {
    event.respondWith(handleUploadRequest(request));
  }
});

// Handle GET requests with cache-first strategy for static files
async function handleGetRequest(request, url) {
  try {
    // For static files, try cache first
    if (STATIC_FILES.some(file => url.pathname.includes(file.replace('/', '')))) {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        console.log('📋 Serving from cache:', url.pathname);
        return cachedResponse;
      }
    }
    
    // For result images, try cache first, then network
    if (url.pathname.startsWith('/results/') || url.pathname.startsWith('/uploads/')) {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        console.log('📋 Serving result from cache:', url.pathname);
        return cachedResponse;
      }
    }
    
    // For dynamic content, try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.status === 200) {
      const responseClone = networkResponse.clone();
      
      // Cache result images separately
      if (url.pathname.startsWith('/results/') || url.pathname.startsWith('/uploads/')) {
        const resultsCache = await caches.open(RESULTS_CACHE);
        resultsCache.put(request, responseClone);
      } else {
        const cache = await caches.open(DYNAMIC_CACHE);
        cache.put(request, responseClone);
      }
    }
    
    return networkResponse;
    
  } catch (error) {
    console.log('🔄 Network failed, trying cache:', url.pathname);
    
    // Try to serve from cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.destination === 'document') {
      return caches.match('/');
    }
    
    // Return a basic response for other requests
    return new Response('Offline - Please check your connection', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// Handle upload requests - queue if offline
async function handleUploadRequest(request) {
  try {
    console.log('📤 Processing upload request');
    const response = await fetch(request);
    
    // If successful, notify clients
    if (response.ok) {
      const clients = await self.clients.matchAll();
      clients.forEach(client => {
        client.postMessage({
          type: 'UPLOAD_SUCCESS',
          timestamp: Date.now()
        });
      });
    }
    
    return response;
  } catch (error) {
    console.error('❌ Upload failed (offline):', error);
    
    // Notify clients that upload should be queued
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'UPLOAD_OFFLINE',
        timestamp: Date.now()
      });
    });
    
    return new Response(JSON.stringify({
      error: 'Upload failed - please check your connection and try again',
      offline: true,
      queued: true
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Background sync for offline uploads
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-upload') {
    console.log('🔄 Background sync: Processing offline uploads');
    event.waitUntil(processOfflineUploads());
  }
});

async function processOfflineUploads() {
  try {
    // Notify clients to process queued uploads
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_UPLOADS',
        timestamp: Date.now()
      });
    });
    console.log('✅ Background sync: Notified clients to process uploads');
  } catch (error) {
    console.error('❌ Background sync error:', error);
  }
}

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'periodic-upload-sync') {
    console.log('🔄 Periodic sync: Processing queued uploads');
    event.waitUntil(processOfflineUploads());
  }
});

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    console.log('📬 Push notification received:', data);
    
    event.waitUntil(
      self.registration.showNotification(data.title, {
        body: data.body,
        icon: '/static/images/icon-192.png',
        badge: '/static/images/logo.svg',
        tag: 'pepperai-notification',
        data: data
      })
    );
  }
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Notification clicked:', event.notification.data);
  
  event.notification.close();
  
  event.waitUntil(
    self.clients.openWindow('/')
  );
});

// Message handler for communication with clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHARE_TARGET') {
    console.log('📤 Share target activated:', event.data);
    // Handle shared content
  } else if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data && event.data.type === 'CACHE_ANALYSIS') {
    // Store analysis result in cache
    const { analysisData, imageUrl } = event.data;
    if (imageUrl) {
      fetch(imageUrl)
        .then(response => {
          if (response.ok) {
            const cache = caches.open(RESULTS_CACHE);
            return cache.then(c => c.put(imageUrl, response));
          }
        })
        .catch(err => console.error('Failed to cache analysis image:', err));
    }
  }
});

console.log('🚀 PepperAI Service Worker loaded successfully');
