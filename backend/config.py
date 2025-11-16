"""
Configuration and Environment Settings for Trading Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Global configuration for the trading bot"""
    
    # ==================== TRADING MODE ====================
    DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
    
    # ==================== API CREDENTIALS ====================
    PK = os.getenv('PK', '')
    BROWSER_ADDRESS = os.getenv('BROWSER_ADDRESS', '')
    
    # ==================== DATABASE ====================
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./polymarket_bot.db')
    
    # ==================== SAFETY LIMITS ====================
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '100'))
    MAX_TRADE_SIZE = float(os.getenv('MAX_TRADE_SIZE', '10'))
    MIN_TRADE_SIZE = float(os.getenv('MIN_TRADE_SIZE', '1'))
    
    # ==================== API SETTINGS ====================
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8080')
    
    @classmethod
    def is_dry_run(cls):
        """Check if running in dry run (simulation) mode"""
        return cls.DRY_RUN
    
    @classmethod
    def is_live_trading(cls):
        """Check if running in live trading mode"""
        return not cls.DRY_RUN
    
    @classmethod
    def validate_trade_size(cls, size: float) -> bool:
        """Validate if trade size is within limits"""
        return cls.MIN_TRADE_SIZE <= size <= cls.MAX_TRADE_SIZE
    
    @classmethod
    def validate_position_size(cls, size: float) -> bool:
        """Validate if position size is within limits"""
        return size <= cls.MAX_POSITION_SIZE
    
    @classmethod
    def log_config(cls):
        """Log current configuration (for startup)"""
        mode = "🔵 DRY RUN (Simulation)" if cls.DRY_RUN else "🔴 LIVE TRADING"
        
        print("\n" + "=" * 60)
        print("POLYMARKET TRADING BOT - CONFIGURATION")
        print("=" * 60)
        print(f"Mode:                {mode}")
        print(f"Max Position Size:   ${cls.MAX_POSITION_SIZE}")
        print(f"Max Trade Size:      ${cls.MAX_TRADE_SIZE}")
        print(f"Min Trade Size:      ${cls.MIN_TRADE_SIZE}")
        print(f"Wallet:              {cls.BROWSER_ADDRESS[:10]}..." if cls.BROWSER_ADDRESS else "Not configured")
        print(f"Database:            {cls.DATABASE_URL}")
        print("=" * 60 + "\n")
        
        if cls.DRY_RUN:
            print("⚠️  DRY RUN MODE: No real orders will be placed")
            print("   All trading activity is simulated\n")
        else:
            print("⚠️  LIVE TRADING MODE: Real money at risk!")
            print("   Orders will be placed on Polymarket\n")

# Initialize on import
Config.log_config()

