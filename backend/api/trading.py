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

