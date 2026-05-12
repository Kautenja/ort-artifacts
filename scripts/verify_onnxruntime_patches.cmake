if(NOT DEFINED ORT_SOURCE_DIR)
    message(FATAL_ERROR "ORT_SOURCE_DIR is required")
endif()

set(MLAS_CMAKE "${ORT_SOURCE_DIR}/cmake/onnxruntime_mlas.cmake")
if(NOT EXISTS "${MLAS_CMAKE}")
    message(FATAL_ERROR "Expected ONNX Runtime MLAS CMake file not found: ${MLAS_CMAKE}")
endif()

file(READ "${MLAS_CMAKE}" MLAS_CMAKE_CONTENT)

string(FIND "${MLAS_CMAKE_CONTENT}" "cvtfp16Avx.S" CVTFP16AVX_INDEX)
if(CVTFP16AVX_INDEX GREATER_EQUAL 0)
    string(FIND "${MLAS_CMAKE_CONTENT}" "CMAKE_CXX_COMPILER_ID MATCHES \"Clang\"" CLANG_GUARD_INDEX)
    if(CLANG_GUARD_INDEX LESS 0)
        message(FATAL_ERROR
            "ONNX Runtime MLAS still allows x86_64/cvtfp16Avx.S for Clang. "
            "This would fail Linux x86_64 builds with unsupported vcvtneeph2ps/vcvtneoph2ps assembler instructions.")
    endif()
endif()

message(STATUS "Verified ONNX Runtime patch guards")
