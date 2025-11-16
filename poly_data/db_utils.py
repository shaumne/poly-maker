"""
Database utility functions for bot to access DB
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from sqlalchemy.orm import Session
from database import SessionLocal, Market, TradingParams, Position, Order
import pandas as pd
from typing import Optional, Dict, List

def get_db_session() -> Session:
    """Get a database session"""
    return SessionLocal()

def get_markets_dataframe() -> pd.DataFrame:
    """
    Get active markets as a DataFrame (replacement for Google Sheets)
    Returns DataFrame in the same format as the old get_sheet_df function
    """
    db = get_db_session()
    try:
        markets = db.query(Market).filter(Market.is_active == True).all()
        
        market_data = []
        for market in markets:
            if not market.trading_params:
                continue
            
            params = market.trading_params
            
            market_data.append({
                'condition_id': market.condition_id,
                'question': market.question,
                'answer1': market.answer1,
                'answer2': market.answer2,
                'token1': market.token1,
                'token2': market.token2,
                'market_slug': market.market_slug or '',
                'neg_risk': market.neg_risk,
                'side_to_trade': market.side_to_trade,
                'trading_mode': market.trading_mode,
                'target_position': market.target_position,
                'best_bid': market.best_bid,
                'best_ask': market.best_ask,
                'spread': market.spread,
                # Trading params
                'trade_size': params.trade_size,
                'max_size': params.max_size,
                'min_size': params.min_size,
                'max_spread': params.max_spread,
                'tick_size': params.tick_size,
                'multiplier': params.multiplier if params.multiplier else '',
                'param_type': params.param_type,
                # Add volatility columns with default values
                '1_hour': 0.0,
                '3_hour': 0.0,
                '6_hour': 0.0,
                '12_hour': 0.0,
                '24_hour': 0.0,
                '7_day': 0.0,
                '14_day': 0.0,
                '30_day': 0.0,
            })
        
        df = pd.DataFrame(market_data)
        return df
    finally:
        db.close()

def get_trading_params() -> Dict:
    """
    Get trading parameters grouped by param_type (replacement for Google Sheets hyperparameters)
    """
    db = get_db_session()
    try:
        markets = db.query(Market).filter(Market.is_active == True).all()
        
        params = {}
        for market in markets:
            if not market.trading_params:
                continue
            
            param_type = market.trading_params.param_type
            if param_type not in params:
                tp = market.trading_params
                params[param_type] = {
                    'stop_loss_threshold': tp.stop_loss_threshold,
                    'take_profit_threshold': tp.take_profit_threshold,
                    'volatility_threshold': tp.volatility_threshold,
                    'spread_threshold': tp.spread_threshold,
                    'sleep_period': tp.sleep_period,
                }
        
        return params
    finally:
        db.close()

def update_position_in_db(token_id: str, size: float, avg_price: float, 
                          side: Optional[str] = None, market_id: Optional[int] = None):
    """Update position in database"""
    db = get_db_session()
    try:
        position = db.query(Position).filter(Position.token_id == token_id).first()
        
        if position:
            position.size = size
            position.avg_price = avg_price
            if side:
                position.side = side
        else:
            # Create new position
            position = Position(
                token_id=token_id,
                size=size,
                avg_price=avg_price,
                side=side,
                market_id=market_id or 0
            )
            db.add(position)
        
        db.commit()
    finally:
        db.close()

def update_order_in_db(order_id: str, token_id: str, side_type: str, 
                       price: float, size: float, status: str = 'PENDING',
                       market_id: Optional[int] = None):
    """Update order in database"""
    db = get_db_session()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        
        if order:
            order.status = status
            order.filled_size = size
        else:
            # Create new order
            order = Order(
                order_id=order_id,
                token_id=token_id,
                side_type=side_type,
                price=price,
                size=size,
                status=status,
                market_id=market_id or 0
            )
            db.add(order)
        
        db.commit()
    finally:
        db.close()

