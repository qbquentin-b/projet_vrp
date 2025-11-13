# Fichier: enrichir_instance.py (Version Traitement par Lot)

import json
import random
import argparse
import os
import glob 

def _parse_solomon_txt(filepath):
    """
    Lit un fichier d'instance Solomon .txt et le convertit
    en une structure de dictionnaire de base.
   
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"ERREUR: Fichier d'instance non trouvé à {filepath}")
        raise

    data = {}
    section = None
    
    for line in lines:
        line = line.strip()
        if not line: continue

        if line.startswith("VEHICLE"):
            section = "VEHICLE"; continue
        elif line.startswith("CUSTOMER"):
            section = "CUSTOMER"; continue
        elif line.startswith("NUMBER"): continue
        elif line.startswith("CUST NO."): continue

        parts = line.split()
        if not parts: continue

        if section == "VEHICLE":
            data["vehicle_capacity"] = float(parts[1])
            section = None
        
        elif section == "CUSTOMER":
            client_id = int(parts[0])
            key = f"customer_{client_id}"
            
            data[key] = {
                "coordinates": {
                    "x": float(parts[1]),
                    "y": float(parts[2])
                },
                "demand": float(parts[3]),
                "ready_time": float(parts[4]),
                "due_time": float(parts[5]),
                "service_time": float(parts[6])
            }
            
    return data

def _generate_attributes():
    """
    Génère un ensemble "logique et équilibré" d'attributs
    pour un seul client.
   
    """
    
    # 1. Logique de Température
    p_temp = random.random()
    if p_temp < 0.75:  # 75%
        temperature = "ambient"
    elif p_temp < 0.90: # 15%
        temperature = "frozen"
    else: # 10%
        temperature = "fresh"
        
    # 2. Logique d'Accès
    p_access = random.random()
    if p_access < 0.85: # 85%
        access = "none"
    elif p_access < 0.98: # 13%
        access = "tail_lift"
    else: # 2%
        access = "crane"
        
    return {
        "temperature": temperature,
        "access_requires": access,
        "incompatible_with": [] 
    }

def _add_rare_incompatibilities(data):
    """
    Ajoute des incompatibilités "concurrent" rares et réciproques.
   
    """
    
    customer_keys = [k for k in data.keys() if k.startswith("customer_") and k != "customer_0"]
    num_clients = len(customer_keys)
    
    # RARE: Créer des paires pour environ 2% des clients
    num_pairs = max(1, int(num_clients * 0.02))
    
    available_clients = customer_keys.copy()
    
    for _ in range(num_pairs):
        if len(available_clients) < 2:
            break 
            
        key_a, key_b = random.sample(available_clients, 2)
        id_a = int(key_a.split('_')[-1])
        id_b = int(key_b.split('_')[-1])
        
        data[key_a]["attributes"]["incompatible_with"].append(id_b)
        data[key_b]["attributes"]["incompatible_with"].append(id_a)
        
        available_clients.remove(key_a)
        available_clients.remove(key_b)
        
    return data

def main(input_dir, output_dir):
    """
    Fonction principale pour lire, enrichir et écrire les fichiers
    en mode "batch" (traitement par lot).
    """
    print(f"--- 1. Scan du répertoire d'entrée ---")
    print(f"Répertoire source: {input_dir}")
    print(f"Répertoire cible:  {output_dir}")
    
    # Utiliser glob pour trouver tous les fichiers .txt dans le répertoire
    # (os.path.join assure que le chemin est correct)
    search_path = os.path.join(input_dir, "*.txt")
    txt_files = glob.glob(search_path)
    
    if not txt_files:
        print(f"Avertissement: Aucun fichier .txt trouvé dans {input_dir}")
        return

    print(f"Trouvé {len(txt_files)} fichier(s) .txt à traiter.")

    # Assurer que le répertoire de sortie existe
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n--- 2. Lancement du traitement par lot ---")
    
    success_count = 0
    fail_count = 0

    for input_filepath in txt_files:
        # Extraire le nom de base (ex: "C101.txt")
        txt_filename = os.path.basename(input_filepath)
        
        # Créer le nom de sortie (ex: "C101.json")
        json_filename = os.path.splitext(txt_filename)[0] + ".json" 
        output_filepath = os.path.join(output_dir, json_filename)
        
        print(f"\nTraitement de '{txt_filename}'...")

        try:
            # --- Logique de traitement (identique à avant) ---
            base_data = _parse_solomon_txt(input_filepath)
            
            # Enrichir
            for key, customer_data in base_data.items():
                if key == "customer_0":
                    customer_data["attributes"] = {
                        "temperature": "multi-temp",
                        "access_requires": "all",
                        "incompatible_with": []
                    }
                elif key.startswith("customer_"):
                    customer_data["attributes"] = _generate_attributes()
                    
            enriched_data = _add_rare_incompatibilities(base_data)
            
            # Écrire
            with open(output_filepath, 'w') as f:
                json.dump(enriched_data, f, indent=4)
                
            print(f"  > Succès ! Fichier sauvegardé sous : {output_filepath}")
            success_count += 1
        
        except Exception as e:
            print(f"  > ERREUR lors du traitement de {txt_filename}: {e}")
            fail_count += 1
            
    print("\n--- Traitement par lot terminé. ---")
    print(f"Succès: {success_count} fichier(s)")
    print(f"Échecs: {fail_count} fichier(s)")

if __name__ == "__main__":
    # Configuration pour l'exécuter depuis la ligne de commande
    parser = argparse.ArgumentParser(
        description="Convertit un RÉPERTOIRE d'instances Solomon .txt en .json enrichis."
    )
    # MODIFIÉ: On demande des répertoires, plus des fichiers
    parser.add_argument(
        "-i", "--input_dir", 
        required=True,
        help="Chemin vers le répertoire contenant les instances .txt (ex: data/solomon_txt)"
    )
    parser.add_argument(
        "-o", "--output_dir", 
        required=True,
        help="Chemin vers le répertoire de sortie pour les fichiers .json (ex: data/json_instances)"
    )
    
    args = parser.parse_args()
    main(args.input_dir, args.output_dir)