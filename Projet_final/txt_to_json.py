"""
txt_to_json.py — Conversion unitaire Solomon .txt -> JSON enrichi

Usage:
  python txt_to_json.py R101 --num-clients 100 [--seed 42]

- Entrée:  Vrp-Set/<INSTANCE>.txt (dossier fixe)
- Sortie:  data/json/<INSTANCE>.json (dossier fixe)

Ajoute les attributs (temperature, access_requires, incompatible_with) avec un RNG privé.
Honorera, si présents dans config.py: REUSE_SAME_RANDOM, EXPLICIT_INCOMP_PROBA,
GENERER_INCOMPAT_ATTRS, GENERER_LISTES_EXPLICITES.
"""

import os
import re
import json
import argparse
import random
import hashlib
import time
import secrets


def _parse_solomon_txt(txt_path: str) -> dict:
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    # Capacité (ligne après VEHICLE + 2)
    cap_idx = next(i for i, ln in enumerate(lines) if ln.upper().startswith('VEHICLE')) + 2
    parts = re.split(r'\s+', lines[cap_idx])
    capacity = float(parts[1])

    # Clients (à partir de CUSTOMER + 2)
    cust_idx = next(i for i, ln in enumerate(lines) if ln.upper().startswith('CUSTOMER')) + 2

    data = {"vehicle_capacity": capacity}
    for ln in lines[cust_idx:]:
        cols = re.split(r'\s+', ln)
        if len(cols) < 7:
            continue
        cid = int(cols[0])
        data[f"customer_{cid}"] = {
            "coordinates": {"x": float(cols[1]), "y": float(cols[2])},
            "demand": float(cols[3]),
            "ready_time": float(cols[4]),
            "due_time": float(cols[5]),
            "service_time": float(cols[6]),
        }

    if "customer_0" not in data:
        raise ValueError("customer_0 manquant dans le .txt (dépôt).")
    return data


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    input_dir = os.path.join(base_dir, 'Vrp-Set')
    output_dir = os.path.join(base_dir, 'data', 'json')

    parser = argparse.ArgumentParser(description="Convertit une instance Solomon .txt en JSON enrichi.")
    parser.add_argument('instance', help="Code instance (ex: R101, C101)")
    parser.add_argument('--num-clients', type=int, required=True, help="Nombre de clients (IDs 1..N) à conserver")
    parser.add_argument('--seed', type=int, default=None, help="Seed aléatoire (si REUSE_SAME_RANDOM=False)")
    args = parser.parse_args()

    base = args.instance
    num_clients = args.num_clients

    # Lire flags éventuels de config
    try:
        import config
        GENERER_INCOMPAT_ATTRS = getattr(config, 'GENERER_INCOMPAT_ATTRS', True)
        GENERER_LISTES_EXPLICITES = getattr(config, 'GENERER_LISTES_EXPLICITES', True)
        REUSE_SAME_RANDOM = getattr(config, 'REUSE_SAME_RANDOM', False)
        EXPLICIT_INCOMP_PROBA = getattr(config, 'EXPLICIT_INCOMP_PROBA', 0.05)
    except Exception:
        GENERER_INCOMPAT_ATTRS = True
        GENERER_LISTES_EXPLICITES = True
        REUSE_SAME_RANDOM = False
        EXPLICIT_INCOMP_PROBA = 0.05

    txt_path = os.path.join(input_dir, f"{base}.txt")
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"Introuvable: {txt_path}")

    # RNG privé
    if REUSE_SAME_RANDOM:
        h = hashlib.sha256()
        with open(txt_path, 'rb') as f:
            h.update(f.read())
        h.update(str(num_clients).encode('utf-8'))
        seed_val = int.from_bytes(h.digest()[:8], 'big')
    elif args.seed is not None:
        seed_val = int(args.seed)
    else:
        seed_val = secrets.randbits(64) ^ (time.time_ns() & ((1 << 64) - 1))
    rng = random.Random(seed_val)
    print(f"[txt_to_json] seed_used={seed_val} stable={REUSE_SAME_RANDOM}")

    # Parse complet
    full = _parse_solomon_txt(txt_path)

    # Sous-échantillonner 1..N
    available = sorted(
        int(k.split('_')[1]) for k in full if k.startswith('customer_') and k != 'customer_0'
    )
    max_avail = available[-1] if available else 0
    if num_clients > max_avail:
        raise ValueError(f"num_clients={num_clients} > dispo={max_avail} dans {txt_path}")

    data = {"vehicle_capacity": full["vehicle_capacity"], "customer_0": full["customer_0"]}
    for cid in range(1, num_clients + 1):
        key = f"customer_{cid}"
        if key not in full:
            raise ValueError(f"{key} absent dans {txt_path}")
        data[key] = full[key]

    # Attributs
    # Logique héritée de l'ancien script:
    # - température: ambient 75%, frozen 15%, fresh 10%
    # - accès: none 85%, tail_lift 13%, crane 2%

    # Dépôt
    data["customer_0"]["attributes"] = {
        "temperature": "multi-temp",
        "access_requires": "all",
        "incompatible_with": []
    }

    # Clients
    for cid in range(1, num_clients + 1):
        key = f"customer_{cid}"
        if GENERER_INCOMPAT_ATTRS:
            # températures avec probabilités
            p = rng.random()
            if p < 0.75:
                temp = "ambient"
            elif p < 0.90:
                temp = "frozen"
            else:
                temp = "fresh"

            # accès avec probabilités
            q = rng.random()
            if q < 0.85:
                access = "none"
            elif q < 0.98:
                access = "tail_lift"
            else:
                access = "crane"
        else:
            temp = "multi-temp"
            access = "all"

        # initialiser sans incompatibilités explicites pour l'instant
        data[key]["attributes"] = {
            "temperature": temp,
            "access_requires": access,
            "incompatible_with": [],
        }

    # Incompatibilités explicites: paires rares et réciproques (~2%)
    if GENERER_LISTES_EXPLICITES:
        try:
            import config as _cfg
            pair_rate = getattr(_cfg, 'EXPLICIT_INCOMP_RATE', getattr(_cfg, 'EXPLICIT_INCOMP_PROBA', 0.02))
        except Exception:
            pair_rate = 0.02

        customer_keys = [f"customer_{i}" for i in range(1, num_clients + 1)]
        n = len(customer_keys)
        num_pairs = max(1, int(n * pair_rate)) if n >= 2 else 0
        available = customer_keys.copy()
        for _ in range(num_pairs):
            if len(available) < 2:
                break
            a_key, b_key = rng.sample(available, 2)
            a_id = int(a_key.split('_')[-1])
            b_id = int(b_key.split('_')[-1])
            data[a_key]["attributes"]["incompatible_with"].append(b_id)
            data[b_key]["attributes"]["incompatible_with"].append(a_id)
            available.remove(a_key)
            available.remove(b_key)

    # Écriture
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{base}.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"OK -> {out_path}")


if __name__ == '__main__':
    main()
