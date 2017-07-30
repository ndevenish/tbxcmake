#!/usr/bin/env python

"""
Prepares a directory for cmake-based building.

Designed to make travis-based testing intuitive (e.g. working with updates
directly on the individual repositories). This means you can check out a 
single repository (at whatever branch or pull request it comes from) and
have the rest of the build automatically constructed around it.
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

# Map of folder names to repository locations
repositories = {
  "dials":          "https://github.com/dials/dials.git",
  "cctbx_project":  "https://github.com/cctbx/cctbx_project.git",
  "cbflib":         "https://github.com/yayahjb/cbflib.git",
  "ccp4io":         "https://github.com/dials/ccp4io.git",
  "xia2":           "https://github.com/xia2/xia2.git",
  "annlib_adaptbx": "https://github.com/dials/annlib_adaptbx.git",
  "annlib":         "https://github.com/dials/annlib.git",
  "ccp4io_adaptbx": "https://github.com/dials/ccp4io_adaptbx.git",
  "tntbx":          "https://github.com/dials/tntbx.git",
  "gui_resources":  "https://github.com/dials/gui_resources.git",
}

for name, url in repositories.items():
  # Assume that if the path exists at all, the user knows what they are doing
  if os.path.exists(name):
    continue
  subprocess.check_call(["git", "clone", "--depth=1", url])

# Copy over tree of files from cmake
merge_tree("cmake/cmakelists", os.getcwd())
shutil.copy2("cmake/RootCMakeLists.txt", "CMakeLists.txt")
