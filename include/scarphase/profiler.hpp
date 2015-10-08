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


#ifndef __SCARPHASE_PROFILER_HPP
#define __SCARPHASE_PROFILER_HPP

#include <map>
#include <set>
#include <list>

#include <boost/date_time.hpp>
#include <boost/program_options.hpp>

#include <boost/unordered_map.hpp>

#include <boost/scoped_ptr.hpp>
#include <boost/ptr_container/ptr_vector.hpp>

#include <scarphase.h>
#include <scarphase/scarphase_debug.h>
#include <scarphase/scarphase_perfevent.h>

#include <scarphase/internal/util/perf_event_wrapper.hpp>

#include <libunwind-ptrace.h>

#include <google/protobuf/io/zero_copy_stream_impl.h>
#include <google/protobuf/io/coded_stream.h>

#include "scarphase/proto/data.pb.h"
#include "scarphase/proto/meta.pb.h"

#include "scarphase/multiplexer/multiplexer.hpp"

namespace scarphase {

/**
 * @brief
 */
class Profiler
{

public:

    /**
     * @brief C-tor.
     */
    Profiler(boost::program_options::variables_map &vm);

    /**
     * @brief Start profiling.
     */
    int Profile(char *path, char *argv[]);

private:

    /**
     * @briefvoid
Profiler::HandleNewThread(pid_t tid)
{
     */
    typedef scarphase::internal::util::perf_event_wrapper::Event PerfEvent;

    /**
     * @brief
     */
    struct _Conf
    {

        /**
         * @brief If verbose output.
         */
        bool verbose;

        /**
         * @brief Program options.
         */
        boost::program_options::variables_map vm;

        /**
         * @brief Scarphase settings.
         */
        scarphase_monitor_attr_t attr;

        /**
         * @brief Scarphase perfevent data accessor settings.
         */
        scarphase_perfevent_attr_t perfevent_attr;

    } conf;

    /**
     * @brief
     */
    struct ThreadControlBlock
    {

        /**
         * @brief The thread id.
         */
        pid_t tid;

        /**
         * @brief
         */
        scarphase::proto::meta::ThreadInfo *proto;

        /**
         * @brief Handle to scarphase.
         */
        scarphase_handle_t scarphase_handle;

        /**
         * @brief
         */
        scarphase_data_accessor_t *scarhase_data_accessor;

        /**
         * @brief
         */
        void *libunwind_handle;

        /**
         * @brief
         */
        struct _Protobuf
        {

            /**
             * @brief
             */
            scarphase::proto::data::Header header;

            /**
             * @brief
             */
            scarphase::proto::data::WindowData window;

            /**
             * @brief
             */
            boost::scoped_ptr<google::protobuf::io::FileOutputStream> fos;

            /**
             * @brief
             */
            boost::scoped_ptr<google::protobuf::io::CodedOutputStream> cos;

        } proto_data;


        struct _Event
        {

            /**
             * @brief event_schedule
             */
            std::vector<int> active;

            /**
             * @brief
             */
            std::vector<uint64_t> values;

            /**
             * @brief
             */
            std::vector<int> cids;

            /**
             * @brief
             */
            boost::ptr_vector<PerfEvent> events;

        } event;

        /**
         * @brief
         */
        boost::scoped_ptr<scarphase::multiplexer::Multiplexer> multiplexer;

    };

    /**
     * @brief
     */
    struct ProcessControlBlock
    {

        /**
         * @brief The process id.
         */
        pid_t pid;

        /**
         * @brief
         */
        scarphase::proto::meta::ProcessInfo *proto;

    };

    /**
     * @brief
     */
    struct _Stats
    {

        /**
         * @brief
         */
        int no_phases;

        /**
         * @brief
         */
        uint64_t no_windows;

    } stats;

    /**
     * @brief Measure the execution time.
     */
    boost::posix_time::ptime time_0, time_1;

    /**
     * @brief The process id of the main thread.
     */
    pid_t root_process;

    /**
     * @brief A set of all running threads.
     */
    std::set<pid_t> tracked_threads;

    /**
     * @brief
     */
    std::set<pid_t> untracked_threads;

    /**
     * @brief All threads ever created.
     */
    std::map<pid_t, pid_t> thread2process_map;

    /**
     * @brief All threads ever created.
     */
    std::map<pid_t, ThreadControlBlock*> thread_table;

    /**
     * @brief All threads ever created.
     */
    std::map<pid_t, ProcessControlBlock*> proc_table;

    /**
     * @brief Profile.
     */
    unw_addr_space_t unw_addr_space;

    /**
     * @brief Profile.
     */
    scarphase::proto::meta::ProfileInfo proto;

    /**
     * @brief Fork a new process and execute command.
     */
    int ForkAndRun(char *path, char *argv[]);

    /**
     * @brief
     */
    ThreadControlBlock* ConfigureNewThread(pid_t tid);

    /**
     * @brief
     */
    void HandleNewUntrackedThread(pid_t tid);

    /**
     * @brief
     */
    void HandleNewThread(pid_t tid);

    /**
     * @brief
     */
    void LinkThreadAndProcess(pid_t tid, pid_t pid);

    /**
     * @brief
     */
    void HandleThreadExit(pid_t tid);

    /**
     * @brief
     */
    void HandleThreadExited(pid_t tid);

    /**
     * @brief
     */
    void HandleNewProcess(pid_t pid, pid_t parent);

    /**
     * @brief
     */
    void HandleExec(pid_t pid);

    /**
     * @brief
     */
    void HandleWindow(ThreadControlBlock *tcb, scarphase_event_info_t *info);

    /**
     * @brief Dump profile to a file.
     */
    void SaveProfile();

    /**
     * @brief
     */
    void LoadScarPhaseSettingsFromFile(const std::string &file);


    /**
     * @brief
     */
    void LoadPerformanceCountersFromFile(const std::string &file);


};

} /* namespace scarphase */

#endif /* __SCARPHASE_PROFILER_HPP */
