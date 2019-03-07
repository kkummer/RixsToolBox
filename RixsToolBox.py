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

__author__ = ["Kurt Kummer", "Annalisa Tamborrino"]
__contact__ = "kurt.kummer@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

___doc__ = """
    ...
"""

def RixsToolBoxVersion():
    return '0.6.1'


import sys
import os


from PyMca5.PyMcaGui import PyMcaQt as qt
# ~ from silx.gui import qt

if __name__ == '__main__':
    from RTB_SplashScreen import splash_xpm
    app = qt.QApplication(sys.argv)
    splash_pix = qt.QPixmap(splash_xpm)
    splash = qt.QSplashScreen(splash_pix)
    splash.setEnabled(False)
    splash.showMessage('<h3><font color=white>RixsToolBox v%s</font></h3>' % RixsToolBoxVersion(), qt.Qt.AlignRight)
    splash.setMask(splash_pix.mask())
    splash.show()
    splash.raise_()
    

import time

import RTB_SpecGen as SpecGenGUI
import RTB_SpecSum as SpecSumGUI
import RTB_EnergyCalibration as SpecEcalibGUI
import RTB_SlopeFinder as SpecSlopeGUI
import RTB_SpecCalibCoef as SpecCalibCoefGUI
import RTB_Polarimeter
import RTB_MapGenerator
import RTB_Alignment

from RTB_Icons import RtbIcons





class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        
        self.app_name = 'RixsToolBox'
        self.version = RixsToolBoxVersion()
        
        self.setWindowTitle('%s' % self.app_name)
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.setWindowFlags(qt.Qt.WindowTitleHint)
        self.build()
        self.setMaximumSize(self.sizeHint())
        
        
    
        self.specgenWindows = []
        self.specsumWindows = []
        self.speccalibWindows = []
        self.polarimeterWindows = []
        self.mapWindows = []
        self.slopeWindows = []
        self.coeffWindows = []
        self.alignmentWindows = []
        self.helpDialog=None
    
    
    def build(self):
        # Create buttons
        specgenButton = self._addButton('Generate spectra', 'SpecGen', 70)
        specsumButton = self._addButton('Align and sum spectra', 'SpecSum', 70)
        speccalibButton = self._addButton('Convert pixel to energy', 'SpecEcalib', 70)
        mapButton = self._addButton('Generate map', 'Map', 70)
        polarimeterButton = self._addButton('Analyse polarimeter data', 'Polarimeter', 70)
        # ~ dummyButton = self._addButton('', None, 70)
        # ~ dummyButton.setEnabled(False)
        
        slopeButton = self._addButton('Determine slope', 'Slope', 40)
        coeffButton = self._addButton('Determine energy calibration', 'Calcoeff', 40)
        alignmentButton = self._addButton('Alignment', 'Alignment', 40)
        
        infoButton = self._addButton('About', 'Info', 40)
        helpButton = self._addButton('Help', 'Help', 40)
        helpButton.setDisabled(True)
        dismissButton = self._addButton('Quit', 'Quit', 40)
        
        
        # Build layout
        expertLayout = qt.QHBoxLayout()
        expertLayout.setContentsMargins(0, 0, 0, 0)
        expertLayout.setSpacing(10)
        expertLayout.addWidget(slopeButton)
        expertLayout.addWidget(coeffButton)
        expertLayout.addWidget(alignmentButton)
        expertWidget = qt.QWidget()
        expertWidget.setLayout(expertLayout)
        
        infoLayout = qt.QHBoxLayout()
        infoLayout.setContentsMargins(0, 0, 0, 0)
        infoLayout.setSpacing(10)
        infoLayout.addWidget(helpButton)
        infoLayout.addWidget(infoButton)
        infoLayout.addWidget(dismissButton)
        infoWidget = qt.QWidget()
        infoWidget.setLayout(infoLayout)
        
        mainLayout = qt.QGridLayout(self)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(10)
        mainLayout.addWidget(specgenButton, 0, 0, 1, 1)
        mainLayout.addWidget(specsumButton, 0, 1, 1, 1)
        mainLayout.addWidget(speccalibButton, 1, 0, 1, 1)
        mainLayout.addWidget(mapButton, 1, 1, 1, 1)
        mainLayout.addWidget(polarimeterButton, 2, 0, 1, 1)
        # ~ mainLayout.addWidget(dummyButton, 2, 1, 1, 1)
        mainLayout.addWidget(
            qt.QFrame(frameShape='HLine', frameShadow='Sunken'), 3, 0, 1, 2)
        mainLayout.addWidget(expertWidget, 4, 0, 1, 2)
        mainLayout.addWidget(
            qt.QFrame(frameShape='HLine', frameShadow='Sunken'), 5, 0, 1, 2)
        mainLayout.addWidget(infoWidget, 6, 0, 1, 2)
        self.setLayout(mainLayout)
        
        # Connect signals
        specgenButton.clicked.connect(self._specgenButtonClicked)
        specsumButton.clicked.connect(self._specsumButtonClicked)
        speccalibButton.clicked.connect(self._speccalibButtonClicked)
        mapButton.clicked.connect(self._mapButtonClicked)
        polarimeterButton.clicked.connect(self._polarimeterButtonClicked)
        slopeButton.clicked.connect(self._slopeButtonClicked)
        coeffButton.clicked.connect(self._coeffButtonClicked)
        alignmentButton.clicked.connect(self.alignmentButtonClicked)
        infoButton.clicked.connect(self.infoButtonClicked)
        helpButton.clicked.connect(self.helpButtonClicked)
        dismissButton.clicked.connect(qt.QCoreApplication.instance().quit)
        
    
    def _addButton(self, label='', icon=None, size=75):
        button = qt.QPushButton(self)
        button.resize(size,size)
        button.setMinimumSize(size,size)
        button.setMaximumSize(size,size)
        if icon != None:
            buttonIcon = qt.QIcon()
            buttonIcon.addPixmap(qt.QPixmap(RtbIcons[icon]))
            button.setIcon(buttonIcon)
            button.setIconSize(qt.QSize(min([60, int(0.85*size)]),min([60, int(0.85*size)])))
            button.setToolTip(label)
        else:
            button.setText(label.replace(' ', '\n'))
        return button
    
    
    def _specgenButtonClicked(self):
        self.specgenWindows.append(SpecGenGUI.MainWindow())
        self.specgenWindows[-1].show()
    
    
    def _specsumButtonClicked(self):
        self.specsumWindows.append(SpecSumGUI.MainWindow())
        self.specsumWindows[-1].show()
    
    
    def _speccalibButtonClicked(self):
        self.speccalibWindows.append(SpecEcalibGUI.MainWindow())
        self.speccalibWindows[-1].show()
    
    
    def _polarimeterButtonClicked(self):
        self.polarimeterWindows.append(RTB_Polarimeter.MainWindow())
        self.polarimeterWindows[-1].show()
    
    def _mapButtonClicked(self):
        self.mapWindows.append(RTB_MapGenerator.MainWindow())
        self.mapWindows[-1].show()
    
    def _slopeButtonClicked(self):
        self.slopeWindows.append(SpecSlopeGUI.MainWindow())
        self.slopeWindows[-1].show()
    
    def _coeffButtonClicked(self):
        self.coeffWindows.append(SpecCalibCoefGUI.MainWindow())
        self.coeffWindows[-1].show()
    
    def alignmentButtonClicked(self):
        self.alignmentWindows.append(RTB_Alignment.MainWindow())
        self.alignmentWindows[-1].show()
    
    
    def infoButtonClicked(self):
        authors = ['Kurt Kummer', 'Annalisa Tamborrino']
        email = 'kurt.kummer@esrf.fr'
        
        self.aboutDialog = qt.QMessageBox(self)
        self.aboutDialog.setWindowTitle('About')
        self.aboutDialog.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Info'])))
        self.aboutDialog.setTextFormat(qt.Qt.RichText)
        self.aboutDialog.setIconPixmap(qt.QPixmap(RtbIcons['InfoLogo']))
        txt = ''.join([
            '<p><b><text style="font-size:x-large">%s</text> v%s</b></p>' \
                % (self.app_name, self.version),
            '<p>RixsToolBox is a collection of data analysis routines for ',
            'data taken at the ESRF ID32 RIXS spectrometer. ',
            'Its latest version is available from<br>',
            '<a href="https://github.com/kkummer/RixsToolBox/releases">',
            'https://github.com/kkummer/RixsToolBox/releases</a><p>',
            '<p><i>J. Synchrotron Rad. <b>24</b>, 531 (2017)</i><br>'
            '<a href="https://doi.org/10.1107/S1600577517000832">https://doi.org/10.1107/S1600577517000832</a></p> ',
            '<p>For feature request and bug reports please contact<br>',
            '<a href="mailto:%s">%s</a></p>' % (email, email),
            'Authors: %s<br>' % ',  '.join(authors),
            '(C) 2016-%s European Synchrotron Radiation Facility' % time.strftime('%Y'),
            ])
        self.aboutDialog.setInformativeText(txt)
        aboutQtButton = self.aboutDialog.addButton(qt.QMessageBox.Ignore)
        aboutQtButton.setText('About Qt')
        aboutQtButton.clicked.connect(self.qtMessage)
        self.aboutDialog.addButton(qt.QMessageBox.Close)
        self.aboutDialog.exec_()
    
    
    def helpButtonClicked(self):
        if self.helpDialog is None:
            self.helpDialog=qt.QTextBrowser()
            self.helpDialog.setWindowTitle('Help')
            self.helpDialog.setSource(qt.QUrl(qt.safe_str("../manual/help.html")))
            self.helpDialog.show()
        if self.helpDialog.isHidden():
            self.helpDialog.show()
        self.helpDialog.raise_()
    
    def qtMessage(self):
        qt.QMessageBox.aboutQt(self.aboutDialog, "About Qt")



if __name__ == "__main__":
    app.lastWindowClosed.connect(app.quit)
    # ~ if 'Fusion' in qt.QStyleFactory.keys():
        # ~ app.setStyle('Fusion')


    w = MainWindow()
    splash.finish(w)
    w.show()
    sys.exit(app.exec_())
        
