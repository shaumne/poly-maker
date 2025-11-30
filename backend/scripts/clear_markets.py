"""
Script to delete all markets from the database.
This will also delete related trading_params, positions, and orders due to cascade.
"""
import sys
import os

# Change to backend directory to ensure correct database path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
os.chdir(backend_dir)

# Add backend directory to path to import database modules
sys.path.insert(0, backend_dir)

from database import SessionLocal, Market, init_db

def clear_all_markets():
    """Delete all markets from the database"""
    # First, ensure database tables exist
    print("Initializing database tables if they don't exist...")
    try:
        init_db()
        print("Database initialized.")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Continuing anyway...")
    
    db = SessionLocal()
    try:
        # Count markets before deletion
        total_markets = db.query(Market).count()
        
        if total_markets == 0:
            print("No markets to delete. Database is already empty.")
            return
        
        print(f"Found {total_markets} market(s) in database.")
        print("Deleting all markets (this will also delete related trading_params, positions, and orders)...")
        
        # Delete all markets (cascade will handle related records)
        deleted_count = db.query(Market).delete()
        db.commit()
        
        print(f"✅ Successfully deleted {deleted_count} market(s) and all related data!")
        print("Database is now clean and ready for fresh market data.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error deleting markets: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Market Database Cleaner")
    print("=" * 60)
    print()
    
    response = input("⚠️  WARNING: This will delete ALL markets from the database!\n"
                     "   This action cannot be undone. Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        clear_all_markets()
    else:
        print("Operation cancelled.")

