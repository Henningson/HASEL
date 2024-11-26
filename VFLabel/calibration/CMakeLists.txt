cmake_minimum_required(VERSION 3.0.0)
project(LsrCamCalib VERSION 0.1.0)
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

if(MSVC)
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /std:c++17")
else()
	set(CMAKE_CXX_STANDARD 17)
endif(MSVC)

set(CMAKE_CXX_STANDARD_REQUIRED ON)

#set(CMAKE_INCLUDE_CURRENT_DIR ON)
#set(CMAKE_AUTOMOC ON)
#set(CMAKE_AUTOUIC ON)
#set(CMAKE_AUTORCC ON)

include_directories(include)
file(GLOB_RECURSE HEADER_FILES include/*.h )
file(GLOB_RECURSE SOURCE_FILES source/*.cpp )

add_compile_definitions(_USE_MATH_DEFINES)

message(STATUS "Header Files: " ${HEADER_FILES})
message(STATUS "Header Files: " ${SOURCE_FILES})

#EIGEN
find_package(Eigen3 REQUIRED)

#OPENCV
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

#Ceres
find_package(Ceres REQUIRED)

add_executable(LsrCamCalib ${HEADER_FILES} ${SOURCE_FILES} ${UI_FILES} ${RESOURCE_FILES})

set_property (TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 17)

target_include_directories(LsrCamCalib PRIVATE ${PROJECT_SOURCE_DIR}/include ${CERES_INCLUDE_DIRS})
target_link_libraries(LsrCamCalib Eigen3::Eigen ${OpenCV_LIBS} ${CERES_LIBRARIES})
