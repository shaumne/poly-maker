"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class SideToTrade(str, Enum):
    YES = "YES"
    NO = "NO"
    BOTH = "BOTH"

class TradingMode(str, Enum):
    MARKET_MAKING = "MARKET_MAKING"
    POSITION_BUILDING = "POSITION_BUILDING"
    HYBRID = "HYBRID"
    SELL_ONLY = "SELL_ONLY"

class MarketCategory(str, Enum):
    CRYPTO = "crypto"
    OTHER = "other"

# Market schemas
class MarketBase(BaseModel):
    condition_id: str
    question: str
    answer1: str
    answer2: str
    token1: str
    token2: str
    market_slug: Optional[str] = None
    side_to_trade: SideToTrade = SideToTrade.BOTH
    trading_mode: TradingMode = TradingMode.MARKET_MAKING
    target_position: float = 0.0
    is_active: bool = True
    category: MarketCategory = MarketCategory.OTHER
    best_bid: float = 0.0
    best_ask: float = 0.0
    spread: float = 0.0
    neg_risk: str = "FALSE"

class MarketCreate(MarketBase):
    pass

class MarketUpdate(BaseModel):
    question: Optional[str] = None
    side_to_trade: Optional[SideToTrade] = None
    trading_mode: Optional[TradingMode] = None
    target_position: Optional[float] = None
    is_active: Optional[bool] = None
    category: Optional[MarketCategory] = None

class BulkMarketUpdate(BaseModel):
    market_ids: List[int]
    question: Optional[str] = None
    side_to_trade: Optional[SideToTrade] = None
    trading_mode: Optional[TradingMode] = None
    target_position: Optional[float] = None
    is_active: Optional[bool] = None
    category: Optional[MarketCategory] = None

class BulkMarketDelete(BaseModel):
    market_ids: List[int]

class MarketResponse(MarketBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Trading params schemas
class TradingParamsBase(BaseModel):
    trade_size: float = 10.0
    max_size: float = 100.0
    min_size: float = 5.0
    max_spread: float = 5.0
    tick_size: float = 0.01
    multiplier: float = 1.0
    stop_loss_threshold: float = -5.0
    take_profit_threshold: float = 2.0
    volatility_threshold: float = 50.0
    spread_threshold: float = 0.05
    sleep_period: float = 1.0
    order_front_running: bool = True
    tick_improvement: int = 1
    quick_cancel_threshold: float = 0.01
    position_patience: float = 24.0
    param_type: str = "default"

class TradingParamsCreate(TradingParamsBase):
    market_id: int

class TradingParamsUpdate(BaseModel):
    trade_size: Optional[float] = None
    max_size: Optional[float] = None
    min_size: Optional[float] = None
    max_spread: Optional[float] = None
    tick_size: Optional[float] = None
    multiplier: Optional[float] = None
    stop_loss_threshold: Optional[float] = None
    take_profit_threshold: Optional[float] = None
    volatility_threshold: Optional[float] = None
    spread_threshold: Optional[float] = None
    sleep_period: Optional[float] = None
    order_front_running: Optional[bool] = None
    tick_improvement: Optional[int] = None
    quick_cancel_threshold: Optional[float] = None
    position_patience: Optional[float] = None

class TradingParamsResponse(TradingParamsBase):
    id: int
    market_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Position schemas
class PositionResponse(BaseModel):
    id: int
    market_id: int
    token_id: str
    size: float
    avg_price: float
    side: Optional[str]
    unrealized_pnl: float
    realized_pnl: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Order schemas
class OrderResponse(BaseModel):
    id: int
    market_id: int
    order_id: Optional[str]
    token_id: str
    side_type: str
    side: Optional[str]
    price: float
    size: float
    filled_size: float
    status: str
    created_at: datetime
    filled_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Settings schemas
class SettingBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class SettingCreate(SettingBase):
    pass

class SettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None

class SettingResponse(SettingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Trading status schemas
class TradingStatusResponse(BaseModel):
    is_running: bool
    started_at: Optional[datetime]
    stopped_at: Optional[datetime]
    total_pnl: float
    total_trades: int
    active_markets: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Stats schemas
class StatsResponse(BaseModel):
    total_markets: int
    active_markets: int
    total_positions: int
    total_pnl: float
    today_pnl: float
    total_orders: int
    active_orders: int
    usdc_balance: Optional[float] = None
    total_balance: Optional[float] = None
    positions_value: Optional[float] = None

# Wallet schemas
class WalletBalanceResponse(BaseModel):
    usdc_balance: float
    total_balance: Optional[float] = None
    positions_value: Optional[float] = None
    wallet_address: str

# Market with full config
class MarketWithConfig(MarketResponse):
    trading_params: Optional[TradingParamsResponse] = None

