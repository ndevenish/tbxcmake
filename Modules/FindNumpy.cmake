# Find the native numpy includes
# This module defines
#  NUMPY_INCLUDE_DIR, where to find numpy/arrayobject.h, etc.
#  NUMPY_FOUND, If false, do not try to use numpy headers.
#
# And creates the imported target Python::Numpy

include(FindPackageHandleStandardArgs)

if (NOT NUMPY_INCLUDE_DIRS)
    exec_program ("${PYTHON_EXECUTABLE}"
      ARGS "-c 'import numpy; print numpy.get_include()'"
      OUTPUT_VARIABLE NUMPY_INCLUDE_DIRS
      RETURN_VALUE NUMPY_NOT_FOUND)

    set(NUMPY_INCLUDE_DIRS ${NUMPY_INCLUDE_DIRS} CACHE PATH "Numpy include path")

    find_package_handle_standard_args(NUMPY DEFAULT_MSG ${NUMPY_INCLUDE_DIRS})

    if (NOT NUMPY_FIND_QUIETLY)
      message(STATUS "Found numpy: ${NUMPY_INCLUDE_DIRS}")
    endif()

    mark_as_advanced (NUMPY_INCLUDE_DIRS)
endif()

# If we found, or were given, an include directory
if (NOT TARGET Python::Numpy AND NUMPY_INCLUDE_DIRS)
  add_library(Python::Numpy INTERFACE IMPORTED)
  set_target_properties(Python::Numpy PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${PYTHON_INCLUDE_DIRS}")
endif()