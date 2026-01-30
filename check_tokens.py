import sqlite3

conn = sqlite3.connect('backend/polymarket_bot.db')
cur = conn.cursor()
cur.execute('SELECT token1, token2, question FROM markets WHERE is_active = 1 LIMIT 5')

for row in cur.fetchall():
    print(f'Token1: {row[0]}')
    print(f'Token2: {row[1]}')
    print(f'Market: {row[2]}')
    print('---')

conn.close()
