"""
Orders API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, Order, Market
from schemas import OrderResponse

router = APIRouter()

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    market_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all orders with optional filtering"""
    query = db.query(Order)
    
    if market_id:
        query = query.filter(Order.market_id == market_id)
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(Order.created_at.desc()).limit(limit).all()
    return orders

@router.get("/active", response_model=List[OrderResponse])
async def get_active_orders(db: Session = Depends(get_db)):
    """Get all active orders"""
    orders = db.query(Order).filter(Order.status == 'PENDING').all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/market/{market_id}", response_model=List[OrderResponse])
async def get_market_orders(market_id: int, db: Session = Depends(get_db)):
    """Get all orders for a specific market"""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    orders = db.query(Order).filter(Order.market_id == market_id).order_by(Order.created_at.desc()).all()
    return orders

