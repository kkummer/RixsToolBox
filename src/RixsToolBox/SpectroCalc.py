#!/usr/bin/env python
# -*- coding: utf-8 -*-

# /*##########################################################################
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


import copy
import math
import os
import re
import time

import numpy as np
from PyMca5.PyMcaGui import IconDict
from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.plotting import PlotWidget

from RixsToolBox.GratingEfficiencies import RtbGratingEfficiencies
from RixsToolBox.Icons import RtbIcons
from RixsToolBox.Math import RtbMath


class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        self.setWindowTitle("RixsToolBox - Spectrometer calculations")
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons["Logo"])))

        self.RTB_Math = RtbMath()

        self.load_motor_parameters()
        self.load_grating_parameters()
        self.load_detector_parameters()
        self.masksize = 6
        self.maskdistance = 200
        self.build()
        self.connect_signals()

    def build(self):
        self.grating_pars = {}
        self.positions = {}

        self.intValidator = qt.QIntValidator()
        self.doubleValidator = qt.QDoubleValidator()

        self.colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

        # Global parameters ----------------------------------------------------

        energyLabel = qt.QLabel("Energy (eV)")
        energyLabel.setStyleSheet("font: bold")
        self.energySpinBox = qt.QDoubleSpinBox()
        self.energySpinBox.setDecimals(1)
        self.energySpinBox.setSingleStep(1)
        self.energySpinBox.setMinimum(300)
        self.energySpinBox.setMaximum(2000)
        self.energySpinBox.setValue(930)
        self.energySpinBox.setMinimumWidth(95)
        self.energySpinBox.setMaximumWidth(95)
        self.energySpinBox.setStyleSheet("font: bold")
        self.energySpinBox.setAlignment(qt.Qt.AlignRight)

        alphaLabel = qt.QLabel("Grating angle \u03b1 (\u00b0)")
        alphaLabel.setStyleSheet("font: bold")
        self.alphaSpinBox = qt.QDoubleSpinBox()
        self.alphaSpinBox.setDecimals(4)
        self.alphaSpinBox.setSingleStep(0.05)
        self.alphaSpinBox.setMinimum(85)
        self.alphaSpinBox.setMaximum(89.9)
        self.alphaSpinBox.setValue(88)
        self.alphaSpinBox.setMinimumWidth(95)
        self.alphaSpinBox.setMaximumWidth(95)
        self.alphaSpinBox.setStyleSheet("font: bold")
        self.alphaSpinBox.setAlignment(qt.Qt.AlignRight)

        s1Label = qt.QLabel("Source size (\u03bcm)")
        self.s1SpinBox = qt.QDoubleSpinBox()
        self.s1SpinBox.setDecimals(2)
        self.s1SpinBox.setSingleStep(0.1)
        self.s1SpinBox.setMinimum(0.1)
        self.s1SpinBox.setMaximum(100)
        self.s1SpinBox.setMinimumWidth(95)
        self.s1SpinBox.setMaximumWidth(95)
        self.s1SpinBox.setValue(2)
        self.s1SpinBox.setAlignment(qt.Qt.AlignRight)

        enealphaLayout = qt.QGridLayout()
        enealphaLayout.setHorizontalSpacing(20)
        enealphaLayout.addWidget(energyLabel, 0, 0, 1, 1)
        enealphaLayout.addWidget(self.energySpinBox, 0, 1, 1, 1)
        enealphaLayout.addWidget(alphaLabel, 1, 0, 1, 1)
        enealphaLayout.addWidget(self.alphaSpinBox, 1, 1, 1, 1)
        enealphaLayout.addWidget(s1Label, 2, 0, 1, 1)
        enealphaLayout.addWidget(self.s1SpinBox, 2, 1, 1, 1)
        enealphaWidget = qt.QWidget()
        enealphaWidget.setLayout(enealphaLayout)

        # Grating parameters ---------------------------------------------------
        gratingLayout = qt.QGridLayout()
        gratingLayout.setHorizontalSpacing(20)

        self.gratingComboBox = qt.QComboBox()
        for grating in self.gratings:
            self.gratingComboBox.addItem(grating)
        gratingLayout.addWidget(self.gratingComboBox, 0, 0, 1, 2)

        self.gratingSpinBoxes = {}
        current_grating = self.gratingComboBox.currentText()
        for iii, param in enumerate(self.gratings[current_grating]):
            self.gratingSpinBoxes[param] = ScientificDoubleSpinBox()
            self.gratingSpinBoxes[param].setAlignment(qt.Qt.AlignRight)
            self.gratingSpinBoxes[param].setMaximumWidth(95)
            self.gratingSpinBoxes[param].setMaximumWidth(95)
            qLabel = qt.QLabel("%s (%s)" % (param, self.gratingParameterUnits[param]))
            gratingLayout.addWidget(qLabel, iii + 1, 0, 1, 1)
            gratingLayout.addWidget(self.gratingSpinBoxes[param], iii + 1, 1, 1, 1)

        gratingWidget = qt.QGroupBox("Grating parameters")
        gratingWidget.setLayout(gratingLayout)
        gratingWidget.setMinimumWidth(290)
        gratingWidget.setMaximumWidth(290)

        # Grating mask parameters ----------------------------------------------
        maskLayout = qt.QGridLayout()
        maskLayout.setHorizontalSpacing(20)
        self.maskSpinBox = ScientificDoubleSpinBox()
        self.maskSpinBox.setAlignment(qt.Qt.AlignRight)
        self.maskSpinBox.setMinimumWidth(95)
        self.maskSpinBox.setMaximumWidth(95)
        self.maskSpinBox.setValue(self.masksize)
        qLabel = qt.QLabel("mask size (mm)")
        maskLayout.addWidget(qLabel, 0, 0, 1, 1)
        maskLayout.addWidget(self.maskSpinBox, 0, 1, 1, 1)
        self.maskdistanceSpinBox = ScientificDoubleSpinBox()
        self.maskdistanceSpinBox.setAlignment(qt.Qt.AlignRight)
        self.maskdistanceSpinBox.setMinimumWidth(95)
        self.maskdistanceSpinBox.setMaximumWidth(95)
        self.maskdistanceSpinBox.setValue(self.maskdistance)
        qLabel = qt.QLabel("distance to grating (mm)")
        maskLayout.addWidget(qLabel, 1, 0, 1, 1)
        maskLayout.addWidget(self.maskdistanceSpinBox, 1, 1, 1, 1)
        maskWidget = qt.QGroupBox("Grating mask")
        maskWidget.setLayout(maskLayout)
        maskWidget.setMinimumWidth(290)
        maskWidget.setMaximumWidth(290)

        # Detector parameters --------------------------------------------------
        detectorLayout = qt.QGridLayout()
        detectorLayout.setHorizontalSpacing(20)

        self.detectorSpinBoxes = {}
        for iii, param in enumerate(self.detector):
            self.detectorSpinBoxes[param] = ScientificDoubleSpinBox()
            self.detectorSpinBoxes[param].setAlignment(qt.Qt.AlignRight)
            self.detectorSpinBoxes[param].setMinimumWidth(95)
            self.detectorSpinBoxes[param].setMaximumWidth(95)
            qLabel = qt.QLabel("%s (%s)" % (param, self.detectorParameterUnits[param]))
            detectorLayout.addWidget(qLabel, iii + 1, 0, 1, 1)
            detectorLayout.addWidget(self.detectorSpinBoxes[param], iii + 1, 1, 1, 1)
            self.detectorSpinBoxes[param].setValue(self.detector[param])

        detectorWidget = qt.QGroupBox("Detector parameters")
        detectorWidget.setLayout(detectorLayout)
        detectorWidget.setMinimumWidth(290)
        detectorWidget.setMaximumWidth(290)

        # Spectrometer positions -----------------------------------------------
        positionsLayout = qt.QGridLayout()
        positionsLayout.setHorizontalSpacing(15)

        labels = {
            "beta": "diffraction angle \u03B2 (\u00B0)",
            "r1": "entrance arm r\u2081 (mm)",
            "r2": "exit arm r\u2082 (mm)",
            "detx": "detx (mm)",
            "detz": "detz (mm)",
        }

        self.positionsLineEdits = {}
        for iii, (pos, label) in enumerate(labels.items()):
            positionsLayout.addWidget(qt.QLabel(label), iii, 0, 1, 1)
            self.positionsLineEdits[pos] = qt.QLineEdit()
            self.positionsLineEdits[pos].setAlignment(qt.Qt.AlignRight)
            self.positionsLineEdits[pos].setMinimumWidth(80)
            self.positionsLineEdits[pos].setMaximumWidth(80)
            self.positionsLineEdits[pos].setReadOnly(True)
            positionsLayout.addWidget(self.positionsLineEdits[pos], iii, 1, 1, 1)

        positionsWidget = qt.QGroupBox("Positions")
        positionsWidget.setLayout(positionsLayout)

        # Dispersion information -----------------------------------------------

        labels = {
            "dispersion": "dispersion (meV/px)",
            "gamma": "dispersion plane angle \u03B3 (\u00B0)",
            "energy window": "detector energy window (eV)",
        }

        dispersionLayout = qt.QGridLayout()
        dispersionLayout.setHorizontalSpacing(15)
        for iii, (pos, label) in enumerate(labels.items()):
            dispersionLayout.addWidget(qt.QLabel(label), iii, 0, 1, 1)
            self.positionsLineEdits[pos] = qt.QLineEdit()
            self.positionsLineEdits[pos].setAlignment(qt.Qt.AlignRight)
            self.positionsLineEdits[pos].setMinimumWidth(80)
            self.positionsLineEdits[pos].setMaximumWidth(80)
            self.positionsLineEdits[pos].setReadOnly(True)
            dispersionLayout.addWidget(self.positionsLineEdits[pos], iii, 1, 1, 1)

        dispersionWidget = qt.QGroupBox("Dispersion")
        dispersionWidget.setLayout(dispersionLayout)

        # Dispersion information -----------------------------------------------

        labels = {
            "used grating length": "used grating length (mm)",
            "acceptanceV": "vertical acceptance (mrad)",
            # ~ 'magnification': 'magnification',
        }

        infoLayout = qt.QGridLayout()
        infoLayout.setHorizontalSpacing(15)
        for iii, (pos, label) in enumerate(labels.items()):
            infoLayout.addWidget(qt.QLabel(label), iii, 0, 1, 1)
            self.positionsLineEdits[pos] = qt.QLineEdit()
            self.positionsLineEdits[pos].setAlignment(qt.Qt.AlignRight)
            self.positionsLineEdits[pos].setMinimumWidth(80)
            self.positionsLineEdits[pos].setMaximumWidth(80)
            self.positionsLineEdits[pos].setReadOnly(True)
            infoLayout.addWidget(self.positionsLineEdits[pos], iii, 1, 1, 1)

        infoWidget = qt.QGroupBox("Acceptance")
        infoWidget.setLayout(infoLayout)

        # Spectrometer resolution ----------------------------------------------
        resolutionLayout = qt.QGridLayout()
        resolutionLayout.setHorizontalSpacing(15)

        labels = {
            "S1": "\u0394E source size (meV)",
            "S2": "\u0394E detector (meV)",
            "SE": "\u0394E slope error (meV)",
            "DL": "\u0394E diffraction limit (meV)",
            "total": "\u0394E total (meV)",
            "RP": "resolving power",
        }

        self.resolutionLineEdits = {}
        for iii, (pos, label) in enumerate(labels.items()):
            color = self.colors[iii]
            qlabel = qt.QLabel(label)
            resolutionLayout.addWidget(qlabel, iii, 0, 1, 1)
            self.resolutionLineEdits[pos] = qt.QLineEdit()
            self.resolutionLineEdits[pos].setAlignment(qt.Qt.AlignRight)
            self.resolutionLineEdits[pos].setMinimumWidth(80)
            self.resolutionLineEdits[pos].setMaximumWidth(80)
            self.resolutionLineEdits[pos].setReadOnly(True)
            resolutionLayout.addWidget(self.resolutionLineEdits[pos], iii, 1, 1, 1)

        resolutionWidget = qt.QGroupBox("Resolution")
        resolutionWidget.setLayout(resolutionLayout)

        # Resolution tab ------------------------------------------------------
        resTabLayout = qt.QGridLayout()
        resTabLayout.setHorizontalSpacing(15)

        labels = {
            "S1": "\u0394E source size (meV)",
            "S2": "\u0394E detector (meV)",
            "SE": "\u0394E slope error (meV)",
            "DL": "\u0394E diffraction limit (meV)",
            "total": "\u0394E total (meV)",
            "RP": "resolving power",
        }

        self.resTabLineEdits = {}
        for iii, (pos, label) in enumerate(labels.items()):
            color = self.colors[iii]
            qlabel = qt.QLabel(label)
            qlabel.setStyleSheet("color: %s" % color)
            resTabLayout.addWidget(qlabel, iii // 2, 2 * (iii % 2), 1, 1)
            self.resTabLineEdits[pos] = qt.QLineEdit()
            self.resTabLineEdits[pos].setStyleSheet("color: %s" % (color))
            self.resTabLineEdits[pos].setAlignment(qt.Qt.AlignRight)
            self.resTabLineEdits[pos].setMinimumWidth(80)
            self.resTabLineEdits[pos].setMaximumWidth(80)
            self.resTabLineEdits[pos].setReadOnly(True)
            resTabLayout.addWidget(
                self.resTabLineEdits[pos], iii // 2, 2 * (iii % 2) + 1, 1, 1
            )
        self.resolutionPlotWidget = PlotWidget.PlotWidget()
        resTabLayout.addWidget(qt.QWidget(), 0, 4, 3, 1)
        resTabLayout.addWidget(self.resolutionPlotWidget, iii + 2, 0, 1, 5)
        resTabLayout.setColumnStretch(4, 100)
        resTabWidget = qt.QWidget()
        resTabWidget.setLayout(resTabLayout)

        # Positions tab ------------------------------------------------------
        posTabLayout = qt.QGridLayout()
        posTabLayout.setHorizontalSpacing(15)

        labels = {
            "beta": "diffraction angle \u03B2 (\u00B0)",
            "r1": "entrance arm r\u2081 (mm)",
            "r2": "exit arm r\u2082 (mm)",
            "detx": "detx (mm)",
            "detz": "detz (mm)",
        }

        self.posTabLineEdits = {}
        for iii, (pos, label) in enumerate(labels.items()):
            color = self.colors[iii]
            qlabel = qt.QLabel(label)
            qlabel.setStyleSheet("color: %s" % color)
            posTabLayout.addWidget(qlabel, iii // 2, 2 * (iii % 2), 1, 1)
            self.posTabLineEdits[pos] = qt.QLineEdit()
            self.posTabLineEdits[pos].setStyleSheet("color: %s" % (color))
            self.posTabLineEdits[pos].setAlignment(qt.Qt.AlignRight)
            self.posTabLineEdits[pos].setMinimumWidth(80)
            self.posTabLineEdits[pos].setMaximumWidth(80)
            self.posTabLineEdits[pos].setReadOnly(True)
            posTabLayout.addWidget(
                self.posTabLineEdits[pos], iii // 2, 2 * (iii % 2) + 1, 1, 1
            )
        posTabLayout.addWidget(qt.QWidget(), 0, 4, 3, 1)

        self.posPlotTabWidget = qt.QTabWidget()
        self.posPlotWidgets = {}
        self.posPlotWidgets["overview"] = PlotWidget.PlotWidget()
        self.posPlotTabWidget.addTab(self.posPlotWidgets["overview"], "Overview")
        for label in labels:
            self.posPlotWidgets[label] = PlotWidget.PlotWidget()
            self.posPlotTabWidget.addTab(self.posPlotWidgets[label], labels[label])

        posTabLayout.addWidget(self.posPlotTabWidget, iii + 2, 0, 1, 5)
        posTabLayout.setColumnStretch(4, 100)

        posTabWidget = qt.QWidget()
        posTabWidget.setLayout(posTabLayout)

        # Efficiency tab ------------------------------------------------------
        effTabLayout = qt.QGridLayout()
        effTabLayout.setHorizontalSpacing(15)

        self.efficiencyPlotTabWidget = qt.QTabWidget()
        self.efficiencyPlotWidgets = {}
        self.efficiencyPlotWidgets["eff_vs_energy"] = PlotWidget.PlotWidget()
        self.efficiencyPlotTabWidget.addTab(
            self.efficiencyPlotWidgets["eff_vs_energy"], "Grating efficiency vs energy"
        )
        self.efficiencyPlotWidgets["acc_vs_energy"] = PlotWidget.PlotWidget()
        self.efficiencyPlotTabWidget.addTab(
            self.efficiencyPlotWidgets["acc_vs_energy"], "Vertical acceptance vs energy"
        )
        self.efficiencyPlotWidgets["eff_acc_vs_energy"] = PlotWidget.PlotWidget()
        self.efficiencyPlotTabWidget.addTab(
            self.efficiencyPlotWidgets["eff_acc_vs_energy"],
            "Efficiency \u00d7 acceptance vs energy",
        )
        self.efficiencyPlotWidgets["eff_vs_alpha"] = PlotWidget.PlotWidget()
        self.efficiencyPlotTabWidget.addTab(
            self.efficiencyPlotWidgets["eff_vs_alpha"],
            "Grating efficiency vs grating angle \u03b1",
        )
        self.efficiencyPlotWidgets["acc_vs_alpha"] = PlotWidget.PlotWidget()
        self.efficiencyPlotTabWidget.addTab(
            self.efficiencyPlotWidgets["acc_vs_alpha"],
            "Vertical acceptance vs grating angle \u03b1",
        )
        self.efficiencyPlotWidgets["eff_acc_vs_alpha"] = PlotWidget.PlotWidget()
        self.efficiencyPlotTabWidget.addTab(
            self.efficiencyPlotWidgets["eff_acc_vs_alpha"],
            "Efficiency \u00d7 acceptance vs grating angle \u03b1",
        )

        effTabLayout.addWidget(self.efficiencyPlotTabWidget)
        efficiencyTabWidget = qt.QWidget()
        efficiencyTabWidget.setLayout(effTabLayout)

        # Summary --------------------------------------------------------------

        overviewLeftLayout = qt.QVBoxLayout()
        overviewLeftLayout.setSpacing(30)
        overviewLeftLayout.addWidget(positionsWidget)
        overviewLeftLayout.addWidget(dispersionWidget)
        overviewLeftLayout.addWidget(qt.QWidget())
        overviewLeftLayout.setStretch(2, 100)
        overviewLeftWidget = qt.QWidget()
        overviewLeftWidget.setMinimumWidth(310)
        overviewLeftWidget.setLayout(overviewLeftLayout)

        overviewRightLayout = qt.QVBoxLayout()
        overviewRightLayout.setSpacing(30)
        overviewRightLayout.addWidget(resolutionWidget)
        overviewRightLayout.addWidget(infoWidget)
        overviewRightLayout.addWidget(qt.QWidget())
        overviewRightLayout.setStretch(2, 100)
        overviewRightWidget = qt.QWidget()
        overviewLeftWidget.setMinimumWidth(310)
        overviewRightWidget.setLayout(overviewRightLayout)

        overviewLayout = qt.QHBoxLayout()
        overviewLayout.addWidget(overviewLeftWidget)
        overviewLayout.addWidget(overviewRightWidget)
        overviewLayout.addWidget(qt.QWidget())
        overviewLayout.setStretch(2, 100)
        overviewWidget = qt.QWidget()
        overviewWidget.setLayout(overviewLayout)

        self.tabWidget = qt.QTabWidget()
        self.tabWidget.addTab(overviewWidget, "Summary")
        self.tabWidget.addTab(resTabWidget, "Spectrometer resolution")
        self.tabWidget.addTab(posTabWidget, "Spectrometer positions")
        self.tabWidget.addTab(efficiencyTabWidget, "Spectrometer efficiency")

        # ~ self.tabWidget.addTab(qt.QWidget(), 'Combined resolution')
        self.tabWidget.setMinimumWidth(350)

        mainLayout = qt.QGridLayout(self)
        mainLayout.addWidget(enealphaWidget, 0, 0, 1, 1)
        mainLayout.addWidget(gratingWidget, 1, 0, 1, 1)
        mainLayout.addWidget(maskWidget, 2, 0, 1, 1)
        mainLayout.addWidget(detectorWidget, 3, 0, 1, 1)
        mainLayout.addWidget(qt.QWidget(), 4, 0, 1, 1)
        mainLayout.addWidget(self.tabWidget, 0, 1, 5, 1)
        mainLayout.setRowStretch(0, 0)
        mainLayout.setRowStretch(1, 0)
        mainLayout.setRowStretch(2, 0)
        mainLayout.setRowStretch(3, 0)
        mainLayout.setRowStretch(4, 10)
        mainLayout.setVerticalSpacing(15)
        self.setLayout(mainLayout)
        self.resize(950, 600)

        self.grating_selection_changed()
        self.update_positions()
        self._calculate_used_grating_length()
        self.update_resolution()

        return 0

    def grating_selection_changed(self):
        current_grating = self.gratingComboBox.currentText()
        for param in self.gratings[current_grating]:
            value = self.gratings[current_grating][param]
            self.gratingSpinBoxes[param].setValue(value)
        self.update_positions()

    def update_positions(self):
        self.update_grating_parameters()
        energy = self.energySpinBox.value()
        alpha = math.radians(self.alphaSpinBox.value())
        beta, r1, r2, gamma = self._calculate_positions(
            energy, alpha, self.grating_pars
        )

        self.positions["beta"] = math.degrees(beta)
        self.positions["r1"] = 1.0 * r1
        self.positions["r2"] = 1.0 * r2
        self.positions["gamma"] = 1.0 * math.degrees(gamma)
        self.positions["detx"] = r2 * np.cos(np.pi - beta - alpha) + r1
        self.positions["detz"] = r2 * np.sin(np.pi - beta - alpha)
        # ~ self.positions['magnification'] = r2 * np.cos(alpha) / r1 / np.cos(beta)

        hc = 1.239842e-3  # mm*eV
        pixelsize = self.detectorSpinBoxes["pixel size"].value()
        detector_angle = math.radians(self.detectorSpinBoxes["mounting angle"].value())
        a0 = self.grating_pars["a0"]
        self.positions["dispersion"] = pixelsize * np.cos(beta) * energy**2
        self.positions["dispersion"] *= np.sin(detector_angle) / (a0 * hc * r2)
        self.positions["energy window"] = (
            self.positions["dispersion"]
            * self.detectorSpinBoxes["pixel rows"].value()
            * 1e-3
        )
        self._calculate_used_grating_length()

        for pos, val in self.positions.items():
            if pos in self.motor_limits:
                if val < self.motor_limits[pos][0] or val > self.motor_limits[pos][1]:
                    self.positionsLineEdits[pos].setStyleSheet("color: red")
                else:
                    color = self.palette().color(qt.QPalette.Text)
                    self.positionsLineEdits[pos].setStyleSheet(
                        "color: %s" % color.name()
                    )
            self.positionsLineEdits[pos].setText("%g" % (val))

        for pos in self.posTabLineEdits:
            val = self.positions[pos]
            self.posTabLineEdits[pos].setText("%g" % (val))

        grtxlow, grtxhigh = self.motor_limits["r1"]
        detxlow, detxhigh = self.motor_limits["detx"]
        detzlow, detzhigh = self.motor_limits["detz"]

        ene = np.linspace(300, 1600, 301)
        beta, r1, r2, gamma = self._calculate_positions(ene, alpha, self.grating_pars)
        detx = r2 * np.cos(np.pi - beta - alpha) + r1
        detz = r2 * np.sin(np.pi - beta - alpha)
        self.posPlotWidgets["beta"].addCurve(
            ene, beta / np.pi * 180, "beta", color="C0"
        )
        self.posPlotWidgets["beta"].addCurve(
            [energy], self.positions["beta"], "beta point", color="C0", symbol="o"
        )
        self.posPlotWidgets["r1"].addCurve(ene, r1, "r1", color="C0")
        self.posPlotWidgets["r1"].addCurve(
            ene,
            0 * r1 + self.motor_limits["r1"][0],
            "r1_lowlim",
            color="k",
            linestyle="--",
        )
        self.posPlotWidgets["r1"].addCurve(
            ene,
            0 * r1 + self.motor_limits["r1"][1],
            "r1_highlim",
            color="k",
            linestyle="--",
        )
        self.posPlotWidgets["r1"].addCurve(
            [energy], self.positions["r1"], "r1 point", color="C0", symbol="o"
        )
        self.posPlotWidgets["r2"].addCurve(ene, r2, "r2", color="C0")
        self.posPlotWidgets["r2"].addCurve(
            [energy], self.positions["r2"], "r2 point", color="C0", symbol="o"
        )
        self.posPlotWidgets["detx"].addCurve(ene, detx, "detx", color="C0")
        self.posPlotWidgets["detx"].addCurve(
            [energy], self.positions["detx"], "detx point", color="C0", symbol="o"
        )
        self.posPlotWidgets["detx"].addCurve(
            ene,
            0 * r1 + self.motor_limits["detx"][0],
            "detx_lowlim",
            color="k",
            linestyle="--",
        )
        self.posPlotWidgets["detx"].addCurve(
            ene,
            0 * r1 + self.motor_limits["detx"][1],
            "detx_highlim",
            color="k",
            linestyle="--",
        )
        self.posPlotWidgets["detz"].addCurve(ene, detz, "detz", color="C0")
        self.posPlotWidgets["detz"].addCurve(
            [energy], self.positions["detz"], "detz point", color="C0", symbol="o"
        )
        self.posPlotWidgets["detz"].addCurve(
            ene,
            0 * r1 + self.motor_limits["detz"][0],
            "detz_lowlim",
            color="k",
            linestyle="--",
        )
        self.posPlotWidgets["detz"].addCurve(
            ene,
            0 * r1 + self.motor_limits["detz"][1],
            "detz_highlim",
            color="k",
            linestyle="--",
        )
        self.posPlotWidgets["detz"].setGraphYLimits(
            detzlow - 0.05 * (detzhigh - detzlow),
            detzhigh + 0.05 * (detzhigh - detzlow),
        )
        self.posPlotWidgets["detx"].setGraphYLimits(
            detxlow - 0.05 * (detxhigh - detxlow),
            detxhigh + 0.05 * (detxhigh - detxlow),
        )
        self.posPlotWidgets["r1"].setGraphYLimits(
            grtxlow - 0.05 * (grtxhigh - grtxlow),
            grtxhigh + 0.05 * (grtxhigh - grtxlow),
        )

        units = ("\u00b0", "mm", "mm", "mm", "mm")
        for iii, pos in enumerate(["beta", "r1", "r2", "detx", "detz"]):
            self.posPlotWidgets[pos].setGraphXLabel("Photon energy (eV)")
            self.posPlotWidgets[pos].setGraphYLabel("%s (%s)" % (pos, units[iii]))

        self.posPlotWidgets["overview"].addCurve(
            [0, self.positions["r1"]], [0, 0], "r1", color="C1", linewidth=2
        )
        self.posPlotWidgets["overview"].addCurve(
            [0, self.positions["detx"]], [-10, -10], "detx1", color="C3", linestyle="--"
        )
        self.posPlotWidgets["overview"].addCurve(
            2 * [self.positions["detx"]],
            [0, self.positions["detz"]],
            "detz",
            color="C4",
            linestyle="--",
        )
        self.posPlotWidgets["overview"].addCurve(
            [self.positions["r1"], self.positions["detx"]],
            [0, self.positions["detz"]],
            "r2",
            color="C2",
            linewidth=2,
        )

        self.posPlotWidgets["overview"].addCurve(
            [0], [0], "sample", symbol="o", color="k"
        )
        self.posPlotWidgets["overview"].addCurve(
            [self.positions["r1"]], [0], "grating", symbol="o", color="k"
        )
        self.posPlotWidgets["overview"].addCurve(
            [self.positions["detx"]],
            [self.positions["detz"]],
            "detector",
            symbol="o",
            color="k",
        )

        r1limitsX = [grtxlow, grtxhigh, grtxhigh, grtxlow, grtxlow]
        r1limitsY = [-50, -50, 50, 50, -50]
        r2limitsX = [detxlow, detxhigh, detxhigh, detxlow, detxlow]
        r2limitsY = [detzlow, detzlow, detzhigh, detzhigh, detzlow]
        self.posPlotWidgets["overview"].addCurve(
            r1limitsX, r1limitsY, "r1limits", color="k", linestyle="--"
        )
        self.posPlotWidgets["overview"].addCurve(
            r2limitsX, r2limitsY, "r2limits", color="k", linestyle="--"
        )
        self.posPlotWidgets["overview"].setGraphXLabel("x (mm)")
        self.posPlotWidgets["overview"].setGraphYLabel("z (mm)")
        self.posPlotWidgets["overview"].setGraphXLimits(-500, 12500)
        self.posPlotWidgets["overview"].setGraphYLimits(-400, 2000)

    def update_resolution(self):
        self.update_grating_parameters()
        S1 = 1e-3 * self.s1SpinBox.value()
        S2 = 1e-3 * self.detectorSpinBoxes["spatial resolution"].value()
        energy = self.energySpinBox.value()
        alpha = math.radians(self.alphaSpinBox.value())
        gamma = math.radians(self.detectorSpinBoxes["mounting angle"].value())

        used_grating_length = float(
            self.positionsLineEdits["used grating length"].text()
        )

        resolution = self._calculate_resolution(
            energy,
            S1,
            S2,
            alpha,
            self.grating_pars,
            gamma,
            illuminated_length=used_grating_length,
        )

        for con in self.resolutionLineEdits:
            self.resolutionLineEdits[con].setText("%.1f" % (resolution[con]))
        self.resolutionLineEdits["RP"].setText("%d" % (resolution[con]))

        for con in self.resTabLineEdits:
            self.resTabLineEdits[con].setText("%.1f" % (resolution[con]))
        self.resTabLineEdits["RP"].setText("%d" % (resolution[con]))

        ene = np.linspace(300, 1600, 301)
        res4plot = self._calculate_resolution(
            ene,
            S1,
            S2,
            alpha,
            self.grating_pars,
            gamma,
            illuminated_length=used_grating_length,
        )
        for iii, con in enumerate(["S1", "S2", "SE", "DL", "total"]):
            self.resolutionPlotWidget.addCurve(
                ene, res4plot[con], con, color="C%d" % (iii)
            )
            self.resolutionPlotWidget.addCurve(
                [energy],
                resolution[con],
                con + " point",
                symbol="o",
                color="C%d" % (iii),
            )
        self.resolutionPlotWidget.setGraphXLabel("Photon energy (eV)")
        self.resolutionPlotWidget.setGraphYLabel("Resolution (meV)")

        self.update_efficiency()

    def update_efficiency(self):
        alphas = RtbGratingEfficiencies["alpha"]
        energy = RtbGratingEfficiencies["energy"]
        current_grating = self.gratingComboBox.currentText()
        if current_grating == "1400 lines/mm":
            eff = RtbGratingEfficiencies["1400"]
        elif current_grating == "2500 lines/mm":
            eff = RtbGratingEfficiencies["2500"]
        else:
            return

        eff_vs_alpha = eff[:, np.argmin(np.abs(energy - self.energySpinBox.value()))]
        eff_vs_energy = eff[np.argmin(np.abs(alphas - self.alphaSpinBox.value())), :]
        self.efficiencyPlotWidgets["eff_vs_alpha"].addCurve(
            alphas, eff_vs_alpha, "eff_vs_alpha", color="C0", symbol=".", linestyle="-"
        )
        self.efficiencyPlotWidgets["eff_vs_energy"].addCurve(
            energy,
            eff_vs_energy,
            "eff_vs_energy",
            color="C0",
            symbol=".",
            linestyle="-",
        )

        beta, r1, r2, gamma = self._calculate_positions(
            self.energySpinBox.value(), alphas / 180 * np.pi, self.grating_pars
        )
        masksize = self.maskSpinBox.value()
        maskdistance = self.maskdistanceSpinBox.value()
        used_grating_length = (
            masksize * r1 / (r1 - maskdistance) / np.cos(alphas / 180 * np.pi)
        )
        used_grating_length *= used_grating_length <= self.grating_pars["useful length"]
        used_grating_length += (used_grating_length == 0) * self.grating_pars[
            "useful length"
        ]
        vertical_acceptance = 1e3 * np.arctan(
            used_grating_length * np.cos(alphas / 180 * np.pi) / r1
        )
        self.efficiencyPlotWidgets["acc_vs_alpha"].addCurve(
            alphas,
            vertical_acceptance,
            "acc_vs_alpha",
            color="C0",
            symbol=".",
            linestyle="-",
        )
        self.efficiencyPlotWidgets["eff_acc_vs_alpha"].addCurve(
            alphas,
            vertical_acceptance * eff_vs_alpha,
            "eff_acc_vs_alpha",
            color="C0",
            symbol=".",
            linestyle="-",
        )

        alpha = self.alphaSpinBox.value() / 180 * np.pi
        beta, r1, r2, gamma = self._calculate_positions(
            energy, alpha, self.grating_pars
        )
        used_grating_length = (
            masksize * r1 / (r1 - maskdistance) / np.cos(alpha / 180 * np.pi)
        )
        used_grating_length *= used_grating_length <= self.grating_pars["useful length"]
        used_grating_length += (used_grating_length == 0) * self.grating_pars[
            "useful length"
        ]
        vertical_acceptance = 1e3 * np.arctan(
            used_grating_length * np.cos(alpha / 180 * np.pi) / r1
        )
        self.efficiencyPlotWidgets["acc_vs_energy"].addCurve(
            energy,
            vertical_acceptance,
            "acc_vs_energy",
            color="C0",
            symbol=".",
            linestyle="-",
        )
        self.efficiencyPlotWidgets["eff_acc_vs_energy"].addCurve(
            energy,
            vertical_acceptance * eff_vs_energy,
            "eff_acc_vs_energy",
            color="C0",
            symbol=".",
            linestyle="-",
        )

        for p in self.efficiencyPlotWidgets:
            if "energy" in p:
                self.efficiencyPlotWidgets[p].setGraphXLabel("Photon energy (eV)")
            if "alpha" in p:
                self.efficiencyPlotWidgets[p].setGraphXLabel(
                    "Grating angle \u03b1 (\u00b0)"
                )
            if "eff_acc" in p:
                self.efficiencyPlotWidgets[p].setGraphYLabel(
                    "Grating efficiency \u00d7 vertical acceptance (mrad)"
                )
            elif "acc" in p:
                self.efficiencyPlotWidgets[p].setGraphYLabel(
                    "Vertical acceptance (mrad)"
                )
            elif "eff" in p:
                self.efficiencyPlotWidgets[p].setGraphYLabel("Grating efficiency")

    def update_grating_parameters(self):
        for par in [
            "radius",
            "a0",
            "a1",
            "a2",
            "a3",
            "slope error rms",
            "useful length",
        ]:
            self.grating_pars[par] = self.gratingSpinBoxes[par].value()

    def load_motor_parameters(self):
        self.motor_limits = {
            "beta": (80, 89.9),
            "r1": (2100, 3000),
            "detx": (10025, 12300),
            "detz": (355, 1615),
            "r2": (0, 2e5),  # will be recalculated from r1, detx, detx
        }

    def load_grating_parameters(self):
        self.gratings = {}

        self.gratings["1400 lines/mm"] = {}
        self.gratings["1400 lines/mm"]["radius"] = 122100
        self.gratings["1400 lines/mm"]["a0"] = 1399.05
        self.gratings["1400 lines/mm"]["a1"] = 0.157
        self.gratings["1400 lines/mm"]["a2"] = -5.49e-5
        self.gratings["1400 lines/mm"]["a3"] = 4.4e-8
        self.gratings["1400 lines/mm"]["slope error rms"] = 90
        self.gratings["1400 lines/mm"]["useful length"] = 215

        self.gratings["2500 lines/mm"] = {}
        self.gratings["2500 lines/mm"]["radius"] = 122100
        self.gratings["2500 lines/mm"]["a0"] = 2501.6
        self.gratings["2500 lines/mm"]["a1"] = 0.2963
        self.gratings["2500 lines/mm"]["a2"] = -4.72e-5
        self.gratings["2500 lines/mm"]["a3"] = 5.2e-8
        self.gratings["2500 lines/mm"]["slope error rms"] = 90
        self.gratings["2500 lines/mm"]["useful length"] = 215

        self.gratings["old 2500 lines/mm"] = {}
        self.gratings["old 2500 lines/mm"]["radius"] = 122000
        self.gratings["old 2500 lines/mm"]["a0"] = 2500
        self.gratings["old 2500 lines/mm"]["a1"] = 0.362
        self.gratings["old 2500 lines/mm"]["a2"] = -6.39e-5
        self.gratings["old 2500 lines/mm"]["a3"] = 1e-8
        self.gratings["old 2500 lines/mm"]["slope error rms"] = 200
        self.gratings["old 2500 lines/mm"]["useful length"] = 215

        self.gratingParameterUnits = {}
        self.gratingParameterUnits["radius"] = "mm"
        self.gratingParameterUnits["a0"] = "mm\u207B\u00B9"
        self.gratingParameterUnits["a1"] = "mm\u207B\u00B2"
        self.gratingParameterUnits["a2"] = "mm\u207B\u00B3"
        self.gratingParameterUnits["a3"] = "mm\u207B\u2074"
        self.gratingParameterUnits["slope error rms"] = "nrad"
        self.gratingParameterUnits["useful length"] = "mm"

    def load_detector_parameters(self):
        self.detector = {}

        self.detector["spatial resolution"] = 10
        self.detector["pixel size"] = 13.5
        self.detector["mounting angle"] = 20
        self.detector["pixel rows"] = 2048

        self.detectorParameterUnits = {}
        self.detectorParameterUnits["spatial resolution"] = "\u03bcm"
        self.detectorParameterUnits["pixel size"] = "\u03bcm"
        self.detectorParameterUnits["mounting angle"] = "\u00B0"
        self.detectorParameterUnits["pixel rows"] = "#"

    def connect_signals(self):
        self.gratingComboBox.activated.connect(self.grating_selection_changed)

        self.alphaSpinBox.valueChanged.connect(self.update_positions)
        self.alphaSpinBox.valueChanged.connect(self._calculate_used_grating_length)

        self.energySpinBox.valueChanged.connect(self.update_positions)
        self.alphaSpinBox.valueChanged.connect(self.update_resolution)
        self.energySpinBox.valueChanged.connect(self.update_resolution)
        self.s1SpinBox.valueChanged.connect(self.update_resolution)
        self.detectorSpinBoxes["spatial resolution"].valueChanged.connect(
            self.update_resolution
        )

        current_grating = self.gratingComboBox.currentText()
        for par in self.gratings[current_grating]:
            self.gratingSpinBoxes[par].valueChanged.connect(self.update_positions)
            self.gratingSpinBoxes[par].valueChanged.connect(self.update_resolution)

        self.maskSpinBox.valueChanged.connect(self.update_positions)
        self.maskSpinBox.valueChanged.connect(self.update_resolution)
        self.maskdistanceSpinBox.valueChanged.connect(self.update_positions)
        self.maskdistanceSpinBox.valueChanged.connect(self.update_resolution)

        self.detectorSpinBoxes["mounting angle"].valueChanged.connect(
            self.update_resolution
        )
        self.detectorSpinBoxes["mounting angle"].valueChanged.connect(
            self.update_positions
        )
        self.detectorSpinBoxes["pixel size"].valueChanged.connect(self.update_positions)
        self.detectorSpinBoxes["pixel rows"].valueChanged.connect(self.update_positions)

        return 0

    def _calculate_used_grating_length(self):
        alpha = math.radians(self.alphaSpinBox.value())
        self.masksize = self.maskSpinBox.value()
        self.maskdistance = self.maskdistanceSpinBox.value()
        self.used_grating_length = min(
            [
                self.grating_pars["useful length"],
                self.masksize
                * self.positions["r1"]
                / (self.positions["r1"] - self.maskdistance)
                / np.cos(alpha),
            ]
        )
        vertical_acceptance = 1e3 * np.arctan(
            self.used_grating_length * np.cos(alpha) / self.positions["r1"]
        )
        self.positionsLineEdits["used grating length"].setText(
            "%g" % self.used_grating_length
        )
        self.positionsLineEdits["acceptanceV"].setText("%g" % vertical_acceptance)

    def _calculate_positions(self, E, alpha, grating_pars, k=1):
        """
        Calculate beta, r1, r2, gamma for a given alpha, energy and k. Angles
        are in radians, lengths in mm.
        """
        hc = 1.239842e-3  # mm*eV

        R = grating_pars["radius"]
        a0 = grating_pars["a0"]
        a1 = grating_pars["a1"]
        a2 = grating_pars["a2"]

        x = E / (k * hc)

        beta = np.arcsin(np.sin(alpha) - k * a0 * hc / E)

        W = np.sqrt(3) * np.sqrt(
            R**2
            * x**2
            * np.cos(alpha) ** 2
            * np.cos(beta) ** 2
            * (
                x
                * np.cos(beta) ** 2
                * np.sin(alpha)
                * (-8 * a2 * R**2 + 3 * x * np.sin(alpha))
                + np.sin(beta)
                * (
                    12 * a1 * R * (a1 * R + x * np.cos(beta)) * np.sin(alpha)
                    + 3 * x * (2 * a1 * R + x * np.cos(beta)) * np.sin(2 * alpha)
                    + x * np.cos(alpha) ** 2 * (8 * a2 * R**2 + 3 * x * np.sin(beta))
                )
            )
        )

        r1 = (
            3
            * R
            * x
            * np.cos(alpha)
            * (
                x * np.cos(beta) * np.sin(alpha - beta)
                - 2 * np.cos(alpha) * (a1 * R + x * np.cos(alpha)) * np.sin(beta)
            )
            - W
        )
        r1 /= 4 * a2 * R**2 * x * np.cos(beta) ** 2 - 6 * (
            a1 * R + x * np.cos(alpha)
        ) * (a1 * R + x * (np.cos(alpha) + np.cos(beta))) * np.sin(beta)

        r2 = (
            3
            * R
            * x
            * np.cos(beta)
            * (
                np.cos(beta)
                * (2 * a1 * R + x * np.cos(alpha) + 2 * x * np.cos(beta))
                * np.sin(alpha)
                - x * np.cos(alpha) ** 2 * np.sin(beta)
            )
            + W
        )
        r2 /= 4 * a2 * R**2 * x * np.cos(alpha) ** 2 + 6 * (
            a1 * R + x * np.cos(beta)
        ) * (a1 * R + x * (np.cos(alpha) + np.cos(beta))) * np.sin(alpha)

        gamma = np.arctan(
            np.cos(beta) / (2 * np.sin(beta) - r2 * (np.tan(beta) / R + a1 / a0))
        )

        return beta, r1, r2, gamma

    def _calculate_resolution(
        self, E, S1, S2, alpha, grating_pars, gamma, illuminated_length=0, k=1
    ):
        """
        Angles are in radians, lengths in mm.
        """
        hc = 1.239842e-3  # mm*eV

        R = grating_pars["radius"]
        a0 = grating_pars["a0"]
        SE = 2.3548 * grating_pars["slope error rms"]
        if not illuminated_length:
            illuminated_length = grating_pars["useful length"]

        beta, r1, r2, gamma_opt = self._calculate_positions(E, alpha, grating_pars)

        dE_S1 = 1e3 * S1 * np.cos(alpha) * E**2 / (a0 * hc * k * r1)
        dE_S2 = 1e3 * S2 * np.cos(beta) * E**2 / (a0 * hc * k * r2) * np.sin(gamma)
        dE_SE = 1e3 * 2 * SE * 1e-9 * E / np.tan((alpha - beta))
        dE_DL = 1e3 * E / (k * illuminated_length * a0)
        dE = np.sqrt(dE_S1**2 + dE_S2**2 + dE_SE**2 + dE_DL**2)

        resolution = {
            "S1": dE_S1,
            "S2": dE_S2,
            "SE": dE_SE,
            "DL": dE_DL,
            "total": dE,
            "RP": 1e3 * E / dE,
        }

        return resolution


# Regular expression to find floats. Match groups are the whole string, the
# whole coefficient, the decimal part of the coefficient, and the exponent
# part.
_float_re = re.compile(r"(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)")


class FloatValidator(qt.QValidator):
    def validate(self, string, position):
        if self.valid_float_string(string):
            state = qt.QValidator.Acceptable
        elif string == "" or string[position - 1] in "e.-+":
            state = qt.QValidator.Intermediate
        else:
            state = qt.QValidator.Invalid
        return (state, string, position)

    def fixup(self, text):
        match = _float_re.search(text)
        return match.groups()[0] if match else ""

    def valid_float_string(self, string):
        match = _float_re.search(string)
        return match.groups()[0] == string if match else False


class ScientificDoubleSpinBox(qt.QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum(-np.inf)
        self.setMaximum(np.inf)
        self.validator = FloatValidator()
        self.setDecimals(10)
        self.valueChanged.connect(self.autosetStepSize)

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        return float(text)

    def textFromValue(self, value):
        return "%g" % (value)

    def autosetStepSize(self):
        self.setSingleStep(10 ** (int(math.log10(abs(self.value()))) - 2))


if __name__ == "__main__":
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)

    w = MainWindow()
    w.show()
    app.exec_()
