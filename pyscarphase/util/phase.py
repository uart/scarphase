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

class Instance:

    def __init__(self, start):
        self.start = start
        self.windows = []


class Phase:

    def __init__(self, pid):
        self.pid = pid
        self.instances = []      
        

def load_phase_hierarchy(reader):
    '''
    phase -> instance -> window
                      -> window
                      -> window

          -> instance -> window
                      -> window

    ...

    '''
    
    #
    phase_list = []

    #
    phase_map = {}

    # Last phase
    _pid = -1

    #
    reader.seek(0)

    #
    for i, w in enumerate(reader):

        # Current phase
        pid = w.phase_info.phase

        # If first time we see this phase
        if not pid in phase_map:
            phase_map[pid] = Phase(pid)
            phase_map[pid].instances.append(Instance(i))
            phase_map[pid].instances[-1].windows.append(None)

        else:

            # If phase change
            if _pid != pid: 
                phase_map[pid].instances.append(Instance(i))

            phase_map[pid].instances[-1].windows.append(None)

        #
        phase_list.append(pid)

        #
        _pid = pid

    #
    return (phase_list, phase_map)
