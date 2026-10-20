/**
 * PulseOS Media Range Cache Service Worker (sw-media-cache.js)
 * High-performance client-side media chunk & intro persistence engine.
 * Eliminates redundant network traffic for replayed intros and audio tracks.
 */

const CACHE_NAME = 'pulseos-media-intro-v4';
const MEMORY_CHUNK_MAP = new Map(); // In-memory hot buffer cache for instant 0ms slicing

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

function getCanonicalMediaKey(url) {
  try {
    const u = new URL(url, self.location.origin);
    // Strip dynamic ephemeral tokens/queries for AList & media streams
    return u.origin + u.pathname;
  } catch (e) {
    return url.split('?')[0];
  }
}

async function notifyClients(data) {
  try {
    const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of clients) {
      client.postMessage(data);
    }
  } catch (e) {}
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = req.url;

  // CRITICAL ARCHITECTURE RULE (Rule 4):
  // NEVER intercept video streaming, AList storage requests, or audio proxy Range requests in Service Worker!
  // Chromium's native C++ media pipeline handles Range requests, connection reuse,
  // multi-threading, cancellation upon pause/seek natively without ServiceWorker thread contention.
  // Intercepting /alist/ or stream proxy requests in SW breaks socket pipelines, causing deadlocks,
  // infinite spinners, and decode failures for FLAC/WAV/MP3.
  if (url.includes('/alist/') || url.includes('/api/audio/stream') || url.includes('/api/cinema/') || url.includes('/api/vault/')) {
    return; // Passthrough directly to native browser C++ media pipeline!
  }

  const isVideo = req.destination === 'video' ||
                  /\.(mp4|mkv|webm|avi|mov|flv|ts|m2ts|iso)(\?|$)/i.test(url);

  if (isVideo) {
    return; // Passthrough directly to native browser C++ media pipeline!
  }

  // Handle local/static audio streams
  const isAudio = req.destination === 'audio' ||
                  /\.(mp3|flac|wav|m4a|aac|ogg)(\?|$)/i.test(url);

  if (!isAudio) {
    return; // Pass through non-audio requests untouched
  }

  const rangeHeader = req.headers.get('range');
  if (rangeHeader) {
    event.respondWith(handleRangeRequest(req, rangeHeader));
    return;
  }

  // Non-range audio request (e.g. full audio metadata)
  event.respondWith(handleFullRequest(req));
});

async function handleRangeRequest(req, rangeHeader) {
  const rangeMatch = rangeHeader.match(/bytes=(\d+)-(\d+)?/);
  if (!rangeMatch) {
    return fetch(req);
  }

  const reqStart = parseInt(rangeMatch[1], 10);
  const reqEnd = rangeMatch[2] ? parseInt(rangeMatch[2], 10) : null;
  const canonicalKey = getCanonicalMediaKey(req.url);

  // 1. Check in-memory hot buffer first
  let cachedInfo = MEMORY_CHUNK_MAP.get(canonicalKey);

  // 2. If not in memory, check CacheStorage
  if (!cachedInfo) {
    try {
      const cache = await caches.open(CACHE_NAME);
      const cachedRes = await cache.match(canonicalKey);
      if (cachedRes) {
        const chunkStart = parseInt(cachedRes.headers.get('X-PulseOS-Chunk-Start') || '0', 10);
        const chunkEnd = parseInt(cachedRes.headers.get('X-PulseOS-Chunk-End') || '0', 10);
        const totalLength = parseInt(cachedRes.headers.get('X-PulseOS-Total-Length') || '0', 10);
        const mimeType = cachedRes.headers.get('Content-Type') || 'video/mp4';
        const ab = await cachedRes.arrayBuffer();

        cachedInfo = {
          chunkStart,
          chunkEnd: Math.max(chunkEnd, ab.byteLength - 1),
          totalLength: totalLength || ab.byteLength,
          mimeType,
          buffer: ab
        };

        // Cache in memory for subsequent Range slices (evict oldest if > 6 items)
        if (MEMORY_CHUNK_MAP.size >= 6) {
          const firstKey = MEMORY_CHUNK_MAP.keys().next().value;
          MEMORY_CHUNK_MAP.delete(firstKey);
        }
        MEMORY_CHUNK_MAP.set(canonicalKey, cachedInfo);
      }
    } catch (e) {
      console.warn('[SW Media Cache] Error loading from CacheStorage:', e);
    }
  }

  // 3. If cache covers reqStart, synthesize 206 Partial Content
  if (cachedInfo && reqStart >= cachedInfo.chunkStart && reqStart <= cachedInfo.chunkEnd) {
    const serveStart = reqStart;
    const serveEnd = (reqEnd !== null && reqEnd <= cachedInfo.chunkEnd)
      ? reqEnd
      : cachedInfo.chunkEnd;

    if (serveEnd >= serveStart) {
      const sliceOffset = serveStart - cachedInfo.chunkStart;
      const sliceEndOffset = serveEnd - cachedInfo.chunkStart + 1;
      const slicedBuffer = cachedInfo.buffer.slice(sliceOffset, sliceEndOffset);
      const sliceLength = slicedBuffer.byteLength;

      const headers = new Headers();
      headers.set('Content-Type', cachedInfo.mimeType || 'video/mp4');
      headers.set('Content-Range', `bytes ${serveStart}-${serveEnd}/${cachedInfo.totalLength || '*'}`);
      headers.set('Content-Length', String(sliceLength));
      headers.set('Accept-Ranges', 'bytes');
      headers.set('Cache-Control', 'private, max-age=2592000');
      headers.set('X-PulseOS-Cache', 'HIT');

      notifyClients({
        type: 'PULSEOS_MEDIA_CACHE_HIT',
        url: req.url,
        canonicalKey,
        savedBytes: sliceLength,
        range: `${serveStart}-${serveEnd}`
      });

      return new Response(slicedBuffer, {
        status: 206,
        statusText: 'Partial Content',
        headers: headers
      });
    }
  }

  // 4. Cache Miss or out-of-range: pass through directly to network
  return fetch(req);
}

async function handleFullRequest(req) {
  const canonicalKey = getCanonicalMediaKey(req.url);
  try {
    const cache = await caches.open(CACHE_NAME);
    const cachedRes = await cache.match(canonicalKey);
    if (cachedRes) {
      const totalLength = parseInt(cachedRes.headers.get('X-PulseOS-Total-Length') || '0', 10);
      const chunkEnd = parseInt(cachedRes.headers.get('X-PulseOS-Chunk-End') || '0', 10);
      // If full file is cached
      if (totalLength > 0 && chunkEnd >= totalLength - 1) {
        notifyClients({
          type: 'PULSEOS_MEDIA_CACHE_HIT',
          url: req.url,
          canonicalKey,
          savedBytes: totalLength,
          range: 'full'
        });
        return cachedRes.clone();
      }
    }
  } catch (e) {}

  return fetch(req);
}

// Client IPC message handler
self.addEventListener('message', (event) => {
  const data = event.data;
  if (!data || !data.type) return;

  if (data.type === 'CACHE_INTRO_CHUNK') {
    const { url, buffer, totalLength, mimeType, chunkStart, chunkEnd, title } = data;
    const canonicalKey = getCanonicalMediaKey(url);

    caches.open(CACHE_NAME).then((cache) => {
      const headers = new Headers();
      headers.set('Content-Type', mimeType || 'video/mp4');
      headers.set('X-PulseOS-Chunk-Start', String(chunkStart || 0));
      headers.set('X-PulseOS-Chunk-End', String(chunkEnd || (buffer.byteLength - 1)));
      headers.set('X-PulseOS-Total-Length', String(totalLength || buffer.byteLength));
      if (title) headers.set('X-PulseOS-Title', encodeURIComponent(title));
      headers.set('Cache-Control', 'private, max-age=2592000');

      const response = new Response(buffer, {
        status: 200,
        headers: headers
      });

      return cache.put(canonicalKey, response).then(() => {
        // Also update memory map
        MEMORY_CHUNK_MAP.set(canonicalKey, {
          chunkStart: chunkStart || 0,
          chunkEnd: chunkEnd || (buffer.byteLength - 1),
          totalLength: totalLength || buffer.byteLength,
          mimeType: mimeType || 'video/mp4',
          buffer: buffer
        });
        notifyClients({
          type: 'PULSEOS_INTRO_CACHED_SUCCESS',
          canonicalKey,
          size: buffer.byteLength,
          totalLength
        });
      });
    }).catch((err) => {
      console.warn('[SW Media Cache] Error caching intro chunk:', err);
    });
  } else if (data.type === 'GET_MEDIA_CACHE_STATS') {
    caches.open(CACHE_NAME).then(async (cache) => {
      const requests = await cache.keys();
      let totalBytes = 0;
      const items = [];
      for (const r of requests) {
        const res = await cache.match(r);
        if (res) {
          const ab = await res.arrayBuffer();
          totalBytes += ab.byteLength;
          items.push({
            url: r.url,
            size: ab.byteLength,
            title: decodeURIComponent(res.headers.get('X-PulseOS-Title') || '')
          });
        }
      }
      if (event.source) {
        event.source.postMessage({
          type: 'PULSEOS_MEDIA_CACHE_STATS',
          count: requests.length,
          totalBytes,
          items
        });
      }
    });
  } else if (data.type === 'CLEAR_MEDIA_CACHE') {
    MEMORY_CHUNK_MAP.clear();
    caches.delete(CACHE_NAME).then(() => {
      notifyClients({
        type: 'PULSEOS_MEDIA_CACHE_CLEARED'
      });
    });
  }
});
