from qgis.core import QgsApplication, QgsProcessingProvider

from .fiche_zone import FicheZone


class Fournisseur(QgsProcessingProvider):
    """Fournisseur de traitements « What AIS doesn't show » : un seul algorithme, la fiche de zone."""

    def id(self):
        return "whataisdoesntshow"

    def name(self):
        return "What AIS doesn't show"

    def longName(self):
        return self.name()

    def loadAlgorithms(self):
        self.addAlgorithm(FicheZone())


class Extension:
    def __init__(self, iface):
        self.iface = iface
        self.fournisseur = None

    def initProcessing(self):
        if self.fournisseur is None:
            self.fournisseur = Fournisseur()
            QgsApplication.processingRegistry().addProvider(self.fournisseur)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        if self.fournisseur is not None:
            QgsApplication.processingRegistry().removeProvider(self.fournisseur)
            self.fournisseur = None
