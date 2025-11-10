# Fichier: individual.py

from problem import ProblemInstance
import math

class Individual:
    """
    Représente un individu (un "chromosome") de la population.
    C'est une solution complète au problème VRPTW-C.
   
    """
    
    def __init__(self, representation):
        self.representation = representation 
        self.fitness = float('inf')
        
        # Métriques pour l'analyse
        self.total_distance = 0
        self.num_vehicles = 0
        self.total_delay_penalty = 0    # Pénalité Beta (t_i - e_i)

    def calculate_fitness(self, problem: 'ProblemInstance'):
        """
        Calcule la fitness (coût Z) de cet individu.
        Modèle "Strict": t_i <= l_i est une contrainte DURE.
       
        """
        
        self.total_distance = 0
        self.num_vehicles = 0
        self.total_delay_penalty = 0 
        
        # 1. Diviser la représentation en tournées (routes)
        routes = []
        current_route = []
        for node_id in self.representation[1:]:
            if node_id == 0:
                if current_route: 
                    routes.append(current_route)
                    self.num_vehicles += 1
                current_route = []
            else:
                current_route.append(node_id)
        
        # 2. Itérer sur chaque tournée
        for route in routes:
            current_capacity = 0
            current_time = 0.0
            last_node_id = 0

            # 2a. Vérifier les contraintes DURES (Capacité et Incompatibilité)
            for i in range(len(route)):
                client_id = route[i]
                client = problem.get_node(client_id)
                
                # Capacité
                current_capacity += client['demand']
                if current_capacity > problem.vehicle_capacity:
                    self.fitness = float('inf'); return self.fitness

                # Incompatibilité
                for j in range(i + 1, len(route)):
                    other_client_id = route[j]
                    pair = tuple(sorted((client_id, other_client_id)))
                    if pair in problem.incompatibilities:
                        self.fitness = float('inf'); return self.fitness

            # 2b. Calculer le coût (Distance et Pénalités de temps)
            for client_id in route:
                client = problem.get_node(client_id)
                
                travel_time = problem.get_distance(last_node_id, client_id)
                self.total_distance += travel_time
                arrival_time = current_time + travel_time
                
                # --- GESTION DES FENÊTRES TEMPORELLES (STRICT) ---
                
                # 1. Heure de début de service
                start_service_time = max(client['e'], arrival_time)
                
                # 2. CONTRAINTE DURE (REMISE EN PLACE)
                if start_service_time > client['l']:
                    self.fitness = float('inf') # Solution INVALIDE
                    return self.fitness
                
                # 3. PÉNALITÉ "RETARD" (Beta)
                delay_penalty = start_service_time - client['e']
                self.total_delay_penalty += delay_penalty
                
                # 4. Mise à jour du temps
                current_time = start_service_time + client['s']
                last_node_id = client_id

            # Retour au dépôt
            self.total_distance += problem.get_distance(last_node_id, 0)

        # 3. Calculer la Fitness (Fonction Objectif Finale)
        cost_z = (
            self.total_distance +
            (problem.alpha * self.num_vehicles) +
            (problem.beta * self.total_delay_penalty)
        )
        
        self.fitness = cost_z
        return self.fitness