

cmake_minimum_required (VERSION 2.6)
project (RSNative)
set(CMAKE_BUILD_TYPE "Release")

if (WIN32)
  
  # Default settings for windows. Usually you only have to adjust this two variables
  set(WIN_PANDA_PATH "D:/P3D/1.9GIT" CACHE PATH "Location of the Panda3D source directory")
  set(BUILD_DIR_NAME "built_x64_buffered" CACHE PATH "Name of the output folder, usually built or built_x64")

  # These vars are based on the WIN_PANDA_PATH and usually are correct
  set(PANDA_BIN "${WIN_PANDA_PATH}/${BUILD_DIR_NAME}/bin")
  set(PANDA_LIBRARY_DIRS "${WIN_PANDA_PATH}/${BUILD_DIR_NAME}/lib")
  set(PANDA_INCLUDE_DIR "${WIN_PANDA_PATH}/${BUILD_DIR_NAME}/include")
  set(PANDA_THIRDPARTY "${WIN_PANDA_PATH}/thirdparty/win-libs-vc10-x64")

  set(PYTHON_LIBRARIES "${WIN_PANDA_PATH}/${BUILD_DIR_NAME}/python/libs/python27.lib")
  set(PYTHON_INCLUDE_DIRS "${WIN_PANDA_PATH}/${BUILD_DIR_NAME}/python/include")
  set(PYTHON_EXECUTABLE "${WIN_PANDA_PATH}/${BUILD_DIR_NAME}/python/python.exe")

  set(BULLET_LIBRARIES "")
  set(BULLET_INCLUDE_DIRS "${PANDA_THIRDPARTY}/bullet/include")

  # Check if all supplied files exist
  set(CHECK_PATHS ${PANDA_BIN} ${PANDA_LIBS} ${PANDA_LIBRARY_DIRS} ${PANDA_INCLUDE_DIR} ${PYTHON_LIBRARIES} ${PYTHON_INCLUDE_DIRS} ${PYTHON_EXECUTABLE} ${PANDA_THIRDPARTY})
  foreach(PATH ${CHECK_PATHS})
    if(NOT (EXISTS "${PATH}"))
        message(FATAL_ERROR "The supplied path '${PATH}' does not exist! Correct the path in CMakeLists.txt!")
    endif()
  endforeach()

  set(PANDA_LIBRARIES "libp3framework;libpanda;libpandaexpress;libp3dtool;libp3dtoolconfig;libp3direct;libp3interrogatedb")
  link_directories("${PANDA_LIBRARY_DIRS}")

else()

  find_package(PythonLibs REQUIRED)
  find_package(PythonInterp REQUIRED)
  find_package(Bullet)


  # Locate the headers
  find_path(PANDA_INCLUDE_DIR dtoolbase.h PATH_SUFFIXES panda3d)

  # Locate the libraries
  set(PANDA_LIBRARIES "")
  foreach(lib pandabullet p3framework panda pandaexpress p3dtool p3dtoolconfig p3direct p3interrogatedb)
    find_library(PANDA_LIBRARY_${lib} ${lib} PATH_SUFFIXES panda3d)
    set(PANDA_LIBRARIES "${PANDA_LIBRARIES};${PANDA_LIBRARY_${lib}}")
  endforeach()

  find_package_handle_standard_args(Panda DEFAULT_MSG
                                    PANDA_LIBRARIES PANDA_INCLUDE_DIR)

  if(NOT EXISTS ${PANDA_INCLUDE_DIR})
    message(FATAL_ERROR "Could not find panda3d headers!")
  endif()

  set(PANDA_BIN "/usr/bin" CACHE PATH "Location of Panda tools such as Interrogate")

endif()


# Make sure interrogate exists
if(NOT (EXISTS "${PANDA_BIN}/interrogate") AND NOT (EXISTS "${PANDA_BIN}/interrogate.exe"))
    message(FATAL_ERROR "Could not locate interrogate executable in ${PANDA_BIN}! Correct the path in CMakeLists.txt!")
endif()


# Link panda includes / libraries
include_directories("${PANDA_INCLUDE_DIR}")

# Also link python includes / libraries
include_directories("${PYTHON_INCLUDE_DIRS}")
include_directories("${BULLET_INCLUDE_DIRS}")

# Run interrogate over the files
# message("Running interrogate ..")

execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" "Scripts/interrogate.py" "${PANDA_BIN}" "${PANDA_LIBS}" "${PANDA_INCLUDE_DIR}"
    OUTPUT_VARIABLE output
    ERROR_VARIABLE errors
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

if(NOT (${errors} STREQUAL ""))
    message(FATAL_ERROR "Interrogate failed: ${errors}")
endif()

message("Interrogate output: ${output} ${errors}")

# Collect sources for compiling
file(GLOB SOURCES Source/*.cpp)
set(SOURCES ${SOURCES_H} ${SOURCES})

# Optimizations
IF(MSVC)
    # sse2 is faster
    ADD_DEFINITIONS("/arch:SSE2")

    # ADD_DEFINITIONS("/Ox")
    ADD_DEFINITIONS("/Ot")
    ADD_DEFINITIONS("/fp:fast")
    ADD_DEFINITIONS("/MD")
    ADD_DEFINITIONS("/wd4275")
    ADD_DEFINITIONS("/wd4018")
    ADD_DEFINITIONS("/wd4267")
    ADD_DEFINITIONS("/wd4996")
    ADD_DEFINITIONS("/wd4101")

    ADD_DEFINITIONS("/D WIN32 /D CRT_SECURE_NO_WARNINGS /D _WINDOWS /D _USRDLL")

ELSE()
   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mtune=native -march=native")
ENDIF()
   

# Build library
add_library(RSNative MODULE ${SOURCES})

# Python wants .pyd on windows
IF (WIN32)
  set_target_properties(RSNative 
    PROPERTIES 
    SUFFIX ".pyd")
ENDIF()

# Don't add lib prefix on Linux
set_target_properties(RSNative PROPERTIES PREFIX "")

FOREACH (flags_var_to_scrub
    CMAKE_CXX_FLAGS_RELEASE
    CMAKE_CXX_FLAGS_RELWITHDEBINFO
    CMAKE_CXX_FLAGS_MINSIZEREL
    CMAKE_C_FLAGS_RELEASE
    CMAKE_C_FLAGS_RELWITHDEBINFO
    CMAKE_C_FLAGS_MINSIZEREL)
  string (REGEX REPLACE "(^| )[/-]D *NDEBUG($| )" " "
    "${flags_var_to_scrub}" "${${flags_var_to_scrub}}")
ENDFOREACH()

target_link_libraries(RSNative ${PYTHON_LIBRARIES} ${PANDA_LIBRARIES} ${BULLET_LIBRARIES})

# After building, copy the file to the current directory
add_custom_command(
    TARGET RSNative
    POST_BUILD
    COMMAND "${PYTHON_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/Scripts/finalize.py" "$<TARGET_FILE:RSNative>"
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

