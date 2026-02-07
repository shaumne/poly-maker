"""
Proxy (Gnosis Safe) üzerinden CTF setApprovalForAll çağrısı.
Böylece bot, outcome token satışı için gerekli on-chain izni kendisi verebilir;
manuel satış veya tarayıcıdan approve gerekmez.
"""
import os
import logging
from typing import Optional

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account

logger = logging.getLogger(__name__)

# Gnosis Safe execTransaction + getTransactionHash + nonce (minimal ABI)
SAFE_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "_nonce", "type": "uint256"}],
        "name": "nonce",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
            {"internalType": "uint8", "name": "operation", "type": "uint8"},
            {"internalType": "uint256", "name": "safeTxGas", "type": "uint256"},
            {"internalType": "uint256", "name": "baseGas", "type": "uint256"},
            {"internalType": "uint256", "name": "gasPrice", "type": "uint256"},
            {"internalType": "address", "name": "gasToken", "type": "address"},
            {"internalType": "address", "name": "refundReceiver", "type": "address"},
            {"internalType": "uint256", "name": "_nonce", "type": "uint256"},
        ],
        "name": "getTransactionHash",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
            {"internalType": "uint8", "name": "operation", "type": "uint8"},
            {"internalType": "uint256", "name": "safeTxGas", "type": "uint256"},
            {"internalType": "uint256", "name": "baseGas", "type": "uint256"},
            {"internalType": "uint256", "name": "gasPrice", "type": "uint256"},
            {"internalType": "address", "name": "gasToken", "type": "address"},
            {"internalType": "address payable", "name": "refundReceiver", "type": "address"},
            {"internalType": "bytes", "name": "signatures", "type": "bytes"},
        ],
        "name": "execTransaction",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "payable",
        "type": "function",
    },
]

CTF_SET_APPROVAL_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "bool", "name": "approved", "type": "bool"},
        ],
        "name": "setApprovalForAll",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

# Polymarket exchange adresleri (proxy bu adreslere CTF token harcama izni verecek)
EXCHANGE_ADDRESSES = [
    "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",  # CTF Exchange
    "0xC5d563A36AE78145C45a50134d48A1215220f80a",  # Neg Risk CTF Exchange
    "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296",  # Neg Risk Adapter
]
CTF_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"


def _get_web3():
    w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def ensure_ctf_allowance_via_proxy(
    proxy_address: str,
    eoa_private_key: str,
    exchange_addresses: Optional[list] = None,
) -> bool:
    """
    Proxy (Gnosis Safe) üzerinden CTF setApprovalForAll(operator, True) çalıştırır.
    Böylece proxy'deki outcome token'lar exchange tarafından harcanabilir (satış çalışır).

    Args:
        proxy_address: Polymarket proxy (Safe) adresi (BROWSER_ADDRESS).
        eoa_private_key: Proxy'yi yöneten EOA'nın private key'i (PK).
        exchange_addresses: Onay verilecek exchange adresleri; None ise varsayılan 3 adres.

    Returns:
        True tüm approval'lar başarılıysa, aksi halde False.
    """
    exchange_addresses = exchange_addresses or EXCHANGE_ADDRESSES
    w3 = _get_web3()
    account = Account.from_key(eoa_private_key)
    proxy_address = Web3.to_checksum_address(proxy_address)
    safe = w3.eth.contract(address=proxy_address, abi=SAFE_ABI)
    ctf = w3.eth.contract(address=Web3.to_checksum_address(CTF_ADDRESS), abi=CTF_SET_APPROVAL_ABI)

    for exchange in exchange_addresses:
        exchange = Web3.to_checksum_address(exchange)
        try:
            # Zaten approved mu kontrol et (opsiyonel; başarısız olursa devam ederiz)
            # CTF.isApprovedForAll(proxy, exchange) için ABI gerekir; şimdilik her seferinde gönderiyoruz
            calldata = ctf.encode_abi("setApprovalForAll", [exchange, True])
            nonce = safe.functions.nonce().call()
            safe_tx_gas = 0
            base_gas = 0
            gas_price = 0
            gas_token = "0x0000000000000000000000000000000000000000"
            refund_receiver = "0x0000000000000000000000000000000000000000"

            raw_hash = safe.functions.getTransactionHash(
                Web3.to_checksum_address(CTF_ADDRESS),
                0,
                calldata,
                0,  # Call
                safe_tx_gas,
                base_gas,
                gas_price,
                gas_token,
                refund_receiver,
                nonce,
            ).call()

            if hasattr(raw_hash, "tobytes"):
                tx_hash_bytes = raw_hash.tobytes()
            elif isinstance(raw_hash, (str,)):
                tx_hash_bytes = bytes.fromhex(raw_hash.replace("0x", ""))
            else:
                tx_hash_bytes = bytes(raw_hash)
            if len(tx_hash_bytes) != 32:
                tx_hash_bytes = (bytes(32 - len(tx_hash_bytes)) + tx_hash_bytes) if len(tx_hash_bytes) < 32 else tx_hash_bytes[:32]

            signed = Account.unsafe_sign_hash(tx_hash_bytes, eoa_private_key)
            sig_bytes = signed.signature
            if len(sig_bytes) != 65:
                sig_bytes = sig_bytes[:65]

            exec_tx = safe.functions.execTransaction(
                Web3.to_checksum_address(CTF_ADDRESS),
                0,
                calldata,
                0,
                safe_tx_gas,
                base_gas,
                gas_price,
                gas_token,
                refund_receiver,
                sig_bytes,
            )
            built = exec_tx.build_transaction({
                "from": account.address,
                "chainId": 137,
                "gas": 200_000,
                "nonce": w3.eth.get_transaction_count(account.address),
            })
            signed_tx = w3.eth.account.sign_transaction(built, private_key=eoa_private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if not receipt.get("status") == 1:
                logger.warning("Proxy CTF approval tx failed for %s", exchange)
                return False
            logger.info("Proxy CTF approval succeeded for %s", exchange)
        except Exception as e:
            logger.exception("Proxy CTF approval failed for %s: %s", exchange, e)
            return False
    return True
