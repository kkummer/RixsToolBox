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

from __future__ import division, print_function

__author__ = "K. Kummer - ESRF ID32"
__contact__ = "kurt.kummer@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
___doc__ = """
    ...
"""

import numpy as np


class RtbMath(object):
    def gaussian_kernel_1d(self, sigma, order, radius):
        """
        Computes a 1D Gaussian convolution kernel.
        """
        if order < 0:
            raise ValueError("order must be non-negative")
        p = np.polynomial.Polynomial([0, 0, -0.5 / (sigma * sigma)])
        x = np.arange(-radius, radius + 1)
        phi_x = np.exp(p(x), dtype=np.double)
        phi_x /= phi_x.sum()
        if order > 0:
            q = np.polynomial.Polynomial([1])
            p_deriv = p.deriv()
            for _ in range(order):
                # f(x) = q(x) * phi(x) = q(x) * exp(p(x))
                # f'(x) = (q'(x) + q(x) * p'(x)) * phi(x)
                q = q.deriv() + q * p_deriv
            phi_x *= q(x)
        return phi_x

    def gaussian_filter(self, y, sigma, order=0, truncate=4.0):
        """
        Applies a Gaussian filter to a 1D input array.
        Adapted from scipy.ndimage
        """
        if abs(sigma) < 1e-15:
            retval = y
        else:
            sd = float(sigma)
            lw = int(truncate * sd + 0.5)
            weights = self.gaussian_kernel_1d(sigma, order, lw)[::-1]
            ytemp = np.hstack(
                (len(weights) // len(y) + 1) * [y, y[::-1], y, y[::-1]]
                + [y]
                + (len(weights) // len(y) + 1) * [y[::-1], y, y[::-1], y]
            )
            retval = np.correlate(ytemp, weights, mode="same")
            retval = retval[
                (len(weights) // len(y) + 1) * 4 * len(y) : (
                    (len(weights) // len(y) + 1) * 4 + 1
                )
                * len(y)
            ]
            retval[: len(weights) // 2] = y[: len(weights) // 2]
            retval[-len(weights) // 2 :] = y[-len(weights) // 2 :]
        return retval

    def gaussian(self, x, x0, amp, fwhm):
        return amp * np.exp(-((x - x0) ** 2) / 2 / (fwhm / 2.3548) ** 2)

    def minimize(
        self,
        func,
        x0,
        args=(),
        xatol=1e-4,
        fatol=1e-4,
        maxiter=None,
        maxfev=None,
        disp=1,
    ):
        """
        Minimize a function using the downhill simplex algorithm.
        Adapted from scipy.optimize
        """

        def wrap_function(function, args):
            ncalls = [0]
            if function is None:
                return ncalls, None

            def function_wrapper(*wrapper_args):
                ncalls[0] += 1
                return function(*(wrapper_args + args))

            return ncalls, function_wrapper

        maxfun = maxfev
        fcalls, func = wrap_function(func, args)

        rho = 1
        chi = 2
        psi = 0.5
        sigma = 0.5

        nonzdelt = 0.05
        zdelt = 0.00025

        x0 = np.asarray(x0, dtype=float).flatten()

        N = len(x0)

        sim = np.zeros((N + 1, N), dtype=x0.dtype)
        sim[0] = x0
        for k in range(N):
            y = np.array(x0, copy=True)
            if y[k] != 0:
                y[k] = (1 + nonzdelt) * y[k]
            else:
                y[k] = zdelt
            sim[k + 1] = y

        # If neither are set, then set both to default
        if maxiter is None and maxfun is None:
            maxiter = N * 200
            maxfun = N * 200
        elif maxiter is None:
            # Convert remaining Nones, to np.inf, unless the other is np.inf, in
            # which case use the default to avoid unbounded iteration
            if maxfun == np.inf:
                maxiter = N * 200
            else:
                maxiter = np.inf
        elif maxfun is None:
            if maxiter == np.inf:
                maxfun = N * 200
            else:
                maxfun = np.inf

        one2np1 = list(range(1, N + 1))
        fsim = np.zeros((N + 1,), float)

        for k in range(N + 1):
            fsim[k] = func(sim[k])

        ind = np.argsort(fsim)
        fsim = np.take(fsim, ind, 0)
        # sort so sim[0,:] has the lowest function value
        sim = np.take(sim, ind, 0)

        iterations = 1

        while fcalls[0] < maxfun and iterations < maxiter:
            if (
                np.max(np.ravel(np.abs(sim[1:] - sim[0]))) <= xatol
                and np.max(np.abs(fsim[0] - fsim[1:])) <= fatol
            ):
                break

            xbar = np.add.reduce(sim[:-1], 0) / N
            xr = (1 + rho) * xbar - rho * sim[-1]
            fxr = func(xr)
            doshrink = 0

            if fxr < fsim[0]:
                xe = (1 + rho * chi) * xbar - rho * chi * sim[-1]
                fxe = func(xe)

                if fxe < fxr:
                    sim[-1] = xe
                    fsim[-1] = fxe
                else:
                    sim[-1] = xr
                    fsim[-1] = fxr
            else:  # fsim[0] <= fxr
                if fxr < fsim[-2]:
                    sim[-1] = xr
                    fsim[-1] = fxr
                else:  # fxr >= fsim[-2]
                    # Perform contraction
                    if fxr < fsim[-1]:
                        xc = (1 + psi * rho) * xbar - psi * rho * sim[-1]
                        fxc = func(xc)

                        if fxc <= fxr:
                            sim[-1] = xc
                            fsim[-1] = fxc
                        else:
                            doshrink = 1
                    else:
                        # Perform an inside contraction
                        xcc = (1 - psi) * xbar + psi * sim[-1]
                        fxcc = func(xcc)

                        if fxcc < fsim[-1]:
                            sim[-1] = xcc
                            fsim[-1] = fxcc
                        else:
                            doshrink = 1

                    if doshrink:
                        for j in one2np1:
                            sim[j] = sim[0] + sigma * (sim[j] - sim[0])
                            fsim[j] = func(sim[j])

            ind = np.argsort(fsim)
            sim = np.take(sim, ind, 0)
            fsim = np.take(fsim, ind, 0)
            iterations += 1

        x = sim[0]
        fval = np.min(fsim)
        warnflag = 0

        if fcalls[0] >= maxfun:
            warnflag = 1
            msg = "Maximum number of function evaluations has been exceeded."
            if disp:
                print("Warning: " + msg)
        elif iterations >= maxiter:
            warnflag = 2
            msg = "Maximum number of iterations has been exceeded."
            if disp:
                print("Warning: " + msg)
        else:
            msg = "Optimization terminated successfully."
            if disp:
                print(msg)
                print("         Current function value: %f" % fval)
                print("         Iterations: %d" % iterations)
                print("         Function evaluations: %d" % fcalls[0])

        result = dict(
            fun=fval,
            nit=iterations,
            nfev=fcalls[0],
            status=warnflag,
            success=(warnflag == 0),
            message=msg,
            x=x,
            final_simplex=(sim, fsim),
        )

        return x, result

    def curve_fit(self, theory, x, y, p0=(1, 1, 1)):
        """
        Covinience function for curve fitting.
        """

        def func2minimize(p0, theory, data):
            return ((data[:, 1] - theory(data[:, 0], *p0)) ** 2).sum()

        popt, msg = self.minimize(
            func2minimize, x0=p0, args=(theory, np.vstack([x, y]).T), disp=False
        )
        return popt, msg
    
    def quadratic_minimum_2d(self, Z, x, y, window=None):
        Z = np.asarray(Z, dtype=float)
        if window is None:
            window = max(Z.shape)
        
        # light smoothing only for locating the minimum region
        Zs = Z.copy()
        for _ in range(2):
            Zs[1:-1, 1:-1] = (
                Zs[1:-1, 1:-1]
                + Zs[:-2, 1:-1] + Zs[2:, 1:-1]
                + Zs[1:-1, :-2] + Zs[1:-1, 2:]
            ) / 5.0
    
        i0, j0 = np.unravel_index(np.nanargmin(Zs), Zs.shape)
    
        i1 = max(0, i0 - window)
        i2 = min(Z.shape[0], i0 + window + 1)
        j1 = max(0, j0 - window)
        j2 = min(Z.shape[1], j0 + window + 1)
    
        yy, xx = np.meshgrid(y[i1:i2], x[j1:j2], indexing="ij")
        zz = Z[i1:i2, j1:j2]
    
        m = np.isfinite(zz)
    
        # fit z = a*x² + b*y² + c*x*y + d*x + e*y + f
        A = np.column_stack([
            xx[m]**2,
            yy[m]**2,
            xx[m]*yy[m],
            xx[m],
            yy[m],
            np.ones(m.sum()),
        ])
    
        coeff, *_ = np.linalg.lstsq(A, zz[m], rcond=None)
        a, b, c, d, e, f = coeff
    
        # solve gradient = 0:
        # 2a x + c y + d = 0
        # c x + 2b y + e = 0
        H = np.array([[2*a, c], [c, 2*b]])
        g = np.array([-d, -e])
    
        x_min, y_min = np.linalg.solve(H, g)
    
        return x_min, y_min, coeff
        
    
    
    
    def interpolate_on_grid(
        self, qvals, xvals, yvals, grid, method="nearest", fill_value=None
    ):
        """
        Interpolate one-dimensional irregular data on a regular, two-dimensional
        grid. Mimics the functionality of scipy.interpolate.griddata.
        """

        gridx, gridy = grid
        qvals = np.array(qvals)

        gridz = np.vstack(
            [
                np.interp(
                    gridx[:, 0], xvals[i], yvals[i], left=fill_value, right=fill_value
                )
                for i in range(len(qvals))
            ]
        ).T
        if method == "nearest":
            gridz = np.vstack(
                [gridz[:, np.argmin(np.abs(qvals - q))] for q in gridy[0, :]]
            ).T
        else:
            idx = np.argsort(qvals)
            qvals = qvals[idx]
            gridz = gridz[:, idx]
            gridz = np.vstack(
                [
                    np.interp(
                        gridy[0, :],
                        qvals,
                        gridz[i, :],
                        left=fill_value,
                        right=fill_value,
                    )
                    for i in range(len(gridz[:, 0]))
                ]
            )
        return gridz

    def normalize(self, y):
        """
        Normalizes spectrum to values between zero and one.
        """
        ymax, ymin = y.max(), y.min()
        return (y - ymin) / (ymax - ymin)

    def calculateShiftsFFT(self, xy, portion=0.95):
        x0, y0 = xy[:, 0], xy[:, 1]
        # y0 = self.normalize(y0)

        fft0 = np.fft.fft(y0)
        x = 1 * x0

        shifts = []

        for y in xy[:, 1:].T:
            ffty = np.fft.fft(y)
            shiftTmp = np.fft.ifft(fft0 * ffty.conjugate()).real
            shiftPhase = np.zeros(shiftTmp.shape, dtype=shiftTmp.dtype)
            m = shiftTmp.size // 2
            shiftPhase[m:] = shiftTmp[:-m]
            shiftPhase[:m] = shiftTmp[-m:]
            # Normalize shiftPhase to standardize thresholding
            shiftPhase = self.normalize(shiftPhase)

            # Thresholding
            xShiftMax = shiftPhase.argmax()
            left, right = xShiftMax, xShiftMax
            threshold = portion * shiftPhase.max()
            while (shiftPhase[left] > threshold) & (shiftPhase[right] > threshold):
                left -= 1
                right += 1
            idx = np.arange(left, right + 1, 1, dtype=int)
            # The shift is determined by center-of-mass around shiftMax
            shiftTmp = (shiftPhase[idx] * idx / shiftPhase[idx].sum()).sum()
            shift = (shiftTmp - m) * (x[1] - x[0])

            shifts.append(shift)
        return shifts

    def EdgeDetector1D(self, spectrum, blur=0, highThreshold=0.9, lowThreshold=0.3):
        # Convert to float to prevent clipping values
        spectrum = np.array(spectrum, dtype=float)

        if blur:
            x = np.linspace(0, len(spectrum) - 1, len(spectrum))
            x -= (len(spectrum) - 1) / 2
            gaussian = np.exp(-(x**2 / 2 / (blur / 2.3548) ** 2))
            scaling = spectrum.sum()
            spectrum = np.convolve(spectrum, gaussian, mode="same")
            spectrum *= scaling / spectrum.sum()

        grad = -1 * np.gradient(spectrum)
        grad = grad * (grad >= 0)
        grad /= grad.max()

        # Non-maximum suppression
        gradSup = grad.copy()
        for iii in range(1, len(spectrum) - 1):
            if grad[iii] <= grad[iii - 1] or grad[iii] <= grad[iii + 1]:
                gradSup[iii] = 0

        # Double threshold
        strongEdges = gradSup > highThreshold

        # Strong has value 2, weak has value 1
        thresholdedEdges = np.array(strongEdges, dtype=np.uint8)
        thresholdedEdges += gradSup > lowThreshold

        return thresholdedEdges


if __name__ == "__main__":
    try:
        import matplotlib.pyplot as plt

        PLOT = True
    except ImportError:
        print("Failed to import matplotlib. Skip plotting.")
        PLOT = False

    a = RtbMath()
    x = np.linspace(-1, 1, 101)
    y = 3 * (np.random.random(len(x)) - 0.5) + a.gaussian(x, 0, 25, 0.2)
    ys = a.gaussian_filter(y, 5)

    def func2minimize(p0, theory, data):
        return ((data[:, 1] - theory(data[:, 0], *p0)) ** 2).sum()

    popt, msg = a.minimize(
        func2minimize, x0=[1, 1, 1], args=(a.gaussian, np.vstack([x, y]).T), disp=True
    )

    if PLOT:
        plt.figure().add_subplot(111)
        plt.errorbar(x, y, yerr=3, marker=".", ls="none", label="Raw data")
        plt.plot(x, ys, label="Smoothed")
        plt.plot(x, a.gaussian(x, *popt), label="fit\n(%.3f, %.3f, %.3f)" % tuple(popt))
        plt.legend()

        plt.show()
