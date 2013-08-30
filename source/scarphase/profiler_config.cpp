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

#include <cstring>
#include <fstream>
#include <iostream>

#include <boost/exception/all.hpp>

#include <boost/foreach.hpp>

#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>

#include <boost/program_options.hpp>
#include <boost/program_options/parsers.hpp>

#include <boost/algorithm/string/predicate.hpp>

#include "scarphase/profiler.hpp"

namespace scarphase {

namespace pt = boost::property_tree;
namespace po = boost::program_options;

//----------------------------------------------------------------------------//

void
Profiler::LoadPerformanceCountersFromFile(const std::string &file)
{

    //
    pt::ptree root;

    //
    pt::read_json(file, root);

    //
    BOOST_FOREACH(pt::ptree::value_type &v, root)
    {

//        std::cout << v.first << std::endl;

        scarphase::proto::meta::PerformanceCounterInfo *ctr_info =
            proto.add_performance_counters();

        // Id in order they are added
        ctr_info->set_id(proto.performance_counters_size() - 1);

        //
        ctr_info->set_name(v.first);

        //
        if (v.second.count("full-name"))
        {
            ctr_info->set_full_name(v.second.get<std::string>("full-name"));
        }

        //
        if (v.second.count("func"))
        {
            ctr_info->set_func(v.second.get<std::string>("func"));
        }

        //
        if (v.second.count("unit"))
        {
            ctr_info->set_unit(v.second.get<std::string>("unit"));
        }

        //
        if (v.second.count("type"))
        {
            ctr_info->set_type(
                std::strtol(v.second.get<std::string>("type").c_str(), 0, 10)
            );
        }
        else
        {
            ctr_info->set_type(PERF_TYPE_RAW);
        }

        if (v.second.count("config"))
        {
            //
            ctr_info->set_config(
                std::strtol(v.second.get<std::string>("config").c_str(), 0, 16)
            );
        }

    }

}

//----------------------------------------------------------------------------//

static boost::program_options::options_description
_get_scarphase_options()
{

    po::options_description options("ScarPhase");

    options.add_options()

        ("sample_period",
            po::value<uint64_t>()
            ->default_value(100000),
           "The sample period to sample basic blocks with.")

        ("window_size",
            po::value<uint64_t>()
            ->default_value(100E6),
           "The size of the interval in instructions.")

        // [dsr]

        ("dsr.enabled",
            po::value<bool>()
            ->default_value(false),
           "Enable dynamic sample rate.")

        ("dsr.maximum_sample_period",
            po::value<uint64_t>()
            ->default_value(10),
            "The maximum sample rate.")

        ("dsr.similarity_threshold",
            po::value<double>()
            ->default_value(0.5),
            "The similarity threshold when in DSR mode.")

        // [classifier]

        ("classifier.type",
            po::value<std::string>()
            ->default_value("leader_follower"),
           "The type of classifier, [ leader_follower ]")

        ("classifier.leader_follower.type",
            po::value<std::string>()
            ->default_value("unbounded"),
           "The type of classifier, [ bounded | unbounded ]")

        ("classifier.leader_follower.similarity_threshold",
            po::value<double>()
            ->default_value(0.35),
            "The diffrence between two siganture to be classified as the same phase.")

        ("classifier.leader_follower.transition_threshold",
            po::value<uint32_t>()
            ->default_value(0),
            "The number of time a signature must occur to be given a stabe phase id.")

        // [predictor]

        ("predictor.type",
            po::value<std::string>()
            ->default_value("last_value"),
            "The type of predictor,  [ last_value | run_length ]")

        ("predictor.run_length.cache_size",
            po::value<size_t>()
            ->default_value(256),
            "The size of the markov table if a markov predictor is used.")

        ("predictor.run_length.pattern_length",
            po::value<size_t>()
            ->default_value(2),
            "The size of the pattern if a markov predictor is used.")

        ("predictor.run_length.confidence_threshold",
            po::value<size_t>()
            ->default_value(1),
            "All predictions with a confidence below the threshold will fall "
            "back to a last value prediction.")

        // [perfevent]

        ("perfevents.sample.counter",
            po::value<std::string>()
            ->default_value("0x0"),
            "The counter to sample.")

        ("perfevents.sample.type_id",
            po::value<uint32_t>()
            ->default_value(0),
            "The type of the counter.")

        ("perfevents.sample.randomize",
            po::value<bool>()
            ->default_value(0),
            "Randomize the sample period.")

        ("perfevents.sample.precise_ip",
            po::value<int>()
            ->default_value(0),
            "Set the precise_ip variable. precise_ip > 0 will enable PEBS.")

        ("perfevents.sample.kernal_buffer_size",
            po::value<size_t>()
            ->default_value(1024),
            "Number of pages to allocate.")

        ("perfevents.window.counter",
            po::value<std::string>()
            ->default_value("0x0"),
            "The counter to sample.")

        ("perfevents.window.type_id",
            po::value<uint32_t>()
            ->default_value(0),
            "The type of the counter.")

      ;

    return options;

}

//----------------------------------------------------------------------------//

static void
_populate_scarphase_attr(
    po::variables_map &vm,
    scarphase_monitor_attr_t *attr,
    scarphase_perfevent_attr_t *perfevent_attr)
{

    scarphase_init_attr(attr);

    attr->window_size = vm["window_size"].as<uint64_t>();
    attr->sample_period = vm["sample_period"].as<uint64_t>();

    //------------------------------------------------------------------------//
    // Dynamic Sample Rate                                                    //
    //------------------------------------------------------------------------//
    {
        attr->dsr.enabled = vm["dsr.enabled"].as<bool>();

        attr->dsr.maximum_sample_period =
            vm["dsr.maximum_sample_period"].as<uint64_t>();

        attr->dsr.similarity_threshold  =
            vm["dsr.similarity_threshold"].as<double>();
    }

    //------------------------------------------------------------------------//
    // Classification                                                         //
    //------------------------------------------------------------------------//
    if (vm["classifier.type"].as<std::string>() == "leader_follower")
    {
        attr->classifier.type = SCARPHASE_CLASSIFIER_TYPE_LEADER_FOLLOWER;

        if (vm["classifier.leader_follower.type"].as<std::string>() ==
            "bounded")
        {
            attr->classifier.attr.leader_follower.type =
                SCARPHASE_CLASSIFIER_LEADER_FOLLOWER_TYPE_BOUNDED;
        }
        else
        {
            attr->classifier.attr.leader_follower.type =
                SCARPHASE_CLASSIFIER_LEADER_FOLLOWER_TYPE_UNBOUNDED;
        }

        attr->classifier.attr.leader_follower.similarity_threshold =
            vm["classifier.leader_follower.similarity_threshold"].as<double>();

        attr->classifier.attr.leader_follower.transition_threshold =
            vm["classifier.leader_follower.transition_threshold"].as<uint32_t>();
    }
    else
    {
        throw std::runtime_error("Missing classifier.");
    }

    //------------------------------------------------------------------------//
    // Prediction                                                             //
    //------------------------------------------------------------------------//
    if (vm["predictor.type"].as<std::string>() == "last_value")
    {
        attr->predictor.type = SCARPHASE_PREDICTOR_TYPE_LAST_VALUE;
    }
    else if (vm["predictor.type"].as<std::string>() == "run_length")
    {
        attr->predictor.type = SCARPHASE_PREDICTOR_TYPE_RUN_LENGTH;

        attr->predictor.attr.run_length.cache_size           =
            vm["predictor.run_length.cache_size"].as<size_t>();

        attr->predictor.attr.run_length.pattern_length       =
            vm["predictor.run_length.pattern_length"].as<size_t>();

        attr->predictor.attr.run_length.confidence_threshold =
            vm["predictor.run_length.confidence_threshold"].as<size_t>();
    }
    else
    {
        throw std::runtime_error("Missing predictor.");
    }

    //------------------------------------------------------------------------//
    // Performance counters                                                   //
    //------------------------------------------------------------------------//
    {

        perfevent_attr->window.counter = std::strtol(
            vm["perfevents.window.counter"].as<std::string>().c_str(), 0, 16
        );

        perfevent_attr->window.type_id =
            vm["perfevents.window.type_id"].as<uint32_t>();

        perfevent_attr->sample.counter = std::strtol(
            vm["perfevents.sample.counter"].as<std::string>().c_str(), 0, 16
        );

        perfevent_attr->sample.type_id =
            vm["perfevents.sample.type_id"].as<uint32_t>();

        perfevent_attr->sample.precise_ip =
            vm["perfevents.sample.precise_ip"].as<int>();

        perfevent_attr->sample.kernal_buffer_size =
            vm["perfevents.sample.kernal_buffer_size"].as<size_t>();

    }

}

//----------------------------------------------------------------------------//

void
Profiler::LoadScarPhaseSettingsFromFile(const std::string &file)
{
    po::options_description options = _get_scarphase_options();
    po::variables_map vm;

    std::ifstream ifs(file.c_str());
    po::store(po::parse_config_file(ifs, options, false), vm);
    po::notify(vm);

    _populate_scarphase_attr(vm, &conf.attr, &conf.perfevent_attr);
}

//----------------------------------------------------------------------------//

} /* namespace scarphase */
