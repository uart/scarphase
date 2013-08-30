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

import os, sys, struct
from pyscarphase.proto import data_pb2 as data_pb

class DataReader:
    '''
    Read scarphase protobuf data file

    <size of header>
    <header>
    <size of window 0>
    <window 0>
    <size of window 1>
    <window 1>    
    ...
    '''

    def __init__(self, filename, uuid=None):
        self.messages  = []
        self.position  = 0
        self.eof       = None

        self.open(filename, uuid)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def open(self, filename, uuid=None):
        self.file = open(filename, 'rb')

        data = self.file.read(4)

        if len(data) != 4:
            raise EOFError()

        size = struct.unpack('<i', data)[0]
    
        data = self.file.read(size)

        header = data_pb.Header()
        header.ParseFromString(data)
    
        if uuid and uuid != header.uuid:
            raise Exception('UUID mismatch')

    def read(self):
        pass

    def get(self, index):
        # Change position
        cur_index = self.tell()
        self.seek(index)

        # Get window
        window = self.next()

        # Restore      
        self.seek(cur_index)     

        #
        return window

    def __next(self, skip=True):
        
        # Get message size
        data = self.file.read(4)

        # Check if end of file
        if len(data) != 4:
            self.eof = True
            raise StopIteration()

        # Add to message position list
        if self.position == len(self.messages):
            self.messages.append(self.file.tell() - 4)

        # 
        self.position += 1

        # Parse size
        size = struct.unpack('<i', data)[0]
    
        if skip:
            self.file.seek(size, os.SEEK_CUR)
        else:
            # Read message
            data = self.file.read(size)

            # Parse message
            window = data_pb.WindowData()
            window.ParseFromString(data)

            return window

    def __read_all(self):
        if not self.eof:
            current_mpos, current_fpos = self.position, self.file.tell()
            try:
                # Go to current end
                if len(self.messages) != 0:
                    current_end = len(self.messages) - 1
                    self.file.seek(self.messages[current_end])

                # Find end
                while True:
                    self.__next(skip=True)

            except StopIteration:

                self.position = current_mpos
                self.file.seek(current_fpos)

    def next(self):
        return self.__next(skip=False)

    def seek(self, position, whence=os.SEEK_SET):
        
        if self.position == position:
            return


        if whence == os.SEEK_SET:
            pass

        elif whence == os.SEEK_CUR:
            self.seek(self.position + position)
            return

        elif whence == os.SEEK_END:
            if position > 0:
                raise IndexError()

            self.__read_all()
            self.seek(len(self.messages) - 1 + position)
            return

        else:
            pass

            
        # If we know the offset already
        if position < len(self.messages):
            self.position = position
            self.file.seek(self.messages[self.position])
        # iterate through messages until we reach right offset
        else:
            if len(self.messages) > 0:
                self.position = len(self.messages) - 1
                self.file.seek(self.messages[self.position])
                position = position - self.position

            try:
                while position > 0:
                    self.__next(skip=True)
                    position -= 1
            except StopIteration:
                raise IndexError()
                

    def tell(self):
        return self.position


class DataWriter:
   
    '''
    Read scarphase protobuf data file

    <size of header>
    <header>
    <size of window 0>
    <window 0>
    <size of window 1>
    <window 1>    
    ...
    '''

    def __init__(self, filename, uuid=None):
        self.open(filename, uuid)

    def open(self, filename, uuid=None):

        self.file = open(filename, 'wb')
        self.uuid = uuid
        
        header = data_pb.Header()
        header.uuid = uuid

        data = header.SerializeToString()
        self.file.write(struct.pack('<i', len(data)))
        self.file.write(data)
        self.file.flush()

    def write(self, window):

        data = window.SerializeToString()
        self.file.write(struct.pack('<i', len(data)))
        self.file.write(data)
