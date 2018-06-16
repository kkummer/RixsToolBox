#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os, time
import numpy as np
from scipy import interpolate, ndimage
from PyMca5.PyMcaIO import EdfFile



class RixsSpectrum():
    def __init__(self, edffile, slope=-.0089, points_per_pixel=2, binning=1,
        lower_threshold=0.05, upper_threshold=0.9, masksize=1, 
        SPC=True, SPC_gridsize= 3, SPC_low_threshold=.2, SPC_high_threshold=1, 
        SPC_single_threshold=.2, SPC_double_threshold=1.5):
        
        self.edffile = edffile
        self.slope = slope
        self.points_per_pixel = points_per_pixel
        self.binning = binning        
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.masksize = masksize
        
        self.SPC = SPC
        self.SPC_gridsize = SPC_gridsize
        self.SPC_low_TH = SPC_low_threshold
        self.SPC_high_TH = SPC_high_threshold
        self.SPC_single_TH = SPC_single_threshold
        self.SPC_double_TH = SPC_double_threshold
        
        
        self.ccd_params = {
            'DarkCounts': 0.00016, # counts per pixel per s
            'ElectronsPerCount': 2.5, 
            'Energy_eh': 3.6 # Electron-hole pair generation energy (eV)
            }
        
        self.get_image()
        self.filter_image()
        self.make_traditional_spectrum()
        
        if self.SPC:
            self.make_single_photon_counting_spectrum()
        
        return None
    
    
    def get_image(self):
        print self.edffile
        self.image = EdfFile.EdfFile(self.edffile)
        self.imagedate = time.strftime('%Y-%m-%d %H:%M:%S', 
            time.localtime(os.stat(self.edffile).st_mtime))
        self.motor_mne = self.image.GetHeader(0)['motor_mne'].split()
        self.motor_pos = self.image.GetHeader(0)['motor_pos'].split()
        self.Motors = dict(zip(self.motor_mne, 
            [float(m) for m in self.motor_pos]))
        if 'counter_mne' in self.image.GetHeader(0).keys():
            self.Counters = dict(zip(
                self.image.GetHeader(0)['counter_mne'].split(),
                self.image.GetHeader(0)['counter_pos'].split()))
        else:
            self.Counters = None
        self.image.Data = self.image.GetData(0)
        self.image.Data = np.array(self.image.Data, dtype=float)
        self.cont_photon = self.Motors['energy'] / \
            self.ccd_params['Energy_eh'] / self.ccd_params['ElectronsPerCount']
        return None
    
    
    def filter_image(self):
        """
        Remove the dark counts and spikes from the image and return a deep copy. 
        This function strictly follows the Milano Matlab macros.
        """
        offset = self.image.Data[:50,:].mean()
        self.exposure =  float(self.image.GetHeader(0)['preset'])
        baseline = offset + self.ccd_params['DarkCounts'] * self.exposure
        low_cutoff = self.lower_threshold * self.cont_photon * self.binning
        high_cutoff = self.upper_threshold * self.cont_photon * self.binning
        
        self.raw_image = 1. * self.image.Data
        self.image.Data -= baseline
        
        self.image.Data = np.where(self.image.Data < low_cutoff, 
            0*self.image.Data, self.image.Data)
        if self.masksize != 1:
            mask = np.where(self.image.Data > high_cutoff, 1, 0)
            mask = ndimage.correlate(mask, 
                np.ones((self.masksize, self.masksize)))
            self.image.Data = np.where(mask,
                0*self.image.Data, self.image.Data)
        else:
            self.image.Data = np.where(self.image.Data > high_cutoff,
            0*self.image.Data, self.image.Data)
        return None
    
    
    def make_traditional_spectrum(self):
        """
        This function follows the procedure in <SpectraExtractInterp2> of the
        Milano Matlab macros.
        """
        nrows, ncols = self.image.Data.shape
        iso = self.binning * self.slope * np.arange(ncols)
        maxshift = np.abs((iso[0]-iso[-1]) * self.points_per_pixel)
        step = 1 / self.points_per_pixel
        x0 = np.arange(nrows)
        x_spectrum = np.linspace(0, nrows, nrows*self.points_per_pixel)
        y_sum = 0 * x_spectrum
        for iii in range(ncols):
            x_shifted = x0 - iso[iii] - 1 / self.points_per_pixel
            y_sum += interpolate.UnivariateSpline(x_shifted, 
                self.image.Data[:,iii], s=0, k=1)(x_spectrum) * step
#        y_sum[:maxshift] = 0
        self.spectrum = {}
        self.spectrum_cols = []
        self.spectrum['Pixel'] = x_spectrum
        self.spectrum_cols.append('Pixel')
        if self.Counters != None:
            self.spectrum['Storage ring current / 100mA'] = \
                0*x_spectrum + float(self.Counters['srcur'])/100
            self.spectrum['Mirror current / 1e6'] = \
                0*x_spectrum + float(self.Counters['mir'])/1e6
            self.spectrum_cols.append('Storage ring current / 100mA')
            self.spectrum_cols.append('Mirror current / 1e6')            
        self.spectrum['Acquisition time']= 0 * x_spectrum + self.exposure
        self.spectrum['Electrons'] = y_sum[::-1]
        self.spectrum['Photons'] = y_sum[::-1] / self.cont_photon
        self.spectrum_cols.append('Acquisition time')
        self.spectrum_cols.append('Electrons')
        self.spectrum_cols.append('Photons')
        return None
    
    
    def make_single_photon_counting_spectrum(self):
        gs = self.SPC_gridsize
        
        LOW_TH_PX = self.SPC_low_TH * self.Motors['energy']
        HIGH_TH_PX = self.SPC_high_TH * self.Motors['energy']
        SpotLOW = self.SPC_single_TH * self.Motors['energy']
        SpotHIGH = self.SPC_double_TH * self.Motors['energy']
        
        # Rescale image from electron counts to photon energy
        self.SPimage = self.image.Data * self.ccd_params['ElectronsPerCount'] \
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
            print "No spots!!!"
            cp = np.array([[0, 0]])
            intensities = np.array([0])

        self.cp = 1. * cp

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
        
        # Add spectrum to list of counters
        self.spectrum_cols.append('SPC single events')
        self.spectrum['SPC single events'] = spectrum_single
        self.spectrum_cols.append('SPC double events')
        self.spectrum['SPC double events'] = spectrum_double
        self.spectrum_cols.append('SPC')
        self.spectrum['SPC'] = spectrum
        
        return None
        
        
    
    def save(self, outputfile='', savedatfile=True):
        """ Generate output and write into *.spec and *.dat files """
        header = self.image.GetHeader(0)
        sheader = self.image.GetStaticHeader(0)
        
        output = []
        output.append('#S %s  %s seconds, slope %f\n' % (header['run'],
            header['preset'], self.slope))
        output.append('#D %s\n' % time.strftime('%Y-%m-%d %H:%M:%S', 
            time.localtime(time.time())))
        
        # Motor names and positions
        motor_mne_lines = []
        motor_pos_lines = []
        for iii in range(len(self.motor_mne)//8):
            motor_mne_lines.append(
                '  '.join(['#O%d' % iii] + self.motor_mne[8*iii:8*(iii+1)]))
            motor_pos_lines.append(
                '  '.join(['#P%d' % iii] + self.motor_pos[8*iii:8*(iii+1)]))
        if len(self.motor_mne) % 8 != 0:
            iii = len(self.motor_mne)//8
            motor_mne_lines.append(
                '  '.join(['#O%d' % iii] + self.motor_mne[8*iii:]))
            motor_pos_lines.append(
                '  '.join(['#P%d' % iii] + self.motor_pos[8*iii:]))
        output.append('\n'.join(motor_mne_lines) + '\n')
        output.append('\n'.join(motor_pos_lines) + '\n')
        
        # Counter names and values
        if self.Counters != None:
            output.append('#C  \n')
            for cnt_mne, cnt_pos in sorted(self.Counters.items()):
                output.append('#C  %s  %s\n' % (cnt_mne, cnt_pos))

        # Image information
        output.append('#C  \n')
        output.append('#C  %s\n' % header['title'])
        output.append('#C  %s/%s\n' % (header['dir'], 
            self.image.FileName.split('/')[-1]))
        output.append('#C  Image saved  %s\n' % self.imagedate)
        output.append('#C  ROI columns  %s...%s  rows  %s...%s\n' % (
            header['col_beg'], header['col_end'], 
            header['row_beg'], header['row_end']))
        output.append('#C  Dimensions   %s x %s\n' % (
            sheader['Dim_1'], sheader['Dim_2']))
        output.append('#C  Acq time     %s seconds\n' % header['preset'])
        output.append('#C  Cnt time     %s\n' % header['count_time'])
        output.append('#C  Offset       %s\n' % header['offset'])
        output.append('#C  Scan number  %s\n' % header['scan_no'])
        output.append('#C  Point number %s\n' % header['point_no'])
        output.append('#C  \n')
        
        # Parameters when extracting the spectra
        output.append('#C  Spectrum extraction parameters\n')
        output.append('#C  Slope        %.6f\n' % self.slope)
        output.append('#C  Points per pixel %.2f\n' % self.points_per_pixel)
        output.append('#C  Binning      %d\n' % self.binning)
        output.append('#C  Lower threshold %.2f\n' % self.lower_threshold)
        output.append('#C  Upper threshold %.2f\n' % self.upper_threshold)
        output.append('#C  Mask       %dx%d\n' % (self.masksize, self.masksize))
        output.append('#C  \n')        

        # Spectrum
        output.append('#N %d\n' % len(self.spectrum_cols))
        output.append('#L  ' + '  '.join(self.spectrum_cols) + '\n')
        output.append(''.join('%s\n' % (' '.join([str(si) for si in s])) 
            for s in np.vstack(
                [self.spectrum[colname] 
                    for colname in self.spectrum_cols]).T.tolist()))
        
        output.append('\n')
        
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
            f.write(''.join(output).encode('ascii'))
        print 'Spectrum saved to \"%s\"' % (specfilename)
        
        if savedatfile:
            if not os.path.isdir(specfilename.rstrip('.spec')):
                os.mkdir(specfilename.rstrip('.spec'))
            
            #~ key = SpecFileDataSource(specfilename).getSourceInfo()['KeyList'][-1]
            #~ datfilename = '%s/S%04d_%s.dat' % (specfilename.rstrip('.spec'),
                #~ scannumber, key.split('.')[-1])
                
            datfilename = '%s/S%04d.dat' % (specfilename.rstrip('.spec'),
                scannumber)
            np.savetxt('%s' % (datfilename), dataObject.data)
            print 'Spectrum saved to \"%s\"\n' % (datfilename)
                
            if not os.path.isdir(outputfile.rstrip('.spec')):
                os.mkdir(outputfile.rstrip('.spec'))
            np.savetxt('%s' % (datfilename), np.vstack(
                [self.spectrum[colname] for colname in self.spectrum_cols]).T)
            print 'Spectrum saved to \"%s\"\n' % (datfilename)
        
        return None



def main():
    return 0

if __name__ == '__main__':
    main()

