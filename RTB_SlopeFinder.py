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
import RTB_SpecGen as SpecGenGUI
from RTB_Icons import RtbIcons
from RTB_Math import RTB_Math



class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('RixsToolBox - Find slope')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        
        self._initialize_parameters()
        
        self._expertDialog = SpecGenGUI.ExpertSettingsDialog(self, 
            lower_threshold=self.lower_threshold,
            upper_threshold=self.upper_threshold, 
            masksize=self.masksize, 
            SPC_gridsize=self.SPC_gridsize,
            SPC_low_threshold=self.SPC_low_threshold, 
            SPC_high_threshold=self.SPC_high_threshold, 
            SPC_single_threshold=self.SPC_single_threshold, 
            SPC_double_threshold=self.SPC_double_threshold)
        
        self.spcPlot = PlotWindow.PlotWindow(parent=self, 
            backend=None, plugins=False, newplot=False, roi=False, 
            control=False, position=True, info=False, logx = False, 
            logy = False, togglePoints = False)
        
        self._sourcefilesWidget = SpecGenGUI.SourceFilesWidget(self)
        self.tableWidget= Table(self)
        self.extractButton = qt.QPushButton('Estimate slope\nfrom images')
        self.extractButton.resize(120, 65)
        self.extractButton.setMinimumSize(120, 65)
        self.extractButton.setMaximumSize(120, 65)
        
        
        self.parametersWidget = SpecGenGUI.ParametersWidget(self)
        self.parametersWidget._spcCheckBox.setDisabled(True)
        # ~ self.parametersWidget._slopeDoubleSpinBox.setValue(0)
        self.parametersWidget._slopeDoubleSpinBox.setDisabled(True)
        self.backgroundWidget = SpecGenGUI.BackgroundWidget(self)
        self.backgroundWidget.extractBackgroundCheckBox.setDisabled(True)
        self.tabWidget = qt.QTabWidget()
        self.tabWidget.addTab(self.parametersWidget, 'Parameters')
        self.tabWidget.addTab(self.backgroundWidget, 'Background subtraction')
        
        
        plotLayout = qt.QVBoxLayout(self)
        plotLayout.addWidget(self.spcPlot)
        plotWidget = qt.QGroupBox()
        plotWidget.setTitle('Photon positions in image')
        plotWidget.setLayout(plotLayout)
        
        tableLayout = qt.QVBoxLayout(self)
        tableLayout.addWidget(self.tableWidget)
        tableBox = qt.QGroupBox()
        tableBox.setTitle('Estimated slopes')
        tableBox.setLayout(tableLayout)
        
        rsLayout = qt.QGridLayout(self)
        rsLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        rsLayout.addWidget(plotWidget, 1, 0, 10, 2)
        rsLayout.addWidget(self.extractButton, 0, 2, 1, 1)
        rsLayout.addWidget(tableBox, 1, 2, 10, 2)
        rsLayout.setSpacing(10)
        rsWidget = qt.QWidget()
        rsWidget.setLayout(rsLayout)
        
        
        
        
        lsLayout = qt.QVBoxLayout(self)
        lsLayout.addWidget(self._sourcefilesWidget)
        lsWidget = qt.QWidget()
        lsWidget.setContentsMargins(0,0,0,-8)
        lsWidget.setSizePolicy(
            qt.QSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Preferred))
        lsWidget.setLayout(lsLayout)
        
        
        
        mainLayout = qt.QHBoxLayout()
        mainLayout.addWidget(lsWidget)
        mainLayout.addWidget(rsWidget)
        self.setLayout(mainLayout)
        
        self.RTB_Math = RTB_Math()
        
        # Initial parameters
        self.parametersWidget._slopeDoubleSpinBox.setValue(self.slope)
        self.parametersWidget._pointsperpixelDoubleSpinBox.setValue(self.points_per_pixel)
        self.parametersWidget._spcCheckBox.setChecked(self.SPC)
        
        self.connect_signals()
    
    
    def _initialize_parameters(self):
        self.slope = 0
        self.points_per_pixel = 2.7
        self.binning = 1 
        self.lower_threshold = -1e5
        self.upper_threshold = 1e5
        self.masksize = 5
        self.SPC = True
        self.SPC_gridsize = 3
        self.SPC_low_threshold = .2
        self.SPC_high_threshold = 1.0
        self.SPC_single_threshold = .4
        self.SPC_double_threshold = 1.5
        self.ROI = None
        self.ccd_parameters = [0.00016, 1.2, 3.6]
        return 0
    
    def connect_signals(self):
        self.extractButton.clicked.connect(self.specgen)
        self.parametersWidget.ExpertSettingsButtonClicked.connect(
            self.expertsettings)
        self._sourcefilesWidget.DarkImagesAdded.connect(
            self.backgroundWidget.addDarkImages)
        self._sourcefilesWidget.DarkImagesRemoved.connect(
            self.backgroundWidget.removeDarkImages)
        self.backgroundWidget.DarkImagesViewModelChanged.connect(
            self.get_dark_images)
    
    def update_parameters(self):
        self.points_per_pixel = \
            self.parametersWidget._pointsperpixelDoubleSpinBox.value()
    
    
    def expertsettings(self):
        self._expertDialog = SpecGenGUI.ExpertSettingsDialog(self, 
            lower_threshold=self.lower_threshold, 
            upper_threshold= self.upper_threshold, 
            masksize=self.masksize,
            SPC_gridsize= self.SPC_gridsize,
            SPC_low_threshold=self.SPC_low_threshold,
            SPC_high_threshold=self.SPC_high_threshold,
            SPC_single_threshold=self.SPC_single_threshold, 
            SPC_double_threshold=self.SPC_double_threshold, 
            ROI=self.ROI, 
            ccd_params=self.ccd_parameters)
        self._expertDialog.show()
    
    
    def spcSettings(self):
        self.SPC = self._parametersWidget._spcCheckBox.isChecked()
    
    
    def get_dark_images(self):
        self.darkImages = []
        for fname in self.backgroundWidget.darkImagesList:
            x = RixsSpectrum(fname, slope=self.slope, 
                        points_per_pixel=self.points_per_pixel, 
                        binning=self.binning,
                        lower_threshold=self.lower_threshold, 
                        upper_threshold=self.upper_threshold, 
                        masksize=self.masksize, 
                        SPC=False, SPC_gridsize=self.SPC_gridsize, 
                        SPC_low_threshold=self.SPC_low_threshold, 
                        SPC_high_threshold=self.SPC_high_threshold, 
                        SPC_single_threshold=self.SPC_single_threshold, 
                        SPC_double_threshold=self.SPC_double_threshold, 
                        roi=self.ROI, ccd_params=self.ccd_parameters,
                        extract_background=True, background='off'
                        )
            for frame in range(len(x.spectrum)):
                self.darkImages.append((x.info['ExposureTime'][frame], 
                                        x.rawImageData[:,:,frame]))
    
    
    def specgen(self):
        self.update_parameters()
        #self._update_expertsetting()
        
        self.background = None
        self.backgroundAcquisitionTime = None
        self.backgroundForceZero = False
        
        if self.backgroundWidget.useDarkImagesCheckBox.isChecked():
            if self.darkImages:
                if self.backgroundWidget.methodComboBox.currentIndex() == 0: #Average
                    self.background = np.dstack(
                        [img[1] for img in self.darkImages]).mean(axis=2)
                else: # Sum
                    self.background = np.dstack(
                        [img[1] for img in self.darkImages]).sum(axis=2)
                if self.backgroundWidget.methodComboBox.currentIndex() == 2: #Sum rescaled to acquistion time
                    self.backgroundAcquisitionTime = sum(
                        [img[0] for img in self.darkImages])
                if self.backgroundWidget.zeroBaselineCheckBox.isChecked():
                    self.backgroundForceZero = True
        
        
        fnames = [i.data(0) for i in 
            self._sourcefilesWidget.sourceView.selectedIndexes()]
        
        self.tableWidget.table.setRowCount(len(fnames))
        self.spcPlot.clearCurves()
        self._specarithmetic= SpecArithmetic()
        colors = self.spcPlot.colorList
        
        opt_slopes = []
        
        nframes = 0
        for i, fname in enumerate(fnames):
            f = '/'.join([self._sourcefilesWidget.sourceFolder, fname])
            self.rxs = RixsSpectrum(f, slope=self.slope, points_per_pixel=self.points_per_pixel, binning=self.binning,
                lower_threshold=self.lower_threshold, upper_threshold=self.upper_threshold, 
                masksize=self.masksize, SPC=self.SPC, SPC_gridsize=self.SPC_gridsize, SPC_low_threshold=self.SPC_low_threshold, SPC_high_threshold=self.SPC_high_threshold, 
                SPC_single_threshold=self.SPC_single_threshold, SPC_double_threshold=self.SPC_double_threshold, roi=self.ROI, ccd_params=self.ccd_parameters,
                extract_background=self.backgroundWidget.extractBackgroundCheckBox.isChecked(), 
                background=self.background, background_aqn_time=self.backgroundAcquisitionTime,
                background_force_zero=self.backgroundForceZero)
            
            for framenumber in range(len(self.rxs.spectrum)):
                self.tableWidget.table.setItem(nframes, 0, 
                    qt.QTableWidgetItem('%s : %04d' % (fname, framenumber)))
                nframes += 1
                xfit = np.arange(self.rxs.imageData[:,:,framenumber].shape[1])
                theta2 = self.RTB_Math.minimize(self.total_huber_loss, [0,0], disp=False)[0]
                self.spcPlot.addCurve(self.rxs.cp[0][:,1],self.rxs.cp[0][:,0],'Original data %s' %fname, color=colors[i%len(colors)], symbol='x', linestyle=' ', replot=True)
                self.spcPlot.addCurve(xfit, theta2[0] + theta2[1] * xfit,'Fitted line %s slope= %.4f' %(fname,theta2[1]), color=colors[i%len(colors)], linestyle='-', replot=True)
                self.spcPlot.replot()
                self.tableWidget.table.setItem(i, 1, qt.QTableWidgetItem('%.4f' %theta2[1]))
                opt_slopes.append(theta2[1])
            
        # Mean values
        opt_slopes = np.array(opt_slopes)
        n_slopes = opt_slopes.size
        if n_slopes < 2: # No reason to calculate mean for only one value
            return
        self.tableWidget.table.setRowCount(n_slopes+1)
        self.tableWidget.table.setItem(n_slopes, 0, qt.QTableWidgetItem('MEAN'))
        
        self.tableWidget.table.setItem(n_slopes, 1, 
            qt.QTableWidgetItem('%.4f' % opt_slopes.mean()))
        return
                
        
        
    
    
    def Extract(self):
        
        fnames = [i.data(0) for i in 
            self._sourcefilesWidget.sourceView.selectedIndexes()]
        if len(fnames) < 1:
            return
        
        self.tableWidget.table.setRowCount(len(fnames))
        self.spcPlot.clearCurves()
        self._specarithmetic= SpecArithmetic()
        colors = self.spcPlot.colorList
        
        opt_slopes = []
        
        for i, fname in enumerate(fnames):
            
            self.tableWidget.table.setItem(i, 0, qt.QTableWidgetItem(fname))
            
            
            f = '/'.join([self._sourcefilesWidget.sourceFolder, fname])
            s = []
            self.rxs = RixsSpectrum(f, slope=0)
            
            
            
            
            xfit = np.arange(self.rxs.imageData.shape[1])
            theta2 = self.RTB_Math.minimize(self.total_huber_loss, [0,0], disp=False)[0]
            #~ ts_slope = stats.theilslopes(self.rxs.cp[:,0], self.rxs.cp[:,1], 0.99)
            self.spcPlot.addCurve(self.rxs.cp[0][:,1],self.rxs.cp[0][:,0],'Original data %s' %fname, color=colors[i%len(colors)], symbol='x', linestyle=' ', replot=True)
            self.spcPlot.addCurve(xfit, theta2[0] + theta2[1] * xfit,'Fitted line %s slope= %.4f' %(fname,theta2[1]), color=colors[i%len(colors)], linestyle='-', replot=True)
            #~ self.spcPlot.addCurve(xfit, ts_slope[1] + ts_slope[0] * xfit,'Fit %s, slope= %.4f' %(fname,theta2[1]), color=colors[i%len(colors)], linestyle='--', replot=True)
            self.spcPlot.replot()
            self.tableWidget.table.setItem(i, 1, qt.QTableWidgetItem('%.4f' %theta2[1]))
            #~ self.tableWidget.table.setItem(i, 1, qt.QTableWidgetItem('%.4f' %ts_slope[0]))
            opt_slopes.append(theta2[1])
            #~ opt_slopes.append(ts_slope[0])
            
        # Mean values
        opt_slopes = np.array(opt_slopes)
        n_slopes = opt_slopes.size
        if n_slopes < 2: # No reason to calculate mean for only one value
            return
        self.tableWidget.table.setRowCount(n_slopes+1)
        self.tableWidget.table.setItem(n_slopes, 0, qt.QTableWidgetItem('MEAN'))
        
        self.tableWidget.table.setItem(n_slopes, 1, 
            qt.QTableWidgetItem('%.4f' % opt_slopes.mean()))
        return
        
        
    def total_huber_loss(self,theta, c=2): 
        x=self.rxs.cp[0][:,1]
        y=self.rxs.cp[0][:,0]
        return self.huber_loss((y - theta[0] - theta[1] * x), c).sum()
        
    def huber_loss(self,t, c=2):
        return ((abs(t) < c) * 0.5 * t ** 2+ (abs(t) >= c) * -c * (0.5 * c - abs(t)))

        
class Table(qt.QDialog):
    def __init__(self, parent=None):
        super(Table, self).__init__(parent)
        layout = qt.QGridLayout() 
        self.led = qt.QLineEdit('Result')
        self.table = qt.QTableWidget()
        #~ self.table.setRowCount(5)
        self.table.setColumnCount(2)
        self.table.setColumnWidth(1, 80)
        self.table.setColumnWidth(0, 150)
        labels=['Image', 'Slope']
        self.table.setHorizontalHeaderLabels(labels)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        





if __name__ == "__main__":
    import numpy as np
    
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)


    w = MainWindow()
    w.show()
    app.exec_()	
