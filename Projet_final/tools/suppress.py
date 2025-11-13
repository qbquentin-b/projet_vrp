import os
import sys
import argparse
import glob


# Base directory is the project root (parent of this tools folder)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _clear_dir(dir_path: str, patterns: list[str], dry_run: bool = False) -> int:
    """Delete files in dir_path matching any of the patterns. Returns count deleted."""
    if not os.path.isdir(dir_path):
        print(f"[info] Dossier introuvable: {dir_path}")
        return 0

    to_delete = []
    for pat in patterns:
        to_delete.extend(glob.glob(os.path.join(dir_path, pat)))

    deleted = 0
    for path in to_delete:
        if os.path.isfile(path):
            if dry_run:
                print(f"[dry-run] supprimer: {path}")
            else:
                try:
                    os.remove(path)
                    deleted += 1
                except Exception as e:
                    print(f"[warn] échec suppression {path}: {e}")
    return deleted


def clear_results_mga(dry_run: bool = False) -> int:
    """Supprime les fichiers CSV dans results_mga."""
    target = os.path.join(BASE_DIR, 'results_mga')
    return _clear_dir(target, ['*.csv'], dry_run=dry_run)


def clear_results_exact(dry_run: bool = False) -> int:
    """Supprime les fichiers CSV dans results_exact."""
    target = os.path.join(BASE_DIR, 'results_exact')
    return _clear_dir(target, ['*.csv'], dry_run=dry_run)


def clear_visualize_mga(dry_run: bool = False) -> int:
    """Supprime les images PNG dans Visualize_MGA."""
    target = os.path.join(BASE_DIR, 'Visualize_MGA')
    return _clear_dir(target, ['*.png'], dry_run=dry_run)


def clear_visualize_exact(dry_run: bool = False) -> int:
    """Supprime les images PNG dans Visualize_Exacte."""
    target = os.path.join(BASE_DIR, 'Visualize_Exacte')
    return _clear_dir(target, ['*.png'], dry_run=dry_run)


CHOICES = {
    'mga': clear_results_mga,
    'exact': clear_results_exact,
    'vis_mga': clear_visualize_mga,
    'vis_exact': clear_visualize_exact,
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Supprime les fichiers de résultats et visualisations.")
    parser.add_argument('what', nargs='+', choices=list(CHOICES.keys()) + ['all'],
                        help="Quels fichiers supprimer: mga, exact, vis_mga, vis_exact, all")
    parser.add_argument('--dry-run', action='store_true', help="N'affiche que ce qui serait supprimé")

    args = parser.parse_args(argv)

    tasks = list(CHOICES.keys()) if 'all' in args.what else args.what

    total = 0
    for key in tasks:
        func = CHOICES[key]
        count = func(dry_run=args.dry_run)
        print(f"[ok] {key}: {count} fichier(s) supprimé(s)")
        total += count

    print(f"Total supprimé: {total}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

