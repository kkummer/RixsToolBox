import os
import pathlib
import time

import numpy as np
from scipy import ndimage

try:    
    from .specfile_handler import SpecFileHandler
except ImportError:
    pass



class RixsSpectrum:
    def __init__(
        self,
        *,
        data,
        scan_number,
        point_number,
        scan_info,
        detector_name,
        detector_info,
        motors,
        norm_counters=["sec", "current", "mir", "it", "mir_xmcd", "it_xmcd", "mir_rixs", "sam_rixs"],
        counter_blacklist=["andor1", "andor2", "dhyana95v2"],
        parameters={},
        ccd_parameters={},
        keep_image=False,
    ):
        
        self.parameters = {
            "slope": -0.0089,
            "smile": 0,
            "points per pixel": 2.7,
            "low threshold": 0.05,
            "high threshold": 0.9,
            "mask size": 1,
            "SPC": True,
            "SPC grid size": 3,
            "SPC low threshold": 0.2,
            "SPC high threshold": 1,
            "SPC single event threshold": 0.2,
            "SPC double event threshold": 1.5,
        }
        self.parameters.update(parameters)
        
        self.detector_parameters = {
            "dark_current": 0.00016,  # counts per pixel per s
            "electrons_per_adc_count": 1.5768,  # 1.2
            "energy_eh": 3.6,  # Electron-hole pair generation energy (eV)
            "chipsize": (2048, 2048), 
        }
        self.detector_parameters.update(ccd_parameters)
        
        self.detector_info = {
            "image_bin": (1, 1),
        }
        self.detector_info.update(detector_info)
        
        
        
        
        try:
            self.energy_calibration = self.parameters["energy_calibration"]
        except KeyError:
            self.energy_calibration = None
        
        
        
        t0 = time.perf_counter()
        
        self.scan_number = int(scan_number)
        self.point_number = point_number
        self.detector_name = detector_name
        self.norm_counters = norm_counters
        self.scan_title = scan_info["title"]
        self.motors = motors
        self.counters = {k: v for k, v in data.items() if k not in counter_blacklist}
        
        
        
        self.binning = self.detector_info["image_bin"][1]
        self.image = data[detector_name]
        self.exposure = data["sec"]
        self.roi = detector_info["image_roi"]
        
        self.slope = self.parameters["slope"]
        self.smile = self.parameters["smile"]
        self.points_per_pixel = self.parameters["points per pixel"]
        self.upper_threshold = self.parameters["high threshold"]
        self.lower_threshold = self.parameters["low threshold"]
        self.masksize = int(self.parameters["mask size"])

        self.SPC = self.parameters["SPC"]
        self.SPC_gridsize = int(self.parameters["SPC grid size"])
        self.SPC_low_TH = self.parameters["SPC low threshold"]
        self.SPC_high_TH = self.parameters["SPC high threshold"]
        self.SPC_single_TH = self.parameters["SPC single event threshold"]
        self.SPC_double_TH = self.parameters["SPC double event threshold"]
        
        
        if "epoch" in self.counters:
            self.image_date = time.localtime(self.counters["epoch"])
        else:
            self.image_date = time.localtime(0)
        self.image_date = time.strftime("%Y-%m-%d %H:%M:%S", self.image_date)
        
        self.cont_photon = (
            self.motors["energy"]
            / self.detector_parameters["energy_eh"]
            / self.detector_parameters["electrons_per_adc_count"]
        )
        
        
        self.valid_pixel_mask = None
        self.shifts = None
        
        self.spectrum = {}
        t1 = time.perf_counter()
        self.filter_image()
        t2 = time.perf_counter()
        self.build_pixel_and_energy_axis()
        t3 = time.perf_counter()
        self.build_integrated_spectrum()
        t4 = time.perf_counter()
        self.build_single_photon_counting_spectrum()
        t5 = time.perf_counter()

        
        if not keep_image:
            del(self.image)
    
        timing_string = "\t".join(
            [
                "Filter image: %.2fms" % (1e3 * (t2 - t1)),
                "Pixel axis: %.2fms" % (1e3 * (t3 - t2)),
                "Photons: %.2fms" % (1e3 * (t4 - t3)),
                "SPC: %.2fms" % (1e3 * (t5 - t4)),
                "Total: %.2fms" % (1e3 * (time.perf_counter() - t0)),
            ]
        )
        print(timing_string)
        
    
    def filter_image(self):
        image = self.image
        dark_offset = image[:50, :].mean()
        image = image - dark_offset
        
        
        low_cutoff = self.lower_threshold * self.cont_photon * self.binning
        high_cutoff = self.upper_threshold * self.cont_photon * self.binning
    
        image[image < low_cutoff] = 0
    
        if self.masksize != 1:
            mask = image > high_cutoff
            mask = ndimage.correlate(
                mask.astype(np.uint8),
                np.ones((self.masksize, self.masksize), dtype=np.uint8),
            )
            image[mask != 0] = 0
        else:
            image[image > high_cutoff] = 0
    
        self.image = image
    
    
    def build_shifts_and_valid_pixel_mask(self):
        nrows, ncols = self.image.shape
        slope = self.slope
        smile = self.smile
        points_per_pixel = self.points_per_pixel
        
        nyp = int(nrows * points_per_pixel)
        yprime = np.linspace(0.0, nrows - 1.0, nyp)
        x = np.linspace(0, ncols-1, ncols)
        x0 = ncols // 2
        shifts = slope * (x - x0) + smile * (x - x0)**2
        
        valid_pixel_mask = (
            (yprime + shifts.min() >= 0.0) &
            (yprime + shifts.max() < nrows - 1)
        )
        
        self.valid_pixel_mask = valid_pixel_mask
        self.shifts = shifts
    
    
    def _add_spectrum_column(self, label, value):
        if self.valid_pixel_mask is None:
            self.build_shifts_and_valid_pixel_mask()
        self.spectrum[label] = value[self.valid_pixel_mask]
        
    
    def build_pixel_and_energy_axis(self):
        nrows, _ = self.image.shape
        self._add_spectrum_column(
            "Pixel",
            np.linspace(0, nrows, int(nrows * self.points_per_pixel)) + self.roi[1]
        )
        if self.energy_calibration:
            Emin, Emax, curvature = self.energy_calibration
            xmax = 2048
            poly_coeffs = (
                curvature / 2,
                (Emax - Emin - curvature / 2) / xmax,
                Emin,
            )
            self.spectrum["Energy out (auto)"] = np.polyval(
                poly_coeffs,
                self.spectrum["Pixel"])
    
    
    
    def build_integrated_spectrum(self):
        Z = self.image
        nrows, _ = Z.shape
    
        points_per_pixel = self.points_per_pixel
        nyp = int(nrows * points_per_pixel)
        yprime = np.linspace(0.0, nrows - 1.0, nyp)
        
        if self.shifts is None:
            self.build_shifts_and_valid_pixel_mask()
        shifts = self.shifts
    
        ZT = np.ascontiguousarray(Z.T)
        out = np.zeros(nyp, dtype=np.float64)
    
        for i, shift in enumerate(shifts):
            jf = yprime + shift
            
            j0 = jf.astype(np.int64)
            t = jf - j0
    
            j0 = np.clip(j0, 0, nrows - 2)
    
            col = ZT[i]
    
            out += (1.0 - t) * col[j0] + t * col[j0 + 1]
    
        out *= 1.0 / points_per_pixel
        
        self._add_spectrum_column("Electrons", out)
        self._add_spectrum_column("Photons", out / self.cont_photon)
        
            
    
    def build_single_photon_counting_spectrum(self):
        gs = self.SPC_gridsize
        r = gs // 2
    
        image = self.image
        energy = self.motors["energy"]
    
        LOW_TH_PX  = self.SPC_low_TH * energy
        HIGH_TH_PX = self.SPC_high_TH * energy
        SpotLOW    = self.SPC_single_TH * energy
        SpotHIGH   = self.SPC_double_TH * energy
    
        SPimage = image * (
            self.detector_parameters["electrons_per_adc_count"]
            * self.detector_parameters["energy_eh"]
        )
        # ~ self.SPimage = SPimage
    
        inner = SPimage[r:-r, r:-r]
        central_pixel = np.argwhere((inner > LOW_TH_PX) & (inner < HIGH_TH_PX))
        central_pixel += r
    
        cp = []
        spots = []
    
        for y, x in central_pixel:
            spot = SPimage[y-r:y+r+1, x-r:x+r+1]
            center = SPimage[y, x]
    
            if np.any(spot > center):
                continue
    
            spots.append(spot)
            cp.append((y, x))
    
        if spots:
            spots = np.stack(spots, axis=0)
            cp = np.asarray(cp, dtype=float)
    
            intensities = spots.sum(axis=(1, 2))
    
            index_rel = np.arange(gs) - r
    
            yc = (spots.sum(axis=2) @ index_rel) / intensities
            xc = (spots.sum(axis=1) @ index_rel) / intensities
    
            cp[:, 0] += yc
            cp[:, 1] += xc
            
            # ~ cp[:,0] += self.roi[1]
            cp[:,1] += self.roi[0]
            
            cp = np.column_stack([cp, intensities])
        else:
            print("No spots!!!")
            cp = np.array([[0, 0, 0.0]], dtype=float)
            intensities = np.array([0.0])
        
        self.cp = cp
        self.centers = cp.copy()
        
        # Correct the slope
        nrows, ncols = self.image.shape
        dx = cp[:, 1] - 1024
        # ~ cp[:, 0] += self.roi[1]
        cp[:, 0] -= dx * self.slope
        cp[:, 0] -= dx**2 * float(self.smile)
    
        single = (intensities > SpotLOW) & (intensities <= SpotHIGH)
        double = intensities > SpotHIGH
    
        step = 1 / self.points_per_pixel
        pixel = np.linspace(0, nrows-1, int(nrows*self.points_per_pixel))
        pixel_bins = np.concatenate([
            pixel-step/2, [pixel[-1] + step/2],
        ])
    
        spectrum_single = np.histogram(cp[single, 0], pixel_bins)[0]
        spectrum_double = np.histogram(cp[double, 0], pixel_bins)[0]
    
        self._add_spectrum_column("SPC single events", spectrum_single)
        self._add_spectrum_column("SPC double events", spectrum_double)
        self._add_spectrum_column("SPC", spectrum_single + 2 * spectrum_double)
    
    
    
    def save(self, outputfile, savedatfile=False, replacefile=False, mode="append"):
        t0 = time.perf_counter()
        """ Generate output and write into *.spec and *.dat files """
        
        for counter in self.norm_counters:
            if counter in self.counters:
                self.spectrum[counter] = 0*self.spectrum["Pixel"] + self.counters[counter]
            
        output = []
        output.append(
            "#S %d  Scan %04d:%04d - %s\n"
            % (self.scan_number, self.scan_number, self.point_number, self.scan_title)
        )
        output.append(
            "#D %s\n" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        )

        # Motor names and positions
        motor_mne_lines = []
        motor_pos_lines = []

        motor_mne, motor_pos = zip(*self.motors.items())
        motor_mne = list(motor_mne)
        motor_pos = [str(mp) for mp in motor_pos]
        for iii in range(len(motor_mne) // 8):
            motor_mne_lines.append(
                "  ".join(["#O%d" % iii] + motor_mne[8 * iii : 8 * (iii + 1)])
            )
            motor_pos_lines.append(
                "  ".join(["#P%d" % iii] + motor_pos[8 * iii : 8 * (iii + 1)])
            )
        if len(motor_mne) % 8 != 0:
            iii = len(motor_mne) // 8
            motor_mne_lines.append("  ".join(["#O%d" % iii] + motor_mne[8 * iii :]))
            motor_pos_lines.append("  ".join(["#P%d" % iii] + motor_pos[8 * iii :]))
        output.append("\n".join(motor_mne_lines) + "\n")
        output.append("\n".join(motor_pos_lines) + "\n")
        output.append("#C  \n")

        # Image information
        # ~ output.append("#C  %s" % self.image_filename)
        # ~ output.append("#C  Scan number    %s\n" % self.scan_number)
        # ~ output.append("#C  Point number   %s\n" % self.point_number)
        # ~ output.append("#C  Exposure time  %s\n" % self.exposure)
        # ~ output.append("#C  \n")

        # Counter names and values
        output.append("#C  -- Counters start\n")
        for cnt_mne, cnt_pos in sorted(self.counters.items()):
            output.append("#C  %s  %s\n" % (cnt_mne, cnt_pos))
        output.append("#C  -- Counters end\n")
        output.append("#C  \n")

        # ROI
        output.append(f"#C  ROI: {self.roi}")
        output.append("#C  \n")

        # Parameters for extracting the spectra
        output.append("#C  -- Specgen parameters start\n")
        for param, value in self.parameters.items():
            output.append(f"#C  {param}  {value}\n")
        output.append("#C  -- Specgen parameters end\n")
        output.append("#C  \n")

        # Spectrum
        output.append("#N %d\n" % len(self.spectrum.keys()))
        output.append("#L  " + "  ".join(self.spectrum.keys()) + "\n")
        output.append(
            "".join(
                "%s\n" % (" ".join([str(si) for si in s]))
                for s in np.vstack(
                    [self.spectrum[colname] for colname in self.spectrum.keys()]
                ).T.tolist()
            )
        )

        output.append("\n")

        # Save into external data files
        specfilename = outputfile
        path = os.path.dirname(specfilename)
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        if not os.path.isfile(specfilename) or replacefile:
            with open("%s" % (specfilename), "wb+") as f:
                fileheader = "#F %s\n\n" % (specfilename)
                f.write(fileheader.encode("ascii"))
        else:
            if mode == "replace":
                specfile = SpecFileHandler(outputfile)
                specfile.removeLastScan(scannumber=self.scan_number)

        with open("%s" % (specfilename), "ab+") as f:
            f.write("".join(output).encode("ascii"))
        print('Spectrum saved to "%s"' % (specfilename))

        if savedatfile:
            if not os.path.isdir(specfilename.rstrip(".spec")):
                os.mkdir(specfilename.rstrip(".spec"))

            datfilename = "%s/S%04d_%04d.dat" % (
                specfilename.rstrip(".spec"),
                self.scan_number,
                self.point_number,
            )
            with open(datfilename, "wb+") as f:
                f.write("".join(output).encode("ascii"))
            print('Spectrum saved to "%s"\n' % (datfilename))

        print("Save spectrum: %.2fms" % (1e3 * (time.perf_counter() - t0)))



    def save_to_hdf5(self, outputfile):
        nvalues = self.spectrum["Pixel"].shape[0]
        
        nvalues = 1
        export_dict = {
            f"{self.scan_number}.{self.point_number}": {
                "title": self.scan_title,
                "scan_nb": self.scan_number,
                "start_time": self.image_date,
                
        
                "instrument": {
                    "name": "ID32",
        
                    "positioners_start": {
                        **positioners_start,
                    },
                },
        
                "measurement": {
                    **self.spectrum,
                    **{cnt: np.full(nvalues, val) for cnt, val in self.counters.items()},
                },
                
                "processing": {
                    "specgen_parameters": hdf5_safe_dict(self.parameters),
                    "detector_parameters": self.detector_parameters,
                    "energy_calibration": self.energy_calibration,
                },
                
            },
        }
        
        dictdump.dicttoh5(export_dict,"test.h5", mode="a")
        
