/**
 * @file
 * @author Andreas Sembrant<andreas@sembrant.com>
 *
 */

#include <gtest/gtest.h>
#include "scarphase/multiplexer/phase_guided_multiplexer.hpp"

TEST(PhaseGuidedMultiplexerTest, CTor)
{
    EXPECT_NO_THROW(scarphase::multiplexer::PhaseGuidedMultiplexer(3));
}

TEST(PhaseGuidedMultiplexerTest, Schedule)
{
    // Multiplex with 2 counters
    scarphase::multiplexer::PhaseGuidedMultiplexer multiplexer(2);

    typedef scarphase::multiplexer::Multiplexer::event_t event_t;

    // Add 10 events
    for (uint64_t i = 0; i < 5; i++)
    {
        multiplexer.AddEvent(event_t(i));
    }

    std::vector<event_t> counters;

    counters = multiplexer.Schedule(1, 1);

    // Check num active events
    EXPECT_EQ(2, counters.size());

    // Check corect events
    EXPECT_EQ(event_t(0), counters[0]);
    EXPECT_EQ(event_t(1), counters[1]);

    counters = multiplexer.Schedule(1, 1);

    // Check corect events
    EXPECT_EQ(event_t(2), counters[0]);
    EXPECT_EQ(event_t(3), counters[1]);

    counters = multiplexer.Schedule(1, 1);

    // Check corect events
    EXPECT_EQ(event_t(4), counters[0]);
    EXPECT_EQ(event_t(0), counters[1]);

}


