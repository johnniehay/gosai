cmake_minimum_required(VERSION 3.13)
project(adaptor C)

set(CMAKE_C_STANDARD 11)

include_directories(/home/johnnie/MEGA/code/gosai/SAI/inc)
include_directories(inc)
include_directories(gen-inc)
#link_directories(/home/johnnie/MEGA/code/gosai/lib/x86_64-linux-gnu)
link_directories(../lib/x86_64-linux-gnu)
AUX_SOURCE_DIRECTORY(gen-src SOURCELIST)

add_library(adaptor
#        src/funcdeftest.c
        ${SOURCELIST})
target_link_libraries(adaptor sai)
