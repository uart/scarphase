################################################################################
# Options                                                                      #
################################################################################
OPTION(BUILD_UNITTESTS "Building Unit-Tests" OFF)

OPTION(ENABLE_STACKTRACES "Build support for collecting stack traces." ON)

################################################################################
# Config                                                                       #
################################################################################
SET(EXECUTABLE_OUTPUT_PATH ${PROJECT_BINARY_DIR}/bin)
SET(LIBRARY_OUTPUT_PATH ${PROJECT_BINARY_DIR}/lib)
SET(THIRD_PARTY_DIR ${PROJECT_BINARY_DIR}/3psw)
