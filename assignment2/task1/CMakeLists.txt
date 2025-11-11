cmake_minimum_required(VERSION 3.16)

project(Task1)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Protobuf CONFIG REQUIRED)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -ggdb -fno-omit-frame-pointer")

# add_executable(make_data make_data0.cpp my_schema.pb.cc)
# target_link_libraries(make_data PUBLIC protobuf::libprotobuf)

add_executable(decode_heap mysterious_heap.cpp payload_chunk.pb.cc)
target_link_libraries(decode_heap PUBLIC protobuf::libprotobuf)