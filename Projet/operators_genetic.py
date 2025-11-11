# Fichier: operators_genetic.py (MIS À JOUR AVEC MUTATION "DESTROY")

import random
from individual import Individual
from problem import ProblemInstance

# On a besoin de cette fonction pour le Crossover et la Réparation
try:
    from operators_local_search import _calculate_route_cost
except ImportError:
    print("Erreur d'importation circulaire.")
    def _calculate_route_cost(route, problem): return 0.0


# ---------------------------------------------------------------------------
# FONCTIONS UTILITAIRES (Inchangées)
# ---------------------------------------------------------------------------

def _get_routes_from_representation(representation):
    """Utilitaire pour extraire les tournées."""
    routes = []
    current_route = []
    for node_id in representation[1:]:
        if node_id == 0:
            if current_route:
                routes.append(current_route)
            current_route = []
        else:
            current_route.append(node_id)
    return routes

def _get_representation_from_routes(routes):
    """Utilitaire pour reconstruire la représentation."""
    new_representation = [0]
    for route in routes:
        if route: # Ne pas ajouter de tournées vides
            new_representation.extend(route)
            new_representation.append(0)
    return new_representation

# ---------------------------------------------------------------------------
# OPÉRATEUR 1: CROSSOVER (BCRC) - (Inchangé)
# ---------------------------------------------------------------------------

def crossover(parent1: Individual, parent2: Individual, problem: ProblemInstance) -> Individual:
    """Opérateur de Croisement (Crossover) "Best-Cost Route Crossover" (BCRC)."""
   
    
    routes_p1 = _get_routes_from_representation(parent1.representation)
    routes_p2 = _get_routes_from_representation(parent2.representation)
    route_pool = routes_p1 + routes_p2
    
    evaluated_pool = []
    for route in route_pool:
        cost = _calculate_route_cost(route, problem)
        if cost != float('inf'):
            evaluated_pool.append((cost, route))
            
    evaluated_pool.sort(key=lambda x: x[0]) # Tri par coût

    child_routes = []
    served_clients = set()

    for cost, route in evaluated_pool:
        has_duplicate = False
        for client_id in route:
            if client_id in served_clients:
                has_duplicate = True
                break
        
        if not has_duplicate:
            child_routes.append(route)
            served_clients.update(route)

    all_clients = set(problem.clients.keys())
    missing_clients = all_clients - served_clients
    
    if missing_clients:
        missing_clients_list = sorted(
            list(missing_clients),
            key=lambda cid: problem.get_node(cid)['l']
        )
        
        child_routes = _repair_with_best_insertion(child_routes, missing_clients_list, problem)

    new_representation = _get_representation_from_routes(child_routes)
    return Individual(new_representation)

def _repair_with_best_insertion(routes, missing_clients, problem: ProblemInstance):
    """Logique de réparation "Best Insertion" (utilisée par Crossover et Destroy)."""
   
    
    for client_id in missing_clients:
        client_to_insert = problem.get_node(client_id)
        if not client_to_insert: continue

        best_insertion_cost = float('inf')
        best_route_idx = -1
        best_position_idx = -1

        for r_idx, route in enumerate(routes):
            current_demand = sum(problem.get_node(c_id)['demand'] for c_id in route)
            if current_demand + client_to_insert['demand'] > problem.vehicle_capacity:
                continue 

            is_incompatible = False
            for existing_client_id in route:
                pair = tuple(sorted((client_id, existing_client_id)))
                if pair in problem.incompatibilities:
                    is_incompatible = True; break
            if is_incompatible: continue
            
            original_route_cost = _calculate_route_cost(route, problem)
            
            for pos in range(len(route) + 1):
                new_route = route[:pos] + [client_id] + route[pos:]
                new_route_cost = _calculate_route_cost(new_route, problem)
                
                if new_route_cost == float('inf'): continue

                insertion_cost_increase = new_route_cost - original_route_cost
                
                if insertion_cost_increase < best_insertion_cost:
                    best_insertion_cost = insertion_cost_increase
                    best_route_idx = r_idx
                    best_position_idx = pos
        
        if best_route_idx != -1:
            routes[best_route_idx].insert(best_position_idx, client_id)
        else:
            new_route = [client_id]
            if _calculate_route_cost(new_route, problem) != float('inf'):
                routes.append(new_route)
            # else: le client ne peut pas être servi (on l'ignore)

    return routes


# ---------------------------------------------------------------------------
# OPÉRATEUR 2: MUTATION (Mis à jour avec "DESTROY")
# ---------------------------------------------------------------------------

def mutation_destroy_route(individual: Individual, problem: ProblemInstance) -> Individual:
    """
    NOUVELLE MUTATION: Opérateur "Destroy Route" (Agressif).
    
    1. Choisit une tournée au hasard (de préférence une petite).
    2. Supprime cette tournée.
    3. Tente de ré-insérer les clients "orphelins" dans les
       tournées restantes en utilisant "Best Insertion".
    """
    
    routes = _get_routes_from_representation(individual.representation)
    if len(routes) < 2:
        return individual # On ne peut pas détruire la seule tournée

    # 1. Choisir une tournée à détruire
    #    Stratégie: choisir la plus petite (plus facile à réinsérer)
    routes.sort(key=len)
    route_to_destroy = routes.pop(0) # Retire la plus petite tournée
    
    clients_to_reinsert = route_to_destroy
    
    if not clients_to_reinsert:
        return individual # La tournée était vide, rien à faire

    # 2. Ré-insérer les clients orphelins dans les tournées restantes
    #    On trie par urgence (l_i) pour maximiser les chances de succès
    clients_to_reinsert.sort(key=lambda cid: problem.get_node(cid)['l'])
    
    remaining_routes = routes
    repaired_routes = _repair_with_best_insertion(remaining_routes, clients_to_reinsert, problem)
    
    # 3. Retourner le nouvel individu (qui a potentiellement moins de véhicules)
    new_representation = _get_representation_from_routes(repaired_routes)
    return Individual(new_representation)


def mutation_exchange(individual: Individual, problem) -> Individual:
    """Opérateur "Exchange" (Inter-Tournée) (Inchangé)."""
   
    routes = _get_routes_from_representation(individual.representation)
    if len(routes) < 2: return individual
    try:
        idx_r1, idx_r2 = random.sample(range(len(routes)), 2)
        r1, r2 = routes[idx_r1], routes[idx_r2]
        if not r1 or not r2: return individual
        idx_c1, idx_c2 = random.randrange(len(r1)), random.randrange(len(r2))
        r1[idx_c1], r2[idx_c2] = r2[idx_c2], r1[idx_c1]
        new_representation = _get_representation_from_routes(routes)
        return Individual(new_representation)
    except ValueError:
        return individual

def mutation_swap(individual: Individual, problem) -> Individual:
    """Opérateur "Swap" (Intra-Tournée) (Inchangé)."""
   
    routes = _get_routes_from_representation(individual.representation)
    if not routes: return individual 
    route_to_mutate = random.choice(routes)
    if len(route_to_mutate) >= 2:
        idx1, idx2 = random.sample(range(len(route_to_mutate)), 2)
        route_to_mutate[idx1], route_to_mutate[idx2] = route_to_mutate[idx2], route_to_mutate[idx1]
    new_representation = _get_representation_from_routes(routes)
    return Individual(new_representation)


def mutation(individual: Individual, problem: ProblemInstance) -> Individual:
    """
    Fonction de mutation principale (MISE À JOUR).
    Donne une chance à la nouvelle mutation "Destroy".
    """
    
    rand_val = random.random()
    
    if rand_val < 0.25:
        # 25% de chance: Mutation Agressive "Destroy Route"
        return mutation_destroy_route(individual, problem)
    
    elif rand_val < 0.75:
        # 50% de chance: Mutation "Exchange" (Inter-Tournée)
        return mutation_exchange(individual, problem)
        
    else:
        # 25% de chance: Mutation "Swap" (Intra-Tournée)
        return mutation_swap(individual, problem)