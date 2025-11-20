"""
Polymarket API Constants

This module contains constants for Polymarket API endpoints, error codes, and rate limits
according to the official Polymarket API documentation.
"""

# API Endpoints
# Source: https://docs.polymarket.com/developers/CLOB/endpoints
CLOB_ENDPOINT = "https://clob.polymarket.com"  # REST endpoint for all CLOB REST endpoints
DATA_API_ENDPOINT = "https://data-api.polymarket.com"  # Data-API endpoint for user data, holdings, and on-chain activities
WSS_MARKET_ENDPOINT = "wss://ws-subscriptions-clob.polymarket.com/ws/market"  # WebSocket endpoint for market channel
WSS_USER_ENDPOINT = "wss://ws-subscriptions-clob.polymarket.com/ws/user"  # WebSocket endpoint for user channel
RTDS_ENDPOINT = "wss://ws-live-data.polymarket.com"  # Real-Time Data Socket endpoint for crypto prices and comments
RELAYER_ENDPOINT = "https://relayer-v2.polymarket.com/"  # Relayer endpoint for gasless transactions

# API Rate Limits (requests per time window)
# Source: https://docs.polymarket.com/quickstart/introduction/rate-limits

# General Rate Limits
GENERAL_RATE_LIMIT = {"requests": 5000, "window_seconds": 10}
OK_ENDPOINT_RATE_LIMIT = {"requests": 50, "window_seconds": 10}

# CLOB API Rate Limits
CLOB_GENERAL_RATE_LIMIT = {"requests": 5000, "window_seconds": 10}
CLOB_GET_BALANCE_ALLOWANCE_RATE_LIMIT = {"requests": 125, "window_seconds": 10}
CLOB_UPDATE_BALANCE_ALLOWANCE_RATE_LIMIT = {"requests": 20, "window_seconds": 10}

# CLOB Market Data Rate Limits
CLOB_BOOK_RATE_LIMIT = {"requests": 200, "window_seconds": 10}
CLOB_BOOKS_RATE_LIMIT = {"requests": 80, "window_seconds": 10}
CLOB_PRICE_RATE_LIMIT = {"requests": 200, "window_seconds": 10}
CLOB_PRICES_RATE_LIMIT = {"requests": 80, "window_seconds": 10}
CLOB_MIDPRICE_RATE_LIMIT = {"requests": 200, "window_seconds": 10}
CLOB_MIDPRICES_RATE_LIMIT = {"requests": 80, "window_seconds": 10}

# CLOB Ledger Endpoints Rate Limits
CLOB_LEDGER_RATE_LIMIT = {"requests": 300, "window_seconds": 10}
CLOB_DATA_ORDERS_RATE_LIMIT = {"requests": 150, "window_seconds": 10}
CLOB_DATA_TRADES_RATE_LIMIT = {"requests": 150, "window_seconds": 10}
CLOB_NOTIFICATIONS_RATE_LIMIT = {"requests": 125, "window_seconds": 10}

# CLOB Markets & Pricing Rate Limits
CLOB_PRICE_HISTORY_RATE_LIMIT = {"requests": 100, "window_seconds": 10}
CLOB_MARKETS_RATE_LIMIT = {"requests": 250, "window_seconds": 10}
CLOB_MARKET_TICK_SIZE_RATE_LIMIT = {"requests": 50, "window_seconds": 10}
CLOB_MARKETS_0X_RATE_LIMIT = {"requests": 50, "window_seconds": 10}
CLOB_MARKETS_LISTING_RATE_LIMIT = {"requests": 100, "window_seconds": 10}

# CLOB Authentication Rate Limits
CLOB_API_KEYS_RATE_LIMIT = {"requests": 50, "window_seconds": 10}

# CLOB Trading Endpoints Rate Limits
CLOB_POST_ORDER_BURST = {"requests": 2400, "window_seconds": 10}  # 240/s burst
CLOB_POST_ORDER_SUSTAINED = {"requests": 24000, "window_seconds": 600}  # 40/s sustained
CLOB_DELETE_ORDER_BURST = {"requests": 2400, "window_seconds": 10}  # 240/s burst
CLOB_DELETE_ORDER_SUSTAINED = {"requests": 24000, "window_seconds": 600}  # 40/s sustained
CLOB_POST_ORDERS_BURST = {"requests": 800, "window_seconds": 10}  # 80/s burst
CLOB_POST_ORDERS_SUSTAINED = {"requests": 12000, "window_seconds": 600}  # 20/s sustained
CLOB_DELETE_ORDERS_BURST = {"requests": 800, "window_seconds": 10}  # 80/s burst
CLOB_DELETE_ORDERS_SUSTAINED = {"requests": 12000, "window_seconds": 600}  # 20/s sustained
CLOB_DELETE_CANCEL_ALL_BURST = {"requests": 200, "window_seconds": 10}  # 20/s burst
CLOB_DELETE_CANCEL_ALL_SUSTAINED = {"requests": 3000, "window_seconds": 600}  # 5/s sustained
CLOB_DELETE_CANCEL_MARKET_ORDERS_BURST = {"requests": 800, "window_seconds": 10}  # 80/s burst
CLOB_DELETE_CANCEL_MARKET_ORDERS_SUSTAINED = {"requests": 12000, "window_seconds": 600}  # 20/s sustained

# Data API Rate Limits
DATA_API_GENERAL_RATE_LIMIT = {"requests": 200, "window_seconds": 10}
DATA_API_ALTERNATIVE_RATE_LIMIT = {"requests": 1200, "window_seconds": 60}  # 10 min block on violation
DATA_API_TRADES_RATE_LIMIT = {"requests": 75, "window_seconds": 10}
DATA_API_OK_ENDPOINT_RATE_LIMIT = {"requests": 10, "window_seconds": 10}

# GAMMA API Rate Limits
GAMMA_GENERAL_RATE_LIMIT = {"requests": 750, "window_seconds": 10}
GAMMA_GET_COMMENTS_RATE_LIMIT = {"requests": 100, "window_seconds": 10}
GAMMA_EVENTS_RATE_LIMIT = {"requests": 100, "window_seconds": 10}
GAMMA_MARKETS_RATE_LIMIT = {"requests": 125, "window_seconds": 10}
GAMMA_MARKETS_EVENTS_LISTING_RATE_LIMIT = {"requests": 100, "window_seconds": 10}
GAMMA_TAGS_RATE_LIMIT = {"requests": 100, "window_seconds": 10}
GAMMA_SEARCH_RATE_LIMIT = {"requests": 300, "window_seconds": 10}

# Error Codes (from Place Single Order documentation)
# Source: https://docs.polymarket.com/developers/CLOB/orders/create-order
INVALID_ORDER_MIN_TICK_SIZE = "INVALID_ORDER_MIN_TICK_SIZE"
INVALID_ORDER_MIN_SIZE = "INVALID_ORDER_MIN_SIZE"
INVALID_ORDER_DUPLICATED = "INVALID_ORDER_DUPLICATED"
INVALID_ORDER_NOT_ENOUGH_BALANCE = "INVALID_ORDER_NOT_ENOUGH_BALANCE"
INVALID_ORDER_EXPIRATION = "INVALID_ORDER_EXPIRATION"
INVALID_ORDER_ERROR = "INVALID_ORDER_ERROR"
EXECUTION_ERROR = "EXECUTION_ERROR"
ORDER_DELAYED = "ORDER_DELAYED"
DELAYING_ORDER_ERROR = "DELAYING_ORDER_ERROR"
FOK_ORDER_NOT_FILLED_ERROR = "FOK_ORDER_NOT_FILLED_ERROR"
MARKET_NOT_READY = "MARKET_NOT_READY"

# Error Code Descriptions
ERROR_CODE_DESCRIPTIONS = {
    INVALID_ORDER_MIN_TICK_SIZE: "Order price breaks minimum tick size rules",
    INVALID_ORDER_MIN_SIZE: "Order size lower than the minimum",
    INVALID_ORDER_DUPLICATED: "Same order has already been placed",
    INVALID_ORDER_NOT_ENOUGH_BALANCE: "Not enough balance or allowance",
    INVALID_ORDER_EXPIRATION: "Invalid expiration (expiration before now)",
    INVALID_ORDER_ERROR: "Could not insert order (system error)",
    EXECUTION_ERROR: "Could not run the execution (system error)",
    ORDER_DELAYED: "Order match delayed due to market conditions",
    DELAYING_ORDER_ERROR: "Error delaying the order (system error)",
    FOK_ORDER_NOT_FILLED_ERROR: "FOK order could not be fully filled",
    MARKET_NOT_READY: "Market is not yet ready to process new orders"
}

# Order Status Values (from Place Single Order documentation)
ORDER_STATUS_MATCHED = "matched"  # Order placed and matched with existing resting order
ORDER_STATUS_LIVE = "live"  # Order placed and resting on the book
ORDER_STATUS_DELAYED = "delayed"  # Order marketable, but subject to matching delay
ORDER_STATUS_UNMATCHED = "unmatched"  # Order marketable, but failure delaying, placement successful

# Trade Status Values (from User Channel documentation)
TRADE_STATUS_MATCHED = "MATCHED"
TRADE_STATUS_MINED = "MINED"
TRADE_STATUS_CONFIRMED = "CONFIRMED"
TRADE_STATUS_RETRYING = "RETRYING"
TRADE_STATUS_FAILED = "FAILED"

# Order Type Values (from User Channel documentation)
ORDER_TYPE_PLACEMENT = "PLACEMENT"
ORDER_TYPE_UPDATE = "UPDATE"
ORDER_TYPE_CANCELLATION = "CANCELLATION"

# WebSocket Event Types
WS_EVENT_TYPE_BOOK = "book"
WS_EVENT_TYPE_PRICE_CHANGE = "price_change"
WS_EVENT_TYPE_TICK_SIZE_CHANGE = "tick_size_change"
WS_EVENT_TYPE_LAST_TRADE_PRICE = "last_trade_price"
WS_EVENT_TYPE_TRADE = "trade"
WS_EVENT_TYPE_ORDER = "order"

# Polygon Chain ID
POLYGON_CHAIN_ID = 137

# Contract Addresses (Polygon Mainnet)
# Source: https://docs.polymarket.com/developers/relayer/relayer-client
USDC_CONTRACT_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # USDC token contract
CONDITIONAL_TOKENS_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"  # CTF (Conditional Token Framework) contract
CTF_EXCHANGE_ADDRESS = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"  # CTF Exchange contract
NEG_RISK_CTF_EXCHANGE_ADDRESS = "0xC5d563A36AE78145C45a50134d48A1215220f80a"  # Neg Risk CTF Exchange contract
NEG_RISK_ADAPTER_ADDRESS = "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"  # Neg Risk Adapter contract

# Proxy Wallet Factory Addresses (Polygon Mainnet)
# Source: https://docs.polymarket.com/developers/CLOB/proxy-wallet
GNOSIS_SAFE_FACTORY_ADDRESS = "0xaacfeea03eb1561c4e67d661e40682bd20e3541b"  # Gnosis Safe factory (for MetaMask users)
POLYMARKET_PROXY_FACTORY_ADDRESS = "0xaB45c54AB0c941a2F231C04C3f49182e1A254052"  # Polymarket proxy factory (for MagicLink users)

