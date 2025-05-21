#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Alec.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class EnergyDetector(gr.sync_block):
    """
    docstring for block EnergyDetector
    """
    def __init__(self, Ns=100):
        gr.sync_block.__init__(self,
            name="EnergyDetector",
            in_sig=[(np.float32, Ns)],
            out_sig=[(np.float32, Ns)])
        self.ns = Ns


    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        # <+signal processing here+>
        for vectorIndex in range(len(input_items[0])):
            samp = input_items[0][vectorIndex]
            squares = np.square(samp)
            energy = np.sum(squares)
            ave_energy = energy/self.ns
            #output assignment
            for sampleIndex in range(len(output_items[0][vectorIndex])):
                output_items[0][vectorIndex][sampleIndex]= ave_energy
        return len(output_items[0])
