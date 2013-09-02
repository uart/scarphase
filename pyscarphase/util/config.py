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

# 2to3
import ConfigParser as configparser

class Config:
    """Wrap .ini config file into python class hierichy. """


    def __init__(self, filename):
        """C-tor.     
        
        """

        with open(filename, 'r') as f:
            config = configparser.ConfigParser()
            config.readfp(f)

            self.__parse_config(config)


    def __parse_config(self, config):
        """Add parameters to config object"""

        import ast

        class Section:
            pass

        def add_or_get_section(obj, section):

            if not hasattr(obj, section):
                setattr(obj, section, Section())

            return getattr(obj, section)

        for section in config.sections():               

            obj = self
            for subsection in section.split('.'):
                obj = add_or_get_section(obj, subsection)

            for option in config.options(section):
                setattr(obj, 
                        option, 
                        ast.literal_eval(config.get(section, option))
                        )
        

