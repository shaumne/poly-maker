# Polymarket Trading Bot - Web Application

Modern web interface ile Polymarket prediction market trading botu.

## 🚀 Özellikler

### Ana Özellikler

- **🎯 Tek Taraflı Trading:** YES, NO veya her iki tarafı da trade edebilme
- **💹 Crypto Market Filtering:** Tüm crypto-ilişkili marketleri otomatik çekme
- **📊 Sub-Market Support:** Multi-outcome marketlerde her seçeneği ayrı ayrı trade etme
- **🔄 Trading Modes:**
  - **Market Making:** Sürekli alım-satım ile spread'den kazanç
  - **Position Building:** Hedef pozisyona ulaşana kadar sadece alım
  - **Hybrid:** Önce pozisyon oluştur, sonra market making yap

### Trading Enhancements

- **Side-Specific PnL Tracking:** Sadece trade ettiğiniz taraf için PnL hesaplama
- **Competitive Bot Features:**
  - Order front-running (botların önüne geçme)
  - Tick improvement (daha iyi fiyat teklifi)
  - Position patience (pozisyonu uzun süre tutma toleransı)
- **Risk Management:**
  - Stop-loss thresholds
  - Take-profit targets
  - Volatility-based trading
  - Sleep periods after losses

### Web Interface

- **Dashboard:** Genel bakış, PnL, aktif trades
- **Markets:** Market yönetimi, crypto market fetching, konfigürasyon
- **Positions:** Tüm pozisyonlar, side-bazlı PnL
- **Orders:** Aktif ve geçmiş orderlar
- **Settings:** API credentials, default parameters, bot behavior

## 📋 Gereksinimler

- Python 3.9.10+
- Node.js 18+
- Docker & Docker Compose
- Polymarket hesabı ve API credentials

## 🔧 Kurulum

### 1. Hızlı Başlangıç (Docker)

```bash
# Repository'yi klonla
git clone https://github.com/yourusername/poly-maker.git
cd poly-maker

# .env dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenle ve credentials ekle

# Docker ile başlat
docker-compose up -d

# Web interface'e eriş
# http://localhost
```

### 2. Manuel Kurulum

#### Backend

```bash
cd backend

# Dependencies yükle
pip install -r requirements.txt

# Database oluştur
python database.py

# FastAPI'yi başlat
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Dependencies yükle
npm install

# Development server
npm run serve

# Production build
npm run build
```

## 📚 Kullanım

### İlk Konfigürasyon

1. **Settings sayfasına git:** API credentials'ınızı girin
   - Private Key (PK)
   - Wallet Address

2. **Markets sayfasından crypto marketleri çek:**
   - "Fetch Crypto Markets" butonuna tıkla
   - Sistem tüm crypto-ilişkili marketleri otomatik olarak çekecek

3. **Market konfigürasyonu yap:**
   - Her market için "Configure" butonuna tıkla
   - **Side to Trade:** YES / NO / BOTH seç
   - **Trading Mode:** Market Making / Position Building / Hybrid seç
   - **Target Position:** (Position Building modunda) hedef pozisyon miktarı
   - **Trading Parameters:** trade_size, max_size, stop_loss vb.

4. **Trading'i başlat:**
   - Dashboard'a dön
   - "Start Trading" butonuna tıkla

### Trading Modes Detayları

#### Market Making Mode
```
Strategi: Sürekli alım-satım ile spread'den kazanç
Kullanım: Likit marketler, düşük volatilite
Davranış:
- Her iki tarafta da limit orderlar
- Buy -> immediate sell placement
- Max_size'a kadar pozisyon büyütme
```

#### Position Building Mode
```
Strategi: Belirli bir tarafa conviction ile pozisyon oluşturma
Kullanım: Yüksek conviction, uzun vade
Davranış:
- Sadece buy orderlar (target'a kadar)
- Target'a ulaşınca sell orderlar başlar
- Pozisyonu resolution'a kadar tutma
```

#### Hybrid Mode
```
Strategi: Önce pozisyon oluştur, sonra market making yap
Kullanım: Balanced approach, orta-uzun vade
Davranış:
- Target'a kadar agresif buy
- Küçük profit-taking sells (position building sırasında)
- Target'a ulaşınca tam market making moduna geç
```

### Side Selection

**YES:** Sadece token1'i (Yes tarafını) trade et
```yaml
Kullanım: Bitcoin yükselecek diye düşünüyorsun
Örnek: "Will Bitcoin reach $100k?" - YES trade et
```

**NO:** Sadece token2'yi (No tarafını) trade et
```yaml
Kullanım: Bir olayın olmayacağına inanıyorsun
Örnek: "Will Bitcoin crash below $50k?" - NO trade et
```

**BOTH:** Her iki tarafı da trade et (default market making)
```yaml
Kullanım: Neutral, sadece spread'den kazanmak
Örnek: Volatil marketlerde spread yakalama
```

## 🏗️ Architecture

```
poly-maker/
├── backend/                 # FastAPI backend
│   ├── main.py             # FastAPI app
│   ├── database.py         # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── api/                # API endpoints
│   │   ├── markets.py
│   │   ├── trading.py
│   │   ├── positions.py
│   │   ├── orders.py
│   │   ├── settings.py
│   │   └── stats.py
│   └── services/           # Business logic
│       ├── market_service.py
│       └── trading_service.py
│
├── frontend/               # Vue.js frontend
│   ├── src/
│   │   ├── views/         # Pages
│   │   │   ├── Dashboard.vue
│   │   │   ├── Markets.vue
│   │   │   ├── Positions.vue
│   │   │   ├── Orders.vue
│   │   │   └── Settings.vue
│   │   ├── store/         # Vuex state
│   │   ├── api/           # API client
│   │   └── router/        # Vue Router
│   └── public/
│
├── poly_data/             # Core trading logic
│   ├── trading.py         # Main trading loop
│   ├── trading_utils.py   # Trading utilities
│   ├── db_utils.py        # Database operations
│   └── polymarket_client.py
│
├── poly_merger/           # Position merging
├── data_updater/          # Market data fetching
├── docker-compose.yml     # Docker orchestration
└── DEPLOYMENT.md          # Deployment guide
```

## 🔐 Güvenlik

- Private key'ler environment variable'larda saklanır
- Database şifreleme (production için önerilir)
- HTTPS/SSL zorunlu (production)
- API rate limiting
- CORS configuration

## 📊 Database Schema

```sql
-- Markets: Market configuration
id, condition_id, question, token1, token2, 
side_to_trade, trading_mode, target_position, is_active

-- TradingParams: Trading parameters per market
market_id, trade_size, max_size, stop_loss_threshold,
take_profit_threshold, order_front_running, tick_improvement

-- Positions: Current positions
token_id, size, avg_price, side, unrealized_pnl, realized_pnl

-- Orders: Order history
order_id, token_id, side_type, price, size, status

-- GlobalSettings: Bot-wide settings
key, value, description
```

## 🚢 Deployment

Detaylı deployment talimatları için [DEPLOYMENT.md](DEPLOYMENT.md) dosyasına bakın.

### Production Checklist

- [ ] Domain DNS ayarları
- [ ] SSL sertifikası (Let's Encrypt)
- [ ] Environment variables (.env)
- [ ] Firewall configuration
- [ ] Database backups
- [ ] Monitoring setup
- [ ] Log rotation

## 🐛 Troubleshooting

### Backend başlamıyor
```bash
# Logları kontrol et
docker-compose logs backend

# Database sorunları
python backend/database.py
```

### Frontend API'ye bağlanamıyor
```bash
# CORS ayarlarını kontrol et
# backend/main.py içinde allow_origins
```

### Trading bot çalışmıyor
```bash
# Credentials kontrolü
# .env dosyasında PK ve BROWSER_ADDRESS

# Logları incele
docker-compose logs trading-bot
```

## 📈 Performance Tips

1. **SQLite Optimization:** Production için PostgreSQL kullanın
2. **Caching:** Redis ekleyin (market data için)
3. **Load Balancing:** Multiple bot instances
4. **Resource Limits:** Docker resource constraints ayarlayın

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## ⚠️ Disclaimer

Bu bot gerçek para ile trade yapar. Kullanmadan önce:
- Küçük miktarlarla test edin
- Risk yönetimini anlayın
- Kayıpları karşılayabileceğinizden emin olun
- Market volatilitesine hazırlıklı olun

## 🙋 Support

- Documentation: Bu README ve DEPLOYMENT.md
- Issues: GitHub Issues
- Discussions: GitHub Discussions

## 🎯 Roadmap

- [ ] Multi-chain support
- [ ] Advanced charting
- [ ] Telegram notifications
- [ ] Machine learning predictions
- [ ] Portfolio optimization
- [ ] Backtesting framework

---

Made with ❤️ for Polymarket traders

