# AutoSketch AI

**Dessine une image trouvee sur internet dans Skribbl.io, Gartic Phone ou Paint, en pilotant ta souris.**

Colle une adresse d'image, choisis le site, clique sur **DESSINER**. Le programme analyse l'image, choisit les couleurs dans la palette du site et trace le dessin a ta place.

La calibration se fait chez toi, en une fois : elle s'adapte a ta resolution, ton zoom et la position de ta fenetre. Aucune position d'ecran n'est codee en dur.

---

## Demarrer

### Tu veux juste dessiner

Recupere **AutoSketch** (voir [Construire l'executable](#construire-lexecutable) si tu pars des sources), puis lance `AutoSketch.exe`. Ni Python ni installation ne sont necessaires.

> Le tout premier lancement prend une vingtaine de secondes : Windows analyse l'application. Les suivants demarrent en 1 a 2 secondes.

### Tu veux lire ou modifier le code

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Prerequis : Python 3.10+ sur Windows (`pyautogui` et `pynput` pilotent la souris).

---

## Comment dessiner

L'interface tient en trois etapes et un bouton.

**1 - Quelle image ?**
Colle l'adresse d'une image trouvee sur internet, ou choisis un fichier.

**2 - Ou dessiner ?**
Choisis le site, puis clique sur **Calibrer**, une seule fois :

- clique le coin haut-gauche, puis le coin bas-droite de la zone de dessin,
- clique chaque couleur de la palette du site, puis appuie sur **ENTREE**.

C'est enregistre : tu n'auras plus jamais a le refaire pour ce site.

**3 - Comment dessiner ?**
Choisis un rendu, regle la vitesse et le detail.

Puis clique sur **DESSINER**.

> **ECHAP arrete tout, a n'importe quel moment.** Le bouton de la souris est toujours relache, meme si tu interromps le dessin ou qu'une erreur survient.

### Les trois rendus

| Rendu | Ce qu'il fait | Quand l'utiliser |
| --- | --- | --- |
| **Couleur** | Un groupe de contours par couleur de la palette | Le meilleur compromis par defaut |
| **Contours** | Trace les contours sans changer de couleur | Rapide, style croquis |
| **Pixels** | Remplit une grille de cellules, en fusionnant les voisines de meme couleur | Aplats et images simples |

---

## Ce qui rend le trace rapide

- **Fusion des cellules voisines** — en mode Pixels, les cellules adjacentes de meme couleur deviennent un seul trait. Le sens de balayage (lignes ou colonnes) est choisi automatiquement, celui qui produit le moins de traits.
- **Optimisation du parcours** — l'ordre des traits est optimise en deux temps (plus proche voisin, puis raffinement 2-opt) pour reduire la distance parcourue a vide par la souris.
- **Quantification sur ta palette reelle** — chaque couleur dessinee correspond exactement a une couleur cliquable du site, avec dithering optionnel pour les degrades.
- **Le bouton n'est jamais laisse enfonce** — garanti par un `finally`, et verifie par un test dedie : c'est le pire incident possible pour cette application.

---

## Developper

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

109 tests, sans souris ni fenetre. C'est possible grace au decoupage central du projet :

- **`drawing/plan.py`** construit *quoi* tracer, dans le repere de l'image, **sans jamais toucher la souris** ;
- **`executor.py`** applique ce plan a l'ecran, avec une souris **injectee**.

Les tests passent donc une fausse souris qui enregistre les appels au lieu de bouger le curseur.

### Structure

Un seul package, decoupe selon les trois roles du programme : **lire l'image**, **decider quoi tracer**, **agir sur l'ecran**.

```
main.py                point d'entree
build.py               construit l'executable
autosketch/
  app.py               interface graphique (Tkinter)
  executor.py          applique un plan a l'ecran
  settings.py          curseur "Detail" -> reglages du moteur
  vision/              lire l'image
    loader.py            chargement (fichier ou URL)
    colors.py            quantification et masques de couleur
    contours.py          detection des contours
    grid.py              reduction en grille de cellules
  drawing/             decider quoi tracer
    plan.py              construit le plan
    paths.py             contours -> traces simplifies et lisses
    routing.py           ordre de passage (plus proche voisin + 2-opt)
    runs.py              fusion des cellules voisines de meme couleur
    strokes.py           trace bas niveau et remplissage en zigzag
  screen/              agir sur l'ecran
    mouse.py             pilotage de la souris
    calibration.py       capture de clics, image -> zone d'ecran
    palette.py           couleurs cliquables du site
    presets.py           calibrations enregistrees par site
assets/                icone de l'application
samples/               images d'exemple
tests/                 suite de tests
```

### Ou sont enregistrees les calibrations

| Contexte | Emplacement |
| --- | --- |
| Depuis les sources | `presets/` a la racine du projet |
| Depuis l'executable | `%APPDATA%\AutoSketch\presets\` |

L'executable ne peut pas ecrire a cote de lui-meme : PyInstaller le decompresse dans un dossier temporaire efface a la fermeture, ce qui ferait perdre la calibration a chaque redemarrage.

### Construire l'executable

```bash
pip install -r requirements-dev.txt
python build.py                # -> dist/AutoSketch/     (recommande)
python build.py --un-fichier   # -> dist/AutoSketch.exe
```

| Mode | Resultat | 1er lancement | Lancements suivants |
| --- | --- | --- | --- |
| **Dossier** (defaut) | un dossier de 178 Mo, a zipper pour le partager | ~18 s | **~1 s** |
| **Fichier unique** | un seul `.exe` de 71 Mo | ~20 s | ~20 s |

Le fichier unique est plus simple a envoyer, mais il redecompresse OpenCV et numpy **a chaque lancement**. Le mode dossier ne paie l'attente qu'une fois, a la premiere ouverture.

L'icone est generee par `python assets/make_icon.py`.

---

## Avertissement

Cet outil automatise des clics et deplacements de souris. Utilise-le de maniere responsable et conformement aux conditions d'utilisation des sites et logiciels concernes.
