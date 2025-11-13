# Projet/tools/fetch_solomon.py
import os
import sys
import argparse

def save_text(path, content: str, overwrite=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"{path} existe déjà (utilise --overwrite pour remplacer).")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def fetch_with_vrplib(instance_code: str) -> str:
    """
    Essaie d'obtenir le contenu texte via vrplib si l'API le permet.
    Selon les versions, vrplib n’expose pas de downloader public.
    On renvoie le contenu texte si possible, sinon lève.
    """
    try:
        import vrplib
    except ImportError as e:
        raise RuntimeError("vrplib non installé (pip install vrplib)") from e

    # Certaines versions n’ont pas de fonction de download publique.
    # On essaie d’ouvrir un chemin local standard si vrplib le propose.
    # Fallback: on signale à l’utilisateur d’utiliser --url.
    #
    # Si ta version expose un reader pour fichier local, ce script ne peut
    # pas “télécharger” sans URL; on renvoie une erreur claire.
    raise RuntimeError(
        "Cette version de vrplib ne fournit pas de downloader public. "
        "Fournis --url vers une source (miroir Solomon) ou dépose R101.txt dans Projet/data."
    )

def fetch_with_url(url: str) -> str:
    import requests
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("instance", help="Code instance (ex: R101, C101)")
    parser.add_argument("--url", help="URL directe du .txt Solomon (si pas de downloader vrplib)")
    parser.add_argument("--overwrite", action="store_true", help="Écrase si le fichier existe")
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dest_txt = os.path.join(base_dir, "data", f"{args.instance}.txt")

    # 1) Si déjà présent et pas overwrite: on stoppe
    if os.path.exists(dest_txt) and not args.overwrite:
        print(f"Déjà présent: {dest_txt}")
        sys.exit(0)

    # 2) Essayer via vrplib, sinon via URL
    content = None
    if not args.url:
        try:
            content = fetch_with_vrplib(args.instance)
        except Exception as e:
            print(f"VRPLIB fetch indisponible: {e}")
            print("Astuce: passe --url <lien direct vers .txt> ou dépose le fichier manuellement.")
            sys.exit(2)
    else:
        content = fetch_with_url(args.url)

    save_text(dest_txt, content, overwrite=args.overwrite)
    print(f"Écrit: {dest_txt}")

if __name__ == "__main__":
    main()
