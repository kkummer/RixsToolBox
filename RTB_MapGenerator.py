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
from PyMca5.PyMcaCore import DataObject
from PyMca5.PyMcaGui import IconDict
from PyMca5.PyMcaGui.plotting import ColormapDialog

from RTB_SpecGen import ExportWidget
from RTB_Icons import RtbIcons
from RTB_Math import RTB_Math



class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('RixsToolBox - Map generator')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.build()
        self.connect_signals()
        
        self.xvals = []
        self.yvals = []
        self.qvals = []
        
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
        
        
        self._sourceWidget.selectorWidget['SpecFile'].addButton.setText('Add to map')
        self._sourceWidget.selectorWidget['SpecFile'].replaceButton.hide()
        self._sourceWidget.selectorWidget['SpecFile'].removeButton.hide()
        
        
        
        self._exportWidget = ExportWidget()
        
        
        self.mapPlotWindow = PlotWindow.PlotWindow(
            parent=self, backend=None, plugins=False, newplot=False, roi=False, 
            control=False, position=True, info=False, fit=False, logx=False, 
            logy=False, save=False, togglePoints=False)
        self.mapPlotWindow.enableActiveCurveHandling(False)
        self.mapPlotWindow.enableOwnSave(False)
        
        
        #~ self.colormapDialog = ColormapDialog.ColormapDialog(self)
        self.colormapDialog = MyColormapDialog(self)
        
        
        
        self.colormapButton = qt.QPushButton()
        self.colormapButton.setMinimumSize(25, 25)
        self.colormapButton.setMaximumSize(25, 25)
        self.colormapButton.setIcon(qt.QIcon(qt.QPixmap(IconDict['colormap'])))
        self.colormapButton.setToolTip('Colormap dialog')
        
        self.updateMapButton = qt.QPushButton()
        self.updateMapButton.setMinimumSize(25, 25)
        self.updateMapButton.setMaximumSize(25, 25)
        self.updateMapButton.setIcon(qt.QIcon(qt.QPixmap(IconDict['reload'])))
        self.updateMapButton.setToolTip('Update map')
        
        
        
        self.waterfallPlotWindow = ScanWindow.ScanWindow(
            parent=self, backend=None, plugins=False,roi=False, 
            control=False, position=True, info=False, fit=False)
        # ~ self.waterfallPlotWindow.enableOwnSave(False)
        
        
        self.minSpinBox = MarkerSpinBox(self, self.waterfallPlotWindow, 'min')
        self.minSpinBox.setMaximumWidth(100)
        self.minSpinBox.setMinimumWidth(70)
        self.minSpinBox.setAlignment(qt.Qt.AlignRight)
        self.minSpinBox.setMinimum(-100000)
        self.minSpinBox.setMaximum(100000)
        self.minSpinBox.setDecimals(2)
        self.minSpinBox.setSingleStep(1)
        self.minSpinBox.setValue(0)
        self.minSpinBox.setEnabled(False)
        self.minSpinBox.hideMarker()
        
        self.maxSpinBox = MarkerSpinBox(self, self.waterfallPlotWindow, 'max')
        self.maxSpinBox.setMaximumWidth(100)
        self.maxSpinBox.setMinimumWidth(70)
        self.maxSpinBox.setAlignment(qt.Qt.AlignRight)
        self.maxSpinBox.setMinimum(-100000)
        self.maxSpinBox.setMaximum(100000)
        self.maxSpinBox.setDecimals(2)
        self.maxSpinBox.setSingleStep(1)
        self.maxSpinBox.setValue(0)
        self.maxSpinBox.setEnabled(False)
        self.maxSpinBox.hideMarker()
        
        
        self.normaliseCheckBox = qt.QCheckBox('Normalise to intensity between')
        self.normaliseCheckBox.setChecked(False)
        
        self.normaliseMethodComboBox = qt.QComboBox(self)
        self.normaliseMethodComboBox.addItem('average')
        self.normaliseMethodComboBox.addItem('maximum')
        self.normaliseMethodComboBox.setMaximumWidth(70)
        self.normaliseMethodComboBox.setMinimumWidth(70)
        self.normaliseMethodComboBox.setEnabled(False)
        
        normaliseLayout = qt.QHBoxLayout(self)
        normaliseLayout.addWidget(self.normaliseCheckBox)
        normaliseLayout.addWidget(self.minSpinBox)
        normaliseLayout.addWidget(qt.QLabel('and'))
        normaliseLayout.addWidget(self.maxSpinBox)
        normaliseLayout.addWidget(qt.QLabel('using the'))
        normaliseLayout.addWidget(self.normaliseMethodComboBox)
        normaliseLayout.addWidget(qt.HorizontalSpacer())
        normaliseLayout.setContentsMargins(0, 0, 0, 0)
        self.normaliseWidget = qt.QWidget(self)
        self.normaliseWidget.setLayout(normaliseLayout)
        
        
        self.dummyPlotWindow = ScanWindow.ScanWindow(
            parent=self, backend=None, plugins=True, roi=False, 
            control=False, position=True, info=False)
        
        
        #~ self._plotSpectraWindow.graph.enablemarkermode()
        #~ self._plotSpectraWindow.enableActiveCurveHandling(False)
        #~ if hasattr(self._plotSpectraWindow, '_buildLegendWidget'):
            #~ self._plotSpectraWindow._buildLegendWidget()
        
        
        
        
        
        self.integralPlotWindow = ScanWindow.ScanWindow(
            parent=self, backend=None, plugins=True, roi=False, 
            control=True, position=True, info=False, fit=True, 
            save=False)
        self.integralPlotWindow.enableActiveCurveHandling(True)
        
        
        
        
        
        
        
        
        self.saveButton = qt.QPushButton('Save')
        self.saveButton.setMinimumSize(75,75)
        self.saveButton.setMaximumSize(75,75)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.saveButton.setDisabled(True)
        self.saveButton.setToolTip('Select output file\nto enable saving')
        
        
        
        
        
        
        self.xAxisBox = qt.QGroupBox('Plot against')
        self.xAxisH = qt.QRadioButton('H', checked=False)
        self.xAxisK = qt.QRadioButton('K', checked=False)
        self.xAxisL = qt.QRadioButton('L', checked=False)
        self.xAxisM = qt.QRadioButton('motor position', checked=False)
        self.xAxisQ = qt.QRadioButton('custom Q', checked=True)
        self.xAxisGroup = qt.QButtonGroup()
        self.xAxisGroup.addButton(self.xAxisH)
        self.xAxisGroup.addButton(self.xAxisK)
        self.xAxisGroup.addButton(self.xAxisL)
        self.xAxisGroup.addButton(self.xAxisM)
        self.xAxisGroup.addButton(self.xAxisQ)
        self.xAxisMotorComboBox = qt.QComboBox()
        xAxisLayout = qt.QGridLayout()
        xAxisLayout.addWidget(self.xAxisH, 0, 0, 1, 1)
        xAxisLayout.addWidget(self.xAxisK, 1, 0, 1, 1)
        xAxisLayout.addWidget(self.xAxisL, 2, 0, 1, 1)
        xAxisLayout.addWidget(self.xAxisM, 3, 0, 1, 1)
        xAxisLayout.addWidget(self.xAxisMotorComboBox, 3, 1, 1, 1)
        xAxisLayout.addWidget(self.xAxisQ, 4, 0, 1, 1)
        xAxisLayout.addWidget(qt.VerticalSpacer(), 5, 0, 1, 1)
        self.xAxisBox.setLayout(xAxisLayout)
        self.xAxisBox.setMaximumWidth(250)
        
        
        
        
        
        
        
        
        self.offsetSpinBox = qt.QDoubleSpinBox()
        self.offsetSpinBox.setMaximumWidth(100)
        self.offsetSpinBox.setMinimumWidth(70)
        self.offsetSpinBox.setAlignment(qt.Qt.AlignRight)
        self.offsetSpinBox.setMinimum(1e-2)
        self.offsetSpinBox.setMaximum(1e6)
        self.offsetSpinBox.setSingleStep(1)
        self.offsetSpinBox.setDecimals(5)
        self.offsetSpinBox.setValue(1)
        self.offsetLayout = qt.QHBoxLayout()
        self.offsetLayout.addWidget(qt.QLabel('Offset between spectra'))
        self.offsetLayout.addSpacing(20)
        self.offsetLayout.addWidget(self.offsetSpinBox)
        self.offsetLayout.addWidget(qt.HorizontalSpacer())
        self.offsetWidget = qt.QWidget()
        self.offsetWidget.setLayout(self.offsetLayout)
        
        self.waterfallWidget = qt.QWidget()
        self.waterfallLayout = qt.QVBoxLayout()
        self.waterfallLayout.addWidget(self.waterfallPlotWindow)
        self.waterfallLayout.addWidget(self.offsetWidget)
        self.waterfallLayout.addWidget(self.normaliseWidget)
        self.waterfallWidget.setLayout(self.waterfallLayout)
        
        
        self.interpolationComboBox = qt.QComboBox()
        self.interpolationComboBox.addItem('nearest')
        self.interpolationComboBox.addItem('linear')
        #~ self.interpolationComboBox.addItem('cubic')
        self.interpolationLayout = qt.QHBoxLayout()
        self.interpolationLayout.addWidget(qt.QLabel('Interpolation'))
        self.interpolationLayout.addSpacing(10)
        self.interpolationLayout.addWidget(self.interpolationComboBox)
        self.interpolationLayout.addSpacing(25)
        self.interpolationLayout.addWidget(self.colormapButton)
        self.interpolationLayout.addWidget(qt.HorizontalSpacer())
        self.interpolationLayout.addWidget(self.updateMapButton)
        self.interpolationWidget = qt.QWidget()
        self.interpolationWidget.setLayout(self.interpolationLayout)
        
        
        
        self.integralTable = IntegralTable(self)
        self.integralTable.setMaximumWidth(170)
        self.integralTable.setMinimumHeight(325)
        self.integralTable.setMaximumHeight(325)
        
        
        self.mapWidget = qt.QWidget()
        self.mapLayout = qt.QVBoxLayout()
        self.mapLayout.addWidget(self.dummyPlotWindow)
        self.mapLayout.addWidget(self.mapPlotWindow)
        self.mapLayout.addWidget(self.interpolationWidget)
        self.mapWidget.setLayout(self.mapLayout)
        self.dummyPlotWindow.hide()
        
        
        self.integralMethodBox = qt.QGroupBox('Plot')
        self.integralMethodIntegral = qt.QRadioButton('Integral', checked=True)
        self.integralMethodMean = qt.QRadioButton('Mean value', checked=False)
        self.integralMethodGroup = qt.QButtonGroup()
        self.integralMethodGroup.addButton(self.integralMethodIntegral)
        self.integralMethodGroup.addButton(self.integralMethodMean)
        self.integralMethodLayout = qt.QVBoxLayout()
        self.integralMethodLayout.addWidget(self.integralMethodIntegral)
        self.integralMethodLayout.addWidget(self.integralMethodMean)
        self.integralMethodBox.setLayout(self.integralMethodLayout)
        self.integralMethodBox.setMaximumWidth(170)
        
        self.integralTableWidget = qt.QWidget()
        self.integralTableWidgetLayout = qt.QVBoxLayout()
        self.integralTableWidgetLayout.addWidget(qt.VerticalSpacer())
        self.integralTableWidgetLayout.addWidget(self.integralTable)
        #~ hint = '\n'.join(['If [Ref] is given integrals [1]...[9]',
            #~ ' will be normalised to integral [Ref].'])
        #~ hintLabel = qt.QLabel(hint, font=qt.QFont("SansSerif", 8))
        #~ self.integralTableWidgetLayout.addWidget(hintLabel)
        self.integralTableWidgetLayout.addSpacing(20)
        self.integralTableWidgetLayout.addWidget(self.integralMethodBox)
        self.integralTableWidgetLayout.addWidget(qt.VerticalSpacer())
        self.integralTableWidget.setLayout(self.integralTableWidgetLayout)
        
        
        self.integralWidget = qt.QWidget()
        self.integralLayout = qt.QHBoxLayout()
        self.integralLayout.addWidget(self.integralPlotWindow, 3)
        self.integralLayout.addWidget(self.integralTableWidget, 1)
        self.integralWidget.setLayout(self.integralLayout)
        
        
        self.tabWidget = qt.QTabWidget()
        self.tabWidget.addTab(self.waterfallWidget, 'Waterfall plot')
        self.tabWidget.addTab(self.mapWidget, 'Map')
        self.tabWidget.addTab(self.integralWidget, 'Integrals')
        
        
        
        
        self.table = SelectionTable(self)
        
        
        self.tableLayout = qt.QHBoxLayout()
        self.tableLayout.addWidget(self.table,3)
        self.tableLayout.addWidget(self.xAxisBox,1)
        self.tableWidget = qt.QGroupBox('Source spectra')
        self.tableWidget.setLayout(self.tableLayout)
        
        
        
        rsLayout = qt.QGridLayout(self)
        rsLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        rsLayout.addWidget(self.tableWidget, 1, 0, 1, 1)
        rsWidget = qt.QWidget()
        rsWidget.setContentsMargins(0,0,0,-8)
        rsWidget.setLayout(rsLayout)
        
                
        self._lsLayout = qt.QVBoxLayout(self)
        self._lsLayout.addWidget(self._sourceWidget)
        self._lsLayout.addWidget(self._exportWidget)
        self._lsWidget = qt.QWidget()
        self._lsWidget.setContentsMargins(0,0,0,-8)
        self._lsWidget.setSizePolicy(
            qt.QSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Preferred))
        self._lsWidget.setLayout(self._lsLayout)
        self._lsWidget.setMaximumWidth(500)
        
        self._exportWidget.hide()
        
        self.splitter = qt.QSplitter(self)
        self.splitter.setOrientation(qt.Qt.Horizontal)
        self.splitter.setHandleWidth(5)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.addWidget(self._lsWidget)
        self.splitter.addWidget(rsWidget)
        
        self._mainLayout = qt.QHBoxLayout()
        self._mainLayout.addWidget(self.splitter)
        self.setLayout(self._mainLayout)
        
        
        
        
        
        
        return 0
    
    
    
    
    
    
    def connect_signals(self):
        self._sourceWidget.sigAddSelection.connect(self.addSpectra)
        
        self._exportWidget.OutputFileSelected.connect(self._enableSaveButton)
        
        
        
        
        self._sourceWidget.selectorWidget['SpecFile'].cntTable.sigSpecFileCntTableSignal.connect(self.update_yselection)
        
        self.xAxisMotorComboBox.activated.connect(self.updatePlots)
        self.table.tableChanged.connect(self.updatePlots)
        self.integralTable.itemChanged.connect(self.integralsChanged)
        self.integralTable.tableChanged.connect(self.integralsChanged)
        self.integralMethodGroup.buttonClicked.connect(self.integralsChanged)
        self.xAxisGroup.buttonClicked.connect(self.updatePlots)
        self.offsetSpinBox.valueChanged.connect(self.updatePlots)

        self.colormapButton.clicked.connect(self.selectColormap)
        self.normaliseCheckBox.stateChanged.connect(self.setNormalisation)
        self.normaliseMethodComboBox.currentIndexChanged.connect(self.updatePlots)
        self.minSpinBox.valueChanged.connect(self.updatePlots)
        self.minSpinBox.intersectionsChangedSignal.connect(self.updatePlots)
        self.maxSpinBox.valueChanged.connect(self.updatePlots)
        self.maxSpinBox.intersectionsChangedSignal.connect(self.updatePlots)
        
        self.interpolationComboBox.currentIndexChanged.connect(self.updateMap)
        self.colormapDialog.sigColormapChanged.connect(self.updateMap)
        self.updateMapButton.clicked.connect(self.updateMap)
        
        self.mapPlotWindow.sigIconSignal.connect(self.saveMap)
        
        return 0
    
    
    def integralsChanged(self):
        self.integralLimits = []
        for row in range(self.integralTable.rowCount()-1):
            if self.integralTable.item(row, 0) \
                    and self.integralTable.item(row, 1):
                try:
                    limit_1 = float(self.integralTable.item(row, 0).text())
                    limit_2 = float(self.integralTable.item(row, 1).text())
                    self.integralLimits.append(
                        [row, min([limit_1, limit_2]), max([limit_1, limit_2])])
                except ValueError:
                    pass
        if not self.integralLimits or not self.qvals:
            return
        self.integralPlotWindow.clearCurves()
        for limit in self.integralLimits:
            yint = []
            xint = []
            for i, qval in enumerate(self.qvals):
                xint.append(qval)
                if self.integralMethodIntegral.isChecked():
                    yint.append(self.yvals[i][
                        np.argwhere(self.xvals[i]>=limit[1])[0][0]: \
                        np.argwhere(self.xvals[i]<=limit[2])[-1][0]].sum())
                else:
                    yint.append(self.yvals[i][
                        np.argwhere(self.xvals[i]>=limit[1])[0][0]: \
                        np.argwhere(self.xvals[i]<=limit[2])[-1][0]].mean())
                int2plot = np.vstack([xint, yint]).T
                int2plot = int2plot[int2plot[:,0].argsort()]
            self.integralPlotWindow.addCurve(int2plot[:,0], int2plot[:,1], 
                legend='Region %d' % (limit[0]+1), ylabel=' ',
                symbol='o')
        return
    
    def setNormalisation(self):
        if self.normaliseCheckBox.isChecked():
            self.minSpinBox.setEnabled(True)
            self.minSpinBox.showMarker()
            self.maxSpinBox.setEnabled(True)
            self.maxSpinBox.showMarker()
            self.normaliseMethodComboBox.setEnabled(True)
            if self.minSpinBox.value() == 0 and self.maxSpinBox.value() == 0:
                xlimits = self.waterfallPlotWindow.getGraphXLimits()
                self.maxSpinBox.setValue(xlimits[0]+0.9*(xlimits[1]-xlimits[0]))
                self.minSpinBox.setValue(xlimits[0]+0.1*(xlimits[1]-xlimits[0]))
        else:
            self.minSpinBox.setEnabled(False)
            self.minSpinBox.hideMarker()
            self.maxSpinBox.setEnabled(False)
            self.maxSpinBox.hideMarker()
            self.normaliseMethodComboBox.setEnabled(False)
        self.updatePlots()
            
    
    
    def update_yselection(self):
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
    
    
    def shiftSpinBoxChanged(self):
        self.preprocessCurves(shift=True)
    
    
    def rescaleSpinBoxChanged(self):
        self.preprocessCurves(rescale=True)
    
    
    def addSpectra(self, selectionlist):
        self.dummyPlotWindow._addSelection(selectionlist)
        curves = self.dummyPlotWindow.getAllCurves()
        self.dummyPlotWindow.clearCurves()
        self.table.update(curves=curves)
    
    
    
    def updatePlots(self):
        print(self.table.motorNames)
        
        # Update list of motor names
        currentMotor = self.xAxisMotorComboBox.currentText()
        self.xAxisMotorComboBox.clear()
        self.xAxisMotorComboBox.addItems(self.table.motorNames)
        if currentMotor:
            print(currentMotor, self.table.motorNames)
            self.xAxisMotorComboBox.setCurrentIndex(
                self.table.motorNames.index(currentMotor))
        
        # Update motor positions
        currentMotor = self.xAxisMotorComboBox.currentText()
        if currentMotor:
            for ii in range(len(self.table.spectra.keys())):
                spectrum = self.table.spectra[self.table.item(ii, 0).text()]
                if currentMotor in spectrum['MotorNames']:
                    motorvalue = float(spectrum['MotorValues'][
                                spectrum['MotorNames'].index(currentMotor)])
                else:
                    motorvalue = np.nan
                self.table.setItem(ii, 4, qt.QTableWidgetItem(str(motorvalue)))
                spectrum['hklmq'][3] = motorvalue
        
        # PLOT WATERFALL
        self.waterfallPlotWindow.clearCurves()
        offset = self.offsetSpinBox.value()
        self.xvals, self.yvals, self.qvals = [], [], []
        
        if self.xAxisH.isChecked():
            ind = 0
        if self.xAxisK.isChecked():
            ind = 1
        if self.xAxisL.isChecked():
            ind = 2
        if self.xAxisM.isChecked():
            ind = 3
        if self.xAxisQ.isChecked():
            ind = 4
        
        for legend, spectrum in self.table.spectra.items():
            x = 1.*spectrum['x']
            y = 1.*spectrum['y']
            if self.normaliseCheckBox.isChecked():
                imin = np.argwhere(x>=self.minSpinBox.value())[0][0]
                imax = np.argwhere(x<=self.maxSpinBox.value())[-1][0]
                if self.normaliseMethodComboBox.currentText() == 'average':
                    y /= y[imin:imax].mean()
                else:
                    y /= y[imin:imax].max()
            self.waterfallPlotWindow.addCurve(x, y/offset+spectrum['hklmq'][ind],
                legend=legend, ylabel='Q')
            self.xvals.append(x)
            
            self.qvals.append(spectrum['hklmq'][ind])
            self.yvals.append(y)
        self.waterfallPlotWindow.setGraphYLabel('Q')
        self.integralsChanged()
    
    
    def updateMap(self):
        # PLOT MAP
        points = [np.vstack([x, self.qvals[i]*np.ones(len(x))]) for i, x in enumerate(self.xvals)]
        points = np.hstack(points).T
        values = np.hstack(self.yvals)
        # Interpolate data on grid
        oversamplingQ = 10
        grid_x, grid_y = np.mgrid[self.xvals[0][0]:self.xvals[0][-1]:len(self.xvals[0])*1j, 
                            min(self.qvals):max(self.qvals):oversamplingQ*len(self.qvals)*1j]
        self.grid_x = grid_x[:,0]
        self.grid_y = grid_y[0,:]
        # ~ self.grid_z = interpolate.griddata(points, values, (grid_x, grid_y), 
            # ~ method=self.interpolationComboBox.currentText(), fill_value=0)
        
        self.grid_z = self.RTB_Math.interpolate_on_grid(self.qvals, self.xvals,
                            self.yvals, (grid_x, grid_y), fill_value=None, 
                            method=self.interpolationComboBox.currentText())
        
        cm_name = self.colormapDialog.combo.currentText()
        cm_autoscale = self.colormapDialog.autoscale
        cm_min = self.colormapDialog.minValue
        cm_max = self.colormapDialog.maxValue
        
        colormap = {'name': cm_name, 'normalization':'linear', 'colors': 256,
                    'autoscale': cm_autoscale, 'vmin': cm_min, 'vmax': cm_max}
        
        self.mapPlotWindow.addImage(self.grid_z, colormap=colormap, yScale=[grid_x[0,0], (grid_x[-1,0]-grid_x[0,0])/len(grid_x[:,0])],
            xScale=[min(self.qvals), (max(self.qvals)-min(self.qvals))/len(self.qvals)/oversamplingQ])
        
        hist = np.histogram(self.grid_z, 10)
        self.colormapDialog.plotHistogram([0.5*(hist[1][1:]+hist[1][:-1]), hist[0]])
    
    
    def saveWaterfall(self, signal):
        if not signal['key'] == 'save':
            return
        
        # Get output filename
        outfile = qt.QFileDialog(self)
        outfile.setWindowTitle("Output File Selection")
        outfile.setModal(1)
        filterlist = ['*.png', '*.dat']
        if hasattr(outfile, "setFilters"):
            outfile.setFilters(filterlist)
        else:
            outfile.setNameFilters(filterlist)
        outfile.setFileMode(outfile.AnyFile)
        outfile.setAcceptMode(outfile.AcceptSave)
        ret = outfile.exec_()
        if not ret:
            return None
        if hasattr(outfile, "selectedFilter"):
            outputFilter = qt.safe_str(outfile.selectedFilter())
        else:
            outputFilter = qt.safe_str(outfile.selectedNameFilter())
        outputFile = qt.safe_str(outfile.selectedFiles()[0])
        outfile.close()
        del outfile
        extension = outputFilter[-4:]
        if len(outputFile) < 5:
            outputFile = outputFile + extension
        elif outputFile[-4:] != extension:
            outputFile = outputFile + extension
        if outputFile is None:
            return
        
        # Save map
        if extension == '.png':
            self.waterfallPlotWindow.saveGraph(outputFile, fileFormat='png', dpi=150)
            print('Plot saved to %s' % outputFile)
        elif extension == '.dat':
            for i, q in enumerate(sorted(self.qvals)):
                index = self.qvals.index(q)
                if i == 0:
                    x = self.xvals[index]
                    array2export = np.zeros((len(x), len(self.qvals)+1))
                    array2export[:,0] = x
                array2export[:,i+1] = np.interp(
                    x, self.xvals[index], self.yvals[index])
            header = '--- ' + ' '.join(np.asarray(sorted(self.qvals), dtype='string').tolist())
            np.savetxt(outputFile, array2export, fmt='%f', header=header)
            print('Data saved to %s' % outputFile)
        
        return
    
    
    def saveMap(self, signal):
        if not signal['key'] == 'save':
            return
        
        # Get output filename
        outfile = qt.QFileDialog(self)
        outfile.setWindowTitle("Output File Selection")
        outfile.setModal(1)
        filterlist = ['*.png', '*.dat']
        if hasattr(outfile, "setFilters"):
            outfile.setFilters(filterlist)
        else:
            outfile.setNameFilters(filterlist)
        outfile.setFileMode(outfile.AnyFile)
        outfile.setAcceptMode(outfile.AcceptSave)
        ret = outfile.exec_()
        if not ret:
            return None
        if hasattr(outfile, "selectedFilter"):
            outputFilter = qt.safe_str(outfile.selectedFilter())
        else:
            outputFilter = qt.safe_str(outfile.selectedNameFilter())
        outputFile = qt.safe_str(outfile.selectedFiles()[0])
        outfile.close()
        del outfile
        extension = outputFilter[-4:]
        if len(outputFile) < 5:
            outputFile = outputFile + extension
        elif outputFile[-4:] != extension:
            outputFile = outputFile + extension
        if outputFile is None:
            return
        
        # Save map
        if extension == '.png':
            self.mapPlotWindow.saveGraph(outputFile, fileFormat='png', dpi=150)
            print('Plot saved to %s' % outputFile)
        elif extension == '.dat':
            header = '--- ' + ' '.join(np.asarray(self.grid_y, dtype='string').tolist())
            array2export = np.vstack([self.grid_x, self.grid_z.T]).T
            np.savetxt(outputFile, array2export, fmt='%f', header=header)
            print('Data saved to %s' % outputFile)
        
        return
    
    
    
    
    
    def selectColormap(self):
        print('Colormap dialog')
        if self.colormapDialog.isHidden():
            self.colormapDialog.show()
        self.colormapDialog.raise_()
        self.colormapDialog.show()
    
    
        
        
        
        
    def _enableSaveButton(self):
        self.saveButton.setEnabled(True)
        self.saveButton.setToolTip(None)
    
    
    
    
    
    def saveButtonClicked(self):
        print('Save button clicked')
    
    
    
    
    
    



class SelectionTable(qt.QTableWidget):
    tableChanged = qt.pyqtSignal()
    def __init__(self, parent):
        super(SelectionTable, self).__init__(parent)
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['Spectrum', 'H', 'K', 'L', 
            'motor position', 'custom Q'])
        self.setColumnWidth(0, 300)
        self.setColumnWidth(1, 60)
        self.setColumnWidth(2, 60)
        self.setColumnWidth(3, 60)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
        self.itemChanged.connect(self.updateQ)
        self.spectra = {}
        self.motorNames = []
        
    
    def update(self, curves=[]):
        legends = [self.item(i, 0).text() for i in range(self.rowCount())]
        # Add curves if any
        for ii, curve in enumerate(curves):
            x, y, legend, info = curve[:4]
            if legend in self.spectra.keys():
                print('%s already in map - will be replaced' % legend)
            
            if not info['MotorNames']:
                info['MotorNames'] = []
            if 'H' in info['MotorNames']:
                hkl_h = info['MotorValues'][info['MotorNames'].index('H')]
                hkl_k = info['MotorValues'][info['MotorNames'].index('K')]
                hkl_l = info['MotorValues'][info['MotorNames'].index('L')]
            else:
                hkl_h = np.nan
                hkl_k = np.nan
                hkl_l = np.nan
            if info['MotorValues']:
                motor = info['MotorValues'][0]
            else:
                motor = np.nan
            custom = 0
            
            self.spectra[legend] = {}
            self.spectra[legend]['hklmq'] = [hkl_h, hkl_k, hkl_l, motor, custom]
            self.spectra[legend]['x'] = x
            self.spectra[legend]['y'] = y
            self.spectra[legend]['MotorNames'] = info['MotorNames']
            self.spectra[legend]['MotorValues'] = info['MotorValues']
            
            if legend in legends:
                row = legends.index(legend)
            else:
                self.insertRow(0)
                row = 0
            
            self.setItem(row, 0, qt.QTableWidgetItem(legend))
            for i in range(6):
                self.item(row, i).setFlags(
                    qt.Qt.ItemIsEnabled | qt.Qt.ItemIsSelectable)
                if i < 5:
                    self.setItem(row, 1+i, qt.QTableWidgetItem(
                                        str(self.spectra[legend]['hklmq'][i])))
        # Remove curves if any and update Q for the remaining spectra
        legends = [self.item(i, 0).text() for i in range(self.rowCount())]
        
        motornames = [set(self.spectra[s]['MotorNames']) for s in legends]
        if motornames:
            self.motorNames = motornames[0]
            for ii in range(1, len(motornames)):
                self.motorNames = self.motorNames.union(motornames[ii])
        self.motorNames = list(self.motorNames)
        indices = np.argsort(np.array([s.lower() for s in self.motorNames]))
        self.motorNames = [self.motorNames[i] for i in indices]
        
        self.spectra = dict(
            [(legend, self.spectra[legend]) for legend in legends])
        self.tableChanged.emit()
    
    
    
    def updateQ(self, item):
        if item.column() == 5:
            legend = self.item(item.row(), 0).text()
            self.spectra[legend]['hklmq'][4] = np.float(item.text())
            self.tableChanged.emit()
        # ~ if item.column() == 4:
            # ~ legend = self.item(item.row(), 0).text()
            # ~ self.spectra[legend]['hklmq'][3] = np.float(item.text())
            # ~ self.tableChanged.emit()
    
    
    
    
    def contextMenuEvent(self, event):
        if self.selectedIndexes():
            menu = qt.QMenu(self)
            removeSpectrumAction = menu.addAction("Remove from list")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == removeSpectrumAction:
                rows2remove = list(set([index.row() for index in self.selectedIndexes()]))
                for row in sorted(rows2remove)[::-1]:
                    self.removeRow(row)
                self.update()


class IntegralTable(qt.QTableWidget):
    tableChanged = qt.pyqtSignal()
    def __init__(self, parent):
        qt.QTableWidget.__init__(self, parent)
        self.setColumnCount(2)
        self.setRowCount(10)
        self.setHorizontalHeaderLabels(['from', 'to'])
        self.setColumnWidth(0, 72)
        self.setColumnWidth(1, 72)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        #~ self.setSelectionBehavior(qt.QAbstractItemView.SelectRows)
        #~ self.itemChanged.connect(self.tableChanged)
        #~ self.setVerticalHeaderLabels(['1', '2', '3', '4', '5', 
            #~ '6', '7', '8', '9', 'Ref'])
    
    def contextMenuEvent(self, event):
        if self.selectedIndexes():
            menu = qt.QMenu(self)
            removeSpectrumAction = menu.addAction("Remove from list")
            action = menu.exec_(self.mapToGlobal(event.pos()))
            if action == removeSpectrumAction:
                rows2remove = list(set([index.row() for index in self.selectedIndexes()]))
                for row in sorted(rows2remove)[::-1]:
                    self.removeRow(row)
                    self.insertRow(9)
                self.tableChanged.emit()



class MyColormapDialog(ColormapDialog.ColormapDialog):
    def __init__(self, parent):
        ColormapDialog.ColormapDialog.__init__(self, parent)
        self.autoScale90Button.hide()
        
        supported_colormaps = parent.mapPlotWindow.getSupportedColormaps()
        
        desired_colormaps = ['terrain', 'seismic', 'jet', 'hot',
            'gray', 'gnuplot', 'coolwarm', 'afmhot', 'Spectra_r', 'Reds_r',
            'RdGy_r', 'RdBu_r', 'PuBu_r', 'OrRd_r',
            'CMRmap', 'BrBG_r', 'Blues_r', 'temperature','RdYlBu_r']
        self.combo.clear()
        self.colormapList = []
        for cm in parent.mapPlotWindow.getSupportedColormaps():
            if cm in desired_colormaps:
                self.combo.addItem(cm)
                self.colormapList.append(cm)
                self.buttonGroup.button(2).hide()
                self.colormapList.append(cm)
        if 'RdYlBu_r' in self.colormapList:
            cmap  = 'RdYlBu_r'
        else:
            cmap = 'jet'
        self.colormapIndex  = self.colormapList.index(cmap)
        self.colormapString = cmap
        self.setDataMinMax(0, 1)
        self.setAutoscale(1)
        self.setColormap(self.colormapIndex)
        
        
        
    
if __name__ == "__main__":
    import numpy as np
    
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)


    w = MainWindow()
    w.show()
    app.exec_()


