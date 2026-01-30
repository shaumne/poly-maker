import sqlite3
from datetime import datetime

conn = sqlite3.connect('backend/polymarket_bot.db')
cur = conn.cursor()

print("=" * 80)
print("🎯 TRADE LOGLARININ DETAYLI ANALİZİ")
print("=" * 80)

# Orders tablosunu sorgula
try:
    cur.execute("""
        SELECT order_id, token_id, side_type, side, price, size, status, created_at 
        FROM orders 
        ORDER BY created_at DESC 
        LIMIT 20
    """)
    
    orders = cur.fetchall()
    
    if orders:
        print(f"\n📊 SON {len(orders)} ORDER:\n")
        buy_count = sum(1 for o in orders if o[2] == 'BUY')
        sell_count = sum(1 for o in orders if o[2] == 'SELL')
        total_volume = sum(o[4] * o[5] for o in orders)  # price * size
        
        print(f"   📈 BUY Orders: {buy_count}")
        print(f"   📉 SELL Orders: {sell_count}")
        print(f"   💰 Total Volume: ${total_volume:.2f}\n")
        print("-" * 80)
        
        for idx, row in enumerate(orders, 1):
            order_id, token_id, side_type, side, price, size, status, created = row
            value = price * size
            
            emoji = "📈" if side_type == "BUY" else "📉"
            print(f"{emoji} {idx}. {created}")
            print(f"   Order ID: {order_id if order_id else 'N/A'}")
            print(f"   {side_type} {side} | Price: ${price} | Size: {size} | Value: ${value:.2f}")
            print(f"   Status: {status}")
            print(f"   Token: ...{token_id[-20:] if token_id else 'N/A'}")
            print()
    else:
        print("\n⚠️  Henüz order kaydı yok!")
        
except Exception as e:
    print(f"❌ Orders tablosu okunamadı: {e}")
    import traceback
    traceback.print_exc()

# Positions tablosunu sorgula  
try:
    cur.execute("""
        SELECT token_id, size, avg_price, side, unrealized_pnl, realized_pnl, timestamp 
        FROM positions 
        ORDER BY timestamp DESC 
        LIMIT 10
    """)
    
    positions = cur.fetchall()
    
    if positions:
        print("\n💼 AKTİF POZİSYONLAR:\n")
        total_unrealized = 0
        total_realized = 0
        
        for token, size, avg_price, side, unreal_pnl, real_pnl, ts in positions:
            if size != 0:
                value = size * avg_price
                total_unrealized += unreal_pnl or 0
                total_realized += real_pnl or 0
                
                print(f"Token: ...{token[-20:]}")
                print(f"Side: {side} | Size: {size} | Avg Price: ${avg_price}")
                print(f"Value: ${value:.2f}")
                print(f"Unrealized PnL: ${unreal_pnl or 0:.2f} | Realized PnL: ${real_pnl or 0:.2f}")
                print(f"Updated: {ts}\n")
        
        if total_unrealized != 0 or total_realized != 0:
            print("-" * 80)
            print(f"📊 TOPLAM PnL:")
            print(f"   Unrealized: ${total_unrealized:.2f}")
            print(f"   Realized: ${total_realized:.2f}")
            print(f"   Total: ${total_unrealized + total_realized:.2f}\n")
    else:
        print("\n⚠️  Henüz pozisyon yok!")
        
except Exception as e:
    print(f"❌ Positions tablosu okunamadı: {e}")
    import traceback
    traceback.print_exc()

# Market bilgisi
try:
    cur.execute("""
        SELECT question, is_active, trading_mode, side_to_trade 
        FROM markets 
        WHERE is_active = 1
    """)
    
    markets = cur.fetchall()
    
    if markets:
        print("\n🎯 AKTİF MARKETLER:\n")
        for question, active, mode, side in markets:
            print(f"Market: {question}")
            print(f"Mode: {mode} | Side: {side}")
            print()
            
except Exception as e:
    print(f"❌ Markets tablosu okunamadı: {e}")

conn.close()
print("=" * 80)
