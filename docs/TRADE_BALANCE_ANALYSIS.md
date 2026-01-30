# Trade & Bakiye Kontrolü Analizi

## Tespit Edilen Sorunlar

### 1. **Bakiye kontrolü yoktu**
- `perform_trade()` ve `send_buy_order()` hiçbir yerde USDC bakiyesini kontrol etmiyordu.
- Sonuç: Bakiyeden fazla BUY order’ı gönderilebiliyordu; API "not enough balance" dönene kadar denemeye devam ediyordu.
- Özellikle **trade_size=10, max_size=100** ile az bakiye (örn. $15) olduğunda bot iki tarafta da $10’luk order koymaya çalışıp toplamda $20 harcamaya kalkabiliyordu.

### 2. **get_buy_sell_amount bakiye kullanmıyor**
- `poly_data/trading_utils.py` içindeki `get_buy_sell_amount(position, bid_price, row, other_position)` sadece:
  - `position`, `max_size`, `trade_size`, `other_position`, `trading_mode` kullanıyor.
- **USDC bakiyesi hiç parametre değil**, bu yüzden `buy_amount` her zaman `trade_size`’a kadar çıkabiliyor.

### 3. **create_order öncesi kontrol yok**
- `polymarket_client.create_order()` sadece API’ye gönderiyor; öncesinde bakiye kontrolü yapılmıyordu.
- Reddedilen order’lar gereksiz API çağrısı ve log kirliliği oluşturuyordu.

---

## Yapılan Düzeltmeler

### A. `trading.py` – perform_trade()

1. **Piyasa döngüsü başında USDC bakiyesi**
   - `client.get_usdc_balance()` bir kez alınıyor.
   - `available_usdc` ve `reserved_usdc` ile bu piyasa için harcanacak miktar takip ediliyor.

2. **Her BUY öncesi bakiye / cap**
   - `cost_usdc = buy_amount` (order size zaten USDC).
   - `available_after_reserved = available_usdc - reserved_usdc`.
   - Eğer `cost_usdc > available_after_reserved`:
     - Bakiye `min_size`’dan büyükse: `buy_amount` bu bakiyeye cap’leniyor, log yazılıyor.
     - Değilse: BUY atlanıyor, `continue` ile sonraki outcome’a geçiliyor.

3. **Rezervasyon**
   - Gerçekten `send_buy_order(order)` çağrılmadan hemen önce `reserved_usdc += order['size']` yapılıyor.
   - Aynı piyasada iki outcome (YES/NO) için art arda BUY atılsa bile toplam harcama bakiyeyi aşmıyor.

### B. `trading.py` – send_buy_order()

- **Son kontrol**
  - Order gönderilmeden hemen önce tekrar `client.get_usdc_balance()` ile kontrol.
  - `usdc < order['size']` ise order atılmıyor, log yazılıp `return` ediliyor.
  - Başka yerden `send_buy_order` çağrılsa bile bakiye aşılmıyor.

---

## Akış Özeti (BUY tarafı)

```
perform_trade(market)
  → USDC balance al (bir kez)
  → reserved_usdc = 0
  → for each outcome (token):
        buy_amount, sell_amount = get_buy_sell_amount(...)
        cost_usdc = buy_amount
        available_after_reserved = available_usdc - reserved_usdc
        if cost_usdc > available_after_reserved:
            cap buy_amount veya skip
        ...
        if ... (buy koşulları):
            order['size'] = buy_amount
            ...
            reserved_usdc += order['size']
            send_buy_order(order)
              → (opsiyonel) son bakiye kontrolü
              → create_order(...)
```

---

## Değişmeyenler (bilinçli)

- **get_buy_sell_amount** hâlâ bakiye parametresi almıyor; cap’leme tamamen `trading.py` içinde yapılıyor. Böylece:
  - Strateji (trade_size, max_size, mode) aynı kalıyor.
  - Sadece “ne kadar harcanacak” kısmı bakiye ile sınırlanıyor.
- **SELL** tarafında bakiye kontrolü yok; SELL pozisyon/token ile yapılıyor, USDC’den harcanmıyor.

---

## Önerilen İzleme

- Log’larda şunları görebilirsiniz:
  - `💰 USDC balance: $X.XX`
  - `📉 Capping buy to available USDC: $X.XX (had $Y.YY)` (cap yapıldığında)
  - `⏸️  Insufficient USDC: need $X.XX, available $Y.YY. Skipping buy.` (atlandığında)
  - `⏸️  Skipping buy - insufficient USDC: have $X.XX, need $Y.YY` (send_buy_order içi güvenlik kontrolü)

Bu sayede trade tarafında bakiye kontrolü ve cap mantığı tek yerde toplanmış ve güvenli hale getirilmiş oldu.
