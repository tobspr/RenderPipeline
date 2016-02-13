
set(PROJECT_NAME CACHE STRING "Module")

cmake_minimum_required (VERSION 2.6)
project (${PROJECT_NAME})

# Project configuration
set(CMAKE_BUILD_TYPE "Release")

# Libraries and options set by the module builder
set(USE_LIB_EIGEN CACHE BOOL TRUE)
set(USE_LIB_BULLET CACHE BOOL FALSE)
set(USE_LIB_FREETYPE CACHE BOOL FALSE)
set(OPTIMIZE CACHE STRING "3")
set(IGATE_VERBOSE CACHE STRING "0")
set(INTERROGATE_LIB CACHE STRING "p3interrogatedb")
set(PYTHON_EXECUTABLE CACHE STRING "python")


# --- User controllable variables ---

# Whether to enable SSE. This only has effect on 32 bit.
# Should probably match the setting for the Panda3D build
set(ENABLE_SSE2 CACHE BOOL 1)
set(TOUCHINPUT_ENABLED CACHE BOOL 0)


# --- End of user variables --

# Reset cmake flags - we user our own
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "")
set(CMAKE_CXX_FLAGS_RELEASE "")
set(CMAKE_CXX_FLAGS_MINSIZEREL "")


set(LIBRARIES "")

# Windows - 32 and 64 bit
if (WIN32)
  
  set(PYTHONVER CACHE STRING "27")
  
  # Find panda path
  execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" "-B" "Scripts/common.py" "--print-sdk-path"
    OUTPUT_VARIABLE WIN_PANDA_PATH
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

  # Find thirdparty directory
  if (CMAKE_CL_32)
    set(THIRDPARTY_DIR "${WIN_PANDA_PATH}/../thirdparty/win-libs-vc10")
    if (NOT (EXISTS "${THIRDPARTY_DIR}"))
      set(THIRDPARTY_DIR "${WIN_PANDA_PATH}/thirdparty/win-libs-vc10")
    endif()
  else()
    set (THIRDPARTY_DIR "${WIN_PANDA_PATH}/../thirdparty/win-libs-vc10-x64")
    if (NOT (EXISTS "${THIRDPARTY_DIR}"))
      set (THIRDPARTY_DIR "${WIN_PANDA_PATH}/thirdparty/win-libs-vc10-x64")
    endif()
  endif()

  # These vars are based on the WIN_PANDA_PATH and usually are correct
  set(PANDA_LIBRARY_DIRS "${WIN_PANDA_PATH}/lib/")
  set(PANDA_INCLUDE_DIR "${WIN_PANDA_PATH}/include") 

  set(PYTHON_LIBRARIES "${WIN_PANDA_PATH}/python/libs/python${PYTHONVER}.lib")
  set(PYTHON_INCLUDE_DIRS "${WIN_PANDA_PATH}/python/include")

  # [LIB] Bullet
  if(USE_LIB_BULLET)
    include_directories("${THIRDPARTY_DIR}/bullet/include/")
    link_directories("${THIRDPARTY_DIR}/bullet/lib/")

    # TODO: Might need more libs
    if(CMAKE_CL_32)
      set(${LIBRARIES} "${LIBRARIES};LinearMath;BulletCollision;BulletDynamics;BulletSoftBody")
    else()
      set(${LIBRARIES} "${LIBRARIES};LinearMath_x64;BulletCollision_x64;BulletDynamics_x64;BulletSoftBody_x64")
    endif()
  endif()

  # [LIB] Eigen 3
  if (USE_LIB_EIGEN)
    include_directories("${THIRDPARTY_DIR}/eigen/include")
  endif()

  # [LIB] Freetype
  if (USE_LIB_FREETYPE)
    include_directories("${THIRDPARTY_DIR}/freetype/include")
    link_directories("${THIRDPARTY_DIR}/freetype/lib")
    set(${LIBRARIES} "${LIBRARIES};freetype")
  endif()

  # Check if all supplied files exist
  set(CHECK_PATHS ${PANDA_LIBRARY_DIRS} ${PANDA_INCLUDE_DIR} ${PYTHON_LIBRARIES} ${PYTHON_INCLUDE_DIRS})
  foreach(PATH ${CHECK_PATHS})
    if(NOT (EXISTS "${PATH}"))
        message(FATAL_ERROR "The supplied path '${PATH}' could not be found!")
    endif()
  endforeach()

  # Link panda libraries
  set(PANDA_LIBRARIES "libp3framework;libpanda;libpandaexpress;libp3dtool;libp3dtoolconfig;libp3direct;${INTERROGATE_LIB}")
  link_directories("${PANDA_LIBRARY_DIRS}")

else()
  set(PYTHONVERDOT CACHE STRING "2.7")
  set(Python_ADDITIONAL_VERSIONS ${PYTHONVERDOT})
  find_package(PythonLibs REQUIRED)

  # [LIB] Bullet
  if (USE_LIB_BULLET)
    find_package(Bullet REQUIRED)
    include_directories(${BULLET_INCLUDE_DIRS})
    set(${LIBRARIES} "${LIBRARIES};${BULLET_LIBRARIES}")
  endif()

  # [LIB] Eigen 3
  if (USE_LIB_EIGEN)
    include_directories(BEFORE "/usr/include/eigen3/")
  endif()

  # [LIB] Freetype
  if(USE_LIB_FREETPYE)
    find_package(freetype REQUIRED)
    include_directories(${FREETYPE_INCLUDE_DIRS})
    set(${LIBRARIES} "${LIBRARIES};${FREETYPE_LIBRARIES}")
  endif()

  # Locate the Panda3D headers
  find_path(PANDA_INCLUDE_DIR dtoolbase.h PATH_SUFFIXES panda3d)

  # Locate the Panda3D libraries

  set(REQ_LIBRARIES p3framework panda pandaexpress p3dtool p3dtoolconfig p3direct ${INTERROGATE_LIB})

  set(PANDA_LIBRARIES "")
  foreach (lib ${REQ_LIBRARIES})
    find_library(PANDA_LIBRARY_${lib} ${lib} PATH_SUFFIXES panda3d)
    set(PANDA_LIBRARIES "${PANDA_LIBRARIES};${PANDA_LIBRARY_${lib}}")
  endforeach()

  find_package_handle_standard_args(Panda DEFAULT_MSG
                                    PANDA_LIBRARIES PANDA_INCLUDE_DIR)

  if (NOT EXISTS ${PANDA_INCLUDE_DIR})
    # Okay, the standard package handling failed. Try finding a local panda3d installation

    # Find panda path
    execute_process(
      COMMAND "${PYTHON_EXECUTABLE}" "-B" "Scripts/common.py" "--print-sdk-path"
      OUTPUT_VARIABLE LOCAL_PANDA_PATH
      WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

    if (NOT EXISTS "${LOCAL_PANDA_PATH}/include")
      message(FATAL_ERROR "Could not find system wide panda3d headers, and no local installation was found!")
    endif()

    set(PANDA_INCLUDE_DIR "${LOCAL_PANDA_PATH}/include")

    set(PANDA_LIBRARIES "")
    foreach(lib ${REQ_LIBRARIES})
      find_library(PANDA_LIBRARY_${lib} ${lib} PATHS "${LOCAL_PANDA_PATH}/lib/")
      set(PANDA_LIBRARIES "${PANDA_LIBRARIES};${PANDA_LIBRARY_${lib}}")
    endforeach()


  endif()

endif()

# Link panda includes / libraries
include_directories("${PANDA_INCLUDE_DIR}")
include_directories("${PYTHON_INCLUDE_DIRS}")

# Run interrogate over the files
execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" "-B" "Scripts/interrogate.py" "${PROJECT_NAME}" "${IGATE_VERBOSE}"
    OUTPUT_VARIABLE output
    ERROR_VARIABLE errors
    RESULT_VARIABLE return_code
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

if (NOT ("${IGATE_VERBOSE}" STREQUAL "0" ))
  message(STATUS "IGATE stdout = ${output}")
  message(STATUS "IGATE stderr = ${errors}")
endif()

if(NOT ("${return_code}" STREQUAL "0"))
    message(FATAL_ERROR "Interrogate failed: ${output} ${errors}")
endif()

# Set compiler flags
if (MSVC)

  # This matches the makepanda options

  if (CMAKE_CL_64)
    add_definitions("/favor:blend /DWIN64_VC /DWIN64 /bigobj")
  endif()

  add_definitions("/wd4996 /wd4275 /wd4267 /wd4101 /wd4273")

  if (TOUCHINPUT_ENABLED)
    # If touchinput is enabled
    add_definitions("/DWINVER=0x601")
  else()
    # If touchinput is disabled
    # add_definitions("/DWINVER=0x501")
  endif()

  if(CMAKE_CL_32 AND ENABLE_SSE2)
    # If SSE is enabled
    add_definitions("/arch:SSE2")
  endif()

  # Different optimization settings
  if (OPTIMIZE STREQUAL "1")
    add_definitions("/MDd /Zi /RTCs /GS")
  elseif(OPTIMIZE STREQUAL "2")
    add_definitions("/MDd /Zi")
  elseif(OPTIMIZE STREQUAL "3")
    add_definitions("/MD /Zi /GS- /O2 /Ob2 /Oi /Ot /fp:fast")
  elseif(OPTIMIZE STREQUAL "4")
    add_definitions("/MD /Zi /GS- /Ox /Ob2 /Oi /Ot /fp:fast /DFORCE_INLINING /DNDEBUG /GL /LTCG")
    add_definitions("/Oy /Zp16")
  else()
    message(FATAL_ERROR "Invalid optimize value! Was: '${OPTIMIZE}'")
  endif()

  add_definitions("/Zm300 /DWIN32_VC /DWIN32")

  # No exceptions
  add_definitions("/D_HAS_EXCEPTIONS=0")

  # No RTTI
  add_definitions("/GR-")

  # Warning level 3 should be enough
  add_definitions("/W3")
  
  # Special case for 32 bit
  if(CMAKE_CL_32)
    add_definitions("/machine:x86")
  endif()

ELSE()
  
  # Assuming GCC here

  add_definitions("-ftemplate-depth-70 -fPIC -c")

  # On mac
  if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    add_definitions("-Wno-deprecated-declarations")
  endif()

  add_definitions("-pthread")
  add_definitions("-mtune=native -march=native -std=c++11")

  # No exceptions
  add_definitions("-fno-exceptions")

  # No RTTI
  # add_definitions("-fno-rtti")

  # Differnt optimization settings
  if (OPTIMIZE STREQUAL "1")
    add_definitions("-ggdb -D_DEBUG")
  elseif(OPTIMIZE STREQUAL "2")
    add_definitions("-O1 -D_DEBUG")
  elseif(OPTIMIZE STREQUAL "3")
    add_definitions("-O2")
    add_definitions("-fno-finite-math-only -ffast-math")
  elseif(OPTIMIZE STREQUAL "4")
    add_definitions("-O3 -DNDEBUG -ffast-math")
  else()
    message(FATAL_ERROR "Invalid optimize value! Was: '${OPTIMIZE}'")
  endif()

ENDIF()

# Define the module name
add_definitions("/DPB_MODULE=${PROJECT_NAME}")
add_definitions("/DPB_CFG_MODULE=${PROJECT_NAME}")

# Collect sources for compiling
file(GLOB_RECURSE SOURCES Source/*.cpp Source/*.cxx)
include_directories("Source/")
set(SOURCES ${SOURCES_H} ${SOURCES})

# Collect subdirs for compiling
file(GLOB POSSIBLE_DIRS RELATIVE ${CMAKE_CURRENT_LIST_DIR} Source/*)
foreach(PDIR ${POSSIBLE_DIRS})
  if (IS_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}/${PDIR})
    include_directories("${PDIR}")
  endif()
endforeach()

# Build library
add_library(${PROJECT_NAME} MODULE ${SOURCES})

# Don't add lib prefix on Linux
set_target_properties(${PROJECT_NAME} PROPERTIES PREFIX "")

# Add the required libraries
target_link_libraries(${PROJECT_NAME} ${PYTHON_LIBRARIES} ${PANDA_LIBRARIES} ${LIBRARIES})

# After building, copy the file to the current directory
add_custom_command(
    TARGET ${PROJECT_NAME}
    POST_BUILD
    COMMAND "${PYTHON_EXECUTABLE}" "-B" "${CMAKE_CURRENT_LIST_DIR}/Scripts/finalize.py" "${PROJECT_NAME}"
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})
