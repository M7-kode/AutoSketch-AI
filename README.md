# AutoSketch AI

Application de bureau (Tkinter) qui reproduit des images en pilotant la souris dans un logiciel de dessin : vision par ordinateur pour extraire les contours et les couleurs, optimisation de trajectoires (glouton + 2-opt), et un mode d'apprentissage de style de trait.

## Fonctionnalites

- **Formes de base** : ligne, rectangle, cercle, ellipse, polyligne libre.
- **Import d'image** et **detection de contours** (OpenCV).
- **Reproduction d'image** en noir et blanc, en couleur (segmentation par palette de couleurs), ou par matrice de pixels.
- **Optimisation de trajectoire** pour minimiser la distance parcourue par la souris (algorithme glouton puis raffinement 2-opt).
- **Fusion des cellules adjacentes** (matrice de pixels) en un minimum de traits, en choisissant le sens de balayage (lignes ou colonnes) le plus efficace.
- **Palettes de couleurs sauvegardables** : calibre une fois la position et la couleur de chaque swatch, puis enregistre/recharge cette palette (Fichier > Charger/Enregistrer une palette) pour ne plus jamais la recalibrer.
- **Quantification sur la palette reelle** (avec dithering optionnel) quand une palette est chargee ou calibree, pour que chaque couleur reproduite corresponde exactement a un swatch disponible.
- **Interruption immediate** d'un dessin en cours avec la touche ECHAP.
- **Mode d'apprentissage** : enregistre ton propre style de trait (vitesse, pauses) et l'applique a la reproduction.

## Prerequis

- Python 3.10+
- Windows (utilise `pyautogui` / `pynput` pour piloter la souris)

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

```bash
python main.py
```

Ouvre ton logiciel de dessin avant de lancer une action, puis suis les instructions affichees dans l'interface (calibration de la zone de dessin, clics de reference, etc.).

## Structure du projet

```
ai_engine/        apprentissage de style, optimisation de trajectoire (2-opt)
automation/       pilotage bas niveau de la souris
core/             calibration des coordonnees ecran <-> image
drawing_engine/   construction et optimisation des chemins a tracer
interface/        interface graphique (Tkinter)
plugins/          calibration et selection de palette de couleurs
vision/           chargement d'image, segmentation couleur, detection de contours
```

## Avertissement

Cet outil automatise des clics et deplacements de souris. Utilise-le de maniere responsable et conformement aux conditions d'utilisation des logiciels avec lesquels tu l'utilises.
