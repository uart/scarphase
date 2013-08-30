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

import pyscarphase.proto.meta
import pyscarphase.proto.data

import cmd

import prettytable 

class ShowCmd(cmd.Cmd):


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
        subparsers = parser.add_subparsers(title="What to show")

        def add_common_args(parser):

            #
            parser.add_argument(
                "profile",
                help="Input profile."
                )

        def conf_show_settings():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'settings',
                help="Show settings")

            # 
            sub_parser.set_defaults(func=self.show_settings)
            
            # 
            add_common_args(sub_parser)

        def conf_show_system_variables():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'system-variables',
                help="Show settings")

            # 
            sub_parser.set_defaults(func=self.show_system_variables)
            
            # 
            add_common_args(sub_parser)

        def conf_show_counters():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'counters',
                help="Show performance counters")

            # 
            sub_parser.set_defaults(func=self.show_counters)
            
            # 
            add_common_args(sub_parser)

        def conf_show_threads():

            #
            sub_parser = subparsers.add_parser(
                'threads',
                help="Show threads"
                )

            #
            sub_parser.set_defaults(func=self.show_threads)

            #
            add_common_args(sub_parser)

        def conf_show_processes():

            #
            sub_parser = subparsers.add_parser(
                'processes',
                help="Show processes"
                )

            #
            sub_parser.set_defaults(func=self.show_processes)

            #
            add_common_args(sub_parser)

        #
        conf_show_settings()
        conf_show_system_variables()
        conf_show_threads()
        conf_show_counters()
        conf_show_processes()

        self.args = parser.parse_args(args[2:])


    def run(self):  
        self.args.func()

    def show_phases(self):
        print("test1")

    def __show_pairs(self, pairs):
        
        # Table
        table = prettytable.PrettyTable([ "Key", "Value" ])
        table.align["Key"] = "l"
        table.align["Value"] = "l"

        # Add data
        for pair in pairs:
            table.add_row(
                [
                    pair.key, 
                    pair.value
                ])

        # Print table
        print(table)

    def show_settings(self):

        # Profile
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)

        #
        self.__show_pairs(profile.settings)

    def show_system_variables(self):

        # Profile
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)

        #
        self.__show_pairs(profile.system_variables)

    def show_threads(self):

        # Profile
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)
        
        # Table
        table = prettytable.PrettyTable(
            ["TID", 
             "Filename", 
             "No Windows"
             ]
            )

        # Add data
        for thread in profile.threads:
            table.add_row(
                [thread.tid, 
                 thread.profile.filename, 
                 thread.profile.no_windows
                 ]
                )

        # Print table
        print(table)


    def show_processes(self):

        # Profile
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)
        
        # Table
        table = prettytable.PrettyTable(
            ["PID", 
             "Parent", 
             "Threads",
             "Cmd Line",
             ]
            )

        def get_threads(pid):
            threads = []

            for thread in profile.threads:
                if thread.process == pid:
                    threads.append(thread.tid)

            return threads

        # Add data
        for process in profile.processes:
            table.add_row(
                [process.pid, 
                 process.parent, 
                 get_threads(process.pid),
                 process.cmdline,
                 ]
                )

        # Print table
        print(table)


    def show_counters(self):

        # Profile
        profile = pyscarphase.proto.meta.load_profile(self.args.profile)
        
        # Table
        table = prettytable.PrettyTable(
            ["ID", 
             "Name", 
             "Full Name", 
             "Config", 
             "Type", 
             "Func", 
             "Unit"
             ]
            )

        # Add data
        for counter in profile.performance_counters:
            table.add_row(
                [counter.id, 
                 counter.name,
                 counter.full_name,
                 hex(counter.config),
                 counter.type,
                 counter.func,
                 counter.unit,
                 ]
                )

        # Print table
        print(table)

def run(args): 
    ShowCmd(args).run();
