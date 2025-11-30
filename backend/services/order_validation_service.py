"""
Order Validation Service

Validates market data before order creation to ensure data integrity.
"""
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database import Market
from services.market_mapping_service import get_market_mapper


class ValidationErrorCode(Enum):
    """Validation error codes"""
    MARKET_NOT_FOUND = "MARKET_NOT_FOUND"
    MARKET_INACTIVE = "MARKET_INACTIVE"
    TOKEN_NOT_IN_MARKET = "TOKEN_NOT_IN_MARKET"
    INVALID_NEG_RISK = "INVALID_NEG_RISK"
    INVALID_SIDE = "INVALID_SIDE"
    TRADING_DISABLED = "TRADING_DISABLED"
    INVALID_TRADING_PARAMS = "INVALID_TRADING_PARAMS"


@dataclass
class ValidationResult:
    """Result of market validation"""
    is_valid: bool
    error_code: Optional[ValidationErrorCode] = None
    error_message: Optional[str] = None
    market: Optional[Market] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class OrderValidationService:
    """
    Service for validating market data before order creation.
    """
    
    def __init__(self):
        """Initialize the validation service"""
        self.mapper = get_market_mapper()
    
    def validate_market_for_order(
        self, 
        token_id: str, 
        side: str,
        neg_risk: Optional[bool] = None
    ) -> ValidationResult:
        """
        Validate market for order creation.
        
        Args:
            token_id: Token ID for the order
            side: Order side ('BUY' or 'SELL')
            neg_risk: Expected neg_risk value (optional, will be validated if provided)
            
        Returns:
            ValidationResult with validation status and market information
        """
        if not token_id:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.MARKET_NOT_FOUND,
                error_message="Token ID is required"
            )
        
        if side not in ['BUY', 'SELL']:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.INVALID_SIDE,
                error_message=f"Invalid side: {side}. Must be 'BUY' or 'SELL'"
            )
        
        # Get market by token ID
        market = self.mapper.get_market_by_token_id(token_id)
        
        if not market:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.MARKET_NOT_FOUND,
                error_message=f"Market not found for token_id: {token_id}"
            )
        
        # Check if market is active
        if not market.is_active:
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.MARKET_INACTIVE,
                error_message=f"Market is not active: {market.question} (ID: {market.id})",
                market=market
            )
        
        # Verify token belongs to this market
        token_id_str = str(token_id)
        if token_id_str != str(market.token1) and token_id_str != str(market.token2):
            return ValidationResult(
                is_valid=False,
                error_code=ValidationErrorCode.TOKEN_NOT_IN_MARKET,
                error_message=f"Token {token_id} does not belong to market {market.condition_id}",
                market=market
            )
        
        # Validate neg_risk flag
        market_neg_risk = market.neg_risk.upper() == 'TRUE' if market.neg_risk else False
        
        if neg_risk is not None:
            if neg_risk != market_neg_risk:
                return ValidationResult(
                    is_valid=False,
                    error_code=ValidationErrorCode.INVALID_NEG_RISK,
                    error_message=(
                        f"neg_risk mismatch: expected {market_neg_risk} (from market), "
                        f"got {neg_risk}. Market neg_risk: {market.neg_risk}"
                    ),
                    market=market
                )
        
        # Check if trading is enabled for this side
        side_to_trade = market.side_to_trade or 'BOTH'
        if side_to_trade != 'BOTH':
            # Determine which token corresponds to which side
            is_token1 = token_id_str == str(market.token1)
            expected_side = 'YES' if is_token1 else 'NO'
            
            if side_to_trade == 'YES' and not is_token1:
                return ValidationResult(
                    is_valid=False,
                    error_code=ValidationErrorCode.TRADING_DISABLED,
                    error_message=(
                        f"Trading is disabled for token {token_id}. "
                        f"Market is configured to trade only YES side (token1)"
                    ),
                    market=market
                )
            elif side_to_trade == 'NO' and is_token1:
                return ValidationResult(
                    is_valid=False,
                    error_code=ValidationErrorCode.TRADING_DISABLED,
                    error_message=(
                        f"Trading is disabled for token {token_id}. "
                        f"Market is configured to trade only NO side (token2)"
                    ),
                    market=market
                )
        
        # Check trading parameters
        warnings = []
        # Handle detached instance - trading_params might not be loaded
        try:
            trading_params = market.trading_params
            if not trading_params:
                warnings.append("Market has no trading parameters configured")
            else:
                if trading_params.trade_size <= 0:
                    warnings.append("Trade size is not configured or invalid")
                if trading_params.max_size <= 0:
                    warnings.append("Max size is not configured or invalid")
                if trading_params.min_size <= 0:
                    warnings.append("Min size is not configured or invalid")
        except Exception:
            # If trading_params is not accessible (detached instance), just add warning
            warnings.append("Could not access trading parameters (may need to reload from database)")
        
        # All validations passed
        return ValidationResult(
            is_valid=True,
            market=market,
            warnings=warnings
        )
    
    def get_market_neg_risk(self, token_id: str) -> Optional[bool]:
        """
        Get neg_risk flag for a market by token ID.
        
        Args:
            token_id: Token ID to lookup
            
        Returns:
            neg_risk boolean value, or None if market not found
        """
        market = self.mapper.get_market_by_token_id(token_id)
        if not market:
            return None
        
        return market.neg_risk.upper() == 'TRUE' if market.neg_risk else False
    
    def get_market_for_token(self, token_id: str) -> Optional[Market]:
        """
        Get market object for a token ID.
        
        Args:
            token_id: Token ID to lookup
            
        Returns:
            Market object or None if not found
        """
        return self.mapper.get_market_by_token_id(token_id)


# Global singleton instance
_validation_instance: Optional[OrderValidationService] = None
_validation_lock = __import__('threading').Lock()


def get_order_validator() -> OrderValidationService:
    """
    Get the global OrderValidationService instance (singleton pattern).
    
    Returns:
        OrderValidationService instance
    """
    global _validation_instance
    if _validation_instance is None:
        with _validation_lock:
            if _validation_instance is None:
                _validation_instance = OrderValidationService()
    return _validation_instance

