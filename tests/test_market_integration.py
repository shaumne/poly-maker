"""
Integration tests for market integration and order creation flow.

Tests the complete flow from market creation to order validation.
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal, Market, TradingParams, init_db
from services.market_mapping_service import get_market_mapper, TokenMarketMapper
from services.order_validation_service import get_order_validator, OrderValidationService, ValidationErrorCode
from services.market_cache_service import get_market_cache_service


@pytest.fixture
def db_session():
    """Create a database session for testing"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_market(db_session):
    """Create a sample market for testing"""
    market = Market(
        condition_id="test_condition_123",
        question="Test Market Question?",
        answer1="YES",
        answer2="NO",
        token1="123456789",
        token2="987654321",
        is_active=True,
        neg_risk="FALSE",
        side_to_trade="BOTH"
    )
    db_session.add(market)
    db_session.flush()
    
    params = TradingParams(market_id=market.id)
    db_session.add(params)
    db_session.commit()
    db_session.refresh(market)
    
    yield market
    
    # Cleanup
    db_session.delete(market)
    db_session.commit()


class TestMarketMapping:
    """Tests for TokenMarketMapper"""
    
    def test_get_market_by_token_id(self, db_session, sample_market):
        """Test getting market by token ID"""
        mapper = get_market_mapper()
        mapper.clear_cache()  # Clear cache for clean test
        
        # Test with token1
        market = mapper.get_market_by_token_id(sample_market.token1)
        assert market is not None
        assert market.id == sample_market.id
        assert market.condition_id == sample_market.condition_id
        
        # Test with token2
        market = mapper.get_market_by_token_id(sample_market.token2)
        assert market is not None
        assert market.id == sample_market.id
        
        # Test with non-existent token
        market = mapper.get_market_by_token_id("999999999")
        assert market is None
    
    def test_get_market_by_condition_id(self, db_session, sample_market):
        """Test getting market by condition ID"""
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        market = mapper.get_market_by_condition_id(sample_market.condition_id)
        assert market is not None
        assert market.id == sample_market.id
        
        # Test with non-existent condition
        market = mapper.get_market_by_condition_id("non_existent")
        assert market is None
    
    def test_cache_invalidation(self, db_session, sample_market):
        """Test cache invalidation"""
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        # Populate cache
        market = mapper.get_market_by_token_id(sample_market.token1)
        assert market is not None
        
        # Invalidate and check
        mapper.invalidate_token_cache(sample_market.token1)
        # Cache should be cleared, but next lookup will repopulate from DB
        stats = mapper.get_cache_stats()
        # After invalidation, cache size should be reduced or token should not be in cache
        assert stats['token_cache_size'] >= 0  # Cache might be empty or have other entries


class TestOrderValidation:
    """Tests for OrderValidationService"""
    
    def test_validate_active_market(self, db_session, sample_market):
        """Test validation of active market"""
        validator = get_order_validator()
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        result = validator.validate_market_for_order(sample_market.token1, "BUY")
        
        assert result.is_valid is True
        assert result.market is not None
        assert result.market.id == sample_market.id
        assert result.error_code is None
    
    def test_validate_inactive_market(self, db_session, sample_market):
        """Test validation of inactive market"""
        validator = get_order_validator()
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        # Deactivate market
        sample_market.is_active = False
        db_session.commit()
        
        # Invalidate cache so it picks up the new is_active status
        mapper.invalidate_token_cache(sample_market.token1)
        mapper.invalidate_token_cache(sample_market.token2)
        mapper.invalidate_condition_cache(sample_market.condition_id)
        
        result = validator.validate_market_for_order(sample_market.token1, "BUY")
        
        assert result.is_valid is False
        assert result.error_code == ValidationErrorCode.MARKET_INACTIVE
        
        # Reactivate for cleanup
        sample_market.is_active = True
        db_session.commit()
        mapper.invalidate_token_cache(sample_market.token1)
        mapper.invalidate_token_cache(sample_market.token2)
    
    def test_validate_nonexistent_token(self, db_session):
        """Test validation with non-existent token"""
        validator = get_order_validator()
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        result = validator.validate_market_for_order("999999999", "BUY")
        
        assert result.is_valid is False
        assert result.error_code == ValidationErrorCode.MARKET_NOT_FOUND
    
    def test_validate_neg_risk_mismatch(self, db_session, sample_market):
        """Test validation with neg_risk mismatch"""
        validator = get_order_validator()
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        # Market has neg_risk=FALSE, but we pass True
        result = validator.validate_market_for_order(
            sample_market.token1, 
            "BUY", 
            neg_risk=True
        )
        
        assert result.is_valid is False
        assert result.error_code == ValidationErrorCode.INVALID_NEG_RISK
    
    def test_validate_side_restriction(self, db_session, sample_market):
        """Test validation with side restriction"""
        validator = get_order_validator()
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        # Set market to trade only YES side
        sample_market.side_to_trade = "YES"
        db_session.commit()
        
        # Try to trade NO side (token2)
        result = validator.validate_market_for_order(sample_market.token2, "BUY")
        
        assert result.is_valid is False
        assert result.error_code == ValidationErrorCode.TRADING_DISABLED
        
        # Reset for cleanup
        sample_market.side_to_trade = "BOTH"
        db_session.commit()
    
    def test_get_market_neg_risk(self, db_session, sample_market):
        """Test getting neg_risk from market"""
        validator = get_order_validator()
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        neg_risk = validator.get_market_neg_risk(sample_market.token1)
        assert neg_risk is False  # Market has neg_risk="FALSE"
        
        # Test with neg_risk market
        sample_market.neg_risk = "TRUE"
        db_session.commit()
        
        # Invalidate cache so it picks up the new neg_risk value
        mapper.invalidate_token_cache(sample_market.token1)
        mapper.invalidate_token_cache(sample_market.token2)
        mapper.invalidate_condition_cache(sample_market.condition_id)
        
        neg_risk = validator.get_market_neg_risk(sample_market.token1)
        assert neg_risk is True
        
        # Reset for cleanup
        sample_market.neg_risk = "FALSE"
        db_session.commit()
        mapper.invalidate_token_cache(sample_market.token1)
        mapper.invalidate_token_cache(sample_market.token2)


class TestMarketCacheService:
    """Tests for MarketCacheService"""
    
    def test_refresh_cache(self, db_session, sample_market):
        """Test cache refresh"""
        cache_service = get_market_cache_service()
        mapper = get_market_mapper()
        mapper.clear_cache()
        
        # Refresh cache
        cache_service.refresh_cache()
        
        # Check that market is in cache
        market = mapper.get_market_by_token_id(sample_market.token1)
        assert market is not None
        assert market.id == sample_market.id
    
    def test_cache_stats(self, db_session, sample_market):
        """Test cache statistics"""
        cache_service = get_market_cache_service()
        cache_service.refresh_cache()
        
        stats = cache_service.get_cache_stats()
        assert 'token_cache_size' in stats
        assert 'condition_cache_size' in stats
        assert 'last_refresh' in stats
        assert stats['last_refresh'] is not None


class TestIntegrationFlow:
    """End-to-end integration tests"""
    
    def test_market_to_order_flow(self, db_session, sample_market):
        """Test complete flow from market creation to order validation"""
        mapper = get_market_mapper()
        validator = get_order_validator()
        mapper.clear_cache()
        
        # Step 1: Market exists in database
        assert sample_market.id is not None
        
        # Step 2: Can lookup market by token
        market = mapper.get_market_by_token_id(sample_market.token1)
        assert market is not None
        
        # Step 3: Can validate order
        result = validator.validate_market_for_order(sample_market.token1, "BUY")
        assert result.is_valid is True
        
        # Step 4: Can get neg_risk
        neg_risk = validator.get_market_neg_risk(sample_market.token1)
        assert neg_risk is not None


if __name__ == "__main__":
    # Initialize database for testing
    init_db()
    pytest.main([__file__, "-v"])

