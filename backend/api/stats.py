"""
Statistics API endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, Market, Position, Order, TradingStatus
from schemas import StatsResponse
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Get overall trading statistics"""
    # Count markets
    total_markets = db.query(Market).count()
    active_markets = db.query(Market).filter(Market.is_active == True).count()
    
    # Count positions
    total_positions = db.query(Position).filter(Position.size > 0).count()
    
    # Calculate PnL
    total_pnl = db.query(func.sum(Position.realized_pnl + Position.unrealized_pnl)).scalar() or 0.0
    
    # Today's PnL (from orders filled today)
    today = datetime.utcnow().date()
    today_pnl = db.query(func.sum(Position.realized_pnl)).filter(
        func.date(Position.updated_at) == today
    ).scalar() or 0.0
    
    # Count orders
    total_orders = db.query(Order).count()
    active_orders = db.query(Order).filter(Order.status == 'PENDING').count()
    
    # Fetch positions value from Polymarket (skip USDC balance)
    positions_value = None
    
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if credentials are configured
        pk = os.getenv("PK", "")
        browser_address = os.getenv("BROWSER_ADDRESS", "")
        
        # Skip balance fetch if credentials are not configured
        if not pk or pk in ["your_private_key_here", "your_actual_private_key"]:
            print("Warning: PK not configured, skipping wallet balance fetch")
        elif not browser_address or browser_address in ["your_wallet_address_here", "your_actual_wallet_address"]:
            print("Warning: BROWSER_ADDRESS not configured, skipping wallet balance fetch")
        else:
            from poly_data.polymarket_client import PolymarketClient
            client = PolymarketClient()
            # Only fetch positions value, not USDC balance
            positions_value = round(client.get_pos_balance(), 2)
    except Exception as e:
        error_msg = str(e)
        # Only log if it's not a configuration issue
        if "hex string" not in error_msg.lower() and "your_actual" not in error_msg.lower():
            print(f"Warning: Failed to fetch positions balance: {error_msg}")
        # Continue without balance info if it fails
    
    return StatsResponse(
        total_markets=total_markets,
        active_markets=active_markets,
        total_positions=total_positions,
        total_pnl=round(total_pnl, 2),
        today_pnl=round(today_pnl, 2),
        total_orders=total_orders,
        active_orders=active_orders,
        usdc_balance=None,  # Don't show USDC balance
        total_balance=positions_value,  # Show only positions value as total
        positions_value=positions_value
    )

@router.get("/pnl/breakdown")
async def get_pnl_breakdown(db: Session = Depends(get_db)):
    """Get PnL breakdown by market"""
    positions = db.query(
        Position.market_id,
        Market.question,
        func.sum(Position.realized_pnl).label('realized'),
        func.sum(Position.unrealized_pnl).label('unrealized')
    ).join(Market).group_by(Position.market_id, Market.question).all()
    
    breakdown = []
    for pos in positions:
        breakdown.append({
            'market_id': pos.market_id,
            'question': pos.question,
            'realized_pnl': round(pos.realized or 0, 2),
            'unrealized_pnl': round(pos.unrealized or 0, 2),
            'total_pnl': round((pos.realized or 0) + (pos.unrealized or 0), 2)
        })
    
    return {'breakdown': breakdown}

@router.get("/performance/daily")
async def get_daily_performance(days: int = 7, db: Session = Depends(get_db)):
    """Get daily performance for the last N days"""
    performance = []
    
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).date()
        
        # Orders filled on this day
        orders_count = db.query(Order).filter(
            func.date(Order.filled_at) == date,
            Order.status == 'FILLED'
        ).count()
        
        # PnL on this day (approximate from position updates)
        daily_pnl = db.query(func.sum(Position.realized_pnl)).filter(
            func.date(Position.updated_at) == date
        ).scalar() or 0.0
        
        performance.append({
            'date': str(date),
            'orders': orders_count,
            'pnl': round(daily_pnl, 2)
        })
    
    return {'performance': performance[::-1]}  # Reverse to show oldest first

