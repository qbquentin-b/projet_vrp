# Fichier: check_solution.py (MIS À JOUR)

import os
from problem import ProblemInstance
from individual import Individual
# Importer les paramètres depuis le fichier config
import config

# --- 1. La Solution à Vérifier ---
solution_representation = [...] # Mettez votre solution ici

# --- 2. Paramètres (MAINTENANT IMPORTÉS) ---
# Les paramètres sont lus depuis config.py
FICHIER_INSTANCE = config.FICHIER_INSTANCE
COUT_FIXE_VEHICULE = config.COUT_FIXE_VEHICULE
PENALITE_RETARD = config.PENALITE_RETARD

# --- 2. Initialisation du problème ---
print("--- Chargement du Problème ---")
try:
    # On crée une instance du problème en lui donnant les paramètres de coût
    problem = ProblemInstance(FICHIER_INSTANCE, 
                              alpha=COUT_FIXE_VEHICULE, 
                              beta=PENALITE_RETARD)
    
    print(f"Instance chargée. Capacité véhicule: {problem.vehicle_capacity}")
    print(f"Clients à servir: {list(problem.clients.keys())}")
    print(f"Incompatibilités connues: {problem.incompatibilities}")
    print("--------------------------------\n")

except FileNotFoundError:
    print(f"ERREUR: Le fichier d'instance '{FICHIER_INSTANCE}' n'a pas été trouvé.")
    exit()


# --- 3. Création d'une solution de test (Individu) ---

# Rappel: la représentation est [0, client, client, ..., 0, client, ..., 0]
# Nous utilisons les clients 1, 2, 3 définis dans problem.py
# Tournée 1: Dépôt -> Client 1 -> Client 3 -> Dépôt
# Tournée 2: Dépôt -> Client 2 -> Dépôt
solution_representation = [0, 1, 3, 0, 2, 0] 

# On crée un objet "Individu" avec cette représentation
individu_test = Individual(solution_representation)


# --- 4. Exécution du calcul de Fitness ---
print(f"--- Évaluation de l'Individu ---")
print(f"Représentation: {individu_test.representation}")

# C'est ici que la logique de 'individual.py' est appelée
fitness_calculee = individu_test.calculate_fitness(problem)

print(f"\n--- Résultats du Calcul ---")
print(f"Fitness (Coût Z total): {fitness_calculee:.2f}")
print(f"  > Distance totale: {individu_test.total_distance:.2f}")
print(f"  > Nb. véhicules: {individu_test.num_vehicles} (Coût: {individu_test.num_vehicles * problem.alpha})")
print(f"  > Retard total: {individu_test.total_delay:.2f} (Coût: {individu_test.total_delay * problem.beta})")


# --- 5. Test d'un cas INVALIDE (avec incompatibilité) ---
# Dans problem.py, nous avons défini (1, 2) comme incompatibles
solution_invalide_rep = [0, 1, 2, 3, 0] # 1 et 2 sont dans la même tournée
individu_invalide = Individual(solution_invalide_rep)

print("\n--- Évaluation d'un Individu INVALIDE ---")
fitness_invalide = individu_invalide.calculate_fitness(problem)
print(f"Représentation: {individu_invalide.representation}")
print(f"Fitness (devrait être infini): {fitness_invalide}")
print("--------------------------------")