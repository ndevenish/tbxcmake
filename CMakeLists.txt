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

# Link to cctbx
include_directories(
  "/dls/science/users/mep23677/dials-dist/modules/cctbx_project"
  "/dls/science/users/mep23677/dials-dist/build/include"
)

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

add_library(dials INTERFACE)
target_include_directories( dials INTERFACE "${CMAKE_CURRENT_SOURCE_DIR}/.." )

add_subdirectory(algorithms)