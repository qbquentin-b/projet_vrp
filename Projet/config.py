# Fichier: config.py
#
# Ce fichier centralise tous les paramètres de l'algorithme
# pour main.py, check_solution.py, et tous les autres scripts.
#
import os

# --- 1. Paramètres de l'Instance ---

# Obtient le chemin absolu du dossier où se trouve config.py
script_dir = os.path.dirname(os.path.abspath(__file__))

INSTANCE_NAME = "C101.json" # <--- Changez .txt en .json

FICHIER_INSTANCE = os.path.join(script_dir, "data", INSTANCE_NAME)

# --- 2. Paramètres de la Fonction Objectif ---
#

# Coût fixe pour l'utilisation d'un nouveau véhicule
# (Essayez 500 ou 1000 pour forcer la réduction de véhicules)
COUT_FIXE_VEHICULE = 100   # alpha

# Pénalité pour le "retard" (temps écoulé après le début de la fenêtre e_i)
#
PENALITE_RETARD = 2     # beta
# Fichier: config.py


# --- 3. Paramètres du MGA (Algorithme Mémétique) ---
#

POP_SIZE = 50        # Taille de la population (N)
GENERATIONS = 100    # Nombre de générations (G)
CROSSOVER_RATE = 0.8 # Taux de croisement (pc)
MUTATION_RATE = 0.02  # Taux de mutation (pm) - Augmenté pour plus d'exploration
ELITE_SIZE = 5       # Nombre d'élites (élitisme)