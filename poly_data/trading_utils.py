import math 
from poly_data.data_utils import update_positions
import poly_data.global_state as global_state


def validate_order_book_data(market: str) -> dict:
    """
    Validate that order book data exists and is valid for a market.
    
    Args:
        market: Market/condition ID to validate
        
    Returns:
        dict with 'is_valid' bool and 'error' message if invalid
    """
    # Check if market exists in all_data
    if market not in global_state.all_data:
        return {
            'is_valid': False,
            'error': f'Market {market[:20]}... not found in order book data. WebSocket may not have sent data yet.'
        }
    
    market_data = global_state.all_data[market]
    
    # Check if market_data has required fields
    if not isinstance(market_data, dict):
        return {
            'is_valid': False,
            'error': f'Market data for {market[:20]}... is not a valid dictionary'
        }
    
    if 'bids' not in market_data or 'asks' not in market_data:
        return {
            'is_valid': False,
            'error': f'Market {market[:20]}... missing bids or asks data'
        }
    
    # Check if there are any bids and asks
    if len(market_data['bids']) == 0 and len(market_data['asks']) == 0:
        return {
            'is_valid': False,
            'error': f'Market {market[:20]}... has empty order book (no bids or asks)'
        }
    
    return {'is_valid': True, 'error': None}


def validate_price_sanity(best_bid: float, best_ask: float, token_name: str = '') -> dict:
    """
    Validate that prices are within expected bounds for prediction markets.
    
    Args:
        best_bid: Best bid price
        best_ask: Best ask price
        token_name: Name of token for error messages
        
    Returns:
        dict with 'is_valid' bool and 'warning' message if any issues
    """
    warnings = []
    
    # Check for None values
    if best_bid is None or best_ask is None:
        return {
            'is_valid': False,
            'error': f'best_bid or best_ask is None for {token_name}'
        }
    
    # Check price bounds (prediction markets are 0-1)
    if best_bid < 0 or best_bid > 1:
        return {
            'is_valid': False,
            'error': f'best_bid {best_bid} is outside valid range (0-1) for {token_name}'
        }
    
    if best_ask < 0 or best_ask > 1:
        return {
            'is_valid': False,
            'error': f'best_ask {best_ask} is outside valid range (0-1) for {token_name}'
        }
    
    # Check that bid < ask (normal market condition)
    if best_bid >= best_ask:
        warnings.append(f'Inverted market: bid ({best_bid}) >= ask ({best_ask}) for {token_name}')
    
    # Check for extremely wide spreads (more than 50%)
    spread = best_ask - best_bid
    if spread > 0.5:
        warnings.append(f'Very wide spread ({spread:.2%}) for {token_name}')
    
    # Check for extreme prices that might indicate stale data
    if best_bid < 0.001:
        warnings.append(f'Extremely low bid ({best_bid}) for {token_name} - may be stale data')
    
    if best_ask > 0.999:
        warnings.append(f'Extremely high ask ({best_ask}) for {token_name} - may be stale data')
    
    return {
        'is_valid': True,
        'warnings': warnings if warnings else None
    }

# def get_avgPrice(position, assetId):
#     curr_global = global_state.all_positions[global_state.all_positions['asset'] == str(assetId)]
#     api_position_size = 0
#     api_avgPrice = 0

#     if len(curr_global) > 0:
#         c_row = curr_global.iloc[0]
#         api_avgPrice = round(c_row['avgPrice'], 2)
#         api_position_size = c_row['size']

#     if position > 0:
#         if abs((api_position_size - position)/position * 100) > 5:
#             print("Updating global positions")
#             update_positions()

#             try:
#                 c_row = curr_global.iloc[0]
#                 api_avgPrice = round(c_row['avgPrice'], 2)
#                 api_position_size = c_row['size']
#             except:
#                 return 0
#     return api_avgPrice

def get_best_bid_ask_deets(market, name, size, deviation_threshold=0.05):
    """
    Get best bid/ask details from order book for a market.
    
    Args:
        market: Market/condition ID
        name: Token name ('token1' or 'token2')
        size: Minimum size to consider for best price
        deviation_threshold: Threshold for calculating liquidity within range
        
    Returns:
        Dictionary with order book details or None values if data unavailable
    """
    # Validate order book data exists
    validation = validate_order_book_data(market)
    if not validation['is_valid']:
        print(f"⚠️  {validation['error']}")
        # Return dict with all None values
        return {
            'best_bid': None,
            'best_bid_size': None,
            'second_best_bid': None,
            'second_best_bid_size': None,
            'top_bid': None,
            'best_ask': None,
            'best_ask_size': None,
            'second_best_ask': None,
            'second_best_ask_size': None,
            'top_ask': None,
            'bid_sum_within_n_percent': 0,
            'ask_sum_within_n_percent': 0
        }

    best_bid, best_bid_size, second_best_bid, second_best_bid_size, top_bid = find_best_price_with_size(global_state.all_data[market]['bids'], size, reverse=True)
    best_ask, best_ask_size, second_best_ask, second_best_ask_size, top_ask = find_best_price_with_size(global_state.all_data[market]['asks'], size, reverse=False)
    
    # Handle None values in mid_price calculation
    if best_bid is not None and best_ask is not None:
        mid_price = (best_bid + best_ask) / 2
        bid_sum_within_n_percent = sum(size for price, size in global_state.all_data[market]['bids'].items() if best_bid <= price <= mid_price * (1 + deviation_threshold))
        ask_sum_within_n_percent = sum(size for price, size in global_state.all_data[market]['asks'].items() if mid_price * (1 - deviation_threshold) <= price <= best_ask)
    else:
        mid_price = None
        bid_sum_within_n_percent = 0
        ask_sum_within_n_percent = 0

    if name == 'token2':
        # Handle None values before arithmetic operations
        if all(x is not None for x in [best_bid, best_ask, second_best_bid, second_best_ask, top_bid, top_ask]):
            best_bid, second_best_bid, top_bid, best_ask, second_best_ask, top_ask = 1 - best_ask, 1 - second_best_ask, 1 - top_ask, 1 - best_bid, 1 - second_best_bid, 1 - top_bid
            best_bid_size, second_best_bid_size, best_ask_size, second_best_ask_size = best_ask_size, second_best_ask_size, best_bid_size, second_best_bid_size
            bid_sum_within_n_percent, ask_sum_within_n_percent = ask_sum_within_n_percent, bid_sum_within_n_percent
        else:
            # Handle case where some prices are None - use available values or defaults
            if best_bid is not None and best_ask is not None:
                best_bid, best_ask = 1 - best_ask, 1 - best_bid
                best_bid_size, best_ask_size = best_ask_size, best_bid_size
            if second_best_bid is not None:
                second_best_bid = 1 - second_best_bid
            if second_best_ask is not None:
                second_best_ask = 1 - second_best_ask
            if top_bid is not None:
                top_bid = 1 - top_bid
            if top_ask is not None:
                top_ask = 1 - top_ask
            bid_sum_within_n_percent, ask_sum_within_n_percent = ask_sum_within_n_percent, bid_sum_within_n_percent



    #return as dictionary
    return {
        'best_bid': best_bid,
        'best_bid_size': best_bid_size,
        'second_best_bid': second_best_bid,
        'second_best_bid_size': second_best_bid_size,
        'top_bid': top_bid,
        'best_ask': best_ask,
        'best_ask_size': best_ask_size,
        'second_best_ask': second_best_ask,
        'second_best_ask_size': second_best_ask_size,
        'top_ask': top_ask,
        'bid_sum_within_n_percent': bid_sum_within_n_percent,
        'ask_sum_within_n_percent': ask_sum_within_n_percent
    }


def find_best_price_with_size(price_dict, min_size, reverse=False):
    lst = list(price_dict.items())

    if reverse:
        lst.reverse()
    
    best_price, best_size = None, None
    second_best_price, second_best_size = None, None
    top_price = None
    set_best = False

    for price, size in lst:
        if top_price is None:
            top_price = price

        if set_best:
            second_best_price, second_best_size = price, size
            break

        if size > min_size:
            if best_price is None:
                best_price, best_size = price, size
                set_best = True

    return best_price, best_size, second_best_price, second_best_size, top_price

def get_order_prices(best_bid, best_bid_size, top_bid,  best_ask, best_ask_size, top_ask, avgPrice, row):

    bid_price = best_bid + row['tick_size']
    ask_price = best_ask - row['tick_size']

    if best_bid_size < row['min_size'] * 1.5:
        bid_price = best_bid
    
    if best_ask_size < 250 * 1.5:
        ask_price = best_ask
    

    if bid_price >= top_ask:
        bid_price = top_bid

    if ask_price <= top_bid:
        ask_price = top_ask

    if bid_price == ask_price:
        bid_price = top_bid
        ask_price = top_ask

    # if ask_price <= avgPrice:
    #     if avgPrice - ask_price <= (row['max_spread']*1.7/100):
    #         ask_price = avgPrice

    #temp for sleep
    if ask_price <= avgPrice and avgPrice > 0:
        ask_price = avgPrice

    return bid_price, ask_price




def round_down(number, decimals):
    factor = 10 ** decimals
    return math.floor(number * factor) / factor

def round_up(number, decimals):
    factor = 10 ** decimals
    return math.ceil(number * factor) / factor

def get_buy_sell_amount(position, bid_price, row, other_token_position=0):
    buy_amount = 0
    sell_amount = 0

    # Get max_size, defaulting to trade_size if not specified
    max_size = row.get('max_size', row['trade_size'])
    trade_size = row['trade_size']
    target_position = row.get('target_position', 0.0)
    trading_mode = row.get('trading_mode', 'MARKET_MAKING')
    
    # Calculate total exposure across both sides
    total_exposure = position + other_token_position
    
    # ------- MODE 0: SELL_ONLY (De-risking) -------
    if trading_mode == 'SELL_ONLY':
        # Pure exit strategy - only sell existing position
        buy_amount = 0
        if position > 0:
            sell_amount = min(position, trade_size)
        else:
            sell_amount = 0
        
        print(f"Sell Only Mode: position={position}, sell={sell_amount}, no buying")
    
    # ------- MODE 1: POSITION_BUILDING -------
    elif trading_mode == 'POSITION_BUILDING':
        # Only buy until target position is reached
        if position < target_position:
            remaining_to_target = target_position - position
            buy_amount = min(trade_size, remaining_to_target)
            sell_amount = 0  # Don't sell while building position
        else:
            # Target reached, now we can sell
            buy_amount = 0
            sell_amount = min(position, trade_size)
        
        print(f"Position Building Mode: target={target_position}, current={position}, buy={buy_amount}, sell={sell_amount}")
    
    # ------- MODE 2: HYBRID -------
    elif trading_mode == 'HYBRID':
        # Build position first, then switch to market making
        if position < target_position:
            # Still building - focus on buying
            remaining_to_target = target_position - position
            buy_amount = min(trade_size, remaining_to_target)
            # Allow small sells for profit taking even while building
            if position >= trade_size * 0.5:
                sell_amount = min(position * 0.2, trade_size * 0.3)
            else:
                sell_amount = 0
        else:
            # Target reached - switch to normal market making
            remaining_to_max = max_size - position
            if position < max_size:
                buy_amount = min(trade_size, remaining_to_max)
                sell_amount = min(position, trade_size) if position >= trade_size else 0
            else:
                sell_amount = min(position, trade_size)
                if total_exposure < max_size * 2:
                    buy_amount = trade_size
                else:
                    buy_amount = 0
        
        print(f"Hybrid Mode: target={target_position}, current={position}, buy={buy_amount}, sell={sell_amount}")
    
    # ------- MODE 3: MARKET_MAKING (default) -------
    else:
        # Market making logic - always quote both sides
        if position < max_size:
            # Continue quoting trade_size amounts until we reach max_size
            remaining_to_max = max_size - position
            buy_amount = min(trade_size, remaining_to_max)
            
            # SELL size must never exceed position (shares). API rejects "not enough balance" otherwise.
            if position > 0:
                sell_amount = min(position, trade_size)
            else:
                sell_amount = 0  # No position - cannot sell
        else:
            # We've reached max_size, implement progressive exit strategy
            # Always offer to sell trade_size amount when at max_size
            sell_amount = min(position, trade_size)
            
            # Continue quoting to buy if total exposure warrants it
            if total_exposure < max_size * 2:  # Allow some flexibility for market making
                buy_amount = trade_size
            else:
                buy_amount = 0

    # Ensure minimum order size compliance
    if buy_amount > 0.7 * row['min_size'] and buy_amount < row['min_size']:
        buy_amount = row['min_size']

    # Apply multiplier for low-priced assets
    if bid_price < 0.1 and buy_amount > 0:
        if row['multiplier'] != '':
            print(f"Multiplying buy amount by {int(row['multiplier'])}")
            buy_amount = buy_amount * int(row['multiplier'])

    return buy_amount, sell_amount

