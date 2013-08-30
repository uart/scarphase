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

import proto.meta
import proto.data

import cmd

class PrettyTableWrapper:

    def __init__(self, output_file, header):
        self.output_file = output_file

        import prettytable
        self.table = prettytable.PrettyTable(header)

        for column in header:
            try:
                self.table._align[column] = "r"
            except:
                self.table.set_field_align(column, "r")

    def __del__(self):
        self.output_file.write(self.table.get_string())
        self.output_file.write('\n')

    def write_row(self, row):
        self.table.add_row(row)


class CsvOutputWrapper:

    def __init__(self, output_file, header):
        self.output_file = output_file

        import csv
        self.csv = csv.writer(
                output_file,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL
                )

        self.csv.writerow([ '#' ] + header)

    def write_row(self, row):
        self.csv.writerow(row)


class DumpCmd(cmd.Cmd):

    def __init__(self, args):
        
        #
        cmd.Cmd.__init__(self)

        #
        self.parse_arguments(args)

    def parse_arguments(self, args):

        #
        parser = argparse.ArgumentParser(
            prog=' '.join(args[0:2]),
            description='Dump data to other formats.'
            )

        subparsers = parser.add_subparsers(title="What to dump")

        def add_common_args(parser):
            '''Add common arguments to all "dump" sub commands.'''

            parser.add_argument(
                "profile",
                help="Input profile."
                )

            parser.add_argument(
                "--thread", "-t",
                type=int,
                help="Thread to dump."
                )

            parser.add_argument(
                "--format",
                choices=[ "csv", "prettytable" ], default="prettytable",
                help="Thread to dump."
                )

            parser.add_argument(
                "--output-file", "-o",
                dest="output_file",
                type=argparse.FileType('w'), default=sys.stdout,
                help="Output file"
                )         

        def conf_dump_windows():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'windows',
                help="Dump windows")

            # 
            sub_parser.set_defaults(func=self.dump_windows)
            
            # 
            add_common_args(sub_parser)

        def conf_dump_raw_samples():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'raw-samples',
                help="Dump raw performance counter samples")

            # 
            sub_parser.set_defaults(func=self.dump_raw_samples)

            #
            add_common_args(sub_parser)
            
        def conf_dump_code():

            # Add new parser
            sub_parser = subparsers.add_parser(
                'code',
                help="Dump instruction count")

            sub_parser.add_argument(
                "--type",
                choices=['window', 'phase-instance', 'phase'],
                required=True,
                help="Type"
                )

            sub_parser.add_argument(
                "--id", "-i",
                type=int,
                required=True,
                help="Id"
                )

            # 
            sub_parser.set_defaults(func=self.dump_code)

            #
            add_common_args(sub_parser)

 
        conf_dump_windows()
        conf_dump_raw_samples()
        conf_dump_code()

        self.args = parser.parse_args(args[2:])


    def run(self):
        self.args.func()

    def dump_raw_samples(self):

        #
        profile = proto.meta.load_profile(self.args.profile)

        #
        thread = profile.threads[self.args.thread]

        #
        reader = proto.data.DataReader(
            thread.profile.filename,
            uuid=thread.profile.uuid
            )

        #
        header = ["WID", "PID", "CID", "Value"]

        if self.args.format == "csv":
            writer = CsvOutputWrapper(self.args.output_file, header)
        else:
            writer = PrettyTableWrapper(self.args.output_file, header)

        for i, w in enumerate(reader):
            for sample in w.perf_samples:
                writer.write_row([i, w.phase_info.phase, sample.cid, sample.value])


    def dump_windows(self):
        '''Dump windows.

        '''

        # Load meta profile
        profile = proto.meta.load_profile(self.args.profile)

        # Get thread to dump
        thread = profile.threads[self.args.thread]

        # Open a reader to that thread's datafile
        reader = proto.data.DataReader(
            thread.profile.filename,
            uuid=thread.profile.uuid
            )

        header = \
            [ "WID", "PID" ] + [ c.name for c in profile.performance_counters ]

        if self.args.format == "csv":
            writer = CsvOutputWrapper(self.args.output_file, header)
        else:
            writer = PrettyTableWrapper(self.args.output_file, header)

        import util.counter
        import util.demultiplexer

        dm = util.demultiplexer.Demultiplexer(reader)

        for i, w in enumerate(dm.read()):
            row = [i, w.phase]

            for c in profile.performance_counters:
                row.append(
                    util.counter.exec_func(
                        c.id, profile.performance_counters, w
                        )
                    )

            writer.write_row(row)


    def dump_phase_instances(self):
        pass

    def dump_phases(self):
        pass

    def dump_average(self):
        pass

    def dump_code(self):
        '''Dump code.

        '''

        # Load meta profile
        profile = proto.meta.load_profile(self.args.profile)

        # Get thread to dump
        thread = profile.threads[self.args.thread]

        # Open a reader to that thread's datafile
        reader = proto.data.DataReader(
            thread.profile.filename,
            uuid=thread.profile.uuid
            )
        
        header = [ "Address", "Count" ]

        if self.args.format == "csv":
            writer = CsvOutputWrapper(self.args.output_file, header)
        else:
            writer = PrettyTableWrapper(self.args.output_file, header)

        rows = {}

        def _get_window():
            for sample in reader.get(self.args.id).code_samples:
                if sample.count:
                    rows[sample.ip] = rows.get(sample.ip, 0) + sample.count
                    
        def _get_phase():
            for i, w in enumerate(reader):
    
                if self.args.id != w.phase_info.phase:
                    continue
                
                for sample in w.code_samples:
                    if sample.count:
                        rows[sample.ip] = rows.get(sample.ip, 0) + sample.count 
                        
        if self.args.type == 'window':
            _get_window()
        elif self.args.type == 'phase-instance':
            raise NotImplementedError
        else:
            _get_phase()
                
        for row in sorted(rows.iteritems(), key=lambda x: x[1], reverse=True):
            writer.write_row(['0x%x' % row[0], row[1]])
        
def run(args):
    DumpCmd(args).run();
