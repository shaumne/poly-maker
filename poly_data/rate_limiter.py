"""
Rate Limiter for Polymarket API calls

This module implements rate limiting according to Polymarket API documentation:
https://docs.polymarket.com/quickstart/introduction/rate-limits

Rate limits are enforced using sliding time windows.
"""
import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter that tracks API calls per endpoint and enforces limits.
    
    Uses sliding time windows to track request counts and delays requests
    that would exceed the rate limit.
    """
    
    def __init__(self):
        # Track request timestamps per endpoint
        self._request_times: Dict[str, deque] = defaultdict(deque)
        self._locks: Dict[str, Lock] = defaultdict(Lock)
        
        # Rate limits from API documentation (requests per window_seconds)
        # Source: https://docs.polymarket.com/quickstart/introduction/rate-limits
        self._rate_limits = {
            # ========== GAMMA API ==========
            'gamma_events': {'requests': 100, 'window_seconds': 10},
            'gamma_markets': {'requests': 125, 'window_seconds': 10},
            'gamma_tags': {'requests': 100, 'window_seconds': 10},
            'gamma_general': {'requests': 750, 'window_seconds': 10},
            'gamma_search': {'requests': 300, 'window_seconds': 10},
            'gamma_comments': {'requests': 100, 'window_seconds': 10},
            'gamma_listing': {'requests': 100, 'window_seconds': 10},
            
            # ========== CLOB API - Trading ==========
            # POST /order - Sustained: 40/s (24000/10min), Burst: 240/s (2400/10s)
            'clob_post_order': {'requests': 40, 'window_seconds': 1},
            'clob_post_order_burst': {'requests': 240, 'window_seconds': 1},
            # DELETE /order - Sustained: 40/s (24000/10min), Burst: 240/s (2400/10s)
            'clob_delete_order': {'requests': 40, 'window_seconds': 1},
            'clob_delete_order_burst': {'requests': 240, 'window_seconds': 1},
            # POST /orders (batch) - Sustained: 20/s (12000/10min), Burst: 80/s (800/10s)
            'clob_post_orders': {'requests': 20, 'window_seconds': 1},
            'clob_post_orders_burst': {'requests': 80, 'window_seconds': 1},
            # DELETE /orders - Sustained: 20/s (12000/10min), Burst: 80/s (800/10s)
            'clob_delete_orders': {'requests': 20, 'window_seconds': 1},
            'clob_delete_orders_burst': {'requests': 80, 'window_seconds': 1},
            # DELETE /cancel-all - Sustained: 5/s (3000/10min), Burst: 20/s (200/10s)
            'clob_cancel_all': {'requests': 5, 'window_seconds': 1},
            'clob_cancel_all_burst': {'requests': 20, 'window_seconds': 1},
            # DELETE /cancel-market-orders - Sustained: 20/s (12000/10min), Burst: 80/s (800/10s)
            'clob_cancel_market_orders': {'requests': 20, 'window_seconds': 1},
            'clob_cancel_market_orders_burst': {'requests': 80, 'window_seconds': 1},
            
            # ========== CLOB API - Market Data ==========
            'clob_book': {'requests': 200, 'window_seconds': 10},
            'clob_books': {'requests': 80, 'window_seconds': 10},
            'clob_price': {'requests': 200, 'window_seconds': 10},
            'clob_prices': {'requests': 80, 'window_seconds': 10},
            'clob_midprice': {'requests': 200, 'window_seconds': 10},
            'clob_midprices': {'requests': 80, 'window_seconds': 10},
            'clob_markets': {'requests': 250, 'window_seconds': 10},
            'clob_markets_listing': {'requests': 100, 'window_seconds': 10},
            'clob_market_tick_size': {'requests': 50, 'window_seconds': 10},
            'clob_price_history': {'requests': 100, 'window_seconds': 10},
            
            # ========== CLOB API - Ledger ==========
            'clob_ledger': {'requests': 300, 'window_seconds': 10},  # /trades /orders /notifications /order
            'clob_data_orders': {'requests': 150, 'window_seconds': 10},
            'clob_data_trades': {'requests': 150, 'window_seconds': 10},
            'clob_notifications': {'requests': 125, 'window_seconds': 10},
            
            # ========== CLOB API - Authentication ==========
            'clob_api_keys': {'requests': 50, 'window_seconds': 10},
            'clob_balance_allowance_get': {'requests': 125, 'window_seconds': 10},
            'clob_balance_allowance_update': {'requests': 20, 'window_seconds': 10},
            
            # ========== Data API ==========
            'data_api_general': {'requests': 200, 'window_seconds': 10},
            'data_api_trades': {'requests': 75, 'window_seconds': 10},
            'data_api_ok': {'requests': 10, 'window_seconds': 10},
            
            # ========== Other APIs ==========
            'relayer_submit': {'requests': 15, 'window_seconds': 60},  # 15/minute
            'user_pnl_api': {'requests': 100, 'window_seconds': 10},
            
            # ========== General ==========
            'general': {'requests': 5000, 'window_seconds': 10},
            'ok_endpoint': {'requests': 50, 'window_seconds': 10},
        }
    
    def _clean_old_requests(self, endpoint: str, window_seconds: int):
        """Remove request timestamps outside the time window"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        with self._locks[endpoint]:
            request_times = self._request_times[endpoint]
            # Remove timestamps outside the window
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()
    
    def _should_wait(self, endpoint: str) -> Optional[float]:
        """
        Check if we need to wait before making a request.
        Returns the number of seconds to wait, or None if no wait needed.
        """
        if endpoint not in self._rate_limits:
            # No rate limit defined, allow immediately
            return None
        
        limit_config = self._rate_limits[endpoint]
        max_requests = limit_config['requests']
        window_seconds = limit_config['window_seconds']
        
        # Clean old requests outside the window
        self._clean_old_requests(endpoint, window_seconds)
        
        with self._locks[endpoint]:
            request_times = self._request_times[endpoint]
            current_count = len(request_times)
            
            if current_count < max_requests:
                # We can make the request immediately
                return None
            
            # We need to wait until the oldest request falls outside the window
            oldest_request_time = request_times[0]
            wait_time = (oldest_request_time + window_seconds) - time.time()
            
            # Add a small buffer to ensure we're safely within the limit
            return max(0, wait_time + 0.1)
    
    def _record_request(self, endpoint: str):
        """Record that a request was made"""
        with self._locks[endpoint]:
            self._request_times[endpoint].append(time.time())
    
    async def wait_if_needed(self, endpoint: str):
        """
        Wait if necessary to respect rate limits for the given endpoint.
        
        Args:
            endpoint: The endpoint identifier (e.g., 'gamma_events', 'clob_post_order')
        """
        wait_time = self._should_wait(endpoint)
        if wait_time and wait_time > 0:
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s for {endpoint}")
            await asyncio.sleep(wait_time)
    
    def wait_if_needed_sync(self, endpoint: str):
        """
        Synchronous version of wait_if_needed.
        
        Args:
            endpoint: The endpoint identifier (e.g., 'gamma_events', 'clob_post_order')
        """
        wait_time = self._should_wait(endpoint)
        if wait_time and wait_time > 0:
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s for {endpoint}")
            time.sleep(wait_time)
    
    def record_request(self, endpoint: str):
        """
        Record that a request was made to the given endpoint.
        Call this after making an API request.
        
        Args:
            endpoint: The endpoint identifier
        """
        self._record_request(endpoint)
    
    def get_rate_limit_info(self, endpoint: str) -> Optional[Dict]:
        """Get rate limit configuration for an endpoint"""
        return self._rate_limits.get(endpoint)


# Global rate limiter instance
_rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    return _rate_limiter


