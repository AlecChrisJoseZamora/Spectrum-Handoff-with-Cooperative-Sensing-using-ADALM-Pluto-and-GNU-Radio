#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2025 Ross.
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy as np
from gnuradio import gr
import threading
import time

class TDD(gr.sync_block):
    """
    docstring for block TDD
    """
    def __init__(self, order = 10, duration1 = 1, duration2 = 0.5):
        gr.sync_block.__init__(self,
            name="TDD",
            in_sig=[],
            out_sig=[np.complex64])
        self.duration1 = duration1
        self.duration2 = duration2
        if order == 10:
            self.first = 1
            self.next = 0
        else:
            self.first = 0
            self.next = 1
        self.multiplier = 0
        
        # Create a thread that runs independently
        self._stop_thread = False
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.start()

    def _worker_loop(self):
        while not self._stop_thread:
            # PROCESS
            self.multiplier = self.first
            time.sleep(self.duration1)
            self.multiplier = self.next
            time.sleep(self.duration2)
            

    def work(self, input_items, output_items):
        output_items[0][:] = self.multiplier
        return len(output_items[0])

    def stop(self):
        self._stop_thread = True
        self.worker_thread.join()
        return True
