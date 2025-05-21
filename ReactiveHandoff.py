#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2025 Ross.
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy as np
from gnuradio import gr
import threading
from xmlrpc.client import ServerProxy
import time
import random
import math

class ReactiveHandoff(gr.sync_block):
    """
    docstring for block ReactiveHandoff
    """
    def __init__(self, num_channels = 1, start_freq = 1000, chan_bw = 20000, initial_trials = 10, delay = 0.1):
        gr.sync_block.__init__(self,
            name="ReactiveHandoff",
            in_sig=[np.float32, np.float32],
            out_sig=[])
        self.num_channels = num_channels
        self.start_freq = start_freq
        self.bw = chan_bw
        self.counter = 1
        self.trials = [0]*num_channels
        self.current_channel = 1
        #Change IP and Port accordingly (same with server)
        self.xmlrpcHandoff1 = ServerProxy('http://localhost:5331')
        self.xmlrpcHandoff2 = ServerProxy('http://localhost:5335')
        self.xmlrpcHandoff3 = ServerProxy('http://localhost:5341')
        self.xmlrpcHandoff4 = ServerProxy('http://localhost:5345')
        self.xmlrpcHandoff5 = ServerProxy('http://localhost:5600')
        self.init = 0
        self.in1 = []
        self.input_energy = 0
        self.energy_per_channel = [0]*num_channels
        self.energy_in_dB = [0]*num_channels
        self.not_idle = 0
        self.set_history(1)
        self.set_relative_rate(1)
        self.delay = delay
        time.sleep(delay)
        self.total_handoffs = 0
        self.time_handoff = 0

        #Flags for interference
        self.control_value = 0
        self.interfered = 0
        self.searching = 0

        # Create a thread that runs independently
        self._stop_thread = False
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.start()

    # HANDOFF AND MONITORING
    def _worker_loop(self):
        while not self._stop_thread:
            if True:
                self.xmlrpcHandoff5.set_switch(1)
                time.sleep(self.delay)
                if self.counter == 1:
                    self.current_channel = random.randint(1, self.num_channels)
                channel = self.current_channel - 1
                current_freq = self.start_freq + self.bw*channel

                if self.interfered == 1:
                    if self.not_idle == 0:
                        end = time.time()
                        elapsed = end - start
                        self.xmlrpcHandoff5.set_switch(1)
                        print(f"\nChannel found. Elapsed Time: {elapsed}s\n")
                        self.time_handoff += elapsed
                        self.total_handoffs += 1
                        print(f"\nTotal Handoffs: {self.total_handoffs}\n")
                        
                        ave_handoff = self.time_handoff/self.total_handoffs
                        print(f"\n Average Handoff Time: {ave_handoff}\n \nTotal Time: {self.time_handoff}\n")
                        self.interfered = 0
                        self.searching = 0

                if self.init == 0:
                    self.init = 1
                    try:
                        self.xmlrpcHandoff1.set_frequency(float(current_freq))
                        self.xmlrpcHandoff2.set_frequency(float(current_freq))
                        self.xmlrpcHandoff3.set_frequency(float(current_freq))
                        self.xmlrpcHandoff4.set_frequency(float(current_freq))
                        self.xmlrpcHandoff5.set_txfreq(float(current_freq))
                    except Exception as e:
                        print(f"Error:{e}")
                    self.consume_each(len(self.in1))

                #NEXT FREQUENCY
                elif self.init == 1:
                    print(f"Sensing channel {channel + 1} at frequency {current_freq}")
                    try:
                        self.xmlrpcHandoff1.set_frequency(float(current_freq))
                        self.xmlrpcHandoff2.set_frequency(float(current_freq))
                        self.xmlrpcHandoff3.set_frequency(float(current_freq))
                        self.xmlrpcHandoff4.set_frequency(float(current_freq))
                        self.xmlrpcHandoff5.set_txfreq(float(current_freq))
                    except Exception as e:
                        print(f"Error:{e}")

                    self.init = 0
                    self.trials[channel] += 1
                    channel_energy = self.input_energy
                    current_ave_energy = channel_energy + self.energy_per_channel[channel]
                    self.energy_per_channel[channel] = current_ave_energy/self.trials[channel]
                    self.energy_in_dB[channel] = 10*math.log10(current_ave_energy/self.trials[channel])/3
                    print(f"Occupancy: {self.not_idle}")
                    print(f"TRIALS: {self.trials}")
                    print(self.energy_per_channel)
                    print(self.energy_in_dB)

                    #INTERFERENCE HANDLING
                    if self.not_idle == 1:
                        curr = self.current_channel
                        while self.current_channel == curr:
                            self.current_channel = random.randint(1, self.num_channels)
                            trials_copy = self.trials.copy()
                            maxim = trials_copy.index(max(trials_copy)) + 1
                        print(f"\n[INTERFERENCE DETECTED] Channel {channel + 1}. Searching for available channel.\n")
                        
                        if self.searching == 0:
                             start = time.time()
                             self.xmlrpcHandoff5.set_switch(0)
                        try:
                            self.xmlrpcHandoff1.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                            self.xmlrpcHandoff2.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                            self.xmlrpcHandoff3.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                            self.xmlrpcHandoff4.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                        except Exception as e:
                            print(f"Error:{e}")
                        self.counter += 1
                        self.interfered = 1
                        self.searching = 1

                self.counter += 1
                self.consume_each(len(self.in1))

            time.sleep(self.delay)

    #INPUT READING
    def work(self, input_items, output_items):
        self.in1 = input_items[0]
        in2 = self.in1.tolist()
        self.not_idle = in2[-1]
        self.input_energy = input_items[1].tolist()[-1]
        return len(input_items[0])

    def stop(self):
        self._stop_thread = True
        self.worker_thread.join()
        return True
