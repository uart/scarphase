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

import pyscarphase.util.progress

import pyscarphase.cmd

class RefineCmd(pyscarphase.cmd.Cmd):


    def __init__(self, args):
        
        #
        pyscarphase.cmd.Cmd.__init__(self)

        #
        self.parse_arguments(args)

    def parse_arguments(self, args):

        #
        self.parser = argparse.ArgumentParser(
            prog=' '.join(args[0:2]), 
            description='Refine ...'
            )

        #
        subparsers = self.parser.add_subparsers(title="What to refine")

        def add_common_args(parser):

            #
            parser.add_argument(
                "profile",
                help="Input profile."
                )

            parser.add_argument(
               "--output-file", "-o",
                dest="output",
                help="Output file"
                )

        def conf_refine_classification():

            # Add new parser
            sub_parser = subparsers.add_parser(
                "classification",
                help="Refine classification")

            sub_parser.add_argument(
                "--no-clusters", "-k",
                dest="k",
                type=int,
                help="Number of clusters"
                )

            sub_parser.add_argument(
                "--max-iterations", "-i",
                dest="max_iter",
                type=int,
                default=20,
                help="Max no. refine iterations"
                )

            # 
            sub_parser.set_defaults(func=self.refine_classification)
            
            # 
            add_common_args(sub_parser)

        conf_refine_classification()

        #
        self.args = self.parser.parse_args(args[2:])

    def run(self):
        self.args.func()

    def refine_classification(self):
        profile = pyscarphase.proto.meta.load_profile(
            self.args.profile
            )
    
        # Open readers to all threads
        readers, writers = [], []
        for thread in profile.threads:
            readers.append(
                pyscarphase.proto.data.DataReader(
                    thread.profile.filename, 
                    uuid=thread.profile.uuid
                    )
                )

            tmpfile = '%s_' % (thread.profile.filename)

            writers.append(
                pyscarphase.proto.data.DataWriter(
                    tmpfile, 
                    uuid=thread.profile.uuid
                    )
                )

        # Refine
        self._refine_classification(
            readers, 
            writers, 
            k = self.args.k, 
            max_iter = self.args.max_iter)

        # Move tmp files to final dest
        import shutil
        for thread in profile.threads:

            tmpfile = '%s_' % (thread.profile.filename)

            if self.args.output:
                thread.profile.filename = '%s<%i>' % (self.args.output, 
                                                      thread.tid)

            shutil.move(tmpfile, thread.profile.filename)

        pyscarphase.proto.meta.save_profile(profile, self.args.output)


    def _refine_classification(self, readers, writers, k=None, max_iter=25):

        from sklearn.cluster import MiniBatchKMeans

        if k == None:
            phase_set = set()

            pyscarphase.util.progress.start(
                'Examing existing phase clusters:', 
                max_value = len(readers)
                )

            for i, reader in enumerate(readers):
                pyscarphase.util.progress.update(i + 1)

                # Find all phases
                for w in reader:
                    phase_set.add(w.phase_info.phase)

                # Reset reader
                reader.seek(0)

            k = len(phase_set)
            pyscarphase.util.progress.stop()


        def _get_batches(readers, size=k):
            batch = []

            for reader in readers:
                while True:
                    try:
                        wd = reader.next()
                        batch.append(wd.phase_info.signature.fv_values[:])

                        if len(batch) == size:
                            yield batch
                            batch = []

                    except StopIteration:
                        reader.seek(0)
                        break

            yield batch



        km = MiniBatchKMeans(k=k, init='k-means++')

        pyscarphase.util.progress.start(
            'Refining phase clusters:',
            max_value = max_iter
            )


        for iteration in range(max_iter):
            pyscarphase.util.progress.update(iteration + 1)

            for batch in _get_batches(readers, km.batch_size):
                km.partial_fit(batch)

        pyscarphase.util.progress.stop()

        # Reclassify        

        pyscarphase.util.progress.start(
            'Reclassifying windows:',
            max_value = len(readers)
            )

        for i, (reader, writer) in enumerate(zip(readers, writers)):
            pyscarphase.util.progress.update(i + 1)

            # Find all phases
            for w in reader:

                # Reclassify
                w.phase_info.phase = \
                    int(km.predict([w.phase_info.signature.fv_values])[0])

                # Invalidate predictions
                w.phase_info.ClearField('prediction')

                # Write to file
                writer.write(w)

        pyscarphase.util.progress.stop()


def run(args):
    RefineCmd(args).run();
