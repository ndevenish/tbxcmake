#!/usr/bin/env python
# coding: utf8
"""
Write a minimal libtbx_env that can be used for run-time processing.

This libtbx_env will not work for builds, dispatcher generation etc. It
works by faking the minimal libtbx environment to create an object tree
that will correctly unpickle.
"""

from __future__ import print_function

import os
import pickle
import sys
from types import ModuleType


def new_module(name, doc=None):
    """Create a new module and inject it into sys.modules"""
    m = ModuleType(name, doc)
    m.__file__ = name + ".py"
    sys.modules[name] = m
    return m


# Create the fake libtbx environment variables
libtbx = new_module("libtbx")
libtbx.env_config = new_module("libtbx.env_config")
libtbx.path = new_module("libtbx.path")


def into(module):
    """Decorates a class to look like it came from a specific module."""

    def _wrap(classdef):
        setattr(module, classdef.__name__, classdef)
        classdef.__module__ = module.__name__
        return classdef

    return _wrap


@into(libtbx.path)
class path_mixin(object):
    pass


@into(libtbx.path)
class relocatable_path(path_mixin):
    """Replicate the relocatable_path attributes"""

    def __init__(self, anchor, relative):
        self._anchor = absolute_path(anchor)
        # Replicate the logic that recalculates relativity if necessary
        if os.path.isabs(relative):
            relative = os.path.relpath(relative, self._anchor._path)
        self.relocatable = relative


@into(libtbx.path)
class absolute_path(path_mixin):
    """Replicate the absolute_path attributes"""

    def __init__(self, path):
        if isinstance(path, absolute_path):
            path = path._path
        self._path = os.path.abspath(path)


@into(libtbx.env_config)
class build_options:
    """Replicate an empty build_options"""

    pass


@into(libtbx.env_config)
class environment:
    """Replicate the pickled environment object"""

    def __init__(self, build_path, modules):
        # Used for .under_build, .under_base, relocatability
        self.build_path = absolute_path(build_path)
        # Needed for env_config.unpickle compatibility - defaults
        # will be written but this is only(?) used during build
        self.build_options = build_options()
        # Checked for existence as part of unpickling compatibility
        self.relocatable = True
        # Used during loading to set custom environment variables
        self.module_list = []
        # Used on load to cross-check configurations
        self.python_version_major_minor = sys.version_info[:2]

        # Dictionary used for looking up dist paths
        self.module_dist_paths = {
            name: relocatable_path(build_path, path) for name, path in modules
        }

        # Work out the repository locations by working backwards from libtbx
        tbx_rel_path = self.module_dist_paths["libtbx"]
        tbx_path = os.path.normpath(
            os.path.join(tbx_rel_path._anchor._path, tbx_rel_path.relocatable)
        )
        cctbx_path = os.path.dirname(tbx_path)
        modules_path = os.path.dirname(cctbx_path)

        # So that libtbx.env_config.find_in_repositories works
        self.repository_paths = [
            relocatable_path(self.build_path, modules_path),
            relocatable_path(self.build_path, cctbx_path),
        ]


# Extract the lists of modules, paths from arguments
paths = list(
    sorted(zip(sys.argv[1].split(";"), sys.argv[2].split(";")), key=lambda x: x[0])
)
build_path = os.getcwd()

maxl = max([len(x) for x, y in paths] + [6])
print("Writing libtbx_env")
print("Build path: {}".format(build_path))
print("Module".ljust(maxl) + " Path")
for name, path in paths:
    print("{} {}".format(name.ljust(maxl), path))

a = environment(build_path, paths)

with open("libtbx_env", "w") as f:
    pickle.dump(a, f)
