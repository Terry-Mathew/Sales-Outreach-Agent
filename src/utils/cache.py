"""
Simple Cache - In-memory caching with TTL support.
"""

from typing import Any, Dict, Optional
import time
import hashlib
import json


class CacheEntry:
    """A single cache entry with value and metadata."""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.hits = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return time.time() > (self.created_at + self.ttl_seconds)
    
    @property
    def age_seconds(self) -> float:
        """How old is this entry in seconds."""
        return time.time() - self.created_at


class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    Useful for caching LLM responses to avoid redundant API calls.
    """
    
    def __init__(self, default_ttl: int = 3600, max_size: int = 100):
        """
        Initialize the cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
            max_size: Maximum number of entries to store
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = json.dumps({
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
        }, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired:
            del self._cache[key]
            self._misses += 1
            return None
        
        entry.hits += 1
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        # Evict oldest entries if at capacity
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        ttl = ttl if ttl is not None else self._default_ttl
        self._cache[key] = CacheEntry(value, ttl)
    
    def _evict_oldest(self) -> None:
        """Evict the oldest entry to make room."""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]
    
    def invalidate(self, key: str) -> bool:
        """
        Remove a specific key from cache.
        
        Returns:
            True if key was found and removed
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            k for k, v in self._cache.items() if v.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)
    
    @property
    def size(self) -> int:
        """Number of entries in cache."""
        return len(self._cache)
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a percentage."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return round((self._hits / total) * 100, 2)
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": self.hit_rate,
            "default_ttl_seconds": self._default_ttl,
        }


# Global singleton
_global_cache: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = SimpleCache()
    return _global_cache
