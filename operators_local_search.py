# Fichier: operators_local_search.py

import random
from individual import Individual
from problem import ProblemInstance

# ---------------------------------------------------------------------------
# FONCTION UTILITAIRE
# ---------------------------------------------------------------------------

def _calculate_route_cost(route, problem: ProblemInstance):
    """
    Calcule le coût d'une SEULE tournée.
    Modèle "Strict": t_i <= l_i est une contrainte DURE.
   
    """
    total_distance = 0
    total_delay_penalty = 0    # Pénalité Beta (t_i - e_i)
    current_time = 0.0
    last_node_id = 0 # Dépôt

    for client_id in route:
        client = problem.get_node(client_id)
        if not client: return float('inf') 

        travel_time = problem.get_distance(last_node_id, client_id)
        total_distance += travel_time
        arrival_time = current_time + travel_time
        
        start_service_time = max(client['e'], arrival_time)
        
        # 1. CONTRAINTE DURE (REMISE EN PLACE)
        if start_service_time > client['l']:
            return float('inf') # Invalide

        # 2. PÉNALITÉ "RETARD" (Beta)
        delay_penalty = start_service_time - client['e']
        total_delay_penalty += delay_penalty
        
        current_time = start_service_time + client['s']
        last_node_id = client_id

    # Retour au dépôt
    total_distance += problem.get_distance(last_node_id, 0)
    
    # Coût (sans gamma)
    cost = (
        total_distance + 
        (problem.beta * total_delay_penalty)
    )
    return cost

# ---------------------------------------------------------------------------
# OPÉRATEUR 1: 2-OPT (Intra-Tournée)
# ---------------------------------------------------------------------------

def _apply_2_opt_to_route(route, problem: ProblemInstance):
    """
    Applique une recherche locale 2-opt sur une SEULE tournée.
   
    """
    if len(route) < 2:
        return route 

    best_route = route
    best_cost = _calculate_route_cost(best_route, problem)
    
    if best_cost == float('inf'):
        return best_route

    improved = True
    while improved:
        improved = False
        for i in range(len(best_route) - 1):
            for j in range(i + 1, len(best_route)):
                if j - i < 1: continue
                new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                new_cost = _calculate_route_cost(new_route, problem)
                
                if new_cost < best_cost - 1e-5: 
                    best_route = new_route
                    best_cost = new_cost
                    improved = True
                    break 
            if improved:
                break 
    return best_route

# ---------------------------------------------------------------------------
# OPÉRATEUR 2: RELOCATE (Inter-Tournées)
# ---------------------------------------------------------------------------

def _apply_relocate_inter_route(individual: Individual, problem: ProblemInstance) -> Individual:
    """
    Tente de déplacer des clients entre les tournées.
   
    """
    
    routes = []
    current_route = []
    for node_id in individual.representation[1:]:
        if node_id == 0:
            if current_route:
                routes.append(current_route)
            current_route = []
        else:
            current_route.append(node_id)
            
    if len(routes) < 2:
        return individual

    num_attempts = len(problem.clients) 
    
    for _ in range(num_attempts):
        
        try:
            idx_r1, idx_r2 = random.sample(range(len(routes)), 2)
        except ValueError:
            break 
            
        r1 = routes[idx_r1]
        r2 = routes[idx_r2]
        
        if not r1: continue

        idx_client = random.randrange(len(r1))
        client_to_move = r1[idx_client]

        cost_r1_old = _calculate_route_cost(r1, problem)
        cost_r2_old = _calculate_route_cost(r2, problem)
        
        # NE PAS TOUCHER si une tournée est déjà 'inf' (invalide)
        if cost_r1_old == float('inf') or cost_r2_old == float('inf'):
            continue
            
        cost_before = cost_r1_old + cost_r2_old
        if len(r1) == 1:
            cost_before += problem.alpha # On gagne le coût alpha

        r1_new = r1[:idx_client] + r1[idx_client+1:]
        cost_r1_new = _calculate_route_cost(r1_new, problem)

        best_r2_new = None
        best_cost_after = float('inf')

        for i in range(len(r2) + 1):
            r2_new = r2[:i] + [client_to_move] + r2[i:]
            cost_r2_new = _calculate_route_cost(r2_new, problem)
            
            # Si le coût est 'inf', on passe
            if cost_r2_new == float('inf'):
                continue

            # Vérifier l'incompatibilité
            is_incompatible = False
            for existing_client_id in r2: 
                pair = tuple(sorted((client_to_move, existing_client_id)))
                if pair in problem.incompatibilities:
                    is_incompatible = True
                    break
            if is_incompatible:
                cost_r2_new = float('inf')
                continue

            cost_after = cost_r1_new + cost_r2_new
            
            if cost_after < best_cost_after:
                best_cost_after = cost_after
                best_r2_new = r2_new
        
        if best_cost_after < cost_before - 1e-5:
            routes[idx_r1] = r1_new
            routes[idx_r2] = best_r2_new
            
            new_representation = [0]
            for route in routes:
                if route: 
                    new_representation.extend(route)
                    new_representation.append(0)
            return Individual(new_representation) 

    return individual

# ---------------------------------------------------------------------------
# FONCTION PRINCIPALE (Wrapper)
# ---------------------------------------------------------------------------

def apply_local_search(individual: Individual, problem: ProblemInstance) -> Individual:
    """
    Fonction principale (wrapper) appelée par mga.py.
    Applique 2-Opt PUIS Relocate.
   
    """
    
    # --- 1. Optimisation 2-Opt (Intra-tournée) ---
    
    new_representation = [0]
    current_route = []
    
    for node_id in individual.representation[1:]:
        if node_id == 0:
            if current_route:
                improved_route = _apply_2_opt_to_route(current_route, problem)
                new_representation.extend(improved_route)
                new_representation.append(0)
            current_route = []
        else:
            current_route.append(node_id)
            
    individual_after_2opt = Individual(new_representation)
    
    # --- 2. Optimisation Relocate (Inter-tournées) ---
    
    individual_after_relocate = _apply_relocate_inter_route(individual_after_2opt, problem)
    
    return individual_after_relocate