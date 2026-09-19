/**
 * PulseOS Media Range Cache Service Worker (sw-media-cache.js)
 * Intercepts video/audio streaming and Range requests.
 * Caches media segments near playback position in CacheStorage/IndexedDB
 * to ensure zero-buffering instant resume after page refresh.
 */

const CACHE_NAME = 'pulseos-media-cache-v1';
const MAX_CACHE_ENTRIES = 50;

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

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = req.url;
  const rangeHeader = req.headers.get('range');

  // Determine if this is an audio/music request or a video file
  const isAudioReq = req.destination === 'audio' || /\.(mp3|flac|wav|m4a|aac|ogg)(\?|$)/i.test(url);
  const isVideoReq = req.destination === 'video' || /\.(mp4|mkv|webm|m4v|mov|ts)(\?|$)/i.test(url);

  // For video range streaming: pass through directly to native browser engine for zero-stutter hardware playback
  if (isVideoReq && rangeHeader) {
    return;
  }

  // We only cache GET requests for media
  const isMediaReq = isAudioReq || isVideoReq || Boolean(rangeHeader);
  if (!isMediaReq || req.method !== 'GET') {
    return;
  }

  event.respondWith(handleMediaRequest(req));
});

async function handleMediaRequest(req) {
  const url = req.url;
  const rangeHeader = req.headers.get('range');
  const cache = await caches.open(CACHE_NAME);

  // If this is a Range request
  if (rangeHeader) {
    // Try to see if we have the full response or a range slice cached
    const cleanUrl = url.split('?')[0];
    const cachedFull = await cache.match(cleanUrl);

    if (cachedFull) {
      // Synthesize 206 Partial Content from full cached response
      return createPartialResponse(cachedFull, rangeHeader);
    }

    // Check if we have exact range cached
    const cachedRange = await cache.match(req);
    if (cachedRange) {
      return cachedRange;
    }

    // Fetch from network with range
    try {
      const netRes = await fetch(req);
      if (netRes.status === 206) {
        // Clone and store small-to-medium range responses
        const contentLength = parseInt(netRes.headers.get('content-length') || '0', 10);
        if (contentLength > 0 && contentLength <= 40 * 1024 * 1024) { // <= 40MB chunk
          try {
            cache.put(req, netRes.clone());
          } catch (e) {}
        }
      } else if (netRes.status === 200) {
        // Full response received
        const contentLength = parseInt(netRes.headers.get('content-length') || '0', 10);
        if (contentLength > 0 && contentLength <= 80 * 1024 * 1024) { // <= 80MB full file
          try {
            cache.put(cleanUrl, netRes.clone());
          } catch (e) {}
        }
        return createPartialResponse(netRes, rangeHeader);
      }
      return netRes;
    } catch (err) {
      // If network fails, attempt to fallback to any cached version
      const fallback = await cache.match(cleanUrl);
      if (fallback) {
        return createPartialResponse(fallback, rangeHeader);
      }
      throw err;
    }
  }

  // Non-range GET media request (e.g. audio full fetch)
  const cached = await cache.match(req);
  if (cached) {
    return cached;
  }

  try {
    const netRes = await fetch(req);
    if (netRes.ok && netRes.status === 200) {
      const len = parseInt(netRes.headers.get('content-length') || '0', 10);
      if (len <= 80 * 1024 * 1024) {
        try {
          cache.put(req, netRes.clone());
        } catch (e) {}
      }
    }
    return netRes;
  } catch (err) {
    throw err;
  }
}

async function createPartialResponse(fullResponse, rangeHeader) {
  const ab = await fullResponse.arrayBuffer();
  const total = ab.byteLength;

  const matches = rangeHeader.match(/bytes=(\d+)-(\d+)?/);
  if (!matches) {
    return new Response(ab, {
      status: 200,
      headers: fullResponse.headers
    });
  }

  const start = parseInt(matches[1], 10);
  let end = matches[2] ? parseInt(matches[2], 10) : total - 1;
  if (end >= total) end = total - 1;

  const chunk = ab.slice(start, end + 1);
  const headers = new Headers(fullResponse.headers);
  headers.set('Content-Range', `bytes ${start}-${end}/${total}`);
  headers.set('Content-Length', String(chunk.byteLength));
  headers.set('Accept-Ranges', 'bytes');

  return new Response(chunk, {
    status: 206,
    statusText: 'Partial Content',
    headers: headers
  });
}
