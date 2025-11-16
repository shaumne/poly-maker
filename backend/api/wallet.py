"""
Wallet API endpoints for balance and account information
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas import WalletBalanceResponse
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

def get_polymarket_client():
    """Get initialized Polymarket client"""
    try:
        # Check if credentials are configured
        pk = os.getenv("PK", "")
        browser_address = os.getenv("BROWSER_ADDRESS", "")
        
        # Check for placeholder values
        if not pk or pk in ["your_private_key_here", "your_actual_private_key"]:
            raise HTTPException(
                status_code=400,
                detail="Private key (PK) not configured. Please set a valid private key in your .env file (starts with 0x)."
            )
        
        if not browser_address or browser_address in ["your_wallet_address_here", "your_actual_wallet_address"]:
            raise HTTPException(
                status_code=400,
                detail="Wallet address (BROWSER_ADDRESS) not configured. Please set a valid wallet address in your .env file (starts with 0x)."
            )
        
        # Validate wallet address format (should be hex string starting with 0x)
        if not browser_address.startswith("0x") or len(browser_address) != 42:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid wallet address format. Expected hex string starting with 0x and 42 characters long. Got: {browser_address[:20]}..."
            )
        
        from poly_data.polymarket_client import PolymarketClient
        client = PolymarketClient()
        return client
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        
        # Provide helpful error messages for common issues
        if "hex string" in error_msg.lower() or "invalid address" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid wallet address format. Please check your BROWSER_ADDRESS in .env file. Error: {error_msg}"
            )
        elif "private key" in error_msg.lower() or "key" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid private key format. Please check your PK in .env file. Error: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize Polymarket client: {error_msg}"
            )

@router.get("/balance", response_model=WalletBalanceResponse)
async def get_usdc_balance():
    """
    Get USDC balance from connected wallet
    """
    try:
        client = get_polymarket_client()
        balance = client.get_usdc_balance()
        
        return WalletBalanceResponse(
            usdc_balance=round(balance, 2),
            total_balance=None,
            positions_value=None,
            wallet_address=os.getenv("BROWSER_ADDRESS", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch USDC balance: {str(e)}"
        )

@router.get("/total", response_model=WalletBalanceResponse)
async def get_total_balance():
    """
    Get total balance (USDC + positions value) from connected wallet
    """
    try:
        client = get_polymarket_client()
        total_balance = client.get_total_balance()
        usdc_balance = client.get_usdc_balance()
        positions_value = client.get_pos_balance()
        
        return WalletBalanceResponse(
            usdc_balance=round(usdc_balance, 2),
            total_balance=round(total_balance, 2),
            positions_value=round(positions_value, 2),
            wallet_address=os.getenv("BROWSER_ADDRESS", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch total balance: {str(e)}"
        )

@router.get("/positions-value", response_model=WalletBalanceResponse)
async def get_positions_value():
    """
    Get total value of all positions
    """
    try:
        client = get_polymarket_client()
        positions_value = client.get_pos_balance()
        usdc_balance = client.get_usdc_balance()
        
        return WalletBalanceResponse(
            usdc_balance=round(usdc_balance, 2),
            total_balance=None,
            positions_value=round(positions_value, 2),
            wallet_address=os.getenv("BROWSER_ADDRESS", "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch positions value: {str(e)}"
        )

@router.get("/info")
async def get_wallet_info():
    """
    Get wallet information (address, connection status)
    """
    wallet_address = os.getenv("BROWSER_ADDRESS", "")
    pk_set = bool(os.getenv("PK", ""))
    
    return {
        "wallet_address": wallet_address,
        "wallet_configured": bool(wallet_address),
        "private_key_configured": pk_set,
        "connected": bool(wallet_address and pk_set)
    }

@router.get("/token-balances")
async def get_token_balances():
    """
    Get all token balances from wallet (only tokens with balance > 0)
    Excludes USDC, only shows position tokens
    """
    try:
        client = get_polymarket_client()
        
        # Get all positions
        positions_df = client.get_all_positions()
        
        if positions_df.empty:
            return {"tokens": [], "total_value": 0.0}
        
        # Filter positions with balance > 0
        active_positions = positions_df[positions_df['size'] > 0]
        
        tokens = []
        total_value = 0.0
        
        for _, row in active_positions.iterrows():
            token_info = {
                "token_id": str(row.get('asset', '')),
                "size": float(row.get('size', 0.0)),
                "avg_price": float(row.get('avgPrice', 0.0)),
                "current_price": float(row.get('curPrice', 0.0)),
                "value": float(row.get('size', 0.0)) * float(row.get('curPrice', 0.0)),
                "pnl_percent": float(row.get('percentPnl', 0.0))
            }
            tokens.append(token_info)
            total_value += token_info["value"]
        
        return {
            "tokens": tokens,
            "total_value": round(total_value, 2),
            "count": len(tokens)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch token balances: {str(e)}"
        )

