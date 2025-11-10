# Fichier: problem.py

import math

class ProblemInstance:
    """
    Cette classe contient toutes les données d'une instance du VRPTW-C.
    Lit un fichier au format Solomon (.txt) et un fichier
    d'incompatibilités_supplémentaire.
    """
    def __init__(self, filepath, alpha, beta):
        # Paramètres de la fonction objectif
        self.alpha = alpha  # Coût fixe par véhicule
        self.beta = beta    # Coût de pénalité (t_i - e_i)

        # Données du problème
        self.clients = {}
        self.depot = None
        self.vehicle_capacity = 0 
        self.incompatibilities = set()
        self.distance_matrix = []
        
        # Lancement du chargement
        print(f"--- 1. Chargement de l'instance Solomon ---")
        self._load_solomon_instance(filepath)
        
        print(f"--- 2. Chargement des contraintes 'C' (Incompatibilités) ---")
        self._load_incompatibilities(filepath)
        
        print(f"--- 3. Calcul des distances ---")
        self._calculate_distances()
        print(f"Instance '{filepath}' chargée avec succès.")


    def _load_solomon_instance(self, filepath):
        """
        Parseur pour les instances de Solomon (type C101, R101, etc.)
       
        """
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"ERREUR: Fichier d'instance non trouvé à {filepath}")
            raise

        section = None
        for line in lines:
            line = line.strip()
            if not line: continue

            if line.startswith("VEHICLE"):
                section = "VEHICLE"; continue
            elif line.startswith("CUSTOMER"):
                section = "CUSTOMER"; continue
            elif line.startswith("NUMBER"): continue
            elif line.startswith("CUST NO."): continue

            parts = line.split()
            if not parts: continue

            if section == "VEHICLE":
                self.vehicle_capacity = float(parts[1])
                section = None
            
            elif section == "CUSTOMER":
                client_id = int(parts[0])
                data = {
                    'id': client_id,
                    'x': float(parts[1]),
                    'y': float(parts[2]),
                    'demand': float(parts[3]),
                    'e': float(parts[4]),      # Ready Time (e_i)
                    'l': float(parts[5]),      # Due Date (l_i)
                    's': float(parts[6])       # Service Time (s_i)
                }
                
                if client_id == 0:
                    self.depot = data
                else:
                    self.clients[client_id] = data
        
        print(f"Instance chargée: {len(self.clients)} clients, capacité véhicule: {self.vehicle_capacity}")

    def _load_incompatibilities(self, base_filepath):
        """
        Tente de charger un fichier d'incompatibilités_associé.
        Ex: pour 'data/C101.txt', cherche 'data/C101_incomp.txt'
       
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
                        pair = tuple(sorted((client1, client2)))
                        self.incompatibilities.add(pair)
            
            print(f"Chargé {len(self.incompatibilities)} contraintes d'incompatibilité depuis {incomp_filepath}.")

        except FileNotFoundError:
            print(f"Fichier d'incompatibilité '{incomp_filepath}' non trouvé. ")
            print("L'algorithme continue avec 0 incompatibilités.")
            self.incompatibilities = set()

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