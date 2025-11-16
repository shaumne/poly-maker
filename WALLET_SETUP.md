# 🔑 Wallet Setup Guide

## Sorun: "when sending a str, it must be a hex string"

Bu hata, `.env` dosyasındaki wallet adresinin placeholder değer olarak kaldığını gösterir.

## ✅ Çözüm

### 1. `.env` Dosyasını Kontrol Edin

`.env` dosyanızı açın ve şu satırları kontrol edin:

```bash
PK=your_private_key_here
BROWSER_ADDRESS=your_actual_wallet_address
```

### 2. Gerçek Değerleri Girin

**ÖNEMLİ:** Placeholder değerleri gerçek değerlerle değiştirin!

```bash
# Örnek (GERÇEK DEĞERLERİNİZİ GİRİN!)
PK=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
BROWSER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

### 3. Format Kontrolü

**Private Key (PK):**
- ✅ `0x` ile başlamalı
- ✅ 66 karakter uzunluğunda olmalı (0x + 64 hex karakter)
- ❌ Placeholder değer olmamalı

**Wallet Address (BROWSER_ADDRESS):**
- ✅ `0x` ile başlamalı
- ✅ 42 karakter uzunluğunda olmalı (0x + 40 hex karakter)
- ❌ Placeholder değer olmamalı

### 4. Örnek `.env` Dosyası

```bash
# ==================== TRADING MODE ====================
DRY_RUN=true

# ==================== POLYMARKET CREDENTIALS ====================
# ⚠️ BURAYA GERÇEK DEĞERLERİNİZİ GİRİN!
PK=0xYOUR_ACTUAL_PRIVATE_KEY_HERE_64_CHARS_AFTER_0x
BROWSER_ADDRESS=0xYOUR_ACTUAL_WALLET_ADDRESS_HERE_40_CHARS_AFTER_0x

# ==================== SAFETY LIMITS ====================
MAX_POSITION_SIZE=100
MAX_TRADE_SIZE=10
MIN_TRADE_SIZE=1

# ==================== API CONFIGURATION ====================
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:8080

# ==================== DATABASE ====================
DATABASE_URL=sqlite:///./polymarket_bot.db
```

## 🔍 Değerleri Nereden Bulabilirim?

### Private Key (PK)
1. MetaMask veya başka bir wallet'ınızdan export edin
2. **DİKKAT:** Private key'i asla paylaşmayın!
3. Format: `0x` + 64 hex karakter

### Wallet Address (BROWSER_ADDRESS)
1. MetaMask veya wallet'ınızda "Account Details" bölümünden kopyalayın
2. Format: `0x` + 40 hex karakter
3. Örnek: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb`

## ⚠️ Güvenlik Uyarıları

1. **`.env` dosyasını ASLA Git'e commit etmeyin!**
2. Private key'inizi kimseyle paylaşmayın
3. `.gitignore` dosyasında `.env` olduğundan emin olun
4. Production'da environment variables kullanın

## 🧪 Test

Değerleri girdikten sonra:

1. Backend'i yeniden başlatın
2. Dashboard'a gidin: http://localhost:8080
3. USDC Balance kartını kontrol edin
4. Eğer hala hata alıyorsanız, backend log'larını kontrol edin

## ❓ Hala Sorun mu Var?

1. **Backend log'larını kontrol edin:**
   ```bash
   # Backend terminal'inde hata mesajlarını görün
   ```

2. **Wallet adresini doğrulayın:**
   - Etherscan'de adresinizi arayın: https://polygonscan.com/
   - Format doğru mu kontrol edin

3. **Private key formatını kontrol edin:**
   - `0x` ile başlıyor mu?
   - 66 karakter uzunluğunda mı?
   - Sadece hex karakterler (0-9, a-f) içeriyor mu?

## 📝 Örnek Hata Mesajları ve Çözümleri

### Hata 1: "when sending a str, it must be a hex string"
**Çözüm:** `BROWSER_ADDRESS` değerini gerçek wallet adresiyle değiştirin

### Hata 2: "Private key not configured"
**Çözüm:** `PK` değerini gerçek private key ile değiştirin

### Hata 3: "Invalid wallet address format"
**Çözüm:** Wallet adresinin `0x` ile başladığından ve 42 karakter uzunluğunda olduğundan emin olun

---

**Başarılar!** 🚀

