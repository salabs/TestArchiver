import os

ARCHIVER_VERSION = "2.2.0.dev"


def dynamic_package_version():
    version = ARCHIVER_VERSION
    build_number = None
    try:
        build_number = os.environ['BUILD_NUMBER_FOR_DEV_PACKAGE_VERSION']
    except KeyError:
        pass

    if build_number:
        # Not an official release
        if 'dev' not in version:
            # If not dev then release candidate
            version += 'rc'
        version += build_number

    return version
