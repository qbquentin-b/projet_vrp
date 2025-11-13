import os
import sys
import json
import csv
import glob
import subprocess
import datetime
import matplotlib.pyplot as plt

def project_root():
    return os.path.abspath(os.path.dirname(__file__))


def run_python(script_path):
    subprocess.run([sys.executable, script_path], check=True)


def latest_csv(results_dir):
    files = glob.glob(os.path.join(results_dir, "Results_*.csv"))
    if not files:
        raise FileNotFoundError(f"Aucun CSV trouvé dans {results_dir}")
    return max(files, key=os.path.getmtime)


def load_coords_from_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    coords = {}
    for key, val in data.items():
        if key == "vehicle_capacity":
            continue
        try:
            cid = int(key.split("_")[1])
        except Exception:
            continue
        coords[cid] = (float(val["coordinates"]["x"]), float(val["coordinates"]["y"]))
    return coords


def parse_routes_from_csv(csv_path):
    routes = []
    route_col_idx = None
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or all((str(c).strip() == "" for c in row)):
                continue
            if route_col_idx is None:
                lowered = [str(c).strip().lower() for c in row]
                if "route" in lowered:
                    route_col_idx = lowered.index("route")
                continue
            # Ligne de détail
            if route_col_idx < len(row):
                route_text = str(row[route_col_idx]).strip()
                if route_text:
                    try:
                        nodes = [int(tok.strip()) for tok in route_text.split("->")]
                        if len(nodes) >= 2:
                            routes.append(nodes)
                    except ValueError:
                        # ignorer lignes non conformes (ex: nouveau header)
                        pass
    return routes


def sanitize_routes(routes):
    """Ensure each route starts and ends at 0; warn and auto-fix if needed."""
    sanitized = []
    for idx, r in enumerate(routes):
        if not r:
            continue
        fixed = list(r)
        changed = False
        if fixed[0] != 0:
            fixed = [0] + fixed
            changed = True
        if fixed[-1] != 0:
            fixed = fixed + [0]
            changed = True
        if changed:
            print(f"[Visualize] Avertissement: route {idx} ne fermait pas sur 0. Auto-correction: {r} -> {fixed}")
        sanitized.append(fixed)
    return sanitized


def plot_routes(coords, routes, title, out_path):
    plt.figure(figsize=(11, 9))

    # Clients (dessinés d'abord pour rester en arrière-plan)
    cx, cy = [], []
    for cid, (x, y) in coords.items():
        if cid == 0:    
            continue
        cx.append(x)
        cy.append(y)
    if cx:
        plt.scatter(cx, cy, c="black", s=40, label="Clients", zorder=1)

    # Tracer les chemins par véhicule
    colors = plt.cm.tab20.colors
    for idx, nodes in enumerate(routes):
        col = colors[idx % len(colors)]
        # segments
        for i in range(len(nodes) - 1):
            a = nodes[i]
            b = nodes[i + 1]
            if a not in coords or b not in coords:
                continue
            x1, y1 = coords[a]
            x2, y2 = coords[b]
            plt.plot([x1, x2], [y1, y2], color=col, linewidth=2.2, zorder=2)
        # marqueur de fin de route (retour au dépôt)
        if nodes and nodes[-1] in coords:
            x0, y0 = coords[nodes[-1]]
            plt.scatter([x0], [y0], s=60, facecolors='none', edgecolors=col, linewidths=2, zorder=4)
        plt.plot([], [], color=col, linewidth=2, label=f"Véhicule {idx}")

    # Dépôt (dessiné en dernier pour être visible mais plus petit)
    depot_xy = coords.get(0, (None, None))
    if depot_xy[0] is not None:
        plt.scatter([depot_xy[0]], [depot_xy[1]], c="red", s=110, marker="s", label="Dépôt (0)", zorder=3)

    plt.title(title)
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend(loc="best", fontsize=9, ncol=2)
    plt.tight_layout()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()


if __name__ == "__main__":
    base_dir = project_root()

    # Import config for instance info
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)
    import config  # noqa: E402  

    # Exiger un JSON déjà présent (pas de génération automatique ici)
    if not os.path.exists(config.FICHIER_INSTANCE):
        instance_base = os.path.splitext(os.path.basename(config.INSTANCE_NAME))[0]
        print(f"ERREUR: JSON introuvable: {config.FICHIER_INSTANCE}")
        print("Crée le JSON une seule fois avec txt_to_json.py, par ex.:")
        print(f"  python txt_to_json.py {instance_base} --num-clients 100")
        sys.exit(1)

    instance_json = config.FICHIER_INSTANCE
    instance_base = os.path.splitext(os.path.basename(config.INSTANCE_NAME))[0]

    # Read visualize execution flags from config (defaults True)
    RUN_MGA = getattr(config, "VISUALIZE_RUN_MGA", True)
    RUN_EXACT = getattr(config, "VISUALIZE_RUN_EXACT", True)
    if not RUN_MGA and not RUN_EXACT:
        print("Visualize: rien à faire (MGA et Exact désactivés).")
        sys.exit(0)

    # Shared timestamp and output folders
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    vis_mga_dir = os.path.join(base_dir, "Visualize_MGA")
    vis_exact_dir = os.path.join(base_dir, "Visualize_Exacte")
    os.makedirs(vis_mga_dir, exist_ok=True)
    os.makedirs(vis_exact_dir, exist_ok=True)

    # Run MGA and visualize
    if RUN_MGA:
        print("Lancement MGA ...")
        run_python(os.path.join(base_dir, "main.py"))
        mga_csv = latest_csv(os.path.join(base_dir, "results_mga"))
        print(f"Dernier CSV MGA: {mga_csv}")

        # Charger les coordonnées APRÈS génération potentielle du JSON
        coords = load_coords_from_json(instance_json)
        mga_routes = sanitize_routes(parse_routes_from_csv(mga_csv))
        mga_img = os.path.join(vis_mga_dir, f"Visualize_{instance_base}_{ts}.png")
        plot_routes(coords, mga_routes, f"Routes MGA - {instance_base}", mga_img)
        print(f"Image MGA enregistrée: {mga_img}")
    else:
        print("Visualize: section MGA désactivée (VISUALIZE_RUN_MGA=False).")

    # Run Exact method and visualize
    if RUN_EXACT:
        print("Lancement Méthode Exacte ...")
        run_python(os.path.join(base_dir, "Methode_exacte", "main_m_e.py"))
        exact_csv = latest_csv(os.path.join(base_dir, "results_exact"))
        print(f"Dernier CSV Exact: {exact_csv}")

        # Reload coords in case JSON was regenerated in the meantime
        coords = load_coords_from_json(instance_json)
        exact_routes = sanitize_routes(parse_routes_from_csv(exact_csv))
        exact_img = os.path.join(vis_exact_dir, f"Visualize_{instance_base}_{ts}.png")
        plot_routes(coords, exact_routes, f"Routes Méthode Exacte - {instance_base}", exact_img)
        print(f"Image Exact enregistrée: {exact_img}")
    else:
        print("Visualize: section Exacte désactivée (VISUALIZE_RUN_EXACT=False).")
