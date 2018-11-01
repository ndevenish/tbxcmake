# Find the native numpy includes
# This module defines
#  NUMPY_INCLUDE_DIR, where to find numpy/arrayobject.h, etc.
#  NUMPY_FOUND, If false, do not try to use numpy headers.
#
# And creates the imported target Python::Numpy

include(FindPackageHandleStandardArgs)

if (NOT NUMPY_INCLUDE_DIR)
    execute_process(
      COMMAND "${PYTHON_EXECUTABLE}"
        -c "import numpy; print numpy.get_include().strip()"
      OUTPUT_VARIABLE NUMPY_INCLUDE_DIR
      RESULT_VARIABLE NUMPY_NOT_FOUND)
    STRING(STRIP "${NUMPY_INCLUDE_DIR}" NUMPY_INCLUDE_DIR)

    if(NUMPY_NOT_FOUND)
        set(NUMPY_INCLUDE_DIR NUMPY-NOTFOUND)
    endif()
    unset(NUMPY_NOT_FOUND)

    set(NUMPY_INCLUDE_DIR ${NUMPY_INCLUDE_DIR} CACHE PATH "Numpy include path")

    mark_as_advanced (NUMPY_INCLUDE_DIR)
endif()

find_package_handle_standard_args(NUMPY DEFAULT_MSG NUMPY_INCLUDE_DIR)

# If we found, or were given, an include directory
if (NOT TARGET Python::Numpy AND NUMPY_INCLUDE_DIR)
  add_library(Python::Numpy INTERFACE IMPORTED)
  set_target_properties(Python::Numpy PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${NUMPY_INCLUDE_DIR}")
endif()
