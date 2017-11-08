#!/bin/bash

# What method to use to fetch github repos e.g. this or ssh
GITHUB_PREFIX=https://github.com/

set -e

# Generate output style codes for pretty output
if [[ -n "$(command -v tput)" ]]; then
  BOLD=$(tput bold)
  NC=$(tput sgr0)
  # LIGHT=$(tput setaf 7)
  LIGHT=$'\e[90m'
fi

# Convenience function to display a header
stage() {
  echo "${NC}== ${BOLD}$*${NC} ==${LIGHT}"
}

# Display some help for the user
print_usage() {
  echo "Usage: convert_to_cmake.sh <distribution>"
}

if [[ ! -d $1 ]]; then
  print_usage
  exit 1
fi

if [[ -z $(command -v cmake) ]]; then
  echo "Error: cmake executable could not be found"
  exit 1
fi

DIST=$(pwd)/$1

stage "Activating distribution"
# Activate the distribution
if [[ ! -f $DIST/build/setpaths.sh ]]; then
  echo "Error: No setpaths.sh found in distribution build directory"
  exit 1
fi
source $DIST/build/setpaths.sh

#stage "Ensuring CMake modules repository is present"
# Get the CMake checkout
( cd $DIST/modules
  if [[ ! -d cmake ]]; then
    stage "Fetching CMake module library"
    git clone ${GITHUB_PREFIX}ndevenish/autobuild.git cmake
  else
    stage "Updating CMake module library"
    ( cd cmake
      git pull --rebase origin )
  fi
  # Make sure that the root CMakeLists is in the right place
  if [[ ! -e CMakeLists.txt ]]; then
    ln -s cmake/RootCMakeLists.txt CMakeLists.txt
  fi
)

# Make sure the CMake conversion scripts are installed
stage "Installing tbxtools"
libtbx.python -mpip install --upgrade git+https://github.com/ndevenish/tbxtools.git

# Work out where this is installed and make sure it's in the path
python_bin_dir=$(libtbx.python -c "import site; print(site.getsitepackages()[0])")/../../../bin
if [[ ! -f ${python_bin_dir}/tbx2cmake ]]; then
  echo "Error: Could not locate python site binary path; not at ${python_bin_dir}"
fi
export PATH=${python_bin_dir}:${PATH}

stage "Generating CMakeLists"
( cd $DIST/modules
  tbx2cmake . . )

# stage "Generating CMake build"

# Boost - since we don't have a real boost installation, we need to
# probably create a new boost installation somewhere.
boost_version=$(cd $DIST && libtbx.python -c 'import re;ver=int(re.search(r"^\s*#define\s+BOOST_VERSION\s+(\d+)\s*$", \
                                              open("modules/boost/boost/version.hpp").read(),re.M).group(1)); \
                                              print("{}.{}.{}".format(ver//100000,ver//100%1000,ver%100))')
# Do we need to install boost?
BOOST_DIR=$DIST/base/boost/$boost_version
if [[ ! -f ${BOOST_DIR}/.completed ]]; then
  stage "Installing boost ${boost_version}"
  BOOST_BUILD_DIR=$DIST/base_tmp/boost-${boost_version}
  BOOST_URL="http://sourceforge.net/projects/boost/files/boost/${boost_version}/boost_${boost_version//\./_}.tar.gz"
  mkdir -p ${BOOST_BUILD_DIR}

  if [[ -z "$(ls -A ${BOOST_BUILD_DIR})" ]]; then
    curl -L ${BOOST_URL} | tar --strip-components=1 -xz -C ${BOOST_BUILD_DIR}
  fi
  mkdir -p $BOOST_DIR
  ( cd ${BOOST_BUILD_DIR} && \
    ./bootstrap.sh && \
    ./b2 -j 3 -d0 --prefix=${BOOST_DIR} --with-python --with-thread install && \
    touch $BOOST_DIR/.completed
    )
fi

stage "Generating CMake build"

echo "Distribution uses boost $boost_version"
echo "Using boost installation in $BOOST_DIR"
cmake_vars="$cmake_vars -DBOOST_ROOT=${BOOST_DIR}"

# Use the base as a generic search location
cmake_vars="$cmake_vars -DCMAKE_PREFIX_PATH=$DIST/base"

# Eigen
if [[ -d $DIST/modules/eigen ]]; then
  cmake_vars="$cmake_vars -DEIGEN_ROOT=$DIST/modules/eigen"
else
  echo "Warning: No Eigen found; this could cause build to fail"
fi

echo

echo "Running cmake configuration with: $cmake_vars"
echo

( cd $DIST/build
  cmake $DIST/modules $cmake_vars )