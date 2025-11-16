"""
FastAPI main application for Polymarket Trading Bot
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dotenv import load_dotenv

from database import get_db, init_db
from api import markets, trading, positions, orders, settings, stats, wallet
from services.trading_service import TradingService
from config import Config

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Polymarket Trading Bot API",
    description="API for managing Polymarket prediction market trading",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    init_db()
    print("✅ Database initialized")

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "online",
        "message": "Polymarket Trading Bot API",
        "version": "1.0.0",
        "mode": "DRY_RUN" if Config.is_dry_run() else "LIVE",
        "max_position_size": Config.MAX_POSITION_SIZE,
        "max_trade_size": Config.MAX_TRADE_SIZE
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Include routers
app.include_router(markets.router, prefix="/api/markets", tags=["markets"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["wallet"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

