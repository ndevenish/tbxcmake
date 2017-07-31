#!/usr/bin/env python

"""
Prepares a directory for cmake-based building.

Usage:
  prepare_singlemodule.py [options]

Options:
  -h, --help    Show this message
  --write-log   Writes the commit ID's of all repositories to commit_ids.txt
  --no-cmake    Don't attempt to copy cmakelists out of cmake/cmakelists/

Designed to make travis-based testing intuitive (e.g. working with updates
directly on the individual repositories). This means you can check out a 
single repository (at whatever branch or pull request it comes from) and
have the rest of the build automatically constructed around it.

Run this in the root of your 'module' directory, with:
  - the autobuild repository checked out in a 'cmake' subdirectory
  - Any custom parts of the build checked out into the properly named folders
"""

import os, sys
import subprocess
import shutil

def merge_tree(src, dst):
  """Copy all files in source tree to destination, merging with an existing tree."""
  for path, dirs, files in os.walk(src):
    relpath = path[len(src)+1:]
    # Copy files over
    for file in files:
      fullsrcpath = os.path.join(path, file)
      fulldstpath = os.path.join(dst, relpath, file)
      shutil.copy2(fullsrcpath, fulldstpath)
    # Ensure the subdirectories exist
    for dir in dirs:
      fulldstpath = os.path.join(dst, relpath, dir)
      if not os.path.exists(fulldstpath):
        print("Making ", fulldstpath)

def get_commit_id(folder):
  newenv = os.environ.copy()
  newenv["GIT_DIR"] = os.path.join(folder, ".git")
  ret = subprocess.check_output(["git", "rev-parse", "HEAD"], env=newenv)
  assert len(ret.strip().splitlines()) == 1
  return ret.strip()

# Parse in a docopt-like way the system arguments
if "-h" in sys.argv or "--help" in sys.argv:
  print(__doc__.strip())
  sys.exit()
options = {
  "--write-log": "--write-log" in sys.argv,
  "--no-cmake": "--no-cmake" in sys.argv
}

# Map of folder names to repository locations
repositories = {
  "dials":          "https://github.com/dials/dials.git",
  "cctbx_project":  ["https://github.com/ndevenish/cctbx_project.git", "--branch", "pmaster"],
  "cbflib":         "https://github.com/yayahjb/cbflib.git",
  "ccp4io":         "https://github.com/dials/ccp4io.git",
  "xia2":           "https://github.com/xia2/xia2.git",
  "annlib_adaptbx": "https://github.com/dials/annlib_adaptbx.git",
  "annlib":         "https://github.com/dials/annlib.git",
  "ccp4io_adaptbx": "https://github.com/dials/ccp4io_adaptbx.git",
  "tntbx":          "https://github.com/dials/tntbx.git",
  "gui_resources":  "https://github.com/dials/gui_resources.git",
}

commit_ids = {}
for name, url in repositories.items():
  # Assume that if the path exists at all, the user knows what they are doing
  if not os.path.exists(name):
    # Convert to a list if not one already (allows multiple custom parameters)
    if isinstance(url, basestring):
      url = [url]
    subprocess.check_call(["git", "clone", "--depth=1"]+url)

  if options["--write-log"]:
    commit_ids[name] = get_commit_id(name)

if options["--write-log"]:
  with open("commit_ids.txt", "wt") as f:
    maxlen = max(len(x) for x in commit_ids)
    for name, sha in sorted(commit_ids.items(), key=lambda (x,y): x):
      f.write(name.ljust(maxlen) + " " + sha + "\n")

if not options["--no-cmake"]:
  # Copy over tree of files from cmake
  merge_tree("cmake/cmakelists", os.getcwd())
  shutil.copy2("cmake/RootCMakeLists.txt", "CMakeLists.txt")
