################################################################################
# ScarPhase                                                                    #
################################################################################

cmake_minimum_required(VERSION 2.8)

project(scarphase-profile)

# The version number.
set(SCARPHASE_VERSION_MAJOR 0)
set(SCARPHASE_VERSION_MINOR 3)

include(scarphase.cmake)

# Configure a header file to pass some of the CMake settings
# to the source code
configure_file(
  "${PROJECT_SOURCE_DIR}/scarphase_config.h.in"
  "${PROJECT_BINARY_DIR}/scarphase_config.h"
)

# Add the binary tree to the search path for include files
# so that we will find TutorialConfig.h
include_directories("${PROJECT_BINARY_DIR}")
include_directories("${PROJECT_BINARY_DIR}/include/")

if(CMAKE_SYSTEM_PROCESSOR MATCHES "amd64.*|x86_64.*|AMD64.*")
    set(X86_64 1)
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "i386.*|i686.*|x86.*|amd64.*|AMD64.*")
    set(X86 1)
endif()


################################################################################
# libscarphase                                                                 #
################################################################################

# Build libarary
add_subdirectory(libscarphase)

find_path(
    SCARPHASE_INCLUDE_DIR
    NAMES scarphase.h
    HINTS ${PROJECT_BINARY_DIR}/libscarphase/include/
)

include_directories(${SCARPHASE_INCLUDE_DIR})

find_library(
    SCARPHASE_LIBRARY
    NAMES scarphase libscarphase
    HINTS ${PROJECT_BINARY_DIR}/libscarphase/lib/
)

################################################################################
# boost                                                                        #
################################################################################

find_package(Boost REQUIRED COMPONENTS program_options)
include_directories(${Boost_INCLUDE_DIRS})

################################################################################
# libunwind                                                                    #
################################################################################

if(${ENABLE_STACKTRACES})

    # Check if 32 or 64bit system
    if(X86_64)
        set(LIBUNWIND_ARCH_LIBRARY "unwind-x86_64")
    else(X86)
        set(LIBUNWIND_ARCH_LIBRARY "unwind-x86")
    endif()

    foreach(COMPONENT "unwind" "unwind-ptrace" "${LIBUNWIND_ARCH_LIBRARY}")

        string(TOUPPER "LIB${COMPONENT}" UPPERCOMPONENT)

        find_library(
            ${UPPERCOMPONENT}
            NAMES "${COMPONENT}" "lib${COMPONENT}"
        )

        set(LIBUNWIND_LIBRARIES
            ${LIBUNWIND_LIBRARIES}
            ${${UPPERCOMPONENT}})

    endforeach()

    set(HAVE_UNWIND 1)

endif(${ENABLE_STACKTRACES})

################################################################################
# BUILD                                                                        #
################################################################################

# Build proto buffer files
include(proto/CMakeLists.txt)

set(SCARPHASE_SRC_FILES
    source/scarphase/profiler.cpp
    source/scarphase/profiler_config.cpp
    source/scarphase/util/procfs.cpp
    source/scarphase/multiplexer/phase_guided_multiplexer.cpp
)


add_executable(
    scarphase-profile
    ${PROTO_SRCS} ${PROTO_HDRS}
    ${SCARPHASE_SRC_FILES}
    source/scarphase-profile.cpp
)

target_link_libraries(
    scarphase-profile
    scarphase
    ${PROTOBUF_LIBRARY}
    ${LIBUNWIND_LIBRARIES}
    ${Boost_PROGRAM_OPTIONS_LIBRARY}
)

################################################################################
# Testing                                                                      #
################################################################################

if(${BUILD_UNITTESTS})

    include_directories(
        ${GTEST_INCLUDE_DIR}
        ${GMOCK_INCLUDE_DIR}
    )

    link_directories(
        ${GTEST_LIB_DIR}
        ${GMOCK_LIB_DIR}
    )

    set(TEST_SRC_FILES
        source/scarphase/multiplexer/phase_guided_multiplexer.cpp
        test/scarphase/multiplexer/phase_guided_multiplexer_unittest.cpp
    )

    add_executable(
        scarphase_test
        ${PROTO_SRCS} ${PROTO_HDRS}
        ${TEST_SRC_FILES}
    )

    target_link_libraries(
        scarphase_test
        pthread
        gtest
        gtest_main
        scarphase
        ${PROTOBUF_LIBRARY}
        ${LIBUNWIND_LIBRARIES}
        ${Boost_PROGRAM_OPTIONS_LIBRARY}
    )

endif(${BUILD_UNITTESTS})
