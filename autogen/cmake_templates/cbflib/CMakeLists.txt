project(cbf)

add_library ( cbf STATIC
            src/cbf.c
            src/cbf_alloc.c
            src/cbf_ascii.c
            src/cbf_binary.c
            src/cbf_byte_offset.c
            src/cbf_canonical.c
            src/cbf_codes.c
            src/cbf_compress.c
            src/cbf_context.c
            src/cbf_file.c
            src/cbf_lex.c
            src/cbf_nibble_offset.c
            src/cbf_packed.c
            src/cbf_predictor.c
            src/cbf_read_binary.c
            src/cbf_read_mime.c
            src/cbf_simple.c
            src/cbf_string.c
            src/cbf_stx.c
            src/cbf_tree.c
            src/cbf_uncompressed.c
            src/cbf_write.c
            src/cbf_write_binary.c
            src/cbf_ws.c
            src/img.c
            src/md5c.c
            ../cctbx_project/cbflib_adaptbx/detectors/buffer_based_service.cpp
            ../cctbx_project/cbflib_adaptbx/detectors/cbf_adaptor.cpp
            ../cctbx_project/cbflib_adaptbx/detectors/cbf_byte_offset_optimized.cpp
            ../cctbx_project/cbflib_adaptbx/detectors/mar_adaptor.cpp )
target_include_directories(cbf PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
# Needed because cbf_adaptor.cpp, cbflib_ext includes "include/img.h"
target_include_directories(cbf PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/.)

# The cbf extra files require scitbx
target_link_libraries(cbf PUBLIC HDF5::HDF5 scitbx)

# Conditionally include PCRE, or disable it
if (TARGET PCRE::POSIX)
  target_link_libraries(cbf PUBLIC PCRE::POSIX)
else()
  target_compile_definitions(cbf PRIVATE CBF_NO_REGEX)
endif()

add_library ( _pycbf 
            pycbf/pycbf_wrap.c
            src/cbf_airy_disk.c )
target_link_libraries(_pycbf cbf Python::Libs HDF5::C)

