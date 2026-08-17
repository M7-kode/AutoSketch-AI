"""Construit AutoSketch pour Windows : ni Python ni dependances chez celui qui le recoit.

    pip install -r requirements-dev.txt
    python build.py              -> dist/AutoSketch/  (demarre vite, un dossier a zipper)
    python build.py --un-fichier -> dist/AutoSketch.exe (un seul fichier, demarrage lent)

Le mode dossier est le defaut : le mode fichier unique doit redecompresser
OpenCV et numpy a chaque lancement, ce qui coute une vingtaine de secondes
d'attente avant que la fenetre apparaisse.
"""

import os
import subprocess
import sys

NAME = "AutoSketch"
ROOT = os.path.dirname(os.path.abspath(__file__))

# Ces paquets ne servent qu'au developpement : les exclure evite de les
# embarquer dans le resultat.
EXCLUDED = ["pytest", "_pytest", "pluggy", "PyInstaller"]


def folder_size_mb(path):
    total = 0
    for directory, _, files in os.walk(path):
        for name in files:
            total += os.path.getsize(os.path.join(directory, name))
    return total / (1024 * 1024)


def main():
    single_file = "--un-fichier" in sys.argv

    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onefile" if single_file else "--onedir",
        "--windowed",
        "--name", NAME,
        "--icon", os.path.join("assets", "icon.ico"),
    ]
    for module in EXCLUDED:
        command += ["--exclude-module", module]
    command.append("main.py")

    print(" ".join(command))
    subprocess.run(command, check=True, cwd=ROOT)

    if single_file:
        result = os.path.join(ROOT, "dist", f"{NAME}.exe")
        size = os.path.getsize(result) / (1024 * 1024)
    else:
        result = os.path.join(ROOT, "dist", NAME)
        size = folder_size_mb(result)
        print(f"\nA partager : zippe le dossier dist/{NAME}/ en entier.")

    print(f"\nOK : {result} ({size:.0f} Mo)")


if __name__ == "__main__":
    main()
