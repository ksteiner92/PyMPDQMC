cmake_minimum_required (VERSION 3.1)

# Project name
project (mpdqmc)

add_library(dqmc STATIC src/quest/dqmc_mpi.F90
        src/quest/dqmc_util.F90
        src/quest/dqmc_cfg.F90
        src/quest/dqmc_geom_param.F90
        src/quest/dqmc_latt.F90
        src/quest/dqmc_bonds.F90
        src/quest/dqmc_reclatt.F90
        src/quest/dqmc_hamilt.F90
        src/quest/dqmc_symm.F90
        src/quest/dqmc_wspace.F90
        src/quest/dqmc_struct.F90
        src/quest/dqmc_geom_wrap.F90
        src/quest/dqmc_matb.F90
        src/quest/dqmc_seqb.F90
        src/quest/dqmc_gfun.F90
        src/quest/dqmc_phy0.F90
        src/quest/dqmc_phy2.F90
        src/quest/dqmc_hubbard.F90
        src/quest/dqmc_gtau.F90
        src/quest/dqmc_tdm1.F90
        src/quest/dqmc_tdm2.F90
        src/quest/dqmc_kbonds.F90
        src/quest/dqmc_2dperl.F90
        src/quest/computeg.c++
        src/quest/blaslapack.c++
        src/quest/kernel_cpu.c++
        src/quest/profile.c++)

# make sure that the default is a RELEASE
if (NOT CMAKE_BUILD_TYPE)
    set (CMAKE_BUILD_TYPE RELEASE CACHE STRING
            "Choose the type of build, options are: None Debug Release."
            FORCE)
endif (NOT CMAKE_BUILD_TYPE)

option(USE_CKB "Use checkboard decomposition" OFF)
option(USE_CUDA "Use GPU support" OFF)

# set cmake module path for *.cmake
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake")

enable_language(Fortran)

#set (CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -funroll-all-loops -fPIC -DDQMC_ASQRD -Wl,--no-undefined")
if (CMAKE_Fortran_COMPILER_ID MATCHES "GNU")
    set (CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -m64 -funroll-loops -Wall -O3 -fPIC")
    #set (CMAKE_Fortran_FLAGS_DEBUG   "-fno-f2c -O0 -g -fPIC")
elseif (CMAKE_Fortran_COMPILER_ID MATCHES "Intel")
    set (CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -m64 -warn all -O3 -unroll -fPIC")
    #set (CMAKE_Fortran_FLAGS_DEBUG   "-O0 -g -fPIC")
endif()


include_directories(${CMAKE_SOURCE_DIR}/src/quest)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC")

# https://software.intel.com/en-us/articles/intel-mkl-link-line-advisor
find_package(MKL)
if(MKL_FOUND)
    # NOTE: -fdefault-integer-8 -m64  are crucial for MKL to avoid SIGSEGV at runtime!
    set (CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -fdefault-integer-8")
    target_link_libraries(dqmc ${MKL_LIBRARIES} pthread dl)
    #
else()
    find_package(BLAS REQUIRED)
    target_link_libraries(dqmc blas)
endif()

# check for OpenMP if turned on
find_package(OpenMP)
if(OPENMP_FOUND)
    set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} ${OpenMP_Fortran_FLAGS}")
else()
    message(STATUS "OpenMP could not be found.")
endif()

find_package(PythonInterp REQUIRED)

add_custom_command(OUTPUT ggeom.so
        COMMAND f2py -L${CMAKE_BINARY_DIR} -lmkl_intel_lp64 -lmkl_sequential
        -lmkl_core -lpthread -ldqmc -lstdc++ -liomp5 -c
        --f90flags='-I${CMAKE_BINARY_DIR} -m64 -warn all -O3 -unroll'
        ${CMAKE_SOURCE_DIR}/src/ggeom.F90 -m ggeom --fcompiler=intelem
        DEPENDS dqmc
        POST_BUILD)

add_custom_target(ggeom ALL DEPENDS ggeom.so)

#include(f2py_add)
#include("${CMAKE_SOURCE_DIR}/cmake/f2py_add.cmake")
#F2PY_ADD(MODULE ggeom SRC "${CMAKE_SOURCE_DIR}/src/ggeom.F90" EXTERNAL_LIBS -ldqmc ${CMAKE_SOURCE_DIR}/cmake-build-debug)
