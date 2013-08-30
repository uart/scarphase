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

import cmd

class ProfileCmd(cmd.Cmd):

    def __init__(self, args):
        
        #
        cmd.Cmd.__init__(self)

        #
        self.parse_arguments(args)

    def parse_arguments(self, args):

        #
        parser = argparse.ArgumentParser(
            prog=' '.join(args[0:2]),
            description='Profile applications.'
            )

        def add_args(parser):
            '''Add common arguments to all "dump" sub commands.'''

            parser.add_argument(
                "profile",
                help="Output profile."
                )

            parser.add_argument(
                "--scarphase-conf", "-s",
                help="ScarPhase configuration file"
                )

            parser.add_argument(
                "--counter-conf", "-c",
                help="Performance counter configuration file"
                )

            parser.add_argument(
                "--counter-limit", "-l",
                type=int,
                help="Max number of active counters"
                )

            parser.add_argument("cmd", 
                nargs=argparse.REMAINDER,
                help="-- cmd"
            )
 
        add_args(parser)
        self.args = parser.parse_args(args[2:])

    def run(self):
        self.profile()

    def profile(self):

        # Update path to work when not installed
        import os, os.path
        #os.environ['PATH'] = os.getcwd() + '/bin/' + ':' + os.environ['PATH']

        bin_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 
            '../bin/'
            )
        
        os.environ['PATH'] = bin_path + ':' + os.environ['PATH']

        # Call C++ scarphase-profile
        import subprocess
        subprocess.call(['scarphase-profile',
            '-s', self.args.scarphase_conf, 
            '-c', self.args.counter_conf, '-l', str(self.args.counter_limit),
            '-o', self.args.profile, 
            '--'] + self.args.cmd)

def run(args):
    ProfileCmd(args).run()
