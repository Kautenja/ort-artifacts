cmake_minimum_required(VERSION 3.26)
project(onnxruntime_static_lib)

set(onnxruntime_BUILD_SHARED_LIB OFF)
set(BUILD_SHARED_LIBS OFF)

add_definitions(-D_SILENCE_ALL_CXX23_DEPRECATION_WARNINGS)
add_subdirectory(${ONNXRUNTIME_SOURCE_DIR}/cmake onnxruntime EXCLUDE_FROM_ALL)

function(bundle_static_library bundled_target_name)
  set(extension_blocklist .dylib .so .dll .tbd)

  function(recursively_collect_dependencies input_target)
    if(NOT TARGET ${input_target})
      if(EXISTS ${input_target})
        get_filename_component(extension "${input_target}" EXT)
        if(NOT extension IN_LIST extension_blocklist)
          list(APPEND static_libs "${input_target}")
          set(static_libs ${static_libs} PARENT_SCOPE)
        endif()
      endif()
      return()
    endif()

    get_target_property(alias ${input_target} ALIASED_TARGET)
    if(TARGET ${alias})
      set(input_target ${alias})
    endif()

    get_property(library_already_added GLOBAL PROPERTY static_bundle_${input_target})
    if(library_already_added)
      return()
    endif()
    set_property(GLOBAL PROPERTY static_bundle_${input_target} ON)

    get_target_property(input_type ${input_target} TYPE)

    if(${input_type} STREQUAL "STATIC_LIBRARY")
      list(APPEND static_libs "$<TARGET_FILE:${input_target}>")
      get_target_property(dependencies ${input_target} LINK_LIBRARIES)
    elseif(${input_type} STREQUAL "INTERFACE_LIBRARY")
      get_target_property(dependencies ${input_target} INTERFACE_LINK_LIBRARIES)
    else()
      get_target_property(dependencies ${input_target} LINK_LIBRARIES)
    endif()

    if(dependencies)
      foreach(dependency IN LISTS dependencies)
        recursively_collect_dependencies(${dependency})
      endforeach()
    endif()

    set(static_libs ${static_libs} PARENT_SCOPE)
  endfunction()

  recursively_collect_dependencies(onnxruntime)
  list(REMOVE_DUPLICATES static_libs)

  set(bundled_target_full_name
      ${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_STATIC_LIBRARY_PREFIX}${bundled_target_name}${CMAKE_STATIC_LIBRARY_SUFFIX})

  find_program(libtool libtool)
  add_custom_command(
    OUTPUT ${bundled_target_full_name}
    COMMAND ${libtool} -static -o ${bundled_target_full_name} ${static_libs}
    DEPENDS onnxruntime
    COMMENT "Bundling ${bundled_target_name}"
    VERBATIM)

  add_custom_target(bundling_${bundled_target_name} ALL DEPENDS ${bundled_target_full_name})
endfunction()

bundle_static_library(${PROJECT_NAME})
