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
import math

class SpecHandoff(gr.sync_block):
    """
    docstring for block SpecHandoff
    """
    def __init__(self, num_channels = 1, start_freq = 1000, chan_bw = 20000, initial_trials = 10, delay = 0.1):
        gr.sync_block.__init__(self,
            name="SpecHandoff",
            in_sig=[np.float32,np.float32],
            out_sig=[])
        self.num_channels = num_channels
        self.start_freq = start_freq
        self.bw = chan_bw
        self.prob = [0]*num_channels
        self.tri_per_chan = [0]*num_channels
        self.counter = 1
        self.trials = initial_trials
        self.current_channel = 1
        # Change Port Number and IP address for the clients accordingly
        # corresp. GNU flowgraph must have same port and IP as server
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
        self.prob_copy = [0]
        self.set_relative_rate(1)
        self.delay = delay
        time.sleep(delay)
        self.total_handoffs = 0
        self.time_handoff = 0
        self.maxim = 1
        self.maxim_copy = 1
        
        #Flags for interference
        self.control_value = 0
        self.interfered = 0
        self.searching = 0

        # Create a thread that runs independently
        self._stop_thread = False
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.start()

    #PROBABILITY MATRIX UPDATING
    def update_prob(self, channel, not_idle):
        x = 0
        self.tri_per_chan[channel] += 1
        num_trials = self.tri_per_chan[channel]
        print(f"Num Trials: {num_trials}")
        num = self.prob[channel] * (num_trials-1)
        occupied = round(not_idle, 2)
        print(f"Recieved Value: {occupied}")
        channel_energy = self.input_energy
        current_ave_energy = channel_energy + self.energy_per_channel[channel]
        self.energy_per_channel[channel] = current_ave_energy/self.tri_per_chan[channel]
        self.energy_in_dB[channel] = 10*math.log10(current_ave_energy/self.tri_per_chan[channel])/3
        print(f"Average: {current_ave_energy}, Read: {channel_energy}")
        if occupied == 1:
            self.prob[channel] = num/num_trials
            print("\n")
            print(f"PROBABILITY: {self.prob}")
            print(f"ENERGY PER CHANNEL: {self.energy_per_channel}")
            print(f"IN DECIBELS: {self.energy_in_dB}")
            print("\n")
        elif occupied != 1:
            self.prob[channel] = (num+1)/num_trials
            print("\n")
            print(f"PROBABILITY: {self.prob}")
            print(f"ENERGY PER CHANNEL: {self.energy_per_channel}")
            print(f"IN DECIBELS: {self.energy_in_dB}")
            print("\n")

    # HANDOFF AND MONITORING PROCESS
    def _worker_loop(self):
        while not self._stop_thread:
            
            time.sleep(self.delay)
            if self.counter < self.trials + 1:
                if self.current_channel != (self.num_channels + 1):
                    channel = self.current_channel - 1
                    current_freq = self.start_freq + self.bw*channel
                    if self.init == 0:
                        self.init = 1
                        try:
                            self.xmlrpcHandoff1.set_frequency(float(current_freq))
                            self.xmlrpcHandoff2.set_frequency(float(current_freq))
                            self.xmlrpcHandoff3.set_frequency(float(current_freq))
                            self.xmlrpcHandoff4.set_frequency(float(current_freq))
                        except Exception as e:
                            print(f"Error:{e}")

                    #NEXT FREQUENCY
                    elif self.init == 1:
                        print(f"\n[INITIAL] Sensing channel {channel+1} at frequency  {current_freq}. \n")
                        try:
                            self.xmlrpcHandoff1.set_frequency(float(current_freq+self.bw))
                            self.xmlrpcHandoff2.set_frequency(float(current_freq+self.bw))
                            self.xmlrpcHandoff3.set_frequency(float(current_freq+self.bw))
                            self.xmlrpcHandoff4.set_frequency(float(current_freq+self.bw))
                        except Exception as e:
                            print(f"Error:{e}")
                        self.update_prob(channel, self.not_idle)
                        self.current_channel += 1
                        self.init = 0 
                    self.consume_each(len(self.in1))

                else:
                    self.counter += 1
                    self.current_channel = 1
                    print(f"Initial Sensing {self.counter - 1}: DONE")

            elif self.counter > self.trials:
                if self.counter == self.trials + 1:
                    print("\n----------------------")
                    print("INITIAL TRIALS DONE")
                    print("----------------------\n")
                    self.xmlrpcHandoff5.set_switch(1)
                    self.xmlrpcHandoff4.set_switch(1)
                    self.current_channel = self.maxim + 1
                    print(f"MATRIX: {self.prob}\n")
                channel = self.current_channel - 1
                current_freq = self.start_freq + self.bw*channel

                if self.interfered == 1:
                    if self.not_idle == 0:
                        end = time.time()
                        elapsed = end - start
                        self.xmlrpcHandoff5.set_switch(1)
                        self.xmlrpcHandoff4.set_switch(1)
                        print(f"\nChannel found. Elapsed Time: {elapsed}s\n")
                        self.time_handoff += elapsed
                        self.total_handoffs += 1
                        print(f"\n Total Handoffs: {self.total_handoffs}\n")
                        ave_handoff = self.time_handoff/self.total_handoffs
                        print(f"\nAverage Handoff Time: {ave_handoff}\n \nTotal Time: {self.time_handoff}\n")
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

                    print(f"\nTRIALS PER CHANNEL: {self.tri_per_chan}\n")
                    a = self.update_prob(channel, self.not_idle)
                    self.init = 0
                    if self.not_idle == 1:
                        holder = self.prob[channel]
                        self.prob[channel] = -1
                        self.current_channel = self.prob.index(max(self.prob)) + 1
                        print(f"\n[INTERFERENCE DETECTED] Channel {channel + 1}. Searching for available channel.\n")
                        self.prob[channel] = holder
                        if self.searching == 0:
                             start = time.time()
                             self.xmlrpcHandoff5.set_switch(0)
                             self.xmlrpcHandoff4.set_switch(0)
                        try:
                            self.xmlrpcHandoff1.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                            self.xmlrpcHandoff2.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                            self.xmlrpcHandoff3.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                            self.xmlrpcHandoff4.set_frequency(float(self.start_freq+self.bw*(self.current_channel-1)))
                            self.xmlrpcHandoff5.set_txfreq(float(self.start_freq+self.bw*(self.current_channel-1)))
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
        self.maxim  = self.prob.index(max(self.prob))
        self.input_energy = input_items[1].tolist()[-1]
        return len(input_items[0])

    def stop(self):
        self._stop_thread = True
        self.worker_thread.join()
        return True
