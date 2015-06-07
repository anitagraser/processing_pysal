import pysal 
import numpy as np
import processing 
from processing.tools.vector import VectorWriter
from qgis.core import *
from PyQt4.QtCore import *
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import *
from processing.core.outputs import *
from processing.tools import dataobjects

class G(GeoAlgorithm):

    INPUT = 'INPUT'
    FIELD = 'FIELD'
    CONTIGUITY = 'CONTIGUITY'
    G = 'G'
    
    CONTIGUITY_OPTIONS = ["queen","rook"]

    def defineCharacteristics(self):
        self.name = "Getis and Ord's G"
        self.group = 'Exploratory Spatial Data Analysis'

        self.addParameter(ParameterVector(self.INPUT,
            self.tr('Input layer'), [ParameterVector.VECTOR_TYPE_POLYGON]))
        self.addParameter(ParameterTableField(self.FIELD,
            self.tr('Field'), self.INPUT))
        self.addParameter(ParameterSelection(self.CONTIGUITY,
            self.tr('Contiguity'), ["queen","rook"]))

        self.addOutput(OutputNumber(self.G, self.tr('g')))
        
    def processAlgorithm(self, progress):
        field = self.getParameterValue(self.FIELD)
        field = field[0:10] # try to handle Shapefile field length limit
        filename = self.getParameterValue(self.INPUT)
        layer = dataobjects.getObjectFromUri(filename)
        filename = dataobjects.exportVectorLayer(layer)        
        
        contiguity = self.getParameterValue(self.CONTIGUITY)
        if self.CONTIGUITY_OPTIONS[contiguity] == 'queen':
            print 'INFO: Getis and Ord\'s G using queen contiguity'
            w = pysal.queen_from_shapefile(filename)
        elif self.CONTIGUITY_OPTIONS[contiguity] == 'rook':
            print 'INFO: Getis and Ord\'s G using rook contiguity'
            w = pysal.rook_from_shapefile(filename)
    
        f = pysal.open(pysal.examples.get_path(filename.replace('.shp','.dbf')))
        y = np.array(f.by_col[str(field)])
        g = pysal.G(y, w, permutations = 999)

        self.setOutputValue(self.G,g.G)
        
        print "Getis and Ord's G: %f" % (g.G)
        print "expected value: %f" % (g.EG)
        print "p_norm: %f" % (g.p_norm)
        print "p_sim: %f" % (g.p_sim)
        print "INFO: p values smaller than 0.05 indicate spatial autocorrelation that is significant at the 5% level."
        print "z_norm: %f" % (g.z_norm)
        print "z_sim: %f" % (g.z_sim)
        print "INFO: z values greater than 1.96 or smaller than -1.96 indicate spatial autocorrelation that is significant at the 5% level."

    def help(self):
        path = os.path.dirname(os.path.abspath(__file__))
        helpUrl = os.path.join(path,"help","getisordg.html")
        return False, helpUrl        
