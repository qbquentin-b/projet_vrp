import math
import json
import itertools # <-- NOUVEL IMPORT pour comparer les paires

class ProblemInstance:
    """
    Cette classe contient toutes les données d'une instance du VRPTW-C.
    Lit un fichier au format JSON et génère les incompatibilités
    à partir des attributs des clients.
    """
    
    def __init__(self, filepath, alpha, beta):
        self.alpha = alpha
        self.beta = beta
        self.clients = {}
        self.depot = None
        self.vehicle_capacity = 0 
        self.incompatibilities = set()
        self.distance_matrix = []
        
        print(f"--- 1. Chargement de l'instance JSON ---")
        self._load_json_instance(filepath)
        
        print(f"--- 2. Chargement des contraintes 'C' (Incompatibilités) ---")
        # Étape 1: Charger les paires manuelles (si le fichier existe)
        self._load_manual_incompatibilities(filepath)
        # Étape 2: Générer les paires basées sur les règles
        self._generate_attribute_incompatibilities()
        
        print(f"Total incompatibilités (manuelles + auto): {len(self.incompatibilities)}")
        
        print(f"--- 3. Calcul des distances ---")
        self._calculate_distances()
        print(f"Instance '{filepath}' chargée avec succès.")

    
    def _load_json_instance(self, filepath):
        """
        Parseur pour le format d'instance JSON.
        MAINTENANT, il charge aussi le bloc 'attributes'.
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"ERREUR: Fichier d'instance JSON non trouvé à {filepath}")
            raise
        except json.JSONDecodeError:
            print(f"ERREUR: Le fichier '{filepath}' n'est pas un JSON valide.")
            raise

        try:
            self.vehicle_capacity = float(data["vehicle_capacity"])
        except KeyError:
            print("ERREUR: 'vehicle_capacity' manquant dans le fichier JSON.")
            raise
        
        for key, customer_data in data.items():
            if key == "vehicle_capacity": continue

            try:
                client_id = int(key.split('_')[-1])
            except (ValueError, IndexError):
                print(f"AVERTISSEMENT: Clé JSON ignorée (format inconnu): {key}")
                continue
                
            try:
                internal_data = {
                    'id': client_id,
                    'x': float(customer_data["coordinates"]["x"]),
                    'y': float(customer_data["coordinates"]["y"]),
                    'demand': float(customer_data["demand"]),
                    'e': float(customer_data["ready_time"]),
                    'l': float(customer_data["due_time"]),
                    's': float(customer_data["service_time"]),
                    # NOUVEAU: Charger les attributs (ou un dict vide)
                    'attributes': customer_data.get("attributes", {})
                }
            except KeyError as e:
                print(f"ERREUR: Donnée manquante {e} pour le client '{key}' dans le JSON.")
                raise
            
            if client_id == 0:
                self.depot = internal_data
            else:
                self.clients[client_id] = internal_data
        
        if not self.depot:
            print("ERREUR: 'customer_0' (dépôt) manquant dans le JSON.")
            raise
            
        print(f"Instance JSON chargée: {len(self.clients)} clients, capacité véhicule: {self.vehicle_capacity}")

    
    def _load_manual_incompatibilities(self, base_filepath):
        """
        Charge les incompatibilités manuelles depuis _incomp.txt
        (Code inchangé)
        """
        incomp_filepath = base_filepath.rsplit('.', 1)[0] + "_incomp.txt"
        
        try:
            with open(incomp_filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    
                    parts = line.split()
                    if len(parts) >= 2:
                        client1 = int(parts[0])
                        client2 = int(parts[1])
                        self.add_incompatibility(client1, client2)
            
            print(f"Chargé {len(self.incompatibilities)} contraintes manuelles depuis {incomp_filepath}.")

        except FileNotFoundError:
            print(f"Fichier d'incompatibilité manuelle '{incomp_filepath}' non trouvé.")
            self.incompatibilities = set()
            
    
    # NOUVELLE FONCTION
    def _generate_attribute_incompatibilities(self):
        """
        Parcourt tous les clients et génère les incompatibilités
        en se basant sur leurs attributs.
        (Version Corrigée)
        """
        print("Génération des incompatibilités basées sur les attributs...")
        
        # Parcourir chaque paire unique de clients
        all_clients = list(self.clients.values())
        for client_i, client_j in itertools.combinations(all_clients, 2):
            
            attr_i = client_i.get("attributes", {})
            attr_j = client_j.get("attributes", {})
            id_i = client_i['id']
            id_j = client_j['id']

            # RÈGLE 1: TEMPÉRATURE (Inchangée)
            # Incompatible s'ils ont des températures définies et différentes.
            temp_i = attr_i.get("temperature", "any")
            temp_j = attr_j.get("temperature", "any")
            if temp_i != "any" and temp_j != "any" and temp_i != temp_j:
                self.add_incompatibility(id_i, id_j)
                continue 

            # RÈGLE 2: ÉQUIPEMENT D'ACCÈS (Logique Corrigée)
            # Un client "none" est compatible avec tout.
            # Une incompatibilité n'arrive que si les deux clients ont des
            # besoins SPÉCIFIQUES et DIFFÉRENTS (ex: 'tail_lift' vs 'crane').
            
            access_i = attr_i.get("access_requires", "none")
            access_j = attr_j.get("access_requires", "none")
            
            # Si l'un des deux est "none", ils sont compatibles.
            # S'ils sont identiques (ex: 'tail_lift' et 'tail_lift'), ils sont compatibles.
            # Ils ne sont incompatibles que s'ils sont différents ET qu'aucun n'est "none".
            if access_i != "none" and access_j != "none" and access_i != access_j:
                 self.add_incompatibility(id_i, id_j)
                 continue

            # RÈGLE 3: CONCURRENT / INCOMPATIBILITÉ MANUELLE (Inchangée)
            if id_j in attr_i.get("incompatible_with", []):
                self.add_incompatibility(id_i, id_j)
                continue
            
            if id_i in attr_j.get("incompatible_with", []):
                self.add_incompatibility(id_i, id_j)
                continue

    
    # NOUVELLE FONCTION UTILITAIRE
    def add_incompatibility(self, client1, client2):
        """Ajoute une paire d'incompatibilité à l'ensemble."""
        pair = tuple(sorted((client1, client2)))
        self.incompatibilities.add(pair)
            
    
    # (Le reste du fichier: _calculate_distances, get_distance, get_node
    # est identique à la version précédente)

    def _calculate_distances(self):
        """Calcule la matrice de distance euclidienne."""
        num_nodes = len(self.clients) + 1 
        
        nodes = [None] * num_nodes
        nodes[0] = self.depot
        for client_id, data in self.clients.items():
            if client_id < num_nodes:
                nodes[client_id] = data

        self.distance_matrix = [[0] * num_nodes for _ in range(num_nodes)]

        for i in range(num_nodes):
            for j in range(num_nodes):
                node_i = nodes[i]
                node_j = nodes[j]
                
                if not node_i or not node_j: continue
                    
                dist = math.sqrt((node_i['x'] - node_j['x'])**2 + 
                                (node_i['y'] - node_j['y'])**2)
                self.distance_matrix[i][j] = dist

    def get_distance(self, node_id_1, node_id_2):
        """Récupère la distance (coût) entre deux nœuds via leurs IDs."""
        try:
            return self.distance_matrix[node_id_1][node_id_2]
        except IndexError:
            return 0 

    def get_node(self, node_id):
        """Récupère le dictionnaire de données pour un nœud (client ou dépôt)."""
        if node_id == 0:
            return self.depot
        return self.clients.get(node_id)