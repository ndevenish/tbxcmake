
if (NOT PYTHONINTERP_FOUND)
  find_package(PythonInterp REQUIRED)
endif()

get_filename_component(LIBTBX_REFRESH_PY ${CMAKE_CURRENT_LIST_DIR}/../run_libtbx_refresh.py ABSOLUTE)

function(add_libtbx_refresh_command refresh_script)
  # Check that we haven't done this for this project before
  if (TARGET ${PROJECT_NAME}_refresh)
    message(FATAL_ERROR "Asked to create more than one libtbx refresh for the same project ${PROJECT_NAME}")
  endif()
  if (NOT TARGET ${PROJECT_NAME})
    message(FATAL_ERROR "Asked to create libtbx refresh files, but no target named ${PROJECT_NAME}")
  endif()
  # Extract the output parameters from this
  cmake_parse_arguments(TBXR "" "" "OUTPUT" ${ARGN})
  # Add the custom command
  add_custom_command(
    COMMAND ${PYTHON_EXECUTABLE} ${LIBTBX_REFRESH_PY} --root=${CMAKE_SOURCE_DIR} --output=${CMAKE_BINARY_DIR} ${refresh_script}
    OUTPUT ${TBXR_OUTPUT} 
    ${TBXR_UNPARSED_ARGUMENTS})
  # Make a custom target and then tie the parent target to this
  add_custom_target(${PROJECT_NAME}_refresh
    DEPENDS ${TBXR_OUTPUT} )
  add_dependencies(${PROJECT_NAME} ${PROJECT_NAME}_refresh)
endfunction()


# --root=<rootpath> --output=<outpath> <file> 
message("run_libtbx_refresh is at ")


# add_custom_command(OUTPUT output1 [output2 ...]
#                    COMMAND command1 [ARGS] [args1...]
#                    [COMMAND command2 [ARGS] [args2...] ...]
#                    [MAIN_DEPENDENCY depend]
#                    [DEPENDS [depends...]]
#                    [IMPLICIT_DEPENDS <lang1> depend1
#                                     [<lang2> depend2] ...]
#                    [WORKING_DIRECTORY dir]
#                    [COMMENT comment] [VERBATIM] [APPEND])

    # set(options OPTIONAL FAST)
    # set(oneValueArgs DESTINATION RENAME)
    # set(multiValueArgs TARGETS CONFIGURATIONS)
    # cmake_parse_arguments(MY_INSTALL "${options}" "${oneValueArgs}"
    #                       "${multiValueArgs}" ${ARGN} )