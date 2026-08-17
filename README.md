# AutoSketch AI

Application de bureau qui dessine une image trouvee sur internet dans **Skribbl.io**, **Gartic Phone** ou **Paint**, en pilotant ta souris.

Contrairement aux bots qui codent en dur des positions d'ecran, la calibration se fait chez toi : elle s'adapte donc a ta resolution, ton zoom et la position de ta fenetre. Tu ne la fais qu'une fois par site.

## Comment ca marche

L'interface tient en trois etapes et un bouton.

1. **Quelle image ?** Colle l'adresse d'une image trouvee sur internet (ou choisis un fichier).
2. **Ou dessiner ?** Choisis le site, puis clique sur **Calibrer** une seule fois :
   - clique le coin haut-gauche puis le coin bas-droite de la zone de dessin,
   - clique chaque couleur de la palette du site, puis appuie sur **ENTREE**.

   C'est enregistre : tu n'auras plus jamais a le refaire pour ce site.
3. **Comment dessiner ?** Choisis un rendu, regle la vitesse et le detail.

Puis clique sur **DESSINER**. **ECHAP arrete tout a n'importe quel moment.**

### Les trois rendus

| Rendu | Ce qu'il fait | Quand l'utiliser |
| --- | --- | --- |
| **Couleur** | Un groupe de contours par couleur de la palette | Le meilleur compromis par defaut |
| **Contours** | Trace uniquement les contours, sans changer de couleur | Rapide, style croquis |
| **Pixels** | Remplit une grille de cellules, en fusionnant les cellules voisines de meme couleur | Aplats et images simples |

## Ce qui rend le trace efficace

- **Fusion des cellules voisines** : en mode Pixels, les cellules adjacentes de meme couleur deviennent un seul trait, et le sens de balayage (lignes ou colonnes) est choisi automatiquement pour minimiser le nombre de traits.
- **Optimisation du parcours** : l'ordre des traits est optimise (glouton puis raffinement 2-opt) pour reduire la distance parcourue a vide par la souris.
- **Quantification sur ta palette reelle** : chaque couleur dessinee correspond exactement a une couleur cliquable du site, avec dithering optionnel.
- **Le bouton n'est jamais laisse enfonce**, meme en cas d'interruption ou d'erreur.

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Prerequis : Python 3.10+ sur Windows (`pyautogui` / `pynput` pilotent la souris).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

La logique de dessin est separee de l'interface : un **plan** (quoi tracer, dans le repere de l'image) se construit sans jamais toucher la souris, et un **executeur** l'applique a l'ecran. C'est ce qui rend l'essentiel du projet testable sans bouger le curseur ni ouvrir de fenetre.

## Structure

```
core/       plan (quoi tracer), executor (l'appliquer), calibration, settings
vision/     chargement d'image (fichier/URL), couleurs, contours, grille
drawing_engine/  traces, fusion des cellules, optimisation du parcours
ai_engine/  raffinement 2-opt du parcours
plugins/    palette de couleurs, calibrations par site
interface/  interface graphique (Tkinter)
tests/      suite de tests
```

Les calibrations sont enregistrees dans `presets/`, propre a ta machine et non versionne.

## Avertissement

Cet outil automatise des clics et deplacements de souris. Utilise-le de maniere responsable et conformement aux conditions d'utilisation des sites et logiciels concernes.
