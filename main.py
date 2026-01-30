import gc                      # Garbage collection
import time                    # Time functions
import asyncio                 # Asynchronous I/O
import traceback               # Exception handling
import threading               # Thread management
import pandas as pd            # Data processing

from poly_data.polymarket_client import PolymarketClient
from poly_data.data_utils import update_positions, update_orders
from poly_data.websocket_handlers import connect_market_websocket, connect_user_websocket
import poly_data.global_state as global_state
from poly_data.data_processing import remove_from_performing
from dotenv import load_dotenv

# Import database models
import os
from backend.database import SessionLocal, Market, init_db

load_dotenv()

# Change to backend directory to access correct database
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

# Initialize database on startup
print("🔧 Initializing database...")
init_db()
print("✅ Database initialized\n")

def load_markets_from_db():
    """
    Load market configuration from database (replaces Google Sheets)
    """
    db = SessionLocal()
    try:
        # Fetch active markets from database
        markets = db.query(Market).filter(Market.is_active == True).all()
        
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
            print("⚠️  WARNING: No active markets found in database!")
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
            token1 = str(row['token1']) if row['token1'] else None
            token2 = str(row['token2']) if row['token2'] else None
            
            # Skip if tokens are missing or invalid
            if not token1 or token1 == 'None' or token1 == 'nan' or not token1.strip():
                print(f"⚠️  Warning: Market '{row['question']}' has invalid token1: {token1}")
                continue
            if not token2 or token2 == 'None' or token2 == 'nan' or not token2.strip():
                print(f"⚠️  Warning: Market '{row['question']}' has invalid token2: {token2}")
                continue
            
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
        
        print(f"✅ Loaded {len(global_state.df)} active markets from database")
        print(f"✅ Subscribing to {len(global_state.all_tokens)} tokens")
        
    except Exception as e:
        print(f"❌ Error loading markets from database: {e}")
        print(traceback.format_exc())
        global_state.df = pd.DataFrame()
        global_state.params = {}
    finally:
        db.close()

def update_once():
    """
    Initialize the application state by fetching market data, positions, and orders.
    """
    load_markets_from_db()  # Get market information from database
    update_positions()      # Get current positions from Polymarket
    update_orders()         # Get current orders from Polymarket

def remove_from_pending():
    """
    Clean up stale trades that have been pending for too long (>15 seconds).
    This prevents the system from getting stuck on trades that may have failed.
    """
    try:
        current_time = time.time()
            
        # Iterate through all performing trades
        for col in list(global_state.performing.keys()):
            for trade_id in list(global_state.performing[col]):
                
                try:
                    # If trade has been pending for more than 15 seconds, remove it
                    if current_time - global_state.performing_timestamps[col].get(trade_id, current_time) > 15:
                        print(f"Removing stale entry {trade_id} from {col} after 15 seconds")
                        remove_from_performing(col, trade_id)
                        print("After removing: ", global_state.performing, global_state.performing_timestamps)
                except:
                    print("Error in remove_from_pending")
                    print(traceback.format_exc())                
    except:
        print("Error in remove_from_pending")
        print(traceback.format_exc())

def update_periodically():
    """
    Background thread function that periodically updates market data, positions and orders.
    - Positions and orders are updated every 5 seconds
    - Market data is updated every 30 seconds (every 6 cycles)
    - Stale pending trades are removed each cycle
    """
    i = 1
    while True:
        time.sleep(5)  # Update every 5 seconds
        
        try:
            # Clean up stale trades
            remove_from_pending()
            
            # Update positions and orders every cycle
            update_positions(avgOnly=True)  # Only update average price, not position size
            update_orders()

            # Update market data every 6th cycle (30 seconds)
            if i % 6 == 0:
                load_markets_from_db()
                i = 1
                    
            gc.collect()  # Force garbage collection to free memory
            i += 1
        except:
            print("Error in update_periodically")
            print(traceback.format_exc())
            
async def main():
    """
    Main application entry point. Initializes client, data, and manages websocket connections.
    """
    # Initialize client
    global_state.client = PolymarketClient()
    
    # Initialize state and fetch initial data
    global_state.all_tokens = []
    update_once()
    print("After initial updates: ", global_state.orders, global_state.positions)

    print("\n")
    print(f'There are {len(global_state.df)} market, {len(global_state.positions)} positions and {len(global_state.orders)} orders. Starting positions: {global_state.positions}')

    # Start background update thread
    update_thread = threading.Thread(target=update_periodically, daemon=True)
    update_thread.start()
    
    # Main loop - maintain websocket connections
    while True:
        try:
            # Connect to market and user websockets simultaneously
            await asyncio.gather(
                connect_market_websocket(global_state.all_tokens), 
                connect_user_websocket()
            )
            print("Reconnecting to the websocket")
        except:
            print("Error in main loop")
            print(traceback.format_exc())
            
        await asyncio.sleep(1)
        gc.collect()  # Clean up memory

if __name__ == "__main__":
    asyncio.run(main())