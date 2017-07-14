# ccp4io/libccp4/fortran/....
# ccp4_diskio_f.c
# ccp4_general.c
# ccp4_general_f.c
# ccp4_parser_f.c
# ccp4_program.c
# ccp4_unitcell_f.c
# cmaplib_f.c
# cmtzlib_f.c
# csymlib_f.c
# library_f.c


function(rewrite_printf source dest)
  if(${source} IS_NEWER_THAN ${CMAKE_BINARY_DIR}/${dest})
    message("File ${source} is newer than ${CMAKE_BINARY_DIR}/${dest}")
    message("Writing ${dest}")
    file(READ ${source} TEXT)
    # STRING(REGEX REPLACE ";" "\\\;" TEXT "${TEXT}")
    string(REGEX REPLACE "([^A-Za-z0-9_])printf([^A-Za-z0-9_])" "\\1ccp4io_printf\\2" TEXT "${TEXT}")
    string(REGEX REPLACE "([^A-Za-z0-9_])fprintf([^A-Za-z0-9_])" "\\1ccp4io_fprintf\\2" TEXT "${TEXT}")
    string(CONCAT TEXT "#include <ccp4io_adaptbx/printf_wrappers.h>\n" "${TEXT}")
    file(WRITE ${CMAKE_BINARY_DIR}/${dest} "${TEXT}")
  endif()
endfunction()

function(rewrite_csymlib source dest)
  if(${source} IS_NEWER_THAN ${CMAKE_BINARY_DIR}/${dest})
    message("Writing ${dest}")
    file(READ ${source} TEXT)
    string(REGEX REPLACE "static int reported_syminfo = 0" "static int reported_syminfo = 1" TEXT "${TEXT}")
    file(WRITE ${CMAKE_BINARY_DIR}/${dest} "${TEXT}")
  endif()
endfunction()

# open(op.join(build_ccp4io_adaptbx, "csymlib.c"), "w").write(
#   open(op.join(path_lib_src, "csymlib.c")).read()
#     .replace(
#       "",
#       ""))