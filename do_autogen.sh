#!/usr/bin/env sh

autogen/resolve.py autogen/bootstrap.log autogen/autogen.yaml --target=autogen/md
autogen/depsToCMake.py autogen/md/AutoBuildDeps.yaml --target=cmakelists --override=autogen/cmake_templates/

