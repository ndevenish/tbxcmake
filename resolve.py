#!/usr/bin/env python
# coding: utf-8

"""
Automatically analyse a build log to determine the input and output targets
of a build process.

Usage: 
  resolve.py [<buildlog>] [--root=<rootpath>] [--target=<target>] [--name=]

Options:
  -h --help          Show this screen.
  --name=<name>      Filename for writing to target [default: AutoBuildDeps.yaml]
  --target=<target>  Write build dependency files to a target directory
  --root=<rootpath>  Explicitly constrain the dependency tree to a particular root
"""

from __future__ import print_function
import itertools
from docopt import docopt, DocoptExit
import shlex
import os
import pickle
from functools import reduce
import operator
import yaml
import logging
logger = logging.getLogger(__name__)

def makedirs(path):
  if not os.path.isdir(path):
    os.makedirs(path)

# all_modules = {
#   "iota"            : "/home/xgkkp/dials_dist/modules/cctbx_project/iota"
#   "prime"           : "/home/xgkkp/dials_dist/modules/cctbx_project/prime"
#   "xia2"            : "/home/xgkkp/dials_dist/modules/xia2"
#   "dials"           : "/home/xgkkp/dials_dist/modules/dials"
#   "xfel"            : "/home/xgkkp/dials_dist/modules/cctbx_project/xfel"
#   "simtbx"          : "/home/xgkkp/dials_dist/modules/cctbx_project/simtbx"
#   "cma_es"          : "/home/xgkkp/dials_dist/modules/cctbx_project/cma_es"
#   "crys3d"          : "/home/xgkkp/dials_dist/modules/cctbx_project/crys3d"
#   "rstbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/rstbx"
#   "spotfinder"      : "/home/xgkkp/dials_dist/modules/cctbx_project/spotfinder"
#   "annlib"          : "/home/xgkkp/dials_dist/modules/annlib"
#   "annlib_adaptbx"  : "/home/xgkkp/dials_dist/modules/annlib_adaptbx"
#   "wxtbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/wxtbx"
#   "gltbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/gltbx"
#   "mmtbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/mmtbx"
#   "iotbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/iotbx"
#   "ccp4io"          : "/home/xgkkp/dials_dist/modules/ccp4io"
#   "ccp4io_adaptbx"  : "/home/xgkkp/dials_dist/modules/ccp4io_adaptbx"
#   "dxtbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/dxtbx"
#   "smtbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/smtbx"
#   "ucif"            : "/home/xgkkp/dials_dist/modules/cctbx_project/ucif"
#   "cbflib"          : "/home/xgkkp/dials_dist/modules/cbflib"
#   "cbflib_adaptbx"  : "/home/xgkkp/dials_dist/modules/cctbx_project/cbflib_adaptbx"
#   "cctbx"           : "/home/xgkkp/dials_dist/modules/cctbx_project/cctbx"
#   "scitbx"          : "/home/xgkkp/dials_dist/modules/cctbx_project/scitbx"
#   "fable"           : "/home/xgkkp/dials_dist/modules/cctbx_project/fable"
#   "omptbx"          : "/home/xgkkp/dials_dist/modules/cctbx_project/omptbx"
#   "boost"           : "/home/xgkkp/dials_dist/modules/boost"
#   "boost_adaptbx"   : "/home/xgkkp/dials_dist/modules/cctbx_project/boost_adaptbx"
#   "tbxx"            : "/home/xgkkp/dials_dist/modules/cctbx_project/tbxx"
#   "chiltbx"         : "/home/xgkkp/dials_dist/modules/cctbx_project/chiltbx"
#   "libtbx"          : "/home/xgkkp/dials_dist/modules/cctbx_project/libtbx"
# }

# GCC Usage for parsing command line arguments
gcc_usage = """Usage:
  g++ [options] [-o OUT] [-I INCLUDEDIR]... [-l LIB]... [-L LIBDIR]... [-D DEFINITION]... [-w] [-W WARNING]... [-f OPTION]... [<source>]...

Options:
  -I INCLUDEDIR   Add an include search path
  -o OUT          The output file
  -D DEFINITION   Compile definitions to use for this
  -L LIBDIR       Paths to search for linked libraries
  -l LIB          Extra library targets to link
  -W WARNING      Warning settings
  -f OPTION       Compiler option switches
  -O OPTIMISE     Choose the optimisation level (0,1,2,3,s)
  -c              Compile and Assemble only, do not link
  -w              Inhibit all warning messages
  -s              Remove all symbol table and relocation information from the executable
  --shared        Produce a shared object which can then be linked
"""

class LogParser(object):
  def __init__(self, filename):
    # Read every gcc
    logger.info("Parsing build log...")
    if os.path.isfile("logparse.pickle") and os.path.getmtime("logparse.pickle") > os.path.getmtime(filename):
      gcc = pickle.load(open("logparse.pickle", "rb"))
    else:
      gcc_lines = [x.strip() for x in open(filename) if x.startswith("g++") or x.startswith("gcc")]
      gcc = []
      for line in gcc_lines:
        try:
          line = line.replace(" -shared ", " --shared ")
          gcc.append(docopt(gcc_usage, argv=shlex.split(line)[1:]))
        except SystemExit:
          logger.error("Error reading ", line)
          raise
      pickle.dump(gcc, open("logparse.pickle", "wb"))
    # Break these down into categories
    self.objects = [x for x in gcc if x["-c"]]
    self.link_targets = [x for x in gcc if not x["-c"]]

    # Used to look at non-abs paths... but these are probably code-generated into build directory
    # # Handle any entries without absolute source paths
    # for entry in [x for x in gcc if not all(os.path.isabs(y) for y in x["<source>"])]:
    #   import pdb
    #   pdb.set_trace()

    # Try to work out the ROOT
    absSources = []
    for compile in [x for x in gcc if x["-c"]]:
      for source in compile["<source>"]:
        if os.path.isabs(source):
          absSources.append(source)
    self.module_root = os.path.commonprefix(absSources)
    assert self.module_root.endswith("/"), "Not handling partial roots atm"
    logger.info("Common root is {}".format(self.module_root))

    # Validate that for every target, we have all the sources as outputs
    for target in self.link_targets:
      for tsource in target["<source>"]:
        assert any(x["-o"] == tsource for x in self.objects), "No source for target"

class Target(object):
  def __init__(self, name, module, relative_path, module_root, sources, libraries):

    self.output_path = os.path.dirname(name)
    if name.endswith(".so"):
      name, extension = os.path.splitext(os.path.basename(name))
    else:
      extension = ""
    if name.startswith("lib"):
      name = name[3:]
    self.name = name
    self.extension = extension
    self.module = module
    self.path = relative_path
    self.module_root = module_root
    self.sources = sources
    self.libraries = libraries
  @property
  def is_executable(self):
    return not self.extension.endswith(".so")
  @property
  def is_test(self):
    return self.is_executable and ("tst" in self.name or "test" in self.name)
  @property
  def is_library(self):
    return self.extension.endswith(".so")
  def describe(self):
    """Return a BuildDeps description dictionary"""

    # Work out our full path
    fullPath = os.path.join(self.module_root, self.path)
    # Find hard-coded sources
    localSources = [x[len(fullPath)+1:] for x in self.sources if x.startswith(fullPath)]
    
    # Basic, common info
    info = {"name": self.name}
    if localSources:
      info["sources"] = localSources
    if self.output_path:
      info["location"] = self.output_path
    
    # Generated sources are in the build directory
    specialSources = [x for x in self.sources if not x.startswith(fullPath)]
    if specialSources:
      warning = "Module {} has special sources: {}".format(self.name, specialSources)
      print(warning)
      info["todo"] = warning
    
    # Handle what's linked to
    if self.libraries:
      info["dependencies"] = list(self.libraries)
    return info




def _build_target_list(logdata):
  # List of all modules and their path
  modules = {}
  # List of targets
  targets = []
  for target in logdata.link_targets:
    target_name = target["-o"]
    # Work out the common source directories
    objects = [x for x in logdata.objects if x["-o"] in target["<source>"]]
    sources = list(itertools.chain(*[x["<source>"] for x in objects]))
    source_dirs = set(os.path.dirname(x) for x in sources)
    abs_source_dirs = [x for x in source_dirs if os.path.isabs(x)]
    if len(abs_source_dirs) > 1:
      # In this case, there is sources from more than one directory contributing. This
      # is okay unless the common path is at the module level
      common = os.path.dirname(os.path.commonprefix(abs_source_dirs))
      logger.info("Multiple source dirs for {}:\n{}".format(target_name, "\n".join("  - " + x for x in abs_source_dirs)))
      logger.info(" Found common path => {}".format(common))
      abs_source_dirs = [common]

      if os.path.normpath(common) == os.path.normpath(logdata.module_root):
        logger.warning("Target {} has no common source path except ROOT, skipping".format(target_name))
        continue
    elif len(abs_source_dirs) == 0:
      # Need to manually resolve these targets with all sources generated in the
      # build directory - technically we could read from the relative and look 
      # for a matching module, but only a single example exists
      logger.warning("Target {} has only generated sources and needs to be included manually. Skipping.".format(target_name))
      continue

    # Work out the base-relative path and thus modulename
    relative_path = abs_source_dirs[0][len(logdata.module_root):]
    if relative_path.startswith("cctbx_project/"):
      module = relative_path[len("cctbx_project/"):].split("/")[0]
      modules[module] = os.path.join("cctbx_project", module)
    else:
      module = relative_path.split("/")[0]
      modules[module] = module
    print(module.ljust(20), relative_path)

    libs = set(target["-l"]) - {"m"}
    targets.append(Target(target_name, module, relative_path, logdata.module_root, sources, libraries=libs))
  return targets, modules

class BuildInfo(object):
  def __init__(self, module, path, parent=None, generate=True):
    self.module = module
    self.path = path
    self.parent = parent

    self.subdirectories = {}
    self.targets = []
    self._generate = generate

  def get_path(self, path):
    """Get, or create, a build object for the requested path"""
    if isinstance(path, str):
      path = os.path.normpath(path).split("/")
    if not path:
      return self
    # Otherwise, we want a subdirectory of this one
    subdir = path[0]
    
    if not subdir in self.subdirectories:
      # handle module assignment
      module = self.module
      if not self.module and not subdir == "cctbx_project":
        module = subdir
      self.subdirectories[subdir] = BuildInfo(module, os.path.join(self.path, subdir), self)
    return self.subdirectories[subdir].get_path(path[1:])

  def collect(self):
    """Collect a list of all build objects"""
    for sub in self.subdirectories.values():
      for x in sub.collect():
        yield x
    yield self

  def __repr__(self):
    return "<BuildInfo {}>".format(self.path)

  def generate(self):
    """Generate the BuildDeps file, as a dictionary to yaml-write"""
    data = {}
    if not self._generate:
      data["generate"] = self._generate

    if self.parent and self.module != self.parent.module:
      data["project"] = self.module
    if self.subdirectories:
      data["subdirectories"] = self.subdirectories.keys()

    for target in self.targets:
      if target.is_library:
        targetlist = data.get("shared_libraries", [])
        data["shared_libraries"] = targetlist
      elif target.is_executable and target.is_test:
        targetlist = data.get("tests", [])
        data["tests"] = targetlist
      elif target.is_executable:
        targetlist = data.get("programs", [])
        data["programs"] = targetlist
      else:
        raise RuntimeError("Cannot classify target")
        
      targetlist.append(target.describe())
    return data

if __name__ == "__main__":
  options = docopt(__doc__)
  logging.basicConfig(level=logging.INFO)
  logdata = LogParser(options["<buildlog>"] or "buildbuild.log")

  if options["--target"]:
    if not os.path.isdir(options["--target"]):
      logger.error("Error: Target must be a valid directory")
    options["--target"] = os.path.abspath(options["--target"])

  # Extract target metadata
  targets, module_paths = _build_target_list(logdata)
  
  # Make a list of all dependencies that AREN'T targets
  all_dependencies = set(itertools.chain(*[x.libraries for x in targets]))
  external_dependencies = all_dependencies - {x.name for x in targets}
  print("External dependencies: ", external_dependencies)

  # Find any targets that match the name of a module
  misdir_modlibs = [x for x in targets if x.name == x.module and not x.path == module_paths[x.module]]
  # If any of these don't match their directory name, then promote them up until they do
  if misdir_modlibs:
    print("Found module-named libraries outside of expected path:", ", ".join(x.name for x in misdir_modlibs))
    for target in misdir_modlibs:
      target.path = module_paths[target.module]

  # import pdb
  # pdb.set_trace()

  # Now we have a list of targets, along with their basic directory
  # Make a directory tree for every target
  root = BuildInfo(None, "", generate=False)

  for target in targets:
    # Get hold of the dependency information object to build
    info = root.get_path(target.path)
    info.targets.append(target)

  max_len_path = reduce(lambda acc, val: max(acc, len(val.path)), root.collect(), 0)

  for (path, info) in [(x.path, x) for x in root.collect()]:
    print(path.ljust(max_len_path), info)

    if options["--target"]:
      targetPath = os.path.join(options["--target"], path, options["--name"])
      print("  ->", targetPath)
      makedirs(os.path.dirname(targetPath))
      with open(targetPath, 'w') as depfile:
        depfile.write(yaml.dump(info.generate()))

