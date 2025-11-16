# Polymarket Trading Bot - Deployment Guide

Bu rehber, Polymarket Trading Bot'u bir VPS'e deploy etmek ve domain bağlamak için gerekli adımları içerir.

## Gereksinimler

- Ubuntu 20.04+ veya Debian 11+ çalıştıran bir VPS
- En az 2GB RAM
- En az 20GB disk alanı
- Root veya sudo yetkisi
- Bir domain adı (opsiyonel ama önerilir)

## 1. VPS Hazırlığı

### VPS'e Bağlanma

```bash
ssh root@your-vps-ip
```

### Sistem Güncellemesi

```bash
apt update && apt upgrade -y
```

### Docker Kurulumu

```bash
# Docker için gerekli paketler
apt install -y apt-transport-https ca-certificates curl software-properties-common

# Docker GPG anahtarı
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Docker repository
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"

# Docker kurulumu
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Docker Compose kurulumu
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Docker servisini başlat
systemctl start docker
systemctl enable docker
```

### Kurulumu Doğrula

```bash
docker --version
docker-compose --version
```

## 2. Proje Kurulumu

### Kod İndirme

```bash
# Projeyi klonla
cd /opt
git clone https://github.com/yourusername/poly-maker.git
cd poly-maker
```

### Environment Variables Ayarlama

```bash
# .env dosyasını oluştur
cp .env.example .env

# .env dosyasını düzenle
nano .env
```

**.env dosyasına şunları ekleyin:**

```
PK=your_private_key_here
BROWSER_ADDRESS=your_wallet_address_here
DATABASE_URL=sqlite:///./polymarket_bot.db
```

**Önemli:** Private key'inizi güvenli tutun!

### Gerekli Dizinleri Oluşturma

```bash
mkdir -p data positions
chmod 755 data positions
```

## 3. Docker ile Başlatma

### Container'ları Oluşturma ve Başlatma

```bash
# Container'ları build et
docker-compose build

# Container'ları başlat
docker-compose up -d

# Logları kontrol et
docker-compose logs -f
```

### Servislerin Durumunu Kontrol Etme

```bash
docker-compose ps
```

Tüm servisler "Up" durumunda olmalı:
- `polymarket-backend` - FastAPI backend (port 8000)
- `polymarket-frontend` - Vue.js frontend (port 80)
- `polymarket-trading-bot` - Trading bot

### Test Etme

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend erişimi
curl http://localhost
```

## 4. Domain Bağlama

### DNS Ayarları

Domain sağlayıcınızın kontrol panelinden:

1. **A Record** ekleyin:
   - Host: `@` (veya `www`)
   - Value: VPS IP adresiniz
   - TTL: 3600

2. Değişikliklerin yayılması için 10-30 dakika bekleyin

3. Doğrulama:
   ```bash
   nslookup yourdomain.com
   ```

### Nginx ve SSL Sertifikası (Let's Encrypt)

#### Nginx Kurulumu (Production için)

```bash
# Nginx'i yükle
apt install -y nginx certbot python3-certbot-nginx

# Nginx yapılandırması
nano /etc/nginx/sites-available/polymarket-bot
```

**Nginx yapılandırması:**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 100M;
}
```

**Yapılandırmayı etkinleştir:**

```bash
# Symbolic link oluştur
ln -s /etc/nginx/sites-available/polymarket-bot /etc/nginx/sites-enabled/

# Default site'ı kaldır
rm /etc/nginx/sites-enabled/default

# Nginx'i test et
nginx -t

# Nginx'i yeniden başlat
systemctl restart nginx
```

#### SSL Sertifikası (Let's Encrypt)

```bash
# SSL sertifikası al
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Email adresinizi girin ve ToS'u kabul edin
# Otomatik HTTP->HTTPS yönlendirmesini seçin (2)
```

**Otomatik yenileme kontrolü:**

```bash
# Dry run test
certbot renew --dry-run

# Cron job zaten kurulu olmalı, kontrol:
systemctl status certbot.timer
```

## 5. Güvenlik Ayarları

### Firewall (UFW) Kurulumu

```bash
# UFW'yi yükle ve etkinleştir
apt install -y ufw

# SSH, HTTP ve HTTPS portlarını aç
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Firewall'ı etkinleştir
ufw enable

# Durumu kontrol et
ufw status
```

### Fail2Ban (Opsiyonel ama önerilir)

```bash
# Fail2ban kurulumu
apt install -y fail2ban

# Servisi başlat
systemctl start fail2ban
systemctl enable fail2ban
```

## 6. Monitoring ve Bakım

### Logları Görüntüleme

```bash
# Tüm servislerin logları
docker-compose logs -f

# Sadece backend
docker-compose logs -f backend

# Sadece trading bot
docker-compose logs -f trading-bot
```

### Container'ları Yönetme

```bash
# Durdurma
docker-compose stop

# Başlatma
docker-compose start

# Yeniden başlatma
docker-compose restart

# Silme (dikkatli!)
docker-compose down

# Yeniden build ve başlat
docker-compose up -d --build
```

### Veritabanı Yedekleme

```bash
# Manuel yedek
docker exec polymarket-backend sqlite3 /app/polymarket_bot.db ".backup /app/backup_$(date +%Y%m%d).db"

# Yedekleri host'a kopyala
docker cp polymarket-backend:/app/backup_*.db ./backups/

# Otomatik yedekleme için cron job
crontab -e
```

**Cron job ekleyin:**

```bash
# Her gün saat 03:00'te yedek al
0 3 * * * cd /opt/poly-maker && docker exec polymarket-backend sqlite3 /app/polymarket_bot.db ".backup /app/backup_$(date +\%Y\%m\%d).db"
```

### Sistem Kaynakları İzleme

```bash
# Docker container resource kullanımı
docker stats

# Disk kullanımı
df -h

# Memory kullanımı
free -m
```

## 7. Güncelleme

### Kod Güncellemesi

```bash
cd /opt/poly-maker

# Değişiklikleri çek
git pull

# Container'ları yeniden build et
docker-compose down
docker-compose build
docker-compose up -d
```

### Docker Image Temizliği

```bash
# Kullanılmayan image'ları temizle
docker image prune -a

# Tüm kullanılmayan kaynakları temizle
docker system prune -a
```

## 8. Troubleshooting

### Port Çakışması

```bash
# Portları kontrol et
netstat -tulpn | grep LISTEN

# Kullanımda olan portu kullanan process'i durdur
kill -9 <PID>
```

### Container Başlamıyor

```bash
# Detaylı logları görüntüle
docker-compose logs backend
docker-compose logs frontend
docker-compose logs trading-bot

# Container içine gir (debug için)
docker exec -it polymarket-backend bash
```

### Database Bozulması

```bash
# Yedekten geri yükle
docker cp ./backups/backup_20240101.db polymarket-backend:/app/polymarket_bot.db

# Container'ı yeniden başlat
docker-compose restart backend trading-bot
```

### SSL Sertifikası Sorunları

```bash
# Sertifikayı yenile
certbot renew --force-renewal

# Nginx'i yeniden başlat
systemctl restart nginx
```

## 9. Performance Tuning

### Docker Resource Limits

`docker-compose.yml` dosyasında resource limitlerini ayarlayın:

```yaml
services:
  backend:
    # ... diğer ayarlar
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Database Optimization

SQLite için:

```bash
# Vacuum (optimize)
docker exec polymarket-backend sqlite3 /app/polymarket_bot.db "VACUUM;"

# Analyze (statistics)
docker exec polymarket-backend sqlite3 /app/polymarket_bot.db "ANALYZE;"
```

## 10. Web Interface'e Erişim

Kurulum tamamlandıktan sonra:

1. **Domain ile:** `https://yourdomain.com`
2. **IP ile:** `http://your-vps-ip`

İlk giriş:
1. Settings sayfasına gidin
2. API credentials'ınızı girin
3. Markets sayfasından "Fetch Crypto Markets" butonuna tıklayın
4. Marketleri yapılandırın
5. Dashboard'dan trading bot'u başlatın

## Yardım ve Destek

Sorun yaşarsanız:

1. Logları kontrol edin: `docker-compose logs -f`
2. Container durumunu kontrol edin: `docker-compose ps`
3. GitHub Issues'a bakın
4. Yeni issue açın

## Güvenlik Notları

⚠️ **ÖNEMLİ:**

- Private key'inizi asla paylaşmayın
- `.env` dosyasını asla Git'e eklemeyin
- Düzenli olarak sistem ve Docker güncellemelerini yapın
- Güçlü bir SSH şifresi veya SSH key kullanın
- Root login'i devre dışı bırakın (opsiyonel)
- VPS firewall'ını düzgün yapılandırın

## Maintenance Checklist

**Günlük:**
- [ ] Bot'un çalıştığını kontrol et
- [ ] Logları incele
- [ ] PnL'yi gözden geçir

**Haftalık:**
- [ ] Disk alanını kontrol et
- [ ] Database backup kontrolü
- [ ] Performance metrics

**Aylık:**
- [ ] Sistem güncellemeleri
- [ ] Docker image güncellemeleri
- [ ] SSL sertifikası kontrolü
- [ ] Security audit

