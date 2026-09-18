// SwimCoach Service Worker
// Version: increment when updating static assets
const CACHE_VERSION = 'v1.0.4';
const STATIC_CACHE = `swimcoach-static-${CACHE_VERSION}`;
const API_CACHE = `swimcoach-api-${CACHE_VERSION}`;
const OFFLINE_CACHE = `swimcoach-offline-${CACHE_VERSION}`;

// Assets to cache immediately
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
    '/css/pico.min.css',
    '/css/style.css',
    '/js/app.js',
    '/js/api.js',
    '/js/utils.js',
    '/js/login.js',
    '/js/register.js',
    '/js/onboarding.js',
    '/js/macrocycle.js',
    '/js/dashboard.js',
    '/js/session.js',
    '/js/feedback.js',
    '/js/profile.js',
    '/js/upgrade.js',
    '/js/settings.js',
    '/js/trees.js',
    '/js/tier_model.js',
    '/js/load_model.js',
    '/ml/modelo1_arbol.json',
    '/ml/modelo2_bosque.json',
    '/assets/icons/icon-192.png',
    '/assets/icons/icon-512.png'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then(keys => {
                return Promise.all(
                    keys.filter(key => {
                        return key.startsWith('swimcoach-') && 
                               key !== STATIC_CACHE && 
                               key !== API_CACHE && 
                               key !== OFFLINE_CACHE;
                    }).map(key => caches.delete(key))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - network first for API, cache first for static
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // API requests - network first with offline fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstApi(event.request));
        return;
    }
    
    // Static assets - cache first
    event.respondWith(cacheFirstStatic(event.request));
});

// Network first strategy for API
async function networkFirstApi(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        // Cache successful GET responses
        if (networkResponse.ok && request.method === 'GET') {
            const cache = await caches.open(API_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        // For POST requests, also cache if it's feedback (for offline support)
        if (request.method === 'POST' && url.pathname.includes('/feedback')) {
            const cache = await caches.open(OFFLINE_CACHE);
            // Store the request body for later sync
            const clonedRequest = request.clone();
            const body = await clonedRequest.text();
            await cache.put(request, new Response(body, {
                headers: { 'Content-Type': 'application/json' }
            }));
        }
        
        return networkResponse;
    } catch (error) {
        // Network failed - try cache
        console.log('[SW] Network failed, trying cache:', request.url);
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline fallback for API
        return new Response(JSON.stringify({
            error: 'offline',
            message: 'You are offline. Data will sync when online.'
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Cache first strategy for static assets
async function cacheFirstStatic(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match('/index.html');
        }
        
        return new Response('Offline', { status: 503 });
    }
}

// Background sync for offline feedback
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-feedback') {
        event.waitUntil(syncOfflineFeedback());
    }
});

async function syncOfflineFeedback() {
    const cache = await caches.open(OFFLINE_CACHE);
    const requests = await cache.keys();
    
    for (const request of requests) {
        try {
            await fetch(request);
            await cache.delete(request);
        } catch (error) {
            console.log('[SW] Failed to sync:', request.url);
        }
    }
}

// Handle messages from client
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
    
    if (event.data === 'getVersion') {
        event.ports[0].postMessage({ version: CACHE_VERSION });
    }
});

// Periodic cache cleanup
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'cleanup-caches') {
        event.waitUntil(cleanupOldCaches());
    }
});

async function cleanupOldCaches() {
    const keys = await caches.keys();
    const now = Date.now();
    
    for (const key of keys) {
        if (key.startsWith('swimcoach-')) {
            const cache = await caches.open(key);
            const requests = await cache.keys();
            
            for (const request of requests) {
                const response = await cache.match(request);
                const dateHeader = response.headers.get('date');
                
                if (dateHeader) {
                    const cachedDate = new Date(dateHeader).getTime();
                    const age = now - cachedDate;
                    
                    // Remove entries older than 7 days for API cache
                    if (key === API_CACHE && age > 7 * 24 * 60 * 60 * 1000) {
                        await cache.delete(request);
                    }
                }
            }
        }
    }
}