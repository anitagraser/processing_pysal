import os
import sys
import inspect
from processing.core.Processing import Processing
from pysalprovider import pysalProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class pysalProviderPlugin:

    def __init__(self):
        self.provider = pysalProvider()

    def initGui(self):
        Processing.addProvider(self.provider)

    def unload(self):
        Processing.removeProvider(self.provider)

    def getSupportedOutputVectorLayerExtensions(self):
        return ['shp']
