# Fichier: main.py

import os
import time
import sys
# Ensure project root is on sys.path so local imports work when running this file directly
proj_root = os.path.abspath(os.path.dirname(__file__))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from problem import ProblemInstance
from mga import MemeticAlgorithm
from individual import Individual
from collections import Counter
import config
import csv
import datetime
# import generate_instance

# ---------------------------------------------------------------------------
# FONCTION DE VÉRIFICATION
# ---------------------------------------------------------------------------

def verify_solution_completeness(problem: ProblemInstance, individual: Individual):
    """
    Vérifie que la solution finale ne contient ni doublons,
    ni clients manquants.
   
    """
    print("\n--- 5. Lancement de la Vérification Post-Optimisation ---")
    is_valid = True
    
    expected_clients = set(problem.clients.keys())
    
    served_clients_list = []
    for node_id in individual.representation:
        if node_id != 0: 
            served_clients_list.append(node_id)
            
    client_counts = Counter(served_clients_list)
    duplicates = [client for client, count in client_counts.items() if count > 1]
    
    if duplicates:
        print(f"❌ ERREUR: Doublons de clients trouvés !")
        print(f"   Clients servis plus d'une fois: {duplicates}")
        is_valid = False
    else:
        print("✅ OK: Aucun doublon de client.")

    served_clients_set = set(served_clients_list)
    missing_clients = expected_clients - served_clients_set
    
    if missing_clients:
        print(f"❌ ERREUR: Clients manquants !")
        print(f"   Clients de l'instance non servis: {missing_clients}")
        is_valid = False
    else:
        print("✅ OK: Aucun client manquant.")
        
    phantom_clients = served_clients_set - expected_clients
    if phantom_clients:
        print(f"❌ ERREUR: Clients 'fantômes' trouvés !")
        is_valid = False

    if is_valid:
        print("🏆 VÉRIFICATION RÉUSSIE: La solution est complète et correcte.")
    else:
        print("🔥 VÉRIFICATION ÉCHOUÉE: La solution est boguée.")
        
    print("------------------------------------------------------")
    return is_valid

# ---------------------------------------------------------------------------
# FONCTION PRINCIPALE (RUN SOLVER)
# ---------------------------------------------------------------------------

def run_solver():
    """Point d'entrée principal du solveur."""
    start_time = time.time()
    
    # 1. Charger / (éventuellement) générer le fichier d'instance JSON
    # print("--- 1. Chargement du Problème ---")
    # if isinstance(config.NUM_CLIENTS, int):
    #     print(f"Génération automatique de l'instance JSON ({config.NUM_CLIENTS} clients) -> {config.FICHIER_INSTANCE}")
    #     generate_instance.generate_instance_json(config.FICHIER_INSTANCE, config.NUM_CLIENTS)
    
    # Exiger un JSON déjà présent (pas de génération automatique ici)

    # Exiger un JSON déjà présent (pas de génération automatique ici)
    if not os.path.exists(config.FICHIER_INSTANCE):
        instance_base = os.path.splitext(os.path.basename(config.INSTANCE_NAME))[0]
        print(f"ERREUR: JSON introuvable: {config.FICHIER_INSTANCE}")
        print("Crée le JSON une seule fois avec txt_to_json.py, par ex.:")
        print(f"  python txt_to_json.py {instance_base} --num-clients 100")
        sys.exit(1)



    # (Appel sans gamma)
    problem = ProblemInstance(filepath=config.FICHIER_INSTANCE, 
                              alpha=config.COUT_FIXE_VEHICULE, 
                              beta=config.PENALITE_RETARD)
    
    print(f"Problème chargé: {config.INSTANCE_NAME} ({len(problem.clients)} clients)")
    print(f"Paramètres: Alpha={problem.alpha}, Beta={problem.beta}\n")

    # 2. Initialiser l'algorithme
    print("--- 2. Initialisation du MGA ---")
    mga = MemeticAlgorithm(problem=problem,
                           pop_size=config.POP_SIZE,
                           generations=config.GENERATIONS,
                           crossover_rate=config.CROSSOVER_RATE,
                           mutation_rate=config.MUTATION_RATE,
                           elite_size=config.ELITE_SIZE)
    
    # 3. Lancer l'optimisation
    print("--- 3. Lancement de l'optimisation ---")
    best_solution = mga.run()

    # 4. Étape de Vérification
    verify_solution_completeness(problem, best_solution)
    
    # 5. Afficher les résultats
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("\n--- 6. Meilleure Solution Trouvée (Détails) ---")
    print(f"Représentation: {best_solution.representation}")
    print(f"Fitness (Coût Z): {best_solution.fitness:.2f}")
    print(f"Nombre de véhicules: {best_solution.num_vehicles}")
    print(f"Distance Totale: {best_solution.total_distance:.2f}")
    
    # Détails des pénalités (gamma est supprimé)
    cost_alpha = problem.alpha * best_solution.num_vehicles
    cost_beta = problem.beta * best_solution.total_delay_penalty
    
    print("\n--- Décomposition du Coût ---")
    print(f"Coût Véhicules (Alpha): {cost_alpha:.2f} ({best_solution.num_vehicles} x {problem.alpha})")
    print(f"Pénalité Retard (Beta): {cost_beta:.2f} ({best_solution.total_delay_penalty:.2f} x {problem.beta})")
        
    print(f"\nTemps total d'exécution: {elapsed_time:.2f} secondes.")

    # --- EXPORT CSV DES RÉSULTATS (MGA) ---
    try:
        # Préparer dossier résultats
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        RESULTS_DIR = os.path.join(BASE_DIR, 'results_mga')
        os.makedirs(RESULTS_DIR, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        instance_base = os.path.splitext(os.path.basename(config.INSTANCE_NAME))[0]
        csv_filename = f"Results_{instance_base}_{timestamp}.csv"
        csv_path = os.path.join(RESULTS_DIR, csv_filename)

        # Récupérer valeurs
        nb_clients = len(problem.clients)
        vehicles_used = getattr(best_solution, 'num_vehicles', '')
        vehicle_capacity = getattr(problem, 'vehicle_capacity', '')
        Z_val = getattr(best_solution, 'fitness', '')
        total_dist = getattr(best_solution, 'total_distance', '')
        vehicle_cost = problem.alpha * vehicles_used if vehicles_used != '' else ''
        penalty_cost = problem.beta * getattr(best_solution, 'total_delay_penalty', 0)

        # Détails par véhicule (reconstruire routes depuis la représentation)
        routes = []
        if best_solution and getattr(best_solution, 'representation', None):
            rep = best_solution.representation
            cur = []
            for nid in rep[1:]:
                if nid == 0:
                    if cur:
                        routes.append(cur)
                        cur = []
                else:
                    cur.append(nid)

        with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Instance", "Nb_Clients", "Nb_Vehicules_alloc", "Vehicules_utilisés",
                "Capacité", "Coût_total_Z*", "Coût_distance", "Coût_véhicules",
                "Coût_pénalité", "Alpha", "Beta", "Statut"
            ])
            writer.writerow([
                instance_base, nb_clients, config.POP_SIZE, vehicles_used,
                vehicle_capacity, round(Z_val, 4) if isinstance(Z_val, (int, float)) else Z_val,
                round(total_dist, 4) if isinstance(total_dist, (int, float)) else total_dist,
                round(vehicle_cost, 4) if isinstance(vehicle_cost, (int, float)) else vehicle_cost,
                round(penalty_cost, 4) if isinstance(penalty_cost, (int, float)) else penalty_cost,
                config.COUT_FIXE_VEHICULE, config.PENALITE_RETARD, 'Heuristic'
            ])

            writer.writerow([])
            writer.writerow(["Véhicule", "Route", "Distance", "Demande"])
            # Calculer distance et demande par route
            for k_idx, route in enumerate(routes):
                route_dist = 0
                route_demand = 0
                last = 0
                for node in route:
                    route_demand += problem.get_node(node)['demand']
                    route_dist += problem.get_distance(last, node)
                    last = node
                route_dist += problem.get_distance(last, 0)
                writer.writerow([k_idx, ' -> '.join(map(str, [0] + route + [0])), round(route_dist, 4), round(route_demand, 4)])

        print(f"\nRésultats exportés vers : {csv_path}")
    except Exception as e:
        print(f"Erreur lors de l'export CSV: {e}")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_solver()
    

    