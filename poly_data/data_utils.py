import poly_data.global_state as global_state
import time

#sth here seems to be removing the position
def update_positions(avgOnly=False):
    pos_df = global_state.client.get_all_positions()
    
    # Import db_utils here to avoid circular imports
    try:
        from poly_data.db_utils import update_position_in_db
        from poly_data.db_utils import get_db_session
        from backend.database import Market
    except ImportError:
        print("⚠️  Database utilities not available, skipping DB sync")
        update_position_in_db = None
        get_db_session = None

    for idx, row in pos_df.iterrows():
        asset = str(row['asset'])

        if asset in  global_state.positions:
            position = global_state.positions[asset].copy()
        else:
            position = {'size': 0, 'avgPrice': 0}

        position['avgPrice'] = row['avgPrice']

        if not avgOnly:
            position['size'] = row['size']
        else:
            
            for col in [f"{asset}_sell", f"{asset}_buy"]:
                #need to review this
                if col not in global_state.performing or not isinstance(global_state.performing[col], set) or len(global_state.performing[col]) == 0:
                    try:
                        old_size = position['size']
                    except:
                        old_size = 0

                    if asset in  global_state.last_trade_update:
                        if time.time() - global_state.last_trade_update[asset] < 5:
                            print(f"Skipping update for {asset} because last trade update was less than 5 seconds ago")
                            continue

                    if old_size != row['size']:
                        print(f"No trades are pending. Updating position from {old_size} to {row['size']} and avgPrice to {row['avgPrice']} using API")
    
                    position['size'] = row['size']
                else:
                    print(f"ALERT: Skipping update for {asset} because there are trades pending for {col} looking like {global_state.performing[col]}")
    
        global_state.positions[asset] = position
        
        # Sync to database
        if update_position_in_db and position['size'] != 0:
            try:
                # Find market_id from token_id using global_state.df
                market_id = None
                side = None
                
                if global_state.df is not None and not global_state.df.empty:
                    # Check if token matches token1 or token2
                    matching_markets = global_state.df[
                        (global_state.df['token1'].astype(str) == asset) | 
                        (global_state.df['token2'].astype(str) == asset)
                    ]
                    
                    if not matching_markets.empty:
                        # Get first matching market (should be only one per token)
                        market_row = matching_markets.iloc[0]
                        condition_id = market_row['condition_id']
                        
                        # Find market_id from database
                        if get_db_session:
                            db = get_db_session()
                            try:
                                market = db.query(Market).filter(Market.condition_id == condition_id).first()
                                if market:
                                    market_id = market.id
                                    # Determine side based on which token matches
                                    if str(market_row['token1']) == asset:
                                        side = 'YES'
                                    elif str(market_row['token2']) == asset:
                                        side = 'NO'
                            finally:
                                db.close()
                
                # Update position in database
                update_position_in_db(
                    token_id=asset,
                    size=position['size'],
                    avg_price=position['avgPrice'],
                    side=side,
                    market_id=market_id
                )
            except Exception as e:
                print(f"⚠️  Error syncing position to database: {e}")
                import traceback
                traceback.print_exc()

def get_position(token):
    token = str(token)
    if token in global_state.positions:
        return global_state.positions[token]
    else:
        return {'size': 0, 'avgPrice': 0}

def set_position(token, side, size, price, source='websocket'):
    token = str(token)
    size = float(size)
    price = float(price)

    global_state.last_trade_update[token] = time.time()
    
    if side.lower() == 'sell':
        size *= -1

    if token in global_state.positions:
        
        prev_price = global_state.positions[token]['avgPrice']
        prev_size = global_state.positions[token]['size']


        if size > 0:
            if prev_size == 0:
                # Starting a new position
                avgPrice_new = price
            else:
                # Buying more; update average price
                avgPrice_new = (prev_price * prev_size + price * size) / (prev_size + size)
        elif size < 0:
            # Selling; average price remains the same
            avgPrice_new = prev_price
        else:
            # No change in position
            avgPrice_new = prev_price


        global_state.positions[token]['size'] += size
        global_state.positions[token]['avgPrice'] = avgPrice_new
    else:
        global_state.positions[token] = {'size': size, 'avgPrice': price}

    print(f"Updated position from {source}, set to ", global_state.positions[token])

def update_orders():
    all_orders = global_state.client.get_all_orders()

    orders = {}
    
    # Import db_utils here to avoid circular imports
    try:
        from poly_data.db_utils import update_order_in_db
        from poly_data.db_utils import get_db_session
        from backend.database import Market
    except ImportError:
        print("⚠️  Database utilities not available, skipping DB sync")
        update_order_in_db = None
        get_db_session = None

    if len(all_orders) > 0:
            for token in all_orders['asset_id'].unique():
                token_str = str(token)
                
                if token_str not in orders:
                    orders[token_str] = {'buy': {'price': 0, 'size': 0}, 'sell': {'price': 0, 'size': 0}}

                curr_orders = all_orders[all_orders['asset_id'] == token_str]
                
                if len(curr_orders) > 0:
                    sel_orders = {}
                    sel_orders['buy'] = curr_orders[curr_orders['side'] == 'BUY']
                    sel_orders['sell'] = curr_orders[curr_orders['side'] == 'SELL']

                    for type in ['buy', 'sell']:
                        curr = sel_orders[type]

                        if len(curr) > 1:
                            print("Multiple orders found, cancelling")
                            global_state.client.cancel_all_asset(token)
                            orders[token_str] = {'buy': {'price': 0, 'size': 0}, 'sell': {'price': 0, 'size': 0}}
                        elif len(curr) == 1:
                            order_row = curr.iloc[0]
                            orders[token_str][type]['price'] = float(order_row['price'])
                            orders[token_str][type]['size'] = float(order_row['original_size'] - order_row['size_matched'])
                            
                            # Sync order to database
                            if update_order_in_db:
                                try:
                                    # Get order details
                                    order_id = str(order_row.get('id', ''))
                                    side_type = type.upper()  # 'BUY' or 'SELL'
                                    price = float(order_row['price'])
                                    size = float(order_row['original_size'])
                                    filled_size = float(order_row['size_matched'])
                                    
                                    # Determine order status
                                    if filled_size >= size:
                                        status = 'FILLED'
                                    else:
                                        status = 'PENDING'
                                    
                                    # Find market_id from token_id using global_state.df
                                    market_id = None
                                    side = None
                                    
                                    if global_state.df is not None and not global_state.df.empty:
                                        # Check if token matches token1 or token2
                                        matching_markets = global_state.df[
                                            (global_state.df['token1'].astype(str) == token_str) | 
                                            (global_state.df['token2'].astype(str) == token_str)
                                        ]
                                        
                                        if not matching_markets.empty:
                                            # Get first matching market
                                            market_row = matching_markets.iloc[0]
                                            condition_id = market_row['condition_id']
                                            
                                            # Find market_id from database
                                            if get_db_session:
                                                db = get_db_session()
                                                try:
                                                    market = db.query(Market).filter(Market.condition_id == condition_id).first()
                                                    if market:
                                                        market_id = market.id
                                                        # Determine side based on which token matches
                                                        if str(market_row['token1']) == token_str:
                                                            side = 'YES'
                                                        elif str(market_row['token2']) == token_str:
                                                            side = 'NO'
                                                finally:
                                                    db.close()
                                    
                                    # Update order in database
                                    update_order_in_db(
                                        order_id=order_id,
                                        token_id=token_str,
                                        side_type=side_type,
                                        price=price,
                                        size=size,
                                        filled_size=filled_size,
                                        status=status,
                                        market_id=market_id
                                    )
                                except Exception as e:
                                    print(f"⚠️  Error syncing order to database: {e}")
                                    import traceback
                                    traceback.print_exc()

    global_state.orders = orders

def get_order(token):
    token = str(token)
    if token in global_state.orders:

        if 'buy' not in global_state.orders[token]:
            global_state.orders[token]['buy'] = {'price': 0, 'size': 0}

        if 'sell' not in global_state.orders[token]:
            global_state.orders[token]['sell'] = {'price': 0, 'size': 0}

        return global_state.orders[token]
    else:
        return {'buy': {'price': 0, 'size': 0}, 'sell': {'price': 0, 'size': 0}}
    
def set_order(token, side, size, price):
    curr = {}
    curr = {side: {'price': 0, 'size': 0}}

    curr[side]['size'] = float(size)
    curr[side]['price'] = float(price)

    global_state.orders[str(token)] = curr
    print("Updated order, set to ", curr)

    

def update_markets():
    """
    Update markets from database (deprecated - use trading_service._load_markets_from_db instead)
    This function is kept for backward compatibility but should not be used.
    """
    # This function is deprecated - markets are now loaded via trading_service._load_markets_from_db
    # Keeping it for backward compatibility but it does nothing
    pass