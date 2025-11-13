import json
import random
import os
import re
import hashlib

try:
    import config
    GENERER_INCOMPAT_ATTRS = getattr(config, "GENERER_INCOMPAT_ATTRS", True)
    GENERER_LISTES_EXPLICITES = getattr(config, "GENERER_LISTES_EXPLICITES", True)
    REUSE_SAME_RANDOM = getattr(config, "REUSE_SAME_RANDOM", False)
    EXPLICIT_INCOMP_PROBA = getattr(config, "EXPLICIT_INCOMP_PROBA", 0.05)
except Exception:
    GENERER_INCOMPAT_ATTRS = True
    GENERER_LISTES_EXPLICITES = True
    REUSE_SAME_RANDOM = False
    EXPLICIT_INCOMP_PROBA = 0.05


def _parse_solomon_txt(txt_path):
    """
    Parse un fichier Solomon .txt basique et retourne un dict:
    {
        "vehicle_capacity": Q,
        "customer_0": {...},
        "customer_1": {...},
        ...
    }
    """
    with open(txt_path, 'r', encoding='utf-8') as f:
        # on supprime les lignes vides et on strip
        lines = [ln.strip() for ln in f if ln.strip()]

    # Trouver la capacité: ligne après 'VEHICLE' + 2 (format Solomon)
    cap_idx = next(i for i, ln in enumerate(lines) if ln.upper().startswith('VEHICLE')) + 2
    parts = re.split(r'\s+', lines[cap_idx])
    capacity = float(parts[1])

    # Début des clients: ligne après 'CUSTOMER' + 2 (format Solomon)
    cust_idx = next(i for i, ln in enumerate(lines) if ln.upper().startswith('CUSTOMER')) + 2

    data = {"vehicle_capacity": capacity}
    for ln in lines[cust_idx:]:
        parts = re.split(r'\s+', ln)
        if len(parts) < 7:
            continue
        cid = int(parts[0])
        data[f"customer_{cid}"] = {
            "coordinates": {"x": float(parts[1]), "y": float(parts[2])},
            "demand": float(parts[3]),
            "ready_time": float(parts[4]),
            "due_time": float(parts[5]),
            "service_time": float(parts[6]),
        }

    if "customer_0" not in data:
        raise ValueError("customer_0 manquant dans le .txt (dépôt).")
    return data


def generate_instance_json(filepath, num_clients, seed=None):
    """
    Génère un JSON d'instance à partir du .txt Solomon correspondant, en conservant:
      - le dépôt (customer_0)
      - les clients 1..num_clients
    et en ajoutant UNIQUEMENT les attributs utilisés pour les incompatibilités.

    - filepath: chemin du JSON de sortie (ex: .../data/json/C101.json)
    - num_clients: nombre de clients à conserver (IDs 1..N)
    - seed: optionnel, pour reproductibilité quand REUSE_SAME_RANDOM == False

    Flags (via config ou défauts):
      - GENERER_INCOMPAT_ATTRS: bool (temperature/access aléatoires vs valeurs neutres)
      - GENERER_LISTES_EXPLICITES: bool (liste 'incompatible_with' aléatoire)
      - REUSE_SAME_RANDOM: bool (seed stable basé sur contenu .txt + num_clients)
      - EXPLICIT_INCOMP_PROBA: float (proba d'ajouter une incompat explicite avec un client précédent)
    """
    if not isinstance(num_clients, int) or num_clients <= 0:
        raise ValueError("num_clients doit être un entier strictement positif")

    # Déduire le .txt source: .../data/json/C101.json -> essayer .../data/C101.txt puis .../data/text/C101.txt
    json_dir = os.path.dirname(filepath)                 # .../data/json
    data_dir = os.path.dirname(json_dir)                 # .../data
    base = os.path.splitext(os.path.basename(filepath))[0]

    txt_path = os.path.join(data_dir, f"{base}.txt")
    if not os.path.exists(txt_path):
        txt_alt = os.path.join(data_dir, "text", f"{base}.txt")
        if os.path.exists(txt_alt):
            txt_path = txt_alt
        else:
            raise FileNotFoundError(f"Solomon .txt introuvable: {txt_path} ni {txt_alt}")

    # ------------- Choix du RNG (corrigé) -------------
    # On évite d'utiliser le générateur global 'random' pour ne pas hériter
    # d'un éventuel random.seed(...) posé ailleurs dans le processus.
    used_seed = None
    if REUSE_SAME_RANDOM:
        # Seed 100% stable = hash(contenu .txt, num_clients)
        h = hashlib.sha256()
        try:
            with open(txt_path, "rb") as f:
                h.update(f.read())
        except Exception:
            h.update(base.encode("utf-8"))
        h.update(str(num_clients).encode("utf-8"))
        used_seed = int.from_bytes(h.digest()[:8], "big")
        rng = random.Random(used_seed)
    elif seed is not None:
        used_seed = int(seed)
        rng = random.Random(used_seed)
    else:
        # Non déterministe et indépendant du générateur global
        rng = random.Random()
        used_seed = None

    print(f"[generate_instance] REUSE_SAME_RANDOM={REUSE_SAME_RANDOM} | seed_utilisé={used_seed}")

    # 1) Parser l’instance complète depuis le .txt
    full_data = _parse_solomon_txt(txt_path)

    # 2) Sous-échantillonner: dépôt + clients 1..num_clients
    available_ids = sorted(
        int(k.split('_')[1]) for k in full_data.keys()
        if k.startswith('customer_') and k != "customer_0"
    )
    max_available = available_ids[-1] if available_ids else 0
    if num_clients > max_available:
        raise ValueError(f"num_clients={num_clients} > disponible={max_available} dans {txt_path}")

    data = {"vehicle_capacity": full_data["vehicle_capacity"]}
    data["customer_0"] = full_data["customer_0"]

    for cid in range(1, num_clients + 1):
        key = f"customer_{cid}"
        if key not in full_data:
            raise ValueError(f"{key} absent dans {txt_path}")
        data[key] = full_data[key]

    # 3) Ajouter/écraser uniquement les attributes, contrôlés par flags
    temperatures = ["ambient", "frozen", "multi-temp"]
    access_options = ["none", "tail_lift", "all"]

    # Dépôt: attributs fixes (compatibles avec tout)
    data["customer_0"]["attributes"] = {
        "temperature": "multi-temp",
        "access_requires": "all",
        "incompatible_with": []
    }

    # Clients: selon flags
    for cid in range(1, num_clients + 1):
        key = f"customer_{cid}"
        node = data[key]

        if GENERER_INCOMPAT_ATTRS:
            temp = rng.choice(temperatures)
            access = rng.choice(access_options)
        else:
            temp = "multi-temp"
            access = "all"

        if GENERER_LISTES_EXPLICITES:
            incomp = []
            for prev in range(1, cid):
                if rng.random() < EXPLICIT_INCOMP_PROBA:
                    incomp.append(prev)
        else:
            incomp = []

        node["attributes"] = {
            "temperature": temp,
            "access_requires": access,
            "incompatible_with": incomp
        }

    # 4) Écrire le JSON final
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return filepath
