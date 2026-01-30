import asyncio                      # Asynchronous I/O
import json                        # JSON handling
import websockets                  # WebSocket client
import traceback                   # Exception handling

from poly_data.data_processing import process_data, process_user_data
import poly_data.global_state as global_state

async def connect_market_websocket(chunk):
    """
    Connect to Polymarket's market WebSocket API and process market updates.
    
    This function:
    1. Establishes a WebSocket connection to the Polymarket API
    2. Subscribes to updates for a specified list of market tokens
    3. Processes incoming order book and price updates
    
    Args:
        chunk (list): List of token IDs to subscribe to
        
    Notes:
        If the connection is lost, the function will exit and the main loop will
        attempt to reconnect after a short delay.
    """
    from poly_data.api_constants import WSS_MARKET_ENDPOINT
    uri = WSS_MARKET_ENDPOINT
    async with websockets.connect(
        uri, 
        ping_interval=5, 
        ping_timeout=None,
        open_timeout=60,  # Increase connection timeout to 60 seconds
        close_timeout=10
    ) as websocket:
        # Prepare and send subscription message
        # According to docs: Market channel subscription format: {"assets_ids": [...], "type": "market"}
        message = {
            "assets_ids": chunk,
            "type": "market"
        }
        await websocket.send(json.dumps(message))

        print("\n")
        print(f"✅ Sent market subscription message for {len(chunk)} tokens: {chunk[:3]}..." if len(chunk) > 3 else f"✅ Sent market subscription message for {len(chunk)} tokens: {chunk}")
        print(f"📡 Waiting for market data updates...")
        
        # Wait for subscription confirmation
        try:
            first_response = await asyncio.wait_for(websocket.recv(), timeout=10)
            print(f"📬 First WebSocket response: {first_response[:200]}")
        except asyncio.TimeoutError:
            print(f"⚠️  No response from Polymarket within 10 seconds!")
        except Exception as e:
            print(f"⚠️  Error receiving first response: {e}")

        # Start ping task according to docs: send PING every 5 seconds
        async def ping_task():
            while True:
                await asyncio.sleep(5)
                try:
                    await websocket.send("PING")
                except Exception as e:
                    print(f"⚠️  Error sending PING: {e}")
                    break
        
        ping_task_handle = asyncio.create_task(ping_task())

        try:
            # Process incoming market data indefinitely
            message_count = 0
            while True:
                message = await websocket.recv()
                message_count += 1
                
                # Debug log every 10 messages
                if message_count % 10 == 0:
                    print(f"📨 Received {message_count} messages so far...")
                
                # Handle PONG/PING responses (non-JSON messages)
                # PONG mesajları "PONG", "PONG...", b"PONG" gibi farklı formatlarda gelebilir
                message_str = message.decode('utf-8') if isinstance(message, bytes) else str(message)
                if message_str.startswith("PONG") or message_str.startswith("PING"):
                    continue  # Skip PONG/PING messages, they're just keepalive
                
                try:
                    # Try to parse as JSON
                    if isinstance(message, str):
                        json_data = json.loads(message)
                    elif isinstance(message, bytes):
                        json_data = json.loads(message.decode('utf-8'))
                    else:
                        json_data = message
                    
                    # Ensure json_data is a dict or list
                    if isinstance(json_data, (dict, list)):
                        # Process order book updates and trigger trading as needed
                        process_data(json_data)
                    else:
                        print(f"⚠️  Received non-dict/list data from websocket: {type(json_data)}")
                except json.JSONDecodeError as e:
                    # If it's not JSON and not PONG/PING, log it but don't crash
                    if not (message_str.startswith("PONG") or message_str.startswith("PING")):
                        print(f"⚠️  Failed to parse websocket message as JSON: {e}")
                        print(f"   Message: {message_str[:100]}...")
                except Exception as e:
                    print(f"⚠️  Error processing websocket message: {e}")
                    import traceback
                    traceback.print_exc()
        except websockets.ConnectionClosed:
            print("Connection closed in market websocket")
            print(traceback.format_exc())
        except Exception as e:
            print(f"Exception in market websocket: {e}")
            print(traceback.format_exc())
        finally:
            # Cancel ping task
            ping_task_handle.cancel()
            try:
                await ping_task_handle
            except asyncio.CancelledError:
                pass
            # Brief delay before attempting to reconnect
            await asyncio.sleep(5)

async def connect_user_websocket():
    """
    Connect to Polymarket's user WebSocket API and process order/trade updates.
    
    This function:
    1. Establishes a WebSocket connection to the Polymarket user API
    2. Authenticates using API credentials (apiKey, secret, passphrase)
    3. Processes incoming order and trade updates for the user
    
    Notes:
        If the connection is lost, the function will exit and the main loop will
        attempt to reconnect after a short delay.
    """
    from poly_data.api_constants import WSS_USER_ENDPOINT
    uri = WSS_USER_ENDPOINT

    async with websockets.connect(
        uri, 
        ping_interval=5, 
        ping_timeout=None,
        open_timeout=60,  # Increase connection timeout to 60 seconds
        close_timeout=10
    ) as websocket:
        # Validate API credentials before sending
        if not hasattr(global_state, 'client') or not global_state.client:
            print("❌ Error: Client not initialized. Cannot connect to user websocket.")
            return
        
        if not hasattr(global_state.client, 'client') or not global_state.client.client:
            print("❌ Error: ClobClient not initialized. Cannot connect to user websocket.")
            return
        
        if not hasattr(global_state.client.client, 'creds') or not global_state.client.client.creds:
            print("❌ Error: API credentials not set. Cannot connect to user websocket.")
            return
        
        creds = global_state.client.client.creds
        api_key = getattr(creds, 'api_key', None)
        api_secret = getattr(creds, 'api_secret', None)
        api_passphrase = getattr(creds, 'api_passphrase', None)
        
        # Validate credentials according to Polymarket API documentation
        if not api_key or not api_secret or not api_passphrase:
            print("❌ Error: Missing API credentials (apiKey, secret, or passphrase). Cannot connect to user websocket.")
            return
        
        # Prepare authentication message with API credentials
        # According to docs: User channel subscription format: {"markets": [...], "type": "user", "auth": {...}}
        # markets can be empty array if subscribing to all markets
        message = {
            "markets": [],  # Empty array subscribes to all markets for the authenticated user
            "type": "user",
            "auth": {
                "apiKey": api_key, 
                "secret": api_secret,  
                "passphrase": api_passphrase
            }
        }

        # Send authentication message
        await websocket.send(json.dumps(message))

        print("\n")
        print(f"✅ Sent user subscription message with authentication")

        # Start ping task according to docs: send PING every 5 seconds
        async def ping_task():
            while True:
                await asyncio.sleep(5)
                try:
                    await websocket.send("PING")
                except Exception as e:
                    print(f"⚠️  Error sending PING: {e}")
                    break
        
        ping_task_handle = asyncio.create_task(ping_task())

        try:
            # Process incoming user data indefinitely
            while True:
                message = await websocket.recv()
                
                # Handle PONG/PING responses (non-JSON messages)
                # PONG mesajları "PONG", "PONG...", b"PONG" gibi farklı formatlarda gelebilir
                message_str = message.decode('utf-8') if isinstance(message, bytes) else str(message)
                if message_str.startswith("PONG") or message_str.startswith("PING"):
                    continue  # Skip PONG/PING messages, they're just keepalive
                
                # Try to parse as JSON
                try:
                    if isinstance(message, bytes):
                        json_data = json.loads(message.decode('utf-8'))
                    else:
                        json_data = json.loads(message)
                    # Process trade and order updates
                    process_user_data(json_data)
                except json.JSONDecodeError as e:
                    # If it's not JSON and not PONG/PING, log it but don't crash
                    if not (message_str.startswith("PONG") or message_str.startswith("PING")):
                        print(f"⚠️  Failed to parse websocket message as JSON: {e}")
                        print(f"   Message: {message_str[:100]}...")
        except websockets.ConnectionClosed:
            print("Connection closed in user websocket")
            print(traceback.format_exc())
        except Exception as e:
            print(f"Exception in user websocket: {e}")
            print(traceback.format_exc())
        finally:
            # Cancel ping task
            ping_task_handle.cancel()
            try:
                await ping_task_handle
            except asyncio.CancelledError:
                pass
            # Brief delay before attempting to reconnect
            await asyncio.sleep(5)