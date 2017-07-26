# Configures the include/boost_adaptbx/type_id_eq.h file
#
# This appears to encode the size of size_t for.. some reason
# But does so using a custom Sconscript stage instead of e.g. the libtbx_refresh
# mechanism which everything else seems to use for generation. Rather than
# altering the source code (which I want to avoid as much as possible for now),
# this module writes the file.

include(CheckTypeSize)

if(NOT ADAPTBX_SIZET_DEF)
  CHECK_TYPE_SIZE("size_t"              SIZE_SIZE_T)
  CHECK_TYPE_SIZE("unsigned short"      SIZE_US)
  CHECK_TYPE_SIZE("unsigned"            SIZE_U)
  CHECK_TYPE_SIZE("unsigned long"       SIZE_UL)
  CHECK_TYPE_SIZE("unsigned long long"  SIZE_LL)
  # Find which of these match the size_t
  if (${SIZE_SIZE_T} EQUAL ${SIZE_US})
    set(ADAPTBX_SIZET_DEF BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_SHORT )
  elseif (${SIZE_SIZE_T} EQUAL ${SIZE_U})
    set(ADAPTBX_SIZET_DEF BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED )
  elseif (${SIZE_SIZE_T} EQUAL ${SIZE_UL})
    set(ADAPTBX_SIZET_DEF BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_LONG )
  elseif (${SIZE_SIZE_T} EQUAL ${SIZE_LL})
    set(ADAPTBX_SIZET_DEF BOOST_ADAPTBX_TYPE_ID_SIZE_T_EQ_UNSIGNED_LONG_LONG )
  else()
    message(FATAL_ERROR "Couldn't determine size type of size_t")
  endif()

  configure_file(${CMAKE_CURRENT_LIST_DIR}/../type_id_eq_h.template
                 ${CMAKE_BINARY_DIR}/include/boost_adaptbx/type_id_eq.h)
endif()