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
import copy
import time

import numpy as np

from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.pymca import ScanWindow
from PyMca5.PyMcaGui.pymca import ScanWindowInfoWidget
from PyMca5.PyMcaGui.plotting import PlotWindow
from PyMca5.PyMcaCore.SpecFileDataSource import SpecFileDataSource
from PyMca5.PyMcaGui.pymca import QDispatcher
from PyMca5.PyMcaGui.pymca.SumRulesTool import MarkerSpinBox
from PyMca5.PyMcaPlugins import AdvancedAlignmentScanPlugin
from PyMca5.PyMcaMath import SimpleMath


from RTB_Icons import RtbIcons
from RTB_Math import RTB_Math


class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('RixsToolBox - Spectrometer alignment')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.build()
        self.connect_signals()
    
        self.specArithmetic = ScanWindowInfoWidget.SpecArithmetic()
        self.RTB_Math = RTB_Math()
    
    def build(self):
        self._sourceWidget = QDispatcher.QDispatcher(self)
        fileTypeList = ['Spec Files (*.spec)',
                        'Dat Files (*.dat)',
                        'All Files (*.*)']
        self._sourceWidget.sourceSelector.fileTypeList = fileTypeList
        
        for tabnum in range(self._sourceWidget.tabWidget.count()):
            if self._sourceWidget.tabWidget.tabText(tabnum) != 'SpecFile':
                self._sourceWidget.tabWidget.removeTab(tabnum)
        self._sourceWidget.selectorWidget['SpecFile']
        
        
        #~ self._sourceWidget.selectorWidget['SpecFile'].autoAddBox.setChecked(False)
        #~ self._sourceWidget.selectorWidget['SpecFile'].autoAddBox.hide()
        #~ self._sourceWidget.selectorWidget['SpecFile'].autoReplaceBox.setChecked(False)
        #~ self._sourceWidget.selectorWidget['SpecFile'].autoReplaceBox.hide()
        #~ self._sourceWidget.selectorWidget['SpecFile'].autoOffBox.setChecked(True)
        #~ self._sourceWidget.selectorWidget['SpecFile'].autoOffBox.hide()
        
        self._sourceWidget.selectorWidget['SpecFile'].meshBox.setChecked(False)
        self._sourceWidget.selectorWidget['SpecFile'].meshBox.hide()
        self._sourceWidget.selectorWidget['SpecFile'].forceMcaBox.setChecked(False)
        self._sourceWidget.selectorWidget['SpecFile'].forceMcaBox.hide()
        if hasattr(self._sourceWidget.selectorWidget['SpecFile'], 'object3DBox'):
            self._sourceWidget.selectorWidget['SpecFile'].object3DBox.setChecked(True)
            self._sourceWidget.selectorWidget['SpecFile'].object3DBox.hide()
        
        
        
        
        
        self._plotSpectraWindow = ScanWindow.ScanWindow(
            parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            newplot=False, # Hide mirror active curve, ... functionality
            roi=False,     # No ROI widget
            control=True, # Hide option button
            position=True, # Show x,y position display
            info=True,
            fit=True,
            kw={'logx': False, # Hide logarithmic x-scale tool button
                'logy': False, # Hide logarithmic y-scale tool button
                'flip': False, # Hide whatever this does
                'fit': False, # Hide simple fit tool button
                'energy': False}) # Hide simple fit tool button
        self._plotSpectraWindow.infoDockWidget.hide()
        #~ self._plotSpectraWindow
        
        
        
        self._plotWidthWindow = PlotWindow.PlotWindow(
            parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            newplot=False, # Hide mirror active curve, ... functionality
            roi=False,     # No ROI widget
            control=False, # Hide option button
            position=False, # Show x,y position display
            kw={'logx': False, # Hide logarithmic x-scale tool button
                'logy': False, # Hide logarithmic y-scale tool button
                'flip': False, # Hide whatever this does
                'fit': True, # Hide simple fit tool button
                'energy': False}) # Hide simple fit tool button
        self._plotWidthWindow.toolBar.show()
        self._plotWidthWindow.enableActiveCurveHandling(False)
        self._plotWidthWindow.setGraphTitle('FWHM')
        
        
        
        
        self._plotHeightWindow = PlotWindow.PlotWindow(
            parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            newplot=False, # Hide mirror active curve, ... functionality
            roi=False,     # No ROI widget
            control=False, # Hide option button
            position=False, # Show x,y position display
            kw={'logx': False, # Hide logarithmic x-scale tool button
                'logy': False, # Hide logarithmic y-scale tool button
                'flip': False, # Hide whatever this does
                'fit': True, # Hide simple fit tool button
                'energy': False}) # Hide simple fit tool button
        self._plotHeightWindow.toolBar.show()
        self._plotHeightWindow.setGraphTitle('Peak height')
        
        
        self._plotPosWindow = PlotWindow.PlotWindow(
            parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            newplot=False, # Hide mirror active curve, ... functionality
            roi=False,     # No ROI widget
            control=False, # Hide option button
            position=False, # Show x,y position display
            kw={'logx': False, # Hide logarithmic x-scale tool button
                'logy': False, # Hide logarithmic y-scale tool button
                'flip': False, # Hide whatever this does
                'fit': True, # Hide simple fit tool button
                'energy': False}) # Hide simple fit tool button
        self._plotPosWindow.toolBar.show()
        self._plotPosWindow.setGraphTitle('Peak position')
        
        
        self.motorComboBox = qt.QComboBox()
        self.motorComboBox.setMinimumWidth(100)
        self.motorComboBox.addItems(['S#'])
        self.motorname = self.motorComboBox.currentText()
        
        self.posLabel = qt.QLabel()
        self.posLabel.setTextFormat(1)
        self.posLabel.setMinimumWidth(200)
        self.widthLabel = qt.QLabel()
        self.widthLabel.setTextFormat(1)
        self.widthLabel.setMinimumWidth(200)
        self.heightLabel = qt.QLabel()
        self.heightLabel.setTextFormat(1)
        self.heightLabel.setMinimumWidth(200)
        
        self.derivCheckBox  = qt.QCheckBox('Analyse derivative')
        
        self.inputLayout = qt.QHBoxLayout(self)
        self.inputLayout.addWidget(self.derivCheckBox)
        self.inputLayout.addWidget(qt.QLabel('Plot against '))
        self.inputLayout.addWidget(self.motorComboBox)
        self.inputLayout.addWidget(qt.HorizontalSpacer())
        self.inputLayout.addSpacing(20)
        self.inputLayout.addWidget(self.widthLabel)
        self.inputLayout.addSpacing(20)
        self.inputLayout.addWidget(self.heightLabel)
        self.inputLayout.addSpacing(20)
        self.inputLayout.addWidget(self.posLabel)
        self.inputLayout.addWidget(qt.HorizontalSpacer())
        self.inputWidget = qt.QWidget()
        self.inputWidget.setLayout(self.inputLayout)
        
        
        self._topLayout = qt.QVBoxLayout(self)
        self._topLayout.addWidget(self._plotSpectraWindow)
        self._topWidget = qt.QWidget()
        self._topWidget.setLayout(self._topLayout)
        
        self._plotLayout = qt.QHBoxLayout(self)
        self._plotLayout.addWidget(self._plotWidthWindow)
        self._plotLayout.addWidget(self._plotHeightWindow)
        self._plotLayout.addWidget(self._plotPosWindow)
        self._plotWidget = qt.QWidget()
        self._plotWidget.setLayout(self._plotLayout)
        
        self.bottomLayout = qt.QVBoxLayout()
        self.bottomLayout.addWidget(self.inputWidget)
        self.bottomLayout.addWidget(self._plotWidget)
        self.bottomWidget = qt.QWidget()
        self.bottomWidget.setLayout(self.bottomLayout)
        
        self.rsSplitter = qt.QSplitter(self)
        self.rsSplitter.setOrientation(qt.Qt.Vertical)
        self.rsSplitter.setHandleWidth(5)
        self.rsSplitter.setStretchFactor(1, 1)
        self.rsSplitter.addWidget(self._topWidget)
        self.rsSplitter.addWidget(self.bottomWidget)
        
        self.rsLayout = qt.QVBoxLayout(self)
        self.rsLayout.addWidget(self.rsSplitter)
        self.rsWidget = qt.QWidget()
        self.rsWidget.setLayout(self.rsLayout)
        
        
        self._lsLayout = qt.QVBoxLayout(self)
        self._lsLayout.addWidget(self._sourceWidget)
        self._lsWidget = qt.QWidget()
        self._lsWidget.setLayout(self._lsLayout)

        self.splitter = qt.QSplitter(self)
        self.splitter.setOrientation(qt.Qt.Horizontal)
        self.splitter.setHandleWidth(5)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.addWidget(self._lsWidget)
        self.splitter.addWidget(self.rsWidget)
        
        self._mainLayout = qt.QHBoxLayout()
        self._mainLayout.addWidget(self.splitter)
        self.setLayout(self._mainLayout)
        
        
        self.simpleMath = SimpleMath.SimpleMath()
        
        
        
        return 0
    
    def connect_signals(self):
        self.motorComboBox.currentIndexChanged.connect(self.selectionChanged)
        
        
        
        self._sourceWidget.sigAddSelection.connect(
            self._plotSpectraWindow._addSelection)
        self._sourceWidget.sigAddSelection.connect(
            self.selectionChanged)
        
        self._sourceWidget.sigRemoveSelection.connect(
            self._plotSpectraWindow._removeSelection)
        self._sourceWidget.sigRemoveSelection.connect(
            self.selectionChanged)
        
        self._sourceWidget.sigReplaceSelection.connect(
            self._plotSpectraWindow._replaceSelection)
        self._sourceWidget.sigReplaceSelection.connect(
            self.selectionChanged)
        
        self.derivCheckBox.stateChanged.connect(self.selectionChanged)
        
        return 0
    
    
        
    
    def selectionChanged(self):
        
        
        curves = self._plotSpectraWindow.getAllCurves()
        motorvalue = []
        peakposition = []
        peakwidth = []
        peakheight = []
        
        gaussian = lambda x, x0, amp, fwhm: amp* np.exp(-(x-x0)**2/2/(fwhm/2.35)**2)
        
        for i, curve in enumerate(curves):
            x, y, legend, info = curve
            
            if self.derivCheckBox.isChecked():
                x, y = self.simpleMath.derivate(x, y)
                if y.mean() < 0:
                    y *= -1
            
            if i == 0:
                motornames = ['S#'] + info['MotorNames']
                selectedMotor = self.motorComboBox.currentText()
                
                self.motorComboBox.currentIndexChanged.disconnect(
                                                    self.selectionChanged)
                self.motorComboBox.clear()
                self.motorComboBox.addItems(motornames)
                if selectedMotor in motornames:
                    self.motorComboBox.setCurrentIndex(
                        motornames.index(selectedMotor))
                self.motorComboBox.currentIndexChanged.connect(
                                                    self.selectionChanged)
                
                self.motorName = self.motorComboBox.currentText()
                motorname = self.motorName
            
            if motorname in info['MotorNames']:
                xval = info['MotorValues'][info['MotorNames'].index(motorname)]
                peakpos, peak, myidx = self.specArithmetic.search_peak(x, y)
                fwhm, cfwhm  = self.specArithmetic.search_fwhm(x, y, 
                                                        peak=peak,index=myidx)
                
                # ~ popt, pcov = optimize.curve_fit(gaussian, x, y, p0=(peakpos, peak, fwhm))
                popt, pcov = self.RTB_Math.curve_fit(
                                    gaussian, x, y, p0=(peakpos, peak, fwhm))
                motorvalue.append(xval)
                peakposition.append(popt[0])
                peakwidth.append(np.abs(popt[2]))
                peakheight.append(popt[1])
            
            if motorname == 'S#':
                xval = float(info['Key'])
                peakpos, peak, myidx = self.specArithmetic.search_peak(x, y)
                fwhm, cfwhm  = self.specArithmetic.search_fwhm(x, y, 
                                                        peak=peak,index=myidx)
                                                        
                # ~ popt, pcov = optimize.curve_fit(gaussian, x, y, p0=(peakpos, peak, fwhm))
                popt, pcov = self.RTB_Math.curve_fit(
                                    gaussian, x, y, p0=(peakpos, peak, fwhm))
                
                motorvalue.append(xval)
                peakposition.append(popt[0])
                peakwidth.append(np.abs(popt[2]))
                peakheight.append(popt[1])
                
        xy = np.array([motorvalue, peakposition, peakwidth, peakheight]).T
        xy = 1. * xy[xy[:,0].argsort()]
        motorvalue = xy[:,0]
        peakposition = xy[:,1]
        peakwidth = xy[:,2]
        peakheight = xy[:,3]
        
        
        
        
        
        
        self._plotWidthWindow.clearCurves()
        self._plotWidthWindow.addCurve(motorvalue, peakwidth, legend='FWHM', 
            info={'xlabel': motorname, 'ylabel': 'FWHM'},
            linestyle='none', symbol='o', color='k')
        self._plotWidthWindow.setGraphTitle('FWHM')
        #~ self._plotWidthWindow.removeMarker('x0')
        self.widthLabel.setText('')
        if len(motorvalue) >= 3:
            xfit = np.linspace(
                motorvalue[0] - 0.05*(motorvalue[-1]-motorvalue[0]), 
                motorvalue[-1]+ 0.05*(motorvalue[-1]-motorvalue[0]), 100)
            popt = np.polyfit(motorvalue, peakwidth, 2)
            yfit = np.polyval(popt, xfit)
            self._plotWidthWindow.addCurve(xfit, yfit, legend='fit', 
                color='red', linestyle='-', symbol=' ')
            x0 = -popt[1]/2/popt[0]
            #~ self._plotWidthWindow.insertXMarker(x0, legend='x0', 
                #~ text='%.2f' % (x0), color='red')
            if popt[0] <= 0:
                text = '<b>FWHM</b><br>Maximum is  %.4f  at  %.4f' % (np.polyval(popt, x0), x0)
            else:
                text = '<b>FWHM</b><br>Minimum is  %.4f  at  %.4f' % (np.polyval(popt, x0), x0)
            self.widthLabel.setText(text)
        self._plotWidthWindow.setGraphXLabel(motorname)
        self._plotWidthWindow.setGraphYLabel(
            'FWHM (%s)' % self._plotSpectraWindow.getGraphXLabel())
        
        
        self._plotHeightWindow.clearCurves()
        self._plotHeightWindow.addCurve(motorvalue, peakheight, legend='Peak height', 
            info={'xlabel': motorname, 'ylabel': 'Peak height'},
            linestyle='none', symbol='o', color='k')
        self._plotHeightWindow.setGraphTitle('Peak height')
        #~ self._plotHeightWindow.removeMarker('x0')
        self.heightLabel.setText('')
        if len(motorvalue) >= 3:
            xfit = np.linspace(
                motorvalue[0]-0.05*(motorvalue[-1]-motorvalue[0]), 
                motorvalue[-1]+ 0.05*(motorvalue[-1]-motorvalue[0]), 100)
            popt = np.polyfit(motorvalue, peakheight, 2)
            yfit = np.polyval(popt, xfit)
            self._plotHeightWindow.addCurve(xfit, yfit, legend='fit', 
                color='red', linestyle='-', symbol=' ')
            x0 = -popt[1]/2/popt[0]
            #~ self._plotHeightWindow.insertXMarker(x0, legend='x0', 
                #~ text='%.2f' % (x0), color='red')
            if popt[0] <= 0:
                text = '<b>Peak height</b><br>Maximum is  %.4f  at  %.4f' % (np.polyval(popt, x0), x0)
            else:
                text = '<b>Peak height</b><br>Minimum is  %.4f  at  %.4f' % (np.polyval(popt, x0), x0)
            self.heightLabel.setText(text)
        self._plotHeightWindow.setGraphXLabel(motorname)
        self._plotHeightWindow.setGraphYLabel(
            'Peak height (%s)' % self._plotSpectraWindow.getGraphYLabel())
        
        
        self._plotPosWindow.clearCurves()
        self._plotPosWindow.addCurve(motorvalue, peakposition, legend='Peak position', 
            info={'xlabel': motorname, 'ylabel': 'Peak position'},
            linestyle='none', symbol='o', color='k')
        self._plotPosWindow.setGraphTitle('Peak position')
        #~ self._plotPosWindow.removeMarker('x0')
        self.posLabel.setText('')
        if len(motorvalue) >= 3:
            xfit = np.linspace(
                motorvalue[0]-0.05*(motorvalue[-1]-motorvalue[0]), 
                motorvalue[-1]+ 0.05*(motorvalue[-1]-motorvalue[0]), 100)
            popt = np.polyfit(motorvalue, peakposition, 2)
            yfit = np.polyval(popt, xfit)
            self._plotPosWindow.addCurve(xfit, yfit, legend='fit', 
                color='red', linestyle='-', symbol=' ')
            x0 = -popt[1]/2/popt[0]
            #~ self._plotPosWindow.insertXMarker(x0, legend='x0', 
                #~ text='%.2f' % (x0), color='red')
            if popt[0] <= 0:
                text = '<b>Peak position</b><br>Maximum is  %.4f  at  %.4f' % (np.polyval(popt, x0), x0)
            else:
                text = '<b>Peak position</b><br>Minimum is  %.4f  at  %.4f' % (np.polyval(popt, x0), x0)
            self.posLabel.setText(text)
        self._plotPosWindow.setGraphXLabel(motorname)
        self._plotPosWindow.setGraphYLabel(
            'Peak position (%s)' % self._plotSpectraWindow.getGraphXLabel())
        
        
        
        
        
    


if __name__ == "__main__":
    import numpy as np
    
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)
    # ~ if 'Fusion' in qt.QStyleFactory.keys():
        # ~ app.setStyle('Fusion')


    w = MainWindow()
    w.show()
    app.exec_()


