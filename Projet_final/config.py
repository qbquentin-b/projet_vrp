# Fichier: config.py
#
# Ce fichier centralise tous les paramètres de l'algorithme
# pour main.py, check_solution.py, et tous les autres scripts.
#
import os

# --- 1. Paramètres de l'Instance ---

# Obtient le chemin absolu du dossier où se trouve config.py
script_dir = os.path.dirname(os.path.abspath(__file__))

INSTANCE_NAME = "C1_10_1.json" # 

# Dis si on veut générer les incompatibilités en Attributs ou pas
GENERER_INCOMPAT_ATTRS = True

# Dis si on veut générer les incompatibilités client-client ou pas
GENERER_LISTES_EXPLICITES = True

# Dis si on veut réutiliser l'instance json actuelle ou la regénérer. 
REUSE_SAME_RANDOM = True

# Dis quelles méthodes Visualize applique. 
VISUALIZE_RUN_MGA = True
VISUALIZE_RUN_EXACT = False

FICHIER_INSTANCE = os.path.join(script_dir, "data", "json", INSTANCE_NAME)

# --- Génération d'instances ---
NUM_CLIENTS = 10

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
GENERATIONS = 500    # Nombre de générations (G)
CROSSOVER_RATE = 0.8 # Taux de croisement (pc)
MUTATION_RATE = 0.02  # Taux de mutation (pm) - Augmenté pour plus d'exploration
ELITE_SIZE = 5       # Nombre d'élites (élitisme)