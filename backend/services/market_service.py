"""
Market fetching and filtering service
"""
import requests
import pandas as pd
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON

load_dotenv()

# Crypto-related keywords for filtering
CRYPTO_KEYWORDS = [
    'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency',
    'blockchain', 'solana', 'sol', 'cardano', 'ada', 'polkadot', 'dot',
    'avalanche', 'avax', 'polygon', 'matic', 'chainlink', 'link',
    'litecoin', 'ltc', 'ripple', 'xrp', 'dogecoin', 'doge', 'shiba',
    'uniswap', 'uni', 'aave', 'maker', 'mkr', 'compound', 'comp',
    'tether', 'usdt', 'usdc', 'dai', 'binance', 'bnb', 'ftx', 'ftm',
    'fantom', 'cosmos', 'atom', 'algorand', 'algo', 'tezos', 'xtz',
    'monero', 'xmr', 'zcash', 'zec', 'stellar', 'xlm', 'eos',
    'tron', 'trx', 'neo', 'dash', 'iota', 'vechain', 'vet',
    'theta', 'filecoin', 'fil', 'decentraland', 'mana', 'sandbox', 'sand',
    'axie', 'gala', 'enjin', 'enj', 'chiliz', 'chz', 'wbtc', 'steth',
    'defi', 'nft', 'web3', 'metaverse', 'token', 'coin', 'satoshi'
]

class MarketService:
    """Service for fetching and filtering Polymarket markets"""
    
    def __init__(self):
        """Initialize market service with Polymarket client"""
        self.client = None
        self._init_client()
    
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
    
    def is_crypto_related(self, text: str) -> bool:
        """Check if text contains crypto-related keywords"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in CRYPTO_KEYWORDS)
    
    def parse_sub_markets(self, market_data: Dict) -> List[Dict]:
        """
        Parse sub-markets from a multi-outcome market.
        For example, "Bitcoin price on Dec 31" with multiple price tiers.
        """
        sub_markets = []
        
        # Check if this is a multi-outcome market
        tokens = market_data.get('tokens', [])
        
        if len(tokens) == 2:
            # Standard binary market (YES/NO)
            sub_markets.append({
                'condition_id': market_data['condition_id'],
                'question': market_data['question'],
                'answer1': tokens[0]['outcome'],
                'answer2': tokens[1]['outcome'],
                'token1': tokens[0]['token_id'],
                'token2': tokens[1]['token_id'],
                'market_slug': market_data.get('market_slug', ''),
                'neg_risk': market_data.get('neg_risk', 'FALSE'),
                'parent_market': None
            })
        elif len(tokens) > 2:
            # Multi-outcome market - create separate markets for each outcome pair
            # This is a simplification; in practice, you might want more sophisticated logic
            parent_question = market_data['question']
            
            for i, token in enumerate(tokens):
                # Create a binary market for each outcome vs "others"
                sub_markets.append({
                    'condition_id': f"{market_data['condition_id']}_{i}",
                    'question': f"{parent_question} - {token['outcome']}",
                    'answer1': token['outcome'],
                    'answer2': 'Other',
                    'token1': token['token_id'],
                    'token2': tokens[0]['token_id'] if i > 0 else tokens[1]['token_id'],
                    'market_slug': market_data.get('market_slug', ''),
                    'neg_risk': market_data.get('neg_risk', 'FALSE'),
                    'parent_market': market_data['condition_id']
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
        """Fetch all crypto-related markets from Polymarket"""
        all_markets = await self.fetch_all_markets()
        
        crypto_markets = []
        
        print(f"Filtering {len(all_markets)} markets for crypto-related ones...")
        
        for idx, market_data in enumerate(all_markets):
            question = market_data.get('question', '')
            description = market_data.get('description', '')
            
            # Check if market is crypto-related
            if self.is_crypto_related(question) or self.is_crypto_related(description):
                # Parse sub-markets if applicable
                sub_markets = self.parse_sub_markets(market_data)
                
                for sub_market in sub_markets:
                    # Skip order book fetch to speed up - we'll fetch it later if needed
                    # This significantly speeds up the initial fetch
                    sub_market['best_bid'] = 0.0
                    sub_market['best_ask'] = 0.0
                    sub_market['spread'] = 0.0
                    
                    crypto_markets.append(sub_market)
            
            # Progress update every 500 markets
            if (idx + 1) % 500 == 0:
                print(f"Filtered {idx + 1}/{len(all_markets)} markets, found {len(crypto_markets)} crypto markets so far...")
        
        print(f"Found {len(crypto_markets)} crypto-related markets")
        return crypto_markets
    
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

