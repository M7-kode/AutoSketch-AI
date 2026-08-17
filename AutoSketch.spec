# Recette de construction PyInstaller. Utilise build.py plutot que de l'appeler
# directement : c'est lui qui positionne AUTOSKETCH_DOSSIER selon le mode voulu.
import os

as_folder = os.environ.get("AUTOSKETCH_DOSSIER") == "1"

# OpenCV embarque les codecs video ffmpeg (~29 Mo). L'application ne lit que des
# images fixes : les retirer allege d'autant, et raccourcit d'autant le
# demarrage du mode fichier unique, qui doit tout redecompresser a chaque fois.
USELESS_BINARIES = ("opencv_videoio_ffmpeg",)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "_pytest", "pluggy", "PyInstaller"],
    noarchive=False,
)

a.binaries = [entry for entry in a.binaries
              if not any(useless in entry[0] for useless in USELESS_BINARIES)]

pyz = PYZ(a.pure)

if as_folder:
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name="AutoSketch",
        console=False,
        icon="assets/icon.ico",
    )
    coll = COLLECT(exe, a.binaries, a.datas, name="AutoSketch")
else:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.datas, [],
        name="AutoSketch",
        upx=True,
        console=False,
        icon="assets/icon.ico",
    )
