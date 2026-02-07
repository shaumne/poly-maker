# -*- coding: utf-8 -*-
"""
Trading işlemlerini dosyaya loglar. Bot kapandıktan sonra logs/trading.log üzerinden incelenebilir.
"""
import os
import json
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "trading.log")
_lock = None

def _ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def _timestamp():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def trade_log(action: str, message: str, **kwargs):
    """
    Hem konsola yazdırır hem de logs/trading.log dosyasına ekler.
    action: BUY_ORDER, SELL_ORDER, CANCEL, TAKE_PROFIT, STOP_LOSS, SKIP, ERROR, INFO, vb.
    message: Kısa açıklama
    **kwargs: Ek alanlar (token, price, size, result, error, market, pnl, vb.) -> log satırında JSON olarak
    """
    _ensure_log_dir()
    extra = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
    line = f"{_timestamp()} | {action} | {message}" + (f" | {extra}" if extra else "")
    # Konsola da yaz (mevcut davranış)
    print(message if not kwargs else f"{message} {kwargs}")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[trade_log write error] {e}")

def trade_log_only_file(action: str, message: str, **kwargs):
    """Sadece dosyaya yazar, konsola yazmaz (zaten print edilen yerlerde tekrar etmemek için)."""
    _ensure_log_dir()
    extra = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
    line = f"{_timestamp()} | {action} | {message}" + (f" | {extra}" if extra else "")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[trade_log write error] {e}")
