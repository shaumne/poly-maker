import json
from poly_utils.google_utils import get_spreadsheet
import pandas as pd 
import os

def pretty_print(txt, dic):
    print("\n", txt, json.dumps(dic, indent=4))

def get_sheet_df(read_only=None):
    """
    Get market data from database
    Fully database-driven - no Google Sheets fallback
    
    Args:
        read_only (bool): Ignored, kept for backwards compatibility
    """
    try:
        # Import db_utils to get data from database
        from poly_data.db_utils import get_markets_dataframe, get_trading_params
        
        df = get_markets_dataframe()
        hyperparams = get_trading_params()
        
        if len(df) == 0:
            print("⚠️  No markets found in database!")
            print("   Please add markets via the web interface:")
            print("   1. Go to http://localhost:8080/markets")
            print("   2. Click 'Fetch Crypto Markets'")
            print("   3. Configure your markets\n")
        
        return df, hyperparams
    
    except Exception as e:
        print(f"❌ Error loading from database: {e}")
        print("   Make sure:")
        print("   1. Database is initialized (python database.py)")
        print("   2. Backend is running")
        print("   3. Markets are configured in web interface\n")
        
        # Return empty dataframes instead of crashing
        return pd.DataFrame(), {}
