# - Find PCRE library and PCREposix extension
# Find the native PCRE includes and library
# This module defines
#  PCRE_INCLUDE_DIRS, where to find pcre.h, Set when
#                     PCRE_INCLUDE_DIR is found.
#  PCRE_LIBRARIES, libraries to link against to use PCRE.
#  PCRE_ROOT_DIR, The base directory to search for PCRE.
#                 This can also be an environment variable.
#  PCRE_FOUND, If false, do not try to use PCRE.
#
# also defined, but not for general use are
#  PCRE_LIBRARY, where to find the PCRE library.

#=============================================================================
# Copyright 2011 Blender Foundation.
#
# Distributed under the OSI-approved BSD License (the "License");
# see accompanying file Copyright.txt for details.
#
# This software is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the License for more information.
#=============================================================================

# If PCRE_ROOT_DIR was defined in the environment, use it.
IF(NOT PCRE_ROOT_DIR AND NOT $ENV{PCRE_ROOT_DIR} STREQUAL "")
  SET(PCRE_ROOT_DIR $ENV{PCRE_ROOT_DIR})
ENDIF()

SET(_pcre_SEARCH_DIRS
  ${PCRE_ROOT_DIR}
  /usr/local
  /sw # Fink
  /opt/local # DarwinPorts
  /opt/csw # Blastwave
)

FIND_PATH(PCRE_INCLUDE_DIR pcre.h
  HINTS
    ${_pcre_SEARCH_DIRS}
  PATH_SUFFIXES
    include
    include
)

FIND_LIBRARY(PCRE_LIBRARY
  NAMES
    pcre
  HINTS
    ${_pcre_SEARCH_DIRS}
  PATH_SUFFIXES
    lib64 lib
  )

FIND_PATH(PCREPOSIX_INCLUDE_DIR pcreposix.h
  HINTS
    ${_pcre_SEARCH_DIRS}
  PATH_SUFFIXES
    include
    include
)
FIND_LIBRARY(PCREPOSIX_LIBRARY 
  NAMES 
    pcreposix libpcreposix
  HINTS
    ${_pcre_SEARCH_DIRS}
  PATH_SUFFIXES
    lib64 lib
  )

# handle the QUIETLY and REQUIRED arguments and set PCRE_FOUND to TRUE if 
# all listed variables are TRUE
INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(PCRE      DEFAULT_MSG PCRE_LIBRARY      PCRE_INCLUDE_DIR)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(PCREPOSIX DEFAULT_MSG PCREPOSIX_LIBRARY PCREPOSIX_INCLUDE_DIR)


IF(PCRE_FOUND)
  SET(PCRE_LIBRARIES ${PCRE_LIBRARY})
  SET(PCRE_INCLUDE_DIRS ${PCRE_INCLUDE_DIR})

  add_library(PCRE::PCRE UNKNOWN IMPORTED)
  set_target_properties(PCRE::PCRE PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${PCRE_INCLUDE_DIRS}"
    IMPORTED_LOCATION "${PCRE_LIBRARY}")
  message("Found PCRE: ${PCRE_LIBRARY}, ${PCRE_INCLUDE_DIRS}")
endif()

if(PCREPOSIX_FOUND)
  SET(PCRE_LIBRARIES ${PCRE_LIBRARY})
  SET(PCREPOSIX_INCLUDE_DIRS ${PCREPOSIX_INCLUDE_DIR})

  add_library(PCRE::POSIX UNKNOWN IMPORTED)
  set_target_properties(PCRE::POSIX PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${PCREPOSIX_INCLUDE_DIRS}"
    IMPORTED_LOCATION "${PCREPOSIX_LIBRARY}")

  message("Found PCREPosix: ${PCREPOSIX_LIBRARY}, ${PCREPOSIX_INCLUDE_DIRS}")
ENDIF()

MARK_AS_ADVANCED(
  PCRE_INCLUDE_DIR
  PCRE_LIBRARY
  PCREPOSIX_INCLUDE_DIR
  PCREPOSIX_LIBRARY
)
