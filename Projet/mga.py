# Fichier: mga.py

import random
from problem import ProblemInstance
from individual import Individual
from operators_genetic import crossover, mutation
from operators_local_search import apply_local_search
from operators_local_search import _calculate_route_cost

class MemeticAlgorithm:
    """
    Implémente l'Algorithme Génétique Mémétique (MGA)
    pour le problème VRPTW-C.
   
    """
    def __init__(self, problem: ProblemInstance, pop_size, generations, 
                 crossover_rate, mutation_rate, elite_size):
        
        self.problem = problem
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elite_size = elite_size # Nombre d'élites à conserver

        self.population = []
        self.best_solution = None

    def _initialize_population(self):
        """
        Génère la population initiale de N individus.
        Doit créer des solutions FAISABLES.
        Avec la nouvelle contrainte dure t_i <= l_i, nous devons
        filtrer les solutions initiales invalides.
        """
        print("Initialisation de la population (filtrage des solutions invalides)...")
        self.population = []
        attempts = 0
        MAX_INIT_ATTEMPTS = self.pop_size * 200 # Augmentation de la sécurité

        while len(self.population) < self.pop_size and attempts < MAX_INIT_ATTEMPTS:
            new_individual = self._create_initial_solution()
            new_individual.calculate_fitness(self.problem)
            
            # On n'ajoute que les solutions valides (non infinies)
            if new_individual.fitness != float('inf'):
                self.population.append(new_individual)
            
            attempts += 1
        
        if not self.population:
            # Si on n'a trouvé AUCUNE solution valide
            print("\n" + "="*50)
            print("ERREUR CRITIQUE: Impossible de générer une population initiale valide.")
            print("Cela signifie que l'heuristique d'insertion aléatoire")
            print("échoue à respecter les fenêtres de temps strictes (t_i <= l_i).")
            print("Causes possibles: Fenêtres de temps trop serrées, ou problème de données.")
            print("="*50 + "\n")
            raise Exception("Échec de l'initialisation de la population.")
        
        # Initialiser la meilleure solution
        self.best_solution = min(self.population, key=lambda ind: ind.fitness)
        print(f"Population initiale VALIDE créée ({len(self.population)} individus). Meilleure fitness: {self.best_solution.fitness:.2f}")

    def _create_initial_solution(self):
        """
        HEURISTIQUE D'INITIALISATION "BEST INSERTION" (Meilleure Insertion).
        
        C'est beaucoup plus lent, mais beaucoup plus intelligent.
        Cela va drastiquement réduire le nombre de véhicules initial.
        """
        
        # 1. Trier les clients par "due date" (l_i)
        clients_to_insert = sorted(
            self.problem.clients.keys(),
            key=lambda client_id: self.problem.get_node(client_id)['l']
        )
        
        routes = [] # Liste de listes (tournées)
        unserved_clients = [] # Clients que nous n'arrivons pas à insérer

        for client_id in clients_to_insert:
            client_to_insert = self.problem.get_node(client_id)
            if not client_to_insert: continue

            best_insertion_cost = float('inf')
            best_route_idx = -1
            best_position_idx = -1

            # 2. Essayer d'insérer ce client dans la MEILLEURE position
            for r_idx, route in enumerate(routes):
                
                # --- Vérifications rapides (pour la tournée entière) ---
                
                # 2a. Capacité
                current_demand = sum(self.problem.get_node(c_id)['demand'] for c_id in route)
                if current_demand + client_to_insert['demand'] > self.problem.vehicle_capacity:
                    continue # Route pleine

                # 2b. Incompatibilité
                is_incompatible = False
                for existing_client_id in route:
                    pair = tuple(sorted((client_id, existing_client_id)))
                    if pair in self.problem.incompatibilities:
                        is_incompatible = True
                        break
                if is_incompatible:
                    continue # Incompatible avec un client de cette route
                
                # --- Vérification de chaque position (coûteux) ---
                
                # On calcule le coût actuel de la tournée
                original_route_cost = _calculate_route_cost(route, self.problem)
                
                for pos in range(len(route) + 1):
                    # Essayer d'insérer le client à la position 'pos'
                    new_route = route[:pos] + [client_id] + route[pos:]
                    
                    # 2c. Vérifier la validité (Temps)
                    new_route_cost = _calculate_route_cost(new_route, self.problem)
                    
                    if new_route_cost == float('inf'):
                        continue # Cette position viole les temps

                    # C'est une insertion valide. Calculer "l'augmentation" de coût
                    insertion_cost_increase = new_route_cost - original_route_cost
                    
                    if insertion_cost_increase < best_insertion_cost:
                        best_insertion_cost = insertion_cost_increase
                        best_route_idx = r_idx
                        best_position_idx = pos
            
            # 3. Décision: Insérer ou créer une nouvelle route?
            if best_route_idx != -1:
                # On a trouvé un emplacement valide. On l'insère.
                routes[best_route_idx].insert(best_position_idx, client_id)
            else:
                # AUCUN emplacement valide n'a été trouvé dans les tournées existantes.
                # On crée une nouvelle tournée pour ce client.
                new_route = [client_id]
                
                # On vérifie que le client est servable seul
                if _calculate_route_cost(new_route, self.problem) != float('inf'):
                    routes.append(new_route)
                else:
                    unserved_clients.append(client_id)
        
        # 4. Signaler si des clients n'ont pas pu être servis
        if unserved_clients:
             print(f"  > Avertissement: Heuristique 'Best Insertion' n'a pas pu servir {len(unserved_clients)} clients.")
             print(f"  > Clients non servis: {unserved_clients}")

        # 5. Convertir au format de représentation
        representation = [0]
        for route in routes:
            if route: 
                representation.extend(route)
                representation.append(0)
            
        return Individual(representation)

    def _selection(self, k=3):
        """
        Sélection par tournoi (Taille k=3).
       
        
        CORRECTIF: Gère le cas où la population est plus petite
        que la taille du tournoi (k).
        """
        
        # Si la population est trop petite pour un tournoi,
        # on retourne juste le meilleur individu disponible.
        if len(self.population) < k:
            return min(self.population, key=lambda ind: ind.fitness)
        
        # Comportement normal
        tournament = random.sample(self.population, k)
        return min(tournament, key=lambda ind: ind.fitness) 

    def run(self):
        """
        Lance l'exécution de l'algorithme génétique mémétique.
        """
        self._initialize_population()
        
        # Boucle principale des générations
        for g in range(self.generations):
            new_population = []

            # 1. ÉLITISME: Conserver les meilleurs individus
            sorted_pop = sorted(self.population, key=lambda ind: ind.fitness)
            elites = sorted_pop[:self.elite_size]
            new_population.extend(elites)

            # 2. Remplir le reste de la population
            while len(new_population) < self.pop_size:
                # 2a. Sélection
                parent1 = self._selection()
                parent2 = self._selection()

                # 2b. Croisement
                if random.random() < self.crossover_rate:
                    child = crossover(parent1, parent2, self.problem)
                else:
                    child = Individual(parent1.representation.copy()) # Clone

                # 2c. Mutation
                if random.random() < self.mutation_rate:
                    child = mutation(child, self.problem)

                # 2d. ÉTAPE MÉMÉTIQUE: Optimisation Locale
                child = apply_local_search(child, self.problem)
                
                # 2e. Évaluation du nouvel individu
                child.calculate_fitness(self.problem)
                
                new_population.append(child)

            # Mettre à jour la population
            self.population = new_population

            # Mettre à jour la meilleure solution globale
            current_best = min(self.population, key=lambda ind: ind.fitness)
            if current_best.fitness < self.best_solution.fitness:
                self.best_solution = current_best

            print(f"Génération {g+1}/{self.generations} | Meilleure Fitness: {self.best_solution.fitness:.2f}")

        # Fin de l'algorithme
        print("\n--- Optimisation Terminée ---")
        return self.best_solution