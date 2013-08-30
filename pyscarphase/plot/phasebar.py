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

from matplotlib.ticker import NullFormatter

import pyscarphase.util.runlength
import pyscarphase.plot.color

def plot(ax, plot_ax, phase_list):

    # All patterns
    HATCHES = [ None, '//', '\\\\' ]

    # Remove labels
    ax.xaxis.set_major_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(NullFormatter())

    # Rank phases 
    def rank_phases(phase_list):
        phase_map = {}
        for pid in phase_list:
            phase_map[pid] = phase_map.get(pid, 0) + 1

        return sorted(phase_map.iteritems(), 
                      key=lambda x: x[1], 
                      reverse=True)



    # Sort phases depending on rank
    sorted_phase_map = rank_phases(phase_list)

    # Create colors
    def create_color_map():
        
        phase_color_map = {}
    
        i = 0
        for h in HATCHES:
            for c in xrange(len(pyscarphase.plot.color.COLORS)):
                
                if i >= len(sorted_phase_map):
                    return phase_color_map
                
                phase_color_map[sorted_phase_map[i][0]] = (
                    pyscarphase.plot.color.COLORS[c], 'k', h
                    )
                
                i += 1
                
        return phase_color_map
    

    phase_color_map = create_color_map()

    # Convert to only phase changes
    compressed_phase_list = pyscarphase.util.runlength.encode(phase_list)

    # Draw phase bar
    i = 0
    for pid, length in compressed_phase_list:
        if pid in phase_color_map:
            ax.axvspan(i, 
                       i + length, 
                       facecolor=phase_color_map[pid][0], 
                       edgecolor=phase_color_map[pid][1],
                       hatch=phase_color_map[pid][2], 
                       lw=0.5) 
            
            ax.text(i + length / 2, 
                    0.5, 
                    '%i' % pid,
                    size='xx-small',
                    horizontalalignment='center',
                    verticalalignment='center')

        i += length


    # Connect bar so it follows zoom in/out in parent
    class Connector:
        
        def __init__(self, ax):
            self.ax = ax

        def __call__(self, ax):
            self.ax.set_xlim(ax.get_xlim())
    
    plot_ax.callbacks.connect('xlim_changed', func=Connector(ax))

