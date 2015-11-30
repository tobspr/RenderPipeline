
# Adjust to your Panda3D installation
set(P3D_DIR "D:/P3D/1.9GIT/built_x64_buffered")

set(P3D_INC_DIR "${P3D_DIR}/include")
set(P3D_LIB_DIR "${P3D_DIR}/lib")

cmake_minimum_required (VERSION 2.6)
project (PrecomputeScattering)
set (CMAKE_BUILD_TYPE "Release")

set(P3D_LIBS "libp3framework;libpanda;libpandaexpress;libp3dtool")
link_directories("${P3D_LIB_DIR}")
include_directories("${P3D_INC_DIR}")

add_executable(PrecomputeScattering main.cpp ArHosekSkyModel.cpp)

target_link_libraries(PrecomputeScattering ${P3D_LIBS})


