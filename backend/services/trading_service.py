"""
Trading service - manages the trading bot execution
"""
import asyncio
import sys
import os

# Add parent directory to path to import from poly_data
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy.orm import Session
from database import Market, TradingStatus
from typing import Optional

class TradingService:
    """Service to manage trading bot lifecycle"""
    
    def __init__(self, db: Session):
        self.db = db
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the trading bot"""
        if self.is_running:
            print("Trading bot is already running")
            return
        
        self.is_running = True
        print("Starting trading bot...")
        
        # Import here to avoid circular dependencies
        from poly_data.polymarket_client import PolymarketClient
        import poly_data.global_state as global_state
        from poly_data.data_utils import update_positions, update_orders
        from poly_data.websocket_handlers import connect_market_websocket, connect_user_websocket
        
        try:
            # Initialize client
            global_state.client = PolymarketClient()
            
            # Load markets from database instead of Google Sheets
            await self._load_markets_from_db()
            
            # Initial data update
            update_positions()
            update_orders()
            
            print(f"Loaded {len(global_state.df)} active markets from database")
            
            # Start trading loop
            while self.is_running:
                try:
                    await asyncio.gather(
                        connect_market_websocket(global_state.all_tokens),
                        connect_user_websocket()
                    )
                except Exception as e:
                    print(f"Error in trading loop: {e}")
                    if not self.is_running:
                        break
                
                await asyncio.sleep(1)
        
        except Exception as e:
            print(f"Error starting trading bot: {e}")
            self.is_running = False
    
    async def stop(self):
        """Stop the trading bot"""
        print("Stopping trading bot...")
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _load_markets_from_db(self):
        """Load market configuration from database"""
        import pandas as pd
        import poly_data.global_state as global_state
        
        # Fetch active markets from database
        markets = self.db.query(Market).filter(Market.is_active == True).all()
        
        # Convert to DataFrame format that the existing code expects
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
                # Risk management
                'stop_loss_threshold': params.stop_loss_threshold,
                'take_profit_threshold': params.take_profit_threshold,
                'volatility_threshold': params.volatility_threshold,
                'spread_threshold': params.spread_threshold,
                'sleep_period': params.sleep_period,
                # Competitive bot params
                'order_front_running': params.order_front_running,
                'tick_improvement': params.tick_improvement,
                'quick_cancel_threshold': params.quick_cancel_threshold,
                'position_patience': params.position_patience,
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
        
        if not market_data:
            global_state.df = pd.DataFrame()
            global_state.params = {}
            return
        
        global_state.df = pd.DataFrame(market_data)
        
        # Group parameters by param_type
        global_state.params = {}
        for market in markets:
            if not market.trading_params:
                continue
            
            param_type = market.trading_params.param_type
            if param_type not in global_state.params:
                params = market.trading_params
                global_state.params[param_type] = {
                    'stop_loss_threshold': params.stop_loss_threshold,
                    'take_profit_threshold': params.take_profit_threshold,
                    'volatility_threshold': params.volatility_threshold,
                    'spread_threshold': params.spread_threshold,
                    'sleep_period': params.sleep_period,
                }
        
        # Set up token tracking
        global_state.all_tokens = []
        global_state.REVERSE_TOKENS = {}
        
        for _, row in global_state.df.iterrows():
            token1 = str(row['token1'])
            token2 = str(row['token2'])
            
            if token1 not in global_state.all_tokens:
                global_state.all_tokens.append(token1)
            if token2 not in global_state.all_tokens:
                global_state.all_tokens.append(token2)
            
            global_state.REVERSE_TOKENS[token1] = token2
            global_state.REVERSE_TOKENS[token2] = token1
            
            # Initialize performing tracking
            for col in [f"{token1}_buy", f"{token1}_sell", f"{token2}_buy", f"{token2}_sell"]:
                if col not in global_state.performing:
                    global_state.performing[col] = set()

