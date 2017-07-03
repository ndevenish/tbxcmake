#!/usr/bin/env python
# coding: utf-8

"""Processes a dependency yaml tree into CMakeLists files.

Usage:
  depsToCMake.py <depfile> [--target=<target>] [--headers=<root>] [--scan]

Options:
  --target=<target>     Set a root folder for writing CMakeLists (else: source)
  --headers=<root>      Set a search folder for headers (else: target)
  --scan                Scan for headers and add to project library
"""
from __future__ import print_function
from docopt import docopt
import sys
import os
import yaml
from StringIO import StringIO
import fnmatch
import itertools

EXTERNAL_DEPENDENCY_MAP = {
  # ['cbf', 'boost_python', 'hdf5', 'tiff', 'ann', 'ccp4io', 'GL', 'GLU']
  "boost_python": "Boost::python",
  "hdf5": "HDF5::CXX",
  "hdf5_c": "HDF5::C",
  "tiff": "TIFF::TIFF",
  "GL": "OpenGL::GL",
  "GLU": "OpenGL::GLU"
}

# Dependencies that are optional
OPTIONAL_DEPENDENCIES = {"OpenGL::GLU"}

# Having one of these means the others are not necessary
IMPLICIT_DEPENDENCIES = {
  "GLU": {"GL"},
}

def target_name(name):
  """Given a dependency name, gets the 'real' target name"""
  if name in EXTERNAL_DEPENDENCY_MAP:
    return EXTERNAL_DEPENDENCY_MAP[name]
  return name

def _normalise_yaml_target(data):
  data["sources"] = data.get("sources", [])
  assert "name" in data
  data["location"] = data.get("location", None)
  data["todo"] = data.get("todo", None)
  data["dependencies"] = data.get("dependencies", [])
  if isinstance(data["dependencies"], str):
    data["dependencies"] = data["dependencies"].split()
  return data
  
def _normalise_yaml(data):
  "Alter the raw yaml-read data so that we have an expected structure"
  data["generate"] = data.get("generate", True)
  data["subdirectories"] = data.get("subdirectories", [])
  data["tests"] = data.get("tests", [])
  data["shared_libraries"] = [_normalise_yaml_target(x) for x in data.get("shared_libraries", [])]
  data["static_libraries"] = [_normalise_yaml_target(x) for x in data.get("static_libraries", [])]
  data["todo"] = data.get("todo", None)
  return data

def find_headers(path, exclusions=[]):
  print("Looking in {} for headers".format(path))
  matches = []
  for root, dirnames, filenames in os.walk(path):
    # Filter this so we don't go into exclusions
    for dir in list(dirnames):
      if os.path.join(root, dir) in exclusions:
        dirnames.remove(dir)
    for filename in fnmatch.filter(filenames, '*.h'):
      fullName = os.path.join(root, filename)
      if not fullName in exclusions:
        matches.append(fullName)
  return matches

def _nice_file_sorting(files):
  "Sort a list of files by directory, then file within directory"
  return sorted(files, key=lambda x: (os.path.dirname(x), os.path.basename(x)))

class FileProcessor(object):
  def __init__(self, filename, target_dir=None, headers_dir=None, parent=None, scan=True):
    self.scan = scan
    self.filename = filename
    self.source_directory = os.path.abspath(os.path.dirname(filename))
    if target_dir is None:
      self.target_directory = self.source_directory
    else:
      self.target_directory = os.path.abspath(target_dir)
    if headers_dir is None:
      self.headers_directory = self.target_directory
    else:
      self.headers_directory = os.path.abspath(headers_dir)

    self.output = StringIO()
    self.macros = {
      "python_library": "add_python_library ( {name}\n    SOURCES {sources} )",
      "library":        "add_library ( {name} {STATIC}\n            {sources} )",
      "source_join": "\n            ",
      "libtbx_refresh": "add_libtbx_refresh_command( ${{CMAKE_CURRENT_SOURCE_DIR}}/{filename}\n     OUTPUT {sources} )"}
    self.project = parent.project if parent else None

  def _find_project_headers(self, data):
    """Accumulate all header files in this tree, excluding:
      - specified subdirectories
      - sources specified by shared libraries or tests"""
    exclusions = {os.path.normpath(os.path.join(self.headers_directory, dir)) for dir in data["subdirectories"]} \
               | set(itertools.chain(*[target["sources"] for target in itertools.chain(data["shared_libraries"], data["tests"]) ]))
    all_headers = find_headers(self.headers_directory, exclusions)
    return {x[len(self.headers_directory)+1:] for x in all_headers}

  def _emit_library(self, library):
      library_type = "python_library" if "boost_python" in library["dependencies"] else "library"

      STATIC = "STATIC" if library["static"] else ""

      if library_type == "python_library":
        library["dependencies"] = list(set(library["dependencies"])-{"boost_python"})
      
      # Unless the name matches the project, add the project as a dependency.
      # Python libraries have this done automatically.
      if library["name"] != self.project and not library_type == "python_library" and self.project:
        library["dependencies"].insert(0, self.project)

      sources = self.macros["source_join"].join(library["sources"])


      indent = ""
      libtext = StringIO()

      print(self.macros[library_type].format(name=library["name"], sources=sources, STATIC=STATIC),
        file=libtext)
      
      # Calculate any dependencies
      if library["dependencies"]:
        indent = ""
        deps = set(library["dependencies"])
        # Remove any implicit dependencies
        deps = deps - set(itertools.chain(*[IMPLICIT_DEPENDENCIES[x] for x in library["dependencies"] if x in IMPLICIT_DEPENDENCIES]))
        # If we have an alternate name for any dependencies, use that
        deps = [target_name(x) for x in library["dependencies"]]
        # Work out any optional dependencies so we can test them
        optional_deps = [target_name(x) for x in deps if x in OPTIONAL_DEPENDENCIES]
        print("target_link_libraries({name} {deps})".format(
          name=library["name"], deps=" ".join(deps)),
        file=libtext)

      # If this is our project library, set the include folder
      include_paths = library.get("include_paths", [])
      if library["name"] == self.project and not include_paths:
        include_paths.append("${CMAKE_CURRENT_SOURCE_DIR}/..")
      
      if include_paths:
        print("target_include_directories({name} PUBLIC {incs})\n".format(name=self.project, incs=" ".join(include_paths)), file=libtext)

      # IF we have optional dependencies, add the if() wrappers
      if library["dependencies"] and optional_deps:
        for index, dep in enumerate(optional_deps):
          print("{}if(TARGET {})".format("  "*index, dep), file=self.output)
        indent = "  "*len(optional_deps)
      
      # Reformat the main library adding with an indent for the option depth
      print("\n".join([indent + x for x in libtext.getvalue().splitlines()]), file=self.output)

      # Unwrap the optional dependencies with endif()
      if library["dependencies"] and optional_deps:
        for index, dep in reversed(list(enumerate(optional_deps))):
          print("{}endif()".format("  "*index, dep), file=self.output)

      if library["todo"]:
        print("message(WARNING \"{}\")".format(library["todo"]), file=self.output)
      print(file=self.output)

  def _emit_libtbx_refresh(self, refresh_list):
    # Run the libtbx-refreshing generation if we have any
    # if "libtbx_refresh" in data:
    sources = self.macros["source_join"].join(os.path.join("${CMAKE_BINARY_DIR}", x) for x in refresh_list)
    print(self.macros["libtbx_refresh"].format(filename="libtbx_refresh.py", sources=sources), file=self.output)
    print(file=self.output)

  def _resolve_include_path(self, path):
    """Takes an include path specification and turns into an absolute expression"""
    if path.startswith("#build"):
      return "${CMAKE_BINARY_DIR}" + path[len("#build"):]
    elif os.path.isabs(path):
      return path
    return os.path.join("${CMAKE_CURRENT_SOURCE_DIR}", path)

  def _emit_interface_library(self, name, data):
    include = "${CMAKE_CURRENT_SOURCE_DIR}/.."
    if "project_include_path" in data:
      include = " ".join([self._resolve_include_path(x) for x in data["project_include_path"]])
    print("add_library( {name} INTERFACE )".format(name=self.project), file=self.output)
    print("target_include_directories({name} INTERFACE {include})\n".format(name=self.project, include=include), file=self.output)

  def process(self):
    """Read and process the dependency file"""
    print("Loading {}".format(self.filename))
    data = _normalise_yaml(yaml.load(open(self.filename)))
    
    # Update the project name and emit a change if we need to
    data_project = data.get("project", self.project)
    is_module_root = not data_project == self.project
    self.project = data_project

    # Find the module library if it's a real one
    for lib in data["shared_libraries"]:
      lib["static"] = False
    for lib in data["static_libraries"]:
      lib["static"] = True
    library_targets = list(data["shared_libraries"]) + list(data["static_libraries"])
    
    project_lib = next(iter(x for x in library_targets if is_module_root and x["name"] == data_project), None)
    if project_lib:
      library_targets.remove(project_lib)

    # If we are a module root, then we might need to emit an interface library
    if is_module_root:
      self.project = data_project
      print("project({})\n".format(self.project), file=self.output)
      # Emit an interface library IFF we don't have a library named the same thing
      if project_lib:
        self._emit_library(project_lib)
      else:
        self._emit_interface_library(self.project, data)

    # Add to project, header files that aren't owned by targets or children
    # BUT don't bother searching if we haven't got a project
    if data["generate"] and self.project and self.scan:
      headers = self._find_project_headers(data)
      if headers:
        print("target_sources( {project}\n  INTERFACE\n{headers}\n)\n".format(
          project=self.project, headers="\n".join("    ${{CMAKE_CURRENT_SOURCE_DIR}}/{}".format(x) for x in _nice_file_sorting(headers))),
          file=self.output)

    # Add any todo warning
    if data["todo"]:
        print("message(WARNING \"{}\")\n".format(data["todo"]), file=self.output)

    # Emit libtbx BEFORE libraries, if we have 
    if "libtbx_refresh" in data:
      self._emit_libtbx_refresh(data["libtbx_refresh"])

    # Emit any other library targets
    for library in library_targets:
      self._emit_library(library)

    # Emit subdirectory traversal
    for dir in sorted(data["subdirectories"]):
      print("add_subdirectory({})".format(dir), file=self.output)

    # Write the target CMakeLists
    output_filename = "CMakeLists.txt"
    if not data["generate"]:
      output_filename = "autogen_CMakeLists.txt"

    # If the folder doesn't exist, make it
    if not os.path.isdir(self.target_directory):
      os.makedirs(self.target_directory)
    open(os.path.join(self.target_directory, output_filename), 'w').write(self.output.getvalue())

    # Now descend into each of the child processes
    for dir in data["subdirectories"]:
      FileProcessor(
        filename=os.path.join(self.source_directory, dir, "AutoBuildDeps.yaml"), 
        target_dir=os.path.join(self.target_directory, dir),
        headers_dir=os.path.join(self.headers_directory, dir),
        parent=self,
        scan=self.scan).process()


if __name__ == "__main__":
  options = docopt(__doc__)
  rootFile = options["<depfile>"]
  if options["--target"]:
    # If it exists, it must be a directory
    assert os.path.isdir(options["--target"]) or not os.path.exists(options["--target"]), "Target exists but is not a directory"
  if options["--headers"]:
    assert os.path.isdir(options["--headers"]), "Headers path must exist"
  FileProcessor(rootFile, target_dir=options["--target"], headers_dir=options["--headers"], scan=options["--scan"]).process()

