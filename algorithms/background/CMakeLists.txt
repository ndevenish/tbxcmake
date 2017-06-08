
add_library(dials_algorithms_background  
			helpers.cc modeller.cc radial_average.cc helpers.h modeller.h radial_average.h
      # //boost_python/background_ext.cc boost_python/helpers.cc boost_python/modeller_ext.cc

      glm/creator.cc glm/robust_poisson_mean.cc glm/creator.h glm/robust_poisson_mean.h
      # glm/boost_python/ext.cc
			)
# target_link_libraries(background ${Boost_LIBRARIES})


add_library(dials_algorithms_background_ext SHARED boost_python/helpers.cc boost_python/background_ext.cc)
target_link_libraries(dials_algorithms_background_ext dials_algorithms_background Boost::python)

add_library(dials_algorithms_background_modeller_ext SHARED boost_python/modeller_ext.cc)
target_link_libraries(dials_algorithms_background_modeller_ext dials_algorithms_background Boost::python)

add_library(dials_algorithms_background_glm_ext SHARED glm/boost_python/ext.cc)
target_link_libraries(dials_algorithms_background_glm_ext dials_algorithms_background Boost::python)