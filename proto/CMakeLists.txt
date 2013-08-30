################################################################################
# ScarPhase                                                                    #
################################################################################

find_program(PROTOC protoc)

set(PROTO_DIR  ${PROJECT_BINARY_DIR}/proto/scarphase/proto)
set(PYSCARPHASE_DIR ${PROJECT_BINARY_DIR}/pyscarphase)

set(PROTOBUF_LIBRARY protobuf pthread)

include_directories(${PROJECT_BINARY_DIR}/proto/)

set(PROTO_HDRS "")
set(PROTO_SRCS "")

foreach(PROTO_TARGET meta data)

    set(PROTO_FILE ${PROTO_DIR}/${PROTO_TARGET}.proto)

    set(PROTO_HDR ${PROTO_DIR}/${PROTO_TARGET}.pb.h)
    set(PROTO_SRC ${PROTO_DIR}/${PROTO_TARGET}.pb.cc)

    set(PROTO_HDRS ${PROTO_HDRS} ${PROTO_HDR})
    set(PROTO_SRCS ${PROTO_SRCS} ${PROTO_SRC})

    set(PROTO_CMD ${PROTOC} ${PROTO_FILE} -I ${PROTO_DIR}/)

    add_custom_command(
        OUTPUT ${PROTO_HDR} ${PROTO_SRC}
        COMMAND ${PROTO_CMD} --cpp_out=${PROTO_DIR}
        DEPENDS ${PROTO_FILE}
        WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
    )

    add_custom_target(protoc_python_${PROTO_TARGET} ALL
        COMMAND ${PROTO_CMD} --python_out=${PYSCARPHASE_DIR}/proto/
        DEPENDS ${PROTO_FILE}
        WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
    )

endforeach()



