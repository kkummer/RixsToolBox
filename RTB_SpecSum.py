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
from PyMca5.PyMcaGui.plotting import PlotWindow
from PyMca5.PyMcaCore.SpecFileDataSource import SpecFileDataSource
from PyMca5.PyMcaGui.pymca import QDispatcher
from PyMca5.PyMcaGui.pymca.SumRulesTool import MarkerSpinBox
from PyMca5.PyMcaPlugins import AdvancedAlignmentScanPlugin
from PyMca5.PyMcaMath import SimpleMath

from RTB_SpecGen import ExportWidget
from RTB_Icons import RtbIcons

from RTB_Math import RTB_Math


class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('RixsToolBox - Align and sum spectra')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.build()
        self.connect_signals()
    
        self.shiftedScans = None
    
    
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
        
        
        
        self._exportWidget = ExportWidget()
        
        # ~ print(dir(silx.gui.plot))
        # ~ self._plotSpectraWindow = silx.gui.plot.PlotWindow()
        
        self._plotSpectraWindow = ScanWindow.ScanWindow(
            parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            roi=False,     # No ROI widget
            control=False, # Hide option button
            position=True, # Show x,y position display
            info=False,
            fit=False,
            specfit=False)
        self._plotSpectraWindow._mathToolBar.hide()
        #~ self._plotSpectraWindow.graph.enablemarkermode()
        
        self._plotShiftsWindow = PlotWindow.PlotWindow(
            parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            roi=False,     # No ROI widget
            control=False, # Hide option button
            position=False, # Show x,y position display
            )
        self._plotShiftsWindow.toolBar.hide()
        self._plotShiftsWindow.setMaximumHeight(250)
        
        
        
        
        
        
        self._minSpinBox = MarkerSpinBox(self, self._plotSpectraWindow, 'min')
        self._minSpinBox.setMaximumWidth(100)
        self._minSpinBox.setMinimumWidth(70)
        self._minSpinBox.setAlignment(qt.Qt.AlignRight)
        self._minSpinBox.setMinimum(-100000)
        self._minSpinBox.setMaximum(100000)
        self._minSpinBox.setDecimals(2)
        self._minSpinBox.setSingleStep(1)
        self._minSpinBox.setValue(0)
        
        
        self._maxSpinBox = MarkerSpinBox(self, self._plotSpectraWindow, 'max')
        self._maxSpinBox.setMaximumWidth(100)
        self._maxSpinBox.setMinimumWidth(70)
        self._maxSpinBox.setAlignment(qt.Qt.AlignRight)
        self._maxSpinBox.setMinimum(-100000)
        self._maxSpinBox.setMaximum(100000)
        self._maxSpinBox.setDecimals(2)
        self._maxSpinBox.setSingleStep(1)
        self._maxSpinBox.setValue(0)
        
        
        self._markersPositioned = False
        
        self.methodComboBox = qt.QComboBox()
        self.methodComboBox.addItems(
            ['FFT',
             'MAX',
             'FIT',
             'FIT DRV'])
        methodToolTip = (''.join([
                    'Select the method used to calculate the shift\n',
                    'is calculated.\n\n',
                    'FFT:\n',
                    '    Calculates the correlation between two curves\n',
                    '    using its Fourier transform. The shift is\n',
                    '    proportional to the distance of the correlation\n',
                    '    function\'s maxima.\n',
                    'MAX:\n',
                    '    Determines the shift as the distance between the\n',
                    '    maxima of two peaks\n',
                    'FIT:\n',
                    '    Guesses the most prominent feature in the spectrum\n',
                    '    and tries to fit it with a Gaussian peak. Before\n',
                    '    the fit is performed, the background is\n',
                    '    substracted. The shift is given by the difference\n',
                    '    of the center of mass between two peaks.\n',
                    'FIT DRV:\n',
                    '    Like FIT, but the fit is performed on the derivate\n',
                    '    of the spectrum.']))
        self.methodComboBox.setToolTip(methodToolTip)
        self.methodComboBox.setMaximumWidth(120)
        
        
        
        
        self.groupCheckBox = qt.QCheckBox(self, text='Calculate for groups of')
        self.groupSpinBox = qt.QSpinBox(self)
        self.groupSpinBox.setRange(2, 10000)
        self.groupSpinBox.setValue(10)
        self.groupSpinBox.setSingleStep(1)
        self.groupSpinBox.setMaximumWidth(100)
        self.groupSpinBox.setMinimumWidth(100)
        self.groupSpinBox.setSuffix(' Spectra')
        
        self.trendCheckBox = qt.QCheckBox(self, text='Align to trend')
        self.sumrefCheckBox = qt.QCheckBox(self, text='Use sum as reference for alignment')
        self.oversampleCheckBox = qt.QCheckBox(self, text='Oversample before alignment')
        
        self.sumrefCheckBox.setChecked(False)
        self.sumrefCheckBox.hide()
        self.oversampleCheckBox.setChecked(False)
        self.oversampleCheckBox.hide()
        
        groupLayout = qt.QHBoxLayout()
        groupLayout.addWidget(self.groupCheckBox)
        groupLayout.addWidget(self.groupSpinBox)
        #~ groupLayout.addSpacing(20)
        #~ groupLayout.addWidget(self.sumrefCheckBox)
        #~ groupLayout.addSpacing(20)
        #~ groupLayout.addWidget(self.oversampleCheckBox)
        groupLayout.addWidget(qt.HorizontalSpacer())
        groupLayout.setContentsMargins(0, 0, 0, 0)
        self.groupWidget = qt.QWidget()
        self.groupWidget.setLayout(groupLayout)
        
        windowLayout = qt.QHBoxLayout()
        windowLayout.addSpacing(20)
        windowLayout.addWidget(self._minSpinBox)
        windowLayout.addSpacing(5)
        windowLayout.addWidget(qt.QLabel('to'))
        windowLayout.addSpacing(5)
        windowLayout.addWidget(self._maxSpinBox)
        windowLayout.addWidget(qt.HorizontalSpacer())
        windowLayout.setContentsMargins(0, 0, 0, 0)
        windowWidget = qt.QWidget(self)
        windowWidget.setLayout(windowLayout)
        
        methodLayout = qt.QHBoxLayout()
        methodLayout.addSpacing(20)
        methodLayout.addWidget(self.methodComboBox)
        methodLayout.addWidget(qt.HorizontalSpacer())
        methodLayout.setContentsMargins(0, 0, 0, 0)
        methodWidget = qt.QWidget()
        methodWidget.setLayout(methodLayout)
        
        alignmentLayout = qt.QGridLayout()
        alignmentLayout.addWidget(qt.QLabel('Window'), 0, 0, 1, 1)
        alignmentLayout.addWidget(windowWidget, 0, 1, 1, 1)
        alignmentLayout.addWidget(qt.QLabel('Method'), 1, 0, 1, 1)
        alignmentLayout.addWidget(methodWidget, 1, 1, 1, 1)
        alignmentLayout.addWidget(self.groupWidget, 2, 0, 1, 2)
        alignmentLayout.setContentsMargins(10, 10, 10, 10)
        alignmentLayout.setSpacing(7)
        alignmentWidget = qt.QGroupBox('Settings for shift calculation')
        alignmentWidget.setLayout(alignmentLayout)
        alignmentWidget.setMaximumWidth(300)
        
        
        
        
        # ~ self.trendSpline = qt.QRadioButton('Smoothing spline', checked=True)
        self.trendPoly = qt.QRadioButton('Polynomial of degree', checked=True)
        self.trendAvg = qt.QRadioButton('Gaussian filter over', checked=False)
        self.trendGroup = qt.QButtonGroup()
        # ~ self.trendGroup.addButton(self.trendSpline)
        self.trendGroup.addButton(self.trendPoly)
        self.trendGroup.addButton(self.trendAvg)
        
        self.trendPolyOrder = qt.QSpinBox()
        self.trendPolyOrder.setMinimum(1)
        self.trendPolyOrder.setMaximum(25)
        self.trendPolyOrder.setValue(1)
        
        self.trendAvgWidth = qt.QDoubleSpinBox()
        self.trendAvgWidth.setMinimum(.1)
        self.trendAvgWidth.setValue(5)
        self.trendAvgWidth.setDecimals(1)
        self.trendAvgWidth.setSingleStep(.2)
        self.trendAvgWidth.setMaximum(100)
        self.trendAvgWidth.setSuffix(' points')
        self.trendAvgWidth.setMinimumWidth(90)
        self.trendAvgWidth.setMaximumWidth(90)
        
        self.trendStateChanged()
        
        trendLayout = qt.QGridLayout()
        trendLayout.addWidget(self.trendCheckBox, 0, 0, 1, 3)
        trendLayout.addWidget(qt.QLabel('     '), 1, 0, 1, 1)
        # ~ trendLayout.addWidget(self.trendSpline, 1, 1, 1, 1)
        trendLayout.addWidget(self.trendPoly, 2, 1, 1, 1)
        trendLayout.addWidget(self.trendPolyOrder, 2, 2, 1, 1)
        trendLayout.addWidget(self.trendAvg, 3, 1, 1, 1)
        trendLayout.addWidget(self.trendAvgWidth, 3, 2, 1, 1)
        trendLayout.setContentsMargins(10, 10, 10, 10)
        trendLayout.setSpacing(7)
        self.trendWidget = qt.QGroupBox('Trend settings')
        self.trendWidget.setLayout(trendLayout)
        
        
        
        
        
        self.calcButton = qt.QPushButton('Calculate\nshifts')
        self.calcButton.setMinimumSize(75,75)
        self.calcButton.setMaximumSize(75,75)
        self.calcButton.clicked.connect(self.calcButtonClicked)
        
        
        self.alignButton = qt.QPushButton('Align')
        self.alignButton.setMinimumSize(75,75)
        self.alignButton.setMaximumSize(75,75)
        self.alignButton.clicked.connect(self.alignButtonClicked)
        self.alignButton.setEnabled(False)
            
        self.sumButton = qt.QPushButton('Sum')
        self.sumButton.setMinimumSize(75,75)
        self.sumButton.setMaximumSize(75,75)
        self.sumButton.clicked.connect(self.sumButtonClicked)
            
        self.saveButton = qt.QPushButton('Save')
        self.saveButton.setMinimumSize(75,75)
        self.saveButton.setMaximumSize(75,75)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.saveButton.setEnabled(False)
        self.saveButton.setToolTip('Select an output file\nto enable saving.')
        
        self.whichButtonClicked = None
        
        self._inputLayout = qt.QHBoxLayout(self)
        self._inputLayout.addWidget(alignmentWidget)
        self._inputLayout.addSpacing(20)
        self._inputLayout.addWidget(self.trendWidget)
        self._inputLayout.addWidget(qt.HorizontalSpacer())
        self._inputLayout.addWidget(self.calcButton)
        self._inputLayout.addWidget(self.alignButton)
        self._inputLayout.addWidget(self.sumButton)
        self._inputLayout.addWidget(self.saveButton)
        self._inputLayout.setContentsMargins(0, 0, 0, 0)
        self._inputWidget = qt.QWidget()
        self._inputWidget.setLayout(self._inputLayout)
        self._inputWidget.setMaximumHeight(170)
        
        
        self._rsLayout = qt.QVBoxLayout(self)
        self._rsLayout.addWidget(self._inputWidget)
        self._rsLayout.addWidget(self._plotSpectraWindow)   
        self._rsLayout.addWidget(self._plotShiftsWindow)
        self._rsWidget = qt.QWidget()
        #~ self._rsWidget.setContentsMargins(0,0,0,-8)
        self._rsWidget.setLayout(self._rsLayout)
        
        self._lsLayout = qt.QVBoxLayout(self)
        self._lsLayout.addWidget(self._sourceWidget)
        self._lsLayout.addWidget(self._exportWidget)
        self._lsWidget = qt.QWidget()
        #~ self._lsWidget.setContentsMargins(0,0,0,-8)
        #~ self._lsWidget.setSizePolicy(
            #~ qt.QSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Preferred))
        self._lsWidget.setLayout(self._lsLayout)
        #~ self._lsWidget.setMaximumWidth(500)

        self.splitter = qt.QSplitter(self)
        self.splitter.setOrientation(qt.Qt.Horizontal)
        self.splitter.setHandleWidth(10)
        self.splitter.addWidget(self._lsWidget)
        self.splitter.addWidget(self._rsWidget)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 4)
        
        self._mainLayout = qt.QHBoxLayout()
        self._mainLayout.addWidget(self.splitter)
        self.setLayout(self._mainLayout)
        
        
        self.simpleMath = SimpleMath.SimpleMath()
        self.RTB_Math = RTB_Math()
        
        
        return 0
    
    
    def connect_signals(self):
        self._sourceWidget.sigAddSelection.connect(
            self._plotSpectraWindow._addSelection)
        self._sourceWidget.sigAddSelection.connect(
            self._positionMarkers)
        self._sourceWidget.sigRemoveSelection.connect(
            self._plotSpectraWindow._removeSelection)
        self._sourceWidget.sigReplaceSelection.connect(
            self._plotSpectraWindow._replaceSelection)
        
        self._exportWidget.OutputFileSelected.connect(self._enableSaveButton)
        
        self._sourceWidget.sigReplaceSelection.connect(
            self._enableButtons)
        
        
        self._sourceWidget.sigReplaceSelection.connect(self.plottedSpectraChanged)
        self._sourceWidget.sigAddSelection.connect(self.plottedSpectraChanged)
        self._sourceWidget.sigRemoveSelection.connect(self.plottedSpectraChanged)
        
        
        self.trendCheckBox.stateChanged.connect(self.trendStateChanged)
        self.trendGroup.buttonClicked.connect(self.trendStateChanged)
        self.trendPolyOrder.valueChanged.connect(self.calculateTrend)
        self.trendAvgWidth.valueChanged.connect(self.calculateTrend)
        
        self._minSpinBox.valueChanged.connect(self.enableCalcButton)
        self._maxSpinBox.valueChanged.connect(self.enableCalcButton)
        self.methodComboBox.currentIndexChanged.connect(self.enableCalcButton)
        self.groupCheckBox.stateChanged.connect(self.enableCalcButton)
        self.groupSpinBox.valueChanged.connect(self.enableCalcButton)
        
        self._minSpinBox.intersectionsChangedSignal.connect(self.enableCalcButton)
        self._maxSpinBox.intersectionsChangedSignal.connect(self.enableCalcButton)
        
        return 0
    
    def enableCalcButton(self):
        self.calcButton.setEnabled(True)
        self.saveButton.setEnabled(False)
    
    
    def plottedSpectraChanged(self):
        self.alignButton.setEnabled(False)
        self.calcButton.setEnabled(True)
        self._plotShiftsWindow.clearCurves()
        
    
    def trendStateChanged(self):
        if self.trendCheckBox.isChecked():
            # ~ self.trendSpline.setEnabled(True)
            self.trendPoly.setEnabled(True)
            if self.trendPoly.isChecked():
                self.trendPolyOrder.setEnabled(True)
            else:
                self.trendPolyOrder.setEnabled(False)
            self.trendAvg.setEnabled(True)
            if self.trendAvg.isChecked():
                self.trendAvgWidth.setEnabled(True)
            else:
                self.trendAvgWidth.setEnabled(False)
            self.calculateTrend()
        else:
            # ~ self.trendSpline.setEnabled(False)
            self.trendPoly.setEnabled(False)
            self.trendPolyOrder.setEnabled(False)
            self.trendAvg.setEnabled(False)
            self.trendAvgWidth.setEnabled(False)
            if self._plotShiftsWindow.getCurve('Trend'):
                self._plotShiftsWindow.removeCurve('Trend')
    
    
    
    def _enableButtons(self):
        #~ self.alignButton.setEnabled(True)
        self.sumButton.setEnabled(True)
        self._sourceWidget.selectorWidget['SpecFile'].addButton.setEnabled(True)
        self._sourceWidget.selectorWidget['SpecFile'].removeButton.setEnabled(True)
        if self._exportWidget._folderLineEdit.text() != '':
            self.saveButton.setEnabled(True)
        self.shiftedScans = None
        return 0
    
    
    def _enableSaveButton(self):
        self.saveButton.setEnabled(True)
        self.saveButton.setToolTip(None)
    
    def _positionMarkers(self):
        if not self._markersPositioned:
            limits = self._plotSpectraWindow.getGraphXLimits()
            self._minSpinBox.setValue(limits[0]+0.1*(limits[1]-limits[0]))
            self._maxSpinBox.setValue(limits[0]+0.9*(limits[1]-limits[0]))
            self._markersPositioned = True
    
    
    def findShifts(self, curves, legends, label=''):
        
        if self.oversampleCheckBox.isChecked():
            oversampling = 5
            self._plotSpectraWindow.removeCurves(legends)
            for curve in curves:
                x, y, legend, info = curve
                xnew = np.linspace(x[0], x[-1], len(x)*oversampling)
                ynew = np.interp(xnew, x, y)
                self._plotSpectraWindow.addCurve(xnew, ynew, legend, info)
        
        if self.groupCheckBox.isChecked():
            old_curves = copy.deepcopy(self._plotSpectraWindow.getAllCurves())
            old_legends = copy.deepcopy(self._plotSpectraWindow.getAllCurves(just_legend=True))
            
            groupsize = self.groupSpinBox.value()
            groups = []
            
            iii = -1
            for iii in range(len(legends)//groupsize):
                groups.append(legends[iii*groupsize:(iii+1)*groupsize])
            if len(legends)%groupsize != 0:
                groups.append(legends[(iii+1)*groupsize:])
            self._plotSpectraWindow.removeCurves(legends)
            
            
            groupshifts = []
            shiftedgroups = []
            
            # Calculate shifts within each group
            for i, scangroup in enumerate(groups):
                for j, scan in enumerate(scangroup):
                    x, y, legend, info = curves[i*groupsize+j]
                    self._plotSpectraWindow.addCurve(x, y, legend, info)
                self._plotSpectraWindow._simpleOperation('average')
                shiftedgroups.append(self._plotSpectraWindow.getActiveCurve())
                
            
            # Calculate shifts between groups
            if len(shiftedgroups) > 1:
                self._plotSpectraWindow.clearCurves()
                for i, group in enumerate(shiftedgroups):
                    x, y, legend, info = group
                    self._plotSpectraWindow.addCurve(x, y, 'Group %d' % i)
                xlimits = self._plotSpectraWindow.getGraphXLimits()
                self._plotSpectraWindow.setGraphXLimits(
                    self._minSpinBox.value(), self._maxSpinBox.value())
                self._plotSpectraWindow.replot()
                llist, ldict = self.aasp.calculateShifts()
                groupshifts = [ldict[legend] for legend in llist]
            else:
                groupshifts.append(0)
            
            # Plot shifts between groups
            x = np.arange(len(legends)) + 1
            y = np.zeros(len(legends))
            for i, shift in enumerate(groupshifts):
                y[i*groupsize:i*groupsize+len(groups[i])] = shift
            #~ self._plotShiftsWindow.addCurve(x, y, 'Group shifts'+label)
            
            # Prepare shift dictionary
            llist = legends
            ldict = {}
            for i, shift in enumerate(groupshifts):
                for j, scan in enumerate(groups[i]):
                    x, y, legend, info = curves[i*groupsize+j]
                    ldict[legend] = shift
            
            # Replot original data
            self._plotSpectraWindow.clearCurves()
            for curve in old_curves:
                x, y, legend, info = curve
                legend = info['selectionlegend']
                self._plotSpectraWindow.addCurve(x, y, legend, info, 
                    xlabel=info['xlabel'], ylabel=info['ylabel'])
        else:
            llist, ldict = self.aasp.calculateShifts()
        
        if llist[0] == 'Average Y':
            ldict.pop(llist[0])
            llist = llist[1:]
        
        spec_num = np.arange(len(llist))
        spec_shift = np.array([ldict[s] for s in llist])
        self._plotShiftsWindow.addCurve(
            spec_num+1, spec_shift, 'Shifts'+label, ylabel='Shift', symbol='o')
        return llist, ldict
    
    
    
    def calculateTrend(self):
        curve = self._plotShiftsWindow.getCurve('Shifts')
        if curve:
            x, y, legend, info = curve
            # ~ if self.trendSpline.isChecked():
                # ~ trend = interpolate.UnivariateSpline(x, y)(x)
            if self.trendPoly.isChecked():
                order = self.trendPolyOrder.value()
                trend = np.polyval(np.polyfit(x, y, order), x)
            else:
                width = self.trendAvgWidth.value()
                trend = self.RTB_Math.gaussian_filter(y, width)
            self._plotShiftsWindow.addCurve(x, trend, 'Trend', color='red')
        return 0
        
    
    
    def calcButtonClicked(self):
        # ~ curves = copy.deepcopy(self._plotSpectraWindow.getAllCurves())
        # ~ legends = copy.deepcopy(self._plotSpectraWindow.getAllCurves(just_legend=True))
        curves = self._plotSpectraWindow.getAllCurves()
        legends = self._plotSpectraWindow.getAllCurves(just_legend=True)
        
        
        # Check if there are at least two scans
        if len(legends) < 2:
            return
        # Set zoom to alignment window
        xlimits = self._plotSpectraWindow.getGraphXLimits()
        self._plotSpectraWindow.setGraphXLimits(
            self._minSpinBox.value(), self._maxSpinBox.value())
        self._plotSpectraWindow.replot()
        # Calculate shifts using Advanced Alignment Plugin
        self.aasp = AdvancedAlignmentScanPlugin.AdvancedAlignmentScanPlugin(
            self._plotSpectraWindow)
        self.aasp.setShiftMethod('Shift x-range')
        self.aasp.setAlignmentMethod(self.methodComboBox.currentText())
        
        
        
        #self._plotShiftsWindow.clearCurves()
        
        if self.sumrefCheckBox.isChecked():
            llist, ldict = self.findShifts(curves, legends, label=' run 1')
            
            
            xvals = [c[0]+ldict[llist[i]] for i, c in enumerate(curves)]
            yvals = [c[1]+ldict[llist[i]] for i, c in enumerate(curves)]
            avgx, avgy = self.simpleMath.average(xvals, yvals)
            
            self._plotSpectraWindow.clearCurves()
            self._plotSpectraWindow.addCurve(avgx, avgy, 'Average')
            for i, curve in enumerate(curves):
                x, y, legend, info = curve
                self._plotSpectraWindow.addCurve(x, y, legend, info)
            
            newcurves = self._plotSpectraWindow.getAllCurves()
            newlegends = self._plotSpectraWindow.getAllCurves(just_legend=True)
            
            newllist, newldict = self.findShifts(newcurves, newlegends, 
                label=' run2')
            
            for i, s in enumerate(llist):
                ldict[s] = newldict[newllist[i]]
        #~ else:
            #~ llist, ldict = self.findShifts(curves, legends)
        
        self.llist, self.ldict = self.findShifts(curves, legends)
        self.alignButton.setEnabled(True)
        
        self._plotSpectraWindow.setGraphXLimits(*xlimits)
        self._plotSpectraWindow.replot()
        
        if self.trendCheckBox.isChecked():
            self.calculateTrend()
        
        self.calcButton.setEnabled(False)
        
        spec_num = np.arange(len(self.llist))
        spec_shift = np.array([self.ldict[s] for s in self.llist])
        if 0:
            np.savetxt('shifts.txt', np.vstack([spec_num, spec_shift]).T)
    
    
    
    def alignButtonClicked(self):
        llist, ldict = self.llist, self.ldict
        
        
        if self.trendCheckBox.isChecked():
            trend = self._plotShiftsWindow.getCurve('Trend')
            if trend:
                for i, s in enumerate(llist):
                    ldict[s] = trend[1][i]
        
        
        #~ shifts = np.array([ldict[i] for i in llist])
        #~ print shifts
        #~ np.savetxt('T:/kurt/shifts.txt', shifts)
        
        
        # ~ curves = copy.deepcopy(self._plotSpectraWindow.getAllCurves())
        # ~ legends = copy.deepcopy(self._plotSpectraWindow.getAllCurves(just_legend=True))
        curves = self._plotSpectraWindow.getAllCurves()
        legends = self._plotSpectraWindow.getAllCurves(just_legend=True)
        
        xlimits = self._plotSpectraWindow.getGraphXLimits()
        
        #~ print (self._plotShiftsWindow.getAllCurves(just_legend=True))
        
        # Align scans
        
        
        self.alignedScans = []
        self.shifts = []
        self.shiftedScans = []
        sourcenames = [s.sourceName[0] for s in self._sourceWidget.sourceList]
        for i, legend in enumerate(llist):
            scaninfo = curves[i][3]
            
            sourceindex = sourcenames.index(scaninfo['FileName'])
            info_key = scaninfo['selectionlegend'].split(' ')[-1]
            dataObject = self._sourceWidget.sourceList[sourceindex].getDataObject(info_key)
            newdataObject = copy.deepcopy(dataObject)
            
            xindex = scaninfo['selection']['x'][0]
            yindex = scaninfo['selection']['y'][0]
            newdataObject.data[:, xindex] += ldict[legend]
            
            
            if i == 0:
                first_scan = '%s:%s' % (
                    newdataObject.info['FileName'].split('/')[-1],
                    newdataObject.info['Key'])
                newdataObject.info['Command'] = '%s' % first_scan
                refscan = legend
            else:
                newdataObject.info['Command'] = '%s:%s aligned to %s' % (
                    newdataObject.info['FileName'].split('/')[-1],
                    newdataObject.info['Key'],
                    first_scan)
                newdataObject.info['Header'].insert(-2, '#C  %s aligned to %s' % (legend, refscan))
                newdataObject.info['Header'].insert(-2, '#C  Shift:  %f' % (ldict[legend]))
            
            self.shifts.append(ldict[legend])
            self.shiftedScans.append(legend)
            
            if i == 0:
                newlegend = legend
            else:
                newlegend = ''.join([legend, ' ALIGNED'])
            self.alignedScans.append( {
                'dataObject': newdataObject,
                'xLabel': scaninfo['selection']['cntlist'][xindex], 
                'yLabel': scaninfo['selection']['cntlist'][yindex], 
                'Shift': ldict[legend],
                'Legend': newlegend,
                'oldLegend': legend,
                'info': scaninfo,
                'Name': ' '.join([
                    scaninfo['SourceName'][0].split('/')[-1], scaninfo['Key']])}
                    )
        
        self._plotSpectraWindow.clearCurves()
        
        for i, scan in enumerate(self.alignedScans):
            newdataObject = self.alignedScans[i]['dataObject']
            self._plotSpectraWindow.addCurve(
                newdataObject.data[:,xindex],
                newdataObject.data[:,yindex], 
                self.alignedScans[i]['Legend'], 
                self.alignedScans[i]['info'], 
                xlabel=self.alignedScans[i]['xLabel'],
                ylabel='',
                replot=False)
        #~ self._plotSpectraWindow.removeCurves(llist[1:], replot=True)
        
        # Reset zoom
        print(dir(self._plotSpectraWindow))
        if self._plotSpectraWindow.isXAxisAutoScale():
            self._plotSpectraWindow.setGraphXLimits(*xlimits)
        self._plotSpectraWindow.replot()
        
        self.alignButton.setDisabled(True)
        self.calcButton.setDisabled(True)
        self._sourceWidget.selectorWidget['SpecFile'].addButton.setDisabled(True)
        self._sourceWidget.selectorWidget['SpecFile'].removeButton.setDisabled(True)
        self.whichButtonClicked = 'ALIGN'
        
        self.saveButton.setEnabled(True)
        
        return
    
    
    
    
    def sumButtonClicked(self):
        sourcenames = [s.sourceName[0] for s in self._sourceWidget.sourceList]
        curves = self._plotSpectraWindow.getAllCurves()
        if len(curves) < 1:
            print ('No curves')
            return
        
        
        self.calcButton.setDisabled(True)
        self.alignButton.setDisabled(True)
        self.sumButton.setDisabled(True)
        self.sumButton.setToolTip('Spectra can be summed only once.\nReplace the spectra to sum again.')
        self._sourceWidget.selectorWidget['SpecFile'].addButton.setDisabled(True)
        self._sourceWidget.selectorWidget['SpecFile'].removeButton.setDisabled(True)
        self.whichButtonClicked = 'SUM'
        
        motors = {}
        
        xlimits = self._plotSpectraWindow.getGraphXLimits()
        curves2sum = []
        for i, curve in enumerate(curves):
            x, y, legend, info = curve
            legend = legend.rstrip()
            if self.shiftedScans != None:
                alignedScans = [alignedScan['Legend'] for alignedScan in self.alignedScans]
                if legend in alignedScans:
                    idx = alignedScans.index(legend)
                    dataObject = self.alignedScans[idx]['dataObject']
                else:
                    sourceindex = sourcenames.index(info['FileName'])
                    info_key = info['selectionlegend'].split(' ')[-1]
                    dataObject = self._sourceWidget.sourceList[sourceindex].getDataObject(info_key)
            else:
                sourceindex = sourcenames.index(info['FileName'])
                dataObject = self._sourceWidget.sourceList[sourceindex].getDataObject(info['Key'])
            
            ylabels = [] + dataObject.info['LabelNames']
            ylabels.remove(info['xlabel'])
            if i == 0:
                columns2sum = set(ylabels)
            else:
                columns2sum = columns2sum & set(ylabels)
            curves2sum.append({
                'dataObject': dataObject, 'xlabel': info['xlabel'], 
                    'ylabel': info['ylabel']})
            
            # Transfer motor names and positions
            if info['MotorValues']:
                if i == 0:
                    mnames = info['MotorNames']
                    mvalues = [str(mv) for mv in info['MotorValues']]
                else:
                    for j, m in enumerate(info['MotorNames']):
                        if m in mnames:
                            if str(info['MotorValues'][j]) != mvalues[mnames.index(m)]:
                                mvalues[mnames.index(m)] = '-999999999'
                                #~ mvalues.pop(mnames.index(m))
                                #~ mnames.remove(m)
            else:
                mnames = []
                mvalues = []
        
        
        newcolsnames = []
        newcols = []
        scale = len(curves2sum)
        for i, col in enumerate(columns2sum):
            xvals = [c2s['dataObject'].data[:,
                c2s['dataObject'].info['LabelNames'].index(c2s['xlabel'])] 
                for c2s in curves2sum]
            yvals = [c2s['dataObject'].data[:,
                c2s['dataObject'].info['LabelNames'].index(col)] 
                for c2s in curves2sum]
            newx, newy = self.simpleMath.average(xvals, yvals)
            newy *= scale
            if i == 0:
                newcols.append(newx)
                newcolsnames.append(curves2sum[0]['xlabel'])
            newcols.append(newy)
            newcolsnames.append(col)
        newcols = np.array(newcols).T
        newdataObject = copy.deepcopy(curves2sum[0]['dataObject'])
        newdataObject.info['LabelNames'] = newcolsnames
        newdataObject.data = newcols
        
        
        # Create header for summed data
        newdataObject.info['Command'] = 'Sum %s to %s' % (
            curves2sum[0]['dataObject'].info['Command'].split('-')[0].strip(),
            curves2sum[-1]['dataObject'].info['Command'].split('-')[0].strip())
        
        
        header = []
        header.append('#D  %s\n' % time.strftime('%Y-%m-%d %H:%M:%S', 
            time.localtime(time.time())))
        header.append('#C  Sum of:')
        if self.shiftedScans != None:
            for i, scan in enumerate(self.shiftedScans):
                header.append('#C  %s shifted by %f' % (scan, self.shifts[i]))
                ylabel = self.alignedScans[0]['yLabel']
        else:
            for i, scan in enumerate(curves2sum):
                header.append('#C  %s:%s' % (
                    curves2sum[i]['dataObject'].info['FileName'].split('/')[-1],
                    curves2sum[i]['dataObject'].info['Key']))
                ylabel = curves2sum[0]['ylabel']
        
        # Motors
        motor_mne_lines = []
        motor_pos_lines = []
        for iii in range(len(mnames)//8):
            motor_mne_lines.append(
                '  '.join(['#O%d' % iii] + mnames[8*iii:8*(iii+1)]))
            motor_pos_lines.append(
                '  '.join(['#P%d' % iii] + mvalues[8*iii:8*(iii+1)]))
        if len(mnames) % 8 != 0:
            iii = len(mnames)//8
            motor_mne_lines.append(
                '  '.join(['#O%d' % iii] + mnames[8*iii:]))
            motor_pos_lines.append(
                '  '.join(['#P%d' % iii] + mvalues[8*iii:]))
        header.append('\n'.join(motor_mne_lines) + '\n')
        header.append('\n'.join(motor_pos_lines) + '\n')
        
        
        
        header.append('#N  %d' % (len(newdataObject.info['LabelNames'])))
        header.append('#L  %s' % ('  '.join(newdataObject.info['LabelNames'])))
        newdataObject.info['Header'] = header
        
        
        
        self.shiftedScans != None
        
        
        
        idx = newdataObject.info['LabelNames'].index(ylabel)
        self._plotSpectraWindow.addCurve(
            newdataObject.data[:,0],
            newdataObject.data[:,idx], 
            'Sum', curves[0][3], 
            xlabel='',
            ylabel='',
            symbol='.',
            replot=True)
        
        
        # Reset zoom
        self._plotSpectraWindow.setGraphXLimits(*xlimits)
        self._plotSpectraWindow.replot()
        self._plotSpectraWindow.setActiveCurve('Sum')
        
        self.summedSpectra = newdataObject
        
        
        return 0
    
    
    
    def _sumSpectra(self):
    #~ def average(self, xarr, yarr, x=None):
        """
        :param xarr : List containing x values in 1-D numpy arrays
        :param yarr : List containing y Values in 1-D numpy arrays
        :param x: x values of the final average spectrum (or None)
        :return: Average spectrum. In case of invalid input (None, None) tuple is returned.

        From the spectra given in xarr & yarr, the method determines the overlap in
        the x-range. For spectra with unequal x-ranges, the method interpolates all
        spectra on the values given in x if provided or the first curve and averages them.
        """
        if (len(xarr) != len(yarr)) or\
           (len(xarr) == 0) or (len(yarr) == 0):
            if DEBUG:
                print('specAverage -- invalid input!')
                print('Array lengths do not match or are 0')
            return None, None

        same = True
        if x == None:
            SUPPLIED = False
            x0 = xarr[0]
        else:
            SUPPLIED = True
            x0 = x
        for x in xarr:
            if len(x0) == len(x):
                if numpy.all(x0 == x):
                    pass
                else:
                    same = False
                    break
            else:
                same = False
                break

        xsort = []
        ysort = []
        for (x,y) in zip(xarr, yarr):
            if numpy.all(numpy.diff(x) > 0.):
                # All values sorted
                xsort.append(x)
                ysort.append(y)
            else:
                # Sort values
                mask = numpy.argsort(x)
                xsort.append(x.take(mask))
                ysort.append(y.take(mask))

        if SUPPLIED:
            xmin0 = x0.min()
            xmax0 = x0.max()
        else:
            xmin0 = xsort[0][0]
            xmax0 = xsort[0][-1]
        if (not same) or (not SUPPLIED):
            # Determine global xmin0 & xmax0
            for x in xsort:
                xmin = x.min()
                xmax = x.max()
                if xmin > xmin0:
                    xmin0 = xmin
                if xmax < xmax0:
                    xmax0 = xmax
            if xmax <= xmin:
                if DEBUG:
                    print('specAverage -- ')
                    print('No overlap between spectra!')
                return numpy.array([]), numpy.array([])

        
        
        
        return 0
    
    
    def saveButtonClicked(self):
        
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
        
        
        
        if self.whichButtonClicked == 'SUM':
            dataObjects = [self.summedSpectra]
        elif self.whichButtonClicked == 'ALIGN':
            dataObjects = [alignedScan['dataObject'] for alignedScan in self.alignedScans]
        else:
            return 0
        
        
        for dataObject in dataObjects:
            output = []
            
            command = dataObject.info['Command']
            if self._exportWidget.askForScanName():
                command = self._exportWidget.getScanName(command)
            if not command:
                command = dataObject.info['Command']
            
            output.append('#S %d  %s\n' % (scannumber, command))
            header = dataObject.info['Header']
            for item in header:
                if item.startswith('#S'):
                    continue
                output.append(''.join([item, '\n']))
            
            output.append(''.join('%s\n' % (' '.join([str(si) for si in s])) 
                for s in dataObject.data.tolist()))
            output.append('\n')
            
            
            with open('%s' % (specfilename), 'ab+') as f:
                f.write(''.join(output).encode('ascii'))
            print('Spectrum saved to \"%s\"' % (specfilename))
            
            key = SpecFileDataSource(specfilename).getSourceInfo()['KeyList'][-1]
            
            if self._exportWidget._datCheckBox.isChecked():
                command = command.replace(':','_').replace(' ', '_')
                if not os.path.isdir(specfilename.rstrip('.spec')):
                    os.mkdir(specfilename.rstrip('.spec'))
                datfilename = '%s/S%04d_%s_%s.dat' % (specfilename.rstrip('.spec'),
                    scannumber, key.split('.')[-1], command)
                np.savetxt('%s' % (datfilename), dataObject.data)
                print('Spectrum saved to \"%s\"\n' % (datfilename))
            
            #~ scannumber +=1
        
        if self.whichButtonClicked == 'SUM':
            self.saveButton.setDisabled(True)
        
        return 0



if __name__ == "__main__":
    import numpy as np
    
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)
    # ~ if 'Fusion' in qt.QStyleFactory.keys():
        # ~ app.setStyle('Fusion')

    w = MainWindow()
    w.show()
    app.exec_()


