cmake_minimum_required(VERSION 3.5 FATAL_ERROR)

project(dials)

option(BUILD_PYTHON_LIBS "Build the python shared libraries" ON)

if (${BUILD_PYTHON_LIBS})
  find_package(PythonInterp REQUIRED)
  find_package(PythonLibs REQUIRED)
  find_package(Boost REQUIRED COMPONENTS python)
  include_directories(${PYTHON_INCLUDE_DIRS})
else()
  find_package(Boost REQUIRED)
endif()

# For now, hardcode links to cctbx
include_directories(
  "/dls/science/users/mep23677/dials-dist/modules/cctbx_project"
  "/dls/science/users/mep23677/dials-dist/build/include"
)

# Convenience macro for setting up python shared libraries
macro(add_dials_python_library name)
  if (BUILD_PYTHON_LIBS)
    add_library(${name} SHARED ${ARGN})
    target_link_libraries(${name} dials Boost::python)
    set_target_properties(${name} PROPERTIES PREFIX "")
  endif()
endmacro()

# Install shared libraries to lib/
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

add_library(dials INTERFACE)
target_include_directories( dials INTERFACE "${CMAKE_CURRENT_SOURCE_DIR}/.." )

add_subdirectory(algorithms)
add_subdirectory(array_family)
add_subdirectory(framework/dftbx)
add_subdirectory(model)
add_subdirectory(nexus)
add_subdirectory(test)
add_subdirectory(util)
add_subdirectory(viewer)


