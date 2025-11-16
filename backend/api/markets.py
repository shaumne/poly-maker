"""
Markets API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, Market, TradingParams
from schemas import (
    MarketCreate, MarketUpdate, MarketResponse, MarketWithConfig,
    TradingParamsCreate, TradingParamsUpdate, TradingParamsResponse,
    BulkMarketUpdate, BulkMarketDelete
)

router = APIRouter()

@router.get("/", response_model=List[MarketResponse])
async def get_markets(
    skip: int = 0,
    limit: int = Query(default=1000, le=10000),  # Default 1000, max 10000
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all markets with optional filtering"""
    query = db.query(Market)
    
    if category:
        query = query.filter(Market.category == category)
    if is_active is not None:
        query = query.filter(Market.is_active == is_active)
    
    markets = query.offset(skip).limit(limit).all()
    return markets

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
    # Check if market already exists
    existing = db.query(Market).filter(Market.condition_id == market.condition_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Market with this condition_id already exists")
    
    db_market = Market(**market.model_dump())
    db.add(db_market)
    db.commit()
    db.refresh(db_market)
    
    # Create default trading params
    default_params = TradingParams(market_id=db_market.id)
    db.add(default_params)
    db.commit()
    
    return db_market

@router.put("/{market_id}", response_model=MarketResponse)
async def update_market(market_id: int, market_update: MarketUpdate, db: Session = Depends(get_db)):
    """Update a market"""
    db_market = db.query(Market).filter(Market.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    update_data = market_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_market, key, value)
    
    db.commit()
    db.refresh(db_market)
    return db_market

@router.delete("/{market_id}")
async def delete_market(market_id: int, db: Session = Depends(get_db)):
    """Delete a market"""
    db_market = db.query(Market).filter(Market.id == market_id).first()
    if not db_market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    db.delete(db_market)
    db.commit()
    return {"message": "Market deleted successfully"}

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

# Store for tracking fetch progress
fetch_progress = {
    "status": "idle",  # idle, fetching, processing, completed, error
    "total_fetched": 0,
    "total_processed": 0,
    "total_saved": 0,
    "error": None,
    "started_at": None,
    "completed_at": None
}

@router.get("/crypto/fetch/status")
async def get_fetch_status():
    """Get the status of crypto markets fetch operation"""
    return fetch_progress

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
                        # Create new market
                        db_market = Market(**filtered_data, category='crypto')
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

