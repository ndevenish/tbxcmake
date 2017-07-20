#!/usr/bin/env python
# coding: utf-8

"""Processes a dependency yaml tree into CMakeLists files.

Usage:
  depsToCMake.py <depfile> [options] [--target=<target>] [--headers=<root>] [--scan]

Options:
  --target=<target>     Set a root folder for writing CMakeLists (else: source)
  --headers=<root>      Set a search folder for headers (else: target)
  --scan                Scan for headers and add to project library
  --override=<path>     Location to look for custom CMakeLists [default: cmake_templates]
"""

from __future__ import print_function
from docopt import docopt
import sys
import os
import yaml
from StringIO import StringIO
import fnmatch
import itertools
from collections import Counter

# Tells us how to convert internal dependency names to what we need in cmake
EXTERNAL_DEPENDENCY_MAP = {
  "boost_python": "Boost::python",
  "python": "Python::Libs",
  "hdf5": "HDF5::HDF5",
  "hdf5_c": "HDF5::C",
  "tiff": "TIFF::TIFF",
  "GL": "OpenGL::GL",
  "GLU": "OpenGL::GLU",
  "OpenGL": "OpenGL::GL",
  "eigen": "Eigen::Eigen",
  "boost": "Boost::boost",
  "pcre": "PCRE::PCRE"
}

# Dependencies that are optional
OPTIONAL_DEPENDENCIES = {"OpenGL::GL"}

# Having one of these means the others are not necessary
IMPLICIT_DEPENDENCIES = {
  "OpenGL::GLU": {"OpenGL::GL"},
  "boost_python": {"python"}
}

# Global target count tracker to avoid conflicts in names
target_count = Counter()

def dependency_name(name):
  """Given a dependency name, gets the 'real' target name"""
  if name in EXTERNAL_DEPENDENCY_MAP:
    return EXTERNAL_DEPENDENCY_MAP[name]
  return name

def target_name(name):
  """Given a name, returns a unique name to use for CMake target purposes"""
  target_count[name] += 1
  count = target_count[name]
  if count == 1:
    return name
  return name + "_{}".format(count)

_TEMPLATE_DIR = None
def find_template(path):
  """Given a path, looks for a pre-prepared template file for that path.
  
  Returns None if there is no template. If the found template is empty, this
  indicates that there should be no output file written (quick hack)
  """
  if _TEMPLATE_DIR is None:
    return None
  template_path = os.path.join(_TEMPLATE_DIR, path)
  if not os.path.isfile(template_path):
    return None
  source = open(template_path).read()
  return source

def _normalise_yaml_target(data):
  data["sources"] = data.get("sources", [])
  data["generated_sources"] = data.get("generated_sources", [])
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
  data["python_extensions"] = [_normalise_yaml_target(x) for x in data.get("python_extensions", [])]
  data["programs"] = [_normalise_yaml_target(x) for x in data.get("programs", [])]
  data["tests"] = [_normalise_yaml_target(x) for x in data.get("tests", [])]
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
  def __init__(self, filename, target_dir=None, headers_dir=None, parent=None, scan=True, override=None):
    self.parent = parent
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
      "python_library": "add_python_library ( {name}\n            {sources} )",
      "library":        "add_library ( {name} {STATIC}\n            {sources} )",
      "source_join": "\n            ",
      "libtbx_refresh": "add_libtbx_refresh_command( ${{CMAKE_CURRENT_SOURCE_DIR}}/{filename}\n     OUTPUT {sources} )",
      "add_generated": "add_generated_sources({target}\n    SOURCES {sources} )"
      }
    self.project = parent.project if parent else None

  @property
  def root_parent(self):
    root = self
    while root.parent:
      root = root.parent
    return root

  def _find_project_headers(self, data):
    """Accumulate all header files in this tree, excluding:
      - specified subdirectories
      - sources specified by shared libraries or tests"""
    exclusions = {os.path.normpath(os.path.join(self.headers_directory, dir)) for dir in data["subdirectories"]} \
               | set(itertools.chain(*[target["sources"] for target in itertools.chain(data["shared_libraries"], data["tests"]) ]))
    all_headers = find_headers(self.headers_directory, exclusions)
    return {x[len(self.headers_directory)+1:] for x in all_headers}

  def _process_dependencies(self, deps):
    """Runs any processing on name, cross-links etc for dependencies"""
    # If we have an alternate name for any dependencies, use that
    deps = {dependency_name(x) for x in deps}

    # Remove any implicit dependencies
    deps = deps - set(itertools.chain(*[IMPLICIT_DEPENDENCIES[x] for x in deps if x in IMPLICIT_DEPENDENCIES]))
    return deps

  def _emit_library(self, library):
      library_type = "python_library" if library["python_extension"] else "library"

      STATIC = "STATIC" if library["static"] else ""

      if library_type == "python_library":
        library["dependencies"] = list(set(library["dependencies"])-{"boost_python"})
      
      # Unless the name matches the project, add the project as a dependency.
      # Python libraries have this done automatically.
      if library["name"] != self.project and not library_type == "python_library" and self.project:
        library["dependencies"].insert(0, self.project)

      sources = self.macros["source_join"].join(library["sources"])
      generated_sources = self.macros["source_join"].join(library["generated_sources"])

      indent = ""
      libtext = StringIO()

      print(self.macros[library_type].format(name=library["name"], sources=sources, STATIC=STATIC),
        file=libtext)
      if generated_sources:
        print(self.macros["add_generated"].format(target=library["name"], sources=generated_sources), file=libtext)
      
      # Calculate any dependencies
      if library["dependencies"]:
        indent = ""
        deps = self._process_dependencies(set(library["dependencies"]))
        # Work out any optional dependencies so we can test them
        optional_deps = [dependency_name(x) for x in deps if x in OPTIONAL_DEPENDENCIES]
        print("target_link_libraries({name} {deps})".format(
          name=library["name"], deps=" ".join(deps)),
        file=libtext)

      # If this is our project library, set the include folder
      include_paths = library.get("include_paths", [])
      if library["name"] == self.project and not include_paths:
        include_paths.append("${CMAKE_CURRENT_SOURCE_DIR}/..")
      include_paths = [self._resolve_include_path(x) for x in include_paths]

      if include_paths:
        print("target_include_directories({name} PUBLIC {incs})\n".format(name=library["name"], incs=" ".join(include_paths)), file=libtext)

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
    if path.startswith("!"):
      path = path[1:]
    if path.startswith("#build"):
      return "${CMAKE_BINARY_DIR}" + path[len("#build"):]
    elif path.startswith("#base"):
      return "${CMAKE_SOURCE_DIR}" + path[len("#base"):]
    elif os.path.isabs(path):
      return path
    return os.path.join("${CMAKE_CURRENT_SOURCE_DIR}", path)

  def _emit_interface_library(self, name, data):
    include = "${CMAKE_CURRENT_SOURCE_DIR}/.."
    if "project_include_path" in data:
      include = " ".join([self._resolve_include_path(x) for x in data["project_include_path"]])
    print("add_library( {name} INTERFACE )".format(name=self.project), file=self.output)
    print("target_include_directories({name} INTERFACE {include})\n".format(name=self.project, include=include), file=self.output)

  def _emit_program(self, data):
    """Emits the cmake code to build an executable. Returns the target name"""
    name = data["name"]
    target = target_name(data["name"])
    generated_sources = data["generated_sources"]

    print("add_executable({name} {sources})".format(name=target, 
      sources=" ".join(itertools.chain(data["sources"], generated_sources))), file=self.output)
    deps = self._process_dependencies(set(data["dependencies"]))
    # If name != target we collided with another, so set the name explicitly
    if name != target:
      print('set_target_properties({target} PROPERTIES OUTPUT_NAME "{name}")'.format(target=target, name=name), file=self.output)
    if generated_sources:
        print(self.macros["add_generated"].format(target=target, sources=generated_sources), file=self.output)
    if deps:
      print("target_link_libraries({name} {deps})".format(name=target, deps=" ".join(deps)), file=self.output)
    return target
      
  def _emit_test(self, data):
    target = self._emit_program(data)
    print("add_test(NAME {name} COMMAND {target})".format(name=target, target=target), file=self.output)


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
      lib["python_extension"] = False
    for lib in data["static_libraries"]:
      lib["static"] = True
      lib["python_extension"] = False
    for lib in data["python_extensions"]:
      lib["static"] = False
      lib["python_extension"] = True

    library_targets = list(data["shared_libraries"]) + list(data["static_libraries"]) + list(data["python_extensions"])
    
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

    for program in list(data["programs"]):
      self._emit_program(program)
      print(file=self.output)

    for test in list(data["tests"]):
      self._emit_test(test)
      print(file=self.output)


    # Emit subdirectory traversal
    for dir in sorted(data["subdirectories"]):
      print("add_subdirectory({})".format(dir), file=self.output)

    # Write the target CMakeLists
    output_filename = "CMakeLists.txt"
    if not data["generate"]:
      output_filename = "autogen_CMakeLists.txt"
    output_file = os.path.join(self.target_directory, output_filename)

    # Explicitly grab the output data (so we can overwrite if needed)
    output_data = self.output.getvalue()

    # Calculate the relative path for templating
    relative_file = os.path.relpath(output_file, start=self.root_parent.target_directory)
    template_data = find_template(relative_file)
    # If we got ANY template data, then use that instead (even if empty)
    if template_data is not None:
      output_data = template_data

    # Don't write empty files
    if output_data.strip():
      # If the folder doesn't exist, make it
      if not os.path.isdir(self.target_directory):
        os.makedirs(self.target_directory)
      open(output_file, 'w').write(output_data)

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
  if options["--override"]:
    assert os.path.isdir(options["--override"])
    _TEMPLATE_DIR = options["--override"]
  FileProcessor(rootFile, target_dir=options["--target"], headers_dir=options["--headers"], scan=options["--scan"], override=options["--override"]).process()

