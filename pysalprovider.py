from processing.core.AlgorithmProvider import AlgorithmProvider
from localmoran import LocalMoran
from moran import Moran

class pysalProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = False

        self.alglist = [LocalMoran(),Moran()]
        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    def getName(self):
        return 'pysal'

    def getDescription(self):
        return 'PySAL'

    def _loadAlgorithms(self):
        self.algs = self.alglist
