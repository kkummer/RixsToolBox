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

import os

from PyMca5.PyMcaGui import PyMcaQt as qt

import SpecGenGUI
import SpecSumGUI
import SpecEcalibGUI
import SpecSlopeGUI
import SpecCalibCoefGUI

from RTB_Icons import RtbIcons

class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        
        self.app_name = 'RixsToolbox'
        self.version = '0.1'
        
        self.setWindowTitle('%s - Main' % self.app_name)
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons['Logo'])))
        self.setWindowFlags(qt.Qt.WindowTitleHint)
        self.build()
        self.setMaximumSize(self.sizeHint())
        
        
    
        self.specgenWindows = []
        self.specsumWindows = []
        self.speccalibWindows = []
        self.slopeWindows = []
        self.coeffWindows = []
        self.helpDialog=None
    
    
    def build(self):
        # Create buttons
        specgenButton = self._addButton('Generate spectra', 'SpecGen', 75)
        specsumButton = self._addButton('Align and sum spectra', 'SpecSum', 75)
        speccalibButton = self._addButton('Energy calibration', 'SpecEcalib', 75)
        slopeButton = self._addButton('Find slope', 'Slope', 32)
        coeffButton = self._addButton('Find energy calibration', 'Calcoeff', 32)
        infoButton = self._addButton('About', 'Info', 32)
        helpButton = self._addButton('Help', 'Help', 32)
        dismissButton = self._addButton('Quit', 'Quit', 75)
        
        #~ infoButton.setDisabled(True)
        #~ helpButton.setDisabled(True)
        
        # Build layout
        mainLayout = qt.QGridLayout(self)
        mainLayout.setMargin(10)
        mainLayout.setSpacing(10)
        
        mainLayout.addWidget(specgenButton, 0, 0, 1, 2)
        mainLayout.addWidget(specsumButton, 1, 0, 1, 2)
        mainLayout.addWidget(speccalibButton, 2, 0, 1, 2)
        mainLayout.addWidget(slopeButton, 3, 0, 1, 1)
        mainLayout.addWidget(coeffButton, 3, 1, 1, 1)
        mainLayout.addWidget(
            qt.QFrame(frameShape='HLine', frameShadow='Sunken'), 4, 0, 1, 2)
        mainLayout.addWidget(helpButton, 5, 0, 1, 1)
        mainLayout.addWidget(infoButton, 5, 1, 1, 1)
        mainLayout.addWidget(dismissButton, 6, 0, 1, 2)
        self.setLayout(mainLayout)
        
        # Connect signals
        specgenButton.clicked.connect(self._specgenButtonClicked)
        specsumButton.clicked.connect(self._specsumButtonClicked)
        speccalibButton.clicked.connect(self._speccalibButtonClicked)
        slopeButton.clicked.connect(self._coeffButtonClicked)
        coeffButton.clicked.connect(self._slopeButtonClicked)
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
            button.setIconSize(qt.QSize(min([50, int(0.8*size)]),min([50, int(0.8*size)])))
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
    
    def _slopeButtonClicked(self):
        self.slopeWindows.append(SpecSlopeGUI.MainWindow())
        self.slopeWindows[-1].show()
    
    def _coeffButtonClicked(self):
        self.coeffWindows.append(SpecCalibCoefGUI.MainWindow())
        self.coeffWindows[-1].show()
    
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
            '<p>RixsToolbox is a collection of data analysis routines for ',
            'data taken at the ESRF ID32 RIXS spectrometer.</p>',
            '<p>This software heavily relies on ',
            '<a href="http://pymca.sourceforge.net/">PyMca</a>. ',
            'It is work in progress and provided "as it is". '
            'Feature request and bug reports are very welcome.</p>',
            'Authors: %s<br>' % ',  '.join(authors),
            'Contact: <a href="mailto:%s">%s</a><br><br>' % (email, email),
            'Copyright (C) 2016 European Synchrotron Radiation Facility',
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
    app = qt.QApplication([])
    qt.QObject.connect(app, qt.SIGNAL('lastWindowClosed()'), app, 
        qt.SLOT('quit()'))


    w = MainWindow()
    w.show()
    app.exec_()
        
