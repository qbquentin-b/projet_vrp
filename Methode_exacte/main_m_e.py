import pulp
import math

# --- 1. Données de l'Instance (Test-Case-5) ---
nodes = {
    0: {'X': 50, 'Y': 50, 'q': 0, 'e': 0, 'l': 1000, 's': 0},  # Dépôt
    1: {'X': 40, 'Y': 40, 'q': 10, 'e': 100, 'l': 200, 's': 10},
    2: {'X': 60, 'Y': 60, 'q': 20, 'e': 0, 'l': 150, 's': 15},
    3: {'X': 40, 'Y': 60, 'q': 15, 'e': 300, 'l': 400, 's': 10},
    4: {'X': 60, 'Y': 40, 'q': 20, 'e': 100, 'l': 180, 's': 10},
    5: {'X': 70, 'Y': 50, 'q': 10, 'e': 50, 'l': 100, 's': 20}
}

num_nodes = len(nodes)
num_vehicles = 2
vehicle_capacity = 50

# Ensembles
N = list(nodes.keys())  # Tous les nœuds [0, 1, 2, 3, 4, 5]
C = N[1:]               # Clients [1, 2, 3, 4, 5]
K = list(range(num_vehicles)) # Véhicules [0, 1]

# Incompatibilités (basé sur ton document)
incompatibles = [(2, 4)]

# --- 2. Paramètres du Modèle ---
alpha = 100  # Coût fixe d'utilisation d'un véhicule
beta = 2     # Pénalité par minute de "retard" après e_i (début fenêtre)
M = 10000    # "Big M"

# --- 3. Pré-calculs (Distances et Temps de trajet) ---
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

# --- 4. Initialisation du Modèle ---
model = pulp.LpProblem("VRPTW-C_Exact_Optimal_v2", pulp.LpMinimize)

# --- 5. Variables de Décision ---
# x_ij_k = 1 si le véhicule k va de i à j
x = pulp.LpVariable.dicts("x", (N, N, K), cat=pulp.LpBinary)

# u_k = 1 si le véhicule k est utilisé
u = pulp.LpVariable.dicts("u", K, cat=pulp.LpBinary)

# t_i = Heure de début de service au nœud i
# ! CHANGEMENT DE LOGIQUE !
# t_i est MAINTENANT borné par e_i (low) ET l_i (up).
# La livraison APRES l_i est DÉSORMAIS IMPOSSIBLE (Contrainte Dure).
t = {i: pulp.LpVariable(f"t_{i}", lowBound=nodes[i]['e'], upBound=nodes[i]['l']) for i in C}
t[0] = pulp.LpVariable("t_0", lowBound=0, upBound=0) # Dépôt commence à 0


# ! VARIABLE L (Lateness vs l_i) SUPPRIMÉE !

# --- 6. Fonction Objectif ---
# (1) distance totale parcourue
distance_cost = pulp.lpSum(d[i][j] * x[i][j][k] for i in N for j in N for k in K if i != j)

# (2) coût fixe d'utilisation des véhicules
vehicle_cost = pulp.lpSum(alpha * u[k] for k in K)

# (3) pénalités pour "retards" (service après e_i)
# ! CHANGEMENT DE LOGIQUE !
# On pénalise la différence entre l'heure de service (t_i) et
# le début de la fenêtre (e_i), comme tu l'as cité.
tardiness_cost_e = pulp.lpSum(beta * (t[i] - nodes[i]['e']) for i in C)

model += distance_cost + vehicle_cost + tardiness_cost_e, "Cout_Total"


# --- 7. Contraintes du Modèle ---

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
# Contrainte de retour au dépôt (avant fermeture dépôt)
for k in K:
    for i in C:
        model += t[i] + nodes[i]['s'] + tau[i][0] \
                 <= nodes[0]['l'] + M * (1 - x[i][0][k])

# Contrainte de succession des services (vers clients)
for k in K:
    for i in N:
        for j in C:
            if i != j:
                model += t[j] >= t[i] + nodes[i]['s'] + tau[i][j] - M * (1 - x[i][j][k])

# ! CONTRAINTE L_i (Lateness vs l_i) SUPPRIMÉE !
# Le respect de l_i est déjà géré dans la définition de la variable t.

# (Contrainte 6.5: Incompatibilités)
for k in K:
    for (i, j) in incompatibles:
        y_ik = pulp.lpSum(x[i][m][k] for m in N if i != m)
        y_jk = pulp.lpSum(x[j][m][k] for m in N if j != m)
        model += y_ik + y_jk <= 1

# --- 8. Résolution du Problème ---
print("======================================================")
print(f"Résolution du modèle exact (MIP) pour {len(C)} clients...")
print("(Logique: Pénalité 'beta' sur service après e_i)")
print("======================================================")

model.solve()

# --- 9. Affichage de la Solution ---
status = pulp.LpStatus[model.status]
print(f"Statut de la solution : {status}")

if status == 'Optimal':
    Z_optimal = pulp.value(model.objective)
    print(f"\nCoût total optimal (Z*) : {Z_optimal:.4f}")
    
    print("\n--- Tournées optimales ---")
    
    total_dist = 0
    total_tardiness_cost_e = 0
    
    for k in K:
        if pulp.value(u[k]) > 0.5:
            print(f"\nVéhicule {k} (utilisé, coût fixe: {alpha}):")
            
            route = [0]
            current_node = 0
            
            while True:
                next_node = -1
                for j in N:
                    if current_node != j and pulp.value(x[current_node][j][k]) > 0.5:
                        next_node = j
                        break
                
                if next_node == -1 or next_node == 0:
                    route.append(0)
                    break
                
                route.append(next_node)
                current_node = next_node
                
                if len(route) > num_nodes + 2:
                    break

            print(f"  Route : {' -> '.join(map(str, route))}")
            
            route_dist = 0
            route_demand = 0
            
            print("  Horaires (Début service) :")
            for node_id in route:
                if node_id != 0: route_demand += nodes[node_id]['q']
                
                t_arrival = pulp.value(t[node_id])
                
                # Calcul de la pénalité pour ce nœud
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
    print(f" (2) Coût véhicules (alpha) : {pulp.value(vehicle_cost):.4f}")
    print(f" (3) Coût pénalité (t-e_i) : {total_tardiness_cost_e:.4f}")
    print(" -----------------------------")
    print(f" Coût total Z* : {Z_optimal:.4f}")
    
elif status == 'Infeasible':
    print("Le problème est 'Infeasible' (infaisable).")
    print("Avec cette nouvelle logique, il est possible que les fenêtres temporelles")
    print("soient trop strictes (ex: impossible de servir t_i <= l_i).")
else:
    print(f"La solution optimale n'a pas été trouvée. Statut : {status}")