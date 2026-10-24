"""Extension QGIS « What AIS doesn't show – Zone sheet » : l'outil de fiche de zone dans la boîte à outils
de traitement, sans copier de script à la main. Le code de l'outil est celui de qgis/outils/fiche_zone.py,
copié dans l'extension par scripts/empaqueter_extension.py."""


def classFactory(iface):
    from .extension import Extension
    return Extension(iface)
