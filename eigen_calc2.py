#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Alec.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr
from numpy import linalg as LA
from TracyWidom import TracyWidom

class eigen_calc2(gr.sync_block):
    """
    docstring for block maxHold
    """
    def __init__(self, smoothing=16, Ns=100, threshold=60):
        gr.sync_block.__init__(self,
            name="eigen_calc2",
            in_sig=[(np.float32, Ns)],
            out_sig=[(np.float32, Ns),(np.float32, Ns)])
        self.ns = Ns
        self.smoothing = smoothing
        self.thresh = threshold


    def work(self, input_items, output_items):
        #processing functions
        def autocorr2(x,smoothing):
            corr=np.array([])
            for lag in range(smoothing):
                if (lag==0):
                    corr=np.append(corr,np.sum(x*x))
                else:
                    y=np.zeros_like(x)
                    y[lag:]=x[:-lag]
                    corr=np.append(corr,np.sum(x*y))
            return corr
            
        def symm_toeplitz_mat(arr1D):
            ID = np.arange(arr1D.size)
            return arr1D[np.abs(ID - ID[:,None])]

        #threshold calculation
        '''
        a4 = ((self.ns-1)**(1/2)+self.smoothing**(1/2))**2
        a5 = ((self.ns-1)**(1/2)+self.smoothing**(1/2))*((self.ns-1)**(-1/2)+self.smoothing**(-1/2))**(1/3)
        tw1=TracyWidom(beta=1)
        thresh = (a5*tw1.cdfinv(1-self.pf)+a4)/self.ns
        '''

        for vectorIndex in range(len(input_items[0])):
            samp = input_items[0][vectorIndex]
            aucorr=autocorr2(samp,self.smoothing)
            cov_mat = symm_toeplitz_mat(aucorr)
            eig = LA.eigvals(cov_mat)
            eig.sort()
            max=eig[np.size(eig,0)-1]
            min=eig[0]
            eig_sum=0
            for i in range(np.size(eig,0)-1):
                eig_sum+=eig[i]
            ave=eig_sum/(np.size(eig,0)-1)
            for sampleIndex in range(len(input_items[0][vectorIndex])):
                #output_items[0][vectorIndex][sampleIndex] = max
                #output_items[0][vectorIndex][sampleIndex] = (max>(ave*thresh))+1
                output_items[0][vectorIndex][sampleIndex] = max
                output_items[1][vectorIndex][sampleIndex] = min #ave

        '''
        for vectorIndex in range(len(input_items[0])):
            #max = np.max(input_items[0][vectorIndex])
            num_vects = len(input_items[0])
            for sampleIndex in range(len(input_items[0][vectorIndex])):
                #output_items[0][vectorIndex][sampleIndex] = max
                output_items[0][vectorIndex][sampleIndex] = num_vects
        '''
        return len(output_items[0])
