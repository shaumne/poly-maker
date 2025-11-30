"""
Market Cache Service

Provides synchronization between database and cache, with periodic refresh
and event-driven invalidation.
"""
import threading
import time
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import SessionLocal, Market
from services.market_mapping_service import get_market_mapper


class MarketCacheService:
    """
    Service for managing market cache synchronization.
    Provides periodic refresh and event-driven invalidation.
    """
    
    def __init__(self, refresh_interval_seconds: int = 300):
        """
        Initialize the cache service.
        
        Args:
            refresh_interval_seconds: How often to refresh cache from database (default: 5 minutes)
        """
        self.refresh_interval = refresh_interval_seconds
        self.mapper = get_market_mapper()
        self._lock = threading.Lock()
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        self._last_refresh: Optional[datetime] = None
        self._is_running = False
    
    def start_periodic_refresh(self):
        """Start periodic cache refresh in background thread"""
        if self._is_running:
            return
        
        self._stop_refresh.clear()
        self._is_running = True
        
        def refresh_loop():
            while not self._stop_refresh.is_set():
                try:
                    self.refresh_cache()
                except Exception as e:
                    print(f"Error in cache refresh: {e}")
                
                # Wait for refresh interval or until stop event
                if self._stop_refresh.wait(timeout=self.refresh_interval):
                    break
        
        self._refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        self._refresh_thread.start()
        print(f"Market cache service started with {self.refresh_interval}s refresh interval")
    
    def stop_periodic_refresh(self):
        """Stop periodic cache refresh"""
        if not self._is_running:
            return
        
        self._stop_refresh.set()
        if self._refresh_thread:
            self._refresh_thread.join(timeout=5.0)
        self._is_running = False
        print("Market cache service stopped")
    
    def refresh_cache(self):
        """
        Refresh cache from database.
        Loads all active markets and updates the cache.
        """
        db = SessionLocal()
        try:
            # Get all active markets
            markets = db.query(Market).filter(Market.is_active == True).all()
            
            with self._lock:
                # Clear existing cache
                self.mapper.clear_cache()
                
                # Pre-populate cache with all active markets
                for market in markets:
                    # Add to cache by condition_id
                    self.mapper._condition_to_market_cache[market.condition_id] = market
                    # Add to cache by token1
                    self.mapper._token_to_market_cache[str(market.token1)] = market
                    # Add to cache by token2
                    self.mapper._token_to_market_cache[str(market.token2)] = market
                
                self._last_refresh = datetime.utcnow()
            
            print(f"Cache refreshed: {len(markets)} active markets loaded")
        except Exception as e:
            print(f"Error refreshing cache: {e}")
        finally:
            db.close()
    
    def invalidate_market(self, market_id: Optional[int] = None, condition_id: Optional[str] = None, 
                         token_id: Optional[str] = None):
        """
        Invalidate cache for a specific market.
        
        Args:
            market_id: Market database ID
            condition_id: Market condition ID
            token_id: Token ID (token1 or token2)
        """
        db = SessionLocal()
        try:
            # Get market from database
            if market_id:
                market = db.query(Market).filter(Market.id == market_id).first()
            elif condition_id:
                market = db.query(Market).filter(Market.condition_id == condition_id).first()
            elif token_id:
                market = db.query(Market).filter(
                    ((Market.token1 == token_id) | (Market.token2 == token_id))
                ).first()
            else:
                return
            
            if market:
                self.mapper.invalidate_market_cache(market)
        finally:
            db.close()
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        mapper_stats = self.mapper.get_cache_stats()
        
        with self._lock:
            return {
                **mapper_stats,
                'last_refresh': self._last_refresh.isoformat() if self._last_refresh else None,
                'is_running': self._is_running,
                'refresh_interval_seconds': self.refresh_interval
            }
    
    def clear_all_cache(self):
        """Clear all caches"""
        self.mapper.clear_cache()
        with self._lock:
            self._last_refresh = None


# Global singleton instance
_cache_service_instance: Optional[MarketCacheService] = None
_cache_service_lock = threading.Lock()


def get_market_cache_service() -> MarketCacheService:
    """
    Get the global MarketCacheService instance (singleton pattern).
    
    Returns:
        MarketCacheService instance
    """
    global _cache_service_instance
    if _cache_service_instance is None:
        with _cache_service_lock:
            if _cache_service_instance is None:
                _cache_service_instance = MarketCacheService()
    return _cache_service_instance

