# Fichier: main.py

import os
import time
from problem import ProblemInstance
from mga import MemeticAlgorithm
from individual import Individual
from collections import Counter
import config

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
    
    # 1. Charger le problème
    print("--- 1. Chargement du Problème ---")
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

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_solver()
    

    