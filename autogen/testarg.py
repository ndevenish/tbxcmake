import shlex

# av = shlex.split("""-o dials/algorithms/refinement/boost_python/gallego_yezzi.o -fno-unused-local-typedefs -fPIC -DBOOST_ALL_NO_LIB -I/home/xgkkp/dials_dist/modules/boost -I/home/xgkkp/dials_dist/modules/boost -I/home/xgkkp/dials_dist/modules/boost -I/home/xgkkp/dials_dist/modules/boost a b""")
# av = shlex.split("""-o dials/algorithms/refinement/boost_python/gallego_yezzi.o -w -DBOOST_PYTHON_MAX_BASES=2 -I/home/xgkkp/dials_dist/modules/boost -I/home/xgkkp/dials_dist/modules/boost -I/home/xgkkp/dials_dist/modules/boost -I/home/xgkkp/dials_dist/modules/boost -fPIC -fno-strict-aliasing  -Wall -Wno-sign-compare -Wno-unknown-pragmas -Wno-parentheses -Winit-self -Wno-unused-local-typedefs -Werror=vla -DNDEBUG  -funroll-loops -ffast-math -DBOOST_ALL_NO_LIB -I/home/xgkkp/dials_dist/build/include -I/home/xgkkp/dials_dist/modules/cctbx_project -I/home/xgkkp/dials_dist/base/include/python2.7 -I/home/xgkkp/dials_dist/modules -I/home/xgkkp/dials_dist/modules/annlib -I/home/xgkkp/dials_dist/modules/annlib/src -I/home/xgkkp/dials_dist/modules/annlib/include -I/home/xgkkp/dials_dist/modules/annlib_adaptbx/include -I/home/xgkkp/dials_dist/build/annlib_adaptbx/include -I/home/xgkkp/dials_dist/modules/annlib -I/home/xgkkp/dials_dist/modules/annlib/src -I/home/xgkkp/dials_dist/modules/annlib/include -I/home/xgkkp/dials_dist/modules/annlib_adaptbx/include -I/home/xgkkp/dials_dist/build/annlib_adaptbx/include -I/home/xgkkp/dials_dist/modules/cctbx_project /home/xgkkp/dials_dist/modules/dials/algorithms/refinement/boost_python/gallego_yezzi.cc""")
# av = shlex.split("""-o annlib/src/ANN.o -c -fPIC -fno-strict-aliasing -w -DNDEBUG -O3 -funroll-loops -ffast-math -DBOOST_ALL_NO_LIB -I/home/xgkkp/dials_dist/build/include -I/home/xgkkp/dials_dist/modules/cctbx_project -I/home/xgkkp/dials_dist/modules/cctbx_project -I/home/xgkkp/dials_dist/modules/boost -I/home/xgkkp/dials_dist/modules/annlib -I/home/xgkkp/dials_dist/modules/annlib/src -I/home/xgkkp/dials_dist/modules/annlib/include -I/home/xgkkp/dials_dist/modules/annlib_adaptbx/include -I/home/xgkkp/dials_dist/build/annlib_adaptbx/include /home/xgkkp/dials_dist/modules/annlib/src/ANN.cpp""")

cmd = """-o lib/libcctbx.so -shared -s cctbx/eltbx/basic.o cctbx/eltbx/xray_scattering/it1992.o cctbx/eltbx/xray_scattering/wk1995.o cctbx/eltbx/xray_scattering/n_gaussian_raw.o cctbx/eltbx/xray_scattering/n_gaussian.o cctbx/eltbx/fp_fdp.o cctbx/eltbx/henke.o cctbx/eltbx/henke_tables_01_12.o cctbx/eltbx/henke_tables_13_24.o cctbx/eltbx/henke_tables_25_36.o cctbx/eltbx/henke_tables_37_48.o cctbx/eltbx/henke_tables_49_60.o cctbx/eltbx/henke_tables_61_72.o cctbx/eltbx/henke_tables_73_84.o cctbx/eltbx/henke_tables_85_92.o cctbx/eltbx/icsd_radii.o cctbx/eltbx/covalent_radii.o cctbx/eltbx/neutron.o cctbx/eltbx/sasaki.o cctbx/eltbx/sasaki_tables_01_12.o cctbx/eltbx/sasaki_tables_13_24.o cctbx/eltbx/sasaki_tables_25_36.o cctbx/eltbx/sasaki_tables_37_48.o cctbx/eltbx/sasaki_tables_49_60.o cctbx/eltbx/sasaki_tables_61_72.o cctbx/eltbx/sasaki_tables_73_82.o cctbx/eltbx/tiny_pse.o cctbx/eltbx/wavelengths.o cctbx/eltbx/electron_scattering/peng1996.o cctbx/eltbx/attenuation_coefficient.o cctbx/miller/asu.o cctbx/miller/bins.o cctbx/miller/index_generator.o cctbx/miller/index_span.o cctbx/miller/match_bijvoet_mates.o cctbx/miller/match_indices.o cctbx/miller/match_multi_indices.o cctbx/miller/sym_equiv.o cctbx/sgtbx/bricks.o cctbx/sgtbx/change_of_basis_op.o cctbx/sgtbx/find_affine.o cctbx/sgtbx/group_codes.o cctbx/sgtbx/hall_in.o cctbx/sgtbx/lattice_tr.o cctbx/sgtbx/lattice_symmetry.o cctbx/sgtbx/miller.o cctbx/sgtbx/reciprocal_space_asu.o cctbx/sgtbx/reciprocal_space_ref_asu.o cctbx/sgtbx/rot_mx.o cctbx/sgtbx/rot_mx_info.o cctbx/sgtbx/row_echelon_solve.o cctbx/sgtbx/rt_mx.o cctbx/sgtbx/select_generators.o cctbx/sgtbx/seminvariant.o cctbx/sgtbx/site_symmetry.o cctbx/sgtbx/space_group.o cctbx/sgtbx/space_group_type.o cctbx/sgtbx/symbols.o cctbx/sgtbx/tensor_rank_2.o cctbx/sgtbx/tr_group.o cctbx/sgtbx/tr_vec.o cctbx/sgtbx/utils.o cctbx/sgtbx/wyckoff.o cctbx/sgtbx/reference_settings/hall_symbol_table.o cctbx/sgtbx/reference_settings/matrix_group_code_table.o cctbx/sgtbx/reference_settings/normalizer.o cctbx/sgtbx/reference_settings/wyckoff.o cctbx/uctbx/uctbx.o cctbx/uctbx/spoil_optimization.o cctbx/uctbx/crystal_orientation.o -Llib -L/home/xgkkp/dials_dist/modules/lib -L/home/xgkkp/dials_dist/modules/cctbx_project/lib -lm"""
cmd = cmd.replace("-shared", "--shared")
av = shlex.split(cmd)

doc = """Usage:
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

from docopt import docopt
print(av)
print(docopt(doc, argv=av))

# -fPIC -fno-strict-aliasing -Wall -Wno-sign-compare -Wno-unknown-pragmas -Wno-parentheses -Winit-self -Wno-unused-local-typedefs -Werror=vla -DNDEBUG -O3 -funroll-loops -ffast-math -DBOOST_ALL_NO_LIB -I/home/xgkkp/dials_dist/build/include -I/home/xgkkp/dials_dist/modules/cctbx_project -I/home/xgkkp/dials_dist/base/include/python2.7 -I/home/xgkkp/dials_dist/modules -I/home/xgkkp/dials_dist/modules/annlib -I/home/xgkkp/dials_dist/modules/annlib/src -I/home/xgkkp/dials_dist/modules/annlib/include -I/home/xgkkp/dials_dist/modules/annlib_adaptbx/include -I/home/xgkkp/dials_dist/build/annlib_adaptbx/include -I/home/xgkkp/dials_dist/modules/annlib -I/home/xgkkp/dials_dist/modules/annlib/src -I/home/xgkkp/dials_dist/modules/annlib/include -I/home/xgkkp/dials_dist/modules/annlib_adaptbx/include -I/home/xgkkp/dials_dist/build/annlib_adaptbx/include -I/home/xgkkp/dials_dist/modules/cctbx_project /home/xgkkp/dials_dist/modules/dials/algorithms/refinement/boost_python/gallego_yezzi.cc


# -c -DBOOST_PYTHON_MAX_BASES=2 