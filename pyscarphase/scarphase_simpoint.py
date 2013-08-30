# Copyright (c) 2011-2013 Andreas Sembrant
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#  - Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  - Neither the name of the copyright holders nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Andreas Sembrant

import argparse
import numpy as np
import scipy.spatial.distance as spd

import pyscarphase.proto.meta
import pyscarphase.proto.data

import cmd

class SimpointCmd(cmd.Cmd):


    def __init__(self, args):
        
        #
        cmd.Cmd.__init__(self)

        #
        self.parse_arguments(args)

    def parse_arguments(self, args):

        #
        parser = argparse.ArgumentParser(
            prog=' '.join(args[0:2]), 
            description='Show cool sectret stuff. Maybe where Santa sleeps.'
            )

        #
        subparsers = parser.add_subparsers(title="Find and display Simulation Points")

        #
        def add_common_args(parser):

            #
            parser.add_argument(
                "profile",
                help="Input profile."
                )

            parser.add_argument(
                "--thread", "-t",
                type=int, default=0,
                help="Threads to plot."
                )

            parser.add_argument(
                "--coverage", "-c",
                type=int, default=80,
                help="Phase coverage in precentage."
                )

        #
        def conf_find():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'find',
                help="Find simulation points")

            # 
            sub_parser.set_defaults(func=self.find_simpoints)
            
            # 
            add_common_args(sub_parser)
         
        #
        def conf_find_first():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'find-first',
                help="Find simulation points")

            # 
            sub_parser.set_defaults(func=self.find_first_simpoints)
            
            # 
            add_common_args(sub_parser)

        #
        conf_find()
        conf_find_first()

        self.args = parser.parse_args(args[2:])

    def run(self):
        self.args.func()
        
    class Phase:
        
        def __init__(self, pid):
            self.pid = pid
            self.windows = []
            self.centroid = []

    def _build_phase_data(self):
        
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)

        thread = profile.threads[self.args.thread]

        reader = pyscarphase.proto.data.DataReader(
            thread.profile.filename, 
            uuid=thread.profile.uuid
            )
        
        phases = {}
        for w in reader:
    
            #
            pid = w.phase_info.phase
               
            #
            if not pid in phases:
                phases[pid] = self.Phase(pid)
                phases[pid].centroid = \
                    np.zeros(len(w.phase_info.signature.fv_values))
    
            #
            phases[pid].centroid = \
                np.add(
                    phases[pid].centroid, 
                    w.phase_info.signature.fv_values[:]
                    )

        # Normalize centroid
        for p in phases.itervalues():
            p.centroid = np.linalg.norm(p.centroid, 1)          
            
        # Do second pass
        reader.seek(0)
        offset = 0
        for w in reader:
    
            #
            pid = w.phase_info.phase
            
            # Calc distance
            d = spd.cityblock(
                phases[pid].centroid, 
                w.phase_info.signature.fv_values[:]
                )

            #
            phases[pid].windows.append((offset, w.size, d))
            
            #
            offset += w.size
            
        # Order phases in descending length
        phases = sorted(
            phases.itervalues(), 
            key=lambda p: len(p.windows), 
            reverse=True
            )
        
        #
        return phases

    def _find_simpoints(self, wfunc):

        #
        phases = self._build_phase_data()
                  
        #
        if len(phases) == 0:
            print("Aborting, nothing to plot (ie, no windows in thread)!")
            exit()

        # 
        no_windows = reduce(lambda y, p: len(p.windows) + y, phases, 0)

        # Convert to windows
        self.args.coverage = self.args.coverage / 100.0 * no_windows

        # Counter
        coverage = 0

        #
        simpoints = []

        #
        for p in phases:

            #
            coverage += len(p.windows)
            
            # Get window
            w = wfunc(p)
          
            # <window, weight>
            simpoints.append((p.pid, w[0], w[1], len(p.windows)))

            #
            if coverage > self.args.coverage:
                break

        #
        coverage = 0
            
        #
        for pid, offset, duration, weight in simpoints:
            coverage += weight
            
        # Sort in window order
        simpoints = sorted(simpoints, key=lambda x: x[1])

        #
        _simpoints = []
        
        #
        for pid, offset, duration, weight in simpoints:
            _simpoints.append({"pid": pid, 
                               "offset" : long(offset), 
                               "duration": long(duration),
                               "weight" : weight
                               })
                               
        import json
        print json.dumps({"simpoints" : _simpoints}, indent=2)
            
    def find_simpoints(self):
        
        def select_center_window(p):
            return min(p.windows, key=lambda x: x[2])
        
        self._find_simpoints(select_center_window)
        
    def find_first_simpoints(self):
        
        def select_first_window(p):
            return p.windows[0]
        
        self._find_simpoints(select_first_window)
        

def run(args): 
    SimpointCmd(args).run();
