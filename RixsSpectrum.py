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


import os, time
import numpy as np
from PyMca5.PyMcaIO import EdfFile
from RTB_Math import RTB_Math

import silx.io



class RixsSpectrum():
    def __init__(self, imgfilename, slope=-.0089, points_per_pixel=2, binning=1,
        lower_threshold=0.05, upper_threshold=0.9, masksize=1, 
        SPC=True, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        SPC_single_threshold=.2, SPC_double_threshold=1.5, 
        roi=None, ccd_params=None, extract_background=True, background=None,
        background_aqn_time=None, background_force_zero=False,
        background_smoothing = False, background_smoothing_width=0):
        
        self.RTB_Math = RTB_Math()
        
        self.imgfilename            = imgfilename
        self.slope                  = slope
        self.points_per_pixel       = points_per_pixel
        self.binning                = binning        
        self.upper_threshold        = upper_threshold
        self.lower_threshold        = lower_threshold
        self.masksize               = masksize
        
        self.SPC                    = SPC
        self.SPC_gridsize           = SPC_gridsize
        self.SPC_low_TH             = SPC_low_threshold
        self.SPC_high_TH            = SPC_high_threshold
        self.SPC_single_TH          = SPC_single_threshold
        self.SPC_double_TH          = SPC_double_threshold
        
        self.roi = roi
        
        if ccd_params != None and len(ccd_params)==3:
            self.ccd_params = {
                'DarkCounts': ccd_params[0],
                'ElectronsPerCount': ccd_params[1],
                'Energy_eh': ccd_params[2]
                }
        else:
            self.ccd_params = {
                'DarkCounts': 0.00016, # counts per pixel per s
                'ElectronsPerCount': 1.2, 
                'Energy_eh': 3.6 # Electron-hole pair generation energy (eV)
                }
        
        self.extract_background     = extract_background
        self.background             = background
        self.background_aqn_time    = background_aqn_time
        self.background_force_zero  = background_force_zero
        self.background_smoothing   = background_smoothing
        self.backgroundSmoothingWidth = background_smoothing_width
        
        self.get_image()
        self.cut_image()
        self.filter_image()
        self.make_traditional_spectrum()
        
        if self.SPC:
            self.make_single_photon_counting_spectrum()
        
        
        return None
    
    
    def get_esrf_id32_image(self):
        self.image = EdfFile.EdfFile(self.imgfilename)
        self.motor_mne = self.image.GetHeader(0)['motor_mne'].split()
        self.motor_pos = self.image.GetHeader(0)['motor_pos'].split()
        if 'H' in self.image.GetHeader(0).keys():
            self.motor_mne.append('H')
            self.motor_mne.append('K')
            self.motor_mne.append('L')
            self.motor_pos.append('%.4f' % round(float(self.image.GetHeader(0)['H']), 4))
            self.motor_pos.append('%.4f' % round(float(self.image.GetHeader(0)['K']), 4))
            self.motor_pos.append('%.4f' % round(float(self.image.GetHeader(0)['L']), 4))
        self.Motors = dict(zip(self.motor_mne, 
            [float(m) for m in self.motor_pos]))
        if 'counter_mne' in self.image.GetHeader(0).keys():
            self.Counters = dict(zip(
                self.image.GetHeader(0)['counter_mne'].split(),
                self.image.GetHeader(0)['counter_pos'].split()))
        else:
            self.Counters = None
        self.imageData = self.image.GetData(0)
        self.imageData = np.array(self.imageData, dtype=float)
        if len(self.imageData.shape) < 3:
            self.imageData.shape += 1,
        self.info = self.image.GetHeader(0)
        self.info['ExposureTime'] =  np.array([float(self.info['count_time'])])
        self.info['ImageNumber'] = self.info['run']
        self.info['ScanNumber'] = self.info['scan_no']
        self.info['ImageFileName'] = '%s/%s' % (self.info['dir'], 
            self.image.FileName.split('/')[-1])
        self.info['Comments'] = []
    
    
    def get_dls_i21_image(self):
        self.image = silx.io.open(self.imgfilename)
        # Get motor positions, ID and temperature information
        self.motor_mne = []
        self.motor_pos = []
        self.info = {}
        self.info['Comments'] = []
        for entry in sorted(self.image['entry1/before_scan']):
            if len(self.image['entry1/before_scan/%s' % (entry)]) == 1:
                motorname = list(self.image['entry1/before_scan/%s' % (entry)])[0]
                motorpos = self.image['entry1/before_scan/%s/%s' % (entry, motorname)][()]
                if type(motorpos) == type(''):
                    self.info['Comments'].append('%15s %15s' % (motorname, motorpos))
                else:
                    self.motor_mne.append(motorname)
                    self.motor_pos.append(motorpos)
            else:
                self.info['Comments'].append(entry)
                for subentry in sorted(self.image['entry1/before_scan/%s' % (entry)]):
                    self.info['Comments'].append('%s %15s %15s' % (entry, subentry, 
                        self.image['entry1/before_scan/%s/%s' % (entry, subentry)][()]))
        self.motor_mne.extend(['H', 'K', 'L'])
        self.motor_pos.extend([0, 0, 0])
        self.Motors = dict(zip(self.motor_mne, [m for m in self.motor_pos]))
        self.Counters = None
        
        # Get image data
        self.imageData = self.image['entry1/andor/data']
        self.imageData = np.array(self.imageData, dtype=float)
        self.imageData = np.moveaxis(self.imageData, 0, -1)
        self.imageData = np.flipud(self.imageData)
        
        # Exposure time
        self.info['ExposureTime'] = self.image['entry1/instrument/andor/count_time'][()]
        
        # Scan number
        self.info['ScanNumber'] = self.image['entry1/entry_identifier'][()]
        self.info['ImageNumber'] = self.info['ScanNumber']
        self.info['ImageFileName'] = self.imgfilename.split('/')[-1]
        self.info['Experiment'] = self.image['entry1/experiment_identifier'][()]
        self.info['User'] = self.image['entry1/user01/username'][()]
        
        
    
    
    def get_image(self):
        print(self.imgfilename)
        
        # ESRF ID32
        if self.imgfilename.endswith('.edf'):
            self.get_esrf_id32_image()
            self.info['Beamline'] = 'ESRF - ID32'
        
        # DLS I21
        if self.imgfilename.endswith('.nxs'):
            self.get_dls_i21_image()
            self.info['Beamline'] = 'DLS - I21'
        
        self.info['Dim_1'] = self.imageData.shape[0]
        self.info['Dim_2'] = self.imageData.shape[1]
        self.info['NumberOfFrames'] = self.imageData.shape[2]
        self.info['ImageDate'] = time.strftime('%Y-%m-%d %H:%M:%S', 
            time.localtime(os.stat(self.imgfilename).st_mtime))
        return None
    
    
    def cut_image(self):
        if self.roi != None and len(self.roi) == 4:
            roi_copy = np.array(self.roi)
            for i, r in enumerate(self.roi):
                if r > self.imageData.shape[1-i//2]:
                    roi_copy[i] = self.imageData.shape[1-i//2]
            self.imageData = self.imageData[roi_copy[2]:roi_copy[3], roi_copy[0]:roi_copy[1]]
        return None
    
    
    
    def filter_image(self):
        """
        Remove the dark counts and spikes from the image
        """
        if 'energy' not in self.Motors.keys():
            self.Motors['energy'] = 930
        
        self.cont_photon = float(self.Motors['energy']) / \
            self.ccd_params['Energy_eh'] / self.ccd_params['ElectronsPerCount']
        
        low_cutoff = self.lower_threshold * self.cont_photon * self.binning
        high_cutoff = self.upper_threshold * self.cont_photon * self.binning
        
        
        # Background subtraction
        if self.extract_background:
            self.rawImageData = 1. * self.imageData
        if type(self.background) == type(self.imageData):
            if self.background.shape == self.imageData.shape[:2]:
                if self.background_aqn_time:
                    self.imageData -= np.array(self.info['ExposureTime']) \
                        * np.dstack(self.imageData.shape[2]*[self.background]) \
                        / self.background_aqn_time
                else:
                    self.imageData -= \
                        np.dstack(self.imageData.shape[2]*[self.background])
            else:
                self.imageData -= self.baseline
        
        offset = self.imageData[:50,:,:].mean(axis=0).mean(axis=0)
        self.baseline = offset + self.ccd_params['DarkCounts'] * self.info['ExposureTime']
        
        if (type(self.background) == type(None)) or self.background_force_zero:
            self.imageData -= self.baseline
            
        
        # Thresholding
        self.imageData = np.where(self.imageData < low_cutoff, 
            0*self.imageData, self.imageData)
        
        mask = np.where(self.imageData > high_cutoff, 1, 0)
        for i in range(1, 1+self.masksize//2):
            mask[i:,:] += np.roll(mask, 1, axis=0)[i:,:]
            mask[:-i,:] += np.roll(mask, -1, axis=0)[:-i,:]
        for i in range(1, 1+self.masksize//2):
            mask[:,i:] += np.roll(mask, 1, axis=1)[:,i:]
            mask[:,:-i] += np.roll(mask, -1, axis=1)[:,:-i]
        # ~ mask += mask.sum(axis=0) # masks the entire line in case of a high-energy event
        mask = 0 * mask + (mask>0)
        self.imageData = np.where(mask, 0*self.imageData, self.imageData)
        
        return None
    
    
    def fft_filter_spectrum(self, signal, kernel):
        freq = np.fft.fft(signal)
        assert(signal.shape == kernel.shape)
        freq_kernel = np.fft.fft(np.fft.ifftshift(kernel))
        convolved = freq*freq_kernel # by the Convolution theorem
        signal_smooth = np.fft.ifft(convolved).real
        signal_smooth *= signal.mean() / signal_smooth.mean()
        return signal_smooth
    
    
    
    
    def make_traditional_spectrum(self):
        """
        Integration along iso-energy lines
        """
        
        self.spectrum = {}
        self.spectrum_cols = []
        self.spectrum_cols.append('Pixel')
        if self.Counters != None:
            self.spectrum_cols.append('Storage ring current / 100mA')
            self.spectrum_cols.append('Mirror current / 1e6')
            self.spectrum_cols.append('Sample current / 1e6')
        self.spectrum_cols.append('Acquisition time')
        if self.extract_background:
            self.spectrum_cols.append('CCD raw signal (ADC counts)')
            self.spectrum_cols.append('CCD raw background (ADC counts)')
            self.spectrum_cols.append('CCD background (ADC counts)')
            if self.background_smoothing:
                self.spectrum_cols.append(
                                'CCD thresholding (ADC counts)')
                self.spectrum_cols.append(
                                'CCD background smoothed (ADC counts)')
        self.spectrum_cols.append('CCD filtered signal (ADC counts)')
        self.spectrum_cols.append('Photons')
        
        for framenumber in range(self.info['NumberOfFrames']):
            imgData = self.imageData[:,:,framenumber]
            nrows, ncols = imgData.shape
            iso = self.binning * self.slope * np.arange(ncols)
            maxshift = np.ceil(np.abs(iso).max() * self.points_per_pixel)
            self.maxshift = int(maxshift)
            step = 1 / self.points_per_pixel
            x0 = np.arange(nrows)
            x_spectrum = np.linspace(0, nrows, nrows*self.points_per_pixel)
            y_sum = 0 * x_spectrum
            
            if self.extract_background:
                
                rawImgData = self.rawImageData[:,:,framenumber]
                yraw_sum = 0 * x_spectrum
                ythreshold_sum = 0 * x_spectrum
                if type(self.background) != type(self.imageData) or framenumber == 0:
                    background = 0 * x_spectrum
                
            for iii in range(ncols):
                x_shifted = x0 - iso[iii] - 1 / self.points_per_pixel
                y_sum += np.interp(x_spectrum, x_shifted, 
                    imgData[:,iii]) * step
                if self.extract_background:
                    yraw_sum += np.interp(x_spectrum, x_shifted, 
                        rawImgData[:,iii]) * step
                    if self.background_smoothing:
                        ythreshold_sum += np.interp(x_spectrum, x_shifted, 
                            rawImgData[:,iii]-imgData[:,iii]) * step
                    if type(self.background) == type(self.imageData):
                        if framenumber == 0:
                            background += np.interp(x_spectrum, x_shifted, 
                                self.background[:,iii]) * step
                    elif type(self.background) == type(None):
                        background += 0 * x_spectrum + self.baseline[framenumber] * step
            
            
            
            
            self.spectrum[framenumber] = {}
            self.spectrum[framenumber]['Pixel'] = x_spectrum
            if self.Counters != None:
                self.spectrum[framenumber]['Storage ring current / 100mA'] = \
                    0*x_spectrum + float(self.Counters['srcur'])/100
                self.spectrum[framenumber]['Mirror current / 1e6'] = \
                    0*x_spectrum + float(self.Counters['mir'])/1e6
                self.spectrum[framenumber]['Sample current / 1e6'] = \
                    0*x_spectrum + float(self.Counters['sam'])/1e6
            self.spectrum[framenumber]['Acquisition time'] = 0 * x_spectrum + self.info['ExposureTime'][framenumber]
            if self.extract_background:
                self.spectrum[framenumber]['CCD raw signal (ADC counts)'] = yraw_sum[::-1]
                self.spectrum[framenumber]['CCD raw background (ADC counts)'] = 0 * x_spectrum + np.flip(background, axis=0)
                self.spectrum[framenumber]['CCD background (ADC counts)'] = yraw_sum[::-1] - y_sum[::-1]
                if self.background_smoothing:
                    # Older version, creates artifacts with thresholding
                    # ~ smooth1DBackground = self.RTB_Math.gaussian_filter(
                        # ~ yraw_sum[::-1]-y_sum[::-1], 
                        # ~ self.backgroundSmoothingWidth)
                    smooth1DBackground = self.RTB_Math.gaussian_filter(
                        self.spectrum[framenumber]['CCD raw background (ADC counts)'], 
                        self.backgroundSmoothingWidth)
                    smooth1DBackground += ythreshold_sum[::-1] - background[::-1]
                    
                    self.spectrum[framenumber][
                                        'CCD thresholding (ADC counts)'] \
                        = 0 * x_spectrum + ythreshold_sum[::-1] - background[::-1]
                    
                    self.spectrum[framenumber][
                                        'CCD background smoothed (ADC counts)'] \
                        = 0 * x_spectrum + smooth1DBackground
                    self.spectrum[framenumber][
                        'CCD filtered signal (ADC counts)']\
                        = yraw_sum[::-1] - smooth1DBackground
                    self.spectrum[framenumber]['Photons'] \
                        = (yraw_sum[::-1]-smooth1DBackground) / self.cont_photon
                else:
                    self.spectrum[framenumber]['CCD filtered signal (ADC counts)'] = y_sum[::-1]
                    self.spectrum[framenumber]['Photons'] = y_sum[::-1] / self.cont_photon
            else:
                self.spectrum[framenumber]['CCD filtered signal (ADC counts)'] = y_sum[::-1]
                self.spectrum[framenumber]['Photons'] = y_sum[::-1] / self.cont_photon
            
        return None
    
    
    def make_single_photon_counting_spectrum(self):
        gs = self.SPC_gridsize
        
        LOW_TH_PX = self.SPC_low_TH * self.Motors['energy']
        HIGH_TH_PX = self.SPC_high_TH * self.Motors['energy']
        SpotLOW = self.SPC_single_TH * self.Motors['energy']
        SpotHIGH = self.SPC_double_TH * self.Motors['energy']
        
        # Rescale image from electron counts to photon energy
        
        self.spectrum_cols.append('SPC single events')
        self.spectrum_cols.append('SPC double events')
        self.spectrum_cols.append('SPC')
        
        self.cp = []
        
        for framenumber in range(self.info['NumberOfFrames']):
            self.SPimage = self.imageData[:,:,framenumber] \
                            * self.ccd_params['ElectronsPerCount'] \
                            * self.ccd_params['Energy_eh']
            # Find candidates for central pixels
            central_pixel = np.argwhere(
                (self.SPimage[gs//2:-gs//2, gs//2:-gs//2] > LOW_TH_PX) * 
                (self.SPimage[gs//2:-gs//2, gs//2:-gs//2] < HIGH_TH_PX))
            central_pixel += np.array([gs//2, gs//2])
            
            # Identify central pixels
            cp = []
            spots = []
            for i, c in enumerate(central_pixel.tolist()):
                if np.where(self.SPimage[c[0]-gs//2:c[0]+gs//2+1, \
                    c[1]-gs//2:c[1]+gs//2+1] > self.SPimage[c[0], 
                    c[1]], 1, 0).sum() > 0:
                    pass
                else:
                    spots.append(self.SPimage[
                        c[0]-gs//2:c[0]+gs//2+1, c[1]-gs//2:c[1]+gs//2+1])
                    cp.append([c[0], c[1]])
            if len(spots) != 0:
                spots = np.dstack(spots)
                cp = np.array(cp, dtype=float)
            
                # Total intensity in each spot
                intensities = spots.sum(axis=0).sum(axis=0)
            
                # Find center of mass
                index_rel = np.arange(gs) - gs//2
                xc = np.dot(spots.sum(axis=0).T, index_rel) / intensities
                yc = np.dot(spots.sum(axis=1).T, index_rel) / intensities
                cp += np.vstack([yc, xc]).T
            else:
                print("No spots!!!")
                cp = np.array([[0, 0]])
                intensities = np.array([0])
    
            self.cp.append(1.*cp)
    
            # Correct the slope
            cp[:,0] = cp[:,0] - cp[:,1] * self.slope
            
            # Separate single and double events
            cp_single = np.where(
                (intensities>SpotLOW)*(intensities<=SpotHIGH), cp[:,0], -1)
            cp_double = np.where(intensities>SpotHIGH, cp[:,0], -1)
            
            # Generate spectrum
            pixel_new = np.linspace(0, self.SPimage.shape[0], 
                self.SPimage.shape[0]*self.points_per_pixel+1)
            pixel_new += 0.5 / self.points_per_pixel
            spectrum_single = np.histogram(cp_single, pixel_new, normed=0)[0][::-1]
            spectrum_double = np.histogram(cp_double, pixel_new, normed=0)[0][::-1]
            spectrum = spectrum_single + 2 * spectrum_double
            
            # ~ if (self.slope >= 0 and self.info['Beamline'] == 'ESRF - ID32') \
               # ~ or (self.slope >= 0 and self.info['Beamline'] == 'DLS - I21'):
                # ~ spectrum_single = spectrum_single[self.maxshift:]
                # ~ spectrum_double = spectrum_double[self.maxshift:]
                # ~ spectrum = spectrum[self.maxshift:]
            # ~ else:
                # ~ spectrum_single = spectrum_single[:-self.maxshift]
                # ~ spectrum_double = spectrum_double[:-self.maxshift]
                # ~ spectrum = spectrum[:-self.maxshift]
            
            # Add spectrum to list of counters
            self.spectrum[framenumber]['SPC single events'] = 1 * spectrum_single
            self.spectrum[framenumber]['SPC double events'] = 1 * spectrum_double
            self.spectrum[framenumber]['SPC'] = 1 * spectrum
            
        return None
        
        
    
    def save(self, outputfile='', savedatfile=False):
        """ Generate output and write into *.spec and *.dat files """
        info = self.info
        
        output = []
        
        # Parameters when extracting the spectra
        output.append('#C  Parameters for image to spectra conversion\n')
        output.append('#C  Slope                        %.6f\n' % self.slope)
        output.append('#C  Points per pixel             %.2f\n' % self.points_per_pixel)
        output.append('#C  Binning                      %d\n' % self.binning)
        output.append('#C  Lower threshold              %.2f\n' % self.lower_threshold)
        output.append('#C  Upper threshold              %.2f\n' % self.upper_threshold)
        output.append('#C  Mask                         %dx%d\n' % (self.masksize, self.masksize))
        output.append('#C  SPC grid size                %dx%d\n' % (self.SPC_gridsize,self.SPC_gridsize))
        output.append('#C  SPC low threshold            %.2f\n' % self.SPC_low_TH)
        output.append('#C  SPC high threshold           %.2f\n' % self.SPC_high_TH)
        output.append('#C  SPC single event threshold   %.2f\n' % self.SPC_single_TH)
        output.append('#C  SPC double event threshold   %.2f\n' % self.SPC_double_TH)
        output.append('#C  \n')
        
        if info['Comments']:
            output.append(''.join(['#C  %s\n' % c for c in info['Comments']]))
            output.append('#C  \n')
        
        # Motor names and positions
        motor_mne_lines = []
        motor_pos_lines = []
        for iii in range(len(self.motor_mne)//8):
            motor_mne_lines.append(
                '  '.join(['#O%d' % iii] + self.motor_mne[8*iii:8*(iii+1)]))
            motor_pos_lines.append(
                '  '.join(['#P%d' % iii] + [str(mp) for mp in self.motor_pos[8*iii:8*(iii+1)]]))
        if len(self.motor_mne) % 8 != 0:
            iii = len(self.motor_mne)//8
            motor_mne_lines.append(
                '  '.join(['#O%d' % iii] + self.motor_mne[8*iii:]))
            motor_pos_lines.append(
                '  '.join(['#P%d' % iii] + [str(mp) for mp in self.motor_pos[8*iii:]]))
        output.append('\n'.join(motor_mne_lines) + '\n')
        output.append('\n'.join(motor_pos_lines) + '\n')
        
        # Counter names and values
        if self.Counters != None:
            output.append('#C  \n')
            for cnt_mne, cnt_pos in sorted(self.Counters.items()):
                output.append('#C  %s  %s\n' % (cnt_mne, cnt_pos))
        
        # HKL
        if 'H' in info.keys():
            output.append('\n#G4  %s %s %s\n' % (info['H'], info['K'], info['L']))
        

        
        # Spectrum
        output.append('#N %d\n' % len(self.spectrum_cols))
        output.append('#L  ' + '  '.join(self.spectrum_cols) + '\n')
        
        for framenumber in range(info['NumberOfFrames']):
            
            if info['Beamline'] == 'ESRF - ID32':
                frmoutput = ['#S %s  Scan %04d : %04d - %.1f seconds\n' % (
                    info['ImageNumber'], int(info['ScanNumber']), 
                    int(info['point_no']), info['ExposureTime'][framenumber])]
            elif self.info['Beamline'] == 'DLS - I21':
                frmoutput = ['#S %s  %s : %04d - %.1f seconds\n' % (
                    info['ImageNumber'], info['ImageFileName'], 
                    framenumber, info['ExposureTime'][framenumber])]
            
            frmoutput.append('#D %s\n' % time.strftime('%Y-%m-%d %H:%M:%S', 
                time.localtime(time.time())))
            
            # Image information
            frmoutput.append('#C  \n')
            frmoutput.append('#C  Beamline       %s\n' % info['Beamline'])
            if 'Experiment' in info.keys():
                frmoutput.append('#C  Experiment     %s\n' % info['Experiment'])
            if 'User' in info.keys():
                frmoutput.append('#C  User           %s\n' % info['User'])
            frmoutput.append('#C  \n')
            frmoutput.append('#C  Image name     %s\n' % info['ImageFileName'])
            frmoutput.append('#C  Number of frames    %s\n' % info['NumberOfFrames'])
            frmoutput.append('#C  Current frame    %d\n' % framenumber)
            if info['Beamline'] == 'ESRF - ID32':
                frmoutput.append('#C  ROI columns    %s...%s     rows  %s...%s\n' % (
                    info['col_beg'], info['col_end'], 
                    info['row_beg'], info['row_end']))
            frmoutput.append('#C  Dimensions     %s x %s\n' % (
                info['Dim_1'], info['Dim_2']))
            frmoutput.append('#C  Exposure time       %.1f seconds\n' % info['ExposureTime'][framenumber])
            if info['Beamline'] == 'ESRF - ID32':
                frmoutput.append('#C  Offset         %s\n' % info['offset'])
                frmoutput.append('#C  Scan number    %s\n' % info['scan_no'])
                frmoutput.append('#C  Point number   %s\n' % info['point_no'])
            frmoutput.append('#C  \n')
            
            frmoutput += output
            
            frmoutput.append(
                ''.join('%s\n' % (' '.join([str(si) for si in s])) 
                for s in np.vstack(
                    [self.spectrum[framenumber][colname] 
                        for colname in self.spectrum_cols]).T.tolist()))
            
            frmoutput.append('\n')
            
            # Save into external data files
            if outputfile == '':
                path = header['dir'].replace('/Images', '/Spectra')
                specfilename = '%s/%s.spec' % (path, header['prefix'])
            else:
                specfilename = outputfile
            if not os.path.isfile(specfilename):
                with open('%s' % (specfilename), 'wb+') as f:
                    fileheader = '#F %s\n\n' % (specfilename)
                    f.write(fileheader.encode('ascii'))
            with open('%s' % (specfilename), 'ab+') as f:
                f.write(''.join(frmoutput).encode('ascii'))
            print('Spectrum saved to \"%s\"' % (specfilename))
            
            if savedatfile:
                if not os.path.isdir(specfilename.rstrip('.spec')):
                    os.mkdir(specfilename.rstrip('.spec'))
                
                if info['Beamline'] == 'ESRF - ID32':
                    datfilename = '%s/Scan_%04d_%04d.dat' % (specfilename.rstrip('.spec'),
                        int(info['ScanNumber']), int(info['point_no']))
                elif info['Beamline'] == 'DLS - I21':
                    datfilename = '%s/%s_%04d.dat' % (specfilename.rstrip('.spec'),
                        info['ImageFileName'].rstrip('.nxs'), framenumber)
                with open(datfilename, 'wb+') as f:
                    f.write(''.join(frmoutput).encode('ascii'))
                print('Spectrum saved to \"%s\"\n' % (datfilename))
        
        return None



def main():
    
    dark = RixsSpectrum('data/Images_I21/i21-77459.nxs', slope=-.0215, points_per_pixel=2, binning=1,
        lower_threshold=-1e5, upper_threshold=1e5, masksize=5, 
        SPC=False, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        SPC_single_threshold=.2, SPC_double_threshold=1.5, 
        roi=None, ccd_params=[0.00016, 3.9, 3.6], background='off')
    # ~ dark.save('data/Images_I21/_test.spec')
    
    dark = RixsSpectrum('data/Images_I21/i21-77459.nxs', slope=-.0215, points_per_pixel=2, binning=1,
        lower_threshold=-1e5, upper_threshold=1e5, masksize=5, 
        SPC=False, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        SPC_single_threshold=.2, SPC_double_threshold=1.5, 
        roi=None, ccd_params=[0.00016, 3.9, 3.6], background=dark.rawImageData[:,:,0],
        background_smoothing = True)
    # ~ dark.save('data/Images_I21/_test.spec')
    
    signal = RixsSpectrum('data/Images_I21/i21-77429.nxs', slope=-.0215, points_per_pixel=2, binning=1,
        lower_threshold=-1e5, upper_threshold=1e5, masksize=5, 
        SPC=False, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        SPC_single_threshold=.2, SPC_double_threshold=1.5, 
        roi=None, ccd_params=[0.00016, 3.9, 3.6], background=dark.rawImageData[:,:,0],
        background_smoothing = True, background_smoothing_width=30)
    signal.save('data/Images_I21/_test.spec')
    
    
    
    
    # ~ x = RixsSpectrum('data/Bi2201_0300.edf', slope=-.0089, points_per_pixel=2, binning=1,
        # ~ lower_threshold=0.05, upper_threshold=0.9, masksize=1, 
        # ~ SPC=True, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        # ~ SPC_single_threshold=.2, SPC_double_threshold=1.5, 
        # ~ roi=None, ccd_params=None)
    
    # ~ x = RixsSpectrum('data/Images_I21/i21-77514.nxs', slope=-.0089, points_per_pixel=2, binning=1,
        # ~ lower_threshold=-1e5, upper_threshold=1e5, masksize=5, 
        # ~ SPC=True, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        # ~ SPC_single_threshold=.2, SPC_double_threshold=1.5, 
        # ~ roi=None, ccd_params=[0.00016, 3.9, 3.6])
    
    # ~ x1 = RixsSpectrum('data/Images_I21/i21-38276.nxs', slope=.0215, points_per_pixel=2, binning=1,
        # ~ lower_threshold=-1e5, upper_threshold=1e5, masksize=1, 
        # ~ SPC=False, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        # ~ SPC_single_threshold=.2, SPC_double_threshold=1.5, 
        # ~ roi=None, ccd_params=[0.00016, 3.9, 3.6], extract_background=True)
    # ~ x1.save('data/Images_I21/_test.spec')
    
    # ~ x2 = RixsSpectrum('data/DY5_150319_0014.edf', slope=-.0254, points_per_pixel=2.7, binning=1,
        # ~ lower_threshold=-1, upper_threshold=20, masksize=5, 
        # ~ SPC=True, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        # ~ SPC_single_threshold=.4, SPC_double_threshold=1.5, 
        # ~ roi=None, ccd_params=None)
    # ~ x2.save('data/Images_I21/_test.spec')
    
    
    return 0

if __name__ == '__main__':
    main()

