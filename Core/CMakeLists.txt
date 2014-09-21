

cmake_minimum_required (VERSION 2.6)
project (RPCore)
set(CMAKE_BUILD_TYPE "Release")



# Configure this variables to match your system
# No trailing slash
if (WIN32)
  
  # Default settings for windows. Usually you only have to adjust WIN_PANDA_PATH
  set (WIN_PANDA_PATH "F:/P3D/1.9.0-1")

  # These vars are based on the WIN_PANDA_PATH and usually are correct
  set(PANDA_SRC "${WIN_PANDA_PATH}/")
  set(PANDA_BIN "${WIN_PANDA_PATH}/built_x64/bin")
  set(PANDA_LIBS "${WIN_PANDA_PATH}/built_x64/lib")
  set(PANDA_INCLUDE "${WIN_PANDA_PATH}/built_x64/include")
  set(PYTHON_LIBS "${WIN_PANDA_PATH}/built_x64/python/libs")
  set(PYTHON_INCLUDE "${WIN_PANDA_PATH}/built_x64/python/include")
  set(PYTHON_BIN "${WIN_PANDA_PATH}/built_x64/python")
  set(PANDA_THIRDPARTY "${WIN_PANDA_PATH}/thirdparty/win-libs-vc10-x64")

else()

  message( FATAL_ERROR "Linux not supported yet" )

endif()


# Check if all supplied directories exist
set(CHECK_DIRS ${PANDA_SRC} ${PANDA_BIN} ${PANDA_LIBS} ${PANDA_INCLUDE} ${PYTHON_LIBS} ${PYTHON_INCLUDE} ${PYTHON_BIN} ${PANDA_THIRDPARTY})
foreach(DIRECTORY ${CHECK_DIRS})
  message("Checking directory '${DIRECTORY}'")
  if(NOT (EXISTS "${DIRECTORY}" AND IS_DIRECTORY "${DIRECTORY}"))
      message(FATAL_ERROR "The supplied directory '${DIRECTORY}' does not exist! Correct the path in CMakeLists.txt!")
  endif()
endforeach()

# Link panda includes / libraries
include_directories("${PANDA_INCLUDE}")
link_directories("${PANDA_LIBS}")

# Also link python includes / libraries
include_directories("${PYTHON_INCLUDE}")
link_directories("${PYTHON_LIBS}")

# Thirdparty includes
include_directories("${PANDA_THIRDPARTY}/eigen/include")
include_directories("${PANDA_THIRDPARTY}/bullet/include")

# Run interrogate over the files
message("Running interrogate ..")

execute_process(
    COMMAND "${PYTHON_BIN}/python" "interrogate.py" "${PANDA_BIN}" "${PANDA_LIBS}" "${PANDA_INCLUDE}"
    OUTPUT_VARIABLE output
    ERROR_VARIABLE errors
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})

message("Interrogate output: ${output} ${errors}")

# Collect sources for compiling
file(GLOB SOURCES Source/*.cxx)

set(SOURCES ${SOURCES_H} ${SOURCES})

# Link python library
IF (WIN32)
    set(LIBRARIES "python27.dll")
ELSE()
    set(LIBRARIES "libpython27.so")
ENDIF()

# Link panda libraries
set(LIBRARIES ${LIBRARIES} "libpandabullet.lib")
set(LIBRARIES ${LIBRARIES} "libp3framework.lib")
set(LIBRARIES ${LIBRARIES} "libpanda.lib")
set(LIBRARIES ${LIBRARIES} "libpandaexpress.lib")
set(LIBRARIES ${LIBRARIES} "libp3dtool.lib")
set(LIBRARIES ${LIBRARIES} "libp3dtoolconfig.lib")
set(LIBRARIES ${LIBRARIES} "libp3direct.lib")

# Optimizations
IF(MSVC)
   # sse2 is faster
   ADD_DEFINITIONS("/arch:SSE2")

   # optimize for speed, not size
   ADD_DEFINITIONS("/Ot")
   ADD_DEFINITIONS("/fp:fast")

ELSE()
   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -msse -msse2 -msse3 -mtune=native -march=native")
ENDIF()


# Build library
add_library(RPCore MODULE ${SOURCES})

# Python wants .pyd on windows
IF (WIN32)
  set_target_properties(RPCore 
    PROPERTIES 
    SUFFIX ".pyd")
ENDIF()


target_link_libraries(RPCore ${LIBRARIES})

# After building, copy the file to the current directory
add_custom_command(
    TARGET RPCore
    POST_BUILD
    COMMAND "${PYTHON_BIN}/python" "finalize.py" "$<TARGET_FILE:RPCore>"
    WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR})
