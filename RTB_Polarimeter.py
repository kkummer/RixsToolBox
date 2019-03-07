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
from PyMca5.PyMcaCore.SpecFileDataSource import SpecFileDataSource
from PyMca5.PyMcaGui.pymca import QDispatcher
from PyMca5.PyMcaGui.pymca.SumRulesTool import MarkerSpinBox
from PyMca5.PyMcaCore import DataObject

from RTB_SpecGen import ExportWidget
from RTB_Icons import RtbIcons
from RTB_Math import RTB_Math

# ~ from silx.gui.plot import PlotWindow

class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('RixsToolBox - Polarimeter analysis')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.build()
        self.connect_signals()
        self.piReflSpinBox.setValue(0.08)
        self.sigmaReflSpinBox.setValue(0.12)
        self.scansCalibrated = False
        
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
        
        
        self._sourceWidget.selectorWidget['SpecFile'].autoAddBox.setChecked(False)
        self._sourceWidget.selectorWidget['SpecFile'].autoAddBox.hide()
        self._sourceWidget.selectorWidget['SpecFile'].autoReplaceBox.setChecked(False)
        self._sourceWidget.selectorWidget['SpecFile'].autoReplaceBox.hide()
        self._sourceWidget.selectorWidget['SpecFile'].autoOffBox.setChecked(True)
        self._sourceWidget.selectorWidget['SpecFile'].autoOffBox.hide()
        
        self._sourceWidget.selectorWidget['SpecFile'].meshBox.setChecked(False)
        self._sourceWidget.selectorWidget['SpecFile'].meshBox.hide()
        self._sourceWidget.selectorWidget['SpecFile'].forceMcaBox.setChecked(False)
        self._sourceWidget.selectorWidget['SpecFile'].forceMcaBox.hide()
        if hasattr(self._sourceWidget.selectorWidget['SpecFile'], 'object3DBox'):
            self._sourceWidget.selectorWidget['SpecFile'].object3DBox.setChecked(True)
            self._sourceWidget.selectorWidget['SpecFile'].object3DBox.hide()
        
        
        self._sourceWidget.selectorWidget['SpecFile'].addButton.setText("Set as DIRECT SPECTRUM")
        self._sourceWidget.selectorWidget['SpecFile'].replaceButton.setText("Set as POLARISED SPECTRUM")
        self._sourceWidget.selectorWidget['SpecFile'].removeButton.hide()
        
        self._sourceWidget.selectorWidget['SpecFile'].list.setSelectionMode(
            qt.QAbstractItemView.SingleSelection)
        
        
        
        self._exportWidget = ExportWidget()
        
        self._plotSpectraWindow = ScanWindow.ScanWindow(parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            roi=False,     # No ROI widget
            control=True, # Hide option button
            position=True, # Show x,y position display
            )
        
        # ~ self._plotSpectraWindow = PlotWindow(parent=self)
        
        if hasattr(self._plotSpectraWindow, '_buildLegendWidget'):
            self._plotSpectraWindow._buildLegendWidget()
        
        
        reflectivityWidget = qt.QGroupBox()
        reflectivityWidget.setTitle('Multilayer reflectivity')
        reflectivityLayout = qt.QGridLayout()
        
        self.piReflSpinBox = qt.QDoubleSpinBox()
        self.piReflSpinBox.setMaximumWidth(100)
        self.piReflSpinBox.setMinimumWidth(70)
        self.piReflSpinBox.setAlignment(qt.Qt.AlignRight)
        self.piReflSpinBox.setMinimum(0.01)
        self.piReflSpinBox.setMaximum(1)
        self.piReflSpinBox.setDecimals(4)
        self.piReflSpinBox.setSingleStep(.001)
        self.piReflSpinBox.setValue(0.1)
        piReflLayout = qt.QHBoxLayout()
        piReflLayout.addWidget(qt.QLabel(u'R\u03C0'))
        piReflLayout.addWidget(qt.HorizontalSpacer())
        piReflLayout.addWidget(self.piReflSpinBox)
        piReflWidget = qt.QWidget()
        piReflWidget.setLayout(piReflLayout)
        
        
        self.sigmaReflSpinBox = qt.QDoubleSpinBox()
        self.sigmaReflSpinBox.setMaximumWidth(100)
        self.sigmaReflSpinBox.setMinimumWidth(70)
        self.sigmaReflSpinBox.setAlignment(qt.Qt.AlignRight)
        self.sigmaReflSpinBox.setMinimum(0.01)
        self.sigmaReflSpinBox.setMaximum(1)
        self.sigmaReflSpinBox.setDecimals(4)
        self.sigmaReflSpinBox.setSingleStep(.001)
        self.sigmaReflSpinBox.setValue(0.1)
        sigmaReflLayout = qt.QHBoxLayout()
        sigmaReflLayout.addWidget(qt.QLabel(u'R\u03C3'))
        sigmaReflLayout.addWidget(qt.HorizontalSpacer())
        sigmaReflLayout.addWidget(self.sigmaReflSpinBox)
        sigmaReflWidget = qt.QWidget()
        sigmaReflWidget.setLayout(sigmaReflLayout)
        
        
        self.deltaReflSpinBox = qt.QDoubleSpinBox()
        self.deltaReflSpinBox.setMaximumWidth(100)
        self.deltaReflSpinBox.setMinimumWidth(70)
        self.deltaReflSpinBox.setAlignment(qt.Qt.AlignRight)
        self.deltaReflSpinBox.setMinimum(0.01)
        self.deltaReflSpinBox.setMaximum(1)
        self.deltaReflSpinBox.setDecimals(4)
        self.deltaReflSpinBox.setSingleStep(.001)
        self.deltaReflSpinBox.setValue(0.12)
        deltaReflLayout = qt.QHBoxLayout()
        deltaReflLayout.addWidget(qt.QLabel(u'\u03B4'))
        deltaReflLayout.addWidget(qt.HorizontalSpacer())
        deltaReflLayout.addWidget(self.deltaReflSpinBox)
        deltaReflWidget = qt.QWidget()
        deltaReflWidget.setLayout(deltaReflLayout)
        
        self.avgReflSpinBox = qt.QDoubleSpinBox()
        self.avgReflSpinBox.setMaximumWidth(100)
        self.avgReflSpinBox.setMinimumWidth(70)
        self.avgReflSpinBox.setAlignment(qt.Qt.AlignRight)
        self.avgReflSpinBox.setMinimum(0.01)
        self.avgReflSpinBox.setMaximum(1)
        self.avgReflSpinBox.setDecimals(4)
        self.avgReflSpinBox.setSingleStep(.001)
        self.avgReflSpinBox.setValue(0.12)
        avgReflLayout = qt.QHBoxLayout()
        avgReflLayout.addWidget(qt.QLabel(u'R_avg'))
        avgReflLayout.addWidget(qt.HorizontalSpacer())
        avgReflLayout.addWidget(self.avgReflSpinBox)
        avgReflWidget = qt.QWidget()
        avgReflWidget.setLayout(avgReflLayout)
        
        hline = qt.QFrame()
        hline.setFrameShape(qt.QFrame.HLine)
        hline.setFrameShadow(qt.QFrame.Sunken)
        
        reflectivityLayout.addWidget(piReflWidget, 0, 0, 1, 1)
        reflectivityLayout.addWidget(sigmaReflWidget, 0, 1, 1, 1)
        reflectivityLayout.addWidget(hline, 1, 0, 1, 2)
        reflectivityLayout.addWidget(deltaReflWidget, 2, 0, 1, 1)
        reflectivityLayout.addWidget(avgReflWidget, 2, 1, 1, 1)
        reflectivityWidget.setLayout(reflectivityLayout)
        
        
        preprocessingWidget = qt.QGroupBox()
        preprocessingWidget.setTitle('Preprocessing')
        preprocessingLayout = qt.QGridLayout()
        
        self.rescaleSpinBox = qt.QDoubleSpinBox()
        self.rescaleSpinBox.setMaximumWidth(80)
        self.rescaleSpinBox.setMinimumWidth(80)
        self.rescaleSpinBox.setAlignment(qt.Qt.AlignRight)
        self.rescaleSpinBox.setMinimum(0.01)
        self.rescaleSpinBox.setDecimals(5)
        self.rescaleSpinBox.setSingleStep(.05)
        self.rescaleSpinBox.setValue(1.00)
        
        
        self.shiftSpinBox = qt.QDoubleSpinBox()
        self.shiftSpinBox.setMaximumWidth(80)
        self.shiftSpinBox.setMinimumWidth(80)
        self.shiftSpinBox.setAlignment(qt.Qt.AlignRight)
        self.shiftSpinBox.setDecimals(4)
        self.shiftSpinBox.setSingleStep(.0005)
        self.shiftSpinBox.setMinimum(-100000)
        self.shiftSpinBox.setValue(0)
        
        self.dirOffsetSpinBox = qt.QDoubleSpinBox()
        self.dirOffsetSpinBox.setMaximumWidth(80)
        self.dirOffsetSpinBox.setMinimumWidth(80)
        self.dirOffsetSpinBox.setAlignment(qt.Qt.AlignRight)
        self.dirOffsetSpinBox.setDecimals(5)
        self.dirOffsetSpinBox.setSingleStep(.0001)
        self.dirOffsetSpinBox.setMinimum(-100000)
        self.dirOffsetSpinBox.setValue(0)
        
        self.polOffsetSpinBox = qt.QDoubleSpinBox()
        self.polOffsetSpinBox.setMaximumWidth(80)
        self.polOffsetSpinBox.setMinimumWidth(80)
        self.polOffsetSpinBox.setAlignment(qt.Qt.AlignRight)
        self.polOffsetSpinBox.setDecimals(5)
        self.polOffsetSpinBox.setSingleStep(.0001)
        self.polOffsetSpinBox.setMinimum(-100000)
        self.polOffsetSpinBox.setValue(0)
        
        
        self.dirGaussSpinBox = qt.QDoubleSpinBox()
        self.dirGaussSpinBox.setMaximumWidth(80)
        self.dirGaussSpinBox.setMinimumWidth(80)
        self.dirGaussSpinBox.setAlignment(qt.Qt.AlignRight)
        self.dirGaussSpinBox.setDecimals(3)
        self.dirGaussSpinBox.setSingleStep(.005)
        self.dirGaussSpinBox.setMinimum(0)
        self.dirGaussSpinBox.setValue(0)
        
        
        self.polGaussSpinBox = qt.QDoubleSpinBox()
        self.polGaussSpinBox.setMaximumWidth(80)
        self.polGaussSpinBox.setMinimumWidth(80)
        self.polGaussSpinBox.setAlignment(qt.Qt.AlignRight)
        self.polGaussSpinBox.setDecimals(3)
        self.polGaussSpinBox.setSingleStep(.005)
        self.polGaussSpinBox.setMinimum(0)
        self.polGaussSpinBox.setValue(0)
        
        self.polStretchSpinBox = qt.QDoubleSpinBox()
        self.polStretchSpinBox.setMaximumWidth(80)
        self.polStretchSpinBox.setMinimumWidth(80)
        self.polStretchSpinBox.setAlignment(qt.Qt.AlignRight)
        self.polStretchSpinBox.setDecimals(3)
        self.polStretchSpinBox.setSingleStep(.005)
        self.polStretchSpinBox.setMinimum(0.001)
        self.polStretchSpinBox.setValue(1)
        
        
        preprocessingLayout.addWidget(qt.HorizontalSpacer(), 0, 0, 1, 1)
        preprocessingLayout.addWidget(qt.QLabel('Direct spectrum'), 0, 1, 1, 1)
        preprocessingLayout.addWidget(qt.QLabel('Polarised spectrum'), 0, 2, 1, 1)
        preprocessingLayout.addWidget(qt.QLabel('Shift by'), 1, 0, 1, 1)
        preprocessingLayout.addWidget(self.shiftSpinBox, 1, 1, 1, 1)
        preprocessingLayout.addWidget(qt.QLabel('Offset by'), 2, 0, 1, 1)
        preprocessingLayout.addWidget(self.dirOffsetSpinBox, 2, 1, 1, 1)
        preprocessingLayout.addWidget(self.polOffsetSpinBox, 2, 2, 1, 1)
        preprocessingLayout.addWidget(qt.QLabel('Multiply by'), 3, 0, 1, 1)
        preprocessingLayout.addWidget(self.rescaleSpinBox, 3, 2, 1, 1)
        preprocessingLayout.addWidget(qt.QLabel('Broaden by'), 4, 0, 1, 1)
        preprocessingLayout.addWidget(self.dirGaussSpinBox, 4, 1, 1, 1)
        preprocessingLayout.addWidget(self.polGaussSpinBox, 4, 2, 1, 1)
        preprocessingLayout.addWidget(qt.QLabel('Stretch by'), 5, 0, 1, 1)
        preprocessingLayout.addWidget(self.polStretchSpinBox, 5, 2, 1, 1)
        
        preprocessingWidget.setLayout(preprocessingLayout)
        
        
        
        postprocessingWidget = qt.QGroupBox()
        postprocessingWidget.setTitle('Postprocessing')
        postprocessingLayout = qt.QHBoxLayout()
        
        self.postGaussWidthSpinBox = qt.QDoubleSpinBox()
        self.postGaussWidthSpinBox.setMaximumWidth(100)
        self.postGaussWidthSpinBox.setMinimumWidth(100)
        self.postGaussWidthSpinBox.setAlignment(qt.Qt.AlignRight)
        self.postGaussWidthSpinBox.setMinimum(0)
        self.postGaussWidthSpinBox.setDecimals(2)
        self.postGaussWidthSpinBox.setSingleStep(.1)
        self.postGaussWidthSpinBox.setValue(1.00)
        self.postGaussWidthSpinBox.setSuffix(' points')
        postGaussWidthLayout = qt.QHBoxLayout()
        postGaussWidthLayout.addWidget(qt.QLabel('Gaussian filter width'))
        postGaussWidthLayout.addWidget(qt.HorizontalSpacer())
        postGaussWidthLayout.addWidget(self.postGaussWidthSpinBox)
        postGaussWidthWidget = qt.QWidget()
        postGaussWidthWidget.setLayout(postGaussWidthLayout)
        
        
        postprocessingLayout.addWidget(postGaussWidthWidget)
        postprocessingWidget.setLayout(postprocessingLayout)
        
        
        
        
        self.saveButton = qt.QPushButton('Save')
        self.saveButton.setMinimumSize(75,75)
        self.saveButton.setMaximumSize(75,75)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.saveButton.setDisabled(True)
        self.saveButton.setToolTip('Select output file\nto enable saving')
        
        
        
        self._inputLayout = qt.QGridLayout(self)
        self._inputLayout.addWidget(reflectivityWidget, 0, 0, 1, 1)
        self._inputLayout.addWidget(preprocessingWidget, 0, 1, 2, 1)
        self._inputLayout.addWidget(postprocessingWidget, 0, 2, 1, 1)
        self._inputLayout.addWidget(qt.HorizontalSpacer(), 0, 3, 2, 1)
        self._inputLayout.addWidget(self.saveButton, 0, 4, 2, 1)
        self._inputWidget = qt.QWidget()
        self._inputWidget.setLayout(self._inputLayout)
        
        
        self._rsLayout = qt.QVBoxLayout(self)
        self._rsLayout.addWidget(self._inputWidget)
        self._rsLayout.addWidget(self._plotSpectraWindow)
        self._rsWidget = qt.QWidget()
        self._rsWidget.setContentsMargins(0,0,0,-8)
        self._rsWidget.setLayout(self._rsLayout)
        
        self._lsLayout = qt.QVBoxLayout(self)
        self._lsLayout.addWidget(self._sourceWidget)
        self._lsLayout.addWidget(self._exportWidget)
        self._lsWidget = qt.QWidget()
        self._lsWidget.setContentsMargins(0,0,0,-8)
        self._lsWidget.setSizePolicy(
            qt.QSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Preferred))
        self._lsWidget.setLayout(self._lsLayout)
        self._lsWidget.setMaximumWidth(500)
        
        
        self.splitter = qt.QSplitter(self)
        self.splitter.setOrientation(qt.Qt.Horizontal)
        self.splitter.setHandleWidth(5)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.addWidget(self._lsWidget)
        self.splitter.addWidget(self._rsWidget)
        
        self._mainLayout = qt.QHBoxLayout()
        self._mainLayout.addWidget(self.splitter)
        self.setLayout(self._mainLayout)
        
        
        self.directbeamset = False
        self.polarisedbeamset = False
        
        
        return 0
    
    
    
    
    def connect_signals(self):
        self._sourceWidget.sigAddSelection.connect(self.setDirectBeam)
        self._sourceWidget.sigReplaceSelection.connect(self.setPolarisedBeam)
        
        self._exportWidget.OutputFileSelected.connect(self._enableSaveButton)
        
        self.shiftSpinBox.valueChanged.connect(self.shiftSpinBoxChanged)
        self.dirOffsetSpinBox.valueChanged.connect(self.dirOffsetSpinBoxChanged)
        self.polOffsetSpinBox.valueChanged.connect(self.polOffsetSpinBoxChanged)
        self.rescaleSpinBox.valueChanged.connect(self.rescaleSpinBoxChanged)
        self.polStretchSpinBox.valueChanged.connect(self.stretchSpinBoxChanged)
        
        self.piReflSpinBox.valueChanged.connect(self.pisigmaReflChanged)
        self.sigmaReflSpinBox.valueChanged.connect(self.pisigmaReflChanged)
        self.deltaReflSpinBox.valueChanged.connect(self.deltaavgReflChanged)
        self.avgReflSpinBox.valueChanged.connect(self.deltaavgReflChanged)
        
        
        self.postGaussWidthSpinBox.valueChanged.connect(self.analyseButtonClicked)
        self.dirGaussSpinBox.valueChanged.connect(self.preprocessCurves)
        self.polGaussSpinBox.valueChanged.connect(self.preprocessCurves)
        
        
        self._sourceWidget.selectorWidget['SpecFile'].cntTable.sigSpecFileCntTableSignal.connect(self._update_yselection)
        
        return 0
    
    
    
    def _update_yselection(self):
        """ Make sure that only one y counter can be selected """
        self._sourceWidget.selectorWidget['SpecFile'].cntTable.ySelection = self._sourceWidget.selectorWidget['SpecFile'].cntTable.ySelection[-1:]
        for i in range(self._sourceWidget.selectorWidget['SpecFile'].cntTable.rowCount()):
            widget = self._sourceWidget.selectorWidget['SpecFile'].cntTable.cellWidget(i, 2)
            if i in self._sourceWidget.selectorWidget['SpecFile'].cntTable.ySelection:
                if not widget.isChecked():
                    widget.setChecked(True)
            else:
                if widget.isChecked():
                    widget.setChecked(False)
        return 0
    
    
    def pisigmaReflChanged(self):
        self.deltaReflSpinBox.valueChanged.disconnect()
        self.avgReflSpinBox.valueChanged.disconnect()
        pi = self.piReflSpinBox.value()
        sigma = self.sigmaReflSpinBox.value()
        self.deltaReflSpinBox.setValue((sigma-pi)/(sigma+pi))
        self.avgReflSpinBox.setValue((sigma+pi)/2)
        self.deltaReflSpinBox.valueChanged.connect(self.deltaavgReflChanged)
        self.avgReflSpinBox.valueChanged.connect(self.deltaavgReflChanged)
        self.preprocessCurves()
        
        
    
    def deltaavgReflChanged(self):
        self.piReflSpinBox.valueChanged.disconnect()
        self.sigmaReflSpinBox.valueChanged.disconnect()
        delta = self.deltaReflSpinBox.value()
        avg = self.avgReflSpinBox.value()
        self.piReflSpinBox.setValue(avg*(1-delta))
        self.sigmaReflSpinBox.setValue(avg*(1+delta))
        self.piReflSpinBox.valueChanged.connect(self.pisigmaReflChanged)
        self.sigmaReflSpinBox.valueChanged.connect(self.pisigmaReflChanged)
        self.preprocessCurves()
    
    def shiftSpinBoxChanged(self):
        self.preprocessCurves(shift=True)
    
    
    def dirOffsetSpinBoxChanged(self):
        self.preprocessCurves(diroffset=True)
    
    def polOffsetSpinBoxChanged(self):
        self.preprocessCurves(poloffset=True)
    
    
    def rescaleSpinBoxChanged(self):
        self.preprocessCurves(rescale=True)
    
    def stretchSpinBoxChanged(self):
        self.preprocessCurves(stretch=True)
    
    
    
    def setDirectBeam(self, selectionlist):
        legends = self._plotSpectraWindow.getAllCurves(just_legend=True)
        for legend in legends:
            if legend.startswith(u'Direct beam - '):
                self._plotSpectraWindow.removeCurve(legend)
        selectionlist[0]['legend'] = u'Direct beam - '+selectionlist[0]['legend']
        self._plotSpectraWindow._addSelection(selectionlist, replot=True)
        self.directbeamset = True
        self.preprocessCurves(shift=True, rescale=True)
        
    
    def setPolarisedBeam(self, selectionlist):
        legends = self._plotSpectraWindow.getAllCurves(just_legend=True)
        for legend in legends:
            if legend.startswith(u'Polarised beam - '):
                self._plotSpectraWindow.removeCurve(legend)
        selectionlist[0]['legend'] = u'Polarised beam - '+selectionlist[0]['legend']
        self._plotSpectraWindow._addSelection(selectionlist, replot=True)
        self.polarisedbeamset = True
        self.preprocessCurves()
        
    
    
    
    def _enableSaveButton(self):
        self.saveButton.setEnabled(True)
        self.saveButton.setToolTip(None)
    
    
    
    def preprocessCurves(self, rescale=False, shift=False, diroffset=False, 
        poloffset=False, stretch=False):
        curves = self._plotSpectraWindow.getAllCurves()
        self._plotSpectraWindow.clearCurves()
        for curve in curves:
            # ~ x, y, dx, dy = curve.getData()
            # ~ dy = np.sqrt(y)
            # ~ legend = curve.getLegend()
            # ~ info = curve.getInfo()
            x, y, legend, info = curve[:4]
            legend = legend.rstrip(' Y')
            if legend.startswith(u'Direct beam - '):
                if shift:
                    if 'xshift' in info.keys():
                        xshift = self.shiftSpinBox.value() - info['xshift']
                    else:
                        xshift = self.shiftSpinBox.value()
                    info['xshift'] = self.shiftSpinBox.value()
                    x += xshift
                if diroffset:
                    if 'offset' in info.keys():
                        offset = self.dirOffsetSpinBox.value() - info['offset']
                    else:
                        offset = self.dirOffsetSpinBox.value()
                    info['offset'] = self.dirOffsetSpinBox.value()
                    y += offset
                
                self._plotSpectraWindow.addCurve(x, y, legend=legend, info=info, 
                    color='black', symbol='.', linestyle=' ')
                gw = self.dirGaussSpinBox.value() * len(x) / (x[-1] - x[0]) / 2.35482 # Assuming equidistance
                self._plotSpectraWindow.addCurve(x, self.RTB_Math.gaussian_filter(y, gw),
                    legend='Direct beam broadened',  
                    color='black', replot=True, linestyle='-')
                
                
            
            elif legend.startswith(u'Polarised beam - '):
                if poloffset:
                    if 'offset' in info.keys():
                        offset = self.polOffsetSpinBox.value() - info['offset']
                    else:
                        offset = self.polOffsetSpinBox.value()
                    info['offset'] = self.polOffsetSpinBox.value()
                    y += offset
                if rescale:
                    if 'yrescaling' in info.keys():
                        yrescaling = self.rescaleSpinBox.value()/info['yrescaling']
                    else:
                        yrescaling = self.rescaleSpinBox.value()
                    info['yrescaling'] = self.rescaleSpinBox.value()
                    y *= yrescaling
                if stretch:
                    if 'xstretching' in info.keys():
                        xstretching = self.polStretchSpinBox.value()/info['xstretching']
                    else:
                        xstretching = self.polStretchSpinBox.value()
                    info['xstretching'] = self.polStretchSpinBox.value()
                    x *= xstretching
                
                self._plotSpectraWindow.addCurve(x, y, legend=legend, info=info, 
                    color='grey', linestyle='--', symbol='.')
                gw = self.polGaussSpinBox.value() * len(x) / (x[-1] - x[0]) / 2.35482 # Assuming equidistance
                self._plotSpectraWindow.addCurve(x, self.RTB_Math.gaussian_filter(y, gw),
                    legend='Polarised beam broadened', color='grey', 
                    replot=True, linestyle='-')
                
                avg_refl = 0.5 * (self.piReflSpinBox.value() + self.sigmaReflSpinBox.value())
                self._plotSpectraWindow.addCurve(x, y/avg_refl, 
                    legend='Polarised beam renormalized to average multilayer reflectivity',
                    color='green', linestyle='--', symbol='.')
                self._plotSpectraWindow.addCurve(x, self.RTB_Math.gaussian_filter(y, gw)/avg_refl,
                    legend='Polarised beam broad renormalized to average multilayer reflectivity', color='green', 
                    replot=True, linestyle='-')
                    
            #~ elif not legend.startswith('Polarised beam') or legend.startswith('Direct beam'):
                #~ self._plotSpectraWindow.removeCurve(legend)
        del curves
        self.analyseButtonClicked()
    
    
    def analyseButtonClicked(self):
        legends = self._plotSpectraWindow.getAllCurves(just_legend=True)
        
        Rh = self.piReflSpinBox.value()
        Rv = self.sigmaReflSpinBox.value()
        
        direct_curve = None
        polar_curve = None
        
        for legend in legends:
            if legend.startswith('Direct beam - '):
                direct_curve_raw = self._plotSpectraWindow.getCurve(legend)
            if legend.startswith('Polarised beam - '):
                polar_curve_raw = self._plotSpectraWindow.getCurve(legend)
        
        for legend in legends:
            if legend.startswith('Direct beam broadened '):
                direct_curve = self._plotSpectraWindow.getCurve(legend)
            if legend.startswith('Polarised beam broadened '):
                polar_curve = self._plotSpectraWindow.getCurve(legend)
                
        if direct_curve == None or polar_curve == None:
            print('Need direct and polarised data')
            return 0
        
        
        x = direct_curve[0]
        direct = direct_curve[1]
        polar = np.interp(x, polar_curve[0], polar_curve[1])
        #~ polar_raw = np.interp(x, polar_curve_raw[0], polar_curve_raw[1])
        #~ 
        #~ self._plotSpectraWindow.addCurve(x, polar_raw, legend=polar_curve_raw[2], 
            #~ color='grey', linestyle='--', symbol='.')
        self._plotSpectraWindow.addCurve(x, polar, legend=polar_curve[2],
            color='grey', replot=True, linestyle='-')
        
        hor = (polar - Rv * direct) / (Rh - Rv)
        ver = (polar - Rh * direct) / (Rv - Rh)
        
        
        self._plotSpectraWindow.addCurve(x, hor, legend='pi out', color='blue', linestyle='--', symbol='.')
        self._plotSpectraWindow.addCurve(x, ver, legend='sigma out', color='red', replot=True, linestyle='--', symbol='.')
        
        self._plotSpectraWindow.addCurve(x, self.RTB_Math.gaussian_filter(hor, self.postGaussWidthSpinBox.value()), legend='pi out Gaussian', color='blue', linestyle='-')
        self._plotSpectraWindow.addCurve(x, self.RTB_Math.gaussian_filter(ver, self.postGaussWidthSpinBox.value()), legend='sigma out Gaussian', color='red', linestyle='-')
        
        
    
        
    
    
    
    
    
    def saveButtonClicked(self):
        curves = self._plotSpectraWindow.getAllCurves()
        
        
        columns = []
        columnlabels = []
        
        for curve in curves:
            if curve[2].startswith('Direct beam -'):
                xref = curve[0]
                columnlabels.insert(0, curve[3]['xlabel'])
                columns.insert(0, xref)
        
        for curve in curves:
            x, y, legend, info = curve
            if legend.startswith('Polarised beam'):
                y = np.interp(xref, x, y)
            columns.append(y)
            columnlabels.append(legend)
        
        columns = np.vstack(columns).T
        
        
        header = []
        header.append('#D  %s' % time.strftime('%Y-%m-%d %H:%M:%S', 
                time.localtime(time.time())))
        
        header.append('#C  ')
        header.append('#C  Multilayer reflectivity')
        header.append('#C  Reflectivity sigma: %.3f' % (self.piReflSpinBox.value()))
        header.append('#C  Reflectivity pi: %.3f' % (self.sigmaReflSpinBox.value()))
        header.append('#C  ')
        header.append('#C  Preprocessing')
        header.append('#C  Direct spectrum shifted by: %.3f units' % (self.shiftSpinBox.value()))
        header.append('#C  Direct spectrum multiplied by: %.3f' % (self.rescaleSpinBox.value()))
        header.append('#C  Direct spectrum broadened by: %.3f units' % (self.dirGaussSpinBox.value()))
        header.append('#C  Polarised spectrum broadened by: %.3f' % (self.polGaussSpinBox.value()))
        header.append('#C  ')
        header.append('#C  Postprocessing')
        header.append('#C  Gaussian filter width: %.3f points' % (self.postGaussWidthSpinBox.value()))
        header.append('#C  ')
        header.append('#N  %d' % (len(columnlabels)))
        header.append('#L  %s' % ('  '.join(columnlabels)))
        
        
        specfilename = self._exportWidget.outputFile
        if not os.path.isfile(specfilename):
            with open('%s' % (specfilename), 'wb+') as f:
                fileheader = '#F %s\n\n' % (specfilename)
                f.write(fileheader.encode('ascii'))
            scannumber = 1
        else:
            keys = SpecFileDataSource(specfilename).getSourceInfo()['KeyList']
            scans = [int(k.split('.')[0]) for k in keys]
            scannumber = max(scans) + 1
            
        output = []
        output.append('#S %d  %s\n' % (scannumber, 'Polarimeter analysis'))
        output.append('\n'.join(header))
        output.append('\n')
        output.append(''.join('%s\n' % (' '.join([str(si) for si in s])) 
            for s in columns.tolist()))
        output.append('\n')
        
        
        with open('%s' % (specfilename), 'ab+') as f:
            f.write(''.join(output).encode('ascii'))
        print('Spectra saved to \"%s\"' % (specfilename))
        
        key = SpecFileDataSource(specfilename).getSourceInfo()['KeyList'][-1]
        
        if self._exportWidget._datCheckBox.isChecked():
            if not os.path.isdir(specfilename.rstrip('.spec')):
                os.mkdir(specfilename.rstrip('.spec'))
            if self._exportWidget.askForScanName():
                path = '%s/S%04d_%s' % (specfilename.rstrip('.spec'), 
                    scannumber, key.split('.')[-1])
                command = self._exportWidget.getScanName(path=path)
            else:
                command = 'Polarimeter analysis'
            command = command.replace('.','_').replace(' ', '_')
            command = command.replace(':','_')
            datfilename = '%s/S%04d_%s_%s.dat' % (
                specfilename.rstrip('.spec'), scannumber, 
                key.split('.')[-1], command)
            np.savetxt('%s' % (datfilename), columns)
            print('Spectra saved to \"%s\"\n' % (datfilename))
    
    
    





if __name__ == "__main__":
    
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)
    
    
    w = MainWindow()
    w.show()
    app.exec_()


