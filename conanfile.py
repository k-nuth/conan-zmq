# Copyright (c) 2016-2020 Knuth Project developers.
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import os
import glob
import platform
import shutil
from conans import tools, CMake
from kthbuild import KnuthConanFile, option_on_off

class ZMQConan(KnuthConanFile):
    def recipe_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    name = "libzmq"
    version = "4.3.2"
    version_flat = "4_3_2"
    license = "LGPL"
    url = "https://github.com/k-nuth/conan-zmq.git"
    description = "ZMQ is a network, sockets on steroids library. Safe for use in commercial applications LGPL v3 with static linking exception"
    settings = "os", "compiler", "build_type", "arch"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "verbose": [True, False],

        "microarchitecture": "ANY",
        "fix_march": [True, False],
        "march_id": "ANY",

        "cxxflags": "ANY",
        "cflags": "ANY",
        "glibcxx_supports_cxx11_abi": "ANY",
    }

    default_options = {
        "shared": False,
        "fPIC": True,
        "verbose": True,
        "microarchitecture": '_DUMMY_',
        "fix_march": False,
        "march_id": '_DUMMY_',
        "cxxflags": '_DUMMY_',
        "cflags": '_DUMMY_',
        "glibcxx_supports_cxx11_abi": '_DUMMY_',
    }


    exports = "FindZeroMQ.cmake", "conan_*", "ci_utils/*"
    generators = "cmake"
    build_policy = "missing"

    @property
    def msvc_mt_build(self):
        return "MT" in str(self.settings.compiler.runtime)

    @property
    def fPIC_enabled(self):
        if self.settings.compiler == "Visual Studio":
            return False
        else:
            return self.options.fPIC

    @property
    def is_shared(self):
        if self.settings.compiler == "Visual Studio" and self.msvc_mt_build:
            return False
        else:
            return self.options.shared

    def config_options(self):
        KnuthConanFile.config_options(self)

    def configure(self):
        KnuthConanFile.configure(self)

    def package_id(self):
        KnuthConanFile.package_id(self)

    def source(self):

        self.run("git -c http.sslVerify=false clone https://github.com/zeromq/libzmq.git")
        # self.run("git clone https://github.com/zeromq/libzmq.git")
        # self.run("git clone git@github.com:zeromq/libzmq.git")

        self.run("cd libzmq && git checkout tags/v4.3.2 -b kth_4.3.2")

        tools.replace_in_file("libzmq/CMakeLists.txt", "project(ZeroMQ)", """project(ZeroMQ)
if(EXISTS ${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()

    remove_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)
    remove_definitions(-D_GLIBCXX_USE_CXX11_ABI=1)

    if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU" OR "${CMAKE_CXX_COMPILER_ID}" MATCHES "Clang")
        if (NOT NOT_USE_CPP11_ABI)
            add_definitions(-D_GLIBCXX_USE_CXX11_ABI=1)
            message( STATUS "Knuth: Using _GLIBCXX_USE_CXX11_ABI=1")
        else()
            add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)
            message( STATUS "Knuth: Using _GLIBCXX_USE_CXX11_ABI=0")
        endif()
        # set(CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wno-macro-redefined")
        # set(CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wno-builtin-macro-redefined")
    endif()
else()
    message(WARNING "The file conanbuildinfo.cmake doesn't exist, you have to run conan install first")
endif()
""")      

        tools.replace_in_file("libzmq/CMakeLists.txt", 
            'check_cxx_compiler_flag("-std=gnu++11" COMPILER_SUPPORTS_CXX11)',
            'check_cxx_compiler_flag("-std=gnu++17" COMPILER_SUPPORTS_CXX17)')

        tools.replace_in_file("libzmq/CMakeLists.txt", 
            'if(COMPILER_SUPPORTS_CXX11)',
            'if(COMPILER_SUPPORTS_CXX17)')

        tools.replace_in_file("libzmq/CMakeLists.txt", 
            '-std=gnu++11',
            '-std=gnu++17')

    def build(self):
        # cmake = CMake(self.settings)
        cmake = CMake(self)

        verbose_str = '-DCMAKE_VERBOSE_MAKEFILE=%s' % (option_on_off(self.options.verbose),)

        cxx11_abi_str = ''
        if self.settings.compiler == "gcc":
            if float(str(self.settings.compiler.version)) >= 5:
                cxx11_abi_str = '-DNOT_USE_CPP11_ABI=OFF'
            else:
                cxx11_abi_str = '-DNOT_USE_CPP11_ABI=ON'
        elif self.settings.compiler == "clang":
            if str(self.settings.compiler.libcxx) == "libstdc++" or str(self.settings.compiler.libcxx) == "libstdc++11":
                cxx11_abi_str = '-DNOT_USE_CPP11_ABI=OFF'
       
        cmake_cmd_1 = 'cmake libzmq %s %s %s -DCMAKE_CXX_FLAGS="-std=c++17" -DCMAKE_SH="CMAKE_SH-NOTFOUND" -DZMQ_BUILD_TESTS=OFF -DZMQ_BUILD_FRAMEWORK=OFF' % (cmake.command_line, verbose_str, cxx11_abi_str)
        cmake_cmd_2 = "cmake --build . %s" % cmake.build_config

        self.output.info(self.settings.compiler)
        self.output.info(self.settings.compiler.version)
        self.output.info(cmake_cmd_1)
        self.output.info(cmake_cmd_2)

        self.run(cmake_cmd_1)
        self.run(cmake_cmd_2)

        # self.run('cmake libzmq %s -DZMQ_BUILD_TESTS=OFF -DZMQ_BUILD_FRAMEWORK=OFF' % cmake.command_line)
        # self.run("cmake --build . %s" % cmake.build_config)

    def package(self):

        # self.copy_headers("*", "libzmq/include")
        self.copy("*.h", dst="include", src="libzmq/include", keep_path=True)
        self.copy("*.hpp", dst="include", src="libzmq/include", keep_path=True)

        self.copy("FindZeroMQ.cmake")
        if not self.options.shared:
            self.copy("*libzmq*-mt-s*.lib", "lib", "lib", keep_path=False)
            self.copy("*.a", "lib", "lib", keep_path=False)  # Linux
        else:
            self.copy("*libzmq*-mt-%s.lib" % self.version_flat, "lib", "lib", keep_path=False)
            self.copy("*libzmq*-mt-gd-%s.lib" % self.version_flat, "lib", "lib", keep_path=False)
            self.copy("*.dll", "bin", "bin", keep_path=False)
            self.copy("*.dylib", "lib", "lib", keep_path=False)
            self.copy("libzmq.so*", "lib", "lib", keep_path=False)  # Linux

    def package_info(self):
        if self.settings.os != "Windows":
            # self.cpp_info.libs = ["zmq-static"] if not self.options.shared else ["zmq"]
            self.cpp_info.libs = ["zmq"]
        else:
            if self.settings.compiler == "Visual Studio":
                ver = ""

                if str(self.settings.compiler.version) in ["11", "12", "14"]:  
                    ver = "-v%s0" % self.settings.compiler.version
                elif str(self.settings.compiler.version) ==  "15":  
                    ver = "-v141"
                elif str(self.settings.compiler.version) ==  "16":  
                    ver = "-v142"
                else:
                    self.output.info(self.settings.compiler.version)
                    ver = "-"

                # static, stat_fix = ("-static", "s") if not self.options.shared else ("", "")
                stat_fix = "s" if not self.options.shared else ""
                debug_fix = "gd" if self.settings.build_type == "Debug" else ""
                fix = ("-%s%s" % (stat_fix, debug_fix)) if stat_fix or debug_fix else ""

                # self.cpp_info.libs = ["libzmq%s%s-mt%s-%s" % (static, ver, fix, self.version_flat)]
                # self.output.info("libzmq%s%s-mt%s-%s" % (static, ver, fix, self.version_flat))

                self.cpp_info.libs = ["libzmq%s-mt%s-%s" % (ver, fix, self.version_flat)]
                self.output.info("libzmq%s-mt%s-%s" % (ver, fix, self.version_flat))
            else: # MinGW
                self.cpp_info.libs = ["zmq"]
                
        if not self.options.shared:
            # if self.settings.compiler == "Visual Studio":
            if self.settings.os == "Windows":
                self.cpp_info.libs.extend(["ws2_32", "wsock32", "Iphlpapi"])
            self.cpp_info.defines = ["ZMQ_STATIC"]

            if not self.settings.os == "Windows":
                self.cpp_info.cppflags = ["-pthread"]
        
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "dl", "rt"])
