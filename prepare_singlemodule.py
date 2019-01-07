#!/usr/bin/env python

"""
Prepares a directory for cmake-based building.

Usage:
  prepare_singlemodule.py [options]

Options:
  -h, --help    Show this message
  --write-log   Writes the commit ID's of all repositories to commit_ids.txt
  --no-cmake    Don't attempt to copy cmakelists out of cmake/cmakelists/
  --shallow     Only get a shallow clone of each repository.
  --reference=<DIR> Use an existing location as a git clone reference. Each
                    repository is assumed to exist as a subdirectory of this.

Designed to make travis-based testing intuitive (e.g. working with updates
directly on the individual repositories). This means you can check out a
single repository (at whatever branch or pull request it comes from) and
have the rest of the build automatically constructed around it.

Run this in the root of your 'module' directory, with:
  - the autobuild repository checked out in a 'cmake' subdirectory
  - Any custom parts of the build checked out into the properly named folders
"""

from __future__ import print_function

import os
import subprocess
import shutil

import docopt


def merge_tree(src, dst):
    """Copy all files in source tree to destination, merging with existing tree."""
    for path, dirs, files in os.walk(src):
        relpath = path[len(src) + 1 :]
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
    """Returns the current git commit ID of a repository, given it's working dir"""
    newenv = os.environ.copy()
    newenv["GIT_DIR"] = os.path.join(folder, ".git")
    ret = subprocess.check_output(["git", "rev-parse", "HEAD"], env=newenv)
    assert len(ret.strip().splitlines()) == 1
    return ret.strip()


# Map of folder names to repository locations
# Either "URL String" or ["URL String", "and_list", "of", "arguments"]
repositories = {
    "annlib_adaptbx": "https://github.com/dials/annlib_adaptbx.git",
    "annlib": "https://github.com/dials/annlib.git",
    "cbflib": "https://github.com/yayahjb/cbflib.git",
    "ccp4io_adaptbx": "https://github.com/dials/ccp4io_adaptbx.git",
    "ccp4io": "https://github.com/dials/ccp4io.git",
    "cctbx_project": "https://github.com/cctbx/cctbx_project.git",
    "dials": "https://github.com/dials/dials.git",
    "gui_resources": "https://github.com/dials/gui_resources.git",
    "tntbx": "https://github.com/dials/tntbx.git",
    "xia2": "https://github.com/xia2/xia2.git",
}
options = docopt.docopt(__doc__)

commit_ids = {}
for name, url in repositories.items():
    # Assume that if the path exists at all, the user knows what they are doing
    if not os.path.exists(name):
        command = ["git", "clone"]
        # Convert to a list if not one already (allows multiple custom parameters)
        if isinstance(url, basestring):
            url = [url]

        if options["--shallow"]:
            command.append("--depth=1")

        # If the reference path exists, pass that through
        if options["--reference"]:
            ref_path = os.path.join(options["--reference"], name)
            ref_git = os.path.join(options["--reference"], name)
            if os.path.isdir(ref_path):
                command.append("--reference-if-able={}".format(ref_path))

        command.extend(url)
        print("Running:", " ".join(command))
        subprocess.check_call(command)
    else:
        print("{} folder exists, skipping.".format(name))

    if options["--write-log"]:
        commit_ids[name] = get_commit_id(name)

if options["--write-log"]:
    with open("commit_ids.txt", "wt") as f:
        maxlen = max(len(x) for x in commit_ids)
        for name, sha in sorted(commit_ids.items(), key=lambda x, y: x):
            f.write(name.ljust(maxlen) + " " + sha + "\n")

if not options["--no-cmake"]:
    # Copy over tree of files from cmake
    merge_tree("cmake/cmakelists", os.getcwd())
    try:
        shutil.copy2("cmake/RootCMakeLists.txt", "CMakeLists.txt")
    except shutil.Error:
        # Happens if both files are the same
        pass
