import json
from sortedcontainers import SortedDict
import poly_data.global_state as global_state
import poly_data.CONSTANTS as CONSTANTS

from trading import perform_trade
import time 
import asyncio
from poly_data.data_utils import set_position, set_order, update_positions

def process_book_data(asset, json_data):
    global_state.all_data[asset] = {
        'asset_id': json_data['asset_id'],  # token_id for the Yes token
        'bids': SortedDict(),
        'asks': SortedDict()
    }

    global_state.all_data[asset]['bids'].update({float(entry['price']): float(entry['size']) for entry in json_data['bids']})
    global_state.all_data[asset]['asks'].update({float(entry['price']): float(entry['size']) for entry in json_data['asks']})

def process_price_change(asset, side, price_level, new_size, asset_id=None):
    # Skip if asset not in all_data
    if asset not in global_state.all_data:
        return
    
    # Skip updates for the No token to prevent duplicated updates (if asset_id provided)
    if asset_id and asset_id != global_state.all_data[asset].get('asset_id'):
        return
    
    if side == 'bids':
        book = global_state.all_data[asset]['bids']
    else:
        book = global_state.all_data[asset]['asks']

    if new_size == 0:
        if price_level in book:
            del book[price_level]
    else:
        book[price_level] = new_size

def process_data(json_datas, trade=True):
    """
    Process WebSocket messages from Polymarket Market Channel.
    
    According to Polymarket API documentation, supports:
    - book: Full order book snapshot
    - price_change: Price level updates
    - tick_size_change: Minimum tick size changes
    - last_trade_price: Trade execution events
    
    Args:
        json_datas: Message data (str, dict, or list)
        trade: Whether to trigger trading logic on updates
    """
    # Handle different input types
    if isinstance(json_datas, str):
        # If it's a string, try to parse it
        try:
            import json
            json_datas = json.loads(json_datas)
        except:
            print(f"⚠️  Failed to parse string data: {json_datas[:100]}")
            return
    
    # Ensure json_datas is a list
    if isinstance(json_datas, dict):
        json_datas = [json_datas]
    elif not isinstance(json_datas, list):
        print(f"⚠️  Unexpected data type in process_data: {type(json_datas)}")
        return

    for json_data in json_datas:
        # Skip if json_data is not a dict
        if not isinstance(json_data, dict):
            print(f"⚠️  Skipping non-dict data in process_data: {type(json_data)}")
            continue
            
        event_type = json_data.get('event_type', 'unknown')
        asset = json_data.get('market', 'unknown')

        # Handle 'book' event - Full order book snapshot
        # Docs: event_type, asset_id, market, bids, asks, timestamp, hash
        if event_type == 'book':
            # Validate required fields according to docs
            if 'asset_id' not in json_data or 'bids' not in json_data or 'asks' not in json_data:
                print(f"⚠️  Invalid book message format: missing required fields")
                continue
                
            process_book_data(asset, json_data)
            
            # Validate that order book has meaningful data before trading
            bids_count = len(json_data.get('bids', []))
            asks_count = len(json_data.get('asks', []))
            print(f"📊 Received book update for market: {asset} (bids: {bids_count}, asks: {asks_count})")
            
            # Only trigger trade if order book has both bids and asks
            if trade:
                if bids_count > 0 and asks_count > 0:
                    print(f"🔄 Triggering perform_trade for market: {asset}")
                    asyncio.create_task(perform_trade(asset))
                else:
                    print(f"⏳ Skipping trade for {asset}: order book incomplete (bids: {bids_count}, asks: {asks_count})")
                
        # Handle 'price_change' event - Price level updates
        # Docs (updated Sept 15, 2025): event_type, market, price_changes[], timestamp
        # Each price_change has: asset_id, price, size, side, hash, best_bid, best_ask
        elif event_type == 'price_change':
            price_changes = json_data.get('price_changes', [])
            if not isinstance(price_changes, list):
                print(f"⚠️  Invalid price_change message: price_changes is not a list")
                continue
            
            timestamp = json_data.get('timestamp', 'unknown')
            print(f"💰 Price change event for market {asset} at {timestamp}")
                
            for data in price_changes:
                # Validate price_change structure according to docs
                required_fields = ['side', 'price', 'size', 'asset_id']
                if not isinstance(data, dict) or not all(field in data for field in required_fields):
                    print(f"⚠️  Invalid price_change entry: missing required fields. Expected: {required_fields}")
                    continue
                
                asset_id = data.get('asset_id')
                side = 'bids' if data['side'] == 'BUY' else 'asks'
                hash_value = data.get('hash', 'N/A')
                best_bid = data.get('best_bid', 'N/A')
                best_ask = data.get('best_ask', 'N/A')
                
                try:
                    price_level = float(data['price'])
                    new_size = float(data['size'])
                except (ValueError, TypeError):
                    print(f"⚠️  Invalid price_change entry: invalid price or size")
                    continue
                
                # Process price change with asset_id for proper filtering
                process_price_change(asset, side, price_level, new_size, asset_id=asset_id)
                
                # Log best bid/ask if available
                if best_bid != 'N/A' and best_ask != 'N/A':
                    print(f"   Asset {asset_id[:20]}...: {side} {new_size} @ {price_level}, best_bid={best_bid}, best_ask={best_ask}")

            if trade:
                # Validate order book has data before triggering trade
                if asset in global_state.all_data:
                    market_data = global_state.all_data[asset]
                    has_bids = len(market_data.get('bids', {})) > 0
                    has_asks = len(market_data.get('asks', {})) > 0
                    
                    if has_bids and has_asks:
                        print(f"💰 Price change detected for {asset}, triggering perform_trade")
                        asyncio.create_task(perform_trade(asset))
                    else:
                        print(f"⏳ Price change for {asset} but order book incomplete, waiting for full book data")
                else:
                    print(f"⏳ Price change for {asset} but no order book data yet, waiting...")
        
        # Handle 'tick_size_change' event - Minimum tick size changes
        # Docs: event_type, asset_id, market, old_tick_size, new_tick_size, side, timestamp
        # This happens when price > 0.96 or price < 0.04
        elif event_type == 'tick_size_change':
            # Validate required fields according to docs
            required_fields = ['asset_id', 'old_tick_size', 'new_tick_size', 'side', 'timestamp']
            if not all(field in json_data for field in required_fields):
                print(f"⚠️  Invalid tick_size_change message: missing required fields. Expected: {required_fields}")
                continue
            
            asset_id = json_data.get('asset_id')
            old_tick_size = json_data.get('old_tick_size')
            new_tick_size = json_data.get('new_tick_size')
            side = json_data.get('side')
            timestamp = json_data.get('timestamp')
            
            print(f"📏 Tick size change for {asset} (asset: {asset_id[:20]}...): {old_tick_size} -> {new_tick_size} ({side}) at {timestamp}")
            # Note: Trading logic may need to adjust based on tick size changes
            # When tick size changes, existing orders may need to be adjusted
        
        # Handle 'last_trade_price' event - Trade execution events
        # Docs: asset_id, event_type, fee_rate_bps, market, price, side, size, timestamp
        # Emitted when a maker and taker order is matched creating a trade event
        elif event_type == 'last_trade_price':
            # Validate required fields according to docs
            required_fields = ['asset_id', 'market', 'price', 'side', 'size', 'timestamp']
            if not all(field in json_data for field in required_fields):
                print(f"⚠️  Invalid last_trade_price message: missing required fields. Expected: {required_fields}")
                continue
            
            asset_id = json_data.get('asset_id')
            price = json_data.get('price')
            size = json_data.get('size')
            side = json_data.get('side')
            timestamp = json_data.get('timestamp')
            fee_rate_bps = json_data.get('fee_rate_bps', 'N/A')
            
            print(f"💵 Last trade for {asset} (asset: {asset_id[:20]}...): {side} {size} @ {price} (fee: {fee_rate_bps}bps) at {timestamp}")
            # Note: This is informational, trading logic may use this for analysis
        

        # pretty_print(f'Received book update for {asset}:', global_state.all_data[asset])

def add_to_performing(col, id):
    if col not in global_state.performing:
        global_state.performing[col] = set()
    
    if col not in global_state.performing_timestamps:
        global_state.performing_timestamps[col] = {}

    # Add the trade ID and track its timestamp
    global_state.performing[col].add(id)
    global_state.performing_timestamps[col][id] = time.time()

def remove_from_performing(col, id):
    if col in global_state.performing:
        global_state.performing[col].discard(id)

    if col in global_state.performing_timestamps:
        global_state.performing_timestamps[col].pop(id, None)

def process_user_data(rows):
    """
    Process WebSocket messages from Polymarket User Channel.
    
    According to Polymarket API documentation, supports:
    - trade: Trade execution events (MATCHED, MINED, CONFIRMED, RETRYING, FAILED)
    - order: Order events (PLACEMENT, UPDATE, CANCELLATION)
    
    Args:
        rows: Message data (list of dicts or single dict)
    """
    # Ensure rows is a list
    if isinstance(rows, dict):
        rows = [rows]
    elif not isinstance(rows, list):
        print(f"⚠️  Unexpected data type in process_user_data: {type(rows)}")
        return

    for row in rows:
        # Validate row is a dict
        if not isinstance(row, dict):
            print(f"⚠️  Skipping non-dict data in process_user_data: {type(row)}")
            continue
        
        # Validate required fields
        if 'event_type' not in row:
            print(f"⚠️  Invalid user message: missing event_type")
            continue
        
        if 'market' not in row:
            print(f"⚠️  Invalid user message: missing market")
            continue
        
        market = row['market']
        event_type = row.get('event_type', 'unknown')

        # Handle 'trade' event
        # Docs: event_type, id, status, side, size, price, maker_orders[], market, outcome, asset_id, 
        #       last_update, matchtime, owner, trade_owner, taker_order_id, timestamp, type
        if event_type == 'trade':
            # Validate required fields for trade event according to docs
            required_fields = ['id', 'asset_id', 'status', 'side', 'size', 'price', 'market', 'outcome', 
                             'maker_orders', 'timestamp', 'type']
            missing_fields = [field for field in required_fields if field not in row]
            if missing_fields:
                print(f"⚠️  Invalid trade message: missing required fields: {missing_fields}")
                continue
            
            # Validate status is one of the expected values
            valid_statuses = ['MATCHED', 'MINED', 'CONFIRMED', 'RETRYING', 'FAILED']
            if row['status'] not in valid_statuses:
                print(f"⚠️  Invalid trade status: {row['status']}. Expected one of: {valid_statuses}")
            
            # Validate maker_orders is a list
            if not isinstance(row.get('maker_orders'), list):
                print(f"⚠️  Invalid trade message: maker_orders must be a list")
                continue
            
            side = row['side'].lower()
            token = row['asset_id']
            
            if token in global_state.REVERSE_TOKENS:     
                col = token + "_" + side
                size = 0
                price = 0
                maker_outcome = ""
                taker_outcome = row['outcome']

                is_user_maker = False
                for maker_order in row['maker_orders']:
                    if maker_order['maker_address'].lower() == global_state.client.browser_wallet.lower():
                        print("User is maker")
                        size = float(maker_order['matched_amount'])
                        price = float(maker_order['price'])
                        
                        is_user_maker = True
                        maker_outcome = maker_order['outcome'] #this is curious

                        if maker_outcome == taker_outcome:
                            side = 'buy' if side == 'sell' else 'sell' #need to reverse as we reverse token too
                        else:
                            token = global_state.REVERSE_TOKENS[token]
                
                if not is_user_maker:
                    size = float(row['size'])
                    price = float(row['price'])
                    print("User is taker")

                print("TRADE EVENT FOR: ", row['market'], "ID: ", row['id'], "STATUS: ", row['status'], " SIDE: ", row['side'], "  MAKER OUTCOME: ", maker_outcome, " TAKER OUTCOME: ", taker_outcome, " PROCESSED SIDE: ", side, " SIZE: ", size) 


                if row['status'] == 'CONFIRMED' or row['status'] == 'FAILED' :
                    if row['status'] == 'FAILED':
                        print(f"Trade failed for {token}, decreasing")
                        asyncio.create_task(asyncio.sleep(2))
                        update_positions()
                    else:
                        remove_from_performing(col, row['id'])
                        print("Confirmed. Performing is ", len(global_state.performing[col]))
                        print("Last trade update is ", global_state.last_trade_update)
                        print("Performing is ", global_state.performing)
                        print("Performing timestamps is ", global_state.performing_timestamps)
                        
                        asyncio.create_task(perform_trade(market))

                elif row['status'] == 'MATCHED':
                    add_to_performing(col, row['id'])

                    print("Matched. Performing is ", len(global_state.performing[col]))
                    set_position(token, side, size, price)
                    print("Position after matching is ", global_state.positions[str(token)])
                    print("Last trade update is ", global_state.last_trade_update)
                    print("Performing is ", global_state.performing)
                    print("Performing timestamps is ", global_state.performing_timestamps)
                    asyncio.create_task(perform_trade(market))
                elif row['status'] == 'MINED':
                    remove_from_performing(col, row['id'])

        # Handle 'order' event
        # Docs: event_type, id, type (PLACEMENT/UPDATE/CANCELLATION), status, side, asset_id, 
        #       original_size, size_matched, price, market, outcome, order_owner, owner, 
        #       associate_trades[], timestamp
        elif event_type == 'order':
            # Validate required fields for order event according to docs
            required_fields = ['id', 'type', 'asset_id', 'market', 'original_size', 'size_matched', 
                             'price', 'side', 'timestamp']
            missing_fields = [field for field in required_fields if field not in row]
            if missing_fields:
                print(f"⚠️  Invalid order message: missing required fields: {missing_fields}")
                continue
            
            order_type = row.get('type')  # PLACEMENT, UPDATE, or CANCELLATION
            token = row['asset_id']
            
            # Validate order type according to docs
            valid_order_types = ['PLACEMENT', 'UPDATE', 'CANCELLATION']
            if order_type not in valid_order_types:
                print(f"⚠️  Unknown order type: {order_type}. Expected one of: {valid_order_types}")
                continue
            
            if 'side' in row:
                side = row['side'].lower()
            else:
                side = 'unknown'
            
            # Validate numeric fields
            try:
                original_size = float(row.get('original_size', 0))
                size_matched = float(row.get('size_matched', 0))
                price = float(row.get('price', 0)) if row.get('price') else 0
            except (ValueError, TypeError):
                print(f"⚠️  Invalid order message: invalid numeric fields")
                continue
            
            print(f"📋 ORDER EVENT: market={row['market']}, type={order_type}, status={row.get('status', 'N/A')}, side={side}, size={original_size}, matched={size_matched}")
            
            if token in global_state.REVERSE_TOKENS:
                set_order(token, side, original_size - size_matched, price)
                asyncio.create_task(perform_trade(market))
            else:
                print(f"⚠️  User data received for {market} but token {token} is not in REVERSE_TOKENS")
        
        else:
            print(f"⚠️  Unknown event type in user channel: {event_type}")
