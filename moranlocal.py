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

class MoranLocal(GeoAlgorithm):

    INPUT = 'INPUT'
    FIELD = 'FIELD'
    OUTPUT = 'OUTPUT'
    CONTIGUITY = 'CONTIGUITY'
    P_SIM = 'P_SIM'
    SIGNIFICANCE_LEVEL = 'SIGNIFICANCE_LEVEL'
    
    CONTIGUITY_OPTIONS = ["queen","rook"]
    SIGNIFICANCE_OPTIONS = ["90%","95%","99%"]

    def defineCharacteristics(self):
        self.name = "Local Moran's"
        self.group = 'Exploratory Spatial Data Analysis'

        self.addParameter(ParameterVector(self.INPUT,
            self.tr('Input layer'), [ParameterVector.VECTOR_TYPE_POLYGON]))
        self.addParameter(ParameterTableField(self.FIELD,
            self.tr('Field'), self.INPUT))
        self.addParameter(ParameterSelection(self.CONTIGUITY,
            self.tr('Contiguity'), self.CONTIGUITY_OPTIONS))
        self.addParameter(ParameterSelection(self.SIGNIFICANCE_LEVEL,
            self.tr('Significance level'), self.SIGNIFICANCE_OPTIONS))   

        self.addOutput(OutputVector(self.OUTPUT, self.tr('Local Moran\'s')))
        self.addOutput(OutputString(self.P_SIM, self.tr('p_sim')))

    def processAlgorithm(self, progress):
        field = self.getParameterValue(self.FIELD)
        field = field[0:10] # try to handle Shapefile field length limit
        filename = self.getParameterValue(self.INPUT)
        layer = dataobjects.getObjectFromUri(filename)
        filename = dataobjects.exportVectorLayer(layer)        
        provider = layer.dataProvider()
        fields = provider.fields()
        fields.append(QgsField('MORANS_P', QVariant.Double))
        fields.append(QgsField('MORANS_Z', QVariant.Double))
        fields.append(QgsField('MORANS_Q', QVariant.Int)) # quadrant
        fields.append(QgsField('MORANS_Q_S', QVariant.Int)) # significant quadrant
        fields.append(QgsField('MORANS_I', QVariant.Double))

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fields, provider.geometryType(), layer.crs() )

        contiguity = self.getParameterValue(self.CONTIGUITY)
        if self.CONTIGUITY_OPTIONS[contiguity] == 'queen':
            print 'INFO: Local Moran\'s using queen contiguity'
            w = pysal.queen_from_shapefile(filename)
        elif self.CONTIGUITY_OPTIONS[contiguity] == 'rook':
            print 'INFO: Local Moran\'s using rook contiguity'
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
        lm = pysal.Moran_Local(y, w, transformation = "r", permutations = 999)

        # http://pysal.readthedocs.org/en/latest/library/esda/moran.html?highlight=local%20moran#pysal.esda.moran.Moran_Local
        # values indicate quadrat location 1 HH,  2 LH,  3 LL,  4 HL

        # http://www.biomedware.com/files/documentation/spacestat/Statistics/LM/Results/Interpreting_univariate_Local_Moran_statistics.htm
        # category - scatter plot quadrant - autocorrelation - interpretation
        # high-high - upper right (red) - positive - Cluster - "I'm high and my neighbors are high."
        # high-low - lower right (pink) - negative - Outlier - "I'm a high outlier among low neighbors."
        # low-low - lower left (med. blue) - positive - Cluster - "I'm low and my neighbors are low."
        # low-high - upper left (light blue) - negative - Outlier - "I'm a low outlier among high neighbors."

        # http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/What_is_a_z_score_What_is_a_p_value/005p00000006000000/
        # z-score (Standard Deviations) | p-value (Probability) | Confidence level
        #     < -1.65 or > +1.65        |        < 0.10         |       90%
        #     < -1.96 or > +1.96        |        < 0.05         |       95%
        #     < -2.58 or > +2.58        |        < 0.01         |       99%

        self.setOutputValue(self.P_SIM, str(lm.p_sim))

        sig_q = lm.q * (lm.p_sim <= max_p) 
        outFeat = QgsFeature()
        i = 0
        for inFeat in processing.features(layer):
            inGeom = inFeat.geometry()
            outFeat.setGeometry(inGeom)
            attrs = inFeat.attributes()
            attrs.append(float(lm.p_sim[i]))
            attrs.append(float(lm.z_sim[i]))
            attrs.append(int(lm.q[i]))
            attrs.append(int(sig_q[i]))
            attrs.append(float(lm.Is[i]))
            outFeat.setAttributes(attrs)
            writer.addFeature(outFeat)
            i+=1

        del writer

    def help(self):
        path = os.path.dirname(os.path.abspath(__file__))
        helpUrl = os.path.join(path,"help","moranlocal.html")
        return False, helpUrl        
