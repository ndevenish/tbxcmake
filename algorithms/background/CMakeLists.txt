
target_sources( dials
    INTERFACE
        "${CMAKE_CURRENT_SOURCE_DIR}/glm/creator.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/glm/robust_poisson_mean.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/gmodel/creator.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/gmodel/model.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/gmodel/pixel_filter.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/gmodel/polar_transform.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/gmodel/robust_estimator.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/helpers.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/median/creator.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/modeller.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/radial_average.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/creator.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/modeller.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/mosflm_outlier_rejector.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/normal_outlier_rejector.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/nsigma_outlier_rejector.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/outlier_rejector.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/truncated_outlier_rejector.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/simple/tukey_outlier_rejector.h"
)

macro(add_dials_python_library name)
  if (BUILD_PYTHON_LIBS)
    add_library(${name} SHARED ${ARGN})
    target_link_libraries(${name} dials Boost::python)
    set_target_properties(${name} PROPERTIES PREFIX "")
  endif()
endmacro()

add_dials_python_library(dials_algorithms_background_ext 
  boost_python/helpers.cc boost_python/background_ext.cc )

add_dials_python_library(dials_algorithms_background_modeller_ext
  boost_python/modeller_ext.cc )

add_dials_python_library( dials_algorithms_background_simple_ext 
  simple/boost_python/outlier_rejector.cc simple/boost_python/modeller.cc simple/boost_python/creator.cc simple/boost_python/background_simple_ext.cc )

add_dials_python_library( dials_algorithms_background_glm_ext
  glm/boost_python/ext.cc )

add_dials_python_library( dials_algorithms_background_median_ext 
  median/boost_python/ext.cc )

add_dials_python_library( dials_algorithms_background_gmodel_ext
  gmodel/boost_python/ext.cc )
