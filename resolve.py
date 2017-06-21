#!/usr/bin/env python

"""resolve.py

Automatically analyse a build log to determine the input and output targets
of a build process.

Usage: 
  resolve.py [<buildlog>] [--root=<rootpath>]"""
from __future__ import print_function
import itertools
from docopt import docopt, DocoptExit
import shlex
import os
import pickle
from functools import reduce
import operator
import logging
logger = logging.getLogger(__name__)

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
  -o OUT
  -D DEFINITION
  -L LIBDIR
  -l LIB
  -W WARNING
  -f OPTION
  -O OPTIMISE     Choose the optimisation level (0,1,2,3,s)
  -c              Compile and Assemble only, do not link
  -w 
  -s              Remove all symbol table and relocation information from the executable
  --shared
"""

class LogParser(object):
  def __init__(self, filename):
    # Read every gcc
    logger.info("Parsing build log...")
    if os.path.isfile("logparse.pickle"):
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
  def __init__(self, name, module, relative_path, module_root, sources):
    self.name = name
    self.module = module
    self.path = relative_path
    self.module_root = module_root
    self.sources = sources
  @property
  def is_executable(self):
    return not self.name.endswith(".so")
  @property
  def is_test(self):
    return self.is_executable and ("tst" in self.name or "test" in self.name)
  @property
  def is_library(self):
    return self.name.endswith(".so")
  def describe(self):
    """Return a BuildDeps description dictionary"""
    # Make relative source paths
    # import pdb
    # pdb.set_trace()
    # return {"name": self.name, "sources": }


def _build_target_list(logdata):
  targets = []
  for target in logdata.link_targets:
    target_name = target["-o"]
    # Work out the common source directories
    objects = [x for x in logdata.objects if x["-o"] in target["<source>"]]
    sources = list(itertools.chain(*[x["<source>"] for x in objects]))
    source_dirs = set(os.path.dirname(x) for x in sources)
    abs_source_dirs = [x for x in source_dirs if os.path.isabs(x)]
    if len(abs_source_dirs) > 1:
      logger.info("Multiple source dirs for {}: {}".format(target_name, abs_source_dirs))
      common = os.path.dirname(os.path.commonprefix(abs_source_dirs))
      logger.info("  Found common path: {}".format(common))

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
    else:
      module = relative_path.split("/")[0]
    print(module.ljust(20), relative_path)

    targets.append(Target(target_name, module, relative_path, logdata.module_root, sources))
  return targets

class BuildInfo(object):
  def __init__(self, module, path):
    self.module = module
    self.path = path

    self.subdirectories = {}
    self.targets = []

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
      self.subdirectories[subdir] = BuildInfo(module, os.path.join(self.path, subdir))
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
    
        

def ensure_tree_path(path, tree):
  if not path[0] in tree.children:
    tree[path[0]] = TreeNode()


if __name__ == "__main__":
  options = docopt(__doc__)
  logging.basicConfig(level=logging.INFO)
  logdata = LogParser(options["<buildlog>"] or "buildbuild.log")

  # Extract target metadata
  targets = _build_target_list(logdata)
  
  # Now we have a list of targets, along with their basic directory
  # Make a directory tree for every target
  root = BuildInfo(None, "")

  for target in targets:
    # Get hold of the dependency information object to build
    info = root.get_path(target.path)
    info.targets.append(target)

  print (list(root.collect()))
  import pdb
  pdb.set_trace()

