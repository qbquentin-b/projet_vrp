# Fichier: operators_local_search.py (MIS À JOUR AVEC EXCHANGE INTER-ROUTES)

import random
import itertools
from individual import Individual
from problem import ProblemInstance

# ---------------------------------------------------------------------------
# FONCTION UTILITAIRE (Inchangée)
# ---------------------------------------------------------------------------

def _calculate_route_cost(route, problem: ProblemInstance):
    """
    Calcule le coût d'une SEULE tournée (Modèle "Strict").
   
    """
    total_distance = 0
    total_delay_penalty = 0    # Pénalité Beta (t_i - e_i)
    current_time = 0.0
    last_node_id = 0 

    for client_id in route:
        client = problem.get_node(client_id)
        if not client: return float('inf') 

        travel_time = problem.get_distance(last_node_id, client_id)
        total_distance += travel_time
        arrival_time = current_time + travel_time
        
        start_service_time = max(client['e'], arrival_time)
        
        if start_service_time > client['l']:
            return float('inf') # Invalide (Contrainte Dure)

        delay_penalty = start_service_time - client['e']
        total_delay_penalty += delay_penalty
        
        current_time = start_service_time + client['s']
        last_node_id = client_id

    total_distance += problem.get_distance(last_node_id, 0)
    
    cost = (
        total_distance + 
        (problem.beta * total_delay_penalty)
    )
    return cost

# ---------------------------------------------------------------------------
# OPÉRATEUR 1: 2-OPT (Intra-Tournée) (Inchangé)
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
# OPÉRATEUR 2: RELOCATE (Inter-Tournées) (Inchangé)
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
        
        if cost_r1_old == float('inf') or cost_r2_old == float('inf'):
            continue
            
        cost_before = cost_r1_old + cost_r2_old
        if len(r1) == 1:
            cost_before += problem.alpha

        r1_new = r1[:idx_client] + r1[idx_client+1:]
        cost_r1_new = _calculate_route_cost(r1_new, problem)

        best_r2_new = None
        best_cost_after = float('inf')

        for i in range(len(r2) + 1):
            r2_new = r2[:i] + [client_to_move] + r2[i:]
            cost_r2_new = _calculate_route_cost(r2_new, problem)
            
            if cost_r2_new == float('inf'):
                continue

            is_incompatible = False
            for existing_client_id in r2: 
                pair = tuple(sorted((client_to_move, existing_client_id)))
                if pair in problem.incompatibilities:
                    is_incompatible = True; break
            if is_incompatible:
                cost_r2_new = float('inf'); continue

            cost_after = cost_r1_new + cost_r2_new
            
            if cost_after < best_cost_after:
                best_cost_after = cost_after
                best_r2_new = r2_new
        
        if best_cost_after < cost_before - 1e-5:
            routes[idx_r1] = r1_new
            routes[idx_r2] = best_r2_new
            
            new_representation = [0]
            for route in routes:
                if route: new_representation.extend(route); new_representation.append(0)
            return Individual(new_representation) 

    return individual

# ---------------------------------------------------------------------------
# NOUVEL OPÉRATEUR 3: EXCHANGE (Inter-Tournées / 2-Opt Inter)
# ---------------------------------------------------------------------------

def _check_incompatibility_in_route(route, problem: ProblemInstance):
    """Vérifie les incompatibilités dans une tournée donnée."""
    for i, j in itertools.combinations(route, 2):
        if tuple(sorted((i, j))) in problem.incompatibilities:
            return True # Incompatible
    return False

def _apply_exchange_inter_route(individual: Individual, problem: ProblemInstance) -> Individual:
    """
    Tente d'échanger les "queues" de deux tournées (2-Opt Inter-Route).
    
    A: 0 -> A_head -> A_tail -> 0
    B: 0 -> B_head -> B_tail -> 0
    
    Devient:
    
    A': 0 -> A_head -> B_tail -> 0
    B': 0 -> B_head -> A_tail -> 0
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

    num_attempts = len(problem.clients) # Nombre de tentatives

    for _ in range(num_attempts):
        try:
            idx_r1, idx_r2 = random.sample(range(len(routes)), 2)
        except ValueError:
            break 
            
        r1 = routes[idx_r1]
        r2 = routes[idx_r2]
        
        if not r1 or not r2: continue

        # Choisir un point de coupe pour chaque tournée
        cut_point_1 = random.randrange(len(r1))
        cut_point_2 = random.randrange(len(r2))
        
        # Définir les têtes et les queues
        r1_head, r1_tail = r1[:cut_point_1], r1[cut_point_1:]
        r2_head, r2_tail = r2[:cut_point_2], r2[cut_point_2:]
        
        # Créer les nouvelles tournées
        r1_new = r1_head + r2_tail
        r2_new = r2_head + r1_tail

        # 1. Vérifier les incompatibilités (vérification rapide)
        #    On vérifie qu'un client de r1_head n'est pas incompatible
        #    avec un client de r2_tail (et vice-versa).
        
        # (Pour simplifier, on vérifie juste la tournée finale)
        if _check_incompatibility_in_route(r1_new, problem):
            continue
        if _check_incompatibility_in_route(r2_new, problem):
            continue

        # 2. Vérifier les coûts
        cost_r1_old = _calculate_route_cost(r1, problem)
        cost_r2_old = _calculate_route_cost(r2, problem)
        
        if cost_r1_old == float('inf') or cost_r2_old == float('inf'):
            continue
            
        cost_before = cost_r1_old + cost_r2_old
        
        cost_r1_new = _calculate_route_cost(r1_new, problem)
        cost_r2_new = _calculate_route_cost(r2_new, problem)
        
        if cost_r1_new == float('inf') or cost_r2_new == float('inf'):
            continue # Invalide (temps, capa)

        cost_after = cost_r1_new + cost_r2_new
        
        # 3. Accepter si amélioration
        if cost_after < cost_before - 1e-5:
            routes[idx_r1] = r1_new
            routes[idx_r2] = r2_new
            
            # Reconstruire et retourner l'individu amélioré
            new_representation = [0]
            for route in routes:
                if route: new_representation.extend(route); new_representation.append(0)
            return Individual(new_representation) 

    # Si aucune amélioration trouvée
    return individual

# ---------------------------------------------------------------------------
# FONCTION PRINCIPALE (Wrapper) - MISE À JOUR
# ---------------------------------------------------------------------------

def apply_local_search(individual: Individual, problem: ProblemInstance) -> Individual:
    """
    Fonction principale (wrapper) appelée par mga.py.
    Applique 2-Opt, PUIS Relocate, PUIS Exchange.
   
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
    
    # --- 3. NOUVEAU: Optimisation Exchange (Inter-tournées) ---
    individual_after_exchange = _apply_exchange_inter_route(individual_after_relocate, problem)
    
    # Retourner l'individu final, triplement optimisé
    return individual_after_exchange