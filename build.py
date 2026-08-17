"""Construit AutoSketch pour Windows : ni Python ni dependances chez celui qui le recoit.

    pip install -r requirements-dev.txt
    python build.py            -> dist/AutoSketch.exe  un seul fichier, deplacable partout
    python build.py --dossier  -> dist/AutoSketch/     demarre plus vite, a garder groupe

Le fichier unique est le defaut parce qu'il fonctionne seul. En mode dossier,
l'exe ne demarre pas sans le dossier _internal qui l'accompagne : il faut
partager le dossier entier, jamais l'exe tout seul.
"""

import os
import subprocess
import sys

NAME = "AutoSketch"
ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(ROOT, f"{NAME}.spec")


def folder_size_mb(path):
    total = 0
    for directory, _, files in os.walk(path):
        for name in files:
            total += os.path.getsize(os.path.join(directory, name))
    return total / (1024 * 1024)


def main():
    as_folder = "--dossier" in sys.argv

    environment = dict(os.environ, AUTOSKETCH_DOSSIER="1" if as_folder else "0")
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", SPEC]

    print(" ".join(command))
    subprocess.run(command, check=True, cwd=ROOT, env=environment)

    if as_folder:
        result = os.path.join(ROOT, "dist", NAME)
        size = folder_size_mb(result)
        print(f"\nA partager : zippe le dossier dist/{NAME}/ EN ENTIER.")
        print("L'exe seul ne demarre pas : il lui faut _internal a cote de lui.")
    else:
        result = os.path.join(ROOT, "dist", f"{NAME}.exe")
        size = os.path.getsize(result) / (1024 * 1024)
        print(f"\nA partager : le fichier dist/{NAME}.exe, tel quel.")

    print(f"\nOK : {result} ({size:.0f} Mo)")


if __name__ == "__main__":
    main()
