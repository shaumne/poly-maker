# Quick Start Guide - Polymarket Trading Bot Web App

## 🚀 5 Dakikada Başlangıç

### 1. Gereksinimler
- Docker & Docker Compose yüklü olmalı
- Polymarket hesabı (private key ve wallet address)

### 2. Kurulum

```bash
# Repository'yi klonla
git clone https://github.com/yourusername/poly-maker.git
cd poly-maker

# .env dosyasını oluştur
cp .env.example .env

# .env dosyasını düzenle
nano .env
```

**.env dosyasına ekle:**
```
PK=your_private_key_here
BROWSER_ADDRESS=your_wallet_address_here
```

### 3. Başlat

```bash
# Docker container'ları başlat
docker-compose up -d

# Logları izle (opsiyonel)
docker-compose logs -f
```

### 4. Web Interface'e Eriş

Tarayıcıda aç: **http://localhost**

### 5. İlk Konfigürasyon

1. **Settings** sayfasına git
   - API credentials'ını gir (zaten .env'de varsa skip edilebilir)

2. **Markets** sayfasına git
   - **"Fetch Crypto Markets"** butonuna tıkla
   - Tüm crypto marketleri otomatik yüklenecek

3. **Market Konfigürasyonu**
   
   Her market için "Configure" butonuna tıkla:
   
   ```
   Side to Trade: YES / NO / BOTH
   Trading Mode: MARKET_MAKING / POSITION_BUILDING / HYBRID
   Target Position: 100 (örnek)
   Trade Size: 10
   Max Size: 100
   Stop Loss: -5%
   Take Profit: 2%
   ```

4. **Dashboard'a dön**
   - **"Start Trading"** butonuna tıkla
   - Bot aktif olacak ✅

## 📊 Örnek Kullanım Senaryoları

### Senaryo 1: Crypto Market'te NO Pozisyonu Oluşturma

```
Market: "Will Bitcoin reach $150k by end of year?"
Config:
  - Side: NO
  - Mode: POSITION_BUILDING
  - Target Position: 200
  - Trade Size: 20
```

**Sonuç:** Bot NO tarafında 200'e ulaşana kadar alım yapacak, sonra satış yapacak.

### Senaryo 2: Her İki Tarafta Market Making

```
Market: "Will Ethereum hit $5000 in Q1?"
Config:
  - Side: BOTH
  - Mode: MARKET_MAKING
  - Max Size: 100
  - Trade Size: 10
```

**Sonuç:** Bot her iki tarafta da limit orderlar koyup spread'den kazanacak.

### Senaryo 3: Hybrid Strateji

```
Market: "Will Solana outperform Ethereum?"
Config:
  - Side: YES
  - Mode: HYBRID
  - Target Position: 150
  - Max Size: 300
```

**Sonuç:** Önce 150 YES pozisyonu oluşturulacak, sonra 300'e kadar market making yapılacak.

## 🎯 Dashboard Özellikleri

- **Total PnL:** Toplam kar/zarar
- **Active Markets:** Aktif trade edilen market sayısı
- **Open Positions:** Açık pozisyon sayısı
- **Active Orders:** Aktif order sayısı
- **Recent Orders:** Son orderlar listesi
- **Active Positions:** Açık pozisyonlar ve PnL'leri

## ⚙️ Önemli Parametreler

### Trade Size vs Max Size

- **Trade Size:** Her order'da kullanılacak miktar
- **Max Size:** Maksimum pozisyon büyüklüğü

Örnek: Trade Size = 10, Max Size = 100
→ Bot 10'ar 10'ar alıp 100'e ulaşacak

### Stop Loss vs Take Profit

- **Stop Loss:** Kaybı durdur (örn: -5%)
- **Take Profit:** Kar al (örn: +2%)

### Order Front Running

- ✅ Enabled: Diğer botların önüne geç
- ❌ Disabled: Normal order placement

### Tick Improvement

- 0: Hiç iyileştirme yapma
- 1-3: Kaç tick daha iyi fiyat teklif et

## 🛠️ Komutlar

```bash
# Logları görüntüle
docker-compose logs -f

# Bot'u durdur
docker-compose stop

# Bot'u yeniden başlat
docker-compose restart

# Tüm container'ları kaldır
docker-compose down

# Yeniden build et
docker-compose up -d --build
```

## 🐛 Sorun Giderme

### Backend başlamıyor
```bash
docker-compose logs backend
```

### Frontend boş sayfa gösteriyor
```bash
# Browser console'u kontrol et (F12)
# API URL'ini kontrol et
```

### Trading bot çalışmıyor
```bash
# .env credentials kontrolü
cat .env

# Database kontrolü
docker exec polymarket-backend python database.py
```

## 📚 Daha Fazla Bilgi

- **Detaylı Deployment:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Tam Özellikler:** [README_WEBAPP.md](README_WEBAPP.md)
- **Original Docs:** [README.md](README.md)

## ⚠️ Önemli Notlar

1. **Küçük miktarlarla test edin!**
2. **Private key'inizi asla paylaşmayın**
3. **Risk yönetimini anlayın**
4. **Volatiliteye dikkat edin**

## 🎉 Başarılı Kurulum!

Bot artık çalışıyor. Dashboard'dan monitoring yapabilir, Markets'ten konfigürasyon değiştirebilir, Positions ve Orders'tan trade'lerinizi takip edebilirsiniz.

Happy Trading! 🚀📈

