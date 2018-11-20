from conans import ConanFile, CMake, tools
# import os
from ci_utils import BitprimCxx11ABIFixer

def option_on_off(option):
    return "ON" if option else "OFF"

class ZMQConan(BitprimCxx11ABIFixer):
    name = "libzmq"
    version = "4.2.2"
    version_flat = "4_2_2"
    license = "LGPL"
    url = "https://github.com/bitprim/bitprim-conan-zmq.git"
    description = "ZMQ is a network, sockets on steroids library. Safe for use in commercial applications LGPL v3 with static linking exception"
    settings = "os", "compiler", "build_type", "arch"

    options = {
               "shared": [True, False],
               "fPIC": [True, False],
               "verbose": [True, False],
               "glibcxx_supports_cxx11_abi": "ANY",
    }

    default_options = "shared=False", \
                      "fPIC=True", \
                      "verbose=True", \
                      "glibcxx_supports_cxx11_abi=_DUMMY_",

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
        self.output.info('*-*-*-*-*-* def config_options(self):')
        if self.settings.compiler == "Visual Studio":
            self.options.remove("fPIC")

            if self.options.shared and self.msvc_mt_build:
                self.options.remove("shared")

    def configure(self):
        BitprimCxx11ABIFixer.configure(self)


    def package_id(self):
        BitprimCxx11ABIFixer.package_id(self)

        self.info.options.verbose = "ANY"

        # #For Bitprim Packages libstdc++ and libstdc++11 are the same
        # if self.settings.compiler == "gcc" or self.settings.compiler == "clang":
        #     if str(self.settings.compiler.libcxx) == "libstdc++" or str(self.settings.compiler.libcxx) == "libstdc++11":
        #         self.info.settings.compiler.libcxx = "ANY"

    def source(self):

        self.run("git -c http.sslVerify=false clone https://github.com/zeromq/libzmq.git")
        # self.run("git clone https://github.com/zeromq/libzmq.git")
        # self.run("git clone git@github.com:zeromq/libzmq.git")

        self.run("cd libzmq && git checkout tags/v4.2.2 -b bitprim_4.2.2")

#         tools.replace_in_file("libzmq/CMakeLists.txt", "project (ZeroMQ)", """project (ZeroMQ)
# include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
# conan_basic_setup()
# """)

        tools.replace_in_file("libzmq/CMakeLists.txt", "project (ZeroMQ)", """project (ZeroMQ)
if(EXISTS ${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()

    remove_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)
    remove_definitions(-D_GLIBCXX_USE_CXX11_ABI=1)

    if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU" OR "${CMAKE_CXX_COMPILER_ID}" MATCHES "Clang")
        if (NOT NOT_USE_CPP11_ABI)
            add_definitions(-D_GLIBCXX_USE_CXX11_ABI=1)
            message( STATUS "Bitprim: Using _GLIBCXX_USE_CXX11_ABI=1")
        else()
            add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)
            message( STATUS "Bitprim: Using _GLIBCXX_USE_CXX11_ABI=0")
        endif()
        # set(CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wno-macro-redefined")
        # set(CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wno-builtin-macro-redefined")
    endif()
else()
    message(WARNING "The file conanbuildinfo.cmake doesn't exist, you have to run conan install first")
endif()
""")      

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
       
        cmake_cmd_1 = 'cmake libzmq %s %s %s -DCMAKE_CXX_FLAGS="-std=c++11" -DCMAKE_SH="CMAKE_SH-NOTFOUND" -DZMQ_BUILD_TESTS=OFF -DZMQ_BUILD_FRAMEWORK=OFF' % (cmake.command_line, verbose_str, cxx11_abi_str)
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
