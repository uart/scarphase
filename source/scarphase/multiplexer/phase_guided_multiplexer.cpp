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

#include "scarphase/multiplexer/phase_guided_multiplexer.hpp"

namespace scarphase {
namespace multiplexer {

//----------------------------------------------------------------------------//

PhaseGuidedMultiplexer::PhaseGuidedMultiplexer(int max_active_events)
    : max_active_events_(max_active_events)
{

}

//----------------------------------------------------------------------------//

void
PhaseGuidedMultiplexer::AddEvent(event_t event)
{
    BOOST_ASSERT(
        std::count(events_.begin(), events_.end(), event) == 0
    );

    events_.push_back(event);

    // Add queue
    for(PhaseMap::iterator phase_entry = phase_table_.begin();
        phase_entry != phase_table_.end();
        ++phase_entry)
    {
        (phase_entry->second).event_queue.push_back(event);
    }
}


//----------------------------------------------------------------------------//

std::vector<Multiplexer::event_t>
PhaseGuidedMultiplexer::Schedule(int phase, int prediction)
{

    PhaseMap::iterator phase_entry = phase_table_.find(phase);

    // Get or create phase entry
    if (phase_entry == phase_table_.end())
    {
        phase_entry = phase_table_.insert(
            PhaseMap::value_type(phase, PhaseData())
        ).first;

        (phase_entry->second).event_queue.insert(
            (phase_entry->second).event_queue.begin(),
            events_.begin(), events_.end()
        );
    }

    // Shorten for readability
    PhaseData &phase_data = (phase_entry->second);

    // Update phase
    // Remove events from active_events and push the correspinding
    // events to the end of the queue
    for (EventList::iterator event = phase_data.event_queue.begin();
        active_events_.size() && event != phase_data.event_queue.end();
        )
    {
        EventVector::iterator active_event = std::find(
            active_events_.begin(), active_events_.end(),
            *event
        );

        if (active_event != active_events_.end())
        {
            // Remove from active
            active_events_.erase(active_event);

            // Move event to end of queue
            phase_data.event_queue.push_back(*event);
            event = phase_data.event_queue.erase(event);
        }
        else
        {
            ++event;
        }
    }

    // Update schedule
    // Use the prediction to schedule events
    phase_data = phase_table_[prediction];

    // Add front of queue to active events
    for (EventList::iterator event = phase_data.event_queue.begin();
         event != phase_data.event_queue.end();
         ++event)
    {
        active_events_.push_back(*event);

        // Stop if max events
        if (active_events_.size() == max_active_events_)
        {
            break;
        }
    }

    return active_events_;
}

//----------------------------------------------------------------------------//

} /* namespace multiplexer */
} /* namespace scarphase */


