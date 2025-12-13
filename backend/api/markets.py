"""
Markets API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import requests
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from poly_data.rate_limiter import get_rate_limiter
from database import get_db, Market, TradingParams
from schemas import (
    MarketCreate, MarketUpdate, MarketResponse, MarketWithConfig,
    TradingParamsCreate, TradingParamsUpdate, TradingParamsResponse,
    BulkMarketUpdate, BulkMarketDelete
)

router = APIRouter()

# Store for tracking fetch progress (must be defined before routes use it)
fetch_progress = {
    "status": "idle",  # idle, fetching, processing, completed, error
    "total_fetched": 0,
    "total_processed": 0,
    "total_saved": 0,
    "error": None,
    "started_at": None,
    "completed_at": None
}

# IMPORTANT: More specific routes must come before less specific ones
# So /fetch and /crypto/fetch must come before /{market_id}

@router.get("/fetch/status")
async def get_fetch_status():
    """Get the status of markets fetch operation"""
    return fetch_progress

@router.get("/crypto/fetch/status")
async def get_crypto_fetch_status():
    """Get the status of crypto markets fetch operation"""
    return fetch_progress

@router.get("/fetch")
async def fetch_all_markets(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Fetch all markets from Polymarket and categorize them (runs in background)
    
    Returns:
        Status message indicating fetch has started
        
    Raises:
        HTTPException: If client initialization fails or fetch already in progress
    """
    from services.market_service import MarketService
    from fastapi import HTTPException
    from datetime import datetime
    
    try:
        # Check if fetch is already in progress
        if fetch_progress["status"] in ["fetching", "processing"]:
            raise HTTPException(
                status_code=409,
                detail=f"Market fetch already in progress. Status: {fetch_progress['status']}, Fetched: {fetch_progress['total_fetched']}"
            )
        
        # Initialize market service to check if client is available
        market_service = MarketService()
        if not market_service.client:
            raise HTTPException(
                status_code=503,
                detail="Polymarket client not initialized. Please check your .env file and ensure PK is set correctly."
            )
        
        # Reset progress
        fetch_progress.update({
            "status": "fetching",
            "total_fetched": 0,
            "total_processed": 0,
            "total_saved": 0,
            "error": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        })
        
        # Start background task (don't pass db session, create new one in background task)
        background_tasks.add_task(fetch_and_save_all_markets)
        
        return {
            "message": "Market fetch started in background",
            "status": "fetching",
            "check_status_endpoint": "/api/markets/fetch/status"
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Error starting market fetch: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start market fetch: {error_msg}"
        )

@router.get("/crypto/fetch")
async def fetch_crypto_markets(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Fetch all crypto-related markets from Polymarket (runs in background)
    
    Returns:
        Status message indicating fetch has started
        
    Raises:
        HTTPException: If client initialization fails or fetch already in progress
    """
    from services.market_service import MarketService
    from fastapi import HTTPException
    from datetime import datetime
    
    # Check if fetch is already in progress
    if fetch_progress["status"] in ["fetching", "processing"]:
        raise HTTPException(
            status_code=409,
            detail=f"Market fetch already in progress. Status: {fetch_progress['status']}, Fetched: {fetch_progress['total_fetched']}"
        )
    
    # Reset progress
    fetch_progress.update({
        "status": "fetching",
        "total_fetched": 0,
        "total_processed": 0,
        "total_saved": 0,
        "error": None,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None
    })
    
    # Start background task (don't pass db session, create new one in background task)
    background_tasks.add_task(fetch_and_save_crypto_markets)
    
    return {
        "message": "Crypto markets fetch started in background",
        "status": "fetching",
        "check_status_endpoint": "/api/markets/crypto/fetch/status"
    }

@router.get("/", response_model=List[MarketResponse])
async def get_markets(
    skip: int = 0,
    limit: int = Query(default=1000, le=10000),  # Default 1000, max 10000
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = Query(None, description="Search query to filter markets by question"),
    db: Session = Depends(get_db)
):
    """Get all markets with optional filtering and search"""
    query = db.query(Market)
    
    if category:
        query = query.filter(Market.category == category)
    if is_active is not None:
        query = query.filter(Market.is_active == is_active)
    if search:
        # Case-insensitive search in question field
        search_term = f"%{search}%"
        query = query.filter(Market.question.ilike(search_term))
    
    markets = query.offset(skip).limit(limit).all()
    return markets

@router.get("/search", response_model=List[MarketResponse])
async def search_markets(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """Search markets by question, category, and active status"""
    query = db.query(Market)
    
    # Search in question field (case-insensitive)
    search_term = f"%{q}%"
    query = query.filter(Market.question.ilike(search_term))
    
    if category:
        query = query.filter(Market.category == category)
    if is_active is not None:
        query = query.filter(Market.is_active == is_active)
    
    markets = query.limit(limit).all()
    return markets

@router.get("/slug/{slug}/all")
async def get_all_markets_by_slug(slug: str):
    """
    Fetch ALL sub-markets from a Polymarket event by slug.
    
    Events can contain multiple markets (e.g., "What price will Bitcoin hit?" 
    with options like $90k, $95k, $100k, each being a separate tradeable market).
    
    This endpoint returns ALL markets within an event, allowing users to 
    select which ones to add to the database.
    
    Returns:
        List of market dictionaries, each with condition_id, question, tokens, etc.
    """
    from services.market_service import MarketService
    
    try:
        market_service = MarketService()
        
        # Fetch from events endpoint
        url = f"https://gamma-api.polymarket.com/events/slug/{slug}"
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('gamma_events')
        response = requests.get(url, timeout=10)
        rate_limiter.record_request('gamma_events')
        
        if response.status_code == 200:
            event_data = response.json()
            
            # Handle different response formats
            if isinstance(event_data, dict):
                event = event_data.get('data', event_data)
            elif isinstance(event_data, list) and len(event_data) > 0:
                event = event_data[0]
            else:
                event = event_data
            
            # Get event title for context
            event_title = event.get('title', '') or event.get('question', '')
            event_description = event.get('description', '')
            
            # Get all markets from event
            event_markets = event.get('markets', [])
            
            all_markets = []
            
            if event_markets and len(event_markets) > 0:
                print(f"DEBUG: Found {len(event_markets)} markets in event '{event_title}'")
                
                for idx, market_data in enumerate(event_markets):
                    # Extract market data using the same logic as get_market_by_slug
                    market_info = _extract_market_info(market_data, event, slug, market_service)
                    
                    if market_info:
                        # Add index and event info for clarity
                        market_info['market_index'] = idx
                        market_info['event_title'] = event_title
                        market_info['total_markets_in_event'] = len(event_markets)
                        all_markets.append(market_info)
            
            # If no markets array, try parse_sub_markets
            if not all_markets:
                parsed_markets = market_service.parse_sub_markets(event)
                
                if parsed_markets:
                    for idx, market in enumerate(parsed_markets):
                        question = market.get('question', '')
                        category = market_service.categorize_market(question, event_description or event_title)
                        market['category'] = category
                        market['market_index'] = idx
                        market['event_title'] = event_title
                        market['total_markets_in_event'] = len(parsed_markets)
                        all_markets.append(market)
            
            # If still no markets, create from event itself
            if not all_markets:
                if event.get('condition_id') or event.get('question') or event.get('title'):
                    question = event.get('question') or event.get('title', '')
                    category = market_service.categorize_market(question, event_description)
                    
                    all_markets.append({
                        'condition_id': event.get('condition_id', ''),
                        'question': question,
                        'answer1': 'YES',
                        'answer2': 'NO',
                        'token1': '',
                        'token2': '',
                        'market_slug': slug,
                        'category': category,
                        'market_index': 0,
                        'event_title': event_title,
                        'total_markets_in_event': 1
                    })
            
            if all_markets:
                return {
                    'event_title': event_title,
                    'event_slug': slug,
                    'total_markets': len(all_markets),
                    'markets': all_markets
                }
        
        # Try market endpoint as fallback
        url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('gamma_markets')
        response = requests.get(url, timeout=10)
        rate_limiter.record_request('gamma_markets')
        
        if response.status_code == 200:
            market_data = response.json()
            
            if isinstance(market_data, dict):
                market = market_data.get('data', market_data)
            else:
                market = market_data
            
            market_info = _extract_market_info(market, {}, slug, market_service)
            
            if market_info:
                market_info['market_index'] = 0
                market_info['event_title'] = market_info.get('question', '')
                market_info['total_markets_in_event'] = 1
                
                return {
                    'event_title': market_info.get('question', ''),
                    'event_slug': slug,
                    'total_markets': 1,
                    'markets': [market_info]
                }
        
        raise HTTPException(status_code=404, detail=f"No markets found for slug '{slug}'")
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching all markets by slug: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching markets: {error_msg}")


def _extract_market_info(market_data: dict, event: dict, slug: str, market_service) -> dict:
    """
    Helper function to extract market information from API response.
    
    Args:
        market_data: Market data from API
        event: Parent event data (can be empty dict)
        slug: Market/event slug
        market_service: MarketService instance for categorization
        
    Returns:
        Dictionary with market information or None if extraction fails
    """
    try:
        # Extract token IDs - clobTokenIds is the most reliable source
        clob_token_ids_raw = market_data.get('clobTokenIds', [])
        
        # Parse clobTokenIds - it might be a JSON string
        clob_token_ids = []
        if isinstance(clob_token_ids_raw, str):
            try:
                clob_token_ids = json.loads(clob_token_ids_raw)
            except (json.JSONDecodeError, ValueError):
                clob_token_ids = []
        elif isinstance(clob_token_ids_raw, list):
            clob_token_ids = clob_token_ids_raw
        else:
            clob_token_ids = []
        
        token1 = ''
        token2 = ''
        answer1 = 'YES'
        answer2 = 'NO'
        
        # Try clobTokenIds first
        if clob_token_ids and len(clob_token_ids) >= 2:
            token1 = str(clob_token_ids[0]) if clob_token_ids[0] is not None else ''
            token2 = str(clob_token_ids[1]) if clob_token_ids[1] is not None else ''
        else:
            # Try outcomes array
            outcomes = market_data.get('outcomes', [])
            tokens = market_data.get('tokens', []) or market_data.get('outcomeTokens', [])
            
            # Parse outcomes - might be JSON string
            if isinstance(outcomes, str):
                try:
                    outcomes = json.loads(outcomes)
                except:
                    outcomes = ['YES', 'NO']
            
            # Handle outcomes array
            if outcomes and len(outcomes) >= 2:
                if isinstance(outcomes[0], dict):
                    token1 = (outcomes[0].get('token_id') or outcomes[0].get('id') or 
                             outcomes[0].get('tokenId') or outcomes[0].get('asset_id') or '')
                    answer1 = outcomes[0].get('outcome', outcomes[0].get('name', 'YES'))
                elif isinstance(outcomes[0], str):
                    answer1 = outcomes[0]
                
                if isinstance(outcomes[1], dict):
                    token2 = (outcomes[1].get('token_id') or outcomes[1].get('id') or 
                             outcomes[1].get('tokenId') or outcomes[1].get('asset_id') or '')
                    answer2 = outcomes[1].get('outcome', outcomes[1].get('name', 'NO'))
                elif isinstance(outcomes[1], str):
                    answer2 = outcomes[1]
            
            # Handle tokens array
            if (not token1 or not token2) and tokens and len(tokens) >= 2:
                if isinstance(tokens[0], dict):
                    token1 = (tokens[0].get('token_id') or tokens[0].get('id') or 
                             tokens[0].get('tokenId') or tokens[0].get('asset_id') or '')
                    answer1 = tokens[0].get('outcome', tokens[0].get('name', answer1))
                elif isinstance(tokens[0], (str, int)):
                    token1 = str(tokens[0])
                
                if isinstance(tokens[1], dict):
                    token2 = (tokens[1].get('token_id') or tokens[1].get('id') or 
                             tokens[1].get('tokenId') or tokens[1].get('asset_id') or '')
                    answer2 = tokens[1].get('outcome', tokens[1].get('name', answer2))
                elif isinstance(tokens[1], (str, int)):
                    token2 = str(tokens[1])
        
        # Get question and condition ID
        question = market_data.get('question', '') or event.get('title', '')
        condition_id = (market_data.get('conditionId', '') or market_data.get('condition_id', '') or 
                       event.get('condition_id', '') or market_data.get('id', ''))
        
        # Get neg_risk flag
        neg_risk_raw = market_data.get('negRisk', market_data.get('neg_risk', event.get('negRisk', 'FALSE')))
        if isinstance(neg_risk_raw, bool):
            neg_risk = 'TRUE' if neg_risk_raw else 'FALSE'
        else:
            neg_risk = str(neg_risk_raw).upper() if neg_risk_raw else 'FALSE'
        
        # Categorize
        description = event.get('description', '') or event.get('title', '')
        category = market_service.categorize_market(question, description)
        
        return {
            'condition_id': condition_id,
            'question': question,
            'answer1': str(answer1) if answer1 else 'YES',
            'answer2': str(answer2) if answer2 else 'NO',
            'token1': str(token1) if token1 else '',
            'token2': str(token2) if token2 else '',
            'market_slug': market_data.get('slug', '') or slug,
            'category': category,
            'neg_risk': neg_risk
        }
        
    except Exception as e:
        print(f"Error extracting market info: {e}")
        return None


@router.get("/slug/{slug}")
async def get_market_by_slug(slug: str):
    """
    Fetch market data from Polymarket by slug (from URL).
    Returns the first market and info about additional sub-markets if present.
    
    For events with multiple markets, use GET /slug/{slug}/all to get all markets.
    """
    from services.market_service import MarketService
    import re
    
    try:
        market_service = MarketService()
        
        # Try to fetch from events endpoint first (events contain markets)
        url = f"https://gamma-api.polymarket.com/events/slug/{slug}"
        # Apply rate limiting for GAMMA events endpoint (100 requests / 10s)
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('gamma_events')
        response = requests.get(url, timeout=10)
        rate_limiter.record_request('gamma_events')
        
        if response.status_code == 200:
            event_data = response.json()
            
            # Handle different response formats
            if isinstance(event_data, dict):
                event = event_data.get('data', event_data)
            elif isinstance(event_data, list) and len(event_data) > 0:
                event = event_data[0]
            else:
                event = event_data
            
            # Debug: Print event structure to understand the data
            print(f"DEBUG: Event keys: {list(event.keys()) if isinstance(event, dict) else 'Not a dict'}")
            if isinstance(event, dict) and 'markets' in event:
                print(f"DEBUG: Event has {len(event.get('markets', []))} markets")
                if event.get('markets') and len(event.get('markets', [])) > 0:
                    print(f"DEBUG: First market keys: {list(event['markets'][0].keys()) if isinstance(event['markets'][0], dict) else 'Not a dict'}")
            
            # Try to get markets from event
            event_markets = event.get('markets', [])
            
            # If event has markets array, use the first market
            if event_markets and len(event_markets) > 0:
                market_data = event_markets[0]
                
                # Extract token IDs from market - clobTokenIds is the most reliable source
                clob_token_ids_raw = market_data.get('clobTokenIds', [])
                
                # Debug: Check clobTokenIds
                print(f"DEBUG: clobTokenIds type: {type(clob_token_ids_raw)}, value: {clob_token_ids_raw}")
                
                # Parse clobTokenIds - it might be a JSON string
                clob_token_ids = []
                if isinstance(clob_token_ids_raw, str):
                    try:
                        import json
                        clob_token_ids = json.loads(clob_token_ids_raw)
                        print(f"DEBUG: Parsed clobTokenIds from JSON string: {clob_token_ids}")
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"DEBUG: Failed to parse clobTokenIds as JSON: {e}")
                        clob_token_ids = []
                elif isinstance(clob_token_ids_raw, list):
                    clob_token_ids = clob_token_ids_raw
                else:
                    clob_token_ids = []
                
                print(f"DEBUG: clobTokenIds is list: {isinstance(clob_token_ids, list)}, length: {len(clob_token_ids) if isinstance(clob_token_ids, list) else 'N/A'}")
                
                token1 = ''
                token2 = ''
                answer1 = 'YES'
                answer2 = 'NO'
                
                if clob_token_ids and isinstance(clob_token_ids, list) and len(clob_token_ids) >= 2:
                    token1 = str(clob_token_ids[0]) if clob_token_ids[0] is not None else ''
                    token2 = str(clob_token_ids[1]) if clob_token_ids[1] is not None else ''
                    print(f"DEBUG: ✅ Found tokens from clobTokenIds: token1={token1[:30]}..., token2={token2[:30]}...")
                else:
                    # Try outcomes array
                    outcomes = market_data.get('outcomes', [])
                    tokens = market_data.get('tokens', [])
                    if not tokens:
                        tokens = market_data.get('outcomeTokens', [])
                    
                    # Debug: Print token structure
                    print(f"DEBUG: Found {len(tokens)} tokens in market, {len(outcomes)} outcomes")
                    if tokens and len(tokens) > 0:
                        print(f"DEBUG: First token type: {type(tokens[0])}, value: {tokens[0]}")
                    if outcomes and len(outcomes) > 0:
                        print(f"DEBUG: First outcome type: {type(outcomes[0])}, value: {outcomes[0]}")
                    
                    # Handle outcomes array (might be dicts or strings)
                    if outcomes and len(outcomes) >= 2:
                        outcome1 = outcomes[0]
                        outcome2 = outcomes[1]
                        
                        if isinstance(outcome1, dict):
                            token1 = (outcome1.get('token_id') or outcome1.get('id') or 
                                     outcome1.get('tokenId') or outcome1.get('asset_id') or 
                                     str(outcome1.get('token_id', '')))
                            answer1 = outcome1.get('outcome', outcome1.get('name', outcome1.get('label', 'YES')))
                        elif isinstance(outcome1, str):
                            # If outcome is a string, it might be the token ID itself
                            token1 = outcome1
                        
                        if isinstance(outcome2, dict):
                            token2 = (outcome2.get('token_id') or outcome2.get('id') or 
                                     outcome2.get('tokenId') or outcome2.get('asset_id') or 
                                     str(outcome2.get('token_id', '')))
                            answer2 = outcome2.get('outcome', outcome2.get('name', outcome2.get('label', 'NO')))
                        elif isinstance(outcome2, str):
                            token2 = outcome2
                    
                    # Handle tokens array
                    elif tokens and len(tokens) >= 2:
                        token1_obj = tokens[0] if isinstance(tokens[0], dict) else {}
                        token2_obj = tokens[1] if isinstance(tokens[1], dict) else {}
                        
                        if isinstance(tokens[0], dict):
                            token1 = (token1_obj.get('token_id') or token1_obj.get('id') or 
                                     token1_obj.get('tokenId') or token1_obj.get('asset_id') or 
                                     str(token1_obj.get('token_id', '')))
                            answer1 = token1_obj.get('outcome', token1_obj.get('name', token1_obj.get('label', 'YES')))
                        elif isinstance(tokens[0], (str, int)):
                            token1 = str(tokens[0])
                        
                        if isinstance(tokens[1], dict):
                            token2 = (token2_obj.get('token_id') or token2_obj.get('id') or 
                                     token2_obj.get('tokenId') or token2_obj.get('asset_id') or 
                                     str(token2_obj.get('token_id', '')))
                            answer2 = token2_obj.get('outcome', token2_obj.get('name', token2_obj.get('label', 'NO')))
                        elif isinstance(tokens[1], (str, int)):
                            token2 = str(tokens[1])
                    
                    # If tokens still empty, try to get from market_data directly
                    if not token1 and not token2:
                        # Check if token IDs are at market level
                        token1 = market_data.get('token1', market_data.get('token_id_1', market_data.get('yesTokenId', '')))
                        token2 = market_data.get('token2', market_data.get('token_id_2', market_data.get('noTokenId', '')))
                
                question = market_data.get('question', '') or event.get('title', '')
                condition_id = market_data.get('conditionId', '') or market_data.get('condition_id', '') or event.get('condition_id', '') or market_data.get('id', '')
                description = event.get('description', '') or event.get('title', '')
                category = market_service.categorize_market(question, description)
                
                # Get neg_risk flag
                neg_risk_raw = market_data.get('negRisk', market_data.get('neg_risk', event.get('negRisk', 'FALSE')))
                if isinstance(neg_risk_raw, bool):
                    neg_risk = 'TRUE' if neg_risk_raw else 'FALSE'
                else:
                    neg_risk = str(neg_risk_raw).upper() if neg_risk_raw else 'FALSE'
                
                # Debug: Print what we found
                print(f"DEBUG: Extracted data - condition_id: {condition_id[:20] if condition_id else 'None'}..., token1: {token1[:20] if token1 else 'None'}..., token2: {token2[:20] if token2 else 'None'}...")
                
                # Count total sub-markets in event
                total_sub_markets = len(event_markets)
                
                return {
                    'condition_id': condition_id,
                    'question': question,
                    'answer1': answer1,
                    'answer2': answer2,
                    'token1': str(token1) if token1 else '',
                    'token2': str(token2) if token2 else '',
                    'market_slug': slug,
                    'category': category,
                    'neg_risk': neg_risk,
                    # Sub-market information
                    'has_sub_markets': total_sub_markets > 1,
                    'total_sub_markets': total_sub_markets,
                    'event_title': event.get('title', '') or event.get('question', ''),
                    'sub_markets_hint': f"This event contains {total_sub_markets} markets. Use /slug/{slug}/all to get all of them." if total_sub_markets > 1 else None
                }
            
            # Parse markets from event using parse_sub_markets
            markets = market_service.parse_sub_markets(event)
            
            if markets and len(markets) > 0:
                # Return first market (or you could return all sub-markets)
                market = markets[0]
                
                # Get category from question
                question = market.get('question', '')
                description = event.get('description', '') or event.get('title', '')
                category = market_service.categorize_market(question, description)
                market['category'] = category
                
                return market
            else:
                # If no sub-markets, try to create from event itself
                if event.get('condition_id') or event.get('question') or event.get('title'):
                    question = event.get('question') or event.get('title', '')
                    description = event.get('description', '')
                    category = market_service.categorize_market(question, description)
                    
                    return {
                        'condition_id': event.get('condition_id', ''),
                        'question': question,
                        'answer1': 'YES',
                        'answer2': 'NO',
                        'token1': '',
                        'token2': '',
                        'market_slug': slug,
                        'category': category
                    }
        
        # If event not found, try market endpoint
        url = f"https://gamma-api.polymarket.com/markets/slug/{slug}"
        # Apply rate limiting for GAMMA markets endpoint (125 requests / 10s)
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('gamma_markets')
        response = requests.get(url, timeout=10)
        rate_limiter.record_request('gamma_markets')
        
        if response.status_code == 200:
            market_data = response.json()
            
            if isinstance(market_data, dict):
                market = market_data.get('data', market_data)
            else:
                market = market_data
            
            # Extract token IDs directly from market - clobTokenIds is the most reliable source
            clob_token_ids_raw = market.get('clobTokenIds', [])
            
            # Parse clobTokenIds - it might be a JSON string
            clob_token_ids = []
            if isinstance(clob_token_ids_raw, str):
                try:
                    clob_token_ids = json.loads(clob_token_ids_raw)
                    print(f"DEBUG: Market endpoint - Parsed clobTokenIds from JSON string: {clob_token_ids}")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"DEBUG: Market endpoint - Failed to parse clobTokenIds as JSON: {e}")
                    clob_token_ids = []
            elif isinstance(clob_token_ids_raw, list):
                clob_token_ids = clob_token_ids_raw
            else:
                clob_token_ids = []
            
            token1 = ''
            token2 = ''
            answer1 = 'YES'
            answer2 = 'NO'
            
            if clob_token_ids and isinstance(clob_token_ids, list) and len(clob_token_ids) >= 2:
                token1 = str(clob_token_ids[0]) if clob_token_ids[0] is not None else ''
                token2 = str(clob_token_ids[1]) if clob_token_ids[1] is not None else ''
                print(f"DEBUG: Market endpoint - ✅ Found tokens from clobTokenIds: token1={token1[:30]}..., token2={token2[:30]}...")
            else:
                # Fallback: Try outcomes and tokens arrays
                outcomes = market.get('outcomes', [])
                tokens = market.get('tokens', [])
                if not tokens:
                    tokens = market.get('outcomeTokens', [])
                
                # Handle outcomes array
                if outcomes and len(outcomes) >= 2:
                    outcome1 = outcomes[0]
                    outcome2 = outcomes[1]
                    
                    if isinstance(outcome1, dict):
                        token1 = (outcome1.get('token_id') or outcome1.get('id') or 
                                 outcome1.get('tokenId') or outcome1.get('asset_id') or 
                                 str(outcome1.get('token_id', '')))
                        answer1 = outcome1.get('outcome', outcome1.get('name', outcome1.get('label', 'YES')))
                    elif isinstance(outcome1, (str, int)):
                        token1 = str(outcome1)
                    
                    if isinstance(outcome2, dict):
                        token2 = (outcome2.get('token_id') or outcome2.get('id') or 
                                 outcome2.get('tokenId') or outcome2.get('asset_id') or 
                                 str(outcome2.get('token_id', '')))
                        answer2 = outcome2.get('outcome', outcome2.get('name', outcome2.get('label', 'NO')))
                    elif isinstance(outcome2, (str, int)):
                        token2 = str(outcome2)
                
                # Handle tokens array
                elif tokens and len(tokens) >= 2:
                    if isinstance(tokens[0], dict):
                        token1_obj = tokens[0]
                        token1 = (token1_obj.get('token_id') or token1_obj.get('id') or 
                                 token1_obj.get('tokenId') or token1_obj.get('asset_id') or 
                                 str(token1_obj.get('token_id', '')))
                        answer1 = token1_obj.get('outcome', token1_obj.get('name', token1_obj.get('label', 'YES')))
                    elif isinstance(tokens[0], (str, int)):
                        token1 = str(tokens[0])
                    
                    if isinstance(tokens[1], dict):
                        token2_obj = tokens[1]
                        token2 = (token2_obj.get('token_id') or token2_obj.get('id') or 
                                 token2_obj.get('tokenId') or token2_obj.get('asset_id') or 
                                 str(token2_obj.get('token_id', '')))
                        answer2 = token2_obj.get('outcome', token2_obj.get('name', token2_obj.get('label', 'NO')))
                    elif isinstance(tokens[1], (str, int)):
                        token2 = str(tokens[1])
                
                # If tokens still empty, try to get from market directly
                if not token1 and not token2:
                    token1 = market.get('token1', market.get('token_id_1', market.get('yesTokenId', '')))
                    token2 = market.get('token2', market.get('token_id_2', market.get('noTokenId', '')))
            
            question = market.get('question', '')
            condition_id = market.get('conditionId', '') or market.get('condition_id', '') or market.get('id', '')
            description = market.get('description', '')
            category = market_service.categorize_market(question, description)
            
            return {
                'condition_id': condition_id,
                'question': question,
                'answer1': answer1,
                'answer2': answer2,
                'token1': token1,
                'token2': token2,
                'market_slug': slug,
                'category': category
            }
        
        raise HTTPException(status_code=404, detail=f"Market with slug '{slug}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching market by slug: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Error fetching market: {error_msg}")

@router.get("/{market_id}", response_model=MarketWithConfig)
async def get_market(market_id: int, db: Session = Depends(get_db)):
    """Get a specific market with its configuration"""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    return market

@router.post("/", response_model=MarketResponse)
async def create_market(market: MarketCreate, db: Session = Depends(get_db)):
    """Create a new market"""
    try:
        # Check if market already exists
        existing = db.query(Market).filter(Market.condition_id == market.condition_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Market with this condition_id already exists")
        
        db_market = Market(**market.model_dump())
        db.add(db_market)
        db.flush()  # Flush to get the ID without committing
        
        # Create default trading params only if they don't exist
        existing_params = db.query(TradingParams).filter(TradingParams.market_id == db_market.id).first()
        if not existing_params:
            default_params = TradingParams(market_id=db_market.id)
            db.add(default_params)
        
        db.commit()
        db.refresh(db_market)
        
        # Invalidate cache after market creation
        try:
            from services.market_service import MarketService
            market_service = MarketService()
            market_service.invalidate_market_cache(db_market)
        except Exception as e:
            # Don't fail if cache invalidation fails
            print(f"Warning: Failed to invalidate cache after market creation: {e}")
        
        return db_market
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating market: {str(e)}")

@router.put("/{market_id}", response_model=MarketResponse)
async def update_market(market_id: int, market_update: MarketUpdate, db: Session = Depends(get_db)):
    """Update a market"""
    try:
        db_market = db.query(Market).filter(Market.id == market_id).first()
        if not db_market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Store old values for cache invalidation
        old_token1 = db_market.token1
        old_token2 = db_market.token2
        old_condition_id = db_market.condition_id
        
        update_data = market_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_market, key, value)
        
        db.commit()
        db.refresh(db_market)
        
        # Invalidate cache after market update
        try:
            from services.market_service import MarketService
            market_service = MarketService()
            # Invalidate old and new cache entries
            if old_token1 != db_market.token1:
                from services.market_mapping_service import get_market_mapper
                get_market_mapper().invalidate_token_cache(old_token1)
            if old_token2 != db_market.token2:
                from services.market_mapping_service import get_market_mapper
                get_market_mapper().invalidate_token_cache(old_token2)
            if old_condition_id != db_market.condition_id:
                from services.market_mapping_service import get_market_mapper
                get_market_mapper().invalidate_condition_cache(old_condition_id)
            market_service.invalidate_market_cache(db_market)
        except Exception as e:
            # Don't fail if cache invalidation fails
            print(f"Warning: Failed to invalidate cache after market update: {e}")
        
        return db_market
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating market: {str(e)}")

@router.delete("/{market_id}")
async def delete_market(market_id: int, db: Session = Depends(get_db)):
    """Delete a market"""
    try:
        db_market = db.query(Market).filter(Market.id == market_id).first()
        if not db_market:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # Store values for cache invalidation before deletion
        token1 = db_market.token1
        token2 = db_market.token2
        condition_id = db_market.condition_id
        
        db.delete(db_market)
        db.commit()
        
        # Invalidate cache after market deletion
        try:
            from services.market_service import MarketService
            market_service = MarketService()
            market_service.invalidate_market_cache({
                'token1': token1,
                'token2': token2,
                'condition_id': condition_id
            })
        except Exception as e:
            # Don't fail if cache invalidation fails
            print(f"Warning: Failed to invalidate cache after market deletion: {e}")
        
        return {"message": "Market deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting market: {str(e)}")

@router.post("/bulk/update")
async def bulk_update_markets(
    bulk_update: BulkMarketUpdate,
    db: Session = Depends(get_db)
):
    """Bulk update multiple markets"""
    if not bulk_update.market_ids:
        raise HTTPException(status_code=400, detail="No market IDs provided")
    
    markets = db.query(Market).filter(Market.id.in_(bulk_update.market_ids)).all()
    if not markets:
        raise HTTPException(status_code=404, detail="No markets found")
    
    # Get update data excluding market_ids
    update_data = bulk_update.model_dump(exclude={'market_ids'}, exclude_unset=True)
    updated_count = 0
    
    for market in markets:
        for key, value in update_data.items():
            setattr(market, key, value)
        updated_count += 1
    
    db.commit()
    return {
        "message": f"Successfully updated {updated_count} market(s)",
        "updated_count": updated_count
    }

@router.post("/bulk/delete")
async def bulk_delete_markets(
    bulk_delete: BulkMarketDelete,
    db: Session = Depends(get_db)
):
    """Bulk delete multiple markets"""
    if not bulk_delete.market_ids:
        raise HTTPException(status_code=400, detail="No market IDs provided")
    
    markets = db.query(Market).filter(Market.id.in_(bulk_delete.market_ids)).all()
    if not markets:
        raise HTTPException(status_code=404, detail="No markets found")
    
    deleted_count = 0
    for market in markets:
        db.delete(market)
        deleted_count += 1
    
    db.commit()
    return {
        "message": f"Successfully deleted {deleted_count} market(s)",
        "deleted_count": deleted_count
    }

@router.post("/cleanup-orphans")
async def cleanup_orphan_records(db: Session = Depends(get_db)):
    """
    Clean up orphan trading_params records that don't have a corresponding market.
    This can happen if markets are deleted but the cascade doesn't work properly.
    """
    try:
        # Find orphan trading_params (where market_id doesn't exist in markets table)
        orphan_params = db.query(TradingParams).filter(
            ~TradingParams.market_id.in_(
                db.query(Market.id)
            )
        ).all()
        
        deleted_count = len(orphan_params)
        
        for param in orphan_params:
            db.delete(param)
        
        db.commit()
        
        return {
            "message": f"Cleaned up {deleted_count} orphan trading_params record(s)",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error cleaning up orphan records: {str(e)}")


@router.delete("/all")
async def delete_all_markets(db: Session = Depends(get_db)):
    """
    Delete ALL markets from the database.
    This will also delete related trading_params, positions, and orders due to cascade.
    WARNING: This action cannot be undone!
    """
    try:
        # Count markets before deletion
        total_markets = db.query(Market).count()
        
        if total_markets == 0:
            return {
                "message": "No markets to delete",
                "deleted_count": 0
            }
        
        # Delete all markets (cascade will handle related records)
        deleted_count = db.query(Market).delete()
        db.commit()
        
        return {
            "message": f"Successfully deleted all {deleted_count} market(s) and related data",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting markets: {str(e)}")

@router.get("/{market_id}/config", response_model=TradingParamsResponse)
async def get_market_config(market_id: int, db: Session = Depends(get_db)):
    """Get trading configuration for a market"""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if not market.trading_params:
        # Create default params if they don't exist
        params = TradingParams(market_id=market_id)
        db.add(params)
        db.commit()
        db.refresh(params)
        return params
    
    return market.trading_params

@router.put("/{market_id}/config", response_model=TradingParamsResponse)
async def update_market_config(
    market_id: int,
    params_update: TradingParamsUpdate,
    db: Session = Depends(get_db)
):
    """Update trading configuration for a market"""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    if not market.trading_params:
        raise HTTPException(status_code=404, detail="Trading params not found")
    
    update_data = params_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(market.trading_params, key, value)
    
    db.commit()
    db.refresh(market.trading_params)
    return market.trading_params

async def fetch_and_save_all_markets():
    """Background task to fetch and save all markets with categorization"""
    from services.market_service import MarketService
    from datetime import datetime
    from database import SessionLocal
    
    # Create new database session for background task
    db = SessionLocal()
    
    try:
        # Initialize market service
        market_service = MarketService()
        
        # Check if client is initialized
        if not market_service.client:
            fetch_progress.update({
                "status": "error",
                "error": "Polymarket client not initialized",
                "completed_at": datetime.utcnow().isoformat()
            })
            return
        
        # Fetch all markets with categorization
        print("Fetching all markets from Polymarket...")
        all_markets = await market_service.fetch_all_markets_categorized()
        
        fetch_progress["total_fetched"] = len(all_markets)
        fetch_progress["status"] = "processing"
        
        if not all_markets:
            fetch_progress.update({
                "status": "error",
                "error": "No markets found",
                "completed_at": datetime.utcnow().isoformat()
            })
            return
        
        print(f"Found {len(all_markets)} markets, saving to database...")
        
        # Save to database in batches
        saved_markets = []
        errors = []
        batch_size = 100  # Process 100 markets at a time
        
        for i in range(0, len(all_markets), batch_size):
            batch = all_markets[i:i + batch_size]
            
            for market_data in batch:
                try:
                    # Filter out fields that don't exist in Market model
                    valid_fields = {
                        'condition_id', 'question', 'answer1', 'answer2', 
                        'token1', 'token2', 'market_slug', 'neg_risk',
                        'best_bid', 'best_ask', 'spread', 'category'
                    }
                    
                    # Only keep fields that exist in Market model
                    filtered_data = {
                        k: v for k, v in market_data.items() 
                        if k in valid_fields
                    }
                    
                    # Ensure category is set
                    if 'category' not in filtered_data or not filtered_data['category']:
                        filtered_data['category'] = 'other'
                    
                    # Check if market already exists
                    existing = db.query(Market).filter(
                        Market.condition_id == filtered_data.get('condition_id')
                    ).first()
                    
                    if existing:
                        # Update existing market (including category)
                        for key, value in filtered_data.items():
                            if hasattr(existing, key) and key != 'id':
                                setattr(existing, key, value)
                        
                        # Only create trading_params if they don't exist
                        if not existing.trading_params:
                            default_params = TradingParams(market_id=existing.id)
                            db.add(default_params)
                        
                        saved_markets.append(existing)
                    else:
                        # Create new market with proper category
                        db_market = Market(**filtered_data)
                        db.add(db_market)
                        db.flush()  # Flush to get the ID without committing
                        
                        # Verify market_id is set
                        if db_market.id is None:
                            raise ValueError(f"Market ID is None after flush for market: {filtered_data.get('question', 'unknown')}")
                        
                        # Create default trading params only if they don't exist
                        existing_params = db.query(TradingParams).filter(TradingParams.market_id == db_market.id).first()
                        if not existing_params:
                            default_params = TradingParams(market_id=db_market.id)
                            db.add(default_params)
                        
                        saved_markets.append(db_market)
                    
                    fetch_progress["total_processed"] += 1
                    
                except Exception as e:
                    errors.append(f"Error saving market {market_data.get('question', 'unknown')}: {str(e)}")
                    import traceback
                    print(f"Full error: {traceback.format_exc()}")
                    continue
            
            # Commit batch
            try:
                db.commit()
                fetch_progress["total_saved"] = len(saved_markets)
            except Exception as e:
                db.rollback()
                print(f"Error committing batch: {e}")
            
            # Progress update
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(all_markets):
                print(f"Processed {min(i + batch_size, len(all_markets))}/{len(all_markets)} markets...")
        
        if errors:
            print(f"Warning: {len(errors)} errors occurred while saving markets:")
            for error in errors[:5]:  # Print first 5 errors
                print(f"  - {error}")
        
        fetch_progress.update({
            "status": "completed" if saved_markets else "error",
            "total_saved": len(saved_markets),
            "error": f"{len(errors)} errors" if errors else None,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        print(f"Successfully saved {len(saved_markets)} markets to database")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in background fetch: {error_msg}")
        import traceback
        traceback.print_exc()
        fetch_progress.update({
            "status": "error",
            "error": error_msg,
            "completed_at": datetime.utcnow().isoformat()
        })
    finally:
        db.close()

async def fetch_and_save_crypto_markets():
    """Background task to fetch and save crypto markets"""
    from services.market_service import MarketService
    from datetime import datetime
    from database import SessionLocal
    
    # Create new database session for background task
    db = SessionLocal()
    
    try:
        # Initialize market service
        market_service = MarketService()
        
        # Check if client is initialized
        if not market_service.client:
            fetch_progress.update({
                "status": "error",
                "error": "Polymarket client not initialized",
                "completed_at": datetime.utcnow().isoformat()
            })
            return
        
        # Fetch crypto markets
        print("Fetching crypto markets from Polymarket...")
        crypto_markets = await market_service.fetch_crypto_markets()
        
        fetch_progress["total_fetched"] = len(crypto_markets)
        fetch_progress["status"] = "processing"
        
        if not crypto_markets:
            fetch_progress.update({
                "status": "error",
                "error": "No crypto markets found",
                "completed_at": datetime.utcnow().isoformat()
            })
            return
        
        print(f"Found {len(crypto_markets)} crypto markets, saving to database...")
        
        # Save to database in batches
        saved_markets = []
        errors = []
        batch_size = 100  # Process 100 markets at a time (increased for speed)
        
        for i in range(0, len(crypto_markets), batch_size):
            batch = crypto_markets[i:i + batch_size]
            
            for market_data in batch:
                try:
                    # Filter out fields that don't exist in Market model
                    valid_fields = {
                        'condition_id', 'question', 'answer1', 'answer2', 
                        'token1', 'token2', 'market_slug', 'neg_risk',
                        'best_bid', 'best_ask', 'spread'
                    }
                    
                    # Only keep fields that exist in Market model
                    filtered_data = {
                        k: v for k, v in market_data.items() 
                        if k in valid_fields
                    }
                    
                    # Check if market already exists
                    existing = db.query(Market).filter(
                        Market.condition_id == filtered_data.get('condition_id')
                    ).first()
                    
                    if existing:
                        # Update existing market
                        for key, value in filtered_data.items():
                            if hasattr(existing, key) and key != 'id':
                                setattr(existing, key, value)
                        saved_markets.append(existing)
                    else:
                        # Create new market with crypto category
                        if 'category' not in filtered_data:
                            filtered_data['category'] = 'crypto'
                        db_market = Market(**filtered_data)
                        db.add(db_market)
                        db.flush()  # Flush to get the ID without committing
                        
                        # Verify market_id is set
                        if db_market.id is None:
                            raise ValueError(f"Market ID is None after flush for market: {filtered_data.get('question', 'unknown')}")
                        
                        # Create default trading params (now market_id is available)
                        default_params = TradingParams(market_id=db_market.id)
                        db.add(default_params)
                        
                        saved_markets.append(db_market)
                    
                    fetch_progress["total_processed"] += 1
                    
                except Exception as e:
                    errors.append(f"Error saving market {market_data.get('question', 'unknown')}: {str(e)}")
                    import traceback
                    print(f"Full error: {traceback.format_exc()}")
                    continue
            
            # Commit batch
            try:
                db.commit()
                fetch_progress["total_saved"] = len(saved_markets)
            except Exception as e:
                db.rollback()
                print(f"Error committing batch: {e}")
            
            # Progress update
            if (i + batch_size) % 500 == 0 or (i + batch_size) >= len(crypto_markets):
                print(f"Processed {min(i + batch_size, len(crypto_markets))}/{len(crypto_markets)} markets...")
        
        if errors:
            print(f"Warning: {len(errors)} errors occurred while saving markets:")
            for error in errors[:5]:  # Print first 5 errors
                print(f"  - {error}")
        
        fetch_progress.update({
            "status": "completed" if saved_markets else "error",
            "total_saved": len(saved_markets),
            "error": f"{len(errors)} errors" if errors else None,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        print(f"Successfully saved {len(saved_markets)} markets to database")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error in background fetch: {error_msg}")
        import traceback
        traceback.print_exc()
        fetch_progress.update({
            "status": "error",
            "error": error_msg,
            "completed_at": datetime.utcnow().isoformat()
        })
    finally:
        db.close()

