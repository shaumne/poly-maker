"""
Database models and configuration for Polymarket Trading Bot
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Market(Base):
    """Market configuration table"""
    __tablename__ = 'markets'
    
    id = Column(Integer, primary_key=True, index=True)
    condition_id = Column(String, unique=True, index=True, nullable=False)
    question = Column(Text, nullable=False)
    answer1 = Column(String, nullable=False)
    answer2 = Column(String, nullable=False)
    token1 = Column(String, nullable=False)
    token2 = Column(String, nullable=False)
    market_slug = Column(String)
    
    # Trading configuration
    side_to_trade = Column(String, default='BOTH')  # YES, NO, BOTH
    trading_mode = Column(String, default='MARKET_MAKING')  # MARKET_MAKING, POSITION_BUILDING, HYBRID
    target_position = Column(Float, default=0.0)  # For position building mode
    is_active = Column(Boolean, default=True)
    category = Column(String, default='other')  # crypto, other
    
    # Market data
    best_bid = Column(Float, default=0.0)
    best_ask = Column(Float, default=0.0)
    spread = Column(Float, default=0.0)
    neg_risk = Column(String, default='FALSE')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trading_params = relationship("TradingParams", back_populates="market", uselist=False, cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="market", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="market", cascade="all, delete-orphan")


class TradingParams(Base):
    """Trading parameters for each market"""
    __tablename__ = 'trading_params'
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey('markets.id'), unique=True, nullable=False)
    
    # Size parameters
    trade_size = Column(Float, default=10.0)
    max_size = Column(Float, default=100.0)
    min_size = Column(Float, default=5.0)
    
    # Market parameters
    max_spread = Column(Float, default=5.0)  # percentage
    tick_size = Column(Float, default=0.01)
    multiplier = Column(Float, default=1.0)
    
    # Risk management
    stop_loss_threshold = Column(Float, default=-5.0)  # percentage
    take_profit_threshold = Column(Float, default=2.0)  # percentage
    volatility_threshold = Column(Float, default=50.0)
    spread_threshold = Column(Float, default=0.05)
    sleep_period = Column(Float, default=1.0)  # hours
    
    # Competitive bot parameters
    order_front_running = Column(Boolean, default=True)
    tick_improvement = Column(Integer, default=1)  # How many ticks to improve price
    quick_cancel_threshold = Column(Float, default=0.01)
    position_patience = Column(Float, default=24.0)  # hours - hold position longer
    
    # Parameter type for different market types
    param_type = Column(String, default='default')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    market = relationship("Market", back_populates="trading_params")


class Position(Base):
    """Position tracking table"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey('markets.id'), nullable=False)
    token_id = Column(String, nullable=False, index=True)
    
    # Position data
    size = Column(Float, default=0.0)
    avg_price = Column(Float, default=0.0)
    side = Column(String)  # YES or NO
    
    # PnL tracking
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    market = relationship("Market", back_populates="positions")


class Order(Base):
    """Order history and active orders table"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, index=True)
    market_id = Column(Integer, ForeignKey('markets.id'), nullable=False)
    
    # Order details
    order_id = Column(String, index=True)  # Polymarket order ID
    token_id = Column(String, nullable=False)
    side_type = Column(String, nullable=False)  # BUY or SELL
    side = Column(String)  # YES or NO
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)
    filled_size = Column(Float, default=0.0)
    status = Column(String, default='PENDING')  # PENDING, FILLED, CANCELLED
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime, nullable=True)
    
    # Relationships
    market = relationship("Market", back_populates="orders")


class GlobalSettings(Base):
    """Global configuration settings"""
    __tablename__ = 'global_settings'
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradingStatus(Base):
    """Trading bot status"""
    __tablename__ = 'trading_status'
    
    id = Column(Integer, primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
    total_pnl = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    active_markets = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database engine and session
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./polymarket_bot.db')
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Initialize trading status
    db = SessionLocal()
    try:
        status = db.query(TradingStatus).first()
        if not status:
            status = TradingStatus(is_running=False)
            db.add(status)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Database initialized successfully!")

