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

import sys, argparse

import matplotlib.cm 
import matplotlib.pyplot as plt

import pyscarphase.proto.meta
import pyscarphase.proto.data

import pyscarphase.plot.phasebar

import pyscarphase.cmd

class PlotCmd(pyscarphase.cmd.Cmd):


    def __init__(self, args):
        
        #
        pyscarphase.cmd.Cmd.__init__(self)

        #
        self.parse_arguments(args)

    def parse_arguments(self, args):

        #
        self.parser = argparse.ArgumentParser(
            prog=' '.join(args[0:2]), 
            description='Plot ...'
            )

        #
        subparsers = self.parser.add_subparsers(title="What to plot")

        def add_common_args(parser):

            #
            parser.add_argument(
                "profile",
                help="Input profile."
                )

            parser.add_argument(
                "--thread", "-t",
                type=int,
                help="Threads to plot."
                )

            parser.add_argument(
                "--counters", "-c",
                type=str,
                help="Performance counter ids."
                )  

            parser.add_argument(
               "--output-file", "-o",
                help="Output file"
                )

        def conf_plot_signatures():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'signatures',
                help="Plot signatures")

            # 
            sub_parser.set_defaults(func=self.plot_signatures)
            
            # 
            add_common_args(sub_parser)

        def conf_plot_windows():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'windows',
                help="Plot windows")

            # 
            sub_parser.set_defaults(func=self.plot_windows)
            
            # 
            add_common_args(sub_parser)

        conf_plot_signatures()
        conf_plot_windows()

        #
        self.args = self.parser.parse_args(args[2:])


    def run(self):
        self.args.func()

    def plot_phases(self):
        pass


    def plot_signatures(self):
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)

        thread = profile.threads[self.args.thread]

        reader = pyscarphase.proto.data.DataReader(thread.profile.filename, 
                                 uuid=thread.profile.uuid)

        phase_list = []
        signatures = []
        for w in reader:
            phase_list.append(w.phase_info.phase)
            signatures.append(w.phase_info.signature.fv_values[:])
       
        import numpy as np
        signatures = np.array(signatures)
        signatures = signatures.transpose()

       
        #
        if len(phase_list) == 0:
            print("Aborting, nothing to plot (ie, no windows in thread)!")
            exit()

        def _plot():

            # Create axis
            pbar_ax = plt.axes([0.1, 0.9, 0.8, 0.025])
            plot_ax = plt.axes([0.1, 0.1, 0.8, 0.75])

            pyscarphase.plot.phasebar.plot(pbar_ax, plot_ax, phase_list)
    
            # Plot counter values
            plot_ax.imshow(signatures, 
                  aspect='auto', 
                  interpolation='nearest', 
                  cmap=matplotlib.cm.binary)


            # 
            if self.args.output_file:
                plt.savefig(self.args.output_file)
            else:
                plt.show()

        #
        _plot()


    def plot_windows(self):

        #
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)

        #
        thread = profile.threads[self.args.thread]

        #
        reader = pyscarphase.proto.data.DataReader(
            thread.profile.filename, 
            uuid=thread.profile.uuid
            )

        #
        counters = [ int(c) for c in self.args.counters.split() ]

        #
        phase_list = []

        #
        samples = {}
        for c in counters:
            samples[c] = []

        def retrieve_data():

            import util.counter
            import util.demultiplexer

            dm = util.demultiplexer.Demultiplexer(reader)

            for w in dm.read():
                phase_list.append(w.phase)
            
                for c in counters:
                    v = util.counter.exec_func(
                        c, profile.performance_counters, w
                        )

                    samples[c].append(v)

        #
        retrieve_data()
            
        #
        if len(phase_list) == 0:
            print("Aborting, nothing to plot (ie, no windows in thread)!")
            exit()

        def _plot():

            # Create axis
            pbar_ax = plt.axes([0.1, 0.9, 0.8, 0.025])
            plot_ax = plt.axes([0.1, 0.1, 0.8, 0.75])

            pyscarphase.plot.phasebar.plot(pbar_ax, plot_ax, phase_list)
    
            # Plot counter values
            for c in counters:
                plot_ax.plot(samples[c], label=profile.performance_counters[c].name)

            plot_ax.legend()

            # 
            if self.args.output_file:
                plt.savefig(self.args.output_file)
            else:
                plt.show()

        #
        _plot()


def run(args):
    PlotCmd(args).run()


