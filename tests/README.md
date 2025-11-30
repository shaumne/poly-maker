# Test Dokümantasyonu

Bu dizin Polymarket Trading Bot için tüm testleri içerir.

## Test Çalıştırma

### Tüm Testleri Çalıştırma

```bash
# Python ile
python tests/run_all_tests.py

# veya pytest ile doğrudan
pytest tests/ -v
```

### Belirli Bir Test Dosyasını Çalıştırma

```bash
# Python ile
python tests/run_all_tests.py --test market_integration

# veya pytest ile doğrudan
pytest tests/test_market_integration.py -v
```

### Belirli Bir Test Sınıfını Çalıştırma

```bash
# Python ile
python tests/run_all_tests.py --file market_integration --class TestMarketMapping

# veya pytest ile doğrudan
pytest tests/test_market_integration.py::TestMarketMapping -v
```

### Belirli Bir Test Fonksiyonunu Çalıştırma

```bash
pytest tests/test_market_integration.py::TestMarketMapping::test_get_market_by_token_id -v
```

## Test Dosyaları

### test_market_integration.py

Market entegrasyonu ve sipariş oluşturma akışı için kapsamlı testler:

- **TestMarketMapping**: Token-market mapping servisi testleri
- **TestOrderValidation**: Sipariş doğrulama servisi testleri
- **TestMarketCacheService**: Cache servisi testleri
- **TestIntegrationFlow**: End-to-end entegrasyon testleri

## Test Gereksinimleri

Testleri çalıştırmak için gerekli paketler:

```bash
pip install pytest pytest-cov
```

## Test Veritabanı

Testler otomatik olarak test veritabanı oluşturur ve temizler. Varsayılan olarak SQLite kullanır.

## Coverage Raporu

Code coverage raporu oluşturmak için:

```bash
pytest tests/ --cov=backend.services --cov=backend.api --cov-report=html
```

Rapor `htmlcov/index.html` dosyasında oluşturulur.

