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

import sys, collections

class Dispatcher:

    CmdData = collections.namedtuple('CmdData', [ 'func', 'help' ])

    def __init__(self, prog = sys.argv[0]):
        self.prog = prog

        import scarphase_dump
        import scarphase_plot
        import scarphase_profile
        import scarphase_show
        import scarphase_refine
        import scarphase_simpoint

        self.subcommands = {
            "show"    : Dispatcher.CmdData(
                func=scarphase_show.run, 
                help="Show stuff"
                ),

            "dump"    : Dispatcher.CmdData(
                func=scarphase_dump.run, 
                help="Dump stuff"
                ),

            "plot"    : Dispatcher.CmdData(
                func=scarphase_plot.run, 
                help="Plot stuff"
                ),

            "profile" : Dispatcher.CmdData(
                func=scarphase_profile.run, 
                help="Profile stuff"
                ),

            "refine"  : Dispatcher.CmdData(
                func=scarphase_refine.run, 
                help="Refine data"
                ),

            "simpoint"  : Dispatcher.CmdData(
                func=scarphase_simpoint.run, 
                help="Find simpoints"
                ),

            }


    def dispatch(self, args):
        '''Dispatch sub-command or print help information.'''

        if len(args) <= 1:
            self.__print_help([])
            return

        command = args[1]
        if command in self.subcommands:
            self.subcommands[command].func(args)
            return

        if command == "help":
            if len(args) < 3:
                self.__print_help([])
            else:
                self.subcommands[args[2]].func([ args[0] ] + args[2:] + [ '-h' ])

            return 
        
        self.__print_help([])


    def __print_usage(self):
        '''Print usage.'''

        print("usage: %s <command> [<args>]" % (self.prog))


    def __print_help(self, args):
        '''Print help'''

        def print_default_help():
            self.__print_usage()
            print("")

            print("Commands:")
            for k, v in self.subcommands.iteritems():
                if v == None:
                    continue
                
                # Align command
                cmd = k + " " * (10-len(k))

                print("   %s   %s" % (cmd, v.help))

            print("")
            print("See '%s help <command>' for more information." % (self.prog))

        if len(args) == 0:
            print_default_help()


def run():
    Dispatcher().dispatch(sys.argv)

