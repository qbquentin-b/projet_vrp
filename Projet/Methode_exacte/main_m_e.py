import pulp
import math
import json
from collections import defaultdict
import itertools

# --- 0. Paramètres à configurer ---

JSON_FILE_PATH = 'data/C101.json' 

# Paramètres de coût (inchangés)
alpha = 100  # Coût fixe d'utilisation d'un véhicule
beta = 2     # Pénalité par minute de "retard" après e_i (début fenêtre)
M = 10000    # "Big M"

# --- 1. Fonction de chargement des données (Logique 'problem.py') ---

def load_data_from_json(filepath):
    """
    Charge les données JSON.
    Génère les incompatibilités basées sur les règles métier
    (explicite, température, et accès).
    """
    print(f"--- Chargement des données depuis : {filepath} ---")
    nodes = {}
    incompatibles_set = set()
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERREUR: Fichier non trouvé à l'emplacement : {filepath}")
        return None, None, None
    except json.JSONDecodeError:
        print(f"ERREUR: Le fichier JSON est mal formaté : {filepath}")
        return None, None, None

    if 'vehicle_capacity' not in data:
        print("ERREUR: 'vehicle_capacity' non trouvé dans le JSON.")
        return None, None, None
        
    vehicle_capacity = data['vehicle_capacity']
    
    client_nodes = {} # Dictionnaire temporaire pour les clients
    
    for key, customer_data in data.items():
        if not key.startswith('customer_'):
            continue
            
        try:
            node_id = int(key.split('_')[1])
        except Exception:
            print(f"ATTENTION: Clé JSON '{key}' ignorée (format non reconnu).")
            continue

        attributes = customer_data.get('attributes', {})
        temp = attributes.get('temperature', 'none')
        access = attributes.get('access_requires', 'none')

        nodes[node_id] = {
            'X': customer_data['coordinates']['x'],
            'Y': customer_data['coordinates']['y'],
            'q': customer_data['demand'],
            'e': customer_data['ready_time'],
            'l': customer_data['due_time'],
            's': customer_data['service_time'],
            'temp': temp,
            'access': access
        }
        
        # Ne traiter que les clients pour les incompatibilités
        if node_id != 0:
            client_nodes[node_id] = nodes[node_id]
        
            # 1. Gérer les incompatibilités EXPLICITES
            if 'incompatible_with' in attributes:
                for incomp_node in attributes['incompatible_with']:
                    pair = tuple(sorted((node_id, incomp_node)))
                    incompatibles_set.add(pair)
                
    if 0 not in nodes:
        print("ERREUR: Le dépôt (customer_0) est manquant dans le JSON.")
        return None, None, None
    
    # 2. Gérer les incompatibilités IMPLICITES (Temp & Accès)
    # On itère sur toutes les paires uniques de clients
    print("Génération des incompatibilités implicites (Temp & Accès)...")
    for i, j in itertools.combinations(client_nodes.keys(), 2):
        client_i = client_nodes[i]
        client_j = client_nodes[j]
        
        # Règle de Température: 'ambient' est incompatible with 'frozen'
        temp_i = client_i['temp']
        temp_j = client_j['temp']
        if (temp_i == 'ambient' and temp_j == 'frozen') or \
           (temp_i == 'frozen' and temp_j == 'ambient'):
            incompatibles_set.add(tuple(sorted((i, j))))
            continue # Une incompatibilité suffit
            
        # Règle d'Accès: Incompatible si les deux sont spécifiques ET différents
        access_i = client_i['access']
        access_j = client_j['access']
        if (access_i != 'none' and access_j != 'none' and access_i != access_j):
            incompatibles_set.add(tuple(sorted((i, j))))

    print(f"Données chargées : {len(client_nodes)} clients, 1 dépôt.")
    print(f"Capacité véhicule (globale) : {vehicle_capacity}")
    print(f"Incompatibilités (totales) : {list(incompatibles_set)}")
    
    return nodes, vehicle_capacity, list(incompatibles_set)

# --- 2. Chargement et Pré-calculs ---
nodes, vehicle_capacity, incompatibles = load_data_from_json(JSON_FILE_PATH)

if nodes is None:
    print("Échec du chargement des données. Arrêt du script.")
    exit()

# Ensembles (générés dynamiquement)
N = sorted(list(nodes.keys()))  # Tous les nœuds
C = N[1:]                       # Clients

# --- NOUVELLE LOGIQUE DE FLOTTE ---
# Flotte homogène. On crée autant de véhicules que de clients.
# Le modèle minimisera 'alpha * u_k' pour trouver le nombre réel nécessaire.
num_vehicles = len(C)
K = list(range(num_vehicles)) # K est [0, 1, 2, 3]

print(f"Flotte homogène disponible : {num_vehicles} véhicules standards.")

# Pré-calculs des distances (inchangé)
d = {}
tau = {}
def calculate_distance(n1, n2):
    return math.sqrt((n1['X'] - n2['X'])**2 + (n1['Y'] - n2['Y'])**2)
for i in N:
    d[i] = {}
    tau[i] = {}
    for j in N:
        dist = calculate_distance(nodes[i], nodes[j])
        d[i][j] = dist
        tau[i][j] = dist

# --- 3. Initialisation du Modèle (inchangé) ---
model = pulp.LpProblem("VRPTW-C_Exact_Homogeneous", pulp.LpMinimize)

# --- 4. Variables de Décision (inchangé) ---
x = pulp.LpVariable.dicts("x", (N, N, K), cat=pulp.LpBinary)
u = pulp.LpVariable.dicts("u", K, cat=pulp.LpBinary)
t = {i: pulp.LpVariable(f"t_{i}", lowBound=nodes[i]['e'], upBound=nodes[i]['l']) for i in C}
t[0] = pulp.LpVariable("t_0", lowBound=0, upBound=0)

# --- 5. Fonction Objectif (inchangé) ---
distance_cost = pulp.lpSum(d[i][j] * x[i][j][k] for i in N for j in N for k in K if i != j)
vehicle_cost = pulp.lpSum(alpha * u[k] for k in K)
tardiness_cost_e = pulp.lpSum(beta * (t[i] - nodes[i]['e']) for i in C)
model += distance_cost + vehicle_cost + tardiness_cost_e, "Cout_Total"

# --- 6. Contraintes du Modèle ---

# (Contrainte 6.0: Interdire les boucles sur soi-même)
for i in N:
    for k in K:
        model += x[i][i][k] == 0

# (Contrainte 6.1: Visite unique)
for i in C:
    model += pulp.lpSum(x[i][j][k] for j in N for k in K if i != j) == 1

# (Contrainte 6.2: Flux et Tournées)
for k in K:
    model += pulp.lpSum(x[0][j][k] for j in C) == u[k]
    model += pulp.lpSum(x[i][0][k] for i in C) == u[k]
    for j in C:
        model += pulp.lpSum(x[i][j][k] for i in N if i != j) == \
                 pulp.lpSum(x[j][i][k] for i in N if i != j)

# (Contrainte 6.3: Capacité)
for k in K:
    model += pulp.lpSum(nodes[i]['q'] * pulp.lpSum(x[i][j][k] for j in N if i != j) for i in C) \
             <= vehicle_capacity * u[k]

# (Contrainte 6.4: Fenêtres temporelles)
for k in K:
    for i in C:
        model += t[i] + nodes[i]['s'] + tau[i][0] \
                 <= nodes[0]['l'] + M * (1 - x[i][0][k])
for k in K:
    for i in N:
        for j in C:
            if i != j:
                model += t[j] >= t[i] + nodes[i]['s'] + tau[i][j] - M * (1 - x[i][j][k])

# (Contrainte 6.5: Incompatibilités (Toutes règles métier))
# Cette contrainte est maintenant alimentée par la liste 'incompatibles'
# qui contient les règles explicites, de température, et d'accès.
for k in K:
    for (i, j) in incompatibles:
        if i not in C or j not in C: 
            continue 
        y_ik = pulp.lpSum(x[i][m][k] for m in N if i != m)
        y_jk = pulp.lpSum(x[j][m][k] for m in N if j != m)
        model += y_ik + y_jk <= 1

# (Contrainte 6.6: SUPPRIMÉE)
# La logique de compatibilité est gérée par 6.5


# --- 7. Résolution du Problème ---
print("======================================================")
print(f"Résolution du modèle exact (MIP) pour {len(C)} clients...")
print("(Logique: Compatibilité Client-Client 'problem.py')")
print("======================================================")

model.solve()

# --- 8. Affichage de la Solution ---
status = pulp.LpStatus[model.status]
print(f"Statut de la solution : {status}")

if status == 'Optimal':
    Z_optimal = pulp.value(model.objective)
    print(f"\nCoût total optimal (Z*) : {Z_optimal:.4f}")
    
    print("\n--- Tournées optimales ---")
    
    total_dist = 0
    total_tardiness_cost_e = 0
    vehicles_used = 0
    
    for k in K:
        if pulp.value(u[k]) > 0.5:
            vehicles_used += 1
            print(f"\nVéhicule {k} (utilisé, coût fixe: {alpha}) [Type: Standard]")
            
            route = [0]
            current_node = 0
            
            while True:
                next_node = -1
                for j in N:
                    if pulp.value(x[current_node][j][k]) > 0.5:
                        next_node = j
                        break
                
                if next_node == -1 or next_node == 0:
                    route.append(0)
                    break
                
                route.append(next_node)
                current_node = next_node
                
                if len(route) > len(N) + 2:
                    print("ERREUR: Boucle infinie détectée dans l'affichage.")
                    break

            print(f"  Route : {' -> '.join(map(str, route))}")
            
            route_dist = 0
            route_demand = 0
            
            print("  Horaires (Début service) :")
            for node_id in route:
                if node_id != 0: route_demand += nodes[node_id]['q']
                
                t_arrival = pulp.value(t.get(node_id, 0))
                
                penalty_e = 0
                if node_id != 0:
                    node_penalty = beta * (t_arrival - nodes[node_id]['e'])
                    if node_penalty > 1e-5:
                        penalty_e = node_penalty
                        total_tardiness_cost_e += node_penalty
                
                print(f"    -> Nœud {node_id}: Fenêtre [{nodes[node_id]['e']}, {nodes[node_id]['l']}] | "
                      f"Début service à t={t_arrival:.2f} | "
                      f"Pénalité (t-e_i): {penalty_e:.2f}")

            for idx in range(len(route) - 1):
                i = route[idx]
                j = route[idx+1]
                route_dist += d[i][j]
                
            total_dist += route_dist
            print(f"  Distance: {route_dist:.2f} | Demande: {route_demand}/{vehicle_capacity}")

    print("\n--- Récapitulatif des Coûts ---")
    print(f" (1) Coût de distance : {total_dist:.4f}")
    print(f" (2) Coût véhicules (alpha) : {pulp.value(vehicle_cost):.4f} ({vehicles_used} véhicules)")
    print(f" (3) Coût pénalité (t-e_i) : {total_tardiness_cost_e:.4f}")
    print(" -----------------------------")
    print(f" Coût total Z* : {Z_optimal:.4f}")
    
elif status == 'Infeasible':
    print("Le problème est 'Infeasible' (infaisable).")
    print("Vérifiez les contraintes (fenêtres temporelles, capacité)")
    print("ou une contradiction dans les incompatibilités (ex: client A-B, B-C, C-A).")
else:
    print(f"La solution optimale n'a pas été trouvée. Statut : {status}")