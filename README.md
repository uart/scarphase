# ScarPhase


Utility program for finding and analyzing runtime phases. It uses libscarphase to detect phases, and phase-guided hardware performance counter multiplexing to record an application phase behavior and performance over time.

See [uart/online-phase-detection][] for more information.

## Quick Start

    git clone git@github.com:uart/scarphase.git
    
    cd scarphase
    git submodule update --init

    cmake .
    make


## Prerequisites

### General

* Linux with perf event support.
* Intel PEBS for sampling branches (works without PEBS, but lower accuracy)

### C/C++

* [libscarphase][] — ScarPhase library, pulled in with submodule.
* [protobuf][] — data storage library
* [boost][] — portable C++ libraries

### Python

* [numpy][] — numeric library
* [scipy][] — 
* [matplotlib][] — graph plotting library
* [prettytable][] — print ascii tables

## Usage

### Help.

    ./scarphase -h
    usage: ./scarphase <command> [<args>]

    Commands:
       profile      Profile stuff
       plot         Plot stuff
       dump         Dump stuff
       show         Show stuff
       simpoint     Find simpoints
       refine       Refine data

    See './scarphase help <command>' for more information.

### 1. Profile  

This profiles and finds runtime phases in gcc from SPEC2006, with input 166.i. The profile is saved in *gcc.profile* and is used in the succeeding examples to plot and dump gcc's phases.

    ./scarphase profile \
        --scarphase-conf configs/scarphase/example0.conf \
        --counter-conf configs/counters/list0.json \
        --counter-limit=3 \
        gcc.profile \
        -- gcc 166.i -o 166.s
     
* `./scarphase profile` - scarphase command
* `--scarphase-conf configs/scarphase/example0.conf` - contains the configuration settings for the ScarPhase library.
* `--counter-conf configs/counters/list0.json` - a list of performance counter to sample
* `--counter-limit` - number of available hardware performance counters
* `gcc.profile` - output file
* `-- gcc 166.i -o 166.s` - command to run
        
### 2. Plot results

This plots the performance data and the detected phases from the example above.

    ./scarphase plot windows -t 0 -c "2" gcc.profile
    
* `./scarphase plot` - scarphase command
* `windows` - subcommand: plots windows over time
* `-t 0` - which thread
* `-c "2"` - which performance counter to plot
* `gcc.profile` - profile from example 1

![gcc/166](http://www.it.uu.se/research/group/uart/measurement/online_phase_detection/gcc-screenshot.png "gcc/166 screenshot")

### 3. Dump data

    ./scarphase dump windows -t 0 gcc.profile
    +-----+-----+-----------+--------------+----------------+------------------+--------------+------------------+-------------------+---------------------+---------------+-------------------+-------------------+
    | WID | PID |    cycles | instructions |            cpi | cache_references | cache_misses | cache_miss_ratio |   cache_miss_rate | branch_instructions | branch_misses | branch_miss_ratio |  branch_miss_rate |
    +-----+-----+-----------+--------------+----------------+------------------+--------------+------------------+-------------------+---------------------+---------------+-------------------+-------------------+
    |   0 |   1 |  82651513 |    100003538 | 0.826485888929 |           573485 |        41360 |  0.0721204565071 |  0.00041358536735 |            20520996 |        341234 |   0.0166285301162 |  0.00341221927568 |
    |   1 |   1 |  82651513 |    100003538 | 0.826485888929 |           573485 |        41360 |  0.0721204565071 |  0.00041358536735 |            20520996 |        341234 |   0.0166285301162 |  0.00341221927568 |
    |   2 |   1 |  82651513 |    100003538 | 0.826485888929 |           573485 |        41360 |  0.0721204565071 |  0.00041358536735 |            20520996 |        341234 |   0.0166285301162 |  0.00341221927568 |
    |   3 |   1 |  82651513 |    100003538 | 0.826485888929 |           573485 |        41360 |  0.0721204565071 |  0.00041358536735 |            20520996 |        341234 |   0.0166285301162 |  0.00341221927568 |
    |   4 |   2 | 104761301 |    100001455 |  1.04759776745 |           610295 |       525822 |   0.861586609754 |  0.00525814349401 |            20594340 |        217958 |   0.0105833933013 |  0.00217954828757 |
    ...
    
* `./scarphase dump` - scarphase command
* `windows` - subcommand: dump windows data over time
* `-t 0` - which thread
* `gcc.profile` - profile from example 1

Output data:
* `WID` - Window Id (100M instruction per window)
* `PID` - Phase id
* `cycles` - executed cycles during the window 
* the rest of the performance counter data (configured in list0.json)


## Publications using ScarPhase 

#### 2013
*    **Modeling Performance Variation Due to Cache Sharing** Andreas Sandberg, Andreas Sembrant, Erik Hagersten and David Black-Schaffer. *In International Symposium on High Performance Computer Architecture (HPCA'13)*

#### 2012
*    **Phase Behavior in Serial and Parallel Applications** Andreas Sembrant, David Black-Schaffer and Erik Hagersten. *In International Symposium on Workload Characterization (IISWC'12)*
*    **Phase Guided Profiling for Fast Cache Modeling** Andreas Sembrant, David Black-Schaffer and Erik Hagersten. *In International Symposium on Code Generation and Optimization (CGO'12)*
*    **Low Overhead Instruction-Cache Modeling Using Instruction Reuse Profiles** Muneeb Khan, Andreas Sembrant and Erik Hagersten. *In International Symposium on Computer Architecture and High Performance Computing (SBAC-PAD'12)*
*    **Power-Sleuth: A Tool for Investigating your Program's Power Behavior** Vasileios Spiliopoulos, Andreas Sembrant and Stefanos Kaxiras. *In International Symposium on Modeling, Analysis and Simulation of Computer and Telecommunication Systems (MASCOTS'12)*

#### 2011
*    **Efficient software-based online phase classification** Andreas Sembrant, David Eklöv, and Erik Hagersten. *In International Symposium on Workload Characterization (IISWC'11)*



[libscarphase]: https://github.com/uart/libscarphase
[boost]: http://www.boost.org/
[protobuf]: https://code.google.com/p/protobuf/

[numpy]: http://www.numpy.org/
[scipy]: http://www.scipy.org/
[prettytable]: https://code.google.com/p/prettytable/
[matplotlib]: http://matplotlib.org/
[uart]: http://www.it.uu.se/research/group/uart/
[uart/online-phase-detection]: http://www.it.uu.se/research/group/uart/measurement#online_phase_detection
