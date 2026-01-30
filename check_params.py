import sqlite3

conn = sqlite3.connect('backend/polymarket_bot.db')
cur = conn.cursor()

# Get active market and its trading params
cur.execute("""
    SELECT 
        m.question,
        m.trading_mode,
        m.side_to_trade,
        tp.trade_size,
        tp.max_size,
        tp.min_size
    FROM markets m
    LEFT JOIN trading_params tp ON m.id = tp.market_id
    WHERE m.is_active = 1
""")

row = cur.fetchone()

if row:
    question, mode, side, trade_size, max_size, min_size = row
    
    print("=" * 80)
    print("AKTIF MARKET TRADING PARAMETERS")
    print("=" * 80)
    print(f"\nMarket: {question}")
    print(f"Mode: {mode}")
    print(f"Side: {side}\n")
    
    print("BAKIYE KULLANIMI:")
    print("-" * 80)
    
    if trade_size:
        print(f"✅ Her order: ${trade_size}")
    else:
        print("⚠️  trade_size YOK! Default $10 kullanılacak")
        trade_size = 10
    
    if max_size:
        print(f"✅ Max position: ${max_size}")
    else:
        print("⚠️  max_size YOK! Default $100 kullanılacak")
        max_size = 100
    
    if min_size:
        print(f"✅ Min order: ${min_size}")
    else:
        print("⚠️  min_size YOK! Default $1 kullanılacak")
        min_size = 1
    
    print("\n" + "=" * 80)
    print("BOT NASIL ÇALIŞACAK:")
    print("=" * 80)
    print(f"1. İlk iteration: ${trade_size} BUY order + ${trade_size} SELL order")
    print(f"2. Her 3 saniyede bir: Fiyat update")
    print(f"3. Position ${max_size}'a ulaşınca: Sadece market making (buy+sell eşit)")
    print(f"4. Toplam max risk: ${max_size} (tek tarafta)")
    print("=" * 80)
else:
    print("❌ Aktif market bulunamadı!")

conn.close()
