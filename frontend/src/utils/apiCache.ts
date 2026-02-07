/**
 * Advanced API Response Caching Utility
 * Provides intelligent caching with TTL, invalidation patterns, and storage persistence
 */

// Cache entry interface
interface CacheEntry<T = any> {
  data: T
  timestamp: number
  ttl: number
  tags: string[]
  accessCount: number
  lastAccessed: number
}

// Cache configuration
interface CacheConfig {
  defaultTTL: number // Default time-to-live in milliseconds
  maxSize: number // Maximum number of entries
  persistToStorage: boolean // Whether to persist to localStorage
  storageKey: string // Key for localStorage
}

// Cache statistics
interface CacheStats {
  hits: number
  misses: number
  size: number
  hitRate: number
}

class ApiCache {
  private cache = new Map<string, CacheEntry>()
  private stats = { hits: 0, misses: 0 }
  private config: CacheConfig

  constructor(config: Partial<CacheConfig> = {}) {
    this.config = {
      defaultTTL: 5 * 60 * 1000, // 5 minutes
      maxSize: 100,
      persistToStorage: true,
      storageKey: 'api_cache',
      ...config
    }

    // Load from localStorage if enabled
    if (this.config.persistToStorage) {
      this.loadFromStorage()
    }

    // Set up periodic cleanup
    setInterval(() => this.cleanup(), 60000) // Cleanup every minute
  }

  // Generate cache key from URL and parameters
  private generateKey(url: string, params?: Record<string, any>): string {
    const paramString = params ? JSON.stringify(params) : ''
    return `${url}:${paramString}`
  }

  // Check if entry is expired
  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl
  }

  // Get entry from cache
  get<T>(url: string, params?: Record<string, any>): T | null {
    const key = this.generateKey(url, params)
    const entry = this.cache.get(key)

    if (!entry) {
      this.stats.misses++
      return null
    }

    if (this.isExpired(entry)) {
      this.cache.delete(key)
      this.stats.misses++
      return null
    }

    // Update access statistics
    entry.accessCount++
    entry.lastAccessed = Date.now()
    this.stats.hits++

    return entry.data as T
  }

  // Set entry in cache
  set<T>(
    url: string, 
    data: T, 
    options: {
      params?: Record<string, any>
      ttl?: number
      tags?: string[]
    } = {}
  ): void {
    const { params, ttl = this.config.defaultTTL, tags = [] } = options
    const key = this.generateKey(url, params)

    // Ensure we don't exceed max size
    if (this.cache.size >= this.config.maxSize) {
      this.evictLeastRecentlyUsed()
    }

    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
      tags,
      accessCount: 0,
      lastAccessed: Date.now()
    }

    this.cache.set(key, entry)

    // Persist to storage if enabled
    if (this.config.persistToStorage) {
      this.saveToStorage()
    }
  }

  // Check if entry exists and is valid
  has(url: string, params?: Record<string, any>): boolean {
    const key = this.generateKey(url, params)
    const entry = this.cache.get(key)
    return entry !== undefined && !this.isExpired(entry)
  }

  // Delete specific entry
  delete(url: string, params?: Record<string, any>): boolean {
    const key = this.generateKey(url, params)
    const deleted = this.cache.delete(key)
    
    if (deleted && this.config.persistToStorage) {
      this.saveToStorage()
    }
    
    return deleted
  }

  // Invalidate entries by tag
  invalidateByTag(tag: string): number {
    let invalidated = 0
    
    for (const [key, entry] of this.cache.entries()) {
      if (entry.tags.includes(tag)) {
        this.cache.delete(key)
        invalidated++
      }
    }

    if (invalidated > 0 && this.config.persistToStorage) {
      this.saveToStorage()
    }

    return invalidated
  }

  // Invalidate entries by URL pattern
  invalidateByPattern(pattern: string | RegExp): number {
    let invalidated = 0
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern
    
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key)
        invalidated++
      }
    }

    if (invalidated > 0 && this.config.persistToStorage) {
      this.saveToStorage()
    }

    return invalidated
  }

  // Clear all cache entries
  clear(): void {
    this.cache.clear()
    this.stats = { hits: 0, misses: 0 }
    
    if (this.config.persistToStorage) {
      localStorage.removeItem(this.config.storageKey)
    }
  }

  // Get cache statistics
  getStats(): CacheStats {
    const total = this.stats.hits + this.stats.misses
    return {
      ...this.stats,
      size: this.cache.size,
      hitRate: total > 0 ? this.stats.hits / total : 0
    }
  }

  // Cleanup expired entries
  private cleanup(): void {
    let cleaned = 0
    
    for (const [key, entry] of this.cache.entries()) {
      if (this.isExpired(entry)) {
        this.cache.delete(key)
        cleaned++
      }
    }

    if (cleaned > 0 && this.config.persistToStorage) {
      this.saveToStorage()
    }
  }

  // Evict least recently used entry
  private evictLeastRecentlyUsed(): void {
    let oldestKey: string | null = null
    let oldestTime = Date.now()

    for (const [key, entry] of this.cache.entries()) {
      if (entry.lastAccessed < oldestTime) {
        oldestTime = entry.lastAccessed
        oldestKey = key
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey)
    }
  }

  // Save cache to localStorage
  private saveToStorage(): void {
    try {
      const serializable = Array.from(this.cache.entries())
      localStorage.setItem(this.config.storageKey, JSON.stringify(serializable))
    } catch (error) {
      console.warn('Failed to save cache to localStorage:', error)
    }
  }

  // Load cache from localStorage
  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.config.storageKey)
      if (stored) {
        const entries: [string, CacheEntry][] = JSON.parse(stored)
        
        // Filter out expired entries during load
        const now = Date.now()
        for (const [key, entry] of entries) {
          if (now - entry.timestamp <= entry.ttl) {
            this.cache.set(key, entry)
          }
        }
      }
    } catch (error) {
      console.warn('Failed to load cache from localStorage:', error)
    }
  }

  // Get all cache keys (for debugging)
  getKeys(): string[] {
    return Array.from(this.cache.keys())
  }

  // Get cache entry details (for debugging)
  getEntry(url: string, params?: Record<string, any>): CacheEntry | null {
    const key = this.generateKey(url, params)
    return this.cache.get(key) || null
  }
}

// Create singleton instance
export const apiCache = new ApiCache()

// Cache invalidation helpers
export const cacheInvalidation = {
  // Invalidate all user-related data
  invalidateUserData: () => {
    apiCache.invalidateByTag('user')
    apiCache.invalidateByPattern(/\/auth\//)
  },

  // Invalidate all document-related data
  invalidateDocuments: () => {
    apiCache.invalidateByTag('documents')
    apiCache.invalidateByPattern(/\/scaledown\//)
  },

  // Invalidate all onboarding data
  invalidateOnboarding: () => {
    apiCache.invalidateByTag('onboarding')
    apiCache.invalidateByPattern(/\/onboarding\//)
  },

  // Invalidate all analytics data
  invalidateAnalytics: () => {
    apiCache.invalidateByTag('analytics')
    apiCache.invalidateByPattern(/\/analytics\//)
  },

  // Invalidate engagement data
  invalidateEngagement: () => {
    apiCache.invalidateByTag('engagement')
    apiCache.invalidateByPattern(/\/engagement\//)
  },

  // Invalidate intervention data
  invalidateIntervention: () => {
    apiCache.invalidateByTag('intervention')
    apiCache.invalidateByPattern(/\/intervention\//)
  },

  // Invalidate all data
  invalidateAll: () => {
    apiCache.clear()
  }
}

// Cache warming utilities
export const cacheWarming = {
  // Warm up common user data
  warmUserData: async (api: any) => {
    try {
      await Promise.all([
        api.auth.getCurrentUser(),
        api.onboarding.getUserSessions(),
        api.documents.getAll()
      ])
    } catch (error) {
      console.warn('Cache warming failed:', error)
    }
  },

  // Warm up analytics data
  warmAnalyticsData: async (api: any) => {
    try {
      await Promise.all([
        api.analytics.getDashboardData(),
        api.analytics.getRealTimeMetrics(),
        api.analytics.getAvailableRoles()
      ])
    } catch (error) {
      console.warn('Analytics cache warming failed:', error)
    }
  }
}

// Cache debugging utilities
export const cacheDebug = {
  // Log cache statistics
  logStats: () => {
    const stats = apiCache.getStats()
    console.log('API Cache Statistics:', stats)
  },

  // Log all cache keys
  logKeys: () => {
    const keys = apiCache.getKeys()
    console.log('API Cache Keys:', keys)
  },

  // Log specific entry
  logEntry: (url: string, params?: Record<string, any>) => {
    const entry = apiCache.getEntry(url, params)
    console.log(`Cache entry for ${url}:`, entry)
  }
}

export { ApiCache }
export type { CacheEntry, CacheConfig, CacheStats }