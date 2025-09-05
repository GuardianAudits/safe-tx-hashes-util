#!/usr/bin/env python3
# safe_queue_collector.py — fetch + local EIP-712 verify + optional bash verify + simulate (pretty logs)

import json
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

import requests
from eth_utils import keccak, to_bytes, to_canonical_address
from eth_abi import encode

# ============================
# CONFIG
# ============================

# network: (chain_id, client_gateway_base, safe_address)
NETWORKS: Dict[str, Tuple[int, str, str]] = {
    # Global client gateway (works for these)
    "ethereum":   (1,        "https://safe-client.safe.global",               "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8"),
    "arbitrum":   (42161,    "https://safe-client.safe.global",               "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8"),
    "polygon":    (137,      "https://safe-client.safe.global",               "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8"),
    "optimism":   (10,       "https://safe-client.safe.global",               "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8"),
    "ink":        (57073,    "https://safe-client.safe.global",               "0xc95de55ce5e93f788A1Faab2A9c9503F51a5dAE2"),
    "unichain":   (130,      "https://safe-client.safe.global",               "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8"),
    "xlayer":     (196,      "https://safe-client.safe.global",               "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8"),

    # Custom client gateways
    "berachain":  (80094,    "https://gateway.safe.berachain.com",            "0x425d1D17C33bdc0615eA18D1b18CCA7e14bEeb58"),
    "flare":      (14,       "https://prod.flare-client-gateway.keypersafe.xyz", "0x6ae078461f35c3cC216A71029F71ee7Bc4d9a10b"),
    "corn":       (21000000, "https://safe-cgw-corn.safe.onchainden.com",     "0x57d798f9d3B014bAC81A6B9fb3c18c0242A9411E"),
    "sei":        (1329,     "https://gateway.sei-safe.protofire.io",         "0x4DFF9b5b0143E642a3F63a5bcf2d1C328e600bf8"),
    "rootstock":  (30,       "https://gateway.safe.rootstock.io",             "0x425d1D17C33bdc0615eA18D1b18CCA7e14bEeb58"),
    "hyperliquid":(999,      "https://gateway.safe.protofire.io",             "0xB64A89AD247a2D691A728Bb6822a85EeDD7Fc541"),
}

# Transaction Service bases (for Safe version lookup when available)
TS_BASES: Dict[str, str] = {
    "ethereum":   "https://safe-transaction-mainnet.safe.global",
    "arbitrum":   "https://safe-transaction-arbitrum.safe.global",
    "polygon":    "https://safe-transaction-polygon.safe.global",
    "optimism":   "https://safe-transaction-optimism.safe.global",
    "xlayer":     "https://safe-transaction-xlayer.safe.global",
    "ink":        "https://safe-transaction-ink.safe.global",
    "unichain":   "https://safe-transaction-unichain.safe.global",

    "berachain":  "https://transaction.safe.berachain.com",
    "sei":        "https://transaction.sei-safe.protofire.io",
    "corn":       "https://safe-transaction-corn-maizenet.safe.onchainden.com",
    "flare":      "https://prod.flare.keypersafe.xyz",  # if it exposes /api/v1/safes
    "rootstock":  "https://gateway.safe.rootstock.io",
    "hyperliquid":"https://gateway.safe.protofire.io",
}

# RPCs for simulate_actions
network_to_rpc = {
    "ethereum": "https://eth-mainnet.g.alchemy.com/v2/NZMxbTFkijopq9I0cAU88Mt0HE4xvgtX",
    "arbitrum": "https://arb1.arbitrum.io/rpc",
    "flare": "https://flare-api.flare.network/ext/bc/C/rpc",
    "berachain": "https://rpc.berachain.com/",
    "ink": "https://rpc-gel.inkonchain.com",
    "unichain": "https://unichain-rpc.publicnode.com",
    "sei": "https://evm-rpc.sei-apis.com",
    "corn": "https://mainnet.corn-rpc.com",
    "optimism": "https://mainnet.optimism.io/",
    "polygon": "https://polygon-rpc.com/",
    "xlayer": "https://rpc.ankr.com/xlayer",
    "hyperliquid": "https://rpc.hyperliquid.xyz/evm",
    "rootstock": "https://public-node.rsk.co",
}

network_to_safe_address = {net: safe for net, (_, _, safe) in NETWORKS.items()}

# ============================
# EIP-712 CONSTANTS
# ============================

DOMAIN_SEPARATOR_TYPEHASH     = keccak(text="EIP712Domain(uint256 chainId,address verifyingContract)")
DOMAIN_SEPARATOR_TYPEHASH_OLD = keccak(text="EIP712Domain(address verifyingContract)")
SAFE_TX_TYPEHASH              = keccak(text="SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 baseGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)")
SAFE_TX_TYPEHASH_OLD          = keccak(text="SafeTx(address to,uint256 value,bytes data,uint8 operation,uint256 safeTxGas,uint256 dataGas,uint256 gasPrice,address gasToken,address refundReceiver,uint256 nonce)")

ZERO = "0x0000000000000000000000000000000000000000"

# ============================
# Helpers: HTTP
# ============================

def get_json(session: requests.Session, url: str) -> Any:
    r = session.get(url, timeout=25)
    r.raise_for_status()
    return r.json()

def fetch_queued_ids(session: requests.Session, base: str, chain_id: int, safe: str) -> List[str]:
    ids: List[str] = []
    url = f"{base}/v1/chains/{chain_id}/safes/{safe}/transactions/queued"
    while url:
        data = get_json(session, url)
        results = data.get("results", data if isinstance(data, list) else [])
        for row in results:
            if row.get("type") != "TRANSACTION":
                continue
            txid = (row.get("transaction") or {}).get("id") or row.get("id")
            if txid:
                ids.append(txid)
        next_url = data.get("next")
        if next_url and next_url.startswith("/"):
            next_url = base + next_url
        url = next_url
    return ids

def fetch_tx_detail(session: requests.Session, base: str, chain_id: int, tx_id: str) -> Dict[str, Any]:
    url = f"{base}/v1/chains/{chain_id}/transactions/{tx_id}"
    return get_json(session, url)

def fetch_safe_version(session: requests.Session, network: str, safe: str) -> str:
    ts = TS_BASES.get(network)
    if not ts:
        return "1.3.0"
    url = f"{ts}/api/v1/safes/{safe}/"
    try:
        data = get_json(session, url)
        ver = data.get("version") or "1.3.0"
        return ver
    except Exception:
        return "1.3.0"

# ============================
# EIP-712 hashing (Python)
# ============================

def _is_legacy_domain(version: str) -> bool:
    v = (version or "").split("+", 1)[0]
    parts = (v.split(".") + ["0", "0"])[:3]
    try:
        major, minor, patch = map(int, parts)
    except ValueError:
        return False
    return (major < 1) or (major == 1 and minor <= 2)

def _is_legacy_tx(version: str) -> bool:
    v = (version or "").split("+", 1)[0]
    parts = (v.split(".") + ["0", "0"])[:3]
    try:
        major, minor, patch = map(int, parts)
    except ValueError:
        return False
    return (major == 0)  # < 1.0.0

def compute_domain_hash(chain_id: int, safe_address: str, version: str) -> bytes:
    if _is_legacy_domain(version):
        return keccak(encode(
            ["bytes32", "address"],
            [DOMAIN_SEPARATOR_TYPEHASH_OLD, to_canonical_address(safe_address)]
        ))
    else:
        return keccak(encode(
            ["bytes32", "uint256", "address"],
            [DOMAIN_SEPARATOR_TYPEHASH, chain_id, to_canonical_address(safe_address)]
        ))

def compute_message_hash(tx: Dict[str, Any], version: str) -> bytes:
    data_hex = tx.get("data", "0x") or "0x"
    data_hash = keccak(to_bytes(hexstr=data_hex))
    typehash = SAFE_TX_TYPEHASH_OLD if _is_legacy_tx(version) else SAFE_TX_TYPEHASH

    return keccak(encode(
        ["bytes32","address","uint256","bytes32","uint8","uint256","uint256","uint256","address","address","uint256"],
        [
            typehash,
            to_canonical_address(tx.get("to", ZERO)),
            int(str(tx.get("value", "0")), 0) if str(tx.get("value","0")).startswith("0x") else int(str(tx.get("value","0"))),
            data_hash,
            int(tx.get("operation", 0)),
            int(tx.get("safeTxGas", 0)),
            int(tx.get("baseGas", 0)),
            int(tx.get("gasPrice", 0)),
            to_canonical_address(tx.get("gasToken", ZERO)),
            to_canonical_address(tx.get("refundReceiver", ZERO)),
            int(tx.get("nonce", 0)),
        ]
    ))

def compute_safe_tx_hash(domain_hash: bytes, message_hash: bytes) -> bytes:
    return keccak(b"\x19\x01" + domain_hash + message_hash)

# ============================
# Core: fetch + verify (PRETTY LOGS)
# ============================

def fetch_and_verify() -> List[Dict[str, Any]]:
    """
    For each network:
      - list queued tx ids
      - fetch detail
      - compute domain/message/safeTxHash locally
      - compare with API’s safeTxHash (if present)
    Writes data.json with full details and returns the rows.
    """
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    rows: List[Dict[str, Any]] = []

    print("\n" + "=" * 78)
    print("FETCH & VERIFY (local EIP-712)".center(78))
    print("=" * 78)

    for net, (cid, base, safe) in NETWORKS.items():
        ok = mism = noapi = 0
        print(f"\n[{datetime.now().isoformat(timespec='seconds')}] Network: {net} | chainId={cid}")
        print(f"Safe: {safe}")
        try:
            version = fetch_safe_version(session, net, safe)
        except Exception as e:
            print(f"  ! Version lookup failed, defaulting 1.3.0: {e}")
            version = "1.3.0"

        try:
            ids = fetch_queued_ids(session, base, cid, safe)
            print(f"  Queued: {len(ids)}")
        except Exception as e:
            print(f"  [!] Error fetching list: {e}")
            continue

        for txid in ids:
            try:
                detail = fetch_tx_detail(session, base, cid, txid)
                txdata = detail.get("txData") or {}
                execinfo = detail.get("detailedExecutionInfo") or {}

                # normalize fields
                to_field = txdata.get("to")
                to_addr = to_field.get("value") if isinstance(to_field, dict) else (to_field or ZERO)
                value = txdata.get("value", "0") or "0"
                hex_data = txdata.get("hexData", "0x") or "0x"
                operation = int(execinfo.get("operation", txdata.get("operation", 0)) or 0)

                safe_tx_gas = int(execinfo.get("safeTxGas", 0) or 0)
                base_gas    = int(execinfo.get("baseGas", 0) or 0)
                gas_price   = int(execinfo.get("gasPrice", 0) or 0)

                gas_token_obj = execinfo.get("gasToken", ZERO)
                gas_token = (gas_token_obj.get("value") if isinstance(gas_token_obj, dict) else gas_token_obj) or ZERO

                rr_obj = execinfo.get("refundReceiver", ZERO)
                refund_receiver = (rr_obj.get("value") if isinstance(rr_obj, dict) else rr_obj) or ZERO

                nonce = int(execinfo.get("nonce", 0) or 0)

                # local EIP-712 compute
                domain_hash = compute_domain_hash(cid, safe, version)
                msg_hash    = compute_message_hash({
                    "to": to_addr,
                    "value": value,
                    "data": hex_data,
                    "operation": operation,
                    "safeTxGas": safe_tx_gas,
                    "baseGas": base_gas,
                    "gasPrice": gas_price,
                    "gasToken": gas_token,
                    "refundReceiver": refund_receiver,
                    "nonce": nonce,
                }, version)
                safe_tx_hash_local = compute_safe_tx_hash(domain_hash, msg_hash).hex()

                # API-reported safetxhash (may be missing on some gateways)
                api_safe_tx_hash = (execinfo.get("safeTxHash") or "").lower()

                verified = (
                    (api_safe_tx_hash != "" and api_safe_tx_hash == safe_tx_hash_local) or
                    (api_safe_tx_hash != "" and api_safe_tx_hash == ("0x"+safe_tx_hash_local[2:] if safe_tx_hash_local.startswith("0x") else "0x"+safe_tx_hash_local))
                )

                row = {
                    "network": net,
                    "chain_id": cid,
                    "safe_address": safe,
                    "tx_id": txid,
                    "nonce": str(nonce),
                    "to_address": to_addr,
                    "hex_data": hex_data,
                    "value": str(value),
                    "operation": operation,
                    # API values (if present)
                    "api_safe_tx_hash": api_safe_tx_hash,
                    # Local computed
                    "computed_domain_hash": domain_hash.hex(),
                    "computed_message_hash": msg_hash.hex(),
                    "computed_safe_tx_hash": safe_tx_hash_local,
                    "safe_version": version,
                    "verified": bool(verified),
                }
                rows.append(row)

                # pretty per-tx line: Safe first, then nonce only
                if api_safe_tx_hash:
                    if verified:
                        print(f"  ✅ Safe {safe}  nonce={nonce}")
                        ok += 1
                    else:
                        print(f"  ⚠️  Safe {safe}  nonce={nonce}  (API/local hash mismatch)")
                        mism += 1
                else:
                    print(f"  ➖ Safe {safe}  nonce={nonce}  (no api safeTxHash)")
                    noapi += 1

            except Exception as e:
                print(f"  [!] detail error ({txid}): {e}")

        # network summary
        print(f"  — Summary: ✅ {ok} | ⚠️ {mism} | ➖ {noapi}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4)
    print("\n" + "=" * 78)
    print(f"[✓] Wrote {len(rows)} transactions to data.json".center(78))
    print("=" * 78 + "\n")
    return rows

# ============================
# Legacy: scrape-only (kept for parity)
# ============================

def scrape_all() -> List[Dict[str, str]]:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    rows: List[Dict[str, str]] = []

    for net, (cid, base, safe) in NETWORKS.items():
        print(f"[+] {net}: chainId={cid}, safe={safe}")
        try:
            ids = fetch_queued_ids(session, base, cid, safe)
            print(f"    found {len(ids)} queued txs")
        except Exception as e:
            print(f"    [!] error fetching list: {e}")
            continue

        for txid in ids:
            try:
                detail = fetch_tx_detail(session, base, cid, txid)
                txdata = detail.get("txData") or {}
                execinfo = detail.get("detailedExecutionInfo") or {}
                to_field = txdata.get("to")
                to_addr = to_field.get("value") if isinstance(to_field, dict) else to_field

                rows.append({
                    "network": net,
                    "address": safe,
                    "to_address": to_addr or ZERO,
                    "nonce": str(execinfo.get("nonce", "")),
                    "expected_data": txdata.get("hexData", ""),
                    "expected_safe_transaction_hash": execinfo.get("safeTxHash", ""),
                })
            except Exception as e:
                print(f"    [!] detail error {txid}: {e}")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=4)
    print(f"[✓] Wrote {len(rows)} transactions to data.json")
    return rows

# ============================
# Optional: verify via existing bash script
# ============================

def verify_with_bash(bulk_file: str = "data.json"):
    """
    If you still want to run the original bash verifier:
    ./safe_hashes.sh --bulk-file data.json
    """
    env = os.environ.copy()
    env["FOUNDRY_DISABLE_NIGHTLY_WARNING"] = "1"  # mute nightly warnings
    try:
        subprocess.run(
            ["bash", "./safe_hashes.sh", "--bulk-file", bulk_file],
            check=True,
            env=env
        )
    except subprocess.CalledProcessError as e:
        print(f"[!] Bash verification failed (exit={e.returncode}).")
        raise

# ============================
# Simulate — Pretty logs
# ============================

def simulate_actions(only_chains: Optional[set] = None, log_per_tx: bool = False):
    """
    Simulate queued transactions.
    - Writes raw Foundry output (stdout + stderr) into log files, unmodified.
    - All chains if only_chains=None.
    - Grouped per chain or per tx depending on log_per_tx.
    """
    if only_chains is not None:
        only_chains = {str(c).strip().lower() for c in only_chains if c and str(c).strip()}

    with open("data.json", "r", encoding="utf-8") as f:
        txs = json.load(f)

    os.makedirs("logs", exist_ok=True)

    # group by network
    by_net: Dict[str, List[Dict[str, Any]]] = {}
    for tx in txs:
        net = tx["network"].lower()
        if only_chains and net not in only_chains:
            continue
        by_net.setdefault(net, []).append(tx)

    if not by_net:
        available = ", ".join(sorted(NETWORKS.keys()))
        print(f"[!] No transactions matched. Available: {available}")
        return

    for net, items in by_net.items():
        rpc_url = network_to_rpc.get(net)
        safe_addr = network_to_safe_address.get(net)
        if not rpc_url or not safe_addr:
            print(f"[!] Missing RPC or safe for {net}")
            continue

        chain_log_path = os.path.join("logs", f"{net}.log")

        for tx in items:
            txhash = tx.get("api_safe_tx_hash") or tx.get("expected_safe_transaction_hash", "")
            to_addr = tx.get("to_address", tx.get("to", ""))
            hexdata = tx.get("hex_data") or tx.get("expected_data", "")

            # choose log file
            if log_per_tx:
                tx_prefix = (txhash or "nohash")[:10]
                log_path = os.path.join("logs", f"{net}_{tx_prefix}.log")
            else:
                log_path = chain_log_path

            env = os.environ.copy()
            env["FOUNDRY_DISABLE_NIGHTLY_WARNING"] = "1"

            # Just append Foundry output directly
            with open(log_path, "ab") as lf:  # binary append = exact bytes
                proc = subprocess.run(
                    [
                        "cast", "call",
                        to_addr,
                        "--rpc-url", rpc_url,
                        "--from", safe_addr,
                        "--data", hexdata,
                        "--trace",
                    ],
                    stdout=lf,
                    stderr=lf,
                    check=False,
                    env=env,
                )

        print(f"[+] {net}: wrote {len(items)} simulation(s) to {chain_log_path if not log_per_tx else 'per-tx logs'}")
    
# ============================
# Entry points (choose what you need)
# ============================

if __name__ == "__main__":
    # 1) Fetch + verify locally (recommended). Pretty per-tx lines:
    #    "✅/⚠️/➖  Safe <addr>  nonce=<n>"
    # fetch_and_verify()

    # 2) (Optional) also run the original bash bulk verifier on the generated data.json
    # verify_with_bash("data.json")

    # 3) simulate actions, sei + arbitrum; one log per chain
    # simulate_actions(only_chains={"sei", "arbitrum"}, log_per_tx=False)
    # all chains; one log per chain
    simulate_actions(log_per_tx=False)
    # all chains; one log per tx
    # simulate_actions(log_per_tx=True)
