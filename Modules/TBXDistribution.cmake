# Distributes under BSD licence

#.rst:
# TBXDistribution
# ---------------
# Tools for configuring and loading a libtbx-style distribution
#
#
# ::
#   find_libtbx_module(<name> [REQUIRED])
#
# Search the tbx-repositories for a specific named module. If the
# ``REQUIRED`` parameter is specified, then an error is thrown if
# the module can not be found.
#
# ::
#   add_libtbx_module(<name> [INTERFACE])
#                            [[GENERATED_FILES files...] | NO_REFRESH]
#
# Register the current directory as a libtbx module, and read the module
# folder and sources to determine any hard/soft dependencies for the
# module.
#
# A target with the same name as the module will be created. If the
# ``INTERFACE`` option is specified then this will be an interface
# target, otherwise it will be a library of the default library type (as
# specified by :variable:`BUILD_SHARED_LIBS`).
#
# If there is a ``libtbx_refresh.py`` file that generates source files for
# inclusion as part of the build, then the output files must be specified
# as a ``GENERATED_FILES`` argument. These files are passed to the
# ``add_libtbx_refresh_command` function. If there happens to be a
# ``libtbx_refresh.py`` script but it does not generate files, then you can
# pass the ``NO_REFRESH`` option to suppress the warning.

include(CMakeParseArguments)
include(${CMAKE_CURRENT_LIST_DIR}/JsonParser.cmake)

# Store this location so we know where to look for relative files
set(__TBXDistribution_list_dir ${CMAKE_CURRENT_LIST_DIR})

function(find_libtbx_module name)
  message(WARNING "find_libtbx_module currently does nothing")
endfunction()

function(add_libtbx_module name)
  cmake_parse_arguments(TBX "INTERFACE;NO_REFRESH" "" "GENERATED_FILES" ${ARGN})
  set(TBX_MODULE ${name} PARENT_SCOPE)
  message(STATUS "Registering TBX module ${name}")
  if(TBX_INTERFACE)
    add_library( ${name} INTERFACE )
    message(STATUS "  ${name} is an INTERFACE module")
  else()
    message(STATUS "  ${name} is a LIBRARY module")
    message(WARNING "  Library module not currently coded")

  endif()

  # Look for a libtbx libtbx_refresh
  if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/libtbx_refresh.py)
    if (NOT TBX_GENERATED_FILES)
      if (NOT TBX_NO_REFRESH)
        message(WARNING "TBX Module ${name} has a libtbx_refresh.py, but no generated-file list has been passed. Unknown output.")
      endif()
    else()
      # We've been given a list of files, and also have a generator. Register them.
      add_libtbx_refresh_command(${CMAKE_CURRENT_SOURCE_DIR}/libtbx_refresh.py OUTPUT ${TBX_GENERATED_FILES})
    endif()
  endif()

  # Generate dispatchers for this module
  _generate_libtbx_dispatchers(${name} ${CMAKE_CURRENT_SOURCE_DIR})
endfunction()

# Read the libtbx_config file for a specific <entry> and read into a variable named <entry>.
function(_read_libtbx_config file entry)
  # Read and parse
  file(READ ${file} libtbx_config_contents)
  sbeParseJson(config libtbx_config)
  # Loop over entries to build the list
  foreach(var ${config.${entry}})
    # message("${var} = ${${var}}")
    list(APPEND ${entry} ${config.${entry}_${var}})
  endforeach()
  # Export the variable
  set(${entry} "${${entry}}" PARENT_SCOPE)
endfunction()

# ::
#   _get_libtbx_dispatcher_rename(<file> <default> <output>)
#
# Read a source file and return a list of names of dispatchers for it.
# <file> is the name of the source file to read. <default> is the default
# name if there is no override specifiers in the file. <output> is the
# name of the output variable to put the list of dispatcher names into.
#
# An override specification is an entry in the file somewhere of the form::
#
#   # LIBTBX_SET_DISPATCHER_NAME [some-new-name]
#
# specifying what the script should be named as a dispatcher. There can be
# multiple entries, in which case more than one dispatcher should be generated.
function(_get_libtbx_dispatcher_rename file default output)
  # The regex to extract the dispatcher name override
  set(DISPATCHER_REGEX "[ \\t]*#[ \\t]?LIBTBX_SET_DISPATCHER_NAME[ \\t]+([A-Za-z0-9_.]+)")

  # Find the matches in the file
  file(READ ${file} CONT)
  string(REGEX MATCHALL "${DISPATCHER_REGEX}" matches "${CONT}")

  # This gives us the full text of every match - we only want the matched group
  # so iterate over the list building a new one
  set(dispatcher_names "")
  foreach(match ${matches})
    string (REGEX REPLACE "${DISPATCHER_REGEX}" "\\1" match "${match}")
    # message("Match after replace: ${match}")
    list(APPEND dispatcher_names "${match}")
  endforeach()
  # Use the default if we had none set
  if (NOT dispatcher_names)
    set(dispatcher_names "${default}")
  endif()
  set(${output} "${dispatcher_names}" PARENT_SCOPE)
endfunction()

# ::
#   _write_dispatcher(<destination> <target>)
#
# Determines the type of dispatcher required to call <target> and writes
# it out to <destination>.
function(_write_dispatcher destination target)
  # Template depends on the type of file...
  if (target MATCHES "\\.py$")
    set(dispatcher_template "${__TBXDistribution_list_dir}/../dispatcher.py.template")
  elseif(target MATCHES "\\.sh$")
    set(dispatcher_template "${__TBXDistribution_list_dir}/../dispatcher.sh.template")
  else()
    message(WARNING "Unknown dispatcher type for target ${target}; ignoring")
    return()
  endif()

  configure_file(${dispatcher_template} ${destination})

  # configure_file(${CMAKE_CURRENT_LIST_DIR}/../type_id_eq_h.template
  #              ${CMAKE_BINARY_DIR}/include/boost_adaptbx/type_id_eq.h)
endfunction()

# ::
#   _generate_libtbx_dispatchers(<name> <path>)
#
# Read a libtbx module path and generate dispatchers by reading the
# command_line folder and any additional folders listed in the
# libtbx_config file's "extra_command_line_locations" entry.
#
# <name> is used to create the default dispatcher name - <name>.<target>
#
function(_generate_libtbx_dispatchers name path)
  message("  Generating dispatchers for ${path}")
  # Read the libtbx_config to see if there are any extra locations to search
  set(dispatcher_locations command_line)
  if (EXISTS ${path}/libtbx_config)
    _read_libtbx_config(${path}/libtbx_config extra_command_line_locations)
    list(APPEND dispatcher_locations ${extra_command_line_locations})
  endif()

  # Find potential targets in each of these locations
  foreach(dir ${dispatcher_locations})
    # Find targets in this folder, relative to the module root
    file(GLOB matches LIST_DIRECTORIES false RELATIVE ${path} ${dir}/*.py ${dir}/*.sh)
    # Exclude items from this list that don't match the criteria; A
    # script is a potential dispatcher IF:
    #   - Filename ends with .py or .sh
    #   - NOT __init__.py
    #   - NOT A hidden file e.g. starts with "."
    foreach(file ${matches})
      if (    ${file} MATCHES "^(.*/)?__init__\\.py$"   # __init__.py
          OR  ${file} MATCHES "^(.*/)?\\." )            # hidden files
        continue()
      else()
        list(APPEND dispatcher_targets ${file})
        message("    dispatcher: ${file}")
      endif()
    endforeach()
  endforeach()
  list(LENGTH dispatcher_targets dispatcher_count)
  message(STATUS "  Found ${dispatcher_count} dispatchers")

  # This is where we could filter the dispatcher list further, remove
  # previously-created dispatchers if they no longer exist, things like that.
  # However, since we want to keep this relatively simple for now, just
  # regenerating the build folder seems like it'd be easy enough.

  # Process every dispatcher target we collected
  foreach(target ${dispatcher_targets})
    get_filename_component(target_stripped_name "${target}" NAME)
    # Get the filename without final extension
    string(REGEX REPLACE "\\.[^.]*$" "" target_stripped_name "${target_stripped_name}")
    # Work out if we had any "rename" directives inside the file
    _get_libtbx_dispatcher_rename(${target} "${name}.${target_stripped_name}" dispatcher_names)
    message("  Writing ${target} as ${dispatcher_names}")
    foreach(name ${dispatcher_names})
      # Write this dispatcher
      _write_dispatcher(${CMAKE_BINARY_DIR}/bin/${name} ${path}/${target})
    endforeach()
  endforeach()
endfunction()




