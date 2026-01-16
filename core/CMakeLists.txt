cmake_minimum_required(VERSION 3.10)
project(system_core)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Platform-specific settings
if(WIN32)
    add_definitions(-DBUILDING_DLL)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
endif()

# Source files
set(SOURCES
    src/system_core.cpp
    src/process_monitor.cpp
)

# Include directories
include_directories(include)

# Create shared library
add_library(system_core SHARED ${SOURCES})

# Platform-specific libraries
if(WIN32)
    target_link_libraries(system_core
        psapi
        kernel32
        user32
        gdi32
        winspool
        shell32
        ole32
        oleaut32
        uuid
        comdlg32
        advapi32
    )
endif()

# Installation
install(TARGETS system_core
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)