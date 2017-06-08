cmake_minimum_required (VERSION 3.5)
project (Dials)

find_package(Boost REQUIRED COMPONENTS python)
find_package(PythonLibs REQUIRED)

include_directories(${PROJECT_SOURCE_DIR}/..)
include_directories(${PROJECT_SOURCE_DIR}/../cctbx_project/)
include_directories(${PROJECT_SOURCE_DIR}/../../build/include)
include_directories(${PYTHON_INCLUDE_DIRS})



add_subdirectory(algorithms)
add_subdirectory(model)


option(BUILD_SHARED_LIBS "Build all libraries as a shared library" ON)

# to run with existing paths e.g.
# cmake -D BOOST_LIBRARYDIR=/dls/science/users/mep23677/dials-dist/build/lib -D BOOST_INCLUDEDIR=/dls/science/users/mep23677/dials-dist/modules/boost -D PYTHON_LIBRARY=/dls/science/users/mep23677/dials-dist/base/lib/ -D PYTHON_INCLUDE_DIR=/dls/science/users/mep23677/dials-dist/base/include ..
