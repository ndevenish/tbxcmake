# Possibly useful parameters to pass to CMake:
#   CMAKE_PREFIX_PATH   The root to search for libraries
#   PYTHON_EXECUTABLE=  The Python executable to use
#   EIGEN_ROOT=         The path to the eigen sources
#   BOOST_ROOT=         The path to Boost
#   HDF5_ROOT=          The path to the HDF5 install

cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
# Boost imported target and cmake_parse_arguments were added in 3.5
# 3.8 added interface targets to OpenGL
cmake_policy(SET CMP0074 NEW) # Searching _ROOT paths by default
cmake_policy(SET CMP0094 NEW) # Finds first active python version rather than highest

project(Dials)


# Add the included modules
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")
include(LibTBXRefresher)

option(BUILD_PYTHON_LIBS "Build the python shared libraries"    ON)
option(BUILD_SHARED_LIBS "Build libraries as shared libraries"  ON)
option(USE_OPENMP        "Use OpenMP"                           OFF)

# Generate more intuitive navigation structure for IDEs
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Deliberately constrain to C++98 - but allow user to override
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 98)
endif()

# Generate compile_commands.json
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Ensure that we can't accidentally find system boost if given a custom root
if (BOOST_ROOT)
  set(Boost_NO_SYSTEM_PATHS ON)
endif()

if (${BUILD_PYTHON_LIBS})
  # Add python interpreter as an imported executable
  find_package(Python REQUIRED COMPONENTS Interpreter Development NumPy)
  message("Found python interpreter ${Python_VERSION}: ${Python_EXECUTABLE}")
  #add_executable(Python::Python IMPORTED)
  #set_target_properties(Python::Python PROPERTIES
  #  IMPORTED_LOCATION ${PYTHON_EXECUTABLE})

  # Get the include from python
  #exec_program(${PYTHON_EXECUTABLE}
  #  ARGS -c "\"from distutils.sysconfig import get_python_inc; print(get_python_inc())\""
  #  OUTPUT_VARIABLE PYTHON_INCLUDE_DIRS
  #  RETURN_VALUE    RUN_RETURN)
  #if (${RUN_RETURN})
  #  message(FATAL_ERROR "Could not determine python include path from python executable")
  #endif()

  # Add python libraries as an imported library
  #find_package(PythonLibs REQUIRED)
  #message("Python Include path: ${PYTHON_INCLUDE_DIRS}")

  #find_package(Numpy REQUIRED)

  # Create an imported interface that just lets us access the header files
  # add_library(Python::Headers SHARED IMPORTED)
  # set_target_properties(Python::Headers PROPERTIES
  #   INTERFACE_INCLUDE_DIRECTORIES ${PYTHON_INCLUDE_DIRS})

  find_package(Boost REQUIRED QUIET)
  # Boost 1.67 added version suffixes to library names for python.
  # CMake 3.11 added support for this, backported so that older boost will
  # still work (I think), but this obviously doesn't work for earlier versions
  if( "${CMAKE_VERSION}" VERSION_GREATER_EQUAL "3.11.4" AND "${Boost_VERSION}" VERSION_GREATER_EQUAL "1.67")
  #  set(PYTHON_BOOST_SUFFIX "${Python_VERSION_MAJOR}${Python_VERSION_MINOR}")
  endif()

  # Find boost python libraries
  find_package(Boost COMPONENTS python${PYTHON_BOOST_SUFFIX} numpy${PYTHON_BOOST_SUFFIX} thread filesystem REQUIRED)
  include_directories(${Python_INCLUDE_DIRS} ${Python_NumPy_INCLUDE_DIRS})

  # Name targets for python without version suffixes for CMake version tolerance
  if("${CMAKE_VERSION}" VERSION_GREATER_EQUAL "3.11.4" AND NOT TARGET Boost::python )
    add_library(Boost::python INTERFACE IMPORTED)
    set_target_properties(Boost::python PROPERTIES
      INTERFACE_LINK_LIBRARIES      Boost::python${PYTHON_BOOST_SUFFIX} )
    add_library(Boost::numpy INTERFACE IMPORTED)
    set_target_properties(Boost::numpy PROPERTIES
      INTERFACE_LINK_LIBRARIES      Boost::numpy${PYTHON_BOOST_SUFFIX} )
  endif()

  # Because of link differences between linux and macOS - namely that by
  # default macOS wants to resolve all symbols at link-time instead of
  # at run-time, we need to change something when building on macOS. One
  # solution is setting "-undefined dynamic_lookup" on the link command -
  # this solves the problem, but also delays any errors from accidentally
  # leaving out symbols until runtime. Setting -weak_library allows the
  # symbols to be resolved at link-time, but doesn't seem to set up any
  # hard tie to the specific library version. Therefore, it's not quite
  # so important that CMake finds the exact correct python library.
  # EXTRA NOTE: There seem to be a problem with doing this when an rpath
  #             is set. So switching to undefined dynamic_lookup so we
  #             can get something working
  # if(APPLE)
  #   # find_package(PythonLibs REQUIRED)
  #   set_property( TARGET Boost::python${PYTHON_BOOST_SUFFIX}
  #                 APPEND
  #                 # PROPERTY INTERFACE_LINK_LIBRARIES "-Wl,-weak_library,${Python_LIBRARIES}")
  #                 PROPERTY INTERFACE_LINK_LIBRARIES "-Wl,-undefined,dynamic_lookup")
  #   # message("Python lib for weak linking: ${Python_LIBRARIES}")
  # elseif(WIN32)
  #   # Windows, however, requires the python27.lib library linked in
  #   find_package(PythonLibs REQUIRED)
  #   set_property( TARGET Boost::python${PYTHON_BOOST_SUFFIX}
  #                 APPEND
  #                 PROPERTY INTERFACE_LINK_LIBRARIES "${Python_LIBRARIES}")
  #   message("Python library for hard linking: ${Python_LIBRARIES}")
  # endif()
  # Add python as a link property
  # set_property( TARGET Boost::python
  #               APPEND
  #               PROPERTY IMPORTED_LINK_INTERFACE_LIBRARIES Python::Headers)
  # Add a definition to the numpy module, for scitbx. Possibly better
  # moved closer to the only use (numpy_bridge) but that requires some
  # more autogenerated functionality
  set_property( TARGET Boost::numpy${PYTHON_BOOST_SUFFIX}
                APPEND
                PROPERTY INTERFACE_COMPILE_DEFINITIONS SCITBX_HAVE_NUMPY_INCLUDE)

  # # Call find_package for boost again - to get optional dependencies
  # if(USE_THREADS)
  #   # find_package(Boost COMPONENTS thread)
  # endif()
else()
  find_package(Boost REQUIRED COMPONENTS thread)
endif()
message("Found Boost headers at: ${Boost_INCLUDE_DIRS}")
message("      Boost-python  at: ${Boost_PYTHON${PYTHON_BOOST_SUFFIX}_LIBRARY}")
message("      Boost-numpy   at: ${Boost_NUMPY${PYTHON_BOOST_SUFFIX}_LIBRARY}")

#find_package(msgpack REQUIRED)
find_package(TIFF REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(OpenGL)
find_package(PNG)
find_package(GTest)

# Used by CBFlib, if present
#find_package(PCRE)
# As a hack: Define the no-regex flag here
add_library(PCRE::PCRE INTERFACE IMPORTED)
add_library(PCRE::POSIX INTERFACE IMPORTED)
set_target_properties(PCRE::PCRE PROPERTIES
  INTERFACE_COMPILE_DEFINITIONS "CBF_NO_REGEX")
#CBF_NO_REGEX

# Add HDF5
find_package(HDF5 REQUIRED COMPONENTS C)
#find_package(HDF5 COMPONENTS HL)
add_library(HDF5::HDF5 INTERFACE IMPORTED)
message("Original HDF5 defs: ${HDF5_DEFINITIONS}")
string(REGEX REPLACE "(^|\\s|;)-D" ";" HDF5_DEFINITIONS_CLEAN    "${HDF5_DEFINITIONS}")
string(REGEX REPLACE "(^|\\s|;)-D" ";" HDF5_C_DEFINITIONS_CLEAN  "${HDF5_C_DEFINITIONS}")
string(REGEX REPLACE "(^|\\s|;)-D" ";" HDF5_C_HL_DEFINITIONS_CLEAN  "${HDF5_C_HL_DEFINITIONS}")

set_target_properties(HDF5::HDF5 PROPERTIES
  INTERFACE_INCLUDE_DIRECTORIES "${HDF5_INCLUDE_DIRS}"
  INTERFACE_COMPILE_DEFINITIONS "${HDF5_DEFINITIONS_CLEAN}"
  INTERFACE_LINK_LIBRARIES      "${HDF5_LIBRARIES}" )
add_library(HDF5::C INTERFACE IMPORTED)
set_target_properties(HDF5::C PROPERTIES
  INTERFACE_INCLUDE_DIRECTORIES "${HDF5_C_INCLUDE_DIRS}"
  INTERFACE_COMPILE_DEFINITIONS "${HDF5_C_DEFINITIONS_CLEAN}"
  INTERFACE_LINK_LIBRARIES      "${HDF5_C_LIBRARIES};HDF5::HDF5")
add_dependencies(HDF5::C HDF5::HDF5)
# HDF5::HL is a very optional dependency, used in (disabled) nexus and cppxfel
if (TARGET HDF5::HL)
  add_library(HDF5::HL INTERFACE IMPORTED)
  set_target_properties(HDF5::HL PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${HDF5_C_HL_INCLUDE_DIRS}"
    INTERFACE_COMPILE_DEFINITIONS "${HDF5_C_HL_DEFINITIONS_CLEAN}"
    INTERFACE_LINK_LIBRARIES      "${HDF5_C_HL_LIBRARIES};HDF5::HDF5")
  add_dependencies(HDF5::HL HDF5::C)
endif()

message("HDF5:")
message("      i: ${HDF5_INCLUDE_DIRS}")
message("      D: ${HDF5_DEFINITIONS_CLEAN}")
message("      l: ${HDF5_LIBRARIES}")
message(" CXX: i: ${HDF5_CXX_INCLUDE_DIRS}")
message("      D: ${HDF5_CXX_DEFINITIONS}")
message("      l: ${HDF5_CXX_LIBRARIES}")
message("   C: i: ${HDF5_C_INCLUDE_DIRS}")
message("      D: ${HDF5_C_DEFINITIONS_CLEAN}")
message("      l: ${HDF5_C_LIBRARIES}")
message("C_HL: i: ${HDF5_C_HL_INCLUDE_DIRS}")
message("      D: ${HDF5_C_HL_DEFINITIONS}")
message("      l: ${HDF5_C_HL_LIBRARIES}")
message("CXXHL:i: ${HDF5_CXX_HL_INCLUDE_DIRS}")
message("      D: ${HDF5_CXX_HL_DEFINITIONS_CLEAN}")
message("      l: ${HDF5_CXX_HL_LIBRARIES}")

if (${USE_OPENMP})
  # If we asked for OpenMP, then we'd better have it
  find_package(OpenMP REQUIRED)
endif()

# If the compiler supports the flag, disable multichar warnings (used in boost::mpl::string)
include(CheckCXXCompilerFlag)
check_cxx_compiler_flag("-Wno-multichar" MULTICHAR_FLAG)
if(MULTICHAR_FLAG)
  add_compile_options("-Wno-multichar")
endif()

# Always do diagnostic colouring e.g. inside ninja. Makes prettier.
if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
  add_compile_options (-fdiagnostics-color=always)
elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
  add_compile_options (-fcolor-diagnostics)
elseif ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "AppleClang")
  add_compile_options (-fcolor-diagnostics)
endif ()

enable_testing()

function(set_project_relative_folder target)
  string(REGEX REPLACE "^${PROJECT_SOURCE_DIR}/?" "" PROJECT_RELATIVE_DIR ${CMAKE_CURRENT_LIST_DIR})
  # message("In Project ${PROJECT_SOURCE_DIR}")
  # message("           ${CMAKE_CURRENT_LIST_DIR}")
  # message("         = ${PROJECT_RELATIVE_DIR}")
  set_target_properties (${name} PROPERTIES FOLDER "${PROJECT_NAME}/${PROJECT_RELATIVE_DIR}")
  # message("           Setting relative folder for ${target} to ${PROJECT_RELATIVE_DIR}")
endfunction()

# Convenience function for setting up python shared libraries
# Usage: add_python_library( <name> SOURCES <file> [<file>]... )
function(add_python_library name)

  # add_library(${name} MODULE ${ARGN})
  Python_add_library(${name} ${ARGN})

  # Tie to current project if we've set one
  if (NOT ${PROJECT_NAME} MATCHES "^Project$")
    # Add to a project meta-target
    if(NOT TARGET ${PROJECT_NAME}_meta)
      add_custom_target(${PROJECT_NAME}_meta)
      set_target_properties (${PROJECT_NAME}_meta PROPERTIES FOLDER meta)
    endif()
    add_dependencies(${PROJECT_NAME}_meta ${name})

    # If the project name is also a target, then add it as a dependency
    if (TARGET ${PROJECT_NAME})
      target_link_libraries(${name} PRIVATE ${PROJECT_NAME})
    endif()

    set_project_relative_folder(${name})
  endif()

  target_link_libraries(${name} PUBLIC Boost::python )
  # set_target_properties(${name} PROPERTIES PREFIX "")

  install(TARGETS ${name} DESTINATION ${Python_SITEARCH})
endfunction()

# Add generated sources to a target
function(add_generated_sources target )
  foreach(f ${ARGN})
    set(ABS_SRC "${CMAKE_BINARY_DIR}/${f}" )
    set_source_files_properties("${ABS_SRC}" PROPERTIES GENERATED TRUE)
    target_sources(${target} PRIVATE ${ABS_SRC})
  endforeach()
endfunction()

# FUNCTION(PREPEND var prefix)
#    SET(listVar "")
#    FOREACH(f ${ARGN})
#       LIST(APPEND listVar "${prefix}/${f}")
#    ENDFOREACH(f)
#    SET(${var} "${listVar}" PARENT_SCOPE)
# ENDFUNCTION(PREPEND)

# Include the three standard 'everything' directories - module, cctbx_project and build include
include_directories(${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/cctbx_project ${CMAKE_BINARY_DIR}/include)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY  "${CMAKE_BINARY_DIR}/lib")

# Write the Boost adaptbx size_t file - this is specially generated
include(BoostAdapTBXSizing)
# Do the CCP4IOGenration steps
include(CCP4IOGeneration)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/ccp4_diskio_f.c ccp4io_adaptbx/ccp4_diskio_f.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/ccp4/ccp4_general.c ccp4io_adaptbx/ccp4_general.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/ccp4_general_f.c ccp4io_adaptbx/ccp4_general_f.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/ccp4_parser_f.c ccp4io_adaptbx/ccp4_parser_f.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/ccp4/ccp4_program.c ccp4io_adaptbx/ccp4_program.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/ccp4_unitcell_f.c ccp4io_adaptbx/ccp4_unitcell_f.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/cmaplib_f.c ccp4io_adaptbx/cmaplib_f.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/cmtzlib_f.c ccp4io_adaptbx/cmtzlib_f.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/csymlib_f.c ccp4io_adaptbx/csymlib_f.c)
rewrite_printf(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/fortran/library_f.c ccp4io_adaptbx/library_f.c)
rewrite_csymlib(${CMAKE_SOURCE_DIR}/ccp4io/libccp4/ccp4/csymlib.c ccp4io_adaptbx/csymlib.c)

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(TBXDistribution)

include(autogen_CMakeLists.txt)

# add_custom_target( dials.find_spots
#   DEPENDS dials_algorithms_image_threshold_ext
#           dxtbx_imageset_ext
#           dxtbx_format_image_ext
#           dxtbx_ext
#           scitbx_array_family_flex_ext
#           dials_model_data_ext 
# dxtbx_model_ext
# cctbx_array_family_flex_ext
# scitbx_array_family_shared_ext
# cctbx_uctbx_ext
# cctbx_sgtbx_ext
# cctbx_orientation_ext
# scitbx_math_ext
# scitbx_linalg_ext
# _pycbf
# boost_rational_ext
# boost_python_meta_ext 
# boost_optional_ext std_pair_ext 
# boost_adaptbx_graph_ext
# dials_array_family_flex_ext
# scitbx_stl_set_ext scitbx_stl_vector_ext scitbx_stl_map_ext scitbx_random_ext
# dials_algorithms_spot_finding_ext 
# dials_util_ext )

# Write the libtbx environment file
write_libtbx_env()

