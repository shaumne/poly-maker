"""
Market fetching and filtering service
"""
import requests
import pandas as pd
from typing import List, Dict, Optional
import os
from datetime import datetime, timedelta
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from poly_data.rate_limiter import get_rate_limiter

# Use robust env loading that handles BOM and encoding issues
try:
    from poly_data.env_utils import load_dotenv_safe
    load_dotenv_safe()
except ImportError:
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8-sig')

# Gamma API base URL
GAMMA_API_BASE = "https://gamma-api.polymarket.com"

# Crypto-related keywords for filtering
CRYPTO_KEYWORDS = [
    # Major cryptocurrencies
    'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 
    'cardano', 'ada', 'polkadot', 'dot', 'avalanche', 'avax',
    'polygon', 'matic', 'chainlink', 'link', 'litecoin', 'ltc',
    'ripple', 'xrp', 'dogecoin', 'doge', 'shiba', 'ethereum classic', 'etc',
    'hyperliquid', 'hype', 'hyper',
    
    # Stablecoins and tokens
    'uniswap', 'uni', 'aave', 'maker', 'mkr', 'compound', 'comp',
    'tether', 'usdt', 'usdc', 'dai', 'binance', 'bnb', 'ftx', 'ftm',
    'fantom', 'cosmos', 'atom', 'algorand', 'algo', 'tezos', 'xtz',
    'monero', 'xmr', 'zcash', 'zec', 'stellar', 'xlm', 'eos',
    'tron', 'trx', 'neo', 'dash', 'iota', 'vechain', 'vet',
    'theta', 'filecoin', 'fil', 'decentraland', 'mana', 'sandbox', 'sand',
    'axie', 'gala', 'enjin', 'enj', 'chiliz', 'chz', 'wbtc', 'steth',
    
    # General crypto terms
    'crypto', 'cryptocurrency', 'blockchain', 'defi', 'nft', 'web3',
    'metaverse', 'token', 'coin', 'satoshi', 'altcoin', 'alt coin',
    
    # Price prediction patterns
    'price', 'hit', 'reach', 'above', 'below', 'trading', 'trade',
    'november', 'december', 'january', 'february', 'march', 'april',
    'may', 'june', 'july', 'august', 'september', 'october',
    'weekly', 'monthly', 'daily', 'end of', 'by end', 'by',
    'will', 'will bitcoin', 'will ethereum', 'will solana',
    'what price', 'what will', 'price will'
]

class MarketService:
    """Service for fetching and filtering Polymarket markets"""
    
    def __init__(self):
        """Initialize market service with Polymarket client"""
        self.client = None
        self.tag_cache = {}  # Cache for tag_id mappings: {'crypto': tag_id, 'politics': tag_id, ...}
        self._init_client()
        # Lazy import to avoid circular dependencies
        self._mapper = None
    
    def _get_mapper(self):
        """Get market mapper instance (lazy initialization)"""
        if self._mapper is None:
            from services.market_mapping_service import get_market_mapper
            self._mapper = get_market_mapper()
        return self._mapper
    
    def invalidate_market_cache(self, market):
        """
        Invalidate cache for a market after create/update/delete operations.
        
        Args:
            market: Market object or dict with market data
        """
        try:
            mapper = self._get_mapper()
            if hasattr(market, 'token1') and hasattr(market, 'token2'):
                # Market object
                mapper.invalidate_market_cache(market)
            elif isinstance(market, dict):
                # Market dict - invalidate by token IDs
                token1 = market.get('token1')
                token2 = market.get('token2')
                condition_id = market.get('condition_id')
                if token1:
                    mapper.invalidate_token_cache(token1)
                if token2:
                    mapper.invalidate_token_cache(token2)
                if condition_id:
                    mapper.invalidate_condition_cache(condition_id)
        except Exception as e:
            # Don't fail if cache invalidation fails
            print(f"Warning: Failed to invalidate cache: {e}")
    
    def _init_client(self):
        """Initialize Polymarket CLOB client"""
        try:
            host = "https://clob.polymarket.com"
            key = os.getenv("PK")
            
            if not key or key == "your_private_key_here":
                print("Warning: PK not set or using default value. Some operations may fail.")
                print("Please set PK in your .env file to enable full functionality.")
                # Try to create read-only client
                try:
                    self.client = ClobClient(host=host, chain_id=POLYGON)
                    print("Initialized read-only Polymarket client (no private key)")
                except Exception as e:
                    print(f"Failed to initialize read-only client: {e}")
                    self.client = None
            else:
                try:
                    self.client = ClobClient(
                        host=host,
                        key=key,
                        chain_id=POLYGON,
                        signature_type=2
                    )
                    print("Successfully initialized Polymarket client with private key")
                except Exception as e:
                    print(f"Failed to initialize Polymarket client with key: {e}")
                    print("Falling back to read-only client...")
                    try:
                        self.client = ClobClient(host=host, chain_id=POLYGON)
                    except Exception as e2:
                        print(f"Failed to initialize read-only client: {e2}")
                        self.client = None
        except Exception as e:
            print(f"Unexpected error initializing Polymarket client: {e}")
            self.client = None
    
    def _load_all_tags(self) -> Dict[str, int]:
        """
        Fetch all tags from Gamma API and map them to our categories.
        Returns dict: {'crypto': tag_id, 'politics': tag_id, ...}
        """
        if self.tag_cache:
            return self.tag_cache
        
        try:
            print("Fetching all tags from Gamma API...")
            # Apply rate limiting for GAMMA tags endpoint (100 requests / 10s)
            rate_limiter = get_rate_limiter()
            rate_limiter.wait_if_needed_sync('gamma_tags')
            response = requests.get(f"{GAMMA_API_BASE}/tags", timeout=10)
            rate_limiter.record_request('gamma_tags')
            if response.status_code == 200:
                tags_data = response.json()
                
                # Handle different response formats
                if isinstance(tags_data, dict):
                    tags = tags_data.get('data', tags_data.get('results', []))
                elif isinstance(tags_data, list):
                    tags = tags_data
                else:
                    tags = []
                
                print(f"Found {len(tags)} tags")
                
                # Debug: Print first few tags to see structure
                if tags:
                    print(f"Sample tag structure: {tags[0]}")
                
                # Debug: Print all tag labels and slugs for easier debugging
                print(f"\nAll available tags ({len(tags)} total):")
                crypto_related_tags = []
                for i, tag in enumerate(tags):
                    tag_label = tag.get('label', 'N/A').lower()
                    tag_slug = tag.get('slug', 'N/A').lower()
                    tag_id = tag.get('id', 'N/A')
                    
                    # Check if this might be crypto-related
                    if any(keyword in tag_label or keyword in tag_slug for keyword in 
                           ['crypto', 'bitcoin', 'ethereum', 'btc', 'eth', 'blockchain', 'defi', 'sol', 'solana']):
                        crypto_related_tags.append((tag_id, tag.get('label', 'N/A'), tag.get('slug', 'N/A')))
                    
                    # Print first 100 tags
                    if i < 100:
                        print(f"  [{tag_id}] {tag.get('label', 'N/A')} ({tag.get('slug', 'N/A')})")
                
                if len(tags) > 100:
                    print(f"  ... and {len(tags) - 100} more tags")
                
                if crypto_related_tags:
                    print(f"\n⚠️  Found {len(crypto_related_tags)} potentially crypto-related tags:")
                    for tag_id, label, slug in crypto_related_tags:
                        print(f"    [{tag_id}] {label} ({slug})")
                else:
                    print(f"\n⚠️  No crypto-related tags found in the list!")
                
                # Category name mappings (what we call them vs what Polymarket calls them)
                # Expanded with more variations and exact matches
                category_mappings = {
                    'crypto': ['crypto', 'cryptocurrency', 'cryptocurrencies', 'bitcoin', 'ethereum', 'btc', 'eth', 
                              'blockchain', 'defi', 'solana', 'sol', 'cardano', 'ada', 'polkadot', 'dot',
                              'avalanche', 'avax', 'polygon', 'matic', 'chainlink', 'link', 'litecoin', 'ltc',
                              'ripple', 'xrp', 'dogecoin', 'doge', 'hyperliquid', 'hype'],
                    'politics': ['politics', 'political', 'election', 'elections', 'government', 'president',
                                'presidential', 'congress', 'senate', 'house', 'democrat', 'republican',
                                'trump', 'biden', 'kamala', 'harris', 'voting', 'vote', 'ballot'],
                    'sports': ['sports', 'sport', 'nfl', 'nba', 'mlb', 'nhl', 'soccer', 'football',
                              'basketball', 'baseball', 'hockey', 'tennis', 'golf', 'mma', 'ufc',
                              'boxing', 'olympics', 'world cup', 'super bowl', 'stanley cup'],
                    'economics': ['economics', 'economic', 'finance', 'financial', 'fed', 'federal reserve',
                                 'inflation', 'gdp', 'unemployment', 'interest rate', 'rate cut', 'rate hike',
                                 'monetary policy', 'treasury', 'dollar', 'currency', 'market'],
                    'entertainment': ['entertainment', 'movies', 'music', 'tv', 'television', 'celebrity',
                                     'oscar', 'grammy', 'emmy', 'award', 'film', 'actor', 'actress',
                                     'director', 'box office', 'album', 'song', 'artist'],
                    'technology': ['technology', 'tech', 'ai', 'artificial intelligence', 'software',
                                  'apple', 'google', 'microsoft', 'meta', 'facebook', 'amazon', 'tesla',
                                  'openai', 'chatgpt', 'gpt', 'llm', 'machine learning', 'ml'],
                    'science': ['science', 'scientific', 'space', 'nasa', 'research', 'medical',
                               'health', 'covid', 'vaccine', 'climate', 'environment', 'earth',
                               'mars', 'moon', 'astronomy', 'physics', 'chemistry', 'biology']
                }
                
                # Find matching tags for each category
                # Tag structure: {'id': '207', 'label': 'dating', 'slug': 'dating', ...}
                for category, keywords in category_mappings.items():
                    for tag in tags:
                        # Use label and slug fields (these are the actual fields in the API response)
                        tag_label = (tag.get('label') or '').lower()
                        tag_slug = (tag.get('slug') or '').lower()
                        tag_text = f"{tag_label} {tag_slug}".lower()
                        
                        # Check if tag matches any keyword for this category
                        # Try exact match first, then substring match
                        matched = False
                        for keyword in keywords:
                            keyword_lower = keyword.lower()
                            # Exact match (whole word or exact string)
                            if (keyword_lower == tag_label or keyword_lower == tag_slug or 
                                f" {keyword_lower} " in f" {tag_text} " or
                                tag_text.startswith(keyword_lower + ' ') or
                                tag_text.endswith(' ' + keyword_lower)):
                                matched = True
                                break
                        
                        if matched:
                            tag_id = tag.get('id')
                            if tag_id:
                                # Convert to int if it's a string
                                try:
                                    tag_id = int(tag_id) if isinstance(tag_id, str) else tag_id
                                except (ValueError, TypeError):
                                    continue
                                
                                self.tag_cache[category] = tag_id
                                tag_display_name = tag.get('label') or tag.get('slug') or 'N/A'
                                print(f"  {category}: tag_id={tag_id} ({tag_display_name})")
                                break  # Found one, move to next category
                
                # If crypto not found, try to find it by checking all tags more thoroughly
                if 'crypto' not in self.tag_cache:
                    print("  Searching for crypto tag in all tags...")
                    crypto_keywords_extended = ['crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'btc', 'eth', 
                                              'blockchain', 'defi', 'sol', 'solana', 'cardano', 'ada', 'polkadot',
                                              'dot', 'avalanche', 'avax', 'polygon', 'matic', 'chainlink', 'link',
                                              'litecoin', 'ltc', 'ripple', 'xrp', 'dogecoin', 'doge', 'hyperliquid', 'hype']
                    for tag in tags:
                        tag_label = (tag.get('label') or '').lower()
                        tag_slug = (tag.get('slug') or '').lower()
                        tag_str = f"{tag_label} {tag_slug}".lower()
                        
                        # More strict matching for crypto - avoid false positives like "schiff" matching "link"
                        for keyword in crypto_keywords_extended:
                            keyword_lower = keyword.lower()
                            # Only match if keyword is exact match or starts/ends with keyword
                            # This prevents "schiff" matching "link" from "chainlink"
                            if (keyword_lower == tag_label or keyword_lower == tag_slug or
                                tag_label.startswith(keyword_lower + ' ') or tag_label.endswith(' ' + keyword_lower) or
                                tag_slug.startswith(keyword_lower + '-') or tag_slug.endswith('-' + keyword_lower)):
                                tag_id = tag.get('id')
                                if tag_id:
                                    try:
                                        tag_id = int(tag_id) if isinstance(tag_id, str) else tag_id
                                    except (ValueError, TypeError):
                                        continue
                                    
                                    self.tag_cache['crypto'] = tag_id
                                    tag_display_name = tag.get('label') or tag.get('slug') or str(tag)
                                    print(f"  crypto: tag_id={tag_id} ({tag_display_name})")
                                    break
                        
                        if 'crypto' in self.tag_cache:
                            break
                
                print(f"Loaded {len(self.tag_cache)} category tags")
                return self.tag_cache
            else:
                print(f"Error fetching tags: {response.status_code}")
        except Exception as e:
            print(f"Error loading tags: {e}")
        
        return {}
    
    def _fetch_markets_by_tag(self, tag_id: int, category: str, limit: int = 100, max_pages: int = 500) -> List[Dict]:
        """
        Fetch markets/events for a specific tag_id from Gamma API.
        Returns list of market dictionaries with category already set.
        """
        all_markets = []
        offset = 0
        page = 0
        
        print(f"Fetching {category} markets (tag_id={tag_id})...")
        
        # Debug: Test the API call first
        test_url = f"{GAMMA_API_BASE}/events"
        test_params = {
            'tag_id': str(tag_id),
            'closed': 'false',
            'limit': 1,
            'offset': 0
        }
        print(f"  Testing API call: {test_url}?tag_id={tag_id}&closed=false&limit=1")
        
        while page < max_pages:
            try:
                # Use events endpoint (events contain their markets)
                url = f"{GAMMA_API_BASE}/events"
                # Convert tag_id to string if needed (API might expect string)
                tag_id_param = str(tag_id) if tag_id else None
                if not tag_id_param:
                    print(f"  Invalid tag_id for {category}, skipping...")
                    break
                    
                params = {
                    'tag_id': tag_id_param,
                    'closed': 'false',
                    'limit': limit,
                    'offset': offset,
                    'order': 'id',
                    'ascending': 'false'
                }
                
                # Debug: Print the actual request
                if page == 0:
                    print(f"  Request URL: {url}")
                    print(f"  Request params: {params}")
                
                # Apply rate limiting for GAMMA events endpoint (100 requests / 10s)
                rate_limiter = get_rate_limiter()
                rate_limiter.wait_if_needed_sync('gamma_events')
                response = requests.get(url, params=params, timeout=30)
                rate_limiter.record_request('gamma_events')
                
                # Debug: Print response status and first few chars of response
                if page == 0:
                    print(f"  Response status: {response.status_code}")
                    if response.status_code != 200:
                        print(f"  Response text (first 500 chars): {response.text[:500]}")
                
                if response.status_code != 200:
                    print(f"  Error fetching {category} markets (page {page + 1}): {response.status_code}")
                    if response.status_code == 404:
                        # Tag might not exist or have no events
                        print(f"  Tag {tag_id} might not exist or have no events")
                        break
                    # For other errors, try next page
                    offset += limit
                    page += 1
                    continue
                
                events_data = response.json()
                
                # Debug: Print response structure
                if page == 0:
                    if isinstance(events_data, dict):
                        print(f"  Response keys: {list(events_data.keys())}")
                    elif isinstance(events_data, list):
                        print(f"  Response is a list with {len(events_data)} items")
                    else:
                        print(f"  Response type: {type(events_data)}")
                if isinstance(events_data, dict):
                    events = events_data.get('data', events_data.get('results', events_data.get('events', [])))
                    # Check for pagination info in response
                    total_count = events_data.get('count', events_data.get('total', None))
                    has_more = events_data.get('hasMore', events_data.get('has_more', None))
                elif isinstance(events_data, list):
                    events = events_data
                    total_count = None
                    has_more = None
                else:
                    events = []
                    total_count = None
                    has_more = None
                
                if not events:
                    # No more events
                    break
                
                # Debug: Print first event structure
                if page == 0 and events:
                    print(f"  Sample event structure: {list(events[0].keys())}")
                    if 'markets' in events[0]:
                        print(f"  Event has {len(events[0].get('markets', []))} markets")
                    if total_count:
                        print(f"  Total events available: {total_count}")
                
                # Parse markets from events
                events_processed = 0
                for event in events:
                    sub_markets = self.parse_sub_markets(event)
                    if not sub_markets:
                        # If no sub-markets found, try to use event itself as a market
                        if event.get('condition_id') or event.get('question') or event.get('title'):
                            sub_markets = [{
                                'condition_id': event.get('condition_id', ''),
                                'question': event.get('question') or event.get('title', ''),
                                'answer1': 'YES',
                                'answer2': 'NO',
                                'token1': '',
                                'token2': '',
                                'market_slug': event.get('slug', event.get('market_slug', '')),
                                'neg_risk': event.get('neg_risk', event.get('negRisk', 'FALSE')),
                                'parent_market': None
                            }]
                    
                    if sub_markets:
                        events_processed += 1
                        for sub_market in sub_markets:
                            sub_market['category'] = category
                            sub_market['best_bid'] = 0.0
                            sub_market['best_ask'] = 0.0
                            sub_market['spread'] = 0.0
                            all_markets.append(sub_market)
                
                print(f"  Page {page + 1}: Fetched {len(events)} events ({events_processed} with markets), {len(all_markets)} total markets so far...")
                
                # Check if there are more pages
                # Continue if we got a full page of results
                if len(events) < limit:
                    # Got fewer results than limit, we're done
                    break
                
                # Check has_more flag if available
                if has_more is False:
                    break
                
                # Move to next page
                offset += limit
                page += 1
                
            except Exception as e:
                print(f"  Error fetching {category} markets (page {page + 1}): {e}")
                import traceback
                traceback.print_exc()
                # Try next page anyway
                offset += limit
                page += 1
                if page >= max_pages:
                    break
        
        print(f"  Total {category} markets: {len(all_markets)} (from {page + 1} pages)")
        return all_markets
    
    def categorize_market(self, question: str, description: str = '') -> str:
        """
        Categorize a market based on its question and description.
        Returns: 'crypto', 'politics', 'sports', 'economics', 'entertainment', 'technology', 'science', 'other'
        
        IMPORTANT: Only categorize as crypto if there's a clear crypto coin name AND price-related context.
        Just having "price" is not enough - must have a crypto coin name too.
        """
        if not question:
            return 'other'
        
        text_lower = (question + ' ' + description).lower()
        
        # Crypto category - STRICT matching: must have crypto coin name + price/price-related context
        crypto_coins = ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 
                       'dogecoin', 'doge', 'ripple', 'xrp', 'ethereum classic', 'etc',
                       'hyperliquid', 'hype', 'cardano', 'ada', 'polkadot', 'dot',
                       'avalanche', 'avax', 'polygon', 'matic', 'chainlink', 'link',
                       'litecoin', 'ltc', 'shiba', 'uniswap', 'uni', 'aave', 'maker', 'mkr',
                       'compound', 'comp', 'tether', 'usdt', 'usdc', 'dai', 'binance', 'bnb',
                       'fantom', 'ftm', 'cosmos', 'atom', 'algorand', 'algo', 'tezos', 'xtz',
                       'monero', 'xmr', 'zcash', 'zec', 'stellar', 'xlm', 'eos', 'tron', 'trx',
                       'neo', 'dash', 'iota', 'vechain', 'vet', 'theta', 'filecoin', 'fil']
        
        # Check if text contains a crypto coin
        has_crypto_coin = any(coin in text_lower for coin in crypto_coins)
        
        # Price-related patterns (only relevant if crypto coin is present)
        price_patterns = ['price', 'hit', 'reach', 'above', 'below', 'trading at', 'close at', 'settle at']
        time_patterns = ['november', 'december', 'january', 'february', 'march', 'april',
                        'may', 'june', 'july', 'august', 'september', 'october',
                        'weekly', 'monthly', 'daily', 'end of', 'by end', 'by']
        
        # Crypto-specific question patterns
        crypto_question_patterns = [
            'what price will', 'what will', 'will bitcoin', 'will ethereum', 'will solana',
            'will doge', 'will xrp', 'will etc', 'will hype', 'bitcoin price', 'ethereum price',
            'solana price', 'doge price', 'xrp price', 'etc price', 'hype price',
            'bitcoin hit', 'ethereum hit', 'solana hit', 'bitcoin reach', 'ethereum reach'
        ]
        
        # Only categorize as crypto if:
        # 1. Has crypto coin AND (price pattern OR time pattern OR crypto question pattern)
        # 2. OR has explicit crypto/cryptocurrency/blockchain terms
        if has_crypto_coin and (any(p in text_lower for p in price_patterns) or 
                               any(p in text_lower for p in time_patterns) or
                               any(p in text_lower for p in crypto_question_patterns)):
            return 'crypto'
        
        # Explicit crypto terms (without price context)
        explicit_crypto_terms = ['crypto', 'cryptocurrency', 'blockchain', 'defi', 'nft', 'web3', 'metaverse']
        if any(term in text_lower for term in explicit_crypto_terms):
            return 'crypto'
        
        # Politics category
        politics_keywords = ['president', 'election', 'trump', 'biden', 'senate', 'congress', 'house', 'senator',
                            'governor', 'mayor', 'vote', 'voting', 'ballot', 'democrat', 'republican', 'party',
                            'impeachment', 'supreme court', 'judge', 'nomination', 'cabinet', 'federal', 'state',
                            'primary', 'caucus', 'debate', 'poll', 'approval rating', 'resign', 'impeach']
        if any(keyword in text_lower for keyword in politics_keywords):
            return 'politics'
        
        # Sports category
        sports_keywords = ['nfl', 'nba', 'mlb', 'nhl', 'soccer', 'football', 'basketball', 'baseball', 'hockey',
                          'tennis', 'golf', 'boxing', 'ufc', 'mma', 'olympics', 'world cup', 'super bowl',
                          'championship', 'playoff', 'playoff', 'final', 'semifinal', 'quarterfinal', 'game',
                          'match', 'team', 'player', 'coach', 'draft', 'trade', 'injury', 'retire', 'mvp',
                          'heisman', 'stanley cup', 'world series', 'nba finals', 'super bowl']
        if any(keyword in text_lower for keyword in sports_keywords):
            return 'sports'
        
        # Economics category
        economics_keywords = ['fed', 'federal reserve', 'interest rate', 'inflation', 'gdp', 'unemployment',
                             'jobs report', 'economic', 'recession', 'depression', 'stock market', 'dow',
                             's&p', 'nasdaq', 'dollar', 'currency', 'yen', 'euro', 'pound', 'trade war',
                             'tariff', 'import', 'export', 'gdp growth', 'consumer price', 'cpi', 'ppi']
        if any(keyword in text_lower for keyword in economics_keywords):
            return 'economics'
        
        # Entertainment category
        entertainment_keywords = ['movie', 'film', 'oscar', 'grammy', 'emmy', 'award', 'celebrity', 'actor',
                                 'actress', 'director', 'producer', 'album', 'song', 'music', 'tv show',
                                 'television', 'streaming', 'netflix', 'disney', 'marvel', 'dc', 'comic',
                                 'book', 'author', 'release', 'premiere', 'box office', 'ticket sales']
        if any(keyword in text_lower for keyword in entertainment_keywords):
            return 'entertainment'
        
        # Technology category
        tech_keywords = ['ai', 'artificial intelligence', 'chatgpt', 'openai', 'google', 'apple', 'microsoft',
                        'amazon', 'meta', 'facebook', 'twitter', 'x.com', 'tesla', 'spacex', 'tech', 'technology',
                        'software', 'hardware', 'chip', 'semiconductor', 'nvidia', 'amd', 'intel', 'iphone',
                        'ipad', 'macbook', 'product launch', 'release date']
        if any(keyword in text_lower for keyword in tech_keywords):
            return 'technology'
        
        # Science category
        science_keywords = ['nasa', 'space', 'rocket', 'mars', 'moon', 'planet', 'asteroid', 'comet', 'earthquake',
                           'volcano', 'climate', 'global warming', 'temperature', 'weather', 'hurricane', 'tornado',
                           'research', 'study', 'discovery', 'scientist', 'nobel prize', 'medicine', 'drug',
                           'vaccine', 'cure', 'treatment', 'disease', 'pandemic', 'epidemic']
        if any(keyword in text_lower for keyword in science_keywords):
            return 'science'
        
        # Default to 'other'
        return 'other'
    
    def is_crypto_related(self, text: str) -> bool:
        """
        Check if text contains crypto-related keywords or patterns.
        Uses strict matching: must have crypto coin name + price/context.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Crypto coin names (specific coins only)
        crypto_coins = ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol',
                       'dogecoin', 'doge', 'ripple', 'xrp', 'ethereum classic', 'etc',
                       'hyperliquid', 'hype', 'cardano', 'ada', 'polkadot', 'dot',
                       'avalanche', 'avax', 'polygon', 'matic', 'chainlink', 'link',
                       'litecoin', 'ltc', 'shiba', 'uniswap', 'uni', 'aave', 'maker', 'mkr',
                       'compound', 'comp', 'tether', 'usdt', 'usdc', 'dai', 'binance', 'bnb',
                       'fantom', 'ftm', 'cosmos', 'atom', 'algorand', 'algo', 'tezos', 'xtz',
                       'monero', 'xmr', 'zcash', 'zec', 'stellar', 'xlm', 'eos', 'tron', 'trx',
                       'neo', 'dash', 'iota', 'vechain', 'vet', 'theta', 'filecoin', 'fil']
        
        # Check if text contains a crypto coin
        has_crypto_coin = any(coin in text_lower for coin in crypto_coins)
        
        # Explicit crypto terms
        explicit_crypto_terms = ['crypto', 'cryptocurrency', 'blockchain', 'defi', 'nft', 'web3', 'metaverse']
        has_explicit_crypto = any(term in text_lower for term in explicit_crypto_terms)
        
        # Price-related patterns (only relevant if crypto coin is present)
        price_patterns = ['price', 'hit', 'reach', 'above', 'below', 'trading at', 'close at', 'settle at']
        time_patterns = ['november', 'december', 'january', 'february', 'march', 'april',
                        'may', 'june', 'july', 'august', 'september', 'october',
                        'weekly', 'monthly', 'daily', 'end of', 'by end', 'by']
        
        # Crypto-specific question patterns
        crypto_question_patterns = [
            'what price will', 'what will', 'will bitcoin', 'will ethereum', 'will solana',
            'will doge', 'will xrp', 'will etc', 'will hype', 'bitcoin price', 'ethereum price',
            'solana price', 'doge price', 'xrp price', 'etc price', 'hype price',
            'bitcoin hit', 'ethereum hit', 'solana hit', 'bitcoin reach', 'ethereum reach'
        ]
        
        # Return True only if:
        # 1. Has explicit crypto terms, OR
        # 2. Has crypto coin AND (price pattern OR time pattern OR crypto question pattern)
        if has_explicit_crypto:
            return True
        
        if has_crypto_coin and (any(p in text_lower for p in price_patterns) or 
                               any(p in text_lower for p in time_patterns) or
                               any(p in text_lower for p in crypto_question_patterns)):
            return True
        
        return False
    
    def parse_sub_markets(self, market_data: Dict) -> List[Dict]:
        """
        Parse sub-markets from a market or event.
        Handles both binary markets and multi-outcome markets.
        For events with multiple markets, each market should be added separately.
        """
        sub_markets = []
        
        # Check if this market has sub-markets (markets array)
        # Some API responses include a 'markets' array within an event
        if 'markets' in market_data and isinstance(market_data['markets'], list) and len(market_data['markets']) > 0:
            # This is an event with multiple markets
            for market in market_data['markets']:
                # Ensure market is a dictionary
                if not isinstance(market, dict):
                    print(f"  Warning: Market is not a dict, skipping: {type(market)}")
                    continue
                
                # Get tokens from market
                tokens = market.get('tokens', [])
                
                # Also check if tokens are at root level of market
                if not tokens:
                    tokens = market.get('outcomes', [])  # Some APIs use 'outcomes' instead of 'tokens'
                
                # Ensure tokens is a list and contains dictionaries
                if not isinstance(tokens, list):
                    tokens = []
                
                # Filter out non-dict items from tokens
                tokens = [t for t in tokens if isinstance(t, dict)]
                
                # If market has tokens, use them
                if len(tokens) >= 2:
                    # Get question from market or event
                    market_question = market.get('question') or market.get('title') or market_data.get('title') or market_data.get('question', '')
                    
                    sub_markets.append({
                        'condition_id': market.get('condition_id') or market.get('id') or market_data.get('condition_id', ''),
                        'question': market_question,
                        'answer1': tokens[0].get('outcome', tokens[0].get('name', 'YES')) if len(tokens) > 0 and isinstance(tokens[0], dict) else 'YES',
                        'answer2': tokens[1].get('outcome', tokens[1].get('name', 'NO')) if len(tokens) > 1 and isinstance(tokens[1], dict) else 'NO',
                        'token1': tokens[0].get('token_id', tokens[0].get('id', '')) if len(tokens) > 0 and isinstance(tokens[0], dict) else '',
                        'token2': tokens[1].get('token_id', tokens[1].get('id', '')) if len(tokens) > 1 and isinstance(tokens[1], dict) else '',
                        'market_slug': market.get('slug') or market.get('market_slug') or market_data.get('slug', market_data.get('market_slug', '')),
                        'neg_risk': market.get('neg_risk') or market.get('negRisk') or market_data.get('neg_risk', market_data.get('negRisk', 'FALSE')),
                        'parent_market': market_data.get('condition_id') or market_data.get('id', None)
                    })
                # If market doesn't have tokens but has condition_id, create a basic market
                elif market.get('condition_id') or market.get('id') or market.get('question') or market.get('title'):
                    market_question = market.get('question') or market.get('title') or market_data.get('title') or market_data.get('question', '')
                    
                    sub_markets.append({
                        'condition_id': market.get('condition_id') or market.get('id') or '',
                        'question': market_question,
                        'answer1': 'YES',
                        'answer2': 'NO',
                        'token1': '',
                        'token2': '',
                        'market_slug': market.get('slug') or market.get('market_slug') or market_data.get('slug', ''),
                        'neg_risk': market.get('neg_risk') or market.get('negRisk') or 'FALSE',
                        'parent_market': market_data.get('condition_id') or market_data.get('id', None)
                    })
            
            if sub_markets:
                return sub_markets
        
        # Check if this is a multi-outcome market (has tokens at root level)
        tokens = market_data.get('tokens', [])
        
        # Ensure tokens is a list and contains dictionaries
        if not isinstance(tokens, list):
            tokens = []
        
        # Filter out non-dict items from tokens
        tokens = [t for t in tokens if isinstance(t, dict)]
        
        if len(tokens) == 2:
            # Standard binary market (YES/NO)
            sub_markets.append({
                'condition_id': market_data.get('condition_id', ''),
                'question': market_data.get('question', '') or market_data.get('title', ''),
                'answer1': tokens[0].get('outcome', tokens[0].get('name', 'YES')) if len(tokens) > 0 and isinstance(tokens[0], dict) else 'YES',
                'answer2': tokens[1].get('outcome', tokens[1].get('name', 'NO')) if len(tokens) > 1 and isinstance(tokens[1], dict) else 'NO',
                'token1': tokens[0].get('token_id', tokens[0].get('id', '')) if len(tokens) > 0 and isinstance(tokens[0], dict) else '',
                'token2': tokens[1].get('token_id', tokens[1].get('id', '')) if len(tokens) > 1 and isinstance(tokens[1], dict) else '',
                'market_slug': market_data.get('slug', market_data.get('market_slug', '')),
                'neg_risk': market_data.get('neg_risk', market_data.get('negRisk', 'FALSE')),
                'parent_market': None
            })
        elif len(tokens) > 2:
            # Multi-outcome market - create separate markets for each outcome
            # For crypto price markets, each price tier is a separate tradeable market
            parent_question = market_data.get('question', '')
            parent_condition_id = market_data.get('condition_id', '')
            
            for i, token in enumerate(tokens):
                # Ensure token is a dictionary
                if not isinstance(token, dict):
                    continue
                
                # For each outcome, create a market with that outcome vs all others
                # In practice, Polymarket may have separate condition_ids for each outcome
                # If we have a unique condition_id per outcome, use it
                outcome_condition_id = token.get('condition_id', f"{parent_condition_id}_{i}")
                
                # Create a descriptive question for each sub-market
                outcome_text = token.get('outcome', token.get('name', f'Option {i+1}'))
                sub_question = f"{parent_question} - {outcome_text}" if parent_question else outcome_text
                
                # Get token IDs safely
                token1_id = token.get('token_id', token.get('id', ''))
                token2_id = ''
                if i > 0 and len(tokens) > 0 and isinstance(tokens[0], dict):
                    token2_id = tokens[0].get('token_id', tokens[0].get('id', ''))
                elif len(tokens) > 1 and isinstance(tokens[1], dict):
                    token2_id = tokens[1].get('token_id', tokens[1].get('id', ''))
                
                sub_markets.append({
                    'condition_id': outcome_condition_id,
                    'question': sub_question,
                    'answer1': outcome_text,
                    'answer2': 'Other',
                    'token1': token1_id,
                    'token2': token2_id,
                    'market_slug': market_data.get('slug', market_data.get('market_slug', '')),
                    'neg_risk': market_data.get('neg_risk', market_data.get('negRisk', 'FALSE')),
                    'parent_market': parent_condition_id if parent_condition_id else None
                })
        
        return sub_markets
    
    async def fetch_all_markets(self) -> List[Dict]:
        """Fetch all markets from Polymarket"""
        if not self.client:
            print("Client not initialized")
            return []
        
        all_markets = []
        cursor = None
        max_iterations = 100  # Safety limit to prevent infinite loops
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                
                # Use sampling_markets which includes all markets
                try:
                    if cursor:
                        markets = self.client.get_sampling_markets(next_cursor=cursor)
                    else:
                        # First request without cursor
                        markets = self.client.get_sampling_markets()
                except Exception as api_error:
                    error_msg = str(api_error)
                    # Check if it's a cursor-related error
                    if 'next item' in error_msg.lower() or 'cursor' in error_msg.lower() or '400' in error_msg:
                        print(f"Cursor error at iteration {iteration}, stopping fetch. Error: {error_msg}")
                        print(f"Successfully fetched {len(all_markets)} markets before error")
                        break
                    else:
                        # Re-raise if it's a different error
                        raise
                
                if not markets:
                    print("No markets returned, stopping fetch")
                    break
                
                # Handle different response formats
                if isinstance(markets, dict):
                    markets_data = markets.get('data', [])
                    next_cursor = markets.get('next_cursor')
                elif isinstance(markets, list):
                    markets_data = markets
                    next_cursor = None
                else:
                    print(f"Unexpected response format: {type(markets)}")
                    break
                
                if not markets_data:
                    print("No market data in response, stopping fetch")
                    break
                
                all_markets.extend(markets_data)
                
                # Validate cursor before using it
                if next_cursor:
                    # Check if cursor is valid (not empty string, not negative number, etc.)
                    if isinstance(next_cursor, str) and next_cursor.strip():
                        cursor = next_cursor
                    elif isinstance(next_cursor, (int, float)) and next_cursor >= 0:
                        cursor = str(next_cursor)
                    else:
                        print(f"Invalid cursor format: {next_cursor}, stopping fetch")
                        break
                else:
                    # No more pages
                    print("No next_cursor, reached end of markets")
                    break
                
                # Progress update every 500 markets
                if len(all_markets) % 500 == 0:
                    print(f"Fetched {len(all_markets)} markets so far...")
        
        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching markets: {error_msg}")
            # If we got some markets before the error, return them
            if all_markets:
                print(f"Returning {len(all_markets)} markets fetched before error")
        
        print(f"Total markets fetched: {len(all_markets)}")
        return all_markets
    
    async def fetch_crypto_markets(self) -> List[Dict]:
        """
        Fetch crypto-related markets from Polymarket using Gamma API tag filtering.
        """
        # Load tags and get crypto tag_id
        tags = self._load_all_tags()
        crypto_tag_id = tags.get('crypto')
        
        if not crypto_tag_id:
            print("Warning: Crypto tag not found. Falling back to keyword filtering...")
            # Fallback to old method
            return await self._fetch_crypto_markets_fallback()
        
        # Fetch markets using tag_id
        return self._fetch_markets_by_tag(crypto_tag_id, 'crypto')
    
    async def _fetch_crypto_markets_fallback(self) -> List[Dict]:
        """Fallback method using keyword filtering if tags are not available"""
        print("Using keyword filtering method (fallback)...")
        all_markets = await self.fetch_all_markets()
        
        crypto_markets = []
        print(f"Filtering {len(all_markets)} markets for crypto-related ones...")
        
        for idx, market_data in enumerate(all_markets):
            question = market_data.get('question', '')
            description = market_data.get('description', '')
            
            # Use strict categorization
            category = self.categorize_market(question, description)
            
            if category == 'crypto':
                sub_markets = self.parse_sub_markets(market_data)
                for sub_market in sub_markets:
                    sub_market['best_bid'] = 0.0
                    sub_market['best_ask'] = 0.0
                    sub_market['spread'] = 0.0
                    sub_market['category'] = 'crypto'
                    crypto_markets.append(sub_market)
            
            if (idx + 1) % 500 == 0:
                print(f"Filtered {idx + 1}/{len(all_markets)} markets, found {len(crypto_markets)} crypto markets so far...")
        
        print(f"Found {len(crypto_markets)} crypto-related markets")
        return crypto_markets
    
    async def fetch_all_markets_categorized(self, months_back: int = 3) -> List[Dict]:
        """
        Fetch active markets from Polymarket created in the last N months and categorize them.
        Uses Gamma API /events endpoint to fetch active events, then categorizes each market.
        This is more reliable than relying on tags, as recommended in Polymarket docs.
        
        Args:
            months_back: Number of months to look back (default: 3 months)
        """
        # Calculate date threshold (N months ago)
        date_threshold = datetime.utcnow() - timedelta(days=months_back * 30)
        date_threshold_str = date_threshold.strftime('%Y-%m-%d')
        
        print(f"Fetching active markets from Gamma API created in the last {months_back} months (since {date_threshold_str})...")
        
        all_categorized_markets = []
        offset = 0
        limit = 100
        max_pages = 200  # Reduced from 500 - only need last 3 months
        page = 0
        
        print(f"Fetching active events from Gamma API (up to {max_pages * limit} events)...")
        
        while page < max_pages:
            try:
                # Use events endpoint to get all active events (as recommended in docs)
                url = f"{GAMMA_API_BASE}/events"
                params = {
                    'closed': 'false',
                    'limit': limit,
                    'offset': offset,
                    'order': 'id',
                    'ascending': 'false'
                }
                
                # Apply rate limiting for GAMMA events endpoint (100 requests / 10s)
                rate_limiter = get_rate_limiter()
                rate_limiter.wait_if_needed_sync('gamma_events')
                response = requests.get(url, params=params, timeout=30)
                rate_limiter.record_request('gamma_events')
                
                if response.status_code != 200:
                    print(f"  Error fetching events (page {page + 1}): {response.status_code}")
                    if response.status_code == 404 or response.status_code >= 500:
                        break
                    # Try next page
                    offset += limit
                    page += 1
                    continue
                
                events_data = response.json()
                if isinstance(events_data, dict):
                    events = events_data.get('data', events_data.get('results', events_data.get('events', [])))
                    total_count = events_data.get('count', events_data.get('total', None))
                    has_more = events_data.get('hasMore', events_data.get('has_more', None))
                elif isinstance(events_data, list):
                    events = events_data
                    total_count = None
                    has_more = None
                else:
                    events = []
                    total_count = None
                    has_more = None
                
                if not events:
                    # No more events
                    break
                
                # Debug: Print first event structure
                if page == 0 and events:
                    print(f"  Sample event structure: {list(events[0].keys())}")
                    if 'markets' in events[0]:
                        print(f"  Event has {len(events[0].get('markets', []))} markets")
                    if total_count:
                        print(f"  Total events available: {total_count}")
                
                # Parse markets from events and categorize them
                events_processed = 0
                events_filtered_by_date = 0
                for event in events:
                    # Filter by creation date (only include events from last N months)
                    creation_date_str = event.get('creationDate') or event.get('createdAt') or event.get('startDate')
                    if creation_date_str:
                        try:
                            # Parse various date formats
                            if isinstance(creation_date_str, str):
                                # Try ISO format first
                                if 'T' in creation_date_str:
                                    event_date = datetime.fromisoformat(creation_date_str.replace('Z', '+00:00'))
                                else:
                                    event_date = datetime.strptime(creation_date_str, '%Y-%m-%d')
                                
                                # Convert to UTC if timezone-aware
                                if event_date.tzinfo:
                                    event_date = event_date.replace(tzinfo=None)
                                
                                # Skip events older than threshold
                                if event_date < date_threshold:
                                    events_filtered_by_date += 1
                                    continue
                        except (ValueError, TypeError) as e:
                            # If date parsing fails, include the event anyway
                            pass
                    
                    # Get event description for better categorization
                    event_description = event.get('description', '')
                    event_title = event.get('title', '')
                    
                    # Parse sub-markets from event
                    sub_markets = self.parse_sub_markets(event)
                    if not sub_markets:
                        # If no sub-markets found, try to use event itself as a market
                        if event.get('condition_id') or event.get('question') or event.get('title'):
                            sub_markets = [{
                                'condition_id': event.get('condition_id', ''),
                                'question': event.get('question') or event.get('title', ''),
                                'answer1': 'YES',
                                'answer2': 'NO',
                                'token1': '',
                                'token2': '',
                                'market_slug': event.get('slug', event.get('market_slug', '')),
                                'neg_risk': event.get('neg_risk', event.get('negRisk', 'FALSE')),
                                'parent_market': None
                            }]
                    
                    if sub_markets:
                        events_processed += 1
                        for sub_market in sub_markets:
                            # Categorize each market
                            market_question = sub_market.get('question', '')
                            category = self.categorize_market(market_question, event_description or event_title)
                            
                            sub_market['category'] = category
                            sub_market['best_bid'] = 0.0
                            sub_market['best_ask'] = 0.0
                            sub_market['spread'] = 0.0
                            all_categorized_markets.append(sub_market)
                
                if events_filtered_by_date > 0:
                    print(f"  Page {page + 1}: Fetched {len(events)} events ({events_filtered_by_date} filtered by date, {events_processed} with markets), {len(all_categorized_markets)} total markets so far...")
                else:
                    print(f"  Page {page + 1}: Fetched {len(events)} events ({events_processed} with markets), {len(all_categorized_markets)} total markets so far...")
                
                # If we filtered many events by date, we might be past the 3-month window
                # Check if we should stop early
                if events_filtered_by_date > len(events) * 0.8:  # If 80%+ are filtered, we're probably past the date range
                    print(f"  Most events are older than {months_back} months, stopping fetch...")
                    break
                
                # Check if there are more pages
                if len(events) < limit:
                    # Got fewer results than limit, we're done
                    break
                
                # Check has_more flag if available
                if has_more is False:
                    break
                
                # Move to next page
                offset += limit
                page += 1
                
            except Exception as e:
                print(f"  Error fetching events (page {page + 1}): {e}")
                import traceback
                traceback.print_exc()
                # Try next page anyway
                offset += limit
                page += 1
                if page >= max_pages:
                    break
        
        # Count by category
        category_counts = {}
        for m in all_categorized_markets:
            cat = m.get('category', 'other')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print(f"\n=== Summary ===")
        print(f"Total categorized markets: {len(all_categorized_markets)}")
        print(f"Category breakdown: {category_counts}")
        print(f"Fetched from {page + 1} pages of events")
        
        return all_categorized_markets
    
    async def _fetch_all_markets_categorized_fallback(self) -> List[Dict]:
        """Fallback method using manual categorization if tags are not available"""
        print("Using manual categorization (fallback)...")
        all_markets = await self.fetch_all_markets()
        
        categorized_markets = []
        print(f"Categorizing {len(all_markets)} markets...")
        
        for idx, market_data in enumerate(all_markets):
            question = market_data.get('question', '')
            description = market_data.get('description', '')
            
            sub_markets = self.parse_sub_markets(market_data)
            
            for sub_market in sub_markets:
                category = self.categorize_market(sub_market.get('question', question), description)
                sub_market['category'] = category
                sub_market['best_bid'] = 0.0
                sub_market['best_ask'] = 0.0
                sub_market['spread'] = 0.0
                categorized_markets.append(sub_market)
            
            if (idx + 1) % 500 == 0:
                category_counts = {}
                for m in categorized_markets:
                    cat = m.get('category', 'other')
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                print(f"Processed {idx + 1}/{len(all_markets)} markets: {category_counts}")
        
        category_counts = {}
        for m in categorized_markets:
            cat = m.get('category', 'other')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        print(f"Total categorized markets: {len(categorized_markets)}")
        print(f"Category breakdown: {category_counts}")
        
        return categorized_markets
    
    def get_market_details(self, condition_id: str) -> Optional[Dict]:
        """Get detailed information for a specific market"""
        if not self.client:
            return None
        
        try:
            # Fetch market details
            # Note: This is a simplified version; you may need to adjust based on API
            pass
        except Exception as e:
            print(f"Error fetching market details: {e}")
            return None

