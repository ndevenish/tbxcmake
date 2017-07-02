
get_filename_component(LIBTBX_REFRESH_PY ${CMAKE_CURRENT_LIST_DIR}/../run_libtbx_refresh.py ABSOLUTE)

function(add_libtbx_refresh_command refresh_script)
  # Check that we haven't done this for this project before
  if (NOT TARGET Python::Python)
    message(FATAL_ERROR "No python interpreter imported executable Python::Python")
  endif()
  if (TARGET ${PROJECT_NAME}_refresh)
    message(FATAL_ERROR "Asked to create more than one libtbx refresh for the same project ${PROJECT_NAME}")
  endif()
  if (NOT TARGET ${PROJECT_NAME})
    message(FATAL_ERROR "Asked to create libtbx refresh files, but no target named ${PROJECT_NAME}")
  endif()
  # Extract the output parameters from this
  # cmake_parse_arguments(MY_INSTALL "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN} )
  cmake_parse_arguments(TBXR "" "" "OUTPUT" ${ARGN})
  # Add the custom command
  add_custom_command(
    COMMAND Python::Python ${LIBTBX_REFRESH_PY} --root=${CMAKE_SOURCE_DIR} --output=${CMAKE_BINARY_DIR} ${refresh_script}
    OUTPUT ${TBXR_OUTPUT} 
    ${TBXR_UNPARSED_ARGUMENTS})
  # Make a custom target and then tie the parent target to this
  add_custom_target(${PROJECT_NAME}_refresh
    DEPENDS ${TBXR_OUTPUT} )
  add_dependencies(${PROJECT_NAME} ${PROJECT_NAME}_refresh)
endfunction()
