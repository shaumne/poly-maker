# 🎯 Polymarket Trading Bot - Kullanım Kılavuzu

## 📋 İçindekiler

1. [Hızlı Başlangıç](#hızlı-başlangıç)
2. [Trading Modları](#trading-modları)
3. [Özellikler](#özellikler)
4. [Web Arayüzü](#web-arayüzü)
5. [Güvenlik](#güvenlik)
6. [Sandbox Test](#sandbox-test)
7. [İleri Seviye](#ileri-seviye)

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```powershell
# Geliştirme ortamını kur
.\INSTALL_DEV.ps1

# .env dosyasını oluştur
copy .env.example .env

# .env dosyasını düzenle (önemli!)
notepad .env
```

### 2. İlk Çalıştırma (DRY RUN)

```powershell
# Backend ve Frontend'i başlat
.\START_DEV.ps1
```

**Önemli:** İlk çalıştırmada `DRY_RUN=true` olmalı! Bu mod:
- ✅ Gerçek order göndermez (simülasyon)
- ✅ Tüm özellikleri test edebilirsiniz
- ✅ Para kaybetme riski yok

### 3. Web Arayüzüne Giriş

Frontend başladıktan sonra:
- 🌐 **http://localhost:8080** adresine gidin
- 🎮 Dashboard'dan bot durumunu görün

---

## 🎮 Trading Modları

Bot 4 farklı modda çalışabilir:

### 1. MARKET_MAKING (Varsayılan)
**Ne Yapar:** Geleneksel market making stratejisi
- Sürekli alım/satım yaparak kar elde eder
- Spread'den kazanır
- Kısa vadeli, yüksek frekanslı işlemler

**Ne Zaman Kullanılır:** 
- Piyasadan kar kazanmak istediğinizde
- Yön tahmini yapmadan trading yapmak istediğinizde

**Örnek Ayarlar:**
```python
trading_mode: MARKET_MAKING
trade_size: 5
spread: 0.02
aggression: 0.5
```

---

### 2. POSITION_BUILDING
**Ne Yapar:** Belirli bir yöne pozisyon açar
- Sadece alım yapar (satış yapmaz)
- Target pozisyona ulaşana kadar alır
- Uzun vadeli tutma stratejisi

**Ne Zaman Kullanılır:**
- Bir market sonucuna güvendiğinizde
- Pozisyon açıp market kapanışına kadar tutacaksanız

**Örnek Ayarlar:**
```python
trading_mode: POSITION_BUILDING
target_position: 100  # 100 USD pozisyon açacak
trade_size: 10
side_to_trade: NO  # veya YES
```

---

### 3. HYBRID (Karma Mod)
**Ne Yapar:** Önce pozisyon açar, sonra market making yapar
- İlk önce target pozisyonu doldurur
- Pozisyon hedefe ulaşınca market making'e geçer
- En fazla kazanç bu modda!

**Ne Zaman Kullanılır:**
- Hem yön tahmini yapmak hem de spread kazanmak istediğinizde
- En çok önerilen mod (sizin için ideal!)

**Örnek Ayarlar:**
```python
trading_mode: HYBRID
target_position: 50    # Önce 50 USD pozisyon aç
trade_size: 5
max_size: 100          # Sonra max 100'e kadar trade yap
side_to_trade: NO
```

---

### 4. SELL_ONLY (Çıkış Modu)
**Ne Yapar:** Sadece elimdeki pozisyonu satar
- Yeni alım yapmaz
- Mevcut pozisyonu yavaşça boşaltır
- Risk azaltma modu

**Ne Zaman Kullanılır:**
- Piyasadan çıkmak istediğinizde
- Risk azaltmak istediğinizde
- Market yönü değiştiğinde

**Örnek Ayarlar:**
```python
trading_mode: SELL_ONLY
trade_size: 10  # Her seferde 10 USD sat
```

---

## 🎯 Özellikler

### Side Selection (Yön Seçimi)

Her market için hangi tarafı trade edeceğinizi seçebilirsiniz:

- **YES**: Sadece YES tarafını trade et
- **NO**: Sadece NO tarafını trade et
- **BOTH**: Her iki tarafı da trade et

**Örnek Kullanım:**
```
Market: "Bitcoin $100K'yı aşacak mı?"
Side: NO
→ Bot sadece NO tarafında pozisyon alır/satar
```

### Alt-Market Desteği

Polymarket'te bazı marketlerin alt-soruları vardır:

**Örnek:**
```
Ana Market: "Bitcoin Ekim ayında hangi fiyata ulaşacak?"
Alt-Marketler:
  ├─ $104,000 YES/NO
  ├─ $106,000 YES/NO
  └─ $108,000 YES/NO
```

Bot **tüm alt-marketleri otomatik bulur** ve her birini ayrı trade edebilirsiniz!

### Crypto Market Filtreleme

Bot otomatik olarak:
- ✅ Tüm kripto marketlerini bulur
- ✅ Alt-marketleri dahil eder
- ✅ Reward-bearing filtreleme yapmaz
- ✅ Manuel ekleme yapabilirsiniz

---

## 🌐 Web Arayüzü

### Dashboard
- 📊 Anlık PnL ve istatistikler
- 🤖 Bot durumu (çalışıyor/durdu)
- 💰 Toplam pozisyon değeri
- 📈 Günlük/haftalık kazanç grafikleri

### Markets
- 📋 Tüm crypto marketleri listesi
- ⚙️ Her market için ayrı ayar:
  - `side_to_trade`: YES / NO / BOTH
  - `trading_mode`: MARKET_MAKING / POSITION_BUILDING / HYBRID / SELL_ONLY
  - `trade_size`, `target_position`, `max_size`
- 🔄 "Fetch Crypto Markets" butonu ile güncelleyin

### Positions
- 📦 Açık pozisyonlarınız
- 💵 Average price ve current price
- 📊 PnL (kar/zarar)
- 🎯 Her pozisyon için side gösterimi

### Orders
- 📝 Açık orderlarınız
- ❌ İptal etme özelliği
- ⏱️ Order geçmişi

### Settings
- 🔑 API key ayarları (güvenli saklama)
- 🔐 Wallet adresi
- 🛡️ Güvenlik limitler
- 🔄 DRY_RUN mod değiştirme

---

## 🔒 Güvenlik

### Private Key Güvenliği

```bash
# .env dosyanızı ASLA paylaşmayın!
# .gitignore'da olduğundan emin olun:
cat .gitignore | grep .env

# Eğer yoksa ekleyin:
echo .env >> .gitignore
```

### Güvenlik Limitleri

`.env` dosyasında tanımlı limitler:

```bash
MAX_POSITION_SIZE=100   # Maksimum 100 USD pozisyon
MAX_TRADE_SIZE=10       # Tek seferde max 10 USD
MIN_TRADE_SIZE=1        # Minimum 1 USD
```

**Canlıya geçerken:**
1. Küçük limitlerle başlayın ($10-20)
2. İlk gün yakından takip edin
3. Sonuçlar iyiyse limitleri artırın

### DRY_RUN Modu

```bash
# .env dosyasında:
DRY_RUN=true   # Güvenli test modu
DRY_RUN=false  # Canlı trading (dikkat!)
```

**Kontrol:**
```bash
# Backend başladığında konsola bakar:
🔵 DRY RUN (Simulation)  ✅ Güvenli
🔴 LIVE TRADING         ⚠️ Dikkat!
```

---

## 🧪 Sandbox Test

### Polymarket Sandbox Var mı?

**Hayır, Polymarket'in resmi bir sandbox/testnet ortamı yok.**

**Alternatifler:**

#### 1. DRY_RUN Modu (Önerilen)
```bash
DRY_RUN=true
```

✅ **Yapabilecekleriniz:**
- Market verilerini çekme
- Order hesaplaması
- Strateji testi
- UI testi
- Log analizi

❌ **Yapamayacaklarınız:**
- Gerçek order gönderme
- Pozisyon açma/kapatma
- Gerçek PnL görme

#### 2. Küçük Miktar Test
```bash
DRY_RUN=false
MAX_TRADE_SIZE=2
MAX_POSITION_SIZE=10
```

- Küçük miktarlarla ($2-10) gerçek test
- Tüm özellikleri deneyebilirsiniz
- Risk düşük

#### 3. Paper Trading Implementasyonu

Bot'ta paper trading modu eklenmiş durumda:

```python
# backend/config.py
DRY_RUN=true

# trading.py içinde:
if Config.is_dry_run():
    print(f"[DRY RUN] Order göndermedi: {order}")
    # Simüle edilmiş sonuç döndür
    return simulated_result
else:
    # Gerçek order gönder
    return clob.place_order(order)
```

**Simülasyon Özellikleri:**
- Order placement simülasyonu
- Fill rate hesaplaması
- PnL tracking (sanal)
- Position tracking (sanal)

---

## 🔧 İleri Seviye

### Bot'u Diğer Botlara Karşı Optimize Etme

#### 1. Aggression Parametresi

```python
aggression: 0.5  # Orta seviye (varsayılan)
aggression: 0.8  # Agresif (daha fazla risk, daha fazla kar)
aggression: 0.2  # Konservatif (az risk, az kar)
```

**Aggression ne yapar:**
- Spread'i daralır (daha rekabetçi fiyatlar)
- Order size'ı artırır
- Daha hızlı pozisyon alır

#### 2. Sizin Üstünlüğünüz

**İnsan Trading Edge:**
- 🎯 Market seçimi (yüksek conviction)
- ⏰ Uzun vadeli tutma toleransı
- 🧠 Fundamental analiz

**Bot Parametreleri:**
```python
# İnsan stratejisini taklit eden ayarlar:
trading_mode: HYBRID
target_position: 100      # Pozisyon aç ve tut
aggression: 0.7           # Agresif al
side_to_trade: NO         # Yön seç
max_size: 200             # Büyük pozisyon toleransı
stop_loss: 0.15           # Uzun vade için geniş stop
```

#### 3. Rakip Bot Tespiti

Bot log'larını izleyin:
```
[2024-11-15 10:30] Bid: $0.45 → $0.46 (rakip bot?)
[2024-11-15 10:31] Ask: $0.48 → $0.47 (rakip bot?)
```

**Karşı strateji:**
- Daha agresif spread
- Daha büyük order size
- Limit order yerine hızlı fill

#### 4. Market Timing

```python
# Oynaklık filtresi
volatility_threshold: 0.05  # %5'ten fazla hareket varsa dur

# Spread filtresi
min_spread: 0.02  # Spread %2'den azsa trade yapma
```

### Özel Strateji Örnekleri

#### Strateji 1: "Conviction Play"
```python
# Yüksek conviction marketler için
trading_mode: POSITION_BUILDING
side_to_trade: NO
target_position: 500
trade_size: 50
aggression: 0.9
stop_loss: null  # Stop yok, uzun vade
```

#### Strateji 2: "Quick Scalp"
```python
# Hızlı kar için
trading_mode: MARKET_MAKING
trade_size: 10
spread: 0.01
aggression: 0.8
take_profit: 0.03  # %3 karda sat
```

#### Strateji 3: "Build Then Trade"
```python
# Önce pozisyon, sonra grinding
trading_mode: HYBRID
target_position: 100
trade_size: 20
max_size: 300
side_to_trade: NO
aggression: 0.6
```

---

## 📊 Monitoring

### Log Takibi

**Backend logs:**
```bash
INFO: Uvicorn running on http://0.0.0.0:8000
[Trading] Market: Bitcoin $100K
[Trading] Side: NO, Position: 45.2, PnL: +2.3%
```

**Frontend console:**
```javascript
// Browser console (F12)
store.state.trading.isRunning  // true/false
store.state.positions.positions // açık pozisyonlar
```

### Performance Metrics

Dashboard'da takip edin:
- 💰 Total PnL
- 📈 Win Rate
- 🔢 Total Trades
- ⏱️ Avg Hold Time
- 📊 Best/Worst Market

---

## 🆘 Troubleshooting

### Problem: Bot çalışmıyor

```bash
# Backend kontrolü
cd backend
python -m uvicorn main:app --reload

# Frontend kontrolü
cd frontend
npm run serve
```

### Problem: Market bulunamıyor

```bash
# Database reset
cd backend
python database.py

# Web interface'den "Fetch Crypto Markets"
```

### Problem: Order gönderilmiyor

1. DRY_RUN modunu kontrol edin
2. API credentials'ı kontrol edin (.env)
3. Polymarket hesabınızda bakiye var mı?

---

## 📞 Destek

### Useful Commands

```powershell
# Full restart
.\START_DEV.ps1

# Backend only
cd backend
python -m uvicorn main:app --reload

# Frontend only
cd frontend
npm run serve

# Database reset
cd backend
python database.py
```

### Logs

```bash
# Backend logs
backend/logs/

# Database
backend/polymarket_bot.db
```

---

## 🎓 Best Practices

1. **Her zaman DRY_RUN ile başla**
2. **Küçük limitlerle test et**
3. **İlk gün yakından takip et**
4. **Log'ları düzenli kontrol et**
5. **Stop-loss kullan**
6. **Çok fazla markete spread yapma**
7. **Yüksek conviction marketleri seç**
8. **Pozisyonları düzenli review et**

---

## 🚀 Production Deployment

VPS'e deploy için:

```bash
# DEPLOYMENT.md dosyasına bakın
# Docker ile production deployment
docker-compose up -d
```

---

Başarılar! 🎯💰

**Not:** Bu bot risk içerir. Yalnızca kaybetmeyi göze alabileceğiniz sermaye ile kullanın.

