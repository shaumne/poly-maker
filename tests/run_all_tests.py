"""
Test Runner - Tüm testleri tek bir noktadan çalıştırma

Bu dosya tüm testleri çalıştırır ve sonuçları raporlar.
"""
import sys
import os
import pytest
from pathlib import Path

# Proje root dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend'))

def run_all_tests():
    """Tüm testleri çalıştır"""
    print("=" * 80)
    print("POLYMARKET TRADING BOT - TÜM TESTLER")
    print("=" * 80)
    print()
    
    # Test dizini
    test_dir = Path(__file__).parent
    
    # Test dosyalarını bul
    test_files = list(test_dir.glob("test_*.py"))
    
    if not test_files:
        print("⚠️  Hiç test dosyası bulunamadı!")
        return 1
    
    print(f"📋 Bulunan test dosyaları ({len(test_files)}):")
    for test_file in test_files:
        print(f"   - {test_file.name}")
    print()
    
    # Database'i başlat
    print("🔧 Veritabanı başlatılıyor...")
    try:
        from backend.database import init_db
        init_db()
        print("✅ Veritabanı başlatıldı")
    except Exception as e:
        print(f"⚠️  Veritabanı başlatma hatası: {e}")
        print("   Testler devam edecek...")
    print()
    
    # Test argümanları
    pytest_args = [
        str(test_dir),
        "-v",  # Verbose
        "--tb=short",  # Kısa traceback
        "--color=yes",  # Renkli çıktı
        "-W", "ignore::DeprecationWarning",  # Deprecation uyarılarını yoksay
    ]
    
    # Coverage için ek argümanlar (eğer pytest-cov yüklüyse)
    try:
        import pytest_cov
        pytest_args.extend([
            "--cov=backend.services",
            "--cov=backend.api",
            "--cov-report=term-missing",
            "--cov-report=html",
        ])
        print("📊 Code coverage aktif")
    except ImportError:
        print("ℹ️  pytest-cov yüklü değil, coverage raporu oluşturulmayacak")
    
    print()
    print("🚀 Testler başlatılıyor...")
    print("=" * 80)
    print()
    
    # Testleri çalıştır
    exit_code = pytest.main(pytest_args)
    
    print()
    print("=" * 80)
    if exit_code == 0:
        print("✅ TÜM TESTLER BAŞARILI!")
    else:
        print(f"❌ BAZI TESTLER BAŞARISIZ (Exit code: {exit_code})")
    print("=" * 80)
    
    return exit_code


def run_specific_test(test_name: str):
    """Belirli bir test dosyasını çalıştır"""
    test_dir = Path(__file__).parent
    test_file = test_dir / f"test_{test_name}.py"
    
    if not test_file.exists():
        print(f"❌ Test dosyası bulunamadı: {test_file}")
        return 1
    
    print(f"🎯 Tek test çalıştırılıyor: {test_file.name}")
    print()
    
    # Database'i başlat
    try:
        from backend.database import init_db
        init_db()
    except Exception as e:
        print(f"⚠️  Veritabanı başlatma hatası: {e}")
    
    exit_code = pytest.main([
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes",
    ])
    
    return exit_code


def run_specific_test_class(test_file: str, test_class: str):
    """Belirli bir test sınıfını çalıştır"""
    test_dir = Path(__file__).parent
    test_file_path = test_dir / f"test_{test_file}.py"
    
    if not test_file_path.exists():
        print(f"❌ Test dosyası bulunamadı: {test_file_path}")
        return 1
    
    print(f"🎯 Test sınıfı çalıştırılıyor: {test_class}")
    print()
    
    # Database'i başlat
    try:
        from backend.database import init_db
        init_db()
    except Exception as e:
        print(f"⚠️  Veritabanı başlatma hatası: {e}")
    
    exit_code = pytest.main([
        f"{test_file_path}::{test_class}",
        "-v",
        "--tb=short",
        "--color=yes",
    ])
    
    return exit_code


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Polymarket Trading Bot Test Runner")
    parser.add_argument(
        "--test",
        type=str,
        help="Belirli bir test dosyasını çalıştır (dosya adı, 'test_' prefix olmadan)",
    )
    parser.add_argument(
        "--class",
        type=str,
        dest="test_class",
        help="Belirli bir test sınıfını çalıştır (TestClassName formatında)",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Test sınıfı için dosya adı (--class ile birlikte kullanılır)",
    )
    
    args = parser.parse_args()
    
    if args.test:
        exit_code = run_specific_test(args.test)
    elif args.test_class and args.file:
        exit_code = run_specific_test_class(args.file, args.test_class)
    else:
        exit_code = run_all_tests()
    
    sys.exit(exit_code)

