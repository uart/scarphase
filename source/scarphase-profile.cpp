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

#include <signal.h>

#include <boost/program_options.hpp>
#include <boost/program_options/parsers.hpp>

#include "scarphase/profiler.hpp"


//----------------------------------------------------------------------------//

static void
HandleSignal(int signum, siginfo_t *info, void *uc)
{

    switch(signum)
    {
        case(SIGINT):
        case(SIGHUP):
        case(SIGABRT):
        case(SIGTERM):
            killpg(getpgid(getpid()), signum);
            exit(EXIT_FAILURE);
    }
}

int
main(int argc, char *argv[])
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    namespace po = boost::program_options;

    // Program options
    po::options_description options("scarphase");
    po::variables_map vm;

    options.add_options()
        ("version",     "Print version string")

        ("help,h",      "Produce help message")

        ("verbose,v",   "Verbose output")

        ("scarphase,s",
            po::value<std::string>()
            ->default_value("scarphase.conf"),
            "Configuration file for scarphase.")

        ("counters,c",
            po::value<std::string>()
            ->default_value("counters.conf"),
            "Performance counter file.")

        ("counter-limit,l",
            po::value<int>()
            ->default_value(3),
            "")

        ("output,o",
            po::value<std::string>()
            ->default_value("scarphase.pb"),
            "Main output file.")

        ;

    // Count to delimiter
    int optc = 0; for (;optc < argc && strcmp(argv[optc], "--") != 0; optc++);

    po::store(po::parse_command_line(optc, argv, options), vm);
    po::notify(vm);

    // Print version and exit
    if (vm.count("version"))
    {
        std::cout << "ex_ptrace 0" << std::endl;
        exit(EXIT_SUCCESS);
    }

    // Print help
    if (vm.count("help"))
    {
        std::cout << options << std::endl;
        exit(EXIT_SUCCESS);
    }

    // Clear Signal action struct
    struct sigaction act;
    std::memset(&act, 0, sizeof(act));
    act.sa_sigaction = HandleSignal;
    act.sa_flags     = SA_SIGINFO;

    // Setup the sigal handler.
    sigaction(SIGINT,  &act, NULL);
    sigaction(SIGTERM, &act, NULL);
    sigaction(SIGHUP,  &act, NULL);
    sigaction(SIGABRT, &act, NULL);

    // Profile the application
    scarphase::Profiler(vm).Profile(argv[optc + 1], &argv[optc + 1]);

    google::protobuf::ShutdownProtobufLibrary();

    return EXIT_SUCCESS;

}
