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
from PyMca5.PyMca import PlotWidget
from PyMca5.PyMcaGui import IconDict
from PyMca5.PyMcaGui.pymca import ScanWindow

from RixsSpectrum import RixsSpectrum
from RTB_Icons import RtbIcons



class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle('SpecGen GUI')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self._initialize_parameters()
        
        self._sourcefilesWidget = SourceFilesWidget(self)
        self._parametersWidget = ParametersWidget(self)
        self._expertDialog = ExpertSettingsDialog(self, 
            lower_threshold=self.lower_threshold,
            upper_threshold=self.upper_threshold, 
            masksize=self.masksize, 
            SPC_gridsize=self.SPC_gridsize,
            SPC_low_threshold=self.SPC_low_threshold, 
            SPC_high_threshold=self.SPC_high_threshold, 
            SPC_single_threshold=self.SPC_single_threshold, 
            SPC_double_threshold=self.SPC_double_threshold)
        
        self._plotSpectraWindow = ScanWindow.ScanWindow(
            parent=self,
            backend=None,
            plugins=True, # Hide plugin tool button
            newplot=True, # Hide mirror active curve, ... functionality
            roi=False,     # No ROI widget
            control=True, # Hide option button
            position=True, # Show x,y position display
            kw={'logx': False, # Hide logarithmic x-scale tool button
                'logy': False, # Hide logarithmic y-scale tool button
                'flip': False, # Hide whatever this does
                'fit': True, # Hide simple fit tool button
                'energy': False}) # Hide simple fit tool button
        
        self._plotCountsWindow = PlotWidget.PlotWidget(
            parent=self,
            backend=None,
            plugins=True, # Hide plugin tool button
            newplot=True, # Hide mirror active curve, ... functionality
            roi=False,     # No ROI widget
            control=False, # Hide option button
            position=True, # Show x,y position display
            kw={'logx': False, # Hide logarithmic x-scale tool button
                'logy': False, # Hide logarithmic y-scale tool button
                'flip': False, # Hide whatever this does
                'fit': True, # Hide simple fit tool button
                'energy': False}) # Hide simple fit tool button
        self._plotCountsWindow.setMaximumHeight(250)
        self._plotCountsWindow.setGraphYLabel('Total intensity')
        
        
        self._exportWidget = ExportWidget(self)
        self._exportWidget.askFileNameCheckBox.hide()
        self._convertbuttonWidget = ConvertButtonWidget(self)
        self._savebuttonWidget = SaveButtonWidget(self)
        
        self.connect(self._convertbuttonWidget, 
            qt.SIGNAL('ConvertButtonClicked'), self.specgen)
        
        self.connect(self._savebuttonWidget, 
            qt.SIGNAL('SaveButtonClicked'), self.save)
        
        self.connect(self._parametersWidget, 
            qt.SIGNAL('ExpertSettingsButtonClicked'), self.expertsettings)
            
        self.connect(self._exportWidget, qt.SIGNAL('OutputFileSelected'),
            self._enableSaveButton)
        
        
       
       
        self.data2export = []
        
        self._inputLayout = qt.QHBoxLayout(self)
        self._inputLayout.addWidget(self._parametersWidget)
        self._inputLayout.addWidget(qt.HorizontalSpacer())
        self._inputLayout.addWidget(self._convertbuttonWidget)
        self._inputLayout.addWidget(self._savebuttonWidget)
        self._inputWidget = qt.QWidget()
        #~ self._inputWidget.setContentsMargins(0,0,0,-8)
        self._inputWidget.setLayout(self._inputLayout)
        
        
        self._rsLayout = qt.QVBoxLayout(self)
        self._rsLayout.addWidget(self._inputWidget)
        self._rsLayout.addWidget(self._plotSpectraWindow)
        self._rsLayout.addWidget(self._plotCountsWindow)
        self._rsWidget = qt.QWidget()
        self._rsWidget.setContentsMargins(0,0,0,-8)
        self._rsWidget.setLayout(self._rsLayout)
        
        self._lsLayout = qt.QVBoxLayout(self)
        self._lsLayout.addWidget(self._sourcefilesWidget)
        self._lsLayout.addWidget(self._exportWidget)
        self._lsWidget = qt.QWidget()
        self._lsWidget.setContentsMargins(0,0,0,-8)
        self._lsWidget.setSizePolicy(
            qt.QSizePolicy(qt.QSizePolicy.Fixed, qt.QSizePolicy.Preferred))
        self._lsWidget.setLayout(self._lsLayout)
        
        
        self._mainLayout = qt.QHBoxLayout()
        self._mainLayout.addWidget(self._lsWidget)
        self._mainLayout.addWidget(self._rsWidget)
        self.setLayout(self._mainLayout)
        
        
        
        
        # Initial parameters
        self._parametersWidget._slopeDoubleSpinBox.setValue(self.slope)
        self._parametersWidget._pointsperpixelDoubleSpinBox.setValue(self.points_per_pixel)
        self._parametersWidget._binningSpinBox.setValue(self.binning)
        
        
    def _initialize_parameters(self):
        self.slope = -.0089
        self.points_per_pixel = 2.0
        self.binning = 1 
        self.lower_threshold = .05
        self.upper_threshold = 1.0
        self.masksize = 5
        self.SPC = True
        self.SPC_gridsize = 3
        self.SPC_low_threshold = .2
        self.SPC_high_threshold = 1.0
        self.SPC_single_threshold = .2
        self.SPC_double_threshold = 1.5
        return 0
        
    def update_parameters(self):
        self.slope = self._parametersWidget._slopeDoubleSpinBox.value()
        self.points_per_pixel=self._parametersWidget._pointsperpixelDoubleSpinBox.value()
        self.binning=self._parametersWidget._binningSpinBox.value()
    
    
    def _enableSaveButton(self):
        self._savebuttonWidget.setEnabled(True)
    
    def specgen(self):
        self.update_parameters()
        #self._update_expertsetting()
        self.data2export = []
        fnames = [i.data(0) for i in 
            self._sourcefilesWidget.sourceView.selectedIndexes()]
        
        self._plotSpectraWindow.clearCurves()
        self._plotCountsWindow.clearCurves()
        counts = []
        
        
        for i, fname in enumerate(fnames):
            f = '/'.join([self._sourcefilesWidget.sourceFolder, fname])
            x=RixsSpectrum(f, slope=self.slope, points_per_pixel=self.points_per_pixel, binning=self.binning,
                lower_threshold=self.lower_threshold, upper_threshold=self.upper_threshold, 
                masksize=self.masksize, SPC=True, SPC_gridsize= self.SPC_gridsize, SPC_low_threshold=self.SPC_low_threshold, SPC_high_threshold=self.SPC_high_threshold, 
                SPC_single_threshold=self.SPC_single_threshold, SPC_double_threshold=self.SPC_double_threshold)
                
            self.data2export.append(x)
            self._plotSpectraWindow.addCurve(x.spectrum['Pixel'], 
                x.spectrum['Photons'], '%s-Photons' % (fname))
            counts.append(x.spectrum['Photons'].sum())
            self._plotCountsWindow.addCurve(
                np.arange(i+1)+1, counts, 'Counts', symbol='o')
            self._plotCountsWindow.setGraphYLabel('Total intensity')
            self._plotCountsWindow.replot()
            
            
        
        
    def save(self):
        self.outputfilename = self._exportWidget._folderLineEdit.text()
        self.savedatfile = self._exportWidget._datCheckBox.isChecked()
        for d2e in self.data2export:
            d2e.save(outputfile=self.outputfilename, 
                savedatfile=self.savedatfile)
            
        
        
      
        
    def expertsettings(self):
        print("expert_settings")
        self._expertDialog = ExpertSettingsDialog(self, lower_threshold= self.lower_threshold, upper_threshold= self.upper_threshold, masksize=self.masksize,
                                               SPC_gridsize= self.SPC_gridsize,SPC_low_threshold=self.SPC_low_threshold, SPC_high_threshold=self.SPC_high_threshold,
                                               SPC_single_threshold=self.SPC_single_threshold, SPC_double_threshold=self.SPC_double_threshold )
        self._expertDialog.show()
        
        


class SourceFilesWidget(qt.QGroupBox):
    def __init__(self, parent):
        qt.QGroupBox.__init__(self, parent)
        self.mainLayout = qt.QGridLayout(self)
        self.mainLayout.setMargin(10)
        self.mainLayout.setSpacing(5)
        self.setTitle('Image Folder')
        
        self.sourceFolder = None
        
        self.build()
        
        
    def build(self):
        
        self.folderLineEdit = qt.QLineEdit(self)
        self.folderLineEdit.setReadOnly(True)
        
        self.openButton = qt.QToolButton(self)
        self.openButton.setIcon(qt.QIcon(qt.QPixmap(IconDict['fileopen'])))
        self.openButton.setToolTip("Select source folder")
        self.connect(self.openButton, qt.SIGNAL('clicked()'), 
            self.openButtonclicked)

        self.refreshButton= qt.QToolButton(self)
        self.refreshButton.setIcon(qt.QIcon(qt.QPixmap(IconDict['reload'])))
        self.refreshButton.setToolTip("Refresh file list")
        self.connect(self.refreshButton, qt.SIGNAL('clicked()'),
            self.built_source_file_list)
        
        self.filesLabel = qt.QLabel("Source files:")
        
        self.sourceView = qt.QTreeView(self)
        self.sourceView.setRootIsDecorated(False)
        self.sourceView.setAlternatingRowColors(True)
        self.sourceView.setSortingEnabled(True)
        self.sourceView.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)
        
        self.mainLayout.addWidget(self.folderLineEdit, 0, 0, 1, 1)
        self.mainLayout.addWidget(self.openButton, 0, 1, 1, 1)
        self.mainLayout.addWidget(self.refreshButton, 0, 2, 1, 1)
        self.mainLayout.addWidget(self.filesLabel, 1, 0, 1, 3)
        self.mainLayout.addWidget(self.sourceView, 2, 0, 1, 3)
    
    
    def openButtonclicked(self):
        sourceDialog = qt.QFileDialog(self)
        #~ sourceDialog.setFileMode(qt.QFileDialog.Directory)
        #~ sourceDialog.setNameFilter("CCD images (*.edf);;All files (*.*)")
        response = str(sourceDialog.getExistingDirectory(self))
        if response:
            self.sourceFolder = response.replace('\\', '/')
            self.folderLineEdit.setText(self.sourceFolder)
            self.built_source_file_list()
        
    
    def built_source_file_list(self):
        if self.sourceFolder:
            model = qt.QStandardItemModel(0, 1, self)
            model.setHeaderData(0, qt.Qt.Horizontal, 'Filename')
            for fname in [s for s in os.listdir(self.sourceFolder) if s.endswith('.edf')]:
                model.insertRow(0)
                model.setData(model.index(0, 0), fname)
            self.fileList = model
            self.sourceView.setModel(self.fileList)
        

class ConvertButtonWidget(qt.QPushButton):
    def __init__(self, parent):
        qt.QPushButton.__init__(self, parent)
        
        self.setText("Generate\n\nspectra")
        self.setMinimumSize(75,75)
        self.setMaximumSize(75,75)
        self.connect(self, qt.SIGNAL('clicked()'), 
            self._convertButtonclicked)
        
        
        
    
    def _convertButtonclicked(self):
        qt.QObject.emit(self, qt.SIGNAL('ConvertButtonClicked'), 'CONVERT')

class SaveButtonWidget(qt.QPushButton):
    def __init__(self, parent):
        qt.QPushButton.__init__(self, parent)
        
        self.setText("Save\n\nspectra")
        self.setMinimumSize(75,75)
        self.setMaximumSize(75,75)
        
        
        self.connect(self, qt.SIGNAL('clicked()'), 
            self._saveButtonclicked)
        
        self.setEnabled(False)
        
        
    
    def _saveButtonclicked(self):
        qt.QObject.emit(self, qt.SIGNAL('SaveButtonClicked'), 'SAVE')
        


        
       
        

class ParametersWidget(qt.QGroupBox):
    def __init__(self, parent):
        qt.QGroupBox.__init__(self, parent)
        self._mainLayout = qt.QVBoxLayout(self)
        self._mainLayout.setMargin(1)
        self._mainLayout.setSpacing(1)
        self.setTitle('Parameters')
        self.build()
        
        self.slopeParameter = None
    
    def build(self):
        self._slopeDoubleSpinBox = qt.QDoubleSpinBox()
        self._slopeDoubleSpinBox.setMaximumWidth(100)
        self._slopeDoubleSpinBox.setMinimumWidth(70)
        self._slopeDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._slopeDoubleSpinBox.setMinimum(-1)
        self._slopeDoubleSpinBox.setMaximum(1)
        self._slopeDoubleSpinBox.setDecimals(4)
        self._slopeDoubleSpinBox.setSingleStep(.0005)
        self._slopeDoubleSpinBox.setValue(-0.0089)
        self._slopeLayout = qt.QHBoxLayout()
        self._slopeLayout.addWidget(qt.QLabel('Slope'))
        self._slopeLayout.addWidget(qt.HorizontalSpacer())
        self._slopeLayout.addWidget(self._slopeDoubleSpinBox)
        self._slopeWidget = qt.QWidget()
        self._slopeWidget.setLayout(self._slopeLayout)
        
        self._pointsperpixelDoubleSpinBox = qt.QDoubleSpinBox()
        self._pointsperpixelDoubleSpinBox.setMaximumWidth(100)
        self._pointsperpixelDoubleSpinBox.setMinimumWidth(70)
        self._pointsperpixelDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._pointsperpixelDoubleSpinBox.setMinimum(0.1)
        self._pointsperpixelDoubleSpinBox.setMaximum(100)
        self._pointsperpixelDoubleSpinBox.setSingleStep(.1)
        self._pointsperpixelDoubleSpinBox.setValue(2)
        self._pointsperpixelLayout = qt.QHBoxLayout()
        self._pointsperpixelLayout.addWidget(qt.QLabel('Points per pixel'))
        self._pointsperpixelLayout.addWidget(qt.HorizontalSpacer())
        self._pointsperpixelLayout.addWidget(self._pointsperpixelDoubleSpinBox)
        self._pointsperpixelWidget = qt.QWidget()
        self._pointsperpixelWidget.setLayout(self._pointsperpixelLayout)
        
        self._binningSpinBox = qt.QSpinBox()
        self._binningSpinBox.setMaximumWidth(100)
        self._binningSpinBox.setMinimumWidth(70)
        self._binningSpinBox.setAlignment(qt.Qt.AlignRight)
        self._binningSpinBox.setMinimum(1)
        self._binningSpinBox.setValue(1)
        self._binningLayout = qt.QHBoxLayout()
        self._binningLayout.addWidget(qt.QLabel('Binning'))
        self._binningLayout.addWidget(qt.HorizontalSpacer())
        self._binningLayout.addWidget(self._binningSpinBox)
        self._binningWidget = qt.QWidget()
        self._binningWidget.setLayout(self._binningLayout)
        
        self._spcCheckBox = qt.QCheckBox()
        self._spcCheckBox.setText('Single photon counting')
        self._spcCheckBox.setCheckState(True)
        self._spcCheckBox.setTristate(False)
        self._spcLayout = qt.QHBoxLayout()
        self._spcLayout.addWidget(self._spcCheckBox)
        self._spcLayout.addWidget(qt.HorizontalSpacer())
        self._spcWidget = qt.QWidget()
        self._spcWidget.setLayout(self._spcLayout)
        
        
        self._expertToolButton = qt.QToolButton(self)
        self._expertToolButton.setToolTip('Expert settings')
        self._expertToolButton.setIcon(qt.QIcon(qt.QPixmap(RtbIcons['Settings'])))
        self.connect(self._expertToolButton, qt.SIGNAL('clicked()'), 
            self.expertToolButtonclicked)

        
        
        self._topLayout = qt.QHBoxLayout()
        self._topLayout.setMargin(1)
        self._topLayout.setSpacing(1)
        self._topLayout.addWidget(self._slopeWidget)
        self._topLayout.addWidget(self._pointsperpixelWidget)
        self._topLayout.addWidget(self._binningWidget)
        self._topWidget = qt.QWidget()
        self._topWidget.setLayout(self._topLayout)
        
        self._bottomLayout = qt.QHBoxLayout()
        self._bottomLayout.setMargin(1)
        self._bottomLayout.setSpacing(1)
        self._bottomLayout.addWidget(self._spcWidget)
        self._bottomLayout.addWidget(qt.HorizontalSpacer())
        self._bottomLayout.addWidget(self._expertToolButton)
        self._bottomWidget = qt.QWidget()
        self._bottomWidget.setLayout(self._bottomLayout)
        
        
        self._mainLayout.addWidget(self._topWidget)
        self._mainLayout.addWidget(self._bottomWidget)
        self.setLayout(self._mainLayout)
    
    
    
    def expertToolButtonclicked(self):
        qt.QObject.emit(self, qt.SIGNAL('ExpertSettingsButtonClicked'), 
            'EXPERT_SETTINGS')
        


class ExpertSettingsDialog(qt.QDialog):
    def __init__(self, parent, lower_threshold=.05 , upper_threshold=1.0, masksize=5, SPC_gridsize= 3 , SPC_low_threshold= .2 ,SPC_high_threshold=1.0  ,SPC_single_threshold= .2 ,SPC_double_threshold= 1.5):
        qt.QDialog.__init__(self, parent)
        self.setWindowTitle('Expert settings')
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        
        self._mainLayout = qt.QVBoxLayout(self)
        self._mainLayout.setSpacing = 0
        self._mainLayout.setMargin = 0
        
        self.parent = parent
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.masksize = masksize
        self.SPC = True
        self.SPC_gridsize = SPC_gridsize
        self.SPC_low_threshold = SPC_low_threshold
        self.SPC_high_threshold = SPC_high_threshold
        self.SPC_single_threshold = SPC_single_threshold
        self.SPC_double_threshold = SPC_double_threshold
        
        self.build()
        
    
    def _resetWindow(self):
        
        self._lowerthresholdDoubleSpinBox.setValue(.05)	
        self._upperthresholdDoubleSpinBox.setValue(1.0)
        self._masksizeSpinBox.setValue(5)
        self._spcgridsizeSpinBox.setValue(3)
        self._spclowthresholdDoubleSpinBox.setValue(.2)
        self._spchighthresholdDoubleSpinBox.setValue(1.0)
        self._spcsinglethresholdDoubleSpinBox.setValue(.2)
        self._spcdoublethresholdDoubleSpinBox.setValue(1.5) 
        
   
    def _closeWindow(self):
        self.close()
      
    
        
    def build(self):
        
        self._intParamsWidget = qt.QGroupBox()
        self._intParamsWidget.setTitle('Integrating algorithm')
        self._intParamsLayout = qt.QVBoxLayout()
        
        
        self._lowerthresholdDoubleSpinBox = qt.QDoubleSpinBox()
        self._lowerthresholdDoubleSpinBox.setMaximumWidth(100)
        self._lowerthresholdDoubleSpinBox.setMinimumWidth(70)
        self._lowerthresholdDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._lowerthresholdDoubleSpinBox.setMinimum(0)
        self._lowerthresholdDoubleSpinBox.setMaximum(100)
        self._lowerthresholdDoubleSpinBox.setSingleStep(.01)
        self._lowerthresholdDoubleSpinBox.setValue(self.lower_threshold)
        self._lowerthresholdLayout = qt.QHBoxLayout()
        self._lowerthresholdLayout.addWidget(qt.QLabel('Lower threshold'))
        self._lowerthresholdLayout.addWidget(qt.HorizontalSpacer())
        self._lowerthresholdLayout.addWidget(self._lowerthresholdDoubleSpinBox)
        self._lowerthresholdWidget = qt.QWidget()
        self._lowerthresholdWidget.setLayout(self._lowerthresholdLayout)
        
        self._upperthresholdDoubleSpinBox = qt.QDoubleSpinBox()
        self._upperthresholdDoubleSpinBox.setMaximumWidth(100)
        self._upperthresholdDoubleSpinBox.setMinimumWidth(70)
        self._upperthresholdDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._upperthresholdDoubleSpinBox.setMinimum(0)
        self._upperthresholdDoubleSpinBox.setMaximum(100)
        self._upperthresholdDoubleSpinBox.setSingleStep(.01)
        self._upperthresholdDoubleSpinBox.setValue(self.upper_threshold)
        self._upperthresholdLayout = qt.QHBoxLayout()
        self._upperthresholdLayout.addWidget(qt.QLabel('Upper threshold'))
        self._upperthresholdLayout.addWidget(qt.HorizontalSpacer())
        self._upperthresholdLayout.addWidget(self._upperthresholdDoubleSpinBox)
        self._upperthresholdWidget = qt.QWidget()
        self._upperthresholdWidget.setLayout(self._upperthresholdLayout)
        
        self._masksizeSpinBox = qt.QSpinBox()
        self._masksizeSpinBox.setMaximumWidth(100)
        self._masksizeSpinBox.setMinimumWidth(70)
        self._masksizeSpinBox.setAlignment(qt.Qt.AlignRight)
        self._masksizeSpinBox.setMinimum(1)
        self._masksizeSpinBox.setMaximum(15)
        self._masksizeSpinBox.setValue(self.masksize)
        self._masksizeSpinBox.setSingleStep(2)
        self._masksizeLayout = qt.QHBoxLayout()
        self._masksizeLayout.addWidget(qt.QLabel('Mask size'))
        self._masksizeLayout.addWidget(qt.HorizontalSpacer())
        self._masksizeLayout.addWidget(self._masksizeSpinBox)
        self._masksizeWidget = qt.QWidget()
        self._masksizeWidget.setLayout(self._masksizeLayout)
        # !!! User can still set even numbers
        
        self._intParamsLayout.addWidget(self._lowerthresholdWidget)
        self._intParamsLayout.addWidget(self._upperthresholdWidget)
        self._intParamsLayout.addWidget(self._masksizeWidget)
        self._intParamsWidget.setLayout(self._intParamsLayout)
        self._mainLayout.addWidget(self._intParamsWidget)
        
        
        self._spcParamsWidget = qt.QGroupBox()
        self._spcParamsWidget.setTitle('Single photon counting')
        self._spcParamsLayout = qt.QVBoxLayout()
        
        self._spcgridsizeSpinBox = qt.QSpinBox()
        self._spcgridsizeSpinBox.setMaximumWidth(100)
        self._spcgridsizeSpinBox.setMinimumWidth(70)
        self._spcgridsizeSpinBox.setAlignment(qt.Qt.AlignRight)
        self._spcgridsizeSpinBox.setMinimum(1)
        self._spcgridsizeSpinBox.setMaximum(7)
        self._spcgridsizeSpinBox.setValue(self.SPC_gridsize)
        self._spcgridsizeSpinBox.setSingleStep(2)
        self._spcgridsizeLayout = qt.QHBoxLayout()
        self._spcgridsizeLayout.addWidget(qt.QLabel('Grid size'))
        self._spcgridsizeLayout.addWidget(qt.HorizontalSpacer())
        self._spcgridsizeLayout.addWidget(self._spcgridsizeSpinBox)
        self._spcgridsizeWidget = qt.QWidget()
        self._spcgridsizeWidget.setLayout(self._spcgridsizeLayout)
        # !!! User can still set even numbers
        
        self._spclowthresholdDoubleSpinBox = qt.QDoubleSpinBox()
        self._spclowthresholdDoubleSpinBox.setMaximumWidth(100)
        self._spclowthresholdDoubleSpinBox.setMinimumWidth(70)
        self._spclowthresholdDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._spclowthresholdDoubleSpinBox.setMinimum(0)
        self._spclowthresholdDoubleSpinBox.setMaximum(1)
        self._spclowthresholdDoubleSpinBox.setSingleStep(.05)
        self._spclowthresholdDoubleSpinBox.setValue(self.SPC_low_threshold)
        self._spclowthresholdLayout = qt.QHBoxLayout()
        self._spclowthresholdLayout.addWidget(qt.QLabel('Lower threshold'))
        self._spclowthresholdLayout.addWidget(qt.HorizontalSpacer())
        self._spclowthresholdLayout.addWidget(
            self._spclowthresholdDoubleSpinBox)
        self._spclowthresholdWidget = qt.QWidget()
        self._spclowthresholdWidget.setLayout(self._spclowthresholdLayout)
        
        self._spchighthresholdDoubleSpinBox = qt.QDoubleSpinBox()
        self._spchighthresholdDoubleSpinBox.setMaximumWidth(100)
        self._spchighthresholdDoubleSpinBox.setMinimumWidth(70)
        self._spchighthresholdDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._spchighthresholdDoubleSpinBox.setMinimum(0)
        self._spchighthresholdDoubleSpinBox.setMaximum(2)
        self._spchighthresholdDoubleSpinBox.setSingleStep(.05)
        self._spchighthresholdDoubleSpinBox.setValue(self.SPC_high_threshold)
        self._spchighthresholdLayout = qt.QHBoxLayout()
        self._spchighthresholdLayout.addWidget(
            qt.QLabel('Upper threshold'))
        self._spchighthresholdLayout.addWidget(qt.HorizontalSpacer())
        self._spchighthresholdLayout.addWidget(
            self._spchighthresholdDoubleSpinBox)
        self._spchighthresholdWidget = qt.QWidget()
        self._spchighthresholdWidget.setLayout(self._spchighthresholdLayout)
        
        self._spcsinglethresholdDoubleSpinBox = qt.QDoubleSpinBox()
        self._spcsinglethresholdDoubleSpinBox.setMaximumWidth(100)
        self._spcsinglethresholdDoubleSpinBox.setMinimumWidth(70)
        self._spcsinglethresholdDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._spcsinglethresholdDoubleSpinBox.setMinimum(0)
        self._spcsinglethresholdDoubleSpinBox.setMaximum(2)
        self._spcsinglethresholdDoubleSpinBox.setSingleStep(.05)
        self._spcsinglethresholdDoubleSpinBox.setValue(self.SPC_single_threshold)
        self._spcsinglethresholdLayout = qt.QHBoxLayout()
        self._spcsinglethresholdLayout.addWidget(
            qt.QLabel('Single count threshold'))
        self._spcsinglethresholdLayout.addWidget(qt.HorizontalSpacer())
        self._spcsinglethresholdLayout.addWidget(
            self._spcsinglethresholdDoubleSpinBox)
        self._spcsinglethresholdWidget = qt.QWidget()
        self._spcsinglethresholdWidget.setLayout(self._spcsinglethresholdLayout)
        
        self._spcdoublethresholdDoubleSpinBox = qt.QDoubleSpinBox()
        self._spcdoublethresholdDoubleSpinBox.setMaximumWidth(100)
        self._spcdoublethresholdDoubleSpinBox.setMinimumWidth(70)
        self._spcdoublethresholdDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._spcdoublethresholdDoubleSpinBox.setMinimum(0)
        self._spcdoublethresholdDoubleSpinBox.setMaximum(5)
        self._spcdoublethresholdDoubleSpinBox.setSingleStep(.05)
        self._spcdoublethresholdDoubleSpinBox.setValue(self.SPC_double_threshold)
        self._spcdoublethresholdLayout = qt.QHBoxLayout()
        self._spcdoublethresholdLayout.addWidget(
            qt.QLabel('Double count threshold'))
        self._spcdoublethresholdLayout.addWidget(qt.HorizontalSpacer())
        self._spcdoublethresholdLayout.addWidget(
            self._spcdoublethresholdDoubleSpinBox)
        self._spcdoublethresholdWidget = qt.QWidget()
        self._spcdoublethresholdWidget.setLayout(self._spcdoublethresholdLayout)
        
        self._spcParamsLayout.addWidget(self._spcgridsizeWidget)
        self._spcParamsLayout.addWidget(self._spclowthresholdWidget)
        self._spcParamsLayout.addWidget(self._spchighthresholdWidget)
        self._spcParamsLayout.addWidget(self._spcsinglethresholdWidget)
        self._spcParamsLayout.addWidget(self._spcdoublethresholdWidget)
        self._spcParamsWidget.setLayout(self._spcParamsLayout)
        self._mainLayout.addWidget(self._spcParamsWidget)
        
        
        self._detParamsWidget = qt.QGroupBox()
        self._detParamsWidget.setTitle('Detector properties')
        self._detParamsLayout = qt.QVBoxLayout()
        
        self._detdarkcountsDoubleSpinBox = qt.QDoubleSpinBox()
        self._detdarkcountsDoubleSpinBox.setMaximumWidth(100)
        self._detdarkcountsDoubleSpinBox.setMinimumWidth(70)
        self._detdarkcountsDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._detdarkcountsDoubleSpinBox.setDecimals(5)
        self._detdarkcountsDoubleSpinBox.setMinimum(0)
        self._detdarkcountsDoubleSpinBox.setMaximum(1)
        self._detdarkcountsDoubleSpinBox.setValue(0.00016)
        self._detdarkcountsDoubleSpinBox.setSingleStep(2e-5)
        self._detdarkcountsDoubleSpinBox.setEnabled(False)
        self._detdarkcountsLayout = qt.QHBoxLayout()
        self._detdarkcountsLayout.addWidget(qt.QLabel('Dark counts'))
        self._detdarkcountsLayout.addWidget(qt.HorizontalSpacer())
        self._detdarkcountsLayout.addWidget(self._detdarkcountsDoubleSpinBox)
        self._detdarkcountsWidget = qt.QWidget()
        self._detdarkcountsWidget.setLayout(self._detdarkcountsLayout)
        # !!! User can still set even numbers
        
        self._detefficiencyDoubleSpinBox = qt.QDoubleSpinBox()
        self._detefficiencyDoubleSpinBox.setMaximumWidth(100)
        self._detefficiencyDoubleSpinBox.setMinimumWidth(70)
        self._detefficiencyDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._detefficiencyDoubleSpinBox.setMinimum(1)
        self._detefficiencyDoubleSpinBox.setMaximum(100)
        self._detefficiencyDoubleSpinBox.setSingleStep(.1)
        self._detefficiencyDoubleSpinBox.setValue(2.5)
        self._detefficiencyDoubleSpinBox.setEnabled(False)
        self._detefficiencyLayout = qt.QHBoxLayout()
        self._detefficiencyLayout.addWidget(qt.QLabel('Electrons per count'))
        self._detefficiencyLayout.addWidget(qt.HorizontalSpacer())
        self._detefficiencyLayout.addWidget(self._detefficiencyDoubleSpinBox)
        self._detefficiencyWidget = qt.QWidget()
        self._detefficiencyWidget.setLayout(self._detefficiencyLayout)
        
        self._detehenergyDoubleSpinBox = qt.QDoubleSpinBox()
        self._detehenergyDoubleSpinBox.setMaximumWidth(100)
        self._detehenergyDoubleSpinBox.setMinimumWidth(70)
        self._detehenergyDoubleSpinBox.setAlignment(qt.Qt.AlignRight)
        self._detehenergyDoubleSpinBox.setMinimum(0)
        self._detehenergyDoubleSpinBox.setMaximum(20)
        self._detehenergyDoubleSpinBox.setSingleStep(.1)
        self._detehenergyDoubleSpinBox.setValue(3.6)
        self._detehenergyDoubleSpinBox.setEnabled(False)
        self._detehenergyLayout = qt.QHBoxLayout()
        self._detehenergyLayout.addWidget(qt.QLabel('Electron-hole pair energy'))
        self._detehenergyLayout.addWidget(qt.HorizontalSpacer())
        self._detehenergyLayout.addWidget(self._detehenergyDoubleSpinBox)
        self._detehenergyWidget = qt.QWidget()
        self._detehenergyWidget.setLayout(self._detehenergyLayout)
        
        
        self._expertDialogButtonBox = qt.QDialogButtonBox()
        #self._expertApplyButton = qt.QPushButton()
        #self._expertCancelButton = qt.QPushButton()
        #self._expertApplyButton.setFlag('Apply')
        #self._expertDialogButtonBox.addButton(self._expertApplyButton)
        
       
        self._detParamsLayout.addWidget(self._detdarkcountsWidget)
        self._detParamsLayout.addWidget(self._detefficiencyWidget)
        self._detParamsLayout.addWidget(self._detehenergyWidget)
        self._detParamsWidget.setLayout(self._detParamsLayout)
        self._mainLayout.addWidget(self._detParamsWidget)
        self._mainLayout.addWidget(self._expertDialogButtonBox)
        
        
        self.setLayout(self._mainLayout)
        
        #qui
        
        self._Apply=self._expertDialogButtonBox.addButton(qt.QDialogButtonBox.Apply)
        self._Cancel=self._expertDialogButtonBox.addButton(qt.QDialogButtonBox.Cancel)
        self._Reset=self._expertDialogButtonBox.addButton(qt.QDialogButtonBox.Reset)
        #self._Apply= ApplyWidget(self)
        
        
        self.connect(self._Cancel,
              qt.SIGNAL('clicked()'), self._closeWindow) 
              
        self.connect(self._Reset,
              qt.SIGNAL('clicked()'), self._resetWindow)
              
        self.connect(self._Apply, qt.SIGNAL('clicked()'), 
            self.ApplyButtonclicked)   
    
    
    def ApplyButtonclicked(self):
        print("Apply button clicked")
        qt.QObject.emit(self, qt.SIGNAL('ApplyButtonClicked'), 
            'APPLY_BUTTON')
        self.parent.lower_threshold = self._lowerthresholdDoubleSpinBox.value()
        self.parent.upper_threshold = self._upperthresholdDoubleSpinBox.value()
        self.parent.masksize = self._masksizeSpinBox.value()
        self.parent.SPC_gridsize = self._spcgridsizeSpinBox.value()
        self.parent.SPC_low_threshold = self._spclowthresholdDoubleSpinBox.value()
        self.parent.SPC_high_threshold = self._spchighthresholdDoubleSpinBox.value()
        self.parent.SPC_single_threshold = self._spcsinglethresholdDoubleSpinBox.value()
        self.parent.SPC_double_threshold = self._spcdoublethresholdDoubleSpinBox.value()
        
        self.close()
    
    
   


class ExportWidget(qt.QGroupBox):
    def __init__(self, parent=None):
        qt.QGroupBox.__init__(self, parent)
        
        self.parent= parent
        self.targetFolder= None
        self.exportOptions = {}
        
        self.build()
        
    
    def build(self):
        
        
        self._folderLineEdit = qt.QLineEdit(self)
        self._folderLineEdit.setReadOnly(True)
        
        self._openButton = qt.QToolButton(self)
        self._openButton.setIcon(qt.QIcon(qt.QPixmap(IconDict['fileopen'])))
        self._openButton.setToolTip('Select target folder')
        self.connect(self._openButton, qt.SIGNAL('clicked()'), 
            self.openButtonclicked)
        
        folderLayout = qt.QHBoxLayout()
        folderLayout.addWidget(self._folderLineEdit)
        folderLayout.addWidget(self._openButton)
        folderLayout.setMargin(0)
        folderLayout.setSpacing(5)
        folderWidget = qt.QWidget()
        folderWidget.setLayout(folderLayout)
        
        self._datCheckBox = qt.QCheckBox()
        self._datCheckBox.setText('Save to *.dat file')
        self._datCheckBox.setCheckState(False)
        self._datCheckBox.setTristate(False)
        self._datCheckBox.setEnabled(False)
        
        self.askFileNameCheckBox = qt.QCheckBox()
        self.askFileNameCheckBox.setText('Ask for *.dat filename')
        self.askFileNameCheckBox.setCheckState(False)
        self.askFileNameCheckBox.setTristate(False)
        self.askFileNameCheckBox.setEnabled(False)
        
        
        self._mainLayout = qt.QGridLayout(self)
        self._mainLayout.setMargin(10)
        self._mainLayout.setSpacing(5)
        self.setTitle('Output file')
        self._mainLayout.addWidget(folderWidget, 0, 0, 1, 2)
        self._mainLayout.addWidget(self._datCheckBox, 1, 0, 1, 1)
        self._mainLayout.addWidget(self.askFileNameCheckBox, 1, 1, 1, 1)
        self.setLayout(self._mainLayout)
        
        
    def savedatfile(self):
        return self._datCheckBox.isChecked()
    
    def askForScanName(self):
        return self.askFileNameCheckBox.isChecked()
    
    def getScanName(self, path='./'):
        dialog = DatFileDialog(path)
        if dialog.exec_() == qt.QDialog.Accepted:
            command = dialog.lineEdit.text()
        else:
            command = None
        dialog.deleteLater()
        return command
    
    def openButtonclicked(self):
        outfile = qt.QFileDialog(self)
        outfile.setWindowTitle("Output File")
        outfile.setModal(1)
        filterlist = ['Specfile, *.spec', 'All files, *.*']
        outfile.setFilters(filterlist)
        outfile.selectFilter(filterlist[0])
        outfile.setFileMode(outfile.AnyFile)
        outfile.setAcceptMode(outfile.AcceptSave)
        outfile.setAcceptMode(False)
        ret = outfile.exec_()
        
        if not ret:
            return None
        
        self.outputFilter = qt.safe_str(outfile.selectedFilter())
        filterused = self.outputFilter.split(',')
        filetype  = filterused[0]
        extension = filterused[1].strip().replace('*', '')
        if extension == '.':
            extension = ''
        
        outdir = qt.safe_str(outfile.selectedFiles()[0])
        try:
            self.outputDir  = os.path.dirname(outdir)
        except:
            print("setting output directory to default")
            self.outputDir  = os.getcwd()
        try:
            outputFile = os.path.basename(outdir)
        except:
            outputFile = outdir
        outfile.close()
        del outfile
        
        
        if not outputFile.endswith(extension):
            outputFile = outputFile + extension
        self.outputFile = '/'.join([self.outputDir, outputFile])
        
        self.outputFile = qt.safe_str(self.outputFile)
        self._folderLineEdit.setText(self.outputFile)
        self._datCheckBox.setEnabled(True)
        self.askFileNameCheckBox.setEnabled(True)
        
        qt.QObject.emit(self, qt.SIGNAL('OutputFileSelected'), 'OutputOK')
        
        return 0
        

class DatFileDialog(qt.QDialog):
    def __init__(self, path='./'):
        qt.QDialog.__init__(self)
        
        self.path = path
        self.label = qt.QLabel()
        self.lineEdit = qt.QLineEdit()
        self.lineEdit.textEdited.connect(self.updateLabel)
        self.buttonOk = qt.QPushButton('Ok', self)
        self.buttonOk.clicked.connect(self.accept)
        self.buttonCancel = qt.QPushButton('Cancel', self)
        self.buttonCancel.clicked.connect(self.reject)
        
        self.layout = qt.QGridLayout()
        self.layout.addWidget(qt.QLabel('File will be save in:'), 0, 0, 1, 2)
        self.layout.addWidget(self.label, 1, 0, 1, 2)
        self.layout.addWidget(self.lineEdit, 2, 0, 1, 2)
        self.layout.addWidget(self.buttonOk, 3, 0, 1, 1)
        self.layout.addWidget(self.buttonCancel, 3, 1, 1, 1)
        self.setLayout(self.layout)
        self.updateLabel()
    
    def updateLabel(self):
        self.label.setText('%s_%s.dat' % (self.path, self.lineEdit.text()))
    



if __name__ == "__main__":
    import numpy as np
    
    app = qt.QApplication([])
    qt.QObject.connect(app, qt.SIGNAL('lastWindowClosed()'), app, 
        qt.SLOT('quit()'))


    w = MainWindow()
    w.show()
    app.exec_()
        
