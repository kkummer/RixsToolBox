#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = "K. Kummer - ESRF ID32"
__contact__ = "kurt.kummer@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"

import os

import numpy as np
from PyMca5.PyMcaGraph import Colors as pymcaColors
from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.plotting import PlotWindow
from PyMca5.PyMcaGui.pymca import ScanWindow
from PyMca5.PyMcaGui.pymca.ScanWindowInfoWidget import SpecArithmetic
from PyMca5.PyMcaGui.pymca import QDispatcher
from silx.gui.plot import Plot2D


from . import SpecGen as SpecGenGUI
from .Icons import RtbIcons
from .Math import RtbMath
from .rixs_spectrum import RixsSpectrum

def Gaussian(x, x0, amp, fwhm):
    return amp * np.exp(-(x-x0)**2/2/(fwhm/2.3548)**2)



class MainWindow(qt.QWidget):
    def __init__(self, parent=None):
        DEBUG = 1
        qt.QWidget.__init__(self, parent)
        
        self._initialize_parameters()
        self.build()
        self.connect_signals()
        
        self.RTB_Math = RtbMath()
        
        self.data = {}
        self.energies = {}
    
    
    def build(self):
        self.setWindowTitle("RixsToolBox - Find isoenergy line parameters")
        self.setWindowIcon(qt.QIcon(qt.QPixmap(RtbIcons["Logo"])))
        
        self.sourceWidget = QDispatcher.QDispatcher(self)
        self.sourceWidget.sourceSelector.fileTypeList = [
            "HDF5 Files (*.nxs *.hdf *.h5 *.hdf5)"
        ]
        tabWidget = self.sourceWidget.tabWidget
        for i in reversed(range(tabWidget.count())):
            if tabWidget.tabText(i) != "HDF5":
                tabWidget.removeTab(i)
        
        # Hide "auto" checkboxes to avoid accidental start of heavy processing
        for cb in self.sourceWidget.selectorWidget["HDF5"].findChildren(qt.QCheckBox):
            if cb.text().lower() in ["auto off", "auto add", "auto replace", "3d on", "2d on", "force mca"]:
                if cb.text().lower() == "auto off":
                    cb.setChecked(True)
                else:
                    cb.setChecked(False)
                cb.hide()
        
        for table in self.sourceWidget.selectorWidget["HDF5"].findChildren(qt.QTableView):
            model = table.model()
            for col in range(model.columnCount()):
                header = model.headerData(col, qt.Qt.Horizontal)
                if header not in ["Dataset", "Signals"]:
                    table.hideColumn(col)
                
        
        self._expertDialog = SpecGenGUI.ExpertSettingsDialog(
            self,
            lower_threshold=self.lower_threshold,
            upper_threshold=self.upper_threshold,
            masksize=self.masksize,
            SPC_gridsize=self.SPC_gridsize,
            SPC_low_threshold=self.SPC_low_threshold,
            SPC_high_threshold=self.SPC_high_threshold,
            SPC_single_threshold=self.SPC_single_threshold,
            SPC_double_threshold=self.SPC_double_threshold,
        )

        self.spcPlot = PlotWindow.PlotWindow(
            parent=self,
            backend=None,
            plugins=False,
            newplot=False,
            roi=False,
            control=False,
            position=True,
            info=False,
            logx=False,
            logy=False,
            togglePoints=False,
        )
        self.spcPlot.setMinimumWidth(300)
        
        self.spcGaussPlot = ScanWindow.ScanWindow(
            parent=self,
            backend=None,
            plugins=False,
            newplot=False,
            roi=False,
            control=True,
            position=True,
            info=False,
            fit=True,
            logx=False,
            logy=False,
            togglePoints=False,
        )
        self.spcGaussPlot.setMinimumWidth(300)
        self.spcGaussPlot.showLegends(True)
        self.spcGaussPlot.legendDockWidget.setMinimumWidth(220)
        
        
        self.refinePlot = Plot2D()
        self.refinePlot.getColorBarWidget().hide()
        self.refinePlot.setMinimumWidth(300)
        
        

        self.parametersWidget = SpecGenGUI.ParametersWidget(self)
        self.parametersWidget._spcCheckBox.setDisabled(True)
        self.parametersWidget._slopeDoubleSpinBox.setValue(0)
        self.parametersWidget._slopeDoubleSpinBox.setDisabled(True)
        self.parametersWidget._smileDoubleSpinBox.setDisabled(True)
        self.backgroundWidget = SpecGenGUI.BackgroundWidget(self)
        self.backgroundWidget.extractBackgroundCheckBox.setDisabled(True)
        self.tabWidget = qt.QTabWidget()
        self.tabWidget.addTab(self.parametersWidget, "Parameters")
        self.tabWidget.addTab(self.backgroundWidget, "Background subtraction")


        rsLayout = qt.QGridLayout(self)
        rsLayout.addWidget(
            qt.QLabel("Fit photon positions in image"), 
            0, 0, 1, 1,
        )
        rsLayout.addWidget(self.spcPlot, 1, 0, 1, 1)
        rsLayout.addWidget(self.spcGaussPlot, 2, 0, 1, 2)
        rsLayout.addWidget(
            qt.QLabel("Refine by minimizing FWHM"), 
            0, 1, 1, 1,
        )
        rsLayout.addWidget(self.refinePlot, 1, 1, 1, 1)
        rsLayout.setVerticalSpacing(10)
        rsLayout.setHorizontalSpacing(25)
        rsLayout.setColumnStretch(0, 1)
        rsLayout.setColumnStretch(1, 1)
        rsWidget = qt.QWidget()
        rsWidget.setLayout(rsLayout)

        lsLayout = qt.QVBoxLayout(self)
        lsLayout.addWidget(self.sourceWidget)
        lsWidget = qt.QWidget()
        lsWidget.setContentsMargins(0, 0, 0, -8)
        lsWidget.setLayout(lsLayout)

        self.splitter = qt.QSplitter(self)
        self.splitter.setOrientation(qt.Qt.Horizontal)
        self.splitter.setHandleWidth(10)
        self.splitter.addWidget(lsWidget)
        self.splitter.addWidget(rsWidget)
        self.splitter.setStretchFactor(1, 4)

        mainLayout = qt.QHBoxLayout()
        mainLayout.addWidget(self.splitter)
        self.setLayout(mainLayout)

        self.RTB_Math = RtbMath()

        # Initial parameters
        self.parametersWidget._slopeDoubleSpinBox.setValue(self.slope)
        self.parametersWidget._pointsperpixelDoubleSpinBox.setValue(
            self.points_per_pixel
        )
        self.parametersWidget._spcCheckBox.setChecked(self.SPC)
            
    
    def _initialize_parameters(self):
        self.slope = 0
        self.smile = 0
        self.points_per_pixel = 2.7
        self.binning = 1
        self.lower_threshold = -1e5
        self.upper_threshold = 1e5
        self.masksize = 5
        self.SPC = True
        self.SPC_gridsize = 3
        self.SPC_low_threshold = 0.2
        self.SPC_high_threshold = 1.0
        self.SPC_single_threshold = 0.4
        self.SPC_double_threshold = 1.5
        self.ROI = None
        self.ccd_parameters = [0.00016, 1.2, 3.6]
        return 0

    def connect_signals(self):
        self.sourceWidget.sigAddSelection.connect(self.add_data)
        self.sourceWidget.sigRemoveSelection.connect(self.remove_data)
        self.sourceWidget.sigReplaceSelection.connect(self.replace_data)
        
    
    def showProgress(self, text, maximum):
        if not hasattr(self, "_progress"):
            self._progress = qt.QProgressDialog(self)
        self._progress.setWindowFlags(
            self._progress.windowFlags()
            & ~qt.Qt.WindowContextHelpButtonHint
        )
        self._progress.reset()
        self._progress.setWindowTitle("Progress")
        self._progress.setLabelText(text)
        self._progress.setMaximum(maximum)
        self._progress.setValue(0)
        self._progress.show()
    
    
    
    def add_data(self, selection_list):
        if not isinstance(selection_list, list):
            selection_list = [selection_list]
        
        my_selection = []
        for selection in selection_list:
            if selection["selection"]["selectiontype"] == "2D":
                my_selection.append(selection)
        selection_list = my_selection
        
        if selection_list == []:
            return
        
        total_number_of_images = 0
        for selection in selection_list:
            images = selection["dataobject"]
            total_number_of_images += images.data.shape[0]
        if total_number_of_images == 0:
            return
        
        self.showProgress("Analysing images ...", total_number_of_images)
        current_image_number = 0
                    
        for selection in selection_list:
            legend = selection["legend"]
            images = selection["dataobject"]
            detector = selection["selection"]["LabelNames"][selection["selection"]["y"][0]]
            motors = dict(zip(images.info["MotorNames"], images.info["MotorValues"]))
            spc_events = []
            for ii, image in enumerate(images.data):
                if self._progress.wasCanceled():
                    self._progress.reset()
                    self._progress.hide()
                    return
                rs = RixsSpectrum(
                    data = {detector: image, "sec": np.ones(image.shape[0])},
                    scan_number = -1,
                    point_number = ii,
                    scan_info = {"title": ""},
                    detector_name = detector,
                    detector_info = {"image_roi": (2048-image.shape[1], 0, *image.T.shape)},
                    motors = motors,
                    norm_counters = [],
                    counter_blacklist = [detector],
                    parameters = {},
                    ccd_parameters = {},
                    keep_image = False,
                )
                spc_events.append(rs.centers)
                
                current_image_number += 1
                self._progress.setValue(current_image_number)
                qt.QApplication.processEvents()
                
            spc_events = np.vstack(spc_events)
            self.data[legend] = spc_events
            self.energies[legend] = motors["energy"]
            
            self.spcPlot.addCurve(
                spc_events[:, 1],
                spc_events[:,0],
                legend,
                symbol=".",
                linestyle=" ",
                replot=True,
                alpha=.25,
            )
            
        
        self._progress.hide()
        
        self.determine_slope_and_smile_from_spc()
        self.refine_slope_and_smile()
    
    
    def remove_data(self, selection_list):
        if not isinstance(selection_list, list):
            selection_list = [selection_list]
        
        for selection in selection_list:
            legend = selection["legend"]
            if legend in self.data:
                self.data.pop(legend, None)
                self.spcPlot.removeCurve(legend)
        
        self.determine_slope_and_smile_from_spc()
    
    
    def replace_data(self, selection_list):
        if not isinstance(selection_list, list):
            selection_list = [selection_list]
        
        legends_keep = [selection["legend"] for selection in selection_list]
        self.data = {k: v for k, v in self.data.items() if k in legends_keep}
        selection_missing = [
            selection for selection in selection_list 
            if selection["legend"] not in self.data
        ]
        curves_to_remove = []
        for curve in self.spcPlot.getAllCurves():
            x, y, legend, info = curve
            if legend not in self.data:
                curves_to_remove.append(legend)
        for legend in curves_to_remove:
            self.spcPlot.removeCurve(legend)
        
        if self.data:
            self.determine_slope_and_smile_from_spc()
            self.refine_slope_and_smile()
        self.add_data(selection_missing)
        
        
    def clear_data(self):
        self.data = {}
        self.spcPlot.clearCurves()
        
    
    
    def determine_slope_and_smile_from_spc(self):
        self.spcPlot.removeCurve("fit")
        if not self.data:
            return
        x = []
        y = []
        for legend, centers in self.data.items():
            x.append(centers[:,1])
            y.append(centers[:,0])
        x = np.hstack(x)
        y = np.hstack(y)
        
        popt, inliers, score = fit_isoenergy_ransac(
            x,
            y,
            x_center=1024,
            n_iter=10000,
            window=6,
            random_state=0,
        )
        
        self.popt_ransac = popt
        self.spcPlot.setGraphTitle(f"slope = {popt[1]:.3e}, smile={popt[0]:.2e}")
        
        xfit = np.linspace(x.min(), x.max(), 101)
        self.spcPlot.addCurve(
            xfit, 
            np.polyval(popt, xfit-1024), 
            "fit", 
            linestyle="-", 
            symbol=" ", 
            replot=True
        )
        
        # ~ self.refine_slope_and_smile()
        elastic = self.calculate_rixs_from_centers(coeffs_polynomial=popt)
        self.spcGaussPlot.addCurve(
            elastic[:,0], 
            elastic[:,1],
            legend="Elastic line",
            symbol='.',
            linestyle="--",
            replace=True,
            replot=True,
            xlabel="Pixel",
            ylabel="SPC",
        )
        
        
        
    def refine_slope_and_smile(self, slope_dev=2e-3, smile_dev=5e-6, 
        slope_points=31, smile_points=31):
        
        popt = self.popt_ransac
        
        slopes = np.linspace(
            popt[1] - slope_dev,
            popt[1] + slope_dev,
            slope_points,
        )
        
        smiles = np.linspace(
            popt[0]  - smile_dev,
            popt[0]  + smile_dev,
            smile_points,
        )
        
        
        results = np.empty((len(slopes), len(smiles)), dtype=float)
        self.showProgress(
            "Refining slope and smile ...", 
            len(slopes)*len(smiles),
        )
        current_point_number = 0
        for i, slope in enumerate(slopes):
            for j, smile in enumerate(smiles):
                if self._progress.wasCanceled():
                    self._progress.reset()
                    self._progress.hide()
                    return
                coeffs = [smile, slope, popt[-1]]
                spectrum = self.calculate_rixs_from_centers(
                    coeffs_polynomial=coeffs, 
                    points_per_pixel=2.7,
                )
                
                if 1: # fit Gaussian (slow)
                    popt_gauss, _ = self.RTB_Math.curve_fit(
                        Gaussian, 
                        spectrum[:,0],
                        spectrum[:,1],
                        p0=(spectrum[:,0].mean(), spectrum[:,1].max(), 2),
                    )
                    fwhm = popt_gauss[-1]
                else: # estimate fwhm from second moment (fast)
                    x2 = spectrum[:,0]
                    y2 = spectrum[:,1]
                    area = y2.sum()
            
                    if area <= 0:
                        results[i, j] = np.nan
                        continue
            
                    mu = np.sum(x2 * y2) / area
            
                    sigma = np.sqrt(
                        np.sum(y2 * (x2 - mu) ** 2) / area
                    )
                    fwhm = 2.3548 * sigma
                results[i, j] = fwhm
                
                current_point_number += 1
                self._progress.setValue(current_point_number)
                qt.QApplication.processEvents()
                
        self._progress.hide()
        self.refinePlot.addImage(
            results,
            legend="FWHM",
            origin=(smiles[0], slopes[0]),
            scale=(
                smiles[1] - smiles[0],
                slopes[1] - slopes[0],
            ),
            colormap={
                "name": "viridis_r",
                "normalization": "linear",
                "autoscale": True,
            },
        )
        self.refinePlot.setGraphXLabel("Smile")
        self.refinePlot.setGraphYLabel("Slope")
        
        
        smile_opt, slope_opt, coeff = self.RTB_Math.quadratic_minimum_2d(
            results,
            smiles,
            slopes,
            window=4,
        )
        self.refinePlot.setGraphTitle(
            f"slope = {slope_opt:.3e}, smile={smile_opt:.2e}"
        )
        
        self.refinePlot.addMarker(
            x=self.popt_ransac[0],
            y=self.popt_ransac[1],
            legend="line fit",
            symbol=".",
            text="line fit",
            color='#777777',
        )
        
        self.refinePlot.addMarker(
            x=smile_opt,
            y=slope_opt,
            legend="refined",
            symbol=".",
            text="refined",
        )
        
        
        
        elastic = self.calculate_rixs_from_centers(
            coeffs_polynomial=(smile_opt, slope_opt, popt[-1])
        )
        self.spcGaussPlot.addCurve(
            elastic[:,0], 
            elastic[:,1],
            legend="Refined elastic line",
            symbol='.',
            linestyle="--",
            replace=False,
            replot=True,
            xlabel="Pixel",
            ylabel="SPC",
        )
        
        
    def calculate_rixs_from_centers(
        self, 
        *, 
        coeffs_polynomial, 
        points_per_pixel=3.7,
        pixel_window=25,
    ):
        
        centers = np.vstack([d for d in self.data.values()])
        energy = np.array([e for e in self.energies.values()]).mean()
        
        x = centers[:,1] - 1024
        y = centers[:,0]
        intensities = centers[:,2]
        
        LOW_TH_PX  = self.SPC_low_threshold * energy
        HIGH_TH_PX = self.SPC_high_threshold * energy
        SpotLOW    = self.SPC_single_threshold * energy
        SpotHIGH   = self.SPC_double_threshold * energy
        
        y -= np.polyval(coeffs_polynomial, x)
        
        
        single = (intensities > SpotLOW) & (intensities <= SpotHIGH)
        double = intensities > SpotHIGH
    
        step = 1 / points_per_pixel
        pixel = np.arange(-pixel_window/2, pixel_window/2, step)
        pixel_bins = np.concatenate([
            pixel-step/2, [pixel[-1] + step/2],
        ])
    
        spectrum_single = np.histogram(y[single], pixel_bins)[0]
        spectrum_double = np.histogram(y[double], pixel_bins)[0]
        
        pixel += coeffs_polynomial[-1]
        
        return np.vstack([pixel, spectrum_single + 2* spectrum_double]).T
        

    def total_huber_loss(self, theta, x, y, c=2):
        
        return self.huber_loss((y - theta[2] - theta[1] * (x-1024) - theta[0] * (x-1024)**2), c).sum()

    def huber_loss(self, t, c=2):
        return (abs(t) < c) * 0.5 * t**2 + (abs(t) >= c) * -c * (0.5 * c - abs(t))




def fit_isoenergy_ransac(
    x,
    y,
    x_center=1024.0,
    n_iter=5000,
    window=5.0,
    min_dx=200.0,
    random_state=None,
):
    rng = np.random.default_rng(random_state)

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xs = x - x_center

    n = len(x)
    best_score = -1
    best_theta = None
    best_mask = None

    for _ in range(n_iter):
        idx = rng.choice(n, size=3, replace=False)

        # avoid nearly vertical / ill-conditioned triplets
        if np.ptp(xs[idx]) < min_dx:
            continue

        theta = np.polyfit(xs[idx], y[idx], deg=2)

        y_model = np.polyval(theta, xs)
        residual = y - y_model
        mask = np.abs(residual) < window

        score = mask.sum()

        if score > best_score:
            best_score = score
            best_theta = theta
            best_mask = mask

    if best_theta is None:
        raise RuntimeError("RANSAC failed")

    # Refit using inliers
    theta_refined = np.polyfit(xs[best_mask], y[best_mask], deg=2)

    # Optional second inlier pass after refinement
    y_model = np.polyval(theta_refined, xs)
    best_mask = np.abs(y - y_model) < window
    theta_refined = np.polyfit(xs[best_mask], y[best_mask], deg=2)

    return theta_refined, best_mask, best_score

if __name__ == "__main__":
    import numpy as np

    app = qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)

    w = MainWindow()
    w.show()
    app.exec_()
