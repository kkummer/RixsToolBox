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
Finding calibration coefficient : 
- selection of spectra (exhibiting only an elastic peak,for ex. Carbon tape) from source folder
- selection of the energy range
- calculation of the calibration coefficient pushing on calibration button
"""


import os

import numpy as np

from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.pymca import ScanWindow
from PyMca5.PyMcaPlugins import AdvancedAlignmentScanPlugin

import SpecSumGUI
from RTB_Icons import RtbIcons

from scipy import interpolate, ndimage
import matplotlib.pyplot as plt
import math


class MainWindow(SpecSumGUI.MainWindow):
    def __init__(self, parent=None):
        SpecSumGUI.MainWindow.__init__(self)
        self.setWindowTitle('SpecCalibCoeffGUI')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.alignButton.setText('Find energy\ncalibration')
        self.sumButton.hide()
        self.saveButton.hide()
        self.groupWidget.hide()
        self._exportWidget.hide()
        self._plotShiftsWindow.setMaximumHeight(10000)
        self._plotShiftsWindow.toolBar.show()
        self.methodComboBox.setCurrentIndex(1)
        
        self.alignButton.clicked.disconnect(self.alignButtonClicked)
        self.alignButton.clicked.connect(self.getCalibration)
        
        return None
    
    
    
    def getCalibration(self):
        legends = self._plotSpectraWindow._curveList
        
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
        llist, ldict = self.aasp.calculateShifts()
        
        # Find shifts
        shifts = []
        energies = []
        sourcenames = [s.sourceName for s in self._sourceWidget.sourceList]
        for i, legend in enumerate(llist):
            scaninfo = self._plotSpectraWindow.getCurve(legend)[3]
            if 'SourceName' not in scaninfo:
                continue
            energies.append(scaninfo['MotorValues'][
                scaninfo['MotorNames'].index('energy')])
            shifts.append(ldict[legend])
            xlabel = scaninfo['xlabel']
        energies = np.array(energies)
        shifts = np.array(shifts)
        shifts = np.abs(shifts)
        
        # Calculate calibration (meV/pixel) and plot result
        coeffs = np.polyfit(energies, shifts, 1)
        self.calib = 1e3/coeffs[0]
        xnew = np.linspace(energies.min()-0.1*(energies.max()-energies.min()),
            energies.max()+0.1*(energies.max()-energies.min()), 2)
        ynew = np.polyval(coeffs, xnew)
        self._plotShiftsWindow.setGraphTitle('%.3f meV / %s' % (self.calib, xlabel))
        self._plotShiftsWindow.addCurve(energies, shifts, 'Shift (%s)' % xlabel, 
            xlabel='Energy (eV)', ylabel='Shift (%s)' % xlabel, symbol='o')
        self._plotShiftsWindow.addCurve(xnew, ynew, 'Fit', 
            xlabel='Energy (eV)', ylabel='Shift (%s)' % xlabel, symbol='', 
            linestyle='-')
        
        return self.calib
        

if __name__ == "__main__":
    app = qt.QApplication([])
    qt.QObject.connect(app, qt.SIGNAL('lastWindowClosed()'), app, 
        qt.SLOT('quit()'))


    w = MainWindow()
    w.show()
    app.exec_()	
    

