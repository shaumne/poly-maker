"""
Trading control API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, TradingStatus
from schemas import TradingStatusResponse
from services.trading_service import TradingService
import asyncio

router = APIRouter()

# Global trading service instance
trading_service = None

@router.get("/status", response_model=TradingStatusResponse)
async def get_trading_status(db: Session = Depends(get_db)):
    """Get current trading bot status"""
    status = db.query(TradingStatus).first()
    if not status:
        status = TradingStatus(is_running=False)
        db.add(status)
        db.commit()
        db.refresh(status)
    return status

@router.post("/start")
async def start_trading(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Start the trading bot"""
    global trading_service
    
    status = db.query(TradingStatus).first()
    if not status:
        status = TradingStatus()
        db.add(status)
    
    if status.is_running:
        raise HTTPException(status_code=400, detail="Trading bot is already running")
    
    # Initialize trading service if not exists
    if trading_service is None:
        trading_service = TradingService(db)
    
    # Start trading in background
    background_tasks.add_task(trading_service.start)
    
    # Update status
    from datetime import datetime
    status.is_running = True
    status.started_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Trading bot started successfully"}

@router.post("/stop")
async def stop_trading(db: Session = Depends(get_db)):
    """Stop the trading bot"""
    global trading_service
    
    status = db.query(TradingStatus).first()
    if not status or not status.is_running:
        raise HTTPException(status_code=400, detail="Trading bot is not running")
    
    # Stop trading service
    if trading_service:
        await trading_service.stop()
    
    # Update status
    from datetime import datetime
    status.is_running = False
    status.stopped_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Trading bot stopped successfully"}

@router.post("/restart")
async def restart_trading(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Restart the trading bot"""
    # Stop first
    try:
        await stop_trading(db)
    except:
        pass
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Start again
    return await start_trading(background_tasks, db)

@router.get("/test-info")
async def get_test_info():
    """Get information about testing the trading bot"""
    from backend.config import Config
    
    return {
        "dry_run_mode": Config.is_dry_run(),
        "live_trading_mode": Config.is_live_trading(),
        "max_trade_size": Config.MAX_TRADE_SIZE,
        "max_position_size": Config.MAX_POSITION_SIZE,
        "min_trade_size": Config.MIN_TRADE_SIZE,
        "testing_guide": {
            "dry_run_testing": {
                "description": "Test trading without real orders",
                "steps": [
                    "1. Set DRY_RUN=true in .env file",
                    "2. Start the bot",
                    "3. Check backend logs for [DRY RUN] messages",
                    "4. Verify orders would be created (but aren't actually sent)"
                ],
                "what_to_look_for": [
                    "[DRY RUN] Would create BUY order",
                    "[DRY RUN] Would create SELL order",
                    "[DRY RUN] Would cancel orders"
                ]
            },
            "live_testing": {
                "description": "Test with real orders (use small amounts!)",
                "steps": [
                    "1. Set DRY_RUN=false in .env file",
                    "2. Set MAX_TRADE_SIZE to small value (2-5 USD)",
                    "3. Set MAX_POSITION_SIZE to small value (10-20 USD)",
                    "4. Start the bot",
                    "5. Check Polymarket website for actual orders",
                    "6. Monitor backend logs (no [DRY RUN] prefix)"
                ],
                "safety_checks": [
                    "Verify DRY_RUN=false",
                    "Use small trade sizes",
                    "Set stop loss",
                    "Monitor closely"
                ]
            },
            "log_monitoring": {
                "description": "How to monitor bot activity",
                "backend_logs": "Check the terminal where backend is running",
                "what_to_watch": [
                    "Order creation messages",
                    "Order cancellation messages",
                    "Market analysis logs",
                    "Strategy decision logs"
                ],
                "log_file": "You can redirect logs to file: python -m uvicorn main:app > trading.log 2>&1"
            }
        }
    }

@router.get("/diagnostics")
async def get_trading_diagnostics(db: Session = Depends(get_db)):
    """Get diagnostic information about why orders might not be created"""
    from database import Market
    import poly_data.global_state as global_state
    
    diagnostics = {
        "bot_status": {},
        "markets": {},
        "websocket": {},
        "recommendations": []
    }
    
    # Check bot status
    status = db.query(TradingStatus).first()
    diagnostics["bot_status"] = {
        "is_running": status.is_running if status else False,
        "started_at": str(status.started_at) if status and status.started_at else None,
        "message": "✅ Bot is running" if (status and status.is_running) else "❌ Bot is NOT running - click Start Trading"
    }
    
    if not status or not status.is_running:
        diagnostics["recommendations"].append("Bot is not running. Go to Dashboard and click 'Start Trading'")
        return diagnostics
    
    # Check markets
    try:
        markets = db.query(Market).filter(Market.is_active == True).all()
        active_markets = [m for m in markets if m.trading_params]
        
        # Check if global_state.df exists and is not None
        loaded_in_memory = 0
        if hasattr(global_state, 'df') and global_state.df is not None:
            try:
                loaded_in_memory = len(global_state.df) if not global_state.df.empty else 0
            except:
                loaded_in_memory = 0
        
        diagnostics["markets"] = {
            "total_active": len(active_markets),
            "markets_with_params": len([m for m in markets if m.trading_params]),
            "markets_without_params": len([m for m in markets if not m.trading_params]),
            "loaded_in_memory": loaded_in_memory,
            "message": f"✅ {len(active_markets)} active markets with trading params" if active_markets else "❌ No active markets with trading params"
        }
        
        if not active_markets:
            diagnostics["recommendations"].append("No active markets found. Go to Markets page, configure markets, and ensure is_active = true")
        
        if not hasattr(global_state, 'df') or global_state.df is None or (hasattr(global_state.df, 'empty') and global_state.df.empty):
            diagnostics["recommendations"].append("Markets not loaded in memory. Bot may need to be restarted.")
        
    except Exception as e:
        diagnostics["markets"] = {
            "error": str(e),
            "total_active": 0,
            "markets_with_params": 0,
            "markets_without_params": 0,
            "loaded_in_memory": 0,
            "message": f"❌ Error checking markets: {str(e)}"
        }
    
    # Check websocket/tokens
    try:
        tokens_count = len(global_state.all_tokens) if hasattr(global_state, 'all_tokens') else 0
        client_initialized = hasattr(global_state, 'client') and global_state.client is not None
        
        # Get sample token info if available
        sample_tokens = []
        if hasattr(global_state, 'all_tokens') and global_state.all_tokens:
            sample_tokens = global_state.all_tokens[:3]  # First 3 tokens
        
        diagnostics["websocket"] = {
            "tokens_to_subscribe": tokens_count,
            "client_initialized": client_initialized,
            "sample_tokens": sample_tokens,
            "message": f"✅ {tokens_count} tokens ready for subscription" if tokens_count > 0 else "❌ No tokens to subscribe to"
        }
        
        if tokens_count == 0:
            diagnostics["recommendations"].append("No tokens found. Markets may not have token1/token2 set properly.")
            # Check if we can get market token info from database
            try:
                from database import Market
                sample_market = db.query(Market).filter(Market.is_active == True).first()
                if sample_market:
                    diagnostics["websocket"]["sample_market_tokens"] = {
                        "question": sample_market.question,
                        "token1": sample_market.token1 if sample_market.token1 else "MISSING",
                        "token2": sample_market.token2 if sample_market.token2 else "MISSING"
                    }
                    if not sample_market.token1 or not sample_market.token2:
                        diagnostics["recommendations"].append(f"Sample market '{sample_market.question}' has missing tokens. Please re-fetch or update the market.")
            except Exception as e:
                pass
        
    except Exception as e:
        diagnostics["websocket"] = {
            "error": str(e),
            "tokens_to_subscribe": 0,
            "client_initialized": False,
            "message": f"❌ Error checking websocket: {str(e)}"
        }
    
    # Check for common issues
    total_active = diagnostics["markets"].get("total_active", 0)
    if diagnostics["bot_status"]["is_running"] and total_active > 0:
        diagnostics["recommendations"].append("✅ Bot is running and markets are active. Check backend logs for:")
        diagnostics["recommendations"].append("   - '📊 Received book update' messages (websocket working)")
        diagnostics["recommendations"].append("   - '🔄 Triggering perform_trade' messages (trading triggered)")
        diagnostics["recommendations"].append("   - '🔍 Processing trade' messages (trade function called)")
        diagnostics["recommendations"].append("   - '[DRY RUN] Would create' messages (orders would be sent)")
        diagnostics["recommendations"].append("If you don't see these, websocket may not be receiving data yet.")
    
    return diagnostics

