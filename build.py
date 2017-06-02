from conan.packager import ConanMultiPackager


if __name__ == "__main__":
    builder = ConanMultiPackager(username="memsharded", channel="testing", visual_versions=["10", "12", "14", "15"])
    builder.add_common_builds(shared_option_name="libzmq:shared")
    
    named_builds = {}
    for settings, options, env_vars, build_requires in builder.builds:
        named_build = named_builds.setdefault("%s_%s_%s" % (settings["compiler"].replace(" ", ""), settings["compiler.version"], settings["arch"]), [])
        named_build.append([settings, options, env_vars, build_requires])
    builder.builds = []
    builder.named_builds = named_builds

    builder.run()