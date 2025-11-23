# Polymarket Trading Bot - Complete Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Strategy](#architecture--strategy)
3. [Prerequisites](#prerequisites)
4. [Installation Guide (Windows)](#installation-guide-windows)
5. [Configuration](#configuration)
6. [Running the Bot](#running-the-bot)
7. [How the Bot Works](#how-the-bot-works)
8. [Trading Strategies](#trading-strategies)
9. [Web Interface](#web-interface)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Configuration](#advanced-configuration)
12. [Security Best Practices](#security-best-practices)

---

## Overview

The Polymarket Trading Bot is an automated market-making system designed to trade on Polymarket prediction markets. It provides liquidity by placing buy and sell orders simultaneously, profiting from the bid-ask spread while managing risk through position limits and trading modes.

### Key Features

- **Automated Market Making**: Places buy and sell orders to capture spread
- **Multiple Trading Modes**: Market Making, Position Building, Hybrid, and Sell-Only
- **Real-time Data**: WebSocket connections for live market data and order updates
- **Web Dashboard**: Vue.js frontend for monitoring and control
- **Risk Management**: Configurable position limits, stop-loss, and take-profit
- **Dry Run Mode**: Test strategies without real money
- **Database Integration**: SQLite database for persistent storage

### System Components

1. **Trading Bot** (`main.py`): Core trading logic with WebSocket connections
2. **Backend API** (`backend/main.py`): FastAPI REST API for frontend
3. **Frontend** (`frontend/`): Vue.js web interface
4. **Database**: SQLite for markets, positions, orders, and settings

---

## Architecture & Strategy

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Vue.js)                    │
│              http://localhost:8080                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│              Backend API (FastAPI)                           │
│              http://localhost:8000                           │
│  - Markets Management                                        │
│  - Positions & Orders                                        │
│  - Trading Control                                           │
│  - Statistics                                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Trading Bot (main.py)                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │  WebSocket Connections                              │     │
│  │  - Market Channel (order book updates)              │     │
│  │  - User Channel (orders & trades)                   │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Trading Engine (trading.py)                        │     │
│  │  - Market Making Logic                              │     │
│  │  - Position Management                              │     │
│  │  - Risk Management                                  │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Data Processing                                    │     │
│  │  - Position Updates (every 5s)                      │     │
│  │  - Order Updates (every 5s)                         │     │
│  │  - Market Data Updates (every 30s)                  │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Polymarket API                                  │
│  - REST API (orders, positions, markets)                    │
│  - WebSocket API (real-time data)                           │
└─────────────────────────────────────────────────────────────┘
```

### Trading Strategy Overview

The bot implements **market making** strategy:

1. **Bid-Ask Spread Capture**: Places buy orders below market price and sell orders above market price
2. **Liquidity Provision**: Provides liquidity to the market, earning spread
3. **Position Management**: Maintains balanced positions or builds directional positions based on mode
4. **Risk Controls**: Limits position sizes, monitors PnL, and implements stop-loss/take-profit

### How Market Making Works

1. **Order Placement**:
   - Buy orders placed at bid price (below mid-price)
   - Sell orders placed at ask price (above mid-price)
   - Spread = Ask Price - Bid Price = Profit per round trip

2. **Price Calculation**:
   - Analyzes order book depth
   - Calculates optimal bid/ask prices
   - Considers current position and risk parameters

3. **Position Management**:
   - Monitors current positions
   - Adjusts order sizes based on position limits
   - Manages average entry price

4. **Risk Management**:
   - Maximum position size limits
   - Stop-loss thresholds
   - Take-profit targets
   - Spread limits

---

## Prerequisites

### Required Software

1. **Python 3.9.10 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

2. **Node.js 18 or higher**
   - Download from: https://nodejs.org/
   - Includes npm (Node Package Manager)
   - Verify: `node --version` and `npm --version`

3. **Git** (optional, for cloning repository)
   - Download from: https://git-scm.com/download/win

4. **PowerShell 5.1+** (included with Windows 10/11)

### Optional but Recommended

- **Visual Studio Code** or similar IDE
- **Postman** or similar API testing tool
- **Browser Developer Tools** (F12) for debugging frontend

### Polymarket Account Requirements

1. **Wallet**: MetaMask or compatible Web3 wallet
2. **Private Key**: For API authentication
3. **USDC Balance**: For trading (test with small amounts first)
4. **API Access**: Polymarket API credentials

---

## Installation Guide (Windows)

### Step 1: Clone or Download the Repository

```powershell
# If using Git
git clone <repository-url>
cd poly-maker-main

# Or download and extract ZIP file
```

### Step 2: Verify Prerequisites

Open PowerShell and verify:

```powershell
python --version    # Should show Python 3.9.10 or higher
node --version      # Should show v18.x.x or higher
npm --version       # Should show 9.x.x or higher
```

### Step 3: Run Installation Script

The easiest way is to use the provided installation script:

```powershell
# Navigate to project directory
cd poly-maker-main

# Run installation script
.\INSTALL_DEV.ps1
```

**What the script does:**
1. Checks Python and Node.js versions
2. Creates Python virtual environment
3. Installs backend dependencies
4. Initializes database
5. Installs frontend dependencies
6. Creates `.env` template file

### Step 4: Manual Installation (Alternative)

If the script fails, follow these steps:

#### Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# If pip install fails, try upgrading pip first:
python -m pip install --upgrade pip

# Initialize database
python -c "from database import init_db; init_db()"
```

**Common Issues:**
- **Error: "python is not recognized"**
  - Solution: Add Python to PATH or use full path: `C:\Python39\python.exe`
  
- **Error: "pip install fails for py-clob-client"**
  - Solution: Install Rust first from https://rustup.rs/
  - Then retry: `pip install py-clob-client`

- **Error: "Microsoft Visual C++ 14.0 is required"**
  - Solution: Install "Microsoft C++ Build Tools" from:
    https://visualstudio.microsoft.com/visual-cpp-build-tools/

#### Frontend Setup

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# If npm install fails, try:
npm install --legacy-peer-deps
```

**Common Issues:**
- **Error: "npm ERR! code ELIFECYCLE"**
  - Solution: Delete `node_modules` and `package-lock.json`, then retry
  - `Remove-Item -Recurse -Force node_modules, package-lock.json`
  - `npm install`

- **Error: "Port 8080 already in use"**
  - Solution: Change port in `vue.config.js` or stop other services

### Step 5: Configure Environment Variables

1. **Locate `.env` file** in project root (created by installation script)

2. **Edit `.env` file** with your credentials:

```env
# Polymarket API Credentials
PK=your_private_key_here
BROWSER_ADDRESS=your_wallet_address_here

# Database Configuration
DATABASE_URL=sqlite:///./polymarket_bot.db

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:8080

# Trading Mode (true = simulation, false = live trading)
DRY_RUN=true

# Safety Limits
MAX_POSITION_SIZE=100
MAX_TRADE_SIZE=10
MIN_TRADE_SIZE=1
```

**⚠️ SECURITY WARNING:**
- Never commit `.env` file to version control
- Keep your private key secure
- Use DRY_RUN=true for testing

**How to get credentials:**
1. **Private Key (PK)**: Export from MetaMask or your wallet
   - MetaMask: Account → Settings → Security & Privacy → Show Private Key
   - ⚠️ Never share this key!

2. **Browser Address (BROWSER_ADDRESS)**: Your wallet address
   - Same as the address shown in MetaMask
   - Format: `0x...` (42 characters)

### Step 6: Verify Installation

```powershell
# Test backend
cd backend
.\venv\Scripts\Activate.ps1
python -c "from poly_data.polymarket_client import PolymarketClient; print('Backend OK')"

# Test frontend
cd ..\frontend
npm run serve
# Should start on http://localhost:8080
```

---

## Configuration

### Environment Variables Explained

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PK` | Private key for wallet | - | Yes |
| `BROWSER_ADDRESS` | Wallet address | - | Yes |
| `DATABASE_URL` | Database connection string | `sqlite:///./polymarket_bot.db` | No |
| `API_HOST` | API server host | `0.0.0.0` | No |
| `API_PORT` | API server port | `8000` | No |
| `FRONTEND_URL` | Frontend URL | `http://localhost:8080` | No |
| `DRY_RUN` | Simulation mode | `true` | No |
| `MAX_POSITION_SIZE` | Maximum position size (USDC) | `100` | No |
| `MAX_TRADE_SIZE` | Maximum trade size (USDC) | `10` | No |
| `MIN_TRADE_SIZE` | Minimum trade size (USDC) | `1` | No |

### Database Configuration

The bot uses SQLite by default. Database file: `backend/polymarket_bot.db`

**Database Tables:**
- `markets`: Market configurations
- `trading_params`: Trading parameters per market
- `positions`: Current positions
- `orders`: Order history
- `global_settings`: Global settings

**To reset database:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from database import init_db; init_db()"
```

---

## Running the Bot

### Quick Start (Using Scripts)

```powershell
# Start everything (backend + frontend)
.\START_DEV.ps1
```

This script:
1. Starts backend API on http://localhost:8000
2. Starts frontend on http://localhost:8080
3. Opens two PowerShell windows (one for each service)

### Manual Start

#### Start Backend API

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
✅ Database initialized
INFO:     Application startup complete.
```

#### Start Frontend

Open a **new** PowerShell window:

```powershell
cd frontend
npm run serve
```

**Expected output:**
```
App running at:
- Local:   http://localhost:8080/
- Network: http://192.168.x.x:8080/
```

#### Start Trading Bot

Open a **third** PowerShell window:

```powershell
cd poly-maker-main
.\backend\venv\Scripts\Activate.ps1
python main.py
```

**Expected output:**
```
🔵 DRY RUN MODE
✅ API credentials created/derived and set successfully
After initial updates: ...
There are X markets, Y positions and Z orders...
📡 Waiting for market data updates...
```

### Accessing the Web Interface

1. Open browser: http://localhost:8080
2. You should see the dashboard
3. Navigate to different pages:
   - **Dashboard**: Overview and statistics
   - **Markets**: Manage markets to trade
   - **Positions**: View current positions
   - **Orders**: View order history
   - **Settings**: Configure global settings

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## How the Bot Works

### Execution Flow

```
1. INITIALIZATION
   ├── Load environment variables (.env)
   ├── Initialize PolymarketClient
   ├── Create/derive API credentials
   ├── Connect to database
   └── Load market configurations

2. DATA LOADING
   ├── Fetch markets from database
   ├── Get current positions from Polymarket API
   ├── Get current orders from Polymarket API
   └── Build token list for WebSocket subscriptions

3. WEBSOCKET CONNECTIONS
   ├── Market Channel: Subscribe to order book updates
   │   └── Receives: Best bid/ask, order book depth
   ├── User Channel: Subscribe to user events
   │   ├── Receives: Order updates (PLACEMENT, UPDATE, CANCELLATION)
   │   └── Receives: Trade updates (MATCHED, MINED, CONFIRMED)
   └── Ping/Pong: Keep connections alive (every 5 seconds)

4. BACKGROUND UPDATES (Every 5 seconds)
   ├── Update positions from Polymarket API
   ├── Update orders from Polymarket API
   └── Clean up stale pending trades (>15 seconds)

5. MARKET DATA UPDATES (Every 30 seconds)
   └── Refresh market information

6. TRADING LOGIC (Triggered by WebSocket events)
   ├── Receive order book update
   ├── Calculate optimal bid/ask prices
   ├── Determine buy/sell amounts based on:
   │   ├── Current position
   │   ├── Trading mode
   │   ├── Risk parameters
   │   └── Market conditions
   ├── Place orders (or cancel existing)
   └── Update position tracking
```

### Key Components

#### 1. PolymarketClient (`poly_data/polymarket_client.py`)

Handles all interactions with Polymarket API:
- Order creation and cancellation
- Position queries
- Order queries
- API authentication (L2 headers)

#### 2. Trading Engine (`trading.py`)

Core trading logic:
- `perform_trade(market)`: Main trading function for each market
- Price calculation based on order book
- Position management
- Risk checks

#### 3. Data Processing (`poly_data/data_processing.py`)

Processes WebSocket messages:
- Order book updates
- Trade confirmations
- Position updates

#### 4. Global State (`poly_data/global_state.py`)

In-memory state management:
- Current positions
- Active orders
- Market data
- Trading parameters

#### 5. Database Layer (`backend/database.py`)

Persistent storage:
- SQLAlchemy ORM models
- Market configurations
- Position history
- Order history

---

## Trading Strategies

The bot supports four trading modes:

### 1. MARKET_MAKING (Default)

**Purpose**: Provide liquidity and capture spread

**Behavior**:
- Places both buy and sell orders simultaneously
- Maintains balanced positions around zero
- Profits from bid-ask spread

**When to use**: 
- High liquidity markets
- When you want consistent, low-risk returns
- Markets with good spread opportunities

**Example**:
```
Current Price: $0.50
Buy Order: $0.49 (size: 10 USDC)
Sell Order: $0.51 (size: 10 USDC)
Spread: $0.02 = 4% profit if both fill
```

### 2. POSITION_BUILDING

**Purpose**: Build a directional position

**Behavior**:
- Only buys until target position is reached
- After target, can sell to take profits
- One-way trading

**When to use**:
- When you have a directional view
- Building positions for events
- Accumulating tokens

**Parameters**:
- `target_position`: Target size to build

**Example**:
```
Target Position: 100 tokens
Current Position: 0
Behavior: Only place buy orders until 100 tokens reached
```

### 3. HYBRID

**Purpose**: Build position first, then market make

**Behavior**:
- Builds position to target (like POSITION_BUILDING)
- After target reached, switches to market making
- Best of both worlds

**When to use**:
- Want to build position but also provide liquidity
- Markets where you have a view but want to trade around it

**Example**:
```
Target: 50 tokens
Current: 0 → 50: Only buying
Current: 50+: Market making (buy and sell)
```

### 4. SELL_ONLY

**Purpose**: Exit positions (de-risking)

**Behavior**:
- Only places sell orders
- No buying
- Reduces position size

**When to use**:
- Exiting positions
- Taking profits
- Risk reduction

**Example**:
```
Current Position: 100 tokens
Behavior: Only place sell orders to reduce position
```

### Trading Parameters

Each market has configurable parameters:

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `trade_size` | Size of each order | 5-20 USDC |
| `max_size` | Maximum position size | 50-200 USDC |
| `min_size` | Minimum position size | 0-5 USDC |
| `max_spread` | Maximum spread to trade | 2-10% |
| `tick_size` | Price increment | 0.01-0.001 |
| `stop_loss_threshold` | Stop loss % | -5% to -10% |
| `take_profit_threshold` | Take profit % | 2% to 5% |

---

## Web Interface

### Dashboard

**Overview Statistics**:
- Total PnL
- Active Markets
- Open Positions
- Active Orders
- Positions Value

**Features**:
- Start/Stop trading bot
- View recent orders
- View active positions
- Trading diagnostics

### Markets Page

**Features**:
- View all markets
- Add markets manually
- Fetch crypto markets from Polymarket
- Configure trading parameters
- Enable/disable markets
- Bulk operations

**Adding a Market**:
1. Click "Fetch Crypto Markets" or "Add Market"
2. Fill in market details:
   - Condition ID
   - Question
   - Token IDs (token1, token2)
3. Configure trading parameters
4. Set `is_active = true`
5. Save

### Positions Page

**Features**:
- View all open positions
- See PnL breakdown
- Filter by market or side
- Refresh positions

**Information Displayed**:
- Market ID
- Token ID
- Side (YES/NO)
- Size
- Average Price
- Unrealized PnL
- Realized PnL
- Total PnL

### Orders Page

**Features**:
- View all orders (active and historical)
- Filter by status (PENDING, FILLED, CANCELLED)
- Filter by market
- View order details

**Information Displayed**:
- Order ID
- Market ID
- Side Type (BUY/SELL)
- Price
- Size
- Filled Size
- Status
- Created Time

### Settings Page

**Global Settings**:
- Trading mode (DRY_RUN / LIVE)
- Safety limits
- API configuration

---

## Troubleshooting

This section provides comprehensive troubleshooting guides for common issues. Follow the steps in order.

### Troubleshooting Methodology

1. **Check Logs First**: Always start by examining console output
2. **Verify Prerequisites**: Ensure Python, Node.js, and dependencies are installed
3. **Check Configuration**: Verify `.env` file is correct
4. **Test Components Individually**: Isolate the problem
5. **Check Network**: Verify internet connection and API accessibility

### Common Issues and Solutions

#### 1. Backend Won't Start

##### Issue: ModuleNotFoundError

**Symptoms**:
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'poly_data'
```

**Diagnosis Steps**:
```powershell
# 1. Check if virtual environment is activated
# You should see (venv) in your prompt
# If not, activate it:
cd backend
.\venv\Scripts\Activate.ps1

# 2. Check installed packages
pip list

# 3. Verify you're in the right directory
pwd  # Should show backend directory
```

**Solution**:
```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# If specific package fails, install individually
pip install fastapi uvicorn sqlalchemy
```

**If pip install fails**:
```powershell
# Clear pip cache
pip cache purge

# Try with --no-cache-dir
pip install --no-cache-dir -r requirements.txt

# For Windows-specific issues, install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

##### Issue: Port Already in Use

**Symptoms**:
```
ERROR:    [Errno 10048] Only one usage of each socket address is permitted
Address already in use
```

**Diagnosis Steps**:
```powershell
# 1. Find what's using port 8000
netstat -ano | findstr :8000

# Output example:
# TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    12345
# The last number (12345) is the Process ID (PID)
```

**Solution**:
```powershell
# Method 1: Kill the process
# Replace 12345 with actual PID from netstat
taskkill /PID 12345 /F

# Method 2: Change port in .env
# Edit .env file:
API_PORT=8001

# Method 3: Find and kill by process name
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

##### Issue: Database Locked

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Diagnosis Steps**:
```powershell
# 1. Check if database file exists
Test-Path backend/polymarket_bot.db

# 2. Check if any process is using the database
# SQLite locks when multiple connections exist
```

**Solution**:
```powershell
# Method 1: Close all Python processes
Get-Process python | Stop-Process -Force

# Method 2: Delete and recreate database
cd backend
.\venv\Scripts\Activate.ps1
Remove-Item polymarket_bot.db -ErrorAction SilentlyContinue
python -c "from database import init_db; init_db()"

# Method 3: Use database browser to check locks
# Download DB Browser for SQLite: https://sqlitebrowser.org/
```

##### Issue: Import Errors (Circular Dependencies)

**Symptoms**:
```
ImportError: cannot import name 'X' from 'Y'
Circular import detected
```

**Solution**:
```powershell
# This usually means Python path is wrong
# Ensure you're running from correct directory
cd backend
.\venv\Scripts\Activate.ps1

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# If poly_data not found, add to path
$env:PYTHONPATH = "$PWD\..;$env:PYTHONPATH"
```

#### 2. Frontend Won't Start

##### Issue: Port 8080 Already in Use

**Symptoms**:
```
Error: listen EADDRINUSE: address already in use :::8080
Port 8080 is already in use
```

**Diagnosis Steps**:
```powershell
# Check what's using port 8080
netstat -ano | findstr :8080

# Check if another Vue dev server is running
Get-Process | Where-Object {$_.ProcessName -like "*node*"}
```

**Solution**:
```powershell
# Method 1: Kill Node.js processes
Get-Process node | Stop-Process -Force

# Method 2: Change port
# Edit frontend/vue.config.js:
# devServer: { port: 8081 }

# Method 3: Use different port via command line
cd frontend
npm run serve -- --port 8081
```

##### Issue: npm install Fails

**Symptoms**:
```
npm ERR! code ELIFECYCLE
npm ERR! errno 1
npm ERR! Failed at the ... script
```

**Diagnosis Steps**:
```powershell
# Check Node.js version
node --version  # Should be 18+

# Check npm version
npm --version

# Check disk space
Get-PSDrive C | Select-Object Used,Free
```

**Solution**:
```powershell
cd frontend

# Step 1: Clean everything
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue

# Step 2: Clear npm cache
npm cache clean --force

# Step 3: Reinstall with legacy peer deps
npm install --legacy-peer-deps

# If still fails, try:
npm install --force

# If specific package fails:
npm install <package-name> --legacy-peer-deps
```

**Common npm Errors**:

- **Error: "python not found"**:
  ```powershell
  # Some npm packages need Python
  npm config set python python
  # Or install windows-build-tools
  npm install --global windows-build-tools
  ```

- **Error: "MSBuild not found"**:
  ```powershell
  # Install Visual Studio Build Tools
  # Download from: https://visualstudio.microsoft.com/downloads/
  # Install "Desktop development with C++" workload
  ```

##### Issue: Cannot Connect to API

**Symptoms**:
- Frontend loads but shows "Loading..." forever
- Console shows: `Failed to fetch` or `Network Error`
- API calls return 404 or CORS errors

**Diagnosis Steps**:
```powershell
# 1. Check if backend is running
curl http://localhost:8000/health
# Or in browser: http://localhost:8000/health

# 2. Check frontend API URL configuration
# Open frontend/vue.config.js or check browser console

# 3. Check CORS in backend
# Open backend/main.py, check CORS middleware
```

**Solution**:
```powershell
# Step 1: Verify backend is running
# In backend directory:
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Step 2: Check API URL in frontend
# Edit frontend/vue.config.js:
module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
}

# Step 3: Verify CORS settings in backend/main.py
# Should have:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Step 4: Check Windows Firewall
# Allow Python and Node.js through firewall
```

##### Issue: Vue Build Errors

**Symptoms**:
```
Module build failed
SyntaxError: Unexpected token
```

**Solution**:
```powershell
cd frontend

# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules, .cache
npm cache clean --force
npm install --legacy-peer-deps

# If using Vue CLI, reinstall
npm install -g @vue/cli
vue upgrade
```

#### 3. Trading Bot Issues

##### Issue: Failed to Create API Credentials

**Symptoms**:
```
❌ Error creating/deriving API credentials
Failed to set up API credentials
ValueError: Failed to create or derive API credentials
```

**Diagnosis Steps**:
```powershell
# 1. Check .env file
Get-Content .env | Select-String "PK|BROWSER_ADDRESS"

# 2. Verify private key format
# Should start with 0x and be 66 characters
# Example: 0x1234567890abcdef...

# 3. Test credentials manually
cd backend
.\venv\Scripts\Activate.ps1
python -c "from poly_data.polymarket_client import PolymarketClient; c=PolymarketClient(); print('OK')"
```

**Solution**:
```powershell
# Step 1: Verify .env file format
# PK should be your private key (with or without 0x prefix)
# BROWSER_ADDRESS should be your wallet address

# Step 2: Check private key is valid
# Private key should be 64 hex characters (or 66 with 0x)
# If exported from MetaMask, it should be correct

# Step 3: Ensure wallet has USDC
# Check on Polygon network: https://polygonscan.com/address/YOUR_ADDRESS

# Step 4: Verify network connectivity
# Test Polymarket API:
python -c "import requests; r=requests.get('https://clob.polymarket.com/'); print(r.status_code)"

# Step 5: Check for special characters in .env
# Ensure no quotes around values:
# WRONG: PK="0x123..."
# CORRECT: PK=0x123...
```

##### Issue: No Markets Found

**Symptoms**:
```
⚠️  WARNING: No active markets found!
There are 0 markets
```

**Diagnosis Steps**:
```powershell
# 1. Check database
cd backend
.\venv\Scripts\Activate.ps1
python -c "from database import SessionLocal, Market; db=SessionLocal(); print(f'Total markets: {db.query(Market).count()}'); print(f'Active markets: {db.query(Market).filter(Market.is_active==True).count()}')"

# 2. Check markets in web interface
# Go to http://localhost:8080/markets
```

**Solution**:
```powershell
# Method 1: Add markets via web interface
# 1. Open http://localhost:8080/markets
# 2. Click "Fetch Crypto Markets" or "Add Market"
# 3. Fill in market details
# 4. Set is_active = true
# 5. Save

# Method 2: Add market via API
# POST http://localhost:8000/api/markets
# Body: {
#   "condition_id": "...",
#   "question": "...",
#   "token1": "...",
#   "token2": "...",
#   "is_active": true
# }

# Method 3: Check database directly
# Use DB Browser for SQLite or:
python -c "from database import SessionLocal, Market; db=SessionLocal(); markets=db.query(Market).all(); [print(f'{m.id}: {m.question} (active: {m.is_active})') for m in markets]"
```

##### Issue: WebSocket Connection Failed

**Symptoms**:
```
Connection closed in market websocket
WebSocket connection failed
Connection refused
```

**Diagnosis Steps**:
```powershell
# 1. Test internet connection
ping google.com

# 2. Test Polymarket WebSocket endpoint
# Use online WebSocket tester or:
python -c "import asyncio, websockets; asyncio.run(websockets.connect('wss://clob-ws.polymarket.com'))"

# 3. Check firewall
# Windows Firewall might block WebSocket connections
```

**Solution**:
```powershell
# Step 1: Check Windows Firewall
# Allow Python through firewall:
# Control Panel → Windows Defender Firewall → Allow an app
# Add Python.exe (from venv)

# Step 2: Check proxy settings
# If behind corporate proxy, configure:
$env:HTTP_PROXY = "http://proxy:port"
$env:HTTPS_PROXY = "http://proxy:port"

# Step 3: Verify WebSocket endpoint
# Check poly_data/api_constants.py for correct endpoint
# Should be: wss://clob-ws.polymarket.com

# Step 4: Check for antivirus interference
# Temporarily disable antivirus to test
# Add Python and Node.js to antivirus exclusions

# Step 5: Test with minimal code
python -c "
import asyncio
import websockets
async def test():
    try:
        async with websockets.connect('wss://clob-ws.polymarket.com') as ws:
            print('Connected!')
    except Exception as e:
        print(f'Error: {e}')
asyncio.run(test())
"
```

##### Issue: Orders Not Being Placed

**Symptoms**:
- Bot is running but no orders appear
- Dashboard shows 0 active orders
- Console shows no order creation messages

**Diagnosis Steps**:
```powershell
# 1. Check DRY_RUN mode
# Console should show: 🔵 DRY RUN MODE or 🔴 LIVE TRADING MODE

# 2. Check markets are active
# In web interface: Markets page → is_active = true

# 3. Check trading parameters
# Markets must have trading_params configured

# 4. Review console logs
# Look for error messages or warnings
```

**Solution**:
```powershell
# Step 1: Verify DRY_RUN setting
# Check .env: DRY_RUN=true (for testing) or false (for live)
# Restart bot after changing

# Step 2: Check market configuration
# In web interface:
# - Markets page → Ensure markets have is_active = true
# - Each market needs trading_params configured
# - Check token1 and token2 are set

# Step 3: Check Diagnostics
# Dashboard → Click "Diagnostics" button
# Review:
# - Bot Status: Should be "Running"
# - Markets: Should show active markets
# - WebSocket: Should show tokens subscribed

# Step 4: Verify WebSocket is receiving data
# Console should show:
# ✅ Sent market subscription message for X tokens
# 📡 Waiting for market data updates...
# If no updates, WebSocket might not be connected

# Step 5: Check order book data
# Console should show order book updates
# If no updates, markets might not have liquidity

# Step 6: Review trading logic
# Check console for:
# - "Creating new order for..." messages
# - "Not creating order because..." messages
# - Error messages

# Step 7: Test with single market
# Start with 1 market, ensure it works, then add more
```

##### Issue: Positions/Orders Not Showing in Web Interface

**Symptoms**:
- Dashboard shows counts (e.g., "1 position") but Positions page is empty
- Orders page shows no orders
- Data exists in database but not displayed

**Diagnosis Steps**:
```powershell
# 1. Check database directly
cd backend
.\venv\Scripts\Activate.ps1
python -c "
from database import SessionLocal, Position, Order
db = SessionLocal()
print(f'Positions in DB: {db.query(Position).count()}')
print(f'Orders in DB: {db.query(Order).count()}')
positions = db.query(Position).filter(Position.size > 0).all()
print(f'Positions with size > 0: {len(positions)}')
for p in positions[:3]:
    print(f'  Position: size={p.size}, market_id={p.market_id}')
"

# 2. Check API response
# In browser: http://localhost:8000/api/positions
# Should return JSON array

# 3. Check browser console (F12)
# Look for API errors or network failures
```

**Solution**:
```powershell
# Step 1: Verify API endpoint
# Test in browser: http://localhost:8000/api/positions
# Should return JSON, not error

# Step 2: Check frontend cache
# In browser: F12 → Application → Clear Storage → Clear site data
# Or hard refresh: Ctrl+Shift+R

# Step 3: Verify database sync
# Positions/Orders are synced from global_state to database
# Check if update_positions() and update_orders() are running
# Console should show periodic updates

# Step 4: Manual refresh
# In Positions/Orders page, click "Refresh" button
# Check browser console for API calls

# Step 5: Check API filters
# Positions API filters: size > 0
# If position size is 0, it won't show
# Check database: SELECT * FROM positions WHERE size > 0;

# Step 6: Verify data format
# API should return proper JSON
# Check response in browser Network tab (F12)
```

##### Issue: PnL Values Not Showing

**Symptoms**:
- Positions page shows positions but PnL columns are $0.00
- Unrealized PnL and Realized PnL are zero

**Diagnosis Steps**:
```powershell
# Check database
python -c "
from database import SessionLocal, Position
db = SessionLocal()
positions = db.query(Position).all()
for p in positions:
    print(f'Position {p.id}: unrealized={p.unrealized_pnl}, realized={p.realized_pnl}')
"
```

**Solution**:
```powershell
# PnL is calculated when positions are updated
# Ensure update_positions() is running (every 5 seconds)
# PnL calculation uses Polymarket API data (curPrice, percentPnl)

# If PnL is still 0:
# 1. Check Polymarket API returns price data
# 2. Verify position has size > 0
# 3. Check avg_price is set correctly
# 4. Review update_positions() function logs
```

#### 4. Database Issues

##### Issue: Table Doesn't Exist

**Symptoms**:
```
sqlalchemy.exc.OperationalError: no such table: markets
Table 'positions' doesn't exist
```

**Diagnosis Steps**:
```powershell
# Check if database file exists
Test-Path backend/polymarket_bot.db

# Check database schema
cd backend
.\venv\Scripts\Activate.ps1
python -c "from database import SessionLocal, Base, engine; Base.metadata.create_all(engine); print('Tables created')"
```

**Solution**:
```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Reinitialize database
python -c "from database import init_db; init_db()"

# Verify tables exist
python -c "
from database import SessionLocal, engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Tables:', tables)
"
```

##### Issue: Positions/Orders Not Showing in Database

**Symptoms**:
- Dashboard shows counts but database is empty
- API returns empty arrays
- Data exists in global_state but not in database

**Diagnosis Steps**:
```powershell
# Step 1: Check database contents
cd backend
.\venv\Scripts\Activate.ps1
python -c "
from database import SessionLocal, Position, Order
db = SessionLocal()
print(f'Positions: {db.query(Position).count()}')
print(f'Orders: {db.query(Order).count()}')
print(f'Positions with size > 0: {db.query(Position).filter(Position.size > 0).count()}')
print(f'Active orders: {db.query(Order).filter(Order.status == \"PENDING\").count()}')
"

# Step 2: Check if sync functions are being called
# Review console logs for:
# - "Error syncing position to database"
# - "Error syncing order to database"
```

**Solution**:
```powershell
# The issue is that update_positions() and update_orders() 
# update global_state but may not sync to database
# This is by design - database sync happens separately

# To manually sync:
# 1. Ensure trading bot is running (main.py or via web interface)
# 2. Bot should call update_positions() and update_orders() every 5 seconds
# 3. Check console for sync errors

# If data still not syncing:
# 1. Check database permissions
# 2. Verify database file is writable
# 3. Check for import errors in db_utils.py
# 4. Review console logs for exceptions
```

##### Issue: Database Corruption

**Symptoms**:
```
database disk image is malformed
database is locked
```

**Solution**:
```powershell
# Step 1: Backup current database
Copy-Item backend/polymarket_bot.db backend/polymarket_bot.db.backup

# Step 2: Try to repair
cd backend
.\venv\Scripts\Activate.ps1
python -c "
import sqlite3
conn = sqlite3.connect('polymarket_bot.db')
conn.execute('PRAGMA integrity_check')
conn.close()
"

# Step 3: If repair fails, recreate
Remove-Item polymarket_bot.db
python -c "from database import init_db; init_db()"

# Step 4: Restore data if possible
# Use SQLite browser to export/import data
```

#### 5. Performance Issues

##### Issue: High CPU Usage

**Symptoms**:
- Task Manager shows Python using 50%+ CPU
- System becomes slow
- Fan noise increases

**Diagnosis Steps**:
```powershell
# Check CPU usage
Get-Process python | Select-Object ProcessName, CPU, WorkingSet

# Check for infinite loops in logs
# Look for repeated error messages
```

**Solution**:
```powershell
# Step 1: Reduce active markets
# In web interface: Markets page → Set fewer markets to is_active = true

# Step 2: Increase update intervals
# Edit main.py:
# time.sleep(5) → time.sleep(10)  # Update every 10s instead of 5s

# Step 3: Check for infinite loops
# Review console logs for repeated messages
# Common causes:
# - WebSocket reconnection loops
# - Error handling that retries too quickly

# Step 4: Optimize trading logic
# Reduce number of markets processed per cycle
# Add delays between market processing
```

##### Issue: High Memory Usage

**Symptoms**:
- Memory usage grows over time
- System becomes slow
- Out of memory errors

**Diagnosis Steps**:
```powershell
# Check memory usage
Get-Process python | Select-Object ProcessName, @{Name="Memory(MB)";Expression={[math]::Round($_.WorkingSet/1MB,2)}}

# Check for memory leaks
# Monitor memory over time
```

**Solution**:
```powershell
# Step 1: Restart bot periodically
# Set up scheduled task to restart every few hours

# Step 2: Clear old data
# Delete old orders/positions from database
python -c "
from database import SessionLocal, Order
from datetime import datetime, timedelta
db = SessionLocal()
old_date = datetime.utcnow() - timedelta(days=30)
old_orders = db.query(Order).filter(Order.created_at < old_date).all()
print(f'Deleting {len(old_orders)} old orders')
[db.delete(o) for o in old_orders]
db.commit()
"

# Step 3: Reduce WebSocket subscriptions
# Subscribe to fewer tokens
# Only subscribe to active markets

# Step 4: Enable garbage collection
# Already enabled in main.py with gc.collect()
# But can increase frequency
```

#### 6. API Rate Limits

##### Issue: 429 Too Many Requests

**Symptoms**:
```
429 Too Many Requests
Rate limit exceeded
```

**Solution**:
```powershell
# Step 1: Reduce update frequency
# Edit main.py: Increase sleep intervals
time.sleep(5) → time.sleep(10)

# Step 2: Implement request throttling
# Add delays between API calls
import time
time.sleep(0.1)  # 100ms between requests

# Step 3: Check Polymarket rate limits
# Review API documentation for limits
# Typically: 100 requests per minute

# Step 4: Cache API responses
# Don't fetch same data repeatedly
# Use cache with 5-second TTL (already implemented)
```

#### 7. Windows-Specific Issues

##### Issue: PowerShell Execution Policy

**Symptoms**:
```
cannot be loaded because running scripts is disabled on this system
```

**Solution**:
```powershell
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or for this session only:
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

##### Issue: Long Path Names

**Symptoms**:
```
The specified path, file name, or both are too long
```

**Solution**:
```powershell
# Enable long path support (Windows 10+)
# Run as Administrator:
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Or move project to shorter path:
# C:\projects\mark → C:\pmbot
```

##### Issue: Antivirus Blocking

**Symptoms**:
- Files deleted or quarantined
- Scripts won't run
- False positive detections

**Solution**:
```powershell
# Add exclusions in Windows Defender:
# Settings → Virus & threat protection → Manage settings → Exclusions
# Add folders:
# - Project directory
# - Python installation
# - Node.js installation
# - venv directory
```

##### Issue: Windows Firewall Blocking

**Symptoms**:
- Can't connect to API
- WebSocket connections fail
- Ports blocked

**Solution**:
```powershell
# Allow Python through firewall:
New-NetFirewallRule -DisplayName "Python" -Direction Inbound -Program "C:\path\to\python.exe" -Action Allow

# Allow Node.js:
New-NetFirewallRule -DisplayName "Node.js" -Direction Inbound -Program "C:\path\to\node.exe" -Action Allow

# Or use Windows Firewall GUI:
# Control Panel → Windows Defender Firewall → Allow an app
```

#### 8. WebSocket Connection Issues

##### Issue: WebSocket Keeps Disconnecting

**Symptoms**:
```
Connection closed
Reconnecting to the websocket
```

**Diagnosis Steps**:
```powershell
# Check network stability
ping -t google.com
# Let it run, check for packet loss

# Check WebSocket endpoint
# Test with online WebSocket client
```

**Solution**:
```powershell
# Step 1: Check internet connection
# Ensure stable connection
# Avoid VPN if possible (can cause issues)

# Step 2: Increase ping interval
# Edit poly_data/websocket_handlers.py:
# ping_interval=5 → ping_interval=10

# Step 3: Add reconnection delay
# Already implemented in main.py
# Increase delay if needed: await asyncio.sleep(1) → await asyncio.sleep(5)

# Step 4: Check for proxy interference
# If behind corporate proxy, configure:
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
```

##### Issue: WebSocket Authentication Failed

**Symptoms**:
```
Authentication failed
Invalid credentials
```

**Solution**:
```powershell
# Step 1: Verify API credentials
# Check .env file has correct PK and BROWSER_ADDRESS

# Step 2: Test credentials
python -c "
from poly_data.polymarket_client import PolymarketClient
c = PolymarketClient()
print('Credentials OK')
"

# Step 3: Check credential format
# PK should be hex string (with or without 0x)
# BROWSER_ADDRESS should be valid Ethereum address
```

### Step-by-Step Debugging Guide

Follow these steps systematically to diagnose issues:

#### Step 1: Verify Prerequisites

```powershell
# Check Python
python --version  # Should be 3.9.10+
where python      # Should show Python path

# Check Node.js
node --version    # Should be 18+
where node        # Should show Node.js path

# Check Git (optional)
git --version
```

#### Step 2: Verify Installation

```powershell
# Check backend dependencies
cd backend
.\venv\Scripts\Activate.ps1
pip list | Select-String "fastapi|uvicorn|sqlalchemy"

# Check frontend dependencies
cd ..\frontend
Test-Path node_modules
```

#### Step 3: Verify Configuration

```powershell
# Check .env file exists and has correct format
Test-Path .env
Get-Content .env

# Verify no syntax errors
# Each line should be: KEY=value (no spaces around =)
# No quotes needed (unless value contains spaces)
```

#### Step 4: Test Components Individually

```powershell
# Test 1: Backend API
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 0.0.0.0 --port 8000
# Should start without errors
# Test: http://localhost:8000/health

# Test 2: Frontend
cd ..\frontend
npm run serve
# Should start on http://localhost:8080

# Test 3: Polymarket Client
cd ..\backend
.\venv\Scripts\Activate.ps1
python -c "from poly_data.polymarket_client import PolymarketClient; c=PolymarketClient(); print('Client OK')"

# Test 4: Database
python -c "from database import SessionLocal, Market; db=SessionLocal(); print(f'Markets: {db.query(Market).count()}')"
```

#### Step 5: Check Logs

**Backend Logs**:
- Console output when running `uvicorn`
- Look for: Errors, warnings, startup messages

**Frontend Logs**:
- Browser console (F12 → Console tab)
- Look for: API errors, network failures, JavaScript errors

**Trading Bot Logs**:
- Console output when running `main.py`
- Look for: WebSocket connections, order placements, errors

#### Step 6: Network Diagnostics

```powershell
# Check if ports are open
netstat -ano | findstr ":8000"  # Backend
netstat -ano | findstr ":8080"  # Frontend

# Test API endpoints
# In browser or PowerShell:
Invoke-WebRequest -Uri http://localhost:8000/health
Invoke-WebRequest -Uri http://localhost:8000/api/markets

# Test Polymarket API
Invoke-WebRequest -Uri https://clob.polymarket.com/

# Test WebSocket (use online tool or Python)
python -c "
import asyncio
import websockets
async def test():
    try:
        async with websockets.connect('wss://clob-ws.polymarket.com') as ws:
            print('WebSocket OK')
    except Exception as e:
        print(f'WebSocket Error: {e}')
asyncio.run(test())
"
```

#### Step 7: Database Diagnostics

```powershell
# Install SQLite tools (if not installed)
# Download from: https://www.sqlite.org/download.html

# Or use Python:
cd backend
.\venv\Scripts\Activate.ps1
python -c "
from database import SessionLocal, Market, Position, Order
db = SessionLocal()

print('=== DATABASE DIAGNOSTICS ===')
print(f'Markets: {db.query(Market).count()}')
print(f'Active Markets: {db.query(Market).filter(Market.is_active==True).count()}')
print(f'Positions: {db.query(Position).count()}')
print(f'Positions (size>0): {db.query(Position).filter(Position.size>0).count()}')
print(f'Orders: {db.query(Order).count()}')
print(f'Active Orders: {db.query(Order).filter(Order.status==\"PENDING\").count()}')

# Show sample data
markets = db.query(Market).limit(3).all()
for m in markets:
    print(f'Market: {m.question} (active: {m.is_active}, tokens: {bool(m.token1 and m.token2)})')
"

# Check database file size
Get-Item backend/polymarket_bot.db | Select-Object Name, Length
```

#### Step 8: Enable Verbose Logging

**Backend Logging**:
```python
# Edit backend/main.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend Logging**:
```javascript
// Browser console already shows logs
// Enable verbose mode in vue.config.js:
module.exports = {
  configureWebpack: {
    devtool: 'source-map'
  }
}
```

**Trading Bot Logging**:
```python
# Add print statements in key functions
# Or use logging module
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Error Messages and Solutions

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| `ModuleNotFoundError` | Package not installed | `pip install -r requirements.txt` |
| `Port already in use` | Another service using port | Kill process or change port |
| `Database locked` | Multiple connections | Close all Python processes |
| `Connection refused` | Service not running | Start backend/frontend |
| `CORS error` | Frontend can't access API | Check CORS settings |
| `WebSocket failed` | Network/firewall issue | Check firewall, test connection |
| `No markets found` | Database empty | Add markets via web interface |
| `Invalid credentials` | Wrong PK/address | Check .env file |
| `429 Too Many Requests` | Rate limit exceeded | Reduce update frequency |

### Getting Help

1. **Check Logs First**: 90% of issues are visible in logs
2. **Review This README**: Most common issues are documented
3. **Check Code Comments**: Inline documentation explains logic
4. **Enable Debug Mode**: Add logging to isolate issues
5. **Test Components**: Isolate which component is failing
6. **Check Polymarket Status**: https://status.polymarket.com/
7. **Review API Docs**: https://docs.polymarket.com/

### Emergency Procedures

**If bot is placing unwanted orders**:
1. Stop bot immediately: Click "Stop Trading" in web interface
2. Cancel all orders manually on Polymarket
3. Review logs to understand what happened
4. Fix configuration before restarting

**If database is corrupted**:
1. Backup current database
2. Recreate database: `python -c "from database import init_db; init_db()"`
3. Re-add markets via web interface
4. Restart bot

**If credentials are compromised**:
1. Stop bot immediately
2. Revoke API access (if possible)
3. Generate new wallet/private key
4. Update .env file
5. Transfer funds to new wallet

---

## Advanced Configuration

### Custom Trading Parameters

Edit market parameters in web interface or database:

```python
# Example: Aggressive market making
trade_size = 20
max_size = 200
max_spread = 10
tick_size = 0.001

# Example: Conservative
trade_size = 5
max_size = 50
max_spread = 3
tick_size = 0.01
```

### WebSocket Configuration

Modify `poly_data/websocket_handlers.py`:

```python
# Ping interval (seconds)
ping_interval = 5

# Reconnection delay (seconds)
reconnect_delay = 1
```

### Update Intervals

Modify `main.py`:

```python
# Position/Order updates (seconds)
UPDATE_INTERVAL = 5

# Market data updates (seconds)
MARKET_UPDATE_INTERVAL = 30
```

### Database Optimization

For production, consider PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost/polymarket_bot
```

---

## Security Best Practices

1. **Private Key Security**:
   - Never commit `.env` to version control
   - Use environment variables in production
   - Consider hardware wallets for large amounts
   - Rotate keys periodically

2. **Network Security**:
   - Use HTTPS in production
   - Restrict API access (firewall)
   - Use VPN if trading from public networks

3. **Access Control**:
   - Password protect web interface
   - Use API keys for frontend-backend communication
   - Limit database access

4. **Monitoring**:
   - Set up alerts for large trades
   - Monitor position sizes
   - Track PnL changes
   - Log all trading activity

5. **Backup**:
   - Regular database backups
   - Export configuration
   - Document custom parameters

---

## Detailed Bot Operation

### Initialization Sequence

When the bot starts (`main.py` or via web interface):

1. **Load Configuration**:
   - Read `.env` file
   - Initialize `Config` class
   - Set DRY_RUN mode

2. **Initialize PolymarketClient**:
   - Create Web3 connection to Polygon
   - Set up API credentials (L2 authentication)
   - Initialize contract interfaces (USDC, Conditional Tokens, Neg Risk Adapter)

3. **Load Markets**:
   - Query database for active markets
   - Convert to DataFrame format
   - Extract token IDs (token1, token2)
   - Build token list for WebSocket subscriptions

4. **Initial Data Fetch**:
   - `update_positions()`: Get current positions from Polymarket API
   - `update_orders()`: Get current orders from Polymarket API
   - Store in `global_state`

5. **Start Background Thread**:
   - `update_periodically()`: Runs every 5 seconds
   - Updates positions and orders
   - Cleans up stale trades

6. **Connect WebSockets**:
   - Market Channel: Subscribe to order book updates
   - User Channel: Subscribe to user events (orders, trades)

### Trading Loop Execution

For each market, the bot executes `perform_trade(market)`:

1. **Get Market Data**:
   - Fetch order book from WebSocket or API
   - Calculate best bid/ask prices
   - Analyze order book depth

2. **Calculate Prices**:
   - `get_order_prices()`: Determines optimal bid/ask
   - Considers:
     - Current best bid/ask
     - Order book depth
     - Spread requirements
     - Tick size
     - Competitive positioning

3. **Determine Trade Amounts**:
   - `get_buy_sell_amount()`: Calculates order sizes
   - Based on:
     - Current position
     - Trading mode
     - Risk parameters
     - Market conditions

4. **Risk Checks**:
   - Position size limits
   - Spread limits
   - Stop-loss checks
   - Take-profit checks

5. **Place Orders**:
   - Cancel existing orders if needed
   - Create new buy order (if conditions met)
   - Create new sell order (if conditions met)
   - Track in `global_state.performing`

6. **Update State**:
   - Update position tracking
   - Update order tracking
   - Log activity

### WebSocket Message Processing

**Market Channel Messages**:
- Order book updates
- Price changes
- Triggers: `process_data()` → `perform_trade()`

**User Channel Messages**:
- Order events: PLACEMENT, UPDATE, CANCELLATION
- Trade events: MATCHED, MINED, CONFIRMED, FAILED
- Triggers: Position/order updates

### Data Flow

```
Polymarket API/WebSocket
    ↓
global_state (in-memory)
    ↓
Trading Logic (trading.py)
    ↓
Order Placement (PolymarketClient)
    ↓
WebSocket Updates (User Channel)
    ↓
Position/Order Updates
    ↓
Database (via update functions)
    ↓
Frontend API
    ↓
Web Interface
```

---

## Advanced Trading Strategy Details

### Price Calculation Algorithm

The bot uses sophisticated price calculation in `get_order_prices()`:

1. **Analyze Order Book**:
   - Best bid/ask prices
   - Second best bid/ask
   - Order book depth within N%
   - Liquidity ratios

2. **Calculate Mid Price**:
   - `mid_price = (best_bid + best_ask) / 2`

3. **Determine Competitive Position**:
   - If `order_front_running = true`: Place orders at best price
   - If `tick_improvement > 0`: Improve by N ticks
   - Consider spread requirements

4. **Apply Risk Adjustments**:
   - Adjust for current position
   - Consider average entry price
   - Apply spread limits

### Position Management

**Position Tracking**:
- Size: Current position size (positive = long, negative = short)
- Average Price: Weighted average entry price
- Updated via WebSocket trades or API polling

**Position Limits**:
- `max_size`: Maximum position size per market
- `min_size`: Minimum position size (usually 0)
- Total exposure across both sides of market

**Position Updates**:
- When buying: `new_avg = (old_avg * old_size + price * size) / (old_size + size)`
- When selling: Average price unchanged, size decreases

### Risk Management

**Stop Loss**:
- Monitors unrealized PnL
- If PnL < `stop_loss_threshold`, exit position
- Implemented in trading logic

**Take Profit**:
- Monitors unrealized PnL
- If PnL > `take_profit_threshold`, take profits
- Can reduce position size

**Spread Limits**:
- Won't trade if spread > `max_spread`
- Protects against low-liquidity markets

**Position Limits**:
- Maximum position size per market
- Maximum total exposure
- Prevents over-leveraging

---

## Quick Reference Guide

### Essential Commands

```powershell
# Start everything
.\START_DEV.ps1

# Start backend only
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start frontend only
cd frontend
npm run serve

# Start trading bot only
cd backend
.\venv\Scripts\Activate.ps1
python ..\main.py

# Check status
# Backend: http://localhost:8000/health
# Frontend: http://localhost:8080
# API Docs: http://localhost:8000/docs
```

### File Locations

| File/Directory | Purpose |
|----------------|---------|
| `.env` | Configuration (credentials, settings) |
| `backend/polymarket_bot.db` | SQLite database |
| `backend/main.py` | FastAPI backend server |
| `main.py` | Trading bot entry point |
| `trading.py` | Core trading logic |
| `poly_data/` | Core trading modules |
| `frontend/src/` | Vue.js frontend code |

### Key Configuration Files

- `.env`: Environment variables
- `backend/config.py`: Configuration class
- `backend/database.py`: Database models
- `frontend/vue.config.js`: Frontend configuration

### Important URLs

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## Next Steps

1. **Start with DRY_RUN**: Test everything in simulation mode
   - Set `DRY_RUN=true` in `.env`
   - Verify bot logic without real money
   - Monitor console logs

2. **Add Markets**: Start with 1-2 markets
   - Use web interface to add markets
   - Configure trading parameters
   - Set `is_active = true`

3. **Monitor Performance**: Watch PnL and order fills
   - Check Dashboard for statistics
   - Review Positions page
   - Monitor Orders page

4. **Adjust Parameters**: Fine-tune based on results
   - Start with conservative parameters
   - Gradually increase trade sizes
   - Optimize based on market conditions

5. **Scale Gradually**: Add more markets as you gain confidence
   - Add markets one at a time
   - Monitor each market's performance
   - Adjust parameters per market

6. **Go Live**: Switch to live trading
   - Set `DRY_RUN=false` in `.env`
   - Start with small trade sizes
   - Monitor closely for first few hours

---

## Support & Resources

### Documentation

- **Polymarket API Docs**: https://docs.polymarket.com/
- **WebSocket Docs**: See `docs/` folder in project
- **Code Comments**: Inline documentation in source files
- **This README**: Comprehensive guide (you're reading it!)

### Useful Tools

- **DB Browser for SQLite**: https://sqlitebrowser.org/
  - View and edit database
  - Useful for debugging

- **Postman**: https://www.postman.com/
  - Test API endpoints
  - Useful for debugging backend

- **WebSocket Client**: Browser extension or online tool
  - Test WebSocket connections
  - Monitor messages

### Getting Help

1. **Check Logs**: Most issues are visible in console output
2. **Review This README**: Troubleshooting section covers common issues
3. **Check Code Comments**: Inline documentation explains logic
4. **Enable Debug Mode**: Add logging to isolate issues
5. **Test Components**: Isolate which component is failing
6. **Check Polymarket Status**: https://status.polymarket.com/

### Community & Support

- Review Polymarket Discord/Community for API questions
- Check GitHub issues (if repository is public)
- Review code comments for implementation details

---

## Appendix

### Environment Variables Reference

Complete list of all environment variables:

```env
# Required
PK=your_private_key_here
BROWSER_ADDRESS=your_wallet_address_here

# Optional (with defaults)
DATABASE_URL=sqlite:///./polymarket_bot.db
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:8080
DRY_RUN=true
MAX_POSITION_SIZE=100
MAX_TRADE_SIZE=10
MIN_TRADE_SIZE=1
```

### Database Schema

**Markets Table**:
- `id`: Primary key
- `condition_id`: Polymarket condition ID
- `question`: Market question
- `token1`, `token2`: Token IDs
- `is_active`: Whether to trade this market
- `trading_mode`: MARKET_MAKING, POSITION_BUILDING, etc.

**TradingParams Table**:
- `market_id`: Foreign key to markets
- `trade_size`: Order size
- `max_size`: Maximum position
- `max_spread`: Maximum spread %
- `stop_loss_threshold`: Stop loss %
- `take_profit_threshold`: Take profit %

**Positions Table**:
- `token_id`: Token identifier
- `size`: Position size
- `avg_price`: Average entry price
- `unrealized_pnl`: Current PnL
- `realized_pnl`: Realized PnL

**Orders Table**:
- `order_id`: Polymarket order ID
- `token_id`: Token identifier
- `side_type`: BUY or SELL
- `price`: Order price
- `size`: Order size
- `status`: PENDING, FILLED, CANCELLED

### API Endpoints Reference

**Markets**:
- `GET /api/markets`: List all markets
- `POST /api/markets`: Create market
- `PUT /api/markets/{id}`: Update market
- `GET /api/markets/crypto/fetch`: Fetch crypto markets

**Trading**:
- `GET /api/trading/status`: Get bot status
- `POST /api/trading/start`: Start bot
- `POST /api/trading/stop`: Stop bot
- `GET /api/trading/diagnostics`: Get diagnostics

**Positions**:
- `GET /api/positions`: List positions
- `GET /api/positions/{id}`: Get position

**Orders**:
- `GET /api/orders`: List orders
- `GET /api/orders/active`: Get active orders

**Stats**:
- `GET /api/stats`: Get statistics
- `GET /api/stats/pnl/breakdown`: PnL breakdown

### WebSocket Message Formats

**Market Channel Subscription**:
```json
{
  "assets_ids": ["token1", "token2", ...],
  "type": "market"
}
```

**Market Channel Update**:
```json
{
  "asset_id": "token_id",
  "bids": [[price, size], ...],
  "asks": [[price, size], ...]
}
```

**User Channel Order Event**:
```json
{
  "event_type": "order",
  "type": "PLACEMENT|UPDATE|CANCELLATION",
  "id": "order_id",
  "asset_id": "token_id",
  "side": "BUY|SELL",
  "price": "0.50",
  "size_matched": "0",
  "original_size": "10"
}
```

**User Channel Trade Event**:
```json
{
  "event_type": "trade",
  "type": "TRADE",
  "id": "trade_id",
  "asset_id": "token_id",
  "side": "BUY|SELL",
  "price": "0.50",
  "size": "10",
  "status": "MATCHED|MINED|CONFIRMED|FAILED"
}
```

---

**⚠️ DISCLAIMER**: 

Trading involves substantial risk of loss. This bot is provided as-is without warranty. Use at your own risk. Always:

1. Test thoroughly in DRY_RUN mode before live trading
2. Start with small amounts
3. Monitor bot activity closely
4. Understand the risks involved
5. Never risk more than you can afford to lose

The authors and contributors are not responsible for any losses incurred from using this software.

