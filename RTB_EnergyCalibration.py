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

from RTB_SpecGen import ExportWidget
from RTB_Icons import RtbIcons

class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('RixsToolBox - Energy conversion')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.build()
        self.connect_signals()
        
        self.scansCalibrated = False
    
    
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
        
        self._exportWidget = ExportWidget()
        
        self._plotSpectraWindow = ScanWindow.ScanWindow(
            parent=self,
            backend=None,
            plugins=False, # Hide plugin tool button
            roi=False,     # No ROI widget
            control=True, # Hide option button
            position=True, # Show x,y position display
            info=True,
            )
        #~ self._plotSpectraWindow.graph.enablemarkermode()
        
        
        
        calibrationWidget = qt.QGroupBox()
        calibrationWidget.setTitle('Parameters')
        calibrationLayout = qt.QHBoxLayout()
        
        self._ecalibSpinBox = qt.QDoubleSpinBox()
        self._ecalibSpinBox.setMaximumWidth(100)
        self._ecalibSpinBox.setMinimumWidth(70)
        self._ecalibSpinBox.setAlignment(qt.Qt.AlignRight)
        self._ecalibSpinBox.setMinimum(-1000000)
        self._ecalibSpinBox.setMaximum(1000000)
        self._ecalibSpinBox.setDecimals(2)
        self._ecalibSpinBox.setSingleStep(1)
        self._ecalibSpinBox.setValue(50)
        ecalibLayout = qt.QHBoxLayout()
        ecalibLayout.addWidget(qt.QLabel('meV / px'))
        ecalibLayout.addWidget(qt.HorizontalSpacer())
        ecalibLayout.addWidget(self._ecalibSpinBox)
        ecalibWidget = qt.QWidget()
        ecalibWidget.setLayout(ecalibLayout)
        
        self._ezeroSpinBox = MarkerSpinBox(self, self._plotSpectraWindow, r'$E=0$')
        self._ezeroSpinBox.setMaximumWidth(100)
        self._ezeroSpinBox.setMinimumWidth(70)
        self._ezeroSpinBox.setAlignment(qt.Qt.AlignRight)
        self._ezeroSpinBox.setMinimum(-100000)
        self._ezeroSpinBox.setMaximum(100000)
        self._ezeroSpinBox.setDecimals(3)
        self._ezeroSpinBox.setSingleStep(1)
        self._ezeroSpinBox.setValue(0)
        ezeroLayout = qt.QHBoxLayout()
        ezeroLayout.addWidget(qt.QLabel('zero energy pixel'))
        ezeroLayout.addWidget(qt.HorizontalSpacer())
        ezeroLayout.addWidget(self._ezeroSpinBox)
        ezeroWidget = qt.QWidget()
        ezeroWidget.setLayout(ezeroLayout)
        
        
        
        
        self._markersPositioned = False
        
        calibrationLayout.addWidget(ecalibWidget)
        calibrationLayout.addWidget(ezeroWidget)
        calibrationWidget.setLayout(calibrationLayout)
        
        
        
        self.showGaussianCheckBox = qt.QCheckBox('Show Gaussian at zero energy')
        
        self.GaussianWidthSpinBox = qt.QDoubleSpinBox()
        self.GaussianWidthSpinBox.setMaximumWidth(100)
        self.GaussianWidthSpinBox.setMinimumWidth(70)
        self.GaussianWidthSpinBox.setAlignment(qt.Qt.AlignRight)
        self.GaussianWidthSpinBox.setMinimum(0.001)
        self.GaussianWidthSpinBox.setMaximum(10000000)
        self.GaussianWidthSpinBox.setDecimals(3)
        self.GaussianWidthSpinBox.setSingleStep(1)
        self.GaussianWidthSpinBox.setValue(1)
        self.GaussianWidthSpinBox.setEnabled(False)
        GaussianWidthLayout = qt.QHBoxLayout()
        GaussianWidthLayout.addWidget(qt.QLabel('FWHM'))
        GaussianWidthLayout.addSpacing(10)
        GaussianWidthLayout.addWidget(self.GaussianWidthSpinBox)
        gaussianWidthWidget = qt.QWidget()
        gaussianWidthWidget.setLayout(GaussianWidthLayout)
        
        self.GaussianHeightSpinBox = qt.QDoubleSpinBox()
        self.GaussianHeightSpinBox.setMaximumWidth(100)
        self.GaussianHeightSpinBox.setMinimumWidth(70)
        self.GaussianHeightSpinBox.setAlignment(qt.Qt.AlignRight)
        self.GaussianHeightSpinBox.setMinimum(0.001)
        self.GaussianHeightSpinBox.setMaximum(10000000)
        self.GaussianHeightSpinBox.setDecimals(3)
        self.GaussianHeightSpinBox.setSingleStep(1)
        self.GaussianHeightSpinBox.setValue(5)
        self.GaussianHeightSpinBox.setEnabled(False)
        GaussianHeightLayout = qt.QHBoxLayout()
        GaussianHeightLayout.addWidget(qt.QLabel('height'))
        GaussianHeightLayout.addSpacing(10)
        GaussianHeightLayout.addWidget(self.GaussianHeightSpinBox)
        gaussianHeightWidget = qt.QWidget()
        gaussianHeightWidget.setLayout(GaussianHeightLayout)
        self.GaussianHeightSpinBox.setDisabled(True)
        
        self.autoscaleGaussianCheckBox = qt.QCheckBox('Autoscale height')
        self.autoscaleGaussianCheckBox.setChecked(True)
        
        gaussianLayout = qt.QGridLayout()
        gaussianLayout.addWidget(self.showGaussianCheckBox, 0, 0, 1, 2)
        gaussianLayout.addWidget(gaussianWidthWidget, 1, 0, 1, 1)
        gaussianLayout.addWidget(gaussianHeightWidget, 1, 2, 1, 1)
        gaussianLayout.addWidget(self.autoscaleGaussianCheckBox, 1, 3, 1, 1)
        gaussianWidget = qt.QWidget()
        gaussianWidget.setLayout(gaussianLayout)
        
        
        
        
        
        self.calibrateButton = qt.QPushButton('Convert')
        self.calibrateButton.setMinimumSize(75,75)
        self.calibrateButton.setMaximumSize(75,75)
        self.calibrateButton.clicked.connect(self.calibrateButtonClicked)
            
        self.saveButton = qt.QPushButton('Save')
        self.saveButton.setMinimumSize(75,75)
        self.saveButton.setMaximumSize(75,75)
        self.saveButton.clicked.connect(self.saveButtonClicked)
        self.saveButton.setDisabled(True)
        self.saveButton.setToolTip('Select output file\nto enable saving')
        
        
        
        self._inputLayout = qt.QHBoxLayout(self)
        self._inputLayout.addWidget(calibrationWidget)
        self._inputLayout.addWidget(gaussianWidget)
        self._inputLayout.addWidget(qt.HorizontalSpacer())
        self._inputLayout.addWidget(self.calibrateButton)
        self._inputLayout.addWidget(self.saveButton)
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
        
        
        
        return 0
    
    
    def connect_signals(self):
        self._sourceWidget.sigAddSelection.connect(
            self._plotSpectraWindow._addSelection)
        self._sourceWidget.sigRemoveSelection.connect(
            self._plotSpectraWindow._removeSelection)
        self._sourceWidget.sigReplaceSelection.connect(
            self._plotSpectraWindow._replaceSelection)
        
        self.autoscaleGaussianCheckBox.stateChanged.connect(
            self.autoscaleGaussianChanged)
        
        self._sourceWidget.sigAddSelection.connect(self._positionMarkers)
        
        self._sourceWidget.sigAddSelection.connect(self._selectionchanged)
        self._sourceWidget.sigReplaceSelection.connect(self._selectionchanged)
        
        self._exportWidget.OutputFileSelected.connect(self._enableSaveButton)
        
        self.showGaussianCheckBox.stateChanged.connect(self.gaussianOnOff)
        self._ezeroSpinBox.intersectionsChangedSignal.connect(self.zeroEnergyChanged)
        self._ezeroSpinBox.valueChanged.connect(lambda: self.zeroEnergyChanged(replot=True))
        self.GaussianWidthSpinBox.valueChanged.connect(lambda: self.zeroEnergyChanged(replot=True))
        self.GaussianHeightSpinBox.valueChanged.connect(lambda: self.zeroEnergyChanged(replot=True))
        self._sourceWidget.sigReplaceSelection.connect(lambda: self.zeroEnergyChanged(replot=True))
        return 0
    
    
    def zeroEnergyChanged(self, replot=False):
        if self.showGaussianCheckBox.isChecked():
            ezero = self._ezeroSpinBox.value()
            gwidth = self.GaussianWidthSpinBox.value()
            gheight = self.GaussianHeightSpinBox.value()
            if self.autoscaleGaussianCheckBox.isChecked():
                curves = [c for c in 
                    self._plotSpectraWindow.getAllCurves(just_legend=True)
                    if not c.startswith('Gaussian')]
                if len(curves):
                    x, y = self._plotSpectraWindow.getCurve(curves[0])[:2]
                    gheight = y[np.abs(x - ezero).argsort()][:5].mean()
                    self.GaussianHeightSpinBox.setValue(gheight)
            gaussianX = np.linspace(ezero-3*gwidth, ezero+3*gwidth, 100)
            gaussianY = gheight * np.exp(-(gaussianX-ezero)**2/(2*(gwidth/2.3548)**2))
            self._plotSpectraWindow.addCurve(
                gaussianX, gaussianY, 'Gaussian', ylabel=' ', replot=replot)
    
    
    def gaussianOnOff(self):
        if self.showGaussianCheckBox.isChecked():
            self.GaussianWidthSpinBox.setEnabled(True)
            if not self.autoscaleGaussianCheckBox.isChecked():
                self.GaussianHeightSpinBox.setEnabled(True)
            self.autoscaleGaussianCheckBox.setEnabled(True)
            self.zeroEnergyChanged(replot=True)
        else:
            self.GaussianWidthSpinBox.setEnabled(False)
            self.GaussianHeightSpinBox.setEnabled(False)
            self.autoscaleGaussianCheckBox.setEnabled(False)
            self._plotSpectraWindow.removeCurve('Gaussian  ')
    
    def autoscaleGaussianChanged(self):
        if self.autoscaleGaussianCheckBox.isChecked():
            self.GaussianHeightSpinBox.setEnabled(False)
        else:
            self.GaussianHeightSpinBox.setEnabled(True)
        
    
    def _enableSaveButton(self):
        self.saveButton.setEnabled(True)
        self.saveButton.setToolTip(None)
    
    def _positionMarkers(self):
        if not self._markersPositioned:
            limits = self._plotSpectraWindow.getGraphXLimits()
            self._ezeroSpinBox.setValue(0.5 * (limits[1]+limits[0]))
            self._markersPositioned = True
    
    def _selectionchanged(self):
        self.scansCalibrated = False
        self.calibrateButton.setEnabled(True)
    
    
    def calibrateButtonClicked(self):
        llist = self._plotSpectraWindow.getAllCurves()
        # Align scans
        self.calibratedScans = []
        oldlegends = []
        sourcenames = [s.sourceName for s in self._sourceWidget.sourceList]
        for i, scan in enumerate(llist):
            x, y, legend, scaninfo = scan[:4]
            
            if 'SourceName' not in scaninfo or legend.rstrip().endswith('ENE') \
                    or legend=='Gaussian  ':
                continue
            
            sourceindex = sourcenames.index(scaninfo['SourceName'])
            dataObject = self._sourceWidget.sourceList[sourceindex].getDataObject(scaninfo['Key'])
            newdataObject = copy.deepcopy(dataObject)
            
            xindex = scaninfo['selection']['x'][0]
            yindex = scaninfo['selection']['y'][0]
            
            newx = x - self._ezeroSpinBox.value()
            newx *= self._ecalibSpinBox.value() * 1e-3
            
            oldlegends.append(legend)
            
            newlegend = ''.join([legend, ' ENE'])
            
            scaninfo['Ezero'] = self._ezeroSpinBox.value()
            scaninfo['Ecalib'] = self._ecalibSpinBox.value()
            scaninfo['oldKey'] = newdataObject.info['Key']
            scaninfo['oldX'] = scaninfo['selection']['cntlist'][
                                scaninfo['selection']['x'][0]]
            
            self._plotSpectraWindow.addCurve(
                newx, y, newlegend, scaninfo, 
                xlabel='Energy',
                ylabel='',
                replot=False)
        
        self._plotSpectraWindow.setGraphXLabel('Energy')
        self._plotSpectraWindow.removeCurves(oldlegends)
        self._plotSpectraWindow.resetZoom()
        
        self.scansCalibrated = True
        self.calibrateButton.setDisabled(True)
        if not self._exportWidget._folderLineEdit.text() == '':
            self.saveButton.setEnabled(True)
        
        
        return
    
    
    
    
    def saveButtonClicked(self):
        curves = self._plotSpectraWindow.getAllCurves()
        
        dataObjects2save = []
        
        sourcenames = [s.sourceName[0] for s in self._sourceWidget.sourceList]
        for curve in curves:
            
            if not legend.rstrip().endswith('ENE'):
                continue
            
            sourceindex = sourcenames.index(info['FileName'])
            dataObject = self._sourceWidget.sourceList[sourceindex].getDataObject(info['oldKey'])
            newdataObject = copy.deepcopy(dataObject)
            
            xindex = newdataObject.info['LabelNames'].index(info['oldX'])
            escale = newdataObject.data[:, xindex] - self._ezeroSpinBox.value()
            escale *= self._ecalibSpinBox.value() * 1e-3
            if newdataObject.info['LabelNames'].count('Energy') > 0:
                ene_index = newdataObject.info['LabelNames'].index('Energy')
                newdataObject.data = np.vstack(
                    [newdataObject.data[:,:ene_index].T, escale, newdataObject.data[:, ene_index+1:].T]).T
            else:
                newdataObject.data = np.vstack(
                    [newdataObject.data[:,0], escale, newdataObject.data[:, 1:].T]).T
                newdataObject.info['LabelNames'] = newdataObject.info['LabelNames'][:1] + \
                    ['Energy'] + newdataObject.info['LabelNames'][1:]
            
            newdataObject.info['Command'] = '%s - energy calibrated' % (
                info['Command'])
            
            header = []
            header.append('#D  %s\n' % time.strftime('%Y-%m-%d %H:%M:%S', 
                time.localtime(time.time())))
            for hline in newdataObject.info['Header']:
                if hline.startswith('#D'):
                    continue
                if hline.startswith('#N'):
                    continue
                if hline.startswith('#L'):
                    continue
                header.append(hline)
            header.append('#C  Parameters for energy calibration')
            header.append('#C  Ezero: %s %s' % (info['Ezero'], info['oldX']))
            header.append('#C  Ecalib: %s meV / %s' % (info['Ecalib'], info['oldX']))
            header.append('#C  ')
            header.append('#N  %d' % (len(newdataObject.info['LabelNames'])))
            header.append('#L  %s' % ('  '.join(newdataObject.info['LabelNames'])))
            newdataObject.info['Header'] = header
            
            dataObjects2save.append(newdataObject)
        
        
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
        
        
        for dataObject in dataObjects2save:
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
                datfilename = '%s/S%04d_%s_%s.dat' % (
                    specfilename.rstrip('.spec'), scannumber, 
                    key.split('.')[-1], command)
                np.savetxt('%s' % (datfilename), dataObject.data)
                print('Spectrum saved to \"%s\"\n' % (datfilename))
        
            #~ scannumber +=1
        
        self.saveButton.setDisabled(True)



if __name__ == "__main__":
    import numpy as np
    
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)


    w = MainWindow()
    w.show()
    app.exec_()


