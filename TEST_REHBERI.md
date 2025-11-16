# 🧪 Alım-Satım Test Rehberi

Bu rehber, trading bot'unuzun stratejilerini test etmeniz ve doğrulamanız için adım adım talimatlar içerir.

## 📋 İçindekiler

1. [DRY_RUN Modu ile Test](#dry_run-modu-ile-test)
2. [Log'ları İzleme](#loglari-izleme)
3. [Strateji Testi](#strateji-testi)
4. [Küçük Miktar ile Gerçek Test](#küçük-miktar-ile-gerçek-test)
5. [Test Kontrol Listesi](#test-kontrol-listesi)

---

## 🔵 DRY_RUN Modu ile Test

### 1. DRY_RUN Modunu Aktifleştirme

`.env` dosyanızı düzenleyin:

```bash
DRY_RUN=true
```

**Önemli:** DRY_RUN modunda bot gerçek order göndermez, sadece simüle eder.

### 2. Bot'u Başlatma

```powershell
# Backend ve Frontend'i başlat
.\START_DEV.ps1
```

Veya manuel olarak:

```powershell
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run serve
```

### 3. Web Arayüzünden Test

1. **http://localhost:8080** adresine gidin
2. **Markets** sayfasından bir market seçin
3. **Configure** butonuna tıklayın
4. Trading parametrelerini ayarlayın
5. **Dashboard** sayfasına gidin
6. **Start Trading** butonuna tıklayın

### 4. Log'ları İzleme

Backend terminal penceresinde şu log'ları göreceksiniz:

```
🔵 DRY RUN MODE
============================================================
POLYMARKET TRADING BOT - CONFIGURATION
============================================================
Mode:                🔵 DRY RUN (Simulation)
Max Position Size:   $100
Max Trade Size:      $10
Min Trade Size:      $1
============================================================

⚠️  DRY RUN MODE: No real orders will be placed
   All trading activity is simulated

[Trading] Processing market: Bitcoin $100K
[DRY RUN] Would create BUY order: 10.0 @ $0.52
[DRY RUN] Would cancel orders for token: 0x...
Creating new order for 10.0 at 0.52
```

**Log Formatı:**
- `[DRY RUN]` = Simüle edilmiş işlem (gerçek değil)
- `Creating new order` = Bot order oluşturmayı deniyor
- `Would create BUY/SELL order` = Hangi order'ı göndereceği

---

## 📊 Log'ları İzleme

### Backend Console Log'ları

Backend terminal penceresinde şu bilgileri görebilirsiniz:

#### 1. Order Placement Log'ları

```
Creating new order for 10.0 at 0.52
0x1234... BUY 0.52 10.0
[DRY RUN] Would create BUY order: 10.0 @ $0.52
```

**Ne Anlama Geliyor:**
- Bot bir order oluşturmayı deniyor
- Token, yön (BUY/SELL), fiyat ve miktar bilgisi
- DRY_RUN modunda gerçekten gönderilmiyor

#### 2. Order Cancellation Log'ları

```
Cancelling buy orders - price diff: 0.0123, size diff: 2.5
[DRY RUN] Would cancel orders for token: 0x1234...
```

**Ne Anlama Geliyor:**
- Mevcut order'lar iptal ediliyor
- Fiyat veya miktar değişikliği nedeniyle
- DRY_RUN modunda gerçekten iptal edilmiyor

#### 3. Market Analysis Log'ları

```
For Bitcoin $100K YES. Orders: {...} Position: 45.2, 
avgPrice: 0.51, Best Bid: 0.50, Best Ask: 0.52, 
Bid Price: 0.49, Ask Price: 0.53, Mid Price: 0.51
```

**Ne Anlama Geliyor:**
- Market analizi yapılıyor
- Mevcut pozisyon, ortalama fiyat, bid/ask fiyatları
- Bot'un karar verme süreci

#### 4. Strategy Decision Log'ları

```
Not creating buy order because its outside acceptable price range (0.1-0.9)
Not creating new order because order price of 0.45 is less than incentive start price of 0.48
```

**Ne Anlama Geliyor:**
- Bot bir order oluşturmamaya karar verdi
- Neden: Fiyat aralığı dışında veya karlı değil
- Bu normal - bot her zaman order göndermez

### Log Dosyasına Kaydetme (Opsiyonel)

Log'ları dosyaya kaydetmek için:

```powershell
# Backend'i log dosyasına yönlendir
cd backend
python -m uvicorn main:app --reload > trading.log 2>&1
```

Sonra log dosyasını izleyin:

```powershell
# Başka bir terminal'de
Get-Content trading.log -Wait -Tail 50
```

---

## 🎯 Strateji Testi

### Test Senaryoları

#### Senaryo 1: Market Making Testi

**Amaç:** Bot'un sürekli alım-satım yapıp yapmadığını test etmek

**Adımlar:**
1. Bir market seçin (ör: Bitcoin $100K)
2. Configure → Trading Mode: **MARKET_MAKING**
3. Trade Size: **5 USD** (küçük başlayın)
4. Max Size: **20 USD**
5. Bot'u başlatın
6. Log'ları izleyin

**Beklenen Sonuç:**
- Bot hem BUY hem SELL order'ları oluşturmalı
- Log'larda `[DRY RUN] Would create BUY order` ve `[DRY RUN] Would create SELL order` görmelisiniz
- Order'lar sürekli güncellenmeli (fiyat değişikliklerine göre)

**Kontrol:**
```bash
# Log'larda şunları arayın:
grep "Would create BUY order" trading.log
grep "Would create SELL order" trading.log
```

#### Senaryo 2: Position Building Testi

**Amaç:** Bot'un belirli bir yöne pozisyon açıp açmadığını test etmek

**Adımlar:**
1. Bir market seçin
2. Configure → Trading Mode: **POSITION_BUILDING**
3. Side to Trade: **YES** (veya NO)
4. Target Position: **50 USD**
5. Trade Size: **10 USD**
6. Bot'u başlatın

**Beklenen Sonuç:**
- Bot sadece seçilen yönde (YES veya NO) order oluşturmalı
- Log'larda sadece BUY order'ları görmelisiniz (SELL değil)
- Pozisyon hedefe ulaşana kadar order'lar devam etmeli

**Kontrol:**
```bash
# Log'larda sadece BUY order'ları olmalı
grep "Would create.*order" trading.log | grep -v "SELL"
```

#### Senaryo 3: Stop Loss / Take Profit Testi

**Amaç:** Risk yönetimi parametrelerinin çalışıp çalışmadığını test etmek

**Adımlar:**
1. Bir market seçin
2. Configure → Stop Loss: **-3%**, Take Profit: **+2%**
3. Küçük bir pozisyon açın (manuel veya bot ile)
4. Bot'u başlatın
5. Log'ları izleyin

**Beklenen Sonuç:**
- Pozisyon -3%'e düşerse bot otomatik kapatmalı
- Pozisyon +2%'ye çıkarsa bot otomatik kapatmalı
- Log'larda position exit mesajları görmelisiniz

**Not:** DRY_RUN modunda gerçek pozisyon yok, bu yüzden bu test için küçük miktar gerçek test gerekebilir.

#### Senaryo 4: Spread Kontrolü Testi

**Amaç:** Bot'un spread kontrolü yapıp yapmadığını test etmek

**Adımlar:**
1. Bir market seçin
2. Configure → Max Spread: **3%** (düşük)
3. Bot'u başlatın
4. Log'ları izleyin

**Beklenen Sonuç:**
- Spread 3%'den yüksekse bot order göndermemeli
- Log'larda "spread too wide" veya benzeri mesajlar görmelisiniz
- Spread daraldığında order'lar başlamalı

---

## 💰 Küçük Miktar ile Gerçek Test

DRY_RUN testinden sonra, küçük miktarlarla gerçek test yapabilirsiniz:

### 1. .env Dosyasını Güncelleyin

```bash
DRY_RUN=false
MAX_TRADE_SIZE=2      # Çok küçük başlayın!
MAX_POSITION_SIZE=10  # Çok küçük başlayın!
```

### 2. Güvenlik Kontrolleri

- [ ] DRY_RUN=false olduğundan emin olun
- [ ] MAX_TRADE_SIZE küçük (2-5 USD)
- [ ] MAX_POSITION_SIZE küçük (10-20 USD)
- [ ] Stop Loss ayarlı (-3% veya daha sıkı)
- [ ] Polymarket hesabında yeterli bakiye var
- [ ] Wallet adresi doğru

### 3. İlk Gerçek Test

```powershell
# Backend'i yeniden başlatın (config değişikliği için)
# Terminal'de şunu görmelisiniz:
🔴 LIVE TRADING MODE
⚠️  LIVE TRADING MODE: Real money at risk!
```

### 4. Log'ları Dikkatle İzleyin

Gerçek modda log'lar farklı olacak:

```
🔴 LIVE TRADING MODE
Creating new order for 2.0 at 0.52
0x1234... BUY 0.52 2.0
# [DRY RUN] mesajı YOK - gerçek order gönderiliyor!
```

### 5. Polymarket'te Kontrol Edin

1. **Polymarket** web sitesine gidin
2. **Portfolio** veya **Orders** sayfasına gidin
3. Bot'un gönderdiği order'ları görmelisiniz
4. Order'ların gerçekten gönderildiğini doğrulayın

---

## ✅ Test Kontrol Listesi

### DRY_RUN Test Kontrol Listesi

- [ ] `.env` dosyasında `DRY_RUN=true`
- [ ] Backend başlatıldı ve log'larda `🔵 DRY RUN MODE` görünüyor
- [ ] Frontend çalışıyor (http://localhost:8080)
- [ ] En az bir market eklendi/çekildi
- [ ] Market configure edildi (parametreler ayarlandı)
- [ ] Bot başlatıldı (Dashboard → Start Trading)
- [ ] Log'larda `[DRY RUN] Would create` mesajları görünüyor
- [ ] Stratejiye göre doğru order'lar oluşturuluyor (BUY/SELL)
- [ ] Order'lar sürekli güncelleniyor (fiyat değişikliklerine göre)

### Gerçek Test Kontrol Listesi

- [ ] DRY_RUN testleri başarılı
- [ ] `.env` dosyasında `DRY_RUN=false`
- [ ] `MAX_TRADE_SIZE` küçük (2-5 USD)
- [ ] `MAX_POSITION_SIZE` küçük (10-20 USD)
- [ ] Stop Loss ayarlı
- [ ] Polymarket hesabında bakiye var
- [ ] Backend log'larında `🔴 LIVE TRADING MODE` görünüyor
- [ ] Polymarket'te order'lar görünüyor
- [ ] İlk birkaç order başarılı
- [ ] Pozisyonlar doğru açılıyor
- [ ] Stop Loss/Take Profit çalışıyor

---

## 🔍 Sorun Giderme

### Problem: Bot hiç order göndermiyor

**Kontrol Edin:**
1. Market aktif mi? (`is_active: true`)
2. Trading Mode doğru mu?
3. Spread çok geniş mi? (Max Spread kontrolü)
4. Fiyat aralığı uygun mu? (0.1-0.9 arası)
5. Log'larda neden order göndermediğine dair mesaj var mı?

**Log'larda Arayın:**
```
Not creating buy order because...
Not creating new order because...
```

### Problem: Sadece BUY order'ları görüyorum, SELL yok

**Olası Nedenler:**
1. Trading Mode = POSITION_BUILDING (sadece alım yapar)
2. Side to Trade = YES veya NO (tek yön)
3. Pozisyon yok, bu yüzden satacak bir şey yok

**Çözüm:**
- MARKET_MAKING moduna geçin
- Veya Side to Trade = BOTH yapın

### Problem: Order'lar çok sık güncelleniyor

**Olası Nedenler:**
1. Quick Cancel Threshold çok düşük
2. Market çok volatil
3. Tick Improvement çok yüksek

**Çözüm:**
- Quick Cancel Threshold'u artırın (0.02 → 0.05)
- Daha stabil bir market seçin

### Problem: DRY_RUN modunda ama log'lar farklı

**Kontrol:**
1. `.env` dosyasını kontrol edin
2. Backend'i yeniden başlatın (config değişikliği için)
3. Log'larda `🔵 DRY RUN MODE` görünüyor mu?

---

## 📈 Test Metrikleri

Test sırasında şu metrikleri takip edin:

### 1. Order Frequency (Order Sıklığı)
- Dakikada kaç order oluşturuluyor?
- Beklentinizle uyumlu mu?

### 2. Order Types (Order Türleri)
- BUY/SELL oranı nedir?
- Stratejiye uygun mu?

### 3. Price Accuracy (Fiyat Doğruluğu)
- Order fiyatları mantıklı mı?
- Spread içinde mi?

### 4. Position Building (Pozisyon Oluşturma)
- Hedef pozisyona ulaşılıyor mu?
- Pozisyon doğru yönde mi?

### 5. Risk Management (Risk Yönetimi)
- Stop Loss çalışıyor mu?
- Take Profit çalışıyor mu?
- Max Size limiti aşılmıyor mu?

---

## 🎓 İleri Seviye Test

### Backtest (Geçmiş Verilerle Test)

Şu anda backtest özelliği yok, ancak log'ları analiz ederek:

1. Log'ları kaydedin
2. Gerçek market fiyatlarıyla karşılaştırın
3. "Eğer bu order'lar gerçekten gönderilseydi ne olurdu?" sorusunu cevaplayın

### Paper Trading (Sanal Para)

DRY_RUN modu zaten bir tür paper trading. Ancak daha gelişmiş bir paper trading için:

1. Sanal bir wallet bakiyesi simüle edin
2. Order'ları simüle edin
3. Fill rate'leri hesaplayın
4. PnL'yi takip edin

---

## 📞 Yardım

Sorun yaşıyorsanız:

1. Log dosyalarını kontrol edin
2. `.env` ayarlarını kontrol edin
3. Market parametrelerini kontrol edin
4. Backend ve Frontend'in çalıştığından emin olun

**Önemli:** İlk testlerde mutlaka DRY_RUN modunu kullanın!

