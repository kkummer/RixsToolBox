#!/usr/bin/env python
#-*- coding: utf-8 -*-

#/*##########################################################################
# Copyright (C) 2016 K. Kummer, A. Tamborino, European Synchrotron Radiation 
# Facility
#
# This file is part of the ID32 RIXSToolBox developed at the ESRF by the ID32
# staff and the ESRF Software group.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################*/

from __future__ import division

__author__ = "K. Kummer - ESRF ID32"
__contact__ = "kurt.kummer@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
___doc__ = """
    ...
"""

import os

import numpy as np

from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGraph import Colors as pymcaColors
from PyMca5.PyMcaGui.plotting import PlotWindow
from PyMca5.PyMcaGui.pymca.ScanWindowInfoWidget import SpecArithmetic

from RixsSpectrum import RixsSpectrum
import SpecGenGUI
from RTB_Icons import RtbIcons

from datetime import datetime
from scipy import interpolate, ndimage, optimize



class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('RixsToolBox Slope Finder')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        
        self.spcPlot = PlotWindow.PlotWindow(parent=self, 
            backend=None, plugins=False, newplot=False, roi=False, 
            control=False, position=True, info=False, logx = False, 
            logy = False, togglePoints = False)
        
        self.tradSpectraPlot = PlotWindow.PlotWindow(
            parent=self,
            backend=None,
            plugins=True, # Hide plugin tool button
            newplot=True, # Hide mirror active curve, ... functionality
            roi=False,     # No ROI widget
            control=True, # Hide option button
            position=True, # Show x,y position display
            info=False,
            kw={'logx': False, # Hide logarithmic x-scale tool button
                'logy': False, # Hide logarithmic y-scale tool button
                'flip': False, # Hide whatever this does
                'fit': True, # Hide simple fit tool button
                'energy': False}) # Hide simple fit tool button
        
        
        self.tradResultsPlot = PlotWindow.PlotWindow(parent=self, 
            backend=None, plugins=False, newplot=False, roi=False, 
            control=False, position=True, info=False, logx = False, 
            logy = False, togglePoints = False)
        
        

        self._sourcefilesWidget = SpecGenGUI.SourceFilesWidget(self)
        self._extractbuttonWidget= ExtractButtonWidget(self)
        self._tableWidget= Table(self)
        
        
        self._LabelSlope = qt.QLabel("Slope Guess:")   
        self._LabelStep = qt.QLabel("Step") 
        self._LabelNum = qt.QLabel("N. of spectra") 
        self._Title= qt.QLabel("Slope:")
        self._Result=qt.QLabel("Results:")
        self._SlopeSPC=qt.QLabel("Slope SPC: ")
        
        
        self._GuessSlope = qt.QDoubleSpinBox()
        self._GuessSlope.setMaximumWidth(100)
        self._GuessSlope.setMinimumWidth(70)
        self._GuessSlope.setAlignment(qt.Qt.AlignRight)
        self._GuessSlope.setDecimals(4)
        self._GuessSlope.setMinimum(-1)
        self._GuessSlope.setMaximum(1)
        self._GuessSlope.setSingleStep(.0005)
        self._GuessSlope.setValue(-0.0065)
        
        
        self._Step = qt.QDoubleSpinBox()
        self._Step.setMaximumWidth(100)
        self._Step.setMinimumWidth(70)
        self._Step.setAlignment(qt.Qt.AlignRight)
        self._Step.setDecimals(4)
        self._Step.setSingleStep(.0005)
        self._Step.setValue(0.0005)
        

        
        self._Num = qt.QDoubleSpinBox()
        self._Num.setMaximumWidth(100)
        self._Num.setMinimumWidth(70)
        self._Num.setAlignment(qt.Qt.AlignRight)
        self._Num.setDecimals(0)
        self._Num.setSingleStep(1)
        self._Num.setValue(11)
        

        self.connect(self._extractbuttonWidget, 
            qt.SIGNAL('ExtractButtonClicked'), self.Extract)
            

        self._inputLayout = qt.QHBoxLayout(self)
        self._inputLayout.setMargin(0)
        
        self._inputLayout.addWidget(self._LabelSlope)
        self._inputLayout.addWidget(self._GuessSlope)
        self._inputLayout.addWidget(qt.HorizontalSpacer())
        self._inputLayout.addWidget(self._LabelStep)
        self._inputLayout.addWidget(self._Step)
        self._inputLayout.addWidget(qt.HorizontalSpacer())
        self._inputLayout.addWidget(self._LabelNum)
        self._inputLayout.addWidget(self._Num)
        self._inputLayout.addWidget(qt.HorizontalSpacer())
        self._inputWidget = qt.QWidget()
        self._inputWidget.setLayout(self._inputLayout)  
        
        self._plotLayout1 = qt.QVBoxLayout(self)
        self._plotLayout1.addWidget(self.spcPlot)
        self._plotWidget1 = qt.QGroupBox()
        self._plotWidget1.setTitle('Single photon counting (SPC)')
        self._plotWidget1.setLayout(self._plotLayout1) 

        self._plotLayout2 = qt.QVBoxLayout(self)
        self._plotLayout2.addWidget(self._tableWidget)
        self._plotWidget2 = qt.QGroupBox()
        self._plotWidget2.setTitle('Estimated slopes')
        self._plotWidget2.setLayout(self._plotLayout2)
        
        plotTradLayout = qt.QVBoxLayout()
        plotTradLayout.addWidget(self._inputWidget)
        plotTradLayout.addWidget(self.tradSpectraPlot)
        plotTradLayout.addWidget(self.tradResultsPlot)
        plotTradWidget = qt.QGroupBox()
        plotTradWidget.setTitle('Integrating algorithm, varying slopes')
        plotTradWidget.setLayout(plotTradLayout)

        self._rsLayout = qt.QGridLayout(self)
        self._rsLayout.addWidget(plotTradWidget, 0, 0, 3, 1)
        #~ self._rsLayout.addWidget(qt.VerticalSpacer(),1,0,)
        #~ self._rsLayout.addWidget(qt.VerticalSpacer(),1,1)
        self._rsLayout.addWidget(self._plotWidget1, 0, 1, 1, 1)
        self._rsLayout.addWidget(self._plotWidget2, 1, 1, 1, 1)
        self._rsLayout.addWidget(self._extractbuttonWidget, 2, 1, 1, 1)
        self._rsWidget = qt.QWidget()
        self._rsWidget.setContentsMargins(0,0,0,-8)
        self._rsWidget.setLayout(self._rsLayout)
        
        
        self._lsLayout = qt.QVBoxLayout(self)
        self._lsLayout.addWidget(self._sourcefilesWidget)
        self._lsWidget = qt.QWidget()
        self._lsWidget.setContentsMargins(0,0,0,-8)
        self._lsWidget.setSizePolicy(
            qt.QSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Preferred))
        self._lsWidget.setLayout(self._lsLayout)
        
        
        self._mainLayout = qt.QHBoxLayout()
        self._mainLayout.addWidget(self._lsWidget)
        self._mainLayout.addWidget(self._rsWidget)
        self.setLayout(self._mainLayout)
    
    
    
    
    def Extract(self):
        
        fnames = [i.data(0) for i in 
            self._sourcefilesWidget.sourceView.selectedIndexes()]
        if len(fnames) < 1:
            return
        
        self._tableWidget.table.setRowCount(len(fnames))
        
        self.spcPlot.clearCurves()
        self.tradSpectraPlot.clearCurves()
        self.tradResultsPlot.clearCurves()
        
        self.num= self._Num.value()
        self.guessSlope= self._GuessSlope.value()
        self.step= self._Step.value()
        self._specarithmetic= SpecArithmetic()
        
        colors = self.spcPlot.colorList
        
        
        slopes = (np.arange(self.num)-self.num//2) * self.step
        slopes += self.guessSlope
        
        opt_slopes = []
        
        for i, fname in enumerate(fnames):
            
            self._tableWidget.table.setItem(i, 0, qt.QTableWidgetItem(fname))
            
            
            f = '/'.join([self._sourcefilesWidget.sourceFolder, fname])
            self.peak=[]
            self.fwhm=[]
            s = []
            self.rxs = RixsSpectrum(f, slope=self.guessSlope)
            xfit = np.arange(self.rxs.image.Data.shape[1])
            theta2 = optimize.fmin(self.total_huber_loss, [0,0], disp=False)
            self.spcPlot.addCurve(self.rxs.cp[:,1],self.rxs.cp[:,0]+5*i,'Original data %s' %fname,color=colors[i], symbol='x', linestyle=' ', replot=True)
            self.spcPlot.addCurve(xfit, theta2[0] + theta2[1] * xfit+5*i,'Fitted line %s slope= %.4f' %(fname,theta2[1]), color=colors[i], linestyle='-', replot=True)
            self.spcPlot.replot()
            self._tableWidget.table.setItem(i, 3, qt.QTableWidgetItem('%.4f' %theta2[1]))            
            
            
            for jjj, slope in enumerate(slopes):
                
                self._tableWidget.table.setItem(i, 1, qt.QTableWidgetItem('%d/%d' % (jjj, len(slopes))))
                self._tableWidget.table.setItem(i, 2, qt.QTableWidgetItem('%d/%d' % (jjj, len(slopes))))
                
                
                starttime = datetime.now()
                if jjj == 0:
                    x = RixsSpectrum(f, slope=slope)
                else:
                    x.slope = slope
                    x.make_traditional_spectrum()
                stoptime = datetime.now()
                print('Traditional: %.f ms' % ((stoptime-starttime).microseconds / 1000))
                self.tradSpectraPlot.addCurve(x.spectrum['Pixel'],x.spectrum['Photons'], '%s-Photons-%s' % (slope,fname),color=colors[i])
                #peak and fwhm from specarithmetic
                peakpos, peakvalue, peakindex = self._specarithmetic.search_peak( x.spectrum['Pixel'], x.spectrum['Photons'])
                fwhmvalue, cfwhm =self._specarithmetic.search_fwhm(x.spectrum['Pixel'], x.spectrum['Photons'])
                s.append(slope)
                self.peak.append(peakvalue)
                self.fwhm.append(fwhmvalue)
                #~ self.tradResultsPlot.addCurve(s, self.peak, 'Peak height', symbol='o', color=self.colors[i])
                #~ self.tradResultsPlot.replot()
            
            
            
            #~ self.tradResultsPlot.setDefaultPlotLines(False)
            self.tradResultsPlot.addCurve(slopes, self.peak,  'Peak values %s' %(fname),color=colors[i],symbol= 'o', linestyle=' ')
            self.tradResultsPlot.addCurve(slopes, self.fwhm,  'Fwhm values %s' %(fname),color=colors[i],symbol= 'o', linestyle=' ')
            poptslope = np.polyfit(slopes, self.peak, 2)
            poptfwhm = np.polyfit(slopes, self.fwhm, 2)
            
            self.optimalPeak=poptslope[1]/(poptslope[0]*2)*(-1)
            self.optimalFwhm=poptfwhm[1]/(poptfwhm[0]*2)*(-1)
            
            xnew = np.linspace(slopes.min(), slopes.max(), 100)
            self.tradResultsPlot.addCurve(xnew, np.polyval(poptslope, xnew), 'Peak fit %s' %(fname), color=colors[i])
            self.tradResultsPlot.addCurve(xnew, np.polyval(poptfwhm, xnew), 'FWHM values %s' %(fname), color=colors[i], replot=True)
            
            
            #print self.optimalSlope
            
            
            
            self._tableWidget.table.setItem(i, 1, qt.QTableWidgetItem('%.4f' %self.optimalPeak))
            self._tableWidget.table.setItem(i, 2, qt.QTableWidgetItem('%.4f' %self.optimalFwhm))
            
            opt_slopes.append([self.optimalPeak, self.optimalFwhm, theta2[1]])
            
        # Mean values
        opt_slopes = np.array(opt_slopes)
        nrows = opt_slopes.shape[0]
        ncols = opt_slopes.shape[1]
        if nrows < 2: # No reason to calculate mean for only one value
            return
        self._tableWidget.table.setRowCount(nrows+1)
        self._tableWidget.table.setItem(nrows, 0, qt.QTableWidgetItem('MEAN'))
        colmean = opt_slopes.mean(axis=0)
        for col in range(ncols):
            self._tableWidget.table.setItem(nrows, col+1, 
                qt.QTableWidgetItem('%.4f' % colmean[col]))
        return
        
            
    def total_huber_loss(self,theta, c=2): 
        x=self.rxs.cp[:,1]
        y=self.rxs.cp[:,0]
        return self.huber_loss((y - theta[0] - theta[1] * x), c).sum()
        
    def huber_loss(self,t, c=2):
        return ((abs(t) < c) * 0.5 * t ** 2+ (abs(t) >= c) * -c * (0.5 * c - abs(t)))

        
class Table(qt.QDialog):
    def __init__(self, parent=None):
        super(Table, self).__init__(parent)
        layout = qt.QGridLayout() 
        self.led = qt.QLineEdit("Result")
        self.table = qt.QTableWidget()
        #~ self.table.setRowCount(5)
        self.table.setColumnCount(4)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)
        labels=['Image', 'Peak height', 'FWHM', 'SPC']
        self.table.setHorizontalHeaderLabels(labels)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        
#Extract button

class ExtractButtonWidget(qt.QPushButton):
    def __init__(self, parent):
        qt.QPushButton.__init__(self, parent)
        
        self.setText("Estimate slope from images")
        self.setMinimumHeight(30)
        self.clicked.connect(self._extractButtonclicked)
            
            
    def _extractButtonclicked(self):
        qt.QObject.emit(self, qt.SIGNAL('ExtractButtonClicked'), 'EXTRACT')







if __name__ == "__main__":
    import numpy as np
    
    app = qt.QApplication([])
    qt.QObject.connect(app, qt.SIGNAL('lastWindowClosed()'), app, 
        qt.SLOT('quit()'))


    w = MainWindow()
    w.show()
    app.exec_()	
