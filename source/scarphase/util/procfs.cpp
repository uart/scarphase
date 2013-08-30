/**
 * Copyright (c) 2011-2013 Andreas Sembrant
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 *
 *  - Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  - Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *  - Neither the name of the copyright holders nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * Authors: Andreas Sembrant
 *
 */

#include <fstream>
#include <sstream>

#include <boost/assert.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/algorithm/string/trim.hpp>
#include <boost/algorithm/string/replace.hpp>

#include "scarphase/util/procfs.hpp"

namespace scarphase {
namespace util {
namespace procfs {

//----------------------------------------------------------------------------//

void
parse_cpuinfo(std::map<std::string, std::string> &info)
{
    std::ifstream ifs;
    ifs.open("/proc/cpuinfo");

    BOOST_ASSERT(ifs.good());

    // read each line of the file
    for (int i = 0; not ifs.eof();)
    {
        std::string key, value;

        std::getline(ifs, key, ':');
        std::getline(ifs, value);

        // Convert to upper and _ space
        boost::trim(key);
        boost::to_upper(key);
        boost::replace_all(key, " ", "_");

        boost::trim(value);

        if (key == "PROCESSOR")
        {
            i++;
            continue;
        }

        std::stringstream _key; _key << "CPUINFO_" << (i - 1) << "." << key;

        info[_key.str()] = value;
    }

}

//----------------------------------------------------------------------------//

void
parse_meminfo(std::map<std::string, std::string> &info)
{
    std::ifstream ifs;
    ifs.open("/proc/meminfo");

    BOOST_ASSERT(ifs.good());

    // read each line of the file
    while (not ifs.eof())
    {
        std::string key, value;

        std::getline(ifs, key, ':');
        std::getline(ifs, value);

        // Convert to upper and _ space
        boost::trim(key);
        boost::to_upper(key);
        boost::replace_all(key, " ", "_");

        boost::trim(value);

        std::stringstream _key; _key << "MEMINFO" << "." << key;

        info[_key.str()] = value;
    }

}

//----------------------------------------------------------------------------//

void
parse_environ(pid_t tid, std::map<std::string, std::string> &info)
{
    std::stringstream filename; filename << "/proc/" << tid << "/environ";

    std::ifstream ifs;
    ifs.open(filename.str().c_str());

    BOOST_ASSERT(ifs.good());

    // read each line of the file
    while (not ifs.eof())
    {
        std::string key, value;

        std::getline(ifs, key, '=');
        std::getline(ifs, value, '\0');

        std::stringstream _key; _key << "ENVIRON" << "." << key;

        info[_key.str()] = value;
    }

}

//----------------------------------------------------------------------------//

std::string
get_cmdline(pid_t tid)
{
    std::stringstream filename; filename << "/proc/" << tid << "/cmdline";

    std::ifstream ifs;
    ifs.open(filename.str().c_str());

    BOOST_ASSERT(ifs.good());

    std::string cmdline;
    std::getline(ifs, cmdline, '\0');

    return cmdline;
}

//----------------------------------------------------------------------------//

} /* namespace procfs */
} /* namespace util */
} /* namespace scarphase */


