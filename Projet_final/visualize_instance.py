import matplotlib.pyplot as plt
import networkx as nx
import math

# --- Début de la définition de la classe ProblemInstance ---
# (Copiée de problem.py pour rendre ce script autonome)

class ProblemInstance:
    """
    Cette classe contient toutes les données d'une instance du VRPTW-C.
    Les données sont chargées une fois et considérées comme immuables.
    """
    def __init__(self, filepath, alpha, beta):
        self.alpha = alpha
        self.beta = beta
        self.clients = {}
        self.depot = None
        self.vehicle_capacity = 0
        self.distance_matrix = []
        self.incompatibilities = set()
        
        # On utilise directement la simulation à 10 clients
        self._load_simulated_10_clients(filepath)

    def _calculate_distances(self):
        """
        Calcule la matrice de distance euclidienne entre tous les nœuds.
        """
        nodes = [self.depot] + list(self.clients.values())
        num_nodes = len(nodes)
        self.distance_matrix = [[0] * num_nodes for _ in range(num_nodes)]

        for i in range(num_nodes):
            for j in range(num_nodes):
                node_i = nodes[i]
                node_j = nodes[j]
                dist = math.sqrt((node_i['x'] - node_j['x'])**2 + 
                                (node_i['y'] - node_j['y'])**2)
                self.distance_matrix[i][j] = dist

    def _load_simulated_10_clients(self, filepath):
        """
        Un parseur SIMULÉ pour un jeu de 10 clients.
       
        """
        print(f"Chargement de l'instance SIMULÉE (10 clients) depuis {filepath}...")
        
        self.vehicle_capacity = 200

        self.depot = {
            'id': 0, 'x': 40, 'y': 50, 'demand': 0,
            'e': 0, 'l': 1200, 's': 0
        }
        
        clients_data = [
            (1, 45, 68, 10, 912, 967, 90),
            (2, 45, 70, 30, 825, 870, 90),
            (3, 42, 66, 10, 65, 146, 90),
            (4, 40, 66, 20, 65, 146, 90),
            (5, 38, 68, 20, 727, 772, 90),
            (6, 35, 66, 10, 727, 772, 90),
            (7, 42, 57, 10, 150, 266, 90),
            (8, 42, 59, 20, 150, 266, 90),
            (9, 38, 58, 10, 321, 401, 90),
            (10, 35, 58, 20, 321, 401, 90)
        ]

        for data in clients_data:
            client_id = data[0]
            self.clients[client_id] = {
                'id': client_id, 'x': data[1], 'y': data[2],
                'demand': data[3], 'e': data[4], 'l': data[5], 's': data[6]
            }
        
        self._calculate_distances()

        incompatibilities_data = [
            (1, 2), (3, 4), (1, 7), (2, 8), (5, 9), (6, 10)
        ]
        
        for pair in incompatibilities_data:
            self.incompatibilities.add(tuple(sorted(pair)))
    
# --- Fin de la définition de la classe ProblemInstance ---


def plot_instance(problem_instance):
    """
    Fonction principale pour créer et sauvegarder le graphe de l'instance.
    """
    print("Création du graphe de l'instance...")
    
    G = nx.Graph()
    pos = {} # Dictionnaire pour stocker les positions (x, y)

    # 1. Ajouter le Dépôt
    depot_id = p.depot['id']
    pos[depot_id] = (p.depot['x'], p.depot['y'])
    G.add_node(depot_id, color='red', size=400)

    # 2. Ajouter les Clients
    for client_id, data in p.clients.items():
        pos[client_id] = (data['x'], data['y'])
        G.add_node(client_id, color='lightblue', size=200)

    # 3. Ajouter les arêtes d'Incompatibilité
    incompatibility_edges = []
    for (i, j) in p.incompatibilities:
        if G.has_node(i) and G.has_node(j):
            G.add_edge(i, j)
            incompatibility_edges.append((i, j))

    # 4. Dessiner le graphe
    plt.figure(figsize=(13, 11))

    node_colors = [data['color'] for _, data in G.nodes(data=True)]
    node_sizes = [data['size'] for _, data in G.nodes(data=True)]

    # Dessiner les nœuds
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes)

    # Dessiner les arêtes d'incompatibilité
    nx.draw_networkx_edges(G, pos, edgelist=incompatibility_edges, 
                           style='dashed', edge_color='red', width=2)

    # Dessiner les étiquettes (IDs)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    plt.title("Représentation de l'Instance VRPTW-C (10 Clients)", size=18, weight='bold')
    plt.xlabel("Coordonnée X", size=14)
    plt.ylabel("Coordonnée Y", size=14)
    plt.axis('on')
    plt.grid(True)
    
    # 5. Créer la légende
    depot_handle = plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor='red', markersize=15, 
                              label='Dépôt (ID 0)')
    client_handle = plt.Line2D([0], [0], marker='o', color='w', 
                               markerfacecolor='lightblue', markersize=10, 
                               label='Clients (ID 1-10)')
    incomp_handle = plt.Line2D([0], [0], linestyle='--', color='red', 
                               linewidth=2, label='Contrainte d\'Incompatibilité')
                               
    plt.legend(handles=[depot_handle, client_handle, incomp_handle], 
               loc='upper right', fontsize=12)

    # 6. Sauvegarder le fichier
    output_filename = "instance_graph.png"
    plt.savefig(output_filename)
    print(f"Graphe sauvegardé avec succès sous le nom : {output_filename}")


# --- Point d'entrée du script ---
if __name__ == "__main__":
    try:
        # On charge l'instance (alpha et beta n'ont pas d'importance ici)
        p = ProblemInstance("data/simulated.txt", alpha=0, beta=0)
        print(f"Clients: {list(p.clients.keys())}")
        print(f"Incompatibilités: {p.incompatibilities}")
        
        # On génère le graphique
        plot_instance(p)
        
    except ImportError:
        print("\nERREUR: Les librairies 'matplotlib' et 'networkx' sont requises.")
        print("Veuillez les installer en utilisant la commande :")
        print("pip install matplotlib networkx")
    except Exception as e:
        print(f"Une erreur est survenue: {e}")