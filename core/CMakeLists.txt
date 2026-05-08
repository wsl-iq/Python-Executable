cmake_minimum_required(VERSION 3.10)
project(SystemCore)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(WIN32)
    add_definitions(-DBUILDING_DLL)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
endif()

set(SOURCES
    src/SystemCore.cpp
    src/ProcessMonitor.cpp
)

include_directories(include)

add_library(SystemCore SHARED ${SOURCES})

if(WIN32)
    target_link_libraries(SystemCore
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

install(TARGETS SystemCore
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)