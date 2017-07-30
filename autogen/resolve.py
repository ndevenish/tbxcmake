#!/usr/bin/env python
# coding: utf-8

"""
Automatically analyse a build log to determine the input and output targets
of a build process.

Usage: 
  resolve.py <buildlog> [<overrides>] [options] [--root=<rootpath>] [--target=<target>] [--name=<name>]

Options:
  -h --help          Show this screen.
  --name=<name>      Filename for writing to target [default: AutoBuildDeps.yaml]
  --target=<target>  Write build dependency files to a target directory
  --root=<rootpath>  Explicitly constrain the dependency tree to a particular root
  --allinone         Generate one dependency file with nested subdirectory data
"""
#   --autogen=<file>   File to use for autogen information [default: Autogen.yaml]

from __future__ import print_function
import itertools
from docopt import docopt, DocoptExit
import shlex
import os
import pickle
from functools import reduce
import operator
import yaml
import re
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
  g++ [options] [-o OUT] [-I INCLUDEDIR]... [-l LIB]... [-L LIBDIR]... [-D DEFINITION]... [-w] [-W WARNING]... [-f OPTION]... [<source>]... [--framework=<NAME>]...

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
  --undefined=<TREAT>  Specifies how undefined symbols are to be treated.
  --bundle        Produce a mach-o bundle that has file type MH_BUNDLE.
  --dylib         Produce a mach-o shared library that has file type MH_DYLIB.
  --nostartfiles Do not use the standard system startup files when linking.
  --Wl=<ARG>      Pass the comma separated arguments in args to the linker.
  --framework=<NAME> This option tells the linker to search for `name.framework/name' the framework search path.
"""
ar_usage = """Usage:
  ar <mode> <archive> <source>...
"""
ld_usage = """Usage:
  ld [options] [-o OUT] [-l LIB]... [<source>]... [--framework=<NAME>]...

Options:
  -o OUT          The output file
  -l LIB          Extra library targets to link
  --dynamic       The default.  Implied by -dylib, -bundle, or -execute
  -m              Don't treat multiple definitions as an error.  This is no longer supported. This option is obsolete.
  -r              Merges object files to produce another mach-o object file with file type MH_OBJECT
  -d              Force definition of common symbols.  That is, transform tentative definitions into real definitions.
  --bind_at_load  Sets a bit in the mach header of the resulting binary which tells dyld to bind all symbols when the binary is loaded, rather than lazily.
  --framework=<NAME> This option tells the linker to search for `name.framework/name' the framework search path.
"""

# GCC arguments to replace -ARG with --ARG
gcc_short_to_long = {"bundle", "dylib", "shared", "undefined", "nostartfiles", "framework"}
ld_short_to_long = {"dynamic", "bind_at_load"}

class LogParser(object):
  def __init__(self, filename):
    # Read every gcc
    logger.info("Parsing build log...")
    if os.path.isfile("logparse.pickle") and os.path.getmtime("logparse.pickle") > os.path.getmtime(filename):
      gcc, ar = pickle.load(open("logparse.pickle", "rb"))
    else:
      # Extract everything we recognise as a command
      gcc_lines = []
      ar_lines = []
      ld_lines = []
      for line in open(filename):
        firstPart = next(iter(line.split()), None)
        if firstPart is None:
          continue
        command = os.path.basename(firstPart)
        # import pdb
        # pdb.set_trace()
        if command in {"g++", "c++", "gcc", "cc"}:
          gcc_lines.append(line.strip())
        # On e.g. mac we can have direct calls to ld
        if command == "ld":
          ld_lines.append(line.strip())
        if command == "ar":
          ar_lines.append(line.strip())

      ar = []
      gcc = []
      for line in gcc_lines:
        
        try:
          # Quick fix for replacing with following space
          line = line + " "
          for directive in gcc_short_to_long:
            line = line.replace(" -"+directive+" ", " --"+directive+" ")
          line = line.replace("--undefined ", "--undefined=")
          line = line.replace("--framework ", "--framework=")
          line = line.replace("-Wl,", "--Wl=")
          
          gcc.append(docopt(gcc_usage, argv=shlex.split(line)[1:]))

        except SystemExit:
          logger.error("Error reading:" + line)
          raise
      for line in ld_lines:
        try:
          # Quick fix for replacing with following space
          line = line + " "
          for directive in ld_short_to_long:
            line = line.replace(" -"+directive+" ", " --"+directive+" ")          
          line = line.replace("--framework ", "--framework=")

          # Just pretend that this was a gcc invocation
          ldopt = docopt(ld_usage, argv=shlex.split(line)[1:])
          ldopt["-c"] = False
          ldopt["-D"] = []
          gcc.append(ldopt)
        except SystemExit:
          logger.error("Error reading:" + line)
          raise

      for line in ar_lines:
        try:
          entry = docopt(ar_usage, argv=shlex.split(line)[1:])
        except SystemExit:
          logger.error("Error docopt reading: " + line)
          raise
        assert entry["<mode>"] == "rc", "Unknown ar command"
        del entry["<mode>"]
        entry["-o"] = entry["<archive>"]
        del entry["<archive>"]
        entry["-l"] = []
        entry["--framework"] = []
        ar.append(entry)
      pickle.dump((gcc, ar), open("logparse.pickle", "wb"))

    # Break these down into categories
    self.objects = [x for x in gcc if x["-c"]]
    self.link_targets = [x for x in gcc if not x["-c"]]
    self.link_targets.extend(ar)

    definitions = set(itertools.chain(*[x["-D"] for x in gcc if x["-D"]]))
    print("All definitions: ", definitions)
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
        assert any(x["-o"] == tsource for x in itertools.chain(self.objects, self.link_targets)), "No source for target {}".format(tsource)


class Target(object):
  def __init__(self, name, module, relative_path, module_root, sources, libraries):

    self.output_path = os.path.dirname(name)
    if name.endswith(".so") or name.endswith(".a"):
      name, extension = os.path.splitext(os.path.basename(name))
    else:
      name = os.path.basename(name)
      extension = ""
    
    if name.startswith("lib"):
      name = name[3:]
      self.prefix = "lib"
    else:
      self.prefix = ""

    self.name = name
    self.extension = extension
    self.module = module
    self.path = relative_path
    self.module_root = module_root
    self.sources = sources
    self.libraries = libraries
    self.include_paths = None
  def __repr__(self):
    return "<Target: {}>".format(self.name)
  
  @property
  def is_executable(self):
    return not self.is_library
  
  @property
  def is_test(self):
    return self.is_executable and ("tst" in self.name or "test" in self.name)
  
  @property
  def is_library(self):
    return self.extension in {".so", ".a", ".dylib"}
  
  @property
  def is_static_library(self):
    return self.extension == ".a"

  @property
  def is_python_library(self):
    return self.is_library and self.prefix != "lib" and "boost_python" in self.libraries

  def describe(self):
    """Return a BuildDeps description dictionary"""

    # Work out our full path
    fullPath = os.path.normpath(os.path.join(self.module_root, self.path))

    # Find hard-coded sources. We want all absolute sources, as a relative path
    localSources = [os.path.relpath(x, fullPath) for x in self.sources if os.path.isabs(x)]

    # Basic, common info
    info = {"name": self.name}
    if localSources:
      info["sources"] = localSources
    if self.output_path:
      info["location"] = self.output_path
    
    # Generated sources are in the build directory
    specialSources = [x for x in self.sources if not os.path.isabs(x)]
    if specialSources:
      info["generated_sources"] = specialSources

    if self.include_paths:
      info["include_paths"] = self.include_paths

    # Handle what's linked to
    if self.libraries:
      info["dependencies"] = list(self.libraries)
    return info



def _get_target(name, tlist):
  return next(iter(x for x in tlist if x.name == name), None)

def _build_target_list(logdata):
  # List of all modules and their path
  modules = {}
  # List of targets
  targets = []
  # Keep track of all and tick them off
  objects_unused = set(id(x) for x in logdata.objects)

  for target in logdata.link_targets:
    target_name = target["-o"]
    # Work out the common source directories
    objects = [x for x in logdata.objects if x["-o"] in target["<source>"]]
    objects_unused -= set(id(x) for x in objects)
    sources = list(itertools.chain(*[x["<source>"] for x in objects]))
    source_dirs = set(os.path.dirname(x) for x in sources)
    abs_source_dirs = [x for x in source_dirs if os.path.isabs(x)]
    if len(abs_source_dirs) > 1:
      # In this case, there is sources from more than one directory contributing. This
      # is okay unless the common path is at the module level
      common = os.path.dirname(os.path.commonprefix(abs_source_dirs))
      # logger.info("Multiple source dirs for {}:\n{}".format(target_name, "\n".join("  - " + x for x in abs_source_dirs)))
      # logger.info(" Found common path => {}".format(common))
      abs_source_dirs = [common]

      # if os.path.normpath(common) == os.path.normpath(logdata.module_root):
      #   logger.warning("Target {} has no common source path except ROOT, skipping".format(target_name))
      #   continue
    elif len(abs_source_dirs) == 0:
      # Need to manually resolve these targets with all sources generated in the
      # build directory - technically we could read from the relative and look 
      # for a matching module, but only a single example exists
      logger.warning("Target {} has only generated sources".format(target_name))
      # continue

    # Work out the base-relative path and thus modulename
    if not abs_source_dirs:
      relative_path = "."
    else:
      relative_path = os.path.relpath(abs_source_dirs[0], logdata.module_root)
      if relative_path.startswith("cctbx_project/"):
        module = relative_path[len("cctbx_project/"):].split("/")[0]
        modules[module] = os.path.join("cctbx_project", module)
      else:
        module = relative_path.split("/")[0]
        modules[module] = module

    libs = (set(target["-l"]) - {"m"}) | set(target["--framework"])
    targets.append(Target(target_name, module, relative_path, logdata.module_root, sources, libraries=libs))

  if objects_unused:
    print("{} objects unused.".format(len(objects_unused)))
    objects_unused = [x for x in logdata.objects if id(x) in objects_unused]
  return targets, modules

class BuildInfo(object):
  def __init__(self, module, path, parent=None):
    self.module = module
    self.path = path
    self.parent = parent

    self.include_paths = None
    self.subdirectories = {}
    self.targets = []
    self.libtbx_refresh_files = []

  def get_path(self, path):
    """Get, or create, a build object for the requested path"""
    if isinstance(path, str):
      path = os.path.normpath(path).split("/")
    if not path or path ==["."]:
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

  def generate(self, embed_subdirs=False):
    """Generate the BuildDeps file, as a dictionary to yaml-write"""
    data = {}

    if self.parent and self.module != self.parent.module:
      data["project"] = self.module
      if self.include_paths:
        data["project_include_path"] = self.include_paths
    if self.subdirectories:
      if embed_subdirs:
        data["subdirectories"] = {x: self.subdirectories[x].generate(embed_subdirs) for x in self.subdirectories}
      else:
        data["subdirectories"] = self.subdirectories.keys()

    if self.libtbx_refresh_files:
      data["libtbx_refresh"] = list(self.libtbx_refresh_files)

    for target in self.targets:
      # Get the list to append to (targetlist)
      if target.is_library:
        if target.is_static_library:
          targetlist = data.get("static_libraries", [])
          data["static_libraries"] = targetlist
        elif target.is_python_library:
          targetlist = data.get("python_extensions", [])
          data["python_extensions"] = targetlist
        else:
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

  @classmethod
  def build_target_tree(cls, targets):
    # Now we have a list of targets, along with their basic directory
    # Make a directory tree for every target
    root = BuildInfo(None, "")

    # Add each target to the dependency tree
    for target in targets:
      info = root.get_path(target.path)
      info.targets.append(target)

    return root

  def write_depfiles(self, root, filename):
    # Write out all the autodependency files
    for (path, info) in [(x.path, x) for x in self.collect()]:
      targetPath = os.path.join(root, path, filename)
      makedirs(os.path.dirname(targetPath))
      with open(targetPath, 'w') as depfile:
        depfile.write(yaml.dump(info.generate()))


if __name__ == "__main__":
  options = docopt(__doc__)
  logging.basicConfig(level=logging.INFO)
  logdata = LogParser(options["<buildlog>"])

  overrides_filename = options["<overrides>"] or "autogen.yaml"

  if options["--target"]:
    options["--target"] = os.path.abspath(options["--target"])

  # Extract target metadata
  targets, module_paths = _build_target_list(logdata)
  # Quick fix: Add annlib path to module list (will only be used if needed)
  module_paths["annlib"] = "annlib"
  module_paths["ccp4io"] = "ccp4io"
  module_paths["."] = None
  
  # Make a list of all dependencies that AREN'T targets
  all_dependencies = set(itertools.chain(*[x.libraries for x in targets]))
  external_dependencies = all_dependencies - {x.name for x in targets}
  print("External dependencies: ", external_dependencies)

  # Find any targets that match the name of a module but aren't at module level
  # This corrects 'spotfinder' and 'ccp4io' for example
  # Find any targets that match the name of a module, and make sure they are in the right place
  misdir_modlibs = [x for x in targets if x.name in module_paths and not x.path == module_paths[x.module]]
  if misdir_modlibs:
    # print("Found module-named libraries outside of expected path:", ", ".join(x.name for x in misdir_modlibs))
    for target in misdir_modlibs:
      prepath = target.path
      target.path = module_paths[target.name]
      print("Moving module-named {} from {} to {}".format(target.name, prepath, target.path))

  # Generate the target tree information
  tree = BuildInfo.build_target_tree(targets)
  
  # Remove Boost from the tree
  if "boost" in tree.subdirectories:
    del tree.subdirectories["boost"]
    bpy = [x for x in tree.targets if "boost_python.dylib" in x.name]
    if bpy:
      assert len(bpy) == 1
      tree.targets.remove(bpy[0])

  # Now, let's integrate the data from our overrides file
  if os.path.isfile(overrides_filename):
    override = yaml.load(open(overrides_filename))

    if "dependencies" in override:
      for name, deps in override["dependencies"].items():
        if isinstance(deps, str):
          deps = [deps]
        # Find target name
        filtered_targets = _get_target(name, targets)
        if not filtered_targets:
          print("WARNING: Could not resolve target {} to add manual dependencies.".format(name))
          continue
        filtered_targets.libraries.update(deps)

    # Add information about automatically generated files
    if "libtbx_refresh" in override:
      for module in override["libtbx_refresh"]:
        # Get the tree folder for this module
        mod_dir = tree.get_path(module_paths[module])
        mod_dir.libtbx_refresh_files = override["libtbx_refresh"][module]

    if "forced_locations" in override:
      for targetname, new_path in override["forced_locations"].items():
        print("Override: Moving {} to {}".format(targetname, new_path))
        target = [x for x in targets if x.name == targetname][0]
        tree.get_path(target.path).targets.remove(target)
        tree.get_path(new_path).targets.append(target)
        target.path = new_path

    if "target_includes" in override:
      for name, paths in override["target_includes"].items():
        if isinstance(paths, str):
          paths = [paths]

        # If this is a target name, add to target
        # Otherwise, look in module names
        target = next(iter(x for x in targets if x.name == name), None)
        if target:
          target.include_paths = paths
        else:
          assert name in module_paths, "Name for extra includes {} not a target or module".format(name)
          tree.get_path(module_paths[name]).include_paths = paths

  if options["--target"]:
    if options["--allinone"]:
      with open(os.path.join(options["--target"], options["--name"]), "w") as f:
        f.write(yaml.dump(tree.generate(embed_subdirs=True)))
    else:
      tree.write_depfiles(root=options["--target"], filename=options["--name"])

