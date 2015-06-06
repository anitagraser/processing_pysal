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

class GLocal(GeoAlgorithm):

    INPUT = 'INPUT'
    FIELD = 'FIELD'
    OUTPUT = 'OUTPUT'
    CONTIGUITY = 'CONTIGUITY'
    P_SIM = 'P_SIM'
    SIGNIFICANCE_LEVEL = 'SIGNIFICANCE_LEVEL'
    
    CONTIGUITY_OPTIONS = ["queen","rook"]
    SIGNIFICANCE_OPTIONS = ["90%","95%","99%"]

    def defineCharacteristics(self):
        self.name = "Local G and G*"
        self.group = 'Exploratory Spatial Data Analysis'

        self.addParameter(ParameterVector(self.INPUT,
            self.tr('Input layer'), [ParameterVector.VECTOR_TYPE_POLYGON]))
        self.addParameter(ParameterTableField(self.FIELD,
            self.tr('Field'), self.INPUT))
        self.addParameter(ParameterSelection(self.CONTIGUITY,
            self.tr('Contiguity'), self.CONTIGUITY_OPTIONS))
        self.addParameter(ParameterSelection(self.SIGNIFICANCE_LEVEL,
            self.tr('Significance level'), self.SIGNIFICANCE_OPTIONS))   

        self.addOutput(OutputVector(self.OUTPUT, self.tr('Local G and G*')))
        self.addOutput(OutputString(self.P_SIM, self.tr('p_sim')))

    def processAlgorithm(self, progress):
        field = self.getParameterValue(self.FIELD)
        field = field[0:10] # try to handle Shapefile field length limit
        filename = self.getParameterValue(self.INPUT)
        layer = dataobjects.getObjectFromUri(filename)
        filename = dataobjects.exportVectorLayer(layer)        
        provider = layer.dataProvider()
        fields = provider.fields()
        fields.append(QgsField('L_G', QVariant.Double))
        fields.append(QgsField('L_G_p', QVariant.Double))
        fields.append(QgsField('L_G_S', QVariant.Int))
        fields.append(QgsField('L_G_ll_hh', QVariant.Int))

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fields, provider.geometryType(), layer.crs() )

        contiguity = self.getParameterValue(self.CONTIGUITY)
        if self.CONTIGUITY_OPTIONS[contiguity] == 'queen':
            print 'INFO: Local G and G* using queen contiguity'
            w = pysal.queen_from_shapefile(filename)
        elif self.CONTIGUITY_OPTIONS[contiguity] == 'rook':
            print 'INFO: Local G and G* using rook contiguity'
            w = pysal.rook_from_shapefile(filename)

        significance_level = self.getParameterValue(self.SIGNIFICANCE_LEVEL)
        if self.SIGNIFICANCE_OPTIONS[significance_level] == '90%':
            max_p = 0.10
        elif self.SIGNIFICANCE_OPTIONS[significance_level] == '95%':
            max_p = 0.05
        elif self.SIGNIFICANCE_OPTIONS[significance_level] == '99%':
            max_p = 0.01    
        print 'INFO: significance level ' + self.SIGNIFICANCE_OPTIONS[significance_level]

        f = pysal.open(pysal.examples.get_path(filename.replace('.shp','.dbf')))
        y = np.array(f.by_col[str(field)])
        lg = pysal.G_Local(y,w,transform = "b", permutations = 999) 

        sig_g =  1.0 * lg.p_sim <= max_p
        ll_hh = 1.0 * (lg.Gs > lg.EGs) + 1
        sig_ll_hh = sig_g * ll_hh
        outFeat = QgsFeature()
        i = 0
        for inFeat in processing.features(layer):
            inGeom = inFeat.geometry()
            outFeat.setGeometry(inGeom)
            attrs = inFeat.attributes()
            attrs.append(float(lg.Gs[i]))
            attrs.append(float(lg.p_sim[i]))
            attrs.append(int(sig_g[i]))
            attrs.append(int(sig_ll_hh[i]))
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)
            i+=1

        del writer
