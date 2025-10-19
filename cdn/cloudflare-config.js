/**
 * CloudFlare Workers for Edge Computing
 * Handles caching and routing at edge locations worldwide
 */

// CloudFlare Worker Configuration
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  
  // Cache configuration
  const cacheConfig = {
    '/api/v1/papers': { ttl: 3600, browser: 1800 },      // 1 hour edge, 30 min browser
    '/api/v1/search': { ttl: 300, browser: 60 },         // 5 min edge, 1 min browser
    '/static/': { ttl: 86400, browser: 86400 },          // 24 hours
    '/api/v1/ask': { ttl: 0, browser: 0 }                // No cache for dynamic queries
  }
  
  // Determine cache strategy
  let cacheTtl = 0
  let browserTtl = 0
  
  for (const [path, config] of Object.entries(cacheConfig)) {
    if (url.pathname.startsWith(path)) {
      cacheTtl = config.ttl
      browserTtl = config.browser
      break
    }
  }
  
  // Check CloudFlare cache
  const cacheKey = new Request(url.toString(), request)
  const cache = caches.default
  
  if (cacheTtl > 0) {
    let response = await cache.match(cacheKey)
    
    if (response) {
      // Add cache hit header
      response = new Response(response.body, response)
      response.headers.set('X-Cache', 'HIT')
      response.headers.set('X-Cache-Region', request.cf.colo)
      return response
    }
  }
  
  // Fetch from origin
  let response = await fetch(request)
  
  // Clone response for caching
  response = new Response(response.body, response)
  
  // Add cache control headers
  if (cacheTtl > 0 && response.status === 200) {
    response.headers.set('Cache-Control', `public, max-age=${browserTtl}, s-maxage=${cacheTtl}`)
    response.headers.set('X-Cache', 'MISS')
    
    // Store in edge cache
    event.waitUntil(cache.put(cacheKey, response.clone()))
  }
  
  // Add security headers
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  
  // Add CORS if needed
  if (request.headers.get('Origin')) {
    response.headers.set('Access-Control-Allow-Origin', request.headers.get('Origin'))
    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  }
  
  return response
}

// Rate limiting at edge
const rateLimits = new Map()

async function checkRateLimit(ip) {
  const key = `ratelimit:${ip}`
  const limit = 1000 // requests per minute
  const window = 60 // seconds
  
  const now = Math.floor(Date.now() / 1000)
  const windowStart = now - (now % window)
  
  if (!rateLimits.has(key)) {
    rateLimits.set(key, { count: 1, windowStart })
    return true
  }
  
  const data = rateLimits.get(key)
  
  if (data.windowStart !== windowStart) {
    // New window
    data.count = 1
    data.windowStart = windowStart
    return true
  }
  
  if (data.count >= limit) {
    return false
  }
  
  data.count++
  return true
}

// Geo-routing based on user location
function getClosestOrigin(request) {
  const country = request.cf.country
  const continent = request.cf.continent
  
  // Route to nearest data center
  const origins = {
    'NA': 'https://us-api.yourdomain.com',
    'EU': 'https://eu-api.yourdomain.com',
    'AS': 'https://asia-api.yourdomain.com',
    'OC': 'https://au-api.yourdomain.com'
  }
  
  return origins[continent] || origins['NA']
}