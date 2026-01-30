import os                           # Operating system interface
import sys                          # System-specific parameters and functions
import logging                      # Structured logging
from typing import Dict, Optional, Tuple, Any, List  # Type hints

# Set up logger
logger = logging.getLogger(__name__)

# Use our robust env loading utility that handles BOM and encoding issues on Windows
try:
    from poly_data.env_utils import load_dotenv_safe, validate_env_variables
    env_loaded = load_dotenv_safe()
    if not env_loaded:
        logger.warning("Could not load .env file using safe loader, trying fallback...")
        from dotenv import load_dotenv
        load_dotenv(encoding='utf-8-sig')
except ImportError:
    # Fallback to standard dotenv with utf-8-sig encoding (handles BOM)
    from dotenv import load_dotenv
    load_dotenv(encoding='utf-8-sig')

# Polymarket API client libraries
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, BalanceAllowanceParams, AssetType, PartialCreateOrderOptions, OrderType
from py_clob_client.constants import POLYGON

# Web3 libraries for blockchain interaction
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account

import requests                     # HTTP requests
import pandas as pd                 # Data analysis
import json                         # JSON processing
import subprocess                   # For calling external processes

from py_clob_client.clob_types import OpenOrderParams

# Smart contract ABIs
from poly_data.abis import NegRiskAdapterABI, ConditionalTokenABI, erc20_abi

# Import API constants
from poly_data.api_constants import ERROR_CODE_DESCRIPTIONS
from poly_data.rate_limiter import get_rate_limiter


class PolymarketClient:
    """
    Client for interacting with Polymarket's API and smart contracts.
    
    This class provides methods for:
    - Creating and managing orders
    - Querying order book data
    - Checking balances and positions
    - Merging positions
    
    The client connects to both the Polymarket API and the Polygon blockchain.
    """
    
    def __init__(self, pk='default') -> None:
        """
        Initialize the Polymarket client with API and blockchain connections.
        
        Args:
            pk (str, optional): Private key identifier, defaults to 'default'
        """
        host="https://clob.polymarket.com"

        # Get credentials from environment variables
        key=os.getenv("PK")
        browser_address = os.getenv("BROWSER_ADDRESS")

        # Don't print sensitive wallet information
        logger.info("Initializing Polymarket client...")
        print("Initializing Polymarket client...")
        
        # Validate private key
        if not key:
            raise ValueError(
                "PK (Private Key) not set in environment variables. "
                "This should be the private key of the EOA (Metamask wallet) that controls your Polymarket proxy wallet."
            )
        
        # Validate browser_address before using it
        # IMPORTANT: According to Polymarket docs, this should be the POLYMARKET_PROXY_ADDRESS
        # (the address shown below your profile picture on Polymarket.com), NOT your browser wallet address
        if not browser_address:
            raise ValueError(
                "BROWSER_ADDRESS not set in environment variables. "
                "This should be your POLYMARKET_PROXY_ADDRESS (shown below your profile picture on Polymarket.com), "
                "NOT your browser wallet (Metamask) address."
            )
        
        # Check for placeholder values
        if browser_address in ["your_wallet_address_here", "your_actual_wallet_address"]:
            raise ValueError(
                f"BROWSER_ADDRESS is set to placeholder value '{browser_address}'. "
                "Please set your POLYMARKET_PROXY_ADDRESS in your .env file. "
                "You can find this address below your profile picture on Polymarket.com (starts with 0x, 42 characters long)."
            )
        
        # Validate format
        if not browser_address.startswith("0x"):
            raise ValueError(
                f"Invalid address format: must start with '0x'. Got: {browser_address[:20]}..."
            )
        
        if len(browser_address) != 42:
            raise ValueError(
                f"Invalid address length: expected 42 characters (0x + 40 hex chars), got {len(browser_address)}. "
                f"Address: {browser_address[:20]}..."
            )
        
        # Verify private key corresponds to a valid address
        try:
            account = Account.from_key(key)
            derived_address = account.address
            logger.info(f"Private key corresponds to address: {derived_address[:10]}...{derived_address[-8:]}")
            print(f"ℹ️  Private key corresponds to EOA address: {derived_address[:10]}...{derived_address[-8:]}")
            print(f"ℹ️  Using proxy address (funder): {browser_address[:10]}...{browser_address[-8:]}")
            print(f"⚠️  NOTE: The proxy address should be the address shown below your profile picture on Polymarket.com")
        except Exception as e:
            logger.warning(f"Could not derive address from private key: {e}")
            print(f"⚠️  Warning: Could not verify private key format: {e}")
        
        chain_id=POLYGON
        try:
            self.browser_wallet=Web3.to_checksum_address(browser_address)
        except Exception as e:
            raise ValueError(
                f"Invalid address format: {str(e)}. "
                f"Please check your BROWSER_ADDRESS in .env file. Got: {browser_address[:20]}..."
            )

        # Initialize the Polymarket API client
        # According to docs: signature_type=2 for Browser Wallet (Metamask, Coinbase Wallet, etc)
        # signature_type=1 for Email/Magic account (POLY_PROXY)
        # signature_type=0 for EOA (direct trading with private key)
        # User logs in with Email/Google (Magic Link) -> signature_type=1
        self.signature_type = 1  # POLY_PROXY - Magic Link / Email login
        
        logger.info(f"Initializing ClobClient with signature_type={self.signature_type} (Browser Wallet)")
        logger.info(f"Funder address: {self.browser_wallet[:10]}...{self.browser_wallet[-8:]}")
        
        self.client = ClobClient(
            host=host,
            key=key,
            chain_id=chain_id,
            funder=self.browser_wallet,
            signature_type=self.signature_type
        )

        # Set up API credentials - required for L2 authentication
        # According to docs: create_or_derive_api_creds() creates or derives API credentials
        try:
            self.creds = self.client.create_or_derive_api_creds()
            if not self.creds:
                raise ValueError("Failed to create or derive API credentials")
            
            self.client.set_api_creds(creds=self.creds)
            logger.info("✅ API credentials created/derived and set successfully")
            
            # Validate credentials
            if not hasattr(self.creds, 'api_key') or not self.creds.api_key:
                logger.warning("⚠️  API key is missing in credentials")
            if not hasattr(self.creds, 'api_secret') or not self.creds.api_secret:
                logger.warning("⚠️  API secret is missing in credentials")
            if not hasattr(self.creds, 'api_passphrase') or not self.creds.api_passphrase:
                logger.warning("⚠️  API passphrase is missing in credentials")
                
        except Exception as e:
            logger.error(f"❌ Error creating/deriving API credentials: {e}")
            raise ValueError(f"Failed to set up API credentials: {e}")
        
        # Initialize Web3 connection to Polygon
        web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
        web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Set up USDC contract for balance checks
        from poly_data.api_constants import USDC_CONTRACT_ADDRESS
        self.usdc_contract = web3.eth.contract(
            address=USDC_CONTRACT_ADDRESS, 
            abi=erc20_abi
        )

        # Store key contract addresses (from api_constants)
        from poly_data.api_constants import (
            USDC_CONTRACT_ADDRESS,
            NEG_RISK_ADAPTER_ADDRESS,
            CONDITIONAL_TOKENS_ADDRESS
        )
        self.addresses = {
            'neg_risk_adapter': NEG_RISK_ADAPTER_ADDRESS,
            'collateral': USDC_CONTRACT_ADDRESS,
            'conditional_tokens': CONDITIONAL_TOKENS_ADDRESS
        }

        # Initialize contract interfaces
        self.neg_risk_adapter = web3.eth.contract(
            address=self.addresses['neg_risk_adapter'], 
            abi=NegRiskAdapterABI
        )

        self.conditional_tokens = web3.eth.contract(
            address=self.addresses['conditional_tokens'], 
            abi=ConditionalTokenABI
        )

        self.web3 = web3

    
    def create_order(self, marketId: str, action: str, price: float, size: float, neg_risk: Optional[bool] = None) -> Dict[str, Any]:
        """
        Create and submit a new order to the Polymarket order book.
        
        Args:
            marketId (str): ID of the market token to trade
            action (str): "BUY" or "SELL"
            price (float): Order price (0-1 range for prediction markets)
            size (float): Order size in USDC
            neg_risk (bool, optional): Whether this is a negative risk market. 
                                      If None, will be automatically determined from market data.
            
        Returns:
            dict: Response from the API containing order details, or empty dict on error
        """
        # Validate market and get market information
        market = None
        validation_result = None
        
        try:
            # Import validation service (lazy import to avoid circular dependencies)
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
            from services.order_validation_service import get_order_validator
            
            validator = get_order_validator()
            validation_result = validator.validate_market_for_order(marketId, action, neg_risk)
            
            if not validation_result.is_valid:
                error_msg = validation_result.error_message or "Market validation failed"
                error_code = validation_result.error_code.value if validation_result.error_code else "VALIDATION_ERROR"
                
                logger.error(f"Market validation failed: {error_msg} (code: {error_code})")
                print(f"❌ Market validation failed: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": error_code,
                    "validation_error": True
                }
            
            market = validation_result.market
            
            # Get neg_risk from market if not provided
            if neg_risk is None:
                neg_risk = validator.get_market_neg_risk(marketId)
                if neg_risk is None:
                    # Fallback to False if market not found (shouldn't happen after validation)
                    neg_risk = False
                    logger.warning(f"Could not determine neg_risk for token {marketId}, defaulting to False")
                else:
                    logger.info(f"Auto-detected neg_risk={neg_risk} from market data for token {marketId}")
            
            # Log warnings if any
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Market validation warning: {warning}")
                    
        except ImportError as e:
            # If validation service is not available, log warning but continue
            logger.warning(f"Order validation service not available: {e}. Proceeding without validation.")
            if neg_risk is None:
                neg_risk = False
        except Exception as e:
            # Don't fail order creation if validation fails, but log the error
            logger.warning(f"Error during market validation: {e}. Proceeding with order creation.")
            if neg_risk is None:
                neg_risk = False
        
        # Check DRY_RUN mode - validate early before any API calls
        try:
            from backend.config import Config
            is_dry_run = Config.is_dry_run()
            logger.info(f"DRY_RUN mode check: {is_dry_run} (from Config.is_dry_run())")
        except ImportError:
            is_dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
            logger.info(f"DRY_RUN mode check: {is_dry_run} (from environment variable)")
        
        if is_dry_run:
            # Convert marketId to string for safe slicing
            market_id_str = str(marketId)
            logger.debug(f"[DRY RUN] Would create {action} order: {size} @ ${price:.3f} for token {market_id_str[:20]}... (neg_risk={neg_risk})")
            print(f"[DRY RUN] Would create {action} order: {size} @ ${price:.3f} for token {market_id_str[:20]}... (neg_risk={neg_risk})")
            return {
                "dry_run": True, 
                "action": action, 
                "price": price, 
                "size": size, 
                "token_id": marketId,
                "neg_risk": neg_risk,
                "market_id": market.id if market else None
            }
        
        # DRY_RUN is False - proceed with real API call
        # Convert marketId to string for safe slicing
        market_id_str = str(marketId)
        logger.info(f"🔴 LIVE TRADING: Creating real {action} order: {size} @ ${price:.3f} for token {market_id_str[:20]}... (neg_risk={neg_risk})")
        
        # Create order parameters
        # According to docs: neg_risk flag must be set correctly for negative risk markets
        # If neg_risk=True, use PartialCreateOrderOptions(neg_risk=True)
        # If neg_risk=False (default), create order normally
        
        # Convert marketId to string for safe slicing
        market_id_str = str(marketId)
        logger.info(f"Creating order: token={market_id_str[:20]}..., action={action}, price={price}, size={size}, neg_risk={neg_risk}")
        
        order_args = OrderArgs(
            token_id=str(marketId),
            price=price,
            size=size,
            side=action
        )

        signed_order = None

        # Handle regular vs negative risk markets differently
        # According to docs: Negrisk Markets require an additional flag in the OrderArgs negrisk=False
        # But in py-clob-client, we use PartialCreateOrderOptions(neg_risk=True) for neg risk markets
        if neg_risk:
            logger.info("Using PartialCreateOrderOptions(neg_risk=True) for negative risk market")
            signed_order = self.client.create_order(order_args, options=PartialCreateOrderOptions(neg_risk=True))
        else:
            logger.info("Creating order for regular (non-negative risk) market")
            signed_order = self.client.create_order(order_args)
            
        try:
            # Apply rate limiting for CLOB POST /order endpoint
            # Sustained: 40/s, Burst: 240/s
            rate_limiter = get_rate_limiter()
            rate_limiter.wait_if_needed_sync('clob_post_order')
            
            # Submit the signed order to the API with GTC (Good-Till-Cancelled) order type
            resp = self.client.post_order(signed_order, OrderType.GTC)
            rate_limiter.record_request('clob_post_order')
            
            # Validate response according to Polymarket API documentation
            # Docs: Response format includes: success, errorMsg, orderId, orderHashes, status
            # Status values: matched, live, delayed, unmatched
            if isinstance(resp, dict):
                success = resp.get('success', False)
                error_msg = resp.get('errorMsg', '')
                order_id = resp.get('orderId', '')
                order_hashes = resp.get('orderHashes', [])
                status = resp.get('status', 'unknown')  # matched, live, delayed, unmatched
                
                if not success:
                    # Map error message to user-friendly description according to docs
                    # All error codes are defined in api_constants.py
                    error_message = error_msg if error_msg else 'Unknown error occurred'
                    error_description = ERROR_CODE_DESCRIPTIONS.get(error_msg, error_message)
                    
                    # Log the error code for debugging
                    if error_msg:
                        logger.debug(f"Error code received: {error_msg}")
                    
                    logger.error(f"Order placement failed: {error_description} (code: {error_msg}, order_id: {order_id})")
                    print(f"❌ Order placement failed: {error_description}")
                    if error_msg and error_msg != error_description:
                        print(f"   Error code: {error_msg}")
                    if order_id:
                        print(f"   Order ID: {order_id}")
                    
                    # Check for account restriction errors
                    if 'closed only mode' in error_msg.lower() or 'closed-only' in error_msg.lower():
                        # Set global flag to prevent further order attempts
                        try:
                            import poly_data.global_state as global_state
                            global_state.account_in_closed_only_mode = True
                        except Exception:
                            pass
                        
                        print("")
                        print("⚠️  ACCOUNT RESTRICTION: Your account is in 'closed only mode'")
                        print("")
                        print("   This means:")
                        print("   • You can only CLOSE existing positions (sell what you own)")
                        print("   • You CANNOT open new positions (cannot place new buy orders)")
                        print("")
                        print("   🔧 How to resolve:")
                        print("   1. Contact Polymarket support to remove the restriction")
                        print("   2. Check your account status on Polymarket.com")
                        print("   3. This restriction is usually temporary and may be lifted automatically")
                        print("")
                        print("   💡 Workaround:")
                        print("   • You can still close existing positions")
                        print("   • Wait for the restriction to be lifted before trading again")
                        print("")
                        print("   ⏸️  Order creation attempts will be paused until restriction is lifted")
                        print("")
                        logger.error("Account is in closed only mode - cannot create new orders")
                    # Check for signature-related errors and provide detailed diagnostics
                    elif 'invalid signature' in error_msg.lower() or 'signature' in error_msg.lower():
                        logger.error("⚠️  SIGNATURE ERROR - Detailed diagnostics:")
                        logger.error(f"   1. Funder (Proxy) address: {self.browser_wallet[:10]}...{self.browser_wallet[-8:]}")
                        logger.error(f"   2. Signature type: {self.signature_type} (Browser Wallet)")
                        logger.error(f"   3. NegRisk flag: {neg_risk}")
                        logger.error(f"   4. API credentials set: {hasattr(self, 'creds') and self.creds is not None}")
                        
                        # Try to get the EOA address from private key
                        try:
                            account = Account.from_key(os.getenv("PK"))
                            eoa_address = account.address
                            logger.error(f"   5. EOA address (from private key): {eoa_address[:10]}...{eoa_address[-8:]}")
                        except:
                            logger.error(f"   5. Could not derive EOA address from private key")
                        
                        print("⚠️  SIGNATURE ERROR - Common causes and solutions:")
                        print("")
                        print("   🔍 CHECK 1: BROWSER_ADDRESS should be your POLYMARKET_PROXY_ADDRESS")
                        print("      - This is the address shown BELOW your profile picture on Polymarket.com")
                        print("      - NOT your Metamask/browser wallet address")
                        print(f"      - Current value: {self.browser_wallet[:10]}...{self.browser_wallet[-8:]}")
                        print("")
                        print("   🔍 CHECK 2: Private Key (PK) should be your EOA (Metamask) private key")
                        print("      - This is the private key of the wallet that CONTROLS your proxy wallet")
                        print("      - Export from Metamask or from https://reveal.magic.link/polymarket")
                        print("")
                        print("   🔍 CHECK 3: Verify the proxy address is correct")
                        print("      - Go to Polymarket.com and check the address below your profile picture")
                        print("      - This should match BROWSER_ADDRESS in your .env file")
                        print("")
                        print("   🔍 CHECK 4: NegRisk flag")
                        print(f"      - Current value: {neg_risk}")
                        print("      - Some markets require neg_risk=True, others require neg_risk=False")
                        print("      - Check the market details to determine the correct value")
                        print("")
                        print("   📚 For more help, see: https://docs.polymarket.com/developers/clob-api/your-first-order")
                    
                    return {
                        "success": False,
                        "error": error_description,
                        "error_code": error_msg,
                        "orderId": order_id
                    }
                
                # Order placed successfully
                # Handle status field according to docs
                status_description = {
                    'matched': 'Order placed and matched with existing resting order',
                    'live': 'Order placed and resting on the book',
                    'delayed': 'Order marketable, but subject to matching delay',
                    'unmatched': 'Order marketable, but failure delaying, placement successful'
                }.get(status, f'Unknown status: {status}')
                
                logger.info(f"Order placed successfully: {order_id} (status: {status}, hashes: {order_hashes})")
                print(f"✅ Order placed successfully: {order_id}")
                print(f"   Status: {status} - {status_description}")
                if order_hashes:
                    print(f"   Order hashes: {order_hashes}")
                
                return {
                    "success": True,
                    "orderId": order_id,
                    "orderHashes": order_hashes,
                    "status": status,
                    "errorMsg": error_msg
                }
            else:
                # Response is not a dict, return as-is for backward compatibility
                return resp
                
        except Exception as ex:
            # Handle Polymarket API exceptions
            error_msg = str(ex)
            error_type = type(ex).__name__
            
            # Check if it's a PolyApiException (from py_clob_client)
            if 'PolyApiException' in error_type or 'status_code' in str(ex):
                # Extract status code and error message if available
                if hasattr(ex, 'status_code'):
                    status_code = ex.status_code
                    error_message = f"API Error (HTTP {status_code}): {error_msg}"
                else:
                    error_message = f"API Error: {error_msg}"
                
                logger.error(f"Polymarket API error: {error_message} (type: {error_type})")
                print(f"❌ Polymarket API error: {error_message}")
                
                # Provide helpful suggestions based on common errors
                if 'closed only mode' in error_msg.lower() or 'closed-only' in error_msg.lower():
                    # Set global flag to prevent further order attempts
                    try:
                        import poly_data.global_state as global_state
                        global_state.account_in_closed_only_mode = True
                    except Exception:
                        pass
                    
                    print("")
                    print("⚠️  ACCOUNT RESTRICTION: Your account is in 'closed only mode'")
                    print("")
                    print("   This means:")
                    print("   • You can only CLOSE existing positions (sell what you own)")
                    print("   • You CANNOT open new positions (cannot place new buy orders)")
                    print("")
                    print("   🔧 How to resolve:")
                    print("   1. Contact Polymarket support to remove the restriction")
                    print("   2. Check your account status on Polymarket.com")
                    print("   3. This restriction is usually temporary and may be lifted automatically")
                    print("")
                    print("   💡 Workaround:")
                    print("   • You can still close existing positions")
                    print("   • Wait for the restriction to be lifted before trading again")
                    print("")
                    print("   ⏸️  Order creation attempts will be paused until restriction is lifted")
                    print("")
                    logger.error("Account is in closed only mode - cannot create new orders")
                elif 'invalid signature' in error_msg.lower() or 'signature' in error_msg.lower():
                    logger.error("⚠️  SIGNATURE ERROR - Detailed diagnostics:")
                    logger.error(f"   1. Funder (Proxy) address: {self.browser_wallet[:10]}...{self.browser_wallet[-8:]}")
                    logger.error(f"   2. Signature type: {self.signature_type} (Browser Wallet)")
                    logger.error(f"   3. NegRisk flag: {neg_risk}")
                    logger.error(f"   4. API credentials set: {hasattr(self, 'creds') and self.creds is not None}")
                    
                    # Try to get the EOA address from private key
                    try:
                        account = Account.from_key(os.getenv("PK"))
                        eoa_address = account.address
                        logger.error(f"   5. EOA address (from private key): {eoa_address[:10]}...{eoa_address[-8:]}")
                    except:
                        logger.error(f"   5. Could not derive EOA address from private key")
                    
                    print("⚠️  SIGNATURE ERROR - Common causes and solutions:")
                    print("")
                    print("   🔍 CHECK 1: BROWSER_ADDRESS should be your POLYMARKET_PROXY_ADDRESS")
                    print("      - This is the address shown BELOW your profile picture on Polymarket.com")
                    print("      - NOT your Metamask/browser wallet address")
                    print(f"      - Current value: {self.browser_wallet[:10]}...{self.browser_wallet[-8:]}")
                    print("")
                    print("   🔍 CHECK 2: Private Key (PK) should be your EOA (Metamask) private key")
                    print("      - This is the private key of the wallet that CONTROLS your proxy wallet")
                    print("      - Export from Metamask or from https://reveal.magic.link/polymarket")
                    print("")
                    print("   🔍 CHECK 3: Verify the proxy address is correct")
                    print("      - Go to Polymarket.com and check the address below your profile picture")
                    print("      - This should match BROWSER_ADDRESS in your .env file")
                    print("")
                    print("   🔍 CHECK 4: NegRisk flag")
                    print(f"      - Current value: {neg_risk}")
                    print("      - Some markets require neg_risk=True, others require neg_risk=False")
                    print("      - Check the market details to determine the correct value")
                    print("")
                    print("   📚 For more help, see: https://docs.polymarket.com/developers/clob-api/your-first-order")
                elif 'not enough balance' in error_msg.lower() or 'allowance' in error_msg.lower():
                    logger.warning("Insufficient balance or allowance")
                    print("   💡 Tip: Ensure you have sufficient USDC balance and allowances set")
                elif '400' in error_msg or 'bad request' in error_msg.lower():
                    logger.warning("Bad request - check order parameters")
                    print("   💡 Tip: Check order parameters (price, size, token_id) are valid")
                
                return {"success": False, "error": error_message, "error_type": error_type}
            else:
                # Generic exception
                logger.error(f"Error creating order: {error_msg} (type: {error_type})")
                print(f"❌ Error creating order: {error_msg}")
                return {"success": False, "error": error_msg, "error_type": error_type}

    def get_order_book(self, market: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get the current order book for a specific market.
        
        Args:
            market (str): Market ID to query
            
        Returns:
            tuple: (bids_df, asks_df) - DataFrames containing bid and ask orders
        """
        # Apply rate limiting for CLOB /book endpoint (200 requests / 10s)
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('clob_book')
        
        orderBook = self.client.get_order_book(market)
        rate_limiter.record_request('clob_book')
        
        return pd.DataFrame(orderBook.bids).astype(float), pd.DataFrame(orderBook.asks).astype(float)


    def get_usdc_balance(self) -> float:
        """
        Get the USDC balance of the connected wallet.
        
        Returns:
            float: USDC balance in decimal format
        """
        return self.usdc_contract.functions.balanceOf(self.browser_wallet).call() / 10**6
     
    def get_pos_balance(self) -> float:
        """
        Get the total value of all positions for the connected wallet.
        
        Returns:
            float: Total position value in USDC
        """
        try:
            # Apply rate limiting for Data API (200 requests / 10s)
            rate_limiter = get_rate_limiter()
            rate_limiter.wait_if_needed_sync('data_api_general')
            
            res = requests.get(f'https://data-api.polymarket.com/value?user={self.browser_wallet}')
            rate_limiter.record_request('data_api_general')
            
            data = res.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                # Expected format: {"value": 123.45}
                return float(data.get('value', 0.0))
            elif isinstance(data, list):
                # If response is a list, try to extract value from first item
                if len(data) > 0 and isinstance(data[0], dict):
                    return float(data[0].get('value', 0.0))
                return 0.0
            elif isinstance(data, (int, float)):
                # If response is directly a number
                return float(data)
            else:
                print(f"Warning: Unexpected response format from positions API: {type(data)}")
                return 0.0
        except Exception as e:
            print(f"Error fetching positions balance: {e}")
            return 0.0

    def get_total_balance(self) -> float:
        """
        Get the combined value of USDC balance and all positions.
        
        Returns:
            float: Total account value in USDC
        """
        return self.get_usdc_balance() + self.get_pos_balance()

    def get_all_positions(self) -> pd.DataFrame:
        """
        Get all positions for the connected wallet across all markets.
        
        Returns:
            DataFrame: All positions with details like market, size, avgPrice
        """
        # Apply rate limiting for Data API (200 requests / 10s)
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('data_api_general')
        
        res = requests.get(f'https://data-api.polymarket.com/positions?user={self.browser_wallet}')
        rate_limiter.record_request('data_api_general')
        
        return pd.DataFrame(res.json())
    
    def get_raw_position(self, tokenId: str) -> int:
        """
        Get the raw token balance for a specific market outcome token.
        
        Args:
            tokenId (int): Token ID to query
            
        Returns:
            int: Raw token amount (before decimal conversion)
        """
        return int(self.conditional_tokens.functions.balanceOf(self.browser_wallet, int(tokenId)).call())

    def get_position(self, tokenId: str) -> Tuple[int, float]:
        """
        Get both raw and formatted position size for a token.
        
        Args:
            tokenId (int): Token ID to query
            
        Returns:
            tuple: (raw_position, shares) - Raw token amount and decimal shares
                   Shares less than 1 are treated as 0 to avoid dust amounts
        """
        raw_position = self.get_raw_position(tokenId)
        shares = float(raw_position / 1e6)

        # Ignore very small positions (dust)
        if shares < 1:
            shares = 0

        return raw_position, shares
    
    def get_all_orders(self) -> pd.DataFrame:
        """
        Get all open orders for the connected wallet.
        
        Returns:
            DataFrame: All open orders with their details
        """
        # Apply rate limiting for CLOB Ledger /orders endpoint (300 requests / 10s)
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('clob_ledger')
        
        orders_df = pd.DataFrame(self.client.get_orders())
        rate_limiter.record_request('clob_ledger')

        # Convert numeric columns to float
        for col in ['original_size', 'size_matched', 'price']:
            if col in orders_df.columns:
                orders_df[col] = orders_df[col].astype(float)

        return orders_df
    
    def get_market_orders(self, market: str) -> pd.DataFrame:
        """
        Get all open orders for a specific market.
        
        Args:
            market (str): Market ID to query
            
        Returns:
            DataFrame: Open orders for the specified market
        """
        # Apply rate limiting for CLOB Ledger /orders endpoint (300 requests / 10s)
        rate_limiter = get_rate_limiter()
        rate_limiter.wait_if_needed_sync('clob_ledger')
        
        orders_df = pd.DataFrame(self.client.get_orders(OpenOrderParams(
            market=market,
        )))
        rate_limiter.record_request('clob_ledger')

        # Convert numeric columns to float
        for col in ['original_size', 'size_matched', 'price']:
            if col in orders_df.columns:
                orders_df[col] = orders_df[col].astype(float)

        return orders_df
    

    def cancel_all_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Cancel all orders for a specific asset token.
        
        Args:
            asset_id (str): Asset token ID
            
        Returns:
            dict: Response with canceled and not_canceled orders, or empty dict on error
        """
        # Check DRY_RUN mode
        try:
            from backend.config import Config
            is_dry_run = Config.is_dry_run()
        except ImportError:
            is_dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        
        if is_dry_run:
            # Convert asset_id to string for safe slicing (in case it's an int)
            asset_id_str = str(asset_id)
            logger.debug(f"[DRY RUN] Would cancel all orders for asset: {asset_id_str[:20]}...")
            print(f"[DRY RUN] Would cancel all orders for asset: {asset_id_str[:20]}...")
            return {"dry_run": True, "asset_id": asset_id}
        
        try:
            # Apply rate limiting for CLOB DELETE /cancel-market-orders endpoint
            # Sustained: 20/s, Burst: 80/s
            rate_limiter = get_rate_limiter()
            rate_limiter.wait_if_needed_sync('clob_delete_orders')
            
            resp = self.client.cancel_market_orders(asset_id=str(asset_id))
            rate_limiter.record_request('clob_delete_orders')
            
            # Validate response according to Polymarket API documentation
            # Response format: {"canceled": string[], "not_canceled": {order_id: reason}}
            if isinstance(resp, dict):
                canceled = resp.get('canceled', [])
                not_canceled = resp.get('not_canceled', {})
                
                if canceled:
                    # Convert asset_id to string for safe slicing
                    asset_id_str = str(asset_id)
                    logger.info(f"Canceled {len(canceled)} order(s) for asset: {asset_id_str[:20]}...")
                    print(f"✅ Canceled {len(canceled)} order(s) for asset: {asset_id_str[:20]}...")
                
                if not_canceled:
                    # Convert asset_id to string for safe slicing
                    asset_id_str = str(asset_id)
                    logger.warning(f"{len(not_canceled)} order(s) could not be canceled for asset: {asset_id_str[:20]}...")
                    print(f"⚠️  {len(not_canceled)} order(s) could not be canceled:")
                    for order_id, reason in not_canceled.items():
                        logger.warning(f"Order {order_id[:20]}... could not be canceled: {reason}")
                        print(f"   Order {order_id[:20]}...: {reason}")
                
                return {
                    "canceled": canceled,
                    "not_canceled": not_canceled
                }
            else:
                # Response is not a dict, return as-is for backward compatibility
                return resp
                
        except Exception as ex:
            # Handle Polymarket API exceptions
            error_msg = str(ex)
            error_type = type(ex).__name__
            
            if 'PolyApiException' in error_type or 'status_code' in str(ex):
                if hasattr(ex, 'status_code'):
                    status_code = ex.status_code
                    error_message = f"API Error (HTTP {status_code}): {error_msg}"
                else:
                    error_message = f"API Error: {error_msg}"
                logger.error(f"Polymarket API error cancelling orders: {error_message}")
                print(f"❌ Polymarket API error cancelling orders: {error_message}")
            else:
                error_message = error_msg
                logger.error(f"Error cancelling orders: {error_message}")
                print(f"❌ Error cancelling orders: {error_message}")
            
            return {"error": error_message, "error_type": error_type}


    
    def cancel_all_market(self, marketId: str) -> Optional[Dict[str, Any]]:
        """
        Cancel all orders in a specific market.
        
        Args:
            marketId (str): Market ID
            
        Returns:
            dict: Response with canceled and not_canceled orders, or empty dict on error
        """
        # Check DRY_RUN mode
        try:
            from backend.config import Config
            is_dry_run = Config.is_dry_run()
        except ImportError:
            is_dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        
        if is_dry_run:
            print(f"[DRY RUN] Would cancel all orders for market: {marketId[:20]}...")
            return {"dry_run": True, "market_id": marketId}
        
        try:
            # Apply rate limiting for CLOB DELETE /cancel-market-orders endpoint
            # Sustained: 20/s, Burst: 80/s
            rate_limiter = get_rate_limiter()
            rate_limiter.wait_if_needed_sync('clob_delete_orders')
            
            resp = self.client.cancel_market_orders(market=marketId)
            rate_limiter.record_request('clob_delete_orders')
            
            # Validate response according to Polymarket API documentation
            # Response format: {"canceled": string[], "not_canceled": {order_id: reason}}
            if isinstance(resp, dict):
                canceled = resp.get('canceled', [])
                not_canceled = resp.get('not_canceled', {})
                
                if canceled:
                    # Convert marketId to string for safe slicing
                    market_id_str = str(marketId)
                    print(f"✅ Canceled {len(canceled)} order(s) for market: {market_id_str[:20]}...")
                
                if not_canceled:
                    print(f"⚠️  {len(not_canceled)} order(s) could not be canceled:")
                    for order_id, reason in not_canceled.items():
                        print(f"   Order {order_id[:20]}...: {reason}")
                
                return {
                    "canceled": canceled,
                    "not_canceled": not_canceled
                }
            else:
                # Response is not a dict, return as-is for backward compatibility
                return resp
                
        except Exception as ex:
            # Handle Polymarket API exceptions
            error_msg = str(ex)
            error_type = type(ex).__name__
            
            if 'PolyApiException' in error_type or 'status_code' in str(ex):
                if hasattr(ex, 'status_code'):
                    status_code = ex.status_code
                    error_message = f"API Error (HTTP {status_code}): {error_msg}"
                else:
                    error_message = f"API Error: {error_msg}"
                print(f"❌ Polymarket API error cancelling market orders: {error_message}")
            else:
                error_message = error_msg
                print(f"❌ Error cancelling market orders: {error_message}")
            
            return {"error": error_message, "error_type": error_type}

    
    def merge_positions(self, amount_to_merge: int, condition_id: str, is_neg_risk_market: bool) -> str:
        """
        Merge positions in a market to recover collateral.
        
        This function calls the external poly_merger Node.js script to execute
        the merge operation on-chain. When you hold both YES and NO positions
        in the same market, merging them recovers your USDC.
        
        Args:
            amount_to_merge (int): Raw token amount to merge (before decimal conversion)
            condition_id (str): Market condition ID
            is_neg_risk_market (bool): Whether this is a negative risk market
            
        Returns:
            str: Transaction hash or output from the merge script
            
        Raises:
            Exception: If the merge operation fails
        """
        amount_to_merge_str = str(amount_to_merge)

        # Prepare the command to run the JavaScript script
        node_command = f'node poly_merger/merge.js {amount_to_merge_str} {condition_id} {"true" if is_neg_risk_market else "false"}'
        print(node_command)

        # Run the command and capture the output
        result = subprocess.run(node_command, shell=True, capture_output=True, text=True)
        
        # Check if there was an error
        if result.returncode != 0:
            print("Error:", result.stderr)
            raise Exception(f"Error in merging positions: {result.stderr}")
        
        print("Done merging")

        # Return the transaction hash or output
        return result.stdout