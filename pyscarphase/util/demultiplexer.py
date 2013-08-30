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

import numpy as np

class Demultiplexer:


    class Type:
        (WINDOW, INSTANCE, PHASE, PROGRAM) = range(0, 4)

    def __init__(self, reader):

        # Load all phases
        import pyscarphase.util.phase
        self.phase_list, self.phase_map = \
            pyscarphase.util.phase.load_phase_hierarchy(reader)

        class RunningAverage:

            def __init__(self):
                self.sum = 0
                self.count = 0

            def add(self, x):
                self.sum += x
                self.count += 1
                return self

        self.average = {}

        # Populate phases
        for pid, phase in self.phase_map.iteritems():
            #
            phase.average = {}

            # Add instance
            for instance in phase.instances:
                #
                instance.average = {}

                # Add samples
                for i in xrange(len(instance.windows)):
                    #
                    value = {}

                    #
                    for s in reader.get(instance.start + i).perf_samples:
                        value[s.cid] = s.value
                        
                        instance.average[s.cid] = \
                            instance.average.get(s.cid, RunningAverage()).add(s.value)

                        phase.average[s.cid] = \
                            phase.average.get(s.cid, RunningAverage()).add(s.value)

                        self.average[s.cid] = \
                            self.average.get(s.cid, RunningAverage()).add(s.value)

                    #
                    instance.windows[i] = value

                for cid, average in instance.average.iteritems():
                    instance.average[cid] = average.sum / average.count

            for cid, average in phase.average.iteritems():
                phase.average[cid] = average.sum / average.count

        for cid, average in self.average.iteritems():
            self.average[cid] = average.sum / average.count
            

    def demultiplex(self, index, counter, level=Type.INSTANCE):
        '''
        Demultiplex counter.

        Searches for best approximation or sample in:

        Window > Phase Instance > Phase > Program

        '''

        phase = self.phase_map[self.phase_list[index]]

        def _get_instance():
            '''Get phase instance'''

            for instance in phase.instances:
                if index >= instance.start and \
                   index <  instance.start + len(instance.windows):
                    return instance

            raise KeyError

        instance = _get_instance()

        # Check window
        widx = index - instance.start
        if level <= Demultiplexer.Type.WINDOW and \
                counter in instance.windows[widx]:
            return (instance.windows[widx][counter], Demultiplexer.Type.WINDOW)
        
        # Check instance
        if level <= Demultiplexer.Type.INSTANCE and \
                counter in instance.average:
            return (instance.average[counter], Demultiplexer.Type.INSTANCE)

        # Check phase
        if level <= Demultiplexer.Type.PHASE and \
                counter in phase.average:
            return (phase.average[counter], Demultiplexer.Type.PHASE)

        # Check program 
        if counter in self.average:
            return (self.average[counter], Demultiplexer.Type.PROGRAM)

        # Counter was never sampled, raise error

        raise KeyError              


    def read(self):
        
        class Window:

            def __init__(self, demultiplexer, index, phase):
                self.demultiplexer = demultiplexer
                self.index = index
                self.phase = phase

            def value(self, counter):
                return self.demultiplexer.demultiplex(self.index, counter)
        
        for i, pid in enumerate(self.phase_list):
            yield Window(self, i, pid)

