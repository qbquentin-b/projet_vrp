-----

```markdown
# 🏛️ Architecture du Projet MGA (VRPTW-C)


---

## ⚙️ Fichier de Configuration

### `config.py`
* **Rôle : Centraliser tous les paramètres.**
* C'est ici que vous réglez "les boutons" de votre algorithme sans toucher au code.
* Il contient :
    * Le nom de l'instance à charger (ex: `C101.txt`).
    * Les coûts de la fonction objectif : `alpha` (coût véhicule) et `beta` (pénalité de "retard" $t_i - e_i$).
    * Les paramètres du MGA : `POP_SIZE` (taille de la population), `GENERATIONS`, `CROSSOVER_RATE`, etc.

---

## 🚀 Fichiers d'Exécution

### `main.py`
* **Rôle : Le point d'entrée principal (le "chef d'orchestre").**
* C'est le fichier que vous exécutez (`python main.py`).
* Il effectue les actions suivantes dans l'ordre :
    1.  Il lit le fichier `config.py` pour récupérer les paramètres.
    2.  Il crée un objet `ProblemInstance` (en utilisant `problem.py`) pour charger toutes les données.
    3.  Il crée un objet `MemeticAlgorithm` (en utilisant `mga.py`) et lui donne le problème à résoudre.
    4.  Il lance l'optimisation (`mga.run()`).
    5.  Il appelle la fonction `verify_solution_completeness` pour vérifier les doublons/manques dans la solution finale.
    6.  Il affiche la meilleure solution trouvée et la décomposition des coûts.

### `check_solution.py` (Script de test)
* **Rôle : Valider manuellement une solution.**
* Il vous permet de coller une représentation de solution (ex: `[0, 1, 5, 0, ...]`) et de la faire évaluer par votre `individual.py` pour voir si elle est valide et quel est son coût exact.

### `visualize_instance.py` (Script de test)
* **Rôle : Dessiner un graphique de l'instance.**
* Il charge le problème (`problem.py`) et utilise `matplotlib`/`networkx` pour générer une image des clients et du dépôt, en affichant les contraintes d'incompatibilité en rouge.

---

## 🏛️ Fichiers de Base (Le Cœur du Problème)

### `problem.py`
* **Rôle : Définir le problème à résoudre.**
* Contient la classe `ProblemInstance`.
* Il est responsable de :
    1.  **Lire et parser** le fichier d'instance de Solomon (ex: `C101.txt`) pour obtenir les clients, leurs positions, leurs demandes et leurs **fenêtres de temps**.
    2.  **Lire et parser** votre fichier `_incomp.txt` personnalisé pour obtenir la liste des **paires incompatibles**.
    3.  **Calculer** la matrice des distances entre tous les clients.
    4.  Stocker toutes ces données (capacité véhicule, clients, distances, etc.) pour que le reste de l'algorithme puisse les utiliser.

### `individual.py`
* **Rôle : Définir ce qu'EST une solution (et implémenter la Fonction Objectif).**
* Contient la classe `Individual`, qui représente un "chromosome" (un plan de tournée complet).
* Sa méthode la plus importante est **`calculate_fitness(problem)`** :
    * C'est l'implémentation mathématique de votre **fonction objectif**.
    * Elle prend une solution (ex: `[0, 5, 2, 0, ...]`) et calcule son coût total (`Z`).
    * C'est elle qui vérifie toutes les **contraintes dures** (capacité, incompatibilité).
    * C'est elle qui applique la **contrainte dure** de fenêtre de temps ($t_i \le l_i$), retournant `float('inf')` si elle est violée.
    * C'est elle qui calcule le coût total : (Distance totale) + ($\alpha$ * Nb Véhicules) + ($\beta$ * Pénalité $t_i - e_i$).

---

## 🧬 Fichiers de l'Algorithme (Le Moteur)

### `mga.py`
* **Rôle : Être le moteur de l'Algorithme Génétique Mémétique (MGA).**
* Contient la classe `MemeticAlgorithm`.
* Il gère la **population** (la liste de 50 `Individual`s).
* Il contient la **boucle principale d'évolution** (`run()`):
    1.  **`_initialize_population`** : Crée la population de départ en utilisant l'heuristique "Best Insertion" pour obtenir des solutions valides.
    2.  **`_selection`** : Sélectionne les meilleurs parents (par tournoi).
    3.  **Appelle `crossover`** (depuis `operators_genetic.py`) pour créer des enfants.
    4.  **Appelle `mutation`** (depuis `operators_genetic.py`) pour diversifier les enfants.
    5.  **Appelle `apply_local_search`** (depuis `operators_local_search.py`) : C'est l'étape **Mémétique** qui optimise localement chaque enfant.
    6.  Remplace la vieille population par la nouvelle et recommence.

### `operators_genetic.py` (Le "G" de MGA : Exploration)
* **Rôle : Créer de nouvelles solutions (Enfants).**
* Contient les opérateurs qui explorent l'espace de recherche :
    * **`crossover` (BCRC)** : Combine deux bons parents pour créer un nouvel enfant.
    * **`mutation_swap`** : Échange deux clients *dans* une même tournée (optimisation fine).
    * **`mutation_exchange`** : Échange deux clients *entre* deux tournées (exploration).
    * **`mutation_destroy_route`** : Opérateur agressif qui détruit une tournée et force la réinsertion, pour tenter de réduire le nombre de véhicules.
    * **`_repair_with_best_insertion`** : Fonction clé utilisée par Crossover et Destroy pour insérer les clients "orphelins" de manière valide.

### `operators_local_search.py` (Le "M" de MGA : Intensification)
* **Rôle : Améliorer (optimiser) les solutions existantes.**
* C'est l'étape "d'affinage" qui rend le MGA si puissant.
* Contient les opérateurs d'optimisation locale :
    * **`_calculate_route_cost`** : Une fonction utilitaire cruciale qui calcule le coût d'une *seule* tournée, en vérifiant la contrainte $t_i \le l_i$ (`inf` si violée).
    * **`_apply_2_opt_to_route`** : Optimise l'ordre *à l'intérieur* d'une tournée pour réduire la distance.
    * **`_apply_relocate_inter_route`** : Tente de déplacer un client d'une tournée A vers une tournée B, si cela est valide et réduit le coût total.
    * **`apply_local_search`** : La fonction "wrapper" appelée par `mga.py` qui applique 2-Opt *puis* Relocate à chaque enfant.
```
