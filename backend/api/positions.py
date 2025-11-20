"""
Positions API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, Position, Market
from schemas import PositionResponse

router = APIRouter()

@router.get("/", response_model=List[PositionResponse])
async def get_positions(
    market_id: Optional[int] = None,
    side: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all positions with optional filtering"""
    query = db.query(Position).filter(Position.size > 0)  # Only show positions with size > 0
    
    if market_id:
        query = query.filter(Position.market_id == market_id)
    if side:
        query = query.filter(Position.side == side)
    
    positions = query.all()
    return positions

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: int, db: Session = Depends(get_db)):
    """Get a specific position"""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position

@router.get("/market/{market_id}", response_model=List[PositionResponse])
async def get_market_positions(market_id: int, db: Session = Depends(get_db)):
    """Get all positions for a specific market"""
    market = db.query(Market).filter(Market.id == market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    positions = db.query(Position).filter(Position.market_id == market_id).all()
    return positions

@router.get("/token/{token_id}", response_model=PositionResponse)
async def get_token_position(token_id: str, db: Session = Depends(get_db)):
    """Get position for a specific token"""
    position = db.query(Position).filter(Position.token_id == token_id).first()
    if not position:
        return PositionResponse(
            id=0,
            market_id=0,
            token_id=token_id,
            size=0.0,
            avg_price=0.0,
            side=None,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            created_at=None,
            updated_at=None
        )
    return position

