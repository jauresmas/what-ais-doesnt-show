"""Graphique « d'où viennent les silences » des fiches de zone.

Partagé par 06_export_gpkg.py (zones prédéfinies) et l'outil QGIS qgis/outils/fiche_zone.py
(zone quelconque) : les deux produisent exactement le même graphique.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# libellés anglais des catégories de silence, dans l'ordre du classement
CATEGORIES = {
    "position incohérente": "Inconsistent position",
    "navire de servitude ou d'État": "Service or state vessel",
    "sortie de la zone": "Left the study area",
    "navigation intérieure ou portuaire": "Inland waterway or harbour",
    "arrêt au port ou au mouillage": "Stopped in port or at anchor",
    "réception insuffisante probable": "Shore reception gap",
    "escale ou détour côtier possible": "Possible port call or coastal detour",
    "sortie de couverture possible": "Possible trip out of coverage",
    "coupure inexpliquée": "Unexplained",
}

ORANGE = "#eb6834"   # silences inexpliqués, comme sur la carte
GRIS = "#9aa7b1"


def graphique(chemin, comptes):
    """Barres horizontales des silences par explication ; l'inexpliqué en orange.

    chemin : fichier SVG à écrire ; comptes : {catégorie : nombre}.
    """
    libelles = list(CATEGORIES.values())
    valeurs = [int(comptes.get(c, 0)) for c in CATEGORIES]
    fig, ax = plt.subplots(figsize=(3.6, 2.35), dpi=150)
    couleurs = [ORANGE if c == "coupure inexpliquée" else GRIS for c in CATEGORIES]
    y = list(range(len(libelles)))[::-1]
    ax.barh(y, valeurs, height=0.68, color=couleurs, edgecolor="white", linewidth=0.8)
    vmax = max(max(valeurs), 1)
    for yi, v, c in zip(y, valeurs, CATEGORIES):
        gras = "bold" if c == "coupure inexpliquée" else "normal"
        ax.text(v + vmax * 0.015, yi, f"{v:,}", va="center", ha="left", fontsize=6.4,
                color="#1d1d1b", fontweight=gras)
    ax.set_yticks(y)
    ax.set_yticklabels(libelles, fontsize=6.4, color="#3d3d3a")
    ax.set_xlim(0, vmax * 1.18)
    ax.xaxis.set_visible(False)
    for cote in ("top", "right", "bottom"):
        ax.spines[cote].set_visible(False)
    ax.spines["left"].set_color("#c9c6bf")
    ax.tick_params(axis="y", length=0, pad=3)
    fig.tight_layout(pad=0.2)
    fig.savefig(chemin, transparent=True)
    plt.close(fig)
