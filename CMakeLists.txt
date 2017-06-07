cmake_minimum_required (VERSION 3.2)
project (Dials)

find_package(Boost REQUIRED COMPONENTS python)
find_package(PythonLibs REQUIRED)

include_directories(${PROJECT_SOURCE_DIR}/..)
include_directories(${PROJECT_SOURCE_DIR}/../cctbx_project/)
include_directories(${PROJECT_SOURCE_DIR}/../../build/include)

add_subdirectory(algorithms)