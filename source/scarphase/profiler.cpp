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

#include <map>
#include <cstdio>
#include <cstring>
#include <sstream>
#include <fstream>
#include <iostream>

#include <fcntl.h>
#include <errno.h>
#include <unistd.h>
#include <signal.h>
#include <syscall.h>

#include <sys/wait.h>
#include <sys/types.h>
#include <sys/ptrace.h>

#include <boost/uuid/uuid.hpp>
#include <boost/uuid/random_generator.hpp>

#include <boost/program_options.hpp>
#include <boost/program_options/parsers.hpp>

#include <boost/date_time/microsec_time_clock.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <boost/date_time/posix_time/posix_time_types.hpp>

#include <scarphase.h>

#include "scarphase/profiler.hpp"

#include "scarphase/util/procfs.hpp"
#include "scarphase/multiplexer/phase_guided_multiplexer.hpp"

namespace scarphase {

/**
 * @brief Print line+errno to stdout.
 */
#define PRINT_E   std::cout << __LINE__ << ": " << strerror(errno) << std::endl;

//----------------------------------------------------------------------------//


Profiler::Profiler(boost::program_options::variables_map &vm)
{
    conf.vm = vm;

    if (scarphase_init() == -1)
    {
        std::cout << "Failed to init scarphase!" << std::endl;
        exit(EXIT_FAILURE);
    }

    conf.verbose = vm.count("verbose");

    LoadScarPhaseSettingsFromFile(vm["scarphase"].as<std::string>());
    LoadPerformanceCountersFromFile(vm["counters"].as<std::string>());

    unw_addr_space = unw_create_addr_space(&_UPT_accessors, __LITTLE_ENDIAN);

    std::map<std::string, std::string> info;

    scarphase::util::procfs::parse_cpuinfo(info);
    scarphase::util::procfs::parse_meminfo(info);

    for (std::map<std::string, std::string>::const_iterator it = info.begin();
         it != info.end();
         ++it)
    {
        //
        scarphase::proto::meta::Pair *pair = proto.add_settings();

        //
        pair->set_key(it->first);
        pair->set_value(it->second);
    }

    stats.no_phases = 0;
    stats.no_windows = 0;
}

//----------------------------------------------------------------------------//

int
Profiler::ForkAndRun(char *path, char *argv[])
{

    // Fork process
    int pid = fork();

    // If error
    if (pid == -1)
    {
        PRINT_E; exit(EXIT_FAILURE);
    }

    // If child process
    if (pid == 0)
    {

        // Allow ptrace
        if (ptrace(PTRACE_TRACEME, 0, NULL, NULL))
        {
            PRINT_E; exit(EXIT_FAILURE);
        }

        // Execute command and enter stopped state
        if (execve(path, argv, environ))
        {
            PRINT_E; exit(EXIT_FAILURE);
        }

    }

    return pid;

}

//----------------------------------------------------------------------------//

Profiler::ThreadControlBlock*
Profiler::ConfigureNewThread(pid_t tid)
{   
    // New control block
    ThreadControlBlock *tcb = new ThreadControlBlock();
    tcb->tid = tid;

    // Create proto data structure
    tcb->proto = proto.add_threads();
    tcb->proto->set_tid(proto.threads_size() - 1);

    // Set header
    boost::uuids::uuid uuid = boost::uuids::random_generator()();

    tcb->proto_data.header.set_uuid(uuid.data, uuid.size());
    tcb->proto->mutable_profile()->set_uuid(uuid.data, uuid.size());

    //------------------------------------------------------------------------//
    // Setup scarphase
    {

        // Set root thread as parent monitor
        scarphase_handle_t parent_monitor = (tid == root_process) ?
            NULL : thread_table[root_process]->scarphase_handle;

        tcb->scarhase_data_accessor =
            scarphase_create_perfevent_data_accessor(tid, &conf.perfevent_attr);

        conf.attr.data_accessor = tcb->scarhase_data_accessor;

        // Open and start scarphase
        if ((tcb->scarphase_handle = scarphase_open_monitor(
                 tcb->tid, &conf.attr, parent_monitor)
             ) == NULL)
        {
            std::cerr << "Failed to open monitor!" << std::endl;
            abort();
        }

        if (scarphase_start_monitor(tcb->scarphase_handle) == -1)
        {
            std::cerr << "Failed to start monitor!" << std::endl;
            abort();
        }

    }

    //------------------------------------------------------------------------//
    // Setup libunwind
    {
        tcb->libunwind_handle = _UPT_create(tcb->tid);
    }

    //------------------------------------------------------------------------//
    // Setup multiplexer and performance counters
    {

        tcb->multiplexer.reset(new multiplexer::PhaseGuidedMultiplexer(
            conf.vm["counter-limit"].as<int>()
        ));

        // Configure performance counters
        for (size_t i = 0; i < proto.performance_counters_size(); i++)
        {
            // Continue if pseudo counter
            if (not proto.performance_counters().Get(i).has_config())
            {
                continue;
            }

            tcb->event.events.push_back(new PerfEvent (
                tcb->tid,
                proto.performance_counters().Get(i).config(),
                proto.performance_counters().Get(i).type(),
                0, PERF_SAMPLE_READ
            ));

            // Open and configure event
            tcb->event.events.back().Configure();

            // Previous window's value
            tcb->event.values.push_back(0);

            // Get counter id
            tcb->event.cids.push_back(
                proto.performance_counters().Get(i).id()
            );

            // Add to multiplexer
            tcb->multiplexer->AddEvent(tcb->event.events.size() - 1);
        }

        // Get events to run
        tcb->event.active = tcb->multiplexer->Schedule(0, 0);

        // Start events
        for (size_t i = 0; i < tcb->event.active.size(); i++)
        {
            tcb->event.events[tcb->event.active[i]].Start();
        }

    }

    //------------------------------------------------------------------------//
    // Setup protobuf streams
    {
        std::stringstream filename;
        filename << conf.vm["output"].as<std::string>()
                 << ".<" << tcb->proto->tid() << ">";

        // Delete existing file
        unlink(filename.str().c_str());

        // Open new file for writing
        int fd = open(
            filename.str().c_str(),
            O_CREAT | O_WRONLY | O_TRUNC,
            S_IRUSR
        );

        if (fd < 0)
        {
            PRINT_E; exit(EXIT_FAILURE);
        }

        // Create FileOutputStream
        tcb->proto_data.fos.reset(
            new google::protobuf::io::FileOutputStream(fd)
        );

        // Close fd when done
        tcb->proto_data.fos->SetCloseOnDelete(true);

        // Create CodedOutputStream
        tcb->proto_data.cos.reset(
            new google::protobuf::io::CodedOutputStream(
                tcb->proto_data.fos.get()
            )
        );

        // Set filename proto header file
        tcb->proto->mutable_profile()->set_filename(filename.str());

    }

    //------------------------------------------------------------------------//
    // Save header to disk
    {
        // Write header size
        tcb->proto_data.cos->WriteLittleEndian32(
            tcb->proto_data.header.ByteSize()
        );

        // Write message
        tcb->proto_data.header.SerializeToCodedStream(
            tcb->proto_data.cos.get()
        );

    }


    //------------------------------------------------------------------------//
    // Setup to handle the coming sample window
    {
        boost::posix_time::ptime time =
                boost::posix_time::microsec_clock::universal_time();

        // Set starting time
        tcb->proto_data.window.mutable_time()->set_start(
            (time - time_0).total_microseconds()
        );
    }

    return tcb;

}

void
Profiler::HandleNewThread(pid_t tid)
{
    ThreadControlBlock *tcb  = ConfigureNewThread(tid);

    // Add to map
    thread_table[tid] = tcb;

    //
    tracked_threads.insert(tid);
}

void
Profiler::HandleNewUntrackedThread(pid_t tid)
{
    ThreadControlBlock *tcb  = ConfigureNewThread(tid);

    // Add to map
    thread_table[tid] = tcb;

    //
    untracked_threads.insert(tid);
}

void
Profiler::LinkThreadAndProcess(pid_t tid, pid_t pid)
{

    ThreadControlBlock *tcb = thread_table[tid];
    ProcessControlBlock *pcb = proc_table[pid];

    // Link thread to process
    thread2process_map[tid] = pid;

    // Update proto
    tcb->proto->set_process(pcb->proto->pid());

}

void
Profiler::HandleThreadExit(pid_t tid)
{

    //
    ThreadControlBlock *tcb = thread_table[tid];

    //------------------------------------------------------------------------//
    // Shutdown scarphase
    {

        if (scarphase_stop_monitor(tcb->scarphase_handle) == -1)
        {
            std::cerr << "Failed to stop monitor!" << std::endl;
            exit(EXIT_FAILURE);
        }

        if (scarphase_close_monitor(tcb->scarphase_handle) == -1)
        {
            std::cerr << "Failed to close monitor!" << std::endl;
            exit(EXIT_FAILURE);
        }

    }

    //------------------------------------------------------------------------//
    // Shutdown libunwind
    {
        _UPT_destroy(tcb->libunwind_handle);
    }

    //------------------------------------------------------------------------//
    // Shutdown multiplexer and performance counters
    {

        // Clear all events, d-tor will be called aurtomatically to close
        // events etc
        tcb->event.events.clear();
        tcb->event.active.clear();
        tcb->event.values.clear();

        // Delete multiplxer
        tcb->multiplexer.reset();
    }

    //------------------------------------------------------------------------//
    // Close protobuf streams
    {

        // Write all data to disk
        tcb->proto_data.cos.reset();
        tcb->proto_data.fos.reset();

    }

}

void
Profiler::HandleThreadExited(pid_t tid)
{
    // Remove from tracked thread set
    tracked_threads.erase(tid);

    //
    thread_table.erase(tid);

    //
    thread2process_map.erase(tid);

    // Remove if also process
    if (proc_table.count(tid))
    {
        proc_table.erase(tid);
    }

}

void
Profiler::HandleNewProcess(pid_t pid, pid_t parent)
{

    // New control block
    ProcessControlBlock *pcb = new ProcessControlBlock();
    pcb->pid = pid;

    // Create proto data structure
    pcb->proto = proto.add_processes();
    pcb->proto->set_pid(proto.processes_size() - 1);

    // Set cmdline info
    pcb->proto->set_cmdline(scarphase::util::procfs::get_cmdline(pid));

    // Add other settings
    {
        std::map<std::string, std::string> info;

        // Add environment
        scarphase::util::procfs::parse_environ(pid, info);

        // Save info
        std::map<std::string, std::string>::const_iterator it = info.begin();
        for (; it != info.end(); ++it)
        {
            //
            scarphase::proto::meta::Pair *pair = pcb->proto->add_settings();

            //
            pair->set_key(it->first);
            pair->set_value(it->second);
        }
    }

    // If not root
    if (pid != parent)
    {
        // Link child to parent
        pcb->proto->set_parent(proc_table[parent]->proto->pid());
    }

    // Add to proc table
    proc_table[pid] = pcb;

    // Point pid to self
    thread2process_map[pid] = pid;

}


void
Profiler::HandleExec(pid_t pid)
{
    // Update proc info

}

void
Profiler::HandleWindow(ThreadControlBlock *tcb, scarphase_event_info_t *info)
{

    boost::posix_time::ptime time =
            boost::posix_time::microsec_clock::universal_time();

    // Set starting time
    tcb->proto_data.window.mutable_time()->set_stop(
        (time - time_0).total_microseconds()
    );

    // The same window size for all windows
    tcb->proto_data.window.set_size(conf.attr.window_size);

    stats.no_windows++;

    std::cout << "\r"
              << (time - time_0).total_microseconds() / 1000000
              << "s: no_windows="
              << stats.no_windows
              << " no_phases="
              << stats.no_phases;

    std::cout.flush();


    //------------------------------------------------------------------------//
    // Add phase information
    {
        scarphase::proto::data::PhaseInfo *phase_info =
            tcb->proto_data.window.mutable_phase_info();

        stats.no_phases = std::max(stats.no_phases, info->phase);

        phase_info->set_phase(info->phase);

        phase_info->mutable_prediction()->set_phase(
            info->prediction.phase
        );

        phase_info->mutable_prediction()->set_confidence(
            info->prediction.confidence
        );

        scarphase_debug_data_t *debug_data =
            static_cast<scarphase_debug_data_t*> (info->_debug);

        // Copy signature

        for (size_t i = 0; i < debug_data->signature.fv_size; i++)
        {
            phase_info->mutable_signature()->add_fv_values(
                debug_data->signature.fv_values[i]
            );
        }

        for (size_t i = 0; i < debug_data->signature.uv_size; i++)
        {
            phase_info->mutable_signature()->add_uv_values(
                debug_data->signature.uv_values[i]
            );
        }
    }

    //------------------------------------------------------------------------//
    // Add code samples
    {

        // Compress and copy samples

        scarphase_debug_data_t *debug_data =
            static_cast<scarphase_debug_data_t*> (info->_debug);

        boost::unordered_map<uint64_t, size_t> compressed_samples;

        for (size_t i = 0; i < debug_data->samples.size; i++)
        {
            uint64_t value = debug_data->samples.values[i];

            boost::unordered_map<uint64_t, size_t>::iterator it =
                compressed_samples.find(value);

            if (it == compressed_samples.end())
            {
                compressed_samples[value] = 1;
            }
            else
            {
                ++(it->second);
            }
        }

        for (boost::unordered_map<uint64_t, size_t>::iterator it =
                compressed_samples.begin();
             it != compressed_samples.end();
             ++it)
        {
            scarphase::proto::data::CodeSample *sample =
                tcb->proto_data.window.add_code_samples();

            sample->set_ip(it->first);
            sample->set_count(it->second);
        }

    }

    //------------------------------------------------------------------------//
    // Add performance counter samples
    {

        // Stop and read event
        for (size_t i = 0; i < tcb->event.active.size(); i++)
        {
            PerfEvent &event = tcb->event.events[tcb->event.active[i]];

            //
            event.Stop();

            //
            scarphase::proto::data::PerformanceCounterSample *sample =
                tcb->proto_data.window.add_perf_samples();

            sample->set_cid(
                tcb->event.cids[tcb->event.active[i]]
            );

            uint64_t value = event.ReadNow<uint64_t>();

            sample->set_value(
                value - tcb->event.values[tcb->event.active[i]]
            );

            tcb->event.values[tcb->event.active[i]] = value;

        }

        // Get new schedule
        tcb->event.active = tcb->multiplexer->Schedule(
            info->phase, info->prediction.phase
        );

        // Start events
        for (size_t i = 0; i < tcb->event.active.size(); i++)
        {
            tcb->event.events[tcb->event.active[i]].Start();
        }

    }

    //------------------------------------------------------------------------//
    // Add stack trace
    {
        ////     unw_cursor_t cursor;
        ////     unw_init_remote(&cursor, unw_addr_space, tw.libunwind_handle);

        ////     if (unw_is_signal_frame(&cursor))
        ////     {
        ////         std::cout << "Signal frame" << std::endl;

        ////     }

        ////     for (int depth = 0; unw_step(&cursor) > 0; depth++)
        ////     {

        ////         unw_word_t  offset, pc;
        ////         char        fname[64];

        ////         unw_get_reg(&cursor, UNW_REG_IP, &pc);

        ////         fname[0] = '\0';
        ////         (void) unw_get_proc_name(&cursor, fname, sizeof(fname), &offset);

        ////         printf ("%p : (%s+0x%x) [%p]\n", (void*) pc, (char*) fname, offset, (void*) pc);

        //// //        unw_word_t ip, sp;
        //// //        unw_get_reg(&cursor, UNW_X86_64_RIP, &ip);
        //// //        unw_get_reg(&cursor, UNW_X86_64_RSP, &sp);
        //// //        std::cout << "d = " << depth << " ip = " << std::hex << ip << " sp = " << sp << " > " << std::dec;
        //// //        step = unw_step(&cursor);
        ////     }
    }

    //------------------------------------------------------------------------//
    // Save window to disk
    {
        // Write header size
        tcb->proto_data.cos->WriteLittleEndian32(
            tcb->proto_data.window.ByteSize()
        );

        // Write message
        tcb->proto_data.window.SerializeToCodedStream(
            tcb->proto_data.cos.get()
        );

    }

    //------------------------------------------------------------------------//
    // Setup for next window
    {
        tcb->proto_data.window.Clear();
        tcb->proto_data.window.mutable_time()->set_start(
            (time - time_0).total_microseconds()
        );
    }

}

void
Profiler::SaveProfile()
{
    // Open file
    std::ofstream ofs(conf.vm["output"].as<std::string>().c_str(),
                      std::ios::trunc | std::ios::binary);

    // Write profile data
    proto.SerializeToOstream(&ofs);

    // Close file
    ofs.close();
}

//----------------------------------------------------------------------------//

template<unsigned int event>
struct is_ptrace_event
{
    inline bool operator()(int status) const
    {
        return (status >> 8 == (SIGTRAP | event << 8));
    }
};

static is_ptrace_event<PTRACE_EVENT_EXEC> is_ptrace_exec_event;
static is_ptrace_event<PTRACE_EVENT_EXIT> is_ptrace_exit_event;

static is_ptrace_event<PTRACE_EVENT_FORK>  is_ptrace_fork_event;
static is_ptrace_event<PTRACE_EVENT_VFORK> is_ptrace_vfork_event;
static is_ptrace_event<PTRACE_EVENT_CLONE> is_ptrace_clone_event;

static is_ptrace_event<
    PTRACE_EVENT_FORK  | PTRACE_EVENT_VFORK | PTRACE_EVENT_CLONE
> is_ptrace_new_proc_event;

static bool is_ptrace_exited_event(int status)   { return WIFEXITED(status);   }
static bool is_ptrace_signaled_event(int status) { return WIFSIGNALED(status); }
static bool is_ptrace_stopped_event(int status)  { return WIFSTOPPED(status);  }

int
Profiler::Profile(char *path, char *argv[])
{

    // Fork and Execute command
    root_process = ForkAndRun(path, argv);

    // Wait for it to stop after execve
    if (root_process != waitpid(root_process, 0, 0))
    {
        PRINT_E; exit(EXIT_FAILURE);
    }

    // Listen for fork, clone, etc.
    ptrace(PTRACE_SETOPTIONS, root_process, 0,
           PTRACE_O_TRACEFORK   |
           PTRACE_O_TRACEVFORK  |
           PTRACE_O_TRACECLONE  |
           PTRACE_O_TRACEEXEC   |
           PTRACE_O_TRACEEXIT);

    // Record time after setup, want to know the target time
    time_0 = boost::posix_time::microsec_clock::universal_time();

    HandleNewThread(root_process);
    HandleNewProcess(root_process, root_process);
    LinkThreadAndProcess(root_process, root_process);

    // Continue the execution
    if (ptrace(PTRACE_CONT, root_process, NULL, 0))
    {
        PRINT_E; exit(EXIT_FAILURE);
    }

    //
    for (int tid = 0, status = 0;
         tracked_threads.size();
         tid = waitpid(-1, &status, __WALL))
    {

//        std::cout << "waitpid -> tid = " << tid << " " << std::endl;

        // If error
        if (tid == -1)
        {
            PRINT_E; break;
        }

        // Continue if signal is not to any child
        if (tid == 0)
        {
//            std::cout << "tid = " << tid << " >> CONTINUE" << std::endl;
            continue;
        }

        // If signal to untracked thread
        if (tracked_threads.count(tid) == 0)
        {           
            BOOST_ASSERT(untracked_threads.count(tid) == 0);

            //
            if (is_ptrace_stopped_event(status))
            {
//                std::cout << "tid = " << tid << " >> UNTRACKED" << std::endl;

                //
                HandleNewUntrackedThread(tid);

                // Continue the child
                if (ptrace(PTRACE_CONT, tid, NULL, WSTOPSIG(status)))
                {
                    PRINT_E; // abort();
                }

                continue;
            }
            else
            {
//                std::cout << "tid = " << tid << " >> UNKOWN EVENT" << std::endl;
                abort();
            }

        }

        // Thread is tracked, handle signals

        if (is_ptrace_fork_event(status)  |
            is_ptrace_vfork_event(status) |
            is_ptrace_clone_event(status))
        {
            long new_tid;

            // Get child pid
            if (ptrace(PTRACE_GETEVENTMSG, tid, NULL, (long) &new_tid))
            {
                PRINT_E; exit(EXIT_FAILURE);
            }

            // If first time we see this new thread/process
            if (untracked_threads.count(new_tid) == 0)
            {
                if (new_tid != waitpid(new_tid, 0, __WALL))
                {
                    PRINT_E; exit(EXIT_FAILURE);
                }

                // Handle new thread
                HandleNewThread(new_tid);

                // If thread
                if (is_ptrace_clone_event(status))
                {
                    // Link
                    LinkThreadAndProcess(new_tid, thread2process_map[tid]);
                }
                else // if process
                {
                    HandleNewProcess(new_tid, tid);
                    // Link
                    LinkThreadAndProcess(new_tid, tid);
                }

                // Continue the child
                if (ptrace(PTRACE_CONT, new_tid, NULL, 0))
                {
                    PRINT_E; // abort();
                }

            }
            // If untracked
            else
            {

                // If thread
                if (is_ptrace_clone_event(status))
                {
                    // Link
                    LinkThreadAndProcess(new_tid, thread2process_map[tid]);
                }
                else // if process
                {
                    HandleNewProcess(new_tid, tid);

                    // Link
                    LinkThreadAndProcess(new_tid, tid);
                }

                // Move thread from untracked to tracked
                untracked_threads.erase(new_tid);
                tracked_threads.insert(new_tid);

            }

            // Continue the parent
            if (ptrace(PTRACE_CONT, tid, NULL, 0))
            {
                PRINT_E; abort();
            }


        }
        else if (is_ptrace_exec_event(status))
        {
//            std::cout << "tid = " << tid << " >> PTRACE_EVENT_EXEC" << std::endl;

            //
            HandleExec(tid);

            if (ptrace(PTRACE_CONT, tid, NULL, 0))
            {
                PRINT_E; abort();
            }

            continue;
        }
        else if (is_ptrace_exit_event(status))
        {
//            std::cout << "tid = " << tid << " >> PTRACE_EVENT_EXIT" << std::endl;

            HandleThreadExit(tid);

            if (ptrace(PTRACE_CONT, tid, NULL, WSTOPSIG(status)))
            {
                PRINT_E; abort();
            }

            continue;
        }
        else if (is_ptrace_exited_event(status))
        {
//            std::cout << "tid = " << tid << " >> WIFEXITED" << std::endl;

            HandleThreadExited(tid);

            continue;
        }
        // If child was forcefully terminated
        else if (is_ptrace_signaled_event(status))
        {
//            std::cout << "tid = " << tid << " >> WIFSIGNALED" << std::endl;
            PRINT_E; abort();
        }
        // If it was stopped
        else if (is_ptrace_stopped_event(status))
        {

            // Handle SIGIO, (ie perfevent signals)
            if (WSTOPSIG(status) == SIGIO)
            {

                // Child siginfo
                siginfo_t info;

                // Get siginfo to pass to looppac
                if (ptrace(PTRACE_GETSIGINFO, tid, NULL, &info))
                {
                    PRINT_E; exit(EXIT_FAILURE);
                }

                ThreadControlBlock *tcb = thread_table[tid];

                //
                scarphase_event_info_t *event_info = scarphase_handle_signal(
                    tcb->scarphase_handle, WSTOPSIG(status), &info, NULL
                );

                // ScarPhase handles the signal, process the event
                if (event_info != NULL)
                {
                    HandleWindow(tcb, event_info);

                    // Resume thread
                    if (ptrace(PTRACE_CONT, tid, NULL, 0))
                    {
                        PRINT_E; exit(EXIT_FAILURE);
                    }

                    continue;
                }
                // ScarPhase ignored signal, forward to target
                else
                {
                    if (ptrace(PTRACE_CONT, tid, NULL, WSTOPSIG(status)))
                    {
                        PRINT_E; exit(EXIT_FAILURE);
                    }

                    continue;
                }

            }
            // Continue the child
            else
            {
                if (ptrace(PTRACE_CONT, tid, NULL, WSTOPSIG(status)))
                {
//                    std::cout << "tid = " << tid << " >> PTRACE_CONT" << std::endl;
                    PRINT_E;
//                    exit(EXIT_FAILURE);
                }

                continue;
            }

        }
        else
        {
            // Should never happen
            BOOST_ASSERT(0);
        }

    }

    // Record time when done
    time_1 = boost::posix_time::microsec_clock::universal_time();

    // Dump profile to file
    SaveProfile();

    //
    std::cout << std::endl;

    // Exit profiler.
    return EXIT_SUCCESS;

}

} /* namespace scarphase */

//----------------------------------------------------------------------------//

