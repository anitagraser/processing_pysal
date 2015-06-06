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

class Moran(GeoAlgorithm):

    INPUT = 'INPUT'
    FIELD = 'FIELD'
    CONTIGUITY = 'CONTIGUITY'
    I = 'I'
    
    CONTIGUITY_OPTIONS = ["queen","rook"]

    def defineCharacteristics(self):
        self.name = "Moran's"
        self.group = 'Exploratory Spatial Data Analysis'

        self.addParameter(ParameterVector(self.INPUT,
            self.tr('Input layer'), [ParameterVector.VECTOR_TYPE_POLYGON]))
        self.addParameter(ParameterTableField(self.FIELD,
            self.tr('Field'), self.INPUT))
        self.addParameter(ParameterSelection(self.CONTIGUITY,
            self.tr('Contiguity'), ["queen","rook"]))

        self.addOutput(OutputNumber(self.I, self.tr('i')))
        
    def processAlgorithm(self, progress):
        field = self.getParameterValue(self.FIELD)
        field = field[0:10] # try to handle Shapefile field length limit
        filename = self.getParameterValue(self.INPUT)
        layer = dataobjects.getObjectFromUri(filename)
        filename = dataobjects.exportVectorLayer(layer)        
        
        contiguity = self.getParameterValue(self.CONTIGUITY)
        if self.CONTIGUITY_OPTIONS[contiguity] == 'queen':
            print 'INFO: Moran\'s using queen contiguity'
            w=pysal.queen_from_shapefile(filename)
        elif self.CONTIGUITY_OPTIONS[contiguity] == 'rook':
            print 'INFO: Moran\'s using rook contiguity'
            w=pysal.rook_from_shapefile(filename)
    
        f = pysal.open(pysal.examples.get_path(filename.replace('.shp','.dbf')))
        y=np.array(f.by_col[str(field)])
        m = pysal.Moran(y,w,transformation = "r", permutations = 999)

        self.setOutputValue(self.I,m.I)
        
        print "Moran's I: %f" % (m.I)
        print "INFO: Moran's I values range from -1 (indicating perfect dispersion) to +1 (perfect correlation). Values close to -1/(n-1) indicate a random spatial pattern."
        print "p_norm: %f" % (m.p_norm)
        print "p_rand: %f" % (m.p_rand)
        print "p_sim: %f" % (m.p_sim)
        print "INFO: p values smaller than 0.05 indicate spatial autocorrelation that is significant at the 5% level."
        print "z_norm: %f" % (m.z_norm)
        print "z_rand: %f" % (m.z_rand)
        print "z_sim: %f" % (m.z_sim)
        print "INFO: z values greater than 1.96 or smaller than -1.96 indicate spatial autocorrelation that is significant at the 5% level."
