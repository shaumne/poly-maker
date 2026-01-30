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


@router.post("/reset-closed-only-mode")
async def reset_closed_only_mode():
    """
    Reset the 'closed only mode' flag.
    
    Use this when your Polymarket account restriction has been lifted
    but the bot is still skipping orders due to the cached flag.
    """
    try:
        import poly_data.global_state as global_state
        
        was_in_closed_mode = global_state.account_in_closed_only_mode
        global_state.account_in_closed_only_mode = False
        
        return {
            "message": "Closed only mode flag has been reset",
            "previous_state": was_in_closed_mode,
            "current_state": False,
            "note": "The bot will now attempt to place orders again. If your account is still restricted, the flag will be set again automatically."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset flag: {str(e)}")

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
    import asyncio
    from concurrent.futures import TimeoutError
    
    diagnostics = {
        "bot_status": {},
        "markets": {},
        "websocket": {},
        "recommendations": []
    }
    
    try:
        # Wrap the entire diagnostic check in a timeout
        async def run_diagnostics():
            from database import Market
            import poly_data.global_state as global_state
            
            # Check bot status (fast)
            try:
                status = db.query(TradingStatus).first()
                diagnostics["bot_status"] = {
                    "is_running": status.is_running if status else False,
                    "started_at": str(status.started_at) if status and status.started_at else None,
                    "message": "✅ Bot is running" if (status and status.is_running) else "❌ Bot is NOT running - click Start Trading"
                }
                
                if not status or not status.is_running:
                    diagnostics["recommendations"].append("Bot is not running. Go to Dashboard and click 'Start Trading'")
                    return diagnostics
            except Exception as e:
                diagnostics["bot_status"] = {"error": str(e), "is_running": False}
            
            # Check markets (optimized query)
            try:
                # Direct count queries - simpler and more reliable
                total_active = db.query(Market).filter(Market.is_active == True).count()
                
                # Count markets that have trading_params relationship
                markets_with_params = db.query(Market).join(
                    Market.trading_params
                ).filter(Market.is_active == True).count()
                
                # Quick check of global state
                loaded_in_memory = 0
                try:
                    if hasattr(global_state, 'df') and global_state.df is not None and hasattr(global_state.df, '__len__'):
                        loaded_in_memory = len(global_state.df) if not global_state.df.empty else 0
                except:
                    pass
                
                diagnostics["markets"] = {
                    "total_active": total_active,
                    "markets_with_params": markets_with_params,
                    "loaded_in_memory": loaded_in_memory,
                    "message": f"✅ {markets_with_params} active markets with trading params" if markets_with_params > 0 else "❌ No active markets with trading params"
                }
                
                if markets_with_params == 0:
                    diagnostics["recommendations"].append("No active markets found. Go to Markets page, configure markets, and ensure is_active = true")
                
                if loaded_in_memory == 0:
                    diagnostics["recommendations"].append("Markets not loaded in memory. Bot may need to be restarted.")
                
            except Exception as e:
                diagnostics["markets"] = {
                    "error": str(e),
                    "total_active": 0,
                    "markets_with_params": 0,
                    "loaded_in_memory": 0,
                    "message": f"❌ Error checking markets: {str(e)}"
                }
            
            # Check websocket/tokens (fast)
            try:
                import poly_data.global_state as global_state
                tokens_count = len(global_state.all_tokens) if hasattr(global_state, 'all_tokens') and global_state.all_tokens else 0
                client_initialized = hasattr(global_state, 'client') and global_state.client is not None
                
                diagnostics["websocket"] = {
                    "tokens_to_subscribe": tokens_count,
                    "client_initialized": client_initialized,
                    "message": f"✅ {tokens_count} tokens ready for subscription" if tokens_count > 0 else "❌ No tokens to subscribe to"
                }
                
                if tokens_count == 0:
                    diagnostics["recommendations"].append("No tokens found. Markets may not have token1/token2 set properly.")
                
            except Exception as e:
                diagnostics["websocket"] = {
                    "error": str(e),
                    "tokens_to_subscribe": 0,
                    "client_initialized": False,
                    "message": f"❌ Error checking websocket: {str(e)}"
                }
            
            # Final recommendations
            total_active = diagnostics["markets"].get("markets_with_params", 0)
            if diagnostics["bot_status"].get("is_running") and total_active > 0:
                diagnostics["recommendations"].append("✅ Bot is running and markets are active. Check backend logs for trading activity.")
            
            return diagnostics
        
        # Run with 5 second timeout
        result = await asyncio.wait_for(run_diagnostics(), timeout=5.0)
        return result
        
    except asyncio.TimeoutError:
        return {
            "error": "Diagnostics check timed out",
            "bot_status": {"message": "Unable to check - operation timed out"},
            "markets": {"message": "Unable to check - operation timed out"},
            "websocket": {"message": "Unable to check - operation timed out"},
            "recommendations": [
                "Diagnostics check timed out after 5 seconds",
                "This may indicate a database lock or slow query",
                "Try restarting the backend server",
                "Check backend logs for errors"
            ]
        }
    except Exception as e:
        return {
            "error": str(e),
            "bot_status": {},
            "markets": {},
            "websocket": {},
            "recommendations": [f"Error running diagnostics: {str(e)}"]
        }

