#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import numpy as np
from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.pymca import ScanWindow
from PyMca5.PyMcaMath import SpecArithmetic
from PyMca5.PyMcaMath.fitting.Specfit import Specfit

from . import SpecSum as SpecSumGUI
from .Icons import RtbIcons


class MainWindow(SpecSumGUI.MainWindow):
    def __init__(self, parent=None):
        SpecSumGUI.MainWindow.__init__(self)
        self.setWindowTitle("RixsToolBox - Find energy calibration")
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons["Logo"])))
        self.alignButton.setText("Find energy\ncalibration")
        self.alignButton.setEnabled(True)
        self.methodWidget.hide()
        self.calcButton.hide()
        self.sumButton.hide()
        self.saveButton.hide()
        self.trendWidget.hide()
        self._exportWidget.hide()
        self.groupWidget.hide()
        self._plotShiftsWindow.setMaximumHeight(10000)
        self._plotShiftsWindow.toolBar.show()
        self.methodComboBox.setCurrentIndex(1)

        self.linearCheckBox = qt.QCheckBox(self, text="Force linear energy calibration")
        self.alignmentLayout.addWidget(self.linearCheckBox, 3, 0, 1, 1)
        self.alignmentLayout.setSpacing(12)
        
        
        self.alignmentWidget.setLayout(self.alignmentLayout)
        self.alignmentWidget.setTitle("Settings for energy calibration")
        
        self.alignButton.clicked.disconnect(self.alignButtonClicked)
        self.alignButton.clicked.connect(self.getCalibration)
        self.linearCheckBox.stateChanged.connect(self.getCalibration)
        
        self._sourceWidget.sigAddSelection.connect(self.getCalibration)
        self._sourceWidget.sigRemoveSelection.connect(self.getCalibration)
        self._sourceWidget.sigReplaceSelection.connect(self.getCalibration)
        

    def plottedSpectraChanged(self):
        return

    def getCalibration(self):
        curves = self._plotSpectraWindow.getAllCurves()
        
        if len(curves) < 2:
            return
        
        xmin = self._minSpinBox.value()
        xmax = self._maxSpinBox.value()
        
        calib = []
        for curve in curves:
            x, y, legend, info = curve
            center, peak, idx = SpecArithmetic.search_peak(x, y)
            if center < xmin or center > xmax:
                continue
            motor_idx = info["MotorNames"].index("energy")
            energy = info["MotorValues"][motor_idx]
            xlabel = info["xlabel"]
            calib.append([center, energy])
        
        if not calib:
            return
        
        calib = np.asarray(calib)
        n_points = calib.shape[0]
        
        if n_points < 2:
            return
        
        calib = calib[np.argsort(calib[:,0])]
        
        if self.linearCheckBox.isChecked() or n_points < 3:
            coeffs = (0, *np.polyfit(calib[:,0], calib[:,1], 1))
        else:
            coeffs = np.polyfit(calib[:,0], calib[:,1], 2)
        
        detector_size = 2048
        Emin = coeffs[-1]
        Emax = np.polyval(coeffs, detector_size - 1)
        curvature = 2 * coeffs[0]
        
        
        # Plot fit result
        title = "$E_0$ = "f"{Emin:.2f}, ""$E_{2047}$ = "f"{Emax:.2f}, "
        if curvature == 0:
            title += f"curvature = 0   \u2192   {1e3*coeffs[1]:.3f} meV/px"
        else:
            title += f"curvature = {curvature:.4e}"
        
        self._plotShiftsWindow.setGraphTitle(title)
        
        e0 = calib[:,0].min()
        e1 = calib[:,0].max()
        xfit = np.linspace(
            e0 - 0.1 * (e1 - e0),
            e1 + 0.1 * (e1 - e0),
            101,
        )
        yfit = np.polyval(coeffs, xfit)
        
        self._plotShiftsWindow.addCurve(
            calib[:,0],
            calib[:,1],
            "Peak positions",
            xlabel=f"{xlabel}",
            ylabel="Energy (eV)",
            symbol="o",
            linestyle="",
        )
        
        self._plotShiftsWindow.addCurve(
            xfit,
            yfit,
            "Fit",
            xlabel=f"{xlabel}",
            ylabel="Energy (eV)",
            symbol="",
            linestyle="-",
        )
        
        self._plotShiftsWindow.addCurve(
            calib[:,0],
            np.polyval(coeffs, calib[:,0]) - calib[:,1],
            "Residuals",
            xlabel=f"{xlabel}",
            ylabel="Residuals (eV)",
            symbol="+",
            linestyle=":",
            yaxis="right",
        )
        
        self._plotShiftsWindow.setActiveCurve("Residuals")
        


if __name__ == "__main__":
    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)

    w = MainWindow()
    w.show()
    app.exec_()
