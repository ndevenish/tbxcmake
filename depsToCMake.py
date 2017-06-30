#!/usr/bin/env python

"""Processes a dependency yaml tree into CMakeLists files.

Usage:
  deptsToCMake.py <depfile>
"""
from __future__ import print_function
from docopt import docopt
import sys
import os
import yaml
from StringIO import StringIO
import fnmatch
import itertools

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
  data["todo"] = data.get("todo", None)
  return data

def find_headers(path, exclusions=[]):
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
  def __init__(self, filename, parent=None):
    self.filename = filename
    self.directory = os.path.abspath(os.path.dirname(filename))
    self.output = StringIO()
    self.macros = {
      "python_library": "add_python_library ( {name}\n    SOURCES {sources} )",
      "library": "add_library ( {name}\n    SOURCES {sources} )",
      "source_join": "\n            "}
    self.project = parent.project if parent else None

  def _find_project_headers(self, data):
    """Accumulate all header files in this tree, excluding:
      - specified subdirectories
      - sources specified by shared libraries or tests"""
    exclusions = {os.path.normpath(os.path.join(self.directory, dir)) for dir in data["subdirectories"]} \
               | set(itertools.chain(*[target["sources"] for target in itertools.chain(data["shared_libraries"], data["tests"]) ]))
    all_headers = find_headers(self.directory, exclusions)
    return {x[len(self.directory)+1:] for x in all_headers}

  def process(self):
    """Read and process the dependency file"""
    print("Loading {}".format(self.filename))
    data = _normalise_yaml(yaml.load(open(self.filename)))
    
    # Update the project name and emit a change if we need to
    data_project = data.get("project", self.project)
    if not data_project == self.project:
      self.project = data_project
      print("project({})\n".format(self.project), file=self.output)
      # Emit an interface library IFF we don't have a library named the same thing
      if not any(x for x in data["shared_libraries"] if x["name"] == self.project):
        print("add_library( {name} INTERFACE )\n".format(name=data_project), file=self.output)

    # Add to project, header files that aren't owned by targets or children
    headers = self._find_project_headers(data)
    if headers:
      print("target_sources( {project}\n  INTERFACE\n{headers}\n)\n".format(
        project=self.project, headers="\n".join("    ${{CMAKE_CURRENT_SOURCE_DIR}}/{}".format(x) for x in _nice_file_sorting(headers))),
        file=self.output)

    # Add any todo warning
    if data["todo"]:
        print("message(WARNING \"{}\")\n".format(data["todo"]), file=self.output)

    # Emit library targets if we have any
    for library in data["shared_libraries"]:
      library_type = "python_library" if "boost_python" in library["dependencies"] else "library"

      if library_type == "python_library":
        library["dependencies"] = list(set(library["dependencies"])-{"boost_python"})
      else:
        print(library)
      sources = self.macros["source_join"].join(library["sources"])
      print(self.macros[library_type].format(name=library["name"], sources=sources),
        file=self.output)
      if library["dependencies"]:
        print("target_link_libraries({name} {deps})".format(
          name=library["name"], deps=" ".join(library["dependencies"])),
        file=self.output)
      if library["todo"]:
        print("message(WARNING \"{}\")".format(library["todo"]), file=self.output)
      print(file=self.output)

    # Emit subdirectory traversal
    for dir in sorted(data["subdirectories"]):
      print("add_subdirectory({})".format(dir), file=self.output)

    # Write the target CMakeLists
    if data["generate"]:
      open(os.path.join(self.directory, "CMakeLists.txt"), 'w').write(self.output.getvalue())

    # Now descend into each of the child processes
    for dir in data["subdirectories"]:
      FileProcessor(os.path.join(self.directory, dir, "AutoBuildDeps.yaml"), parent=self).process()


if __name__ == "__main__":
  options = docopt(__doc__)
  rootFile = options["<depfile>"]
  FileProcessor(rootFile).process()