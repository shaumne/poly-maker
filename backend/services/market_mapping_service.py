"""
Market-Token Mapping Service

Provides fast token_id to market lookup with LRU cache for performance optimization.
"""
from functools import lru_cache
from typing import Optional, Dict
from sqlalchemy.orm import Session, joinedload
from threading import Lock
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import SessionLocal, Market, TradingParams


class TokenMarketMapper:
    """
    Service for mapping token IDs and condition IDs to Market objects.
    Uses LRU cache for fast lookups and provides cache invalidation.
    """
    
    def __init__(self, cache_size: int = 1000):
        """
        Initialize the mapper with a cache.
        
        Args:
            cache_size: Maximum number of items to cache (default: 1000)
        """
        self.cache_size = cache_size
        self._lock = Lock()
        # Cache dictionaries
        self._token_to_market_cache: Dict[str, Optional[Market]] = {}
        self._condition_to_market_cache: Dict[str, Optional[Market]] = {}
        self._cache_access_order: list = []  # For LRU eviction
        
    def _get_db_session(self) -> Session:
        """Get a database session"""
        return SessionLocal()
    
    def _evict_lru(self):
        """Evict least recently used items from cache"""
        if len(self._token_to_market_cache) >= self.cache_size:
            # Remove oldest accessed items
            to_remove = len(self._token_to_market_cache) - self.cache_size + 1
            for _ in range(to_remove):
                if self._cache_access_order:
                    key = self._cache_access_order.pop(0)
                    if key.startswith('token:'):
                        token_id = key.replace('token:', '')
                        self._token_to_market_cache.pop(token_id, None)
                    elif key.startswith('condition:'):
                        condition_id = key.replace('condition:', '')
                        self._condition_to_market_cache.pop(condition_id, None)
    
    def _update_access_order(self, key: str):
        """Update access order for LRU eviction"""
        if key in self._cache_access_order:
            self._cache_access_order.remove(key)
        self._cache_access_order.append(key)
    
    def get_market_by_token_id(self, token_id: str) -> Optional[Market]:
        """
        Get market by token ID (token1 or token2).
        
        Args:
            token_id: Token ID to lookup
            
        Returns:
            Market object if found, None otherwise
        """
        if not token_id:
            return None
        
        # Convert to string for consistency
        token_id = str(token_id)
        cache_key = f'token:{token_id}'
        
        with self._lock:
            # Check cache first
            if token_id in self._token_to_market_cache:
                self._update_access_order(cache_key)
                return self._token_to_market_cache[token_id]
        
        # Cache miss - query database
        db = self._get_db_session()
        try:
            # Query for markets where token_id matches token1 or token2
            # Use eager loading to avoid detached instance errors
            # Note: We don't filter by is_active here - let validation service handle that
            market = db.query(Market).options(
                joinedload(Market.trading_params)
            ).filter(
                (Market.token1 == token_id) | (Market.token2 == token_id)
            ).first()
            
            # If market found, detach it from session before caching
            # We need to access trading_params while still in session to load it
            if market:
                # Access trading_params to ensure it's loaded (eager loading should handle this)
                trading_params = market.trading_params  # Force load if not already loaded
                # Now expunge to detach from session
                db.expunge(market)
                # Try to expunge trading_params if it exists
                # Note: trading_params might not be in the session if it was loaded via joinedload
                # and already detached, so we wrap in try-except
                if trading_params:
                    try:
                        db.expunge(trading_params)
                    except Exception:
                        # If expunge fails, it's okay - the object might not be in session
                        # or might already be detached. The relationship will still work in cache.
                        pass
            
            with self._lock:
                # Store in cache
                self._evict_lru()
                if market:
                    self._token_to_market_cache[token_id] = market
                    self._update_access_order(cache_key)
            
            return market
        finally:
            db.close()
    
    def get_market_by_condition_id(self, condition_id: str) -> Optional[Market]:
        """
        Get market by condition ID.
        
        Args:
            condition_id: Condition ID to lookup
            
        Returns:
            Market object if found, None otherwise
        """
        if not condition_id:
            return None
        
        # Convert to string for consistency
        condition_id = str(condition_id)
        cache_key = f'condition:{condition_id}'
        
        with self._lock:
            # Check cache first
            if condition_id in self._condition_to_market_cache:
                self._update_access_order(cache_key)
                return self._condition_to_market_cache[condition_id]
        
        # Cache miss - query database
        db = self._get_db_session()
        try:
            # Use eager loading to avoid detached instance errors
            market = db.query(Market).options(
                joinedload(Market.trading_params)
            ).filter(
                Market.condition_id == condition_id
            ).first()
            
            # If market found, detach it from session before caching
            if market:
                # Access trading_params to ensure it's loaded
                trading_params = market.trading_params  # Force load if not already loaded
                # Now expunge to detach from session
                db.expunge(market)
                # Try to expunge trading_params if it exists
                # Note: trading_params might not be in the session if it was loaded via joinedload
                # and already detached, so we wrap in try-except
                if trading_params:
                    try:
                        db.expunge(trading_params)
                    except Exception:
                        # If expunge fails, it's okay - the object might not be in session
                        # or might already be detached. The relationship will still work in cache.
                        pass
            
            with self._lock:
                # Store in cache
                self._evict_lru()
                if market:
                    self._condition_to_market_cache[condition_id] = market
                    self._update_access_order(cache_key)
            
            return market
        finally:
            db.close()
    
    def invalidate_token_cache(self, token_id: str):
        """
        Invalidate cache for a specific token ID.
        
        Args:
            token_id: Token ID to invalidate
        """
        token_id = str(token_id)
        with self._lock:
            if token_id in self._token_to_market_cache:
                del self._token_to_market_cache[token_id]
            # Remove from access order
            cache_key = f'token:{token_id}'
            if cache_key in self._cache_access_order:
                self._cache_access_order.remove(cache_key)
    
    def invalidate_condition_cache(self, condition_id: str):
        """
        Invalidate cache for a specific condition ID.
        
        Args:
            condition_id: Condition ID to invalidate
        """
        condition_id = str(condition_id)
        with self._lock:
            if condition_id in self._condition_to_market_cache:
                del self._condition_to_market_cache[condition_id]
            # Remove from access order
            cache_key = f'condition:{condition_id}'
            if cache_key in self._cache_access_order:
                self._cache_access_order.remove(cache_key)
    
    def invalidate_market_cache(self, market: Market):
        """
        Invalidate cache for a market (both tokens and condition).
        
        Args:
            market: Market object to invalidate
        """
        if market:
            self.invalidate_token_cache(market.token1)
            self.invalidate_token_cache(market.token2)
            self.invalidate_condition_cache(market.condition_id)
    
    def clear_cache(self):
        """Clear all caches"""
        with self._lock:
            self._token_to_market_cache.clear()
            self._condition_to_market_cache.clear()
            self._cache_access_order.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                'token_cache_size': len(self._token_to_market_cache),
                'condition_cache_size': len(self._condition_to_market_cache),
                'total_cached': len(self._token_to_market_cache) + len(self._condition_to_market_cache),
                'max_cache_size': self.cache_size
            }


# Global singleton instance
_mapper_instance: Optional[TokenMarketMapper] = None
_mapper_lock = Lock()


def get_market_mapper() -> TokenMarketMapper:
    """
    Get the global TokenMarketMapper instance (singleton pattern).
    
    Returns:
        TokenMarketMapper instance
    """
    global _mapper_instance
    if _mapper_instance is None:
        with _mapper_lock:
            if _mapper_instance is None:
                _mapper_instance = TokenMarketMapper()
    return _mapper_instance

