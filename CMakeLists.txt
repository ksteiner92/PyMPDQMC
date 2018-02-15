cmake_minimum_required (VERSION 3.1)

# Project name
project (mpdqmc)

# make sure that the default is a RELEASE
if (NOT CMAKE_BUILD_TYPE)
    set (CMAKE_BUILD_TYPE RELEASE CACHE STRING
            "Choose the type of build, options are: None Debug Release."
            FORCE)
endif (NOT CMAKE_BUILD_TYPE)

option(USE_CKB "Use checkboard decomposition" OFF)
#option(USE_CUDA "Use GPU support" OFF)
set(F2PY_EXEC f2py CACHE FILEPATH "f2py executable")
set(F90WRAP_EXEC f90wrap CACHE FILEPATH "f90wrap executable")

# set cmake module path for *.cmake
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake")

enable_language(Fortran)

add_library(util OBJECT src/quest/dqmc_mpi.F90 src/quest/dqmc_util.F90 src/quest/dqmc_cfg.F90)
add_library(latt OBJECT src/quest/dqmc_geom_param.F90 src/quest/dqmc_latt.F90 src/quest/dqmc_bonds.F90 src/quest/dqmc_reclatt.F90 )
add_library(hamilt OBJECT src/quest/dqmc_hamilt.F90 src/quest/dqmc_symm.F90)
if (USE_CKB)
    set (CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -DDQMC_CKB")
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DDQMC_CKB")
    add_library(mat OBJECT src/quest/dqmc_wspace.F90 src/quest/dqmc_struct.F90 src/quest/dqmc_geom_wrap.F90 src/quest/dqmc_checkerboard.F90)
else()
    add_library(mat OBJECT src/quest/dqmc_wspace.F90 src/quest/dqmc_struct.F90 src/quest/dqmc_geom_wrap.F90 src/quest/dqmc_matb.F90)
endif()
add_library(phy OBJECT src/quest/dqmc_seqb.F90 src/quest/dqmc_gfun.F90 src/quest/dqmc_phy0.F90 src/quest/computeg.c++
        src/quest/blaslapack.c++
        src/quest/kernel_cpu.c++
        src/quest/profile.c++)
add_library(phy2 OBJECT src/quest/dqmc_phy2.F90 src/quest/dqmc_hubbard.F90 src/quest/dqmc_gtau.F90)
add_library(tdm OBJECT src/quest/dqmc_tdm1.F90 src/quest/dqmc_tdm2.F90 src/quest/dqmc_kbonds.F90 src/quest/dqmc_2dperl.F90)

add_dependencies(latt util)
add_dependencies(hamilt latt)
add_dependencies(mat hamilt)
add_dependencies(phy mat)
add_dependencies(phy2 phy)
add_dependencies(tdm phy2)

add_library(dqmc STATIC src/ggeom.F90 $<TARGET_OBJECTS:util>
                                      $<TARGET_OBJECTS:latt>
                                      $<TARGET_OBJECTS:hamilt>
                                      $<TARGET_OBJECTS:mat>
                                      $<TARGET_OBJECTS:phy>
                                      $<TARGET_OBJECTS:phy2>
                                      $<TARGET_OBJECTS:tdm>)

if (CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    set (CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -m64 -funroll-loops -Wall -O3 -fPIC")
    set (F2PY_COMPILER gnu95)
elseif (CMAKE_Fortran_COMPILER_ID MATCHES "Intel")
    set (CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -m64 -warn all -O3 -unroll -fPIC")
    set (F2PY_COMPILER intelem)
endif()

include_directories(${CMAKE_SOURCE_DIR}/src/quest)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -m64 -Wall -O3 -funroll-loops -fPIC")

find_package(MKL)
if("${MKL_LIBRARIES}" STREQUAL "")
    find_package(BLAS REQUIRED)
    if (BLAS_FOUND)
        message("MKL is not found using blas instead")
        target_link_libraries(dqmc blas)
    else()
        message(STATUS "No blas library could be found.")
    endif()
else()
    message(STATUS "Found required mkl libraries")
    target_link_libraries(dqmc ${MKL_LIBRARIES} pthread dl)
endif()

find_package(OpenMP)
if(OPENMP_FOUND)
    set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} ${OpenMP_Fortran_FLAGS}")
else()
    message(STATUS "OpenMP could not be found.")
endif()

find_package(PythonInterp REQUIRED)

set(F2PY_PREFIX ggeom_)
set(F2PY_MODULE dqmc)

execute_process(
        COMMAND "${PYTHON_EXECUTABLE}" -c "if True:
                                                from distutils import sysconfig as sc
                                                print(sc.get_python_lib(prefix='', plat_specific=True))"
        OUTPUT_VARIABLE PYTHON_SITE
        OUTPUT_STRIP_TRAILING_WHITESPACE)

add_custom_command(OUTPUT ${F2PY_PREFIX}ggeom.f90
        COMMAND ${F90WRAP_EXEC} --kind-map ${CMAKE_SOURCE_DIR}/src/py/kind.map --prefix ${F2PY_PREFIX} -m ${F2PY_MODULE} ${CMAKE_SOURCE_DIR}/src/ggeom.F90
        DEPENDS dqmc
        POST_BUILD)

add_custom_command(OUTPUT dqmc.so
        COMMAND ${F2PY_EXEC} -L${CMAKE_BINARY_DIR} ${MKL_LIBRARIES} -ldqmc -lstdc++  -c
        --f90flags='-I${CMAKE_BINARY_DIR} ${CMAKE_Fortran_FLAGS}'
        ${CMAKE_BINARY_DIR}/${F2PY_PREFIX}*.f90 -m ${F2PY_MODULE} --fcompiler=${F2PY_COMPILER}
        DEPENDS ${F2PY_PREFIX}ggeom.f90
        POST_BUILD)

add_custom_target(mpdqmc ALL DEPENDS dqmc.so)

set(SETUP_PY_IN "${CMAKE_SOURCE_DIR}/src/py/setup.py.in")
set(SETUP_PY    "${CMAKE_CURRENT_BINARY_DIR}/setup.py")
set(PYDQMC_MOD "libdqmc")
configure_file(${SETUP_PY_IN} ${SETUP_PY})

install(FILES ${CMAKE_SOURCE_DIR}/src/py/MANIFEST.in DESTINATION ${CMAKE_BINARY_DIR})
install(FILES ${CMAKE_BINARY_DIR}/dqmc.so DESTINATION ${CMAKE_BINARY_DIR}/${PYDQMC_MOD})
install(FILES ${CMAKE_SOURCE_DIR}/src/py/dqmc/__init__.py DESTINATION ${CMAKE_BINARY_DIR}/${PYDQMC_MOD})
install(FILES ${CMAKE_SOURCE_DIR}/src/py/dqmc/dqmc_handler.py DESTINATION ${CMAKE_BINARY_DIR}/${PYDQMC_MOD})
install(FILES ${CMAKE_SOURCE_DIR}/src/py/dqmc/extractor.py DESTINATION ${CMAKE_BINARY_DIR}/${PYDQMC_MOD})
install(CODE "execute_process(COMMAND ${PYTHON_EXECUTABLE} setup.py install)")

