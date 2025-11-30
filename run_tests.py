#!/usr/bin/env python
"""
Test Runner - Proje root'tan tüm testleri çalıştırma

Kullanım:
    python run_tests.py              # Tüm testleri çalıştır
    python run_tests.py --test market_integration  # Belirli test
    python run_tests.py --help       # Yardım
"""
import sys
import os
from pathlib import Path

# Proje root'u path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend'))

# Test runner'ı import et ve çalıştır
if __name__ == "__main__":
    from tests.run_all_tests import run_all_tests, run_specific_test, run_specific_test_class
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

