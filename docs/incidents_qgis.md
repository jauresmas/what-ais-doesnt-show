# Incidents : fermetures brutales de QGIS (23 octobre 2026)

QGIS s'est fermé deux fois pendant la construction du projet, alors qu'il était piloté à distance par l'extension QGIS MCP. Cette note garde la trace du diagnostic et des corrections, pour que l'incident ne se reproduise pas.

## Plantage n° 1 : objet C++ détruit avant usage

**Symptôme.** Fermeture immédiate pendant l'exécution de `scripts/07_projet_qgis.py` dans QGIS.

**Diagnostic.** Le script relancé hors interface avec le traceur de Python (`python-qgis-ltr.bat -X faulthandler`) s'arrête toujours à la même ligne :

```python
s.appendSymbolLayer(ligne(ORANGE, 0.55, tirets="1.6;1").symbolLayer(0).clone())
```

Le symbole renvoyé par `ligne(...)` est un objet temporaire : Python le détruit dès que `symbolLayer(0)` a rendu la main, et `clone()` s'exécute sur une couche de symbole dont le parent C++ n'existe plus.

**Correction.** Garder une référence au symbole source le temps du clone. Cause certaine : reproduite à la ligne près.

## Plantage n° 2 : corruption du tas pendant le rechargement du projet

**Symptôme.** Fermeture pendant la commande `load_project` de l'extension MCP. Journal d'événements Windows : `qgis-ltr-bin.exe`, module `ntdll.dll`, code `0xc0000374` (corruption du tas : mémoire libérée deux fois ou utilisée après libération). Pas de vidage mémoire, donc pas de pile d'appels.

**Ce qui a été constaté.**

- L'extension charge un projet en appelant directement `QgsProject.instance().read()` depuis une minuterie, et non par la procédure de QGIS (`iface.addProject`).
- À l'ouverture du projet, QGIS affichait une **fenêtre modale par couche** : « Sélectionner la transformation pour… ». Le poste est réglé pour demander la transformation quand plusieurs existent entre WGS84 et ETRS89-LAEA. Pendant que cette fenêtre attend, la minuterie de l'extension continue de tourner : elle peut exécuter d'autres commandes au milieu du chargement.
- Le GeoPackage avait été réécrit pendant que le projet était ouvert.

**Essais de reproduction.** Copie isolée du projet, second QGIS lancé avec `--code`, journal écrit à chaque étape et chien de garde sur les fenêtres modales.

| Essai | Conditions | Résultat |
|---|---|---|
| A | Rechargement par `QgsProject.read()` | Bloqué par la fenêtre de transformation |
| A2 | Idem, fenêtre validée automatiquement | Pas de plantage |
| D | Code exécuté pendant que la fenêtre bloque le chargement | Pas de plantage |
| C2 | Table du GeoPackage réécrite pendant que le projet est ouvert, puis rechargement | Pas de plantage |

Aucun facteur ne fait planter QGIS à lui seul. Le plantage tient à une combinaison de ces conditions, autour d'un chargement de projet hors procédure normale.

**Corrections.**

1. La transformation WGS84 → ETRS89-LAEA est fixée dans le projet (« Inverse of ETRS89 to WGS 84 (1) », précise au mètre). QGIS ne pose plus la question, aucune fenêtre modale ne bloque le chargement. Vérifié : ouverture et rechargement sans fenêtre (essai A rejoué).
2. Ne plus utiliser la commande `load_project` de l'extension : ouvrir un projet en lançant QGIS avec le fichier, ou par `iface.addProject()`.
3. Ne jamais réécrire ni compacter un GeoPackage ouvert dans QGIS : travailler sur une copie ou hors interface, puis rouvrir le projet.
4. Mettre au point tout script PyQGIS hors interface, avec le traceur, avant de l'exécuter dans le QGIS d'un utilisateur.

**Contrôle de l'outil « Produire une fiche de zone » dans un QGIS avec interface.** Fiche du Fehmarn Belt produite en 3 secondes, sans incident (essai T).
