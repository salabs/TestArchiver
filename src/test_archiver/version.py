# import os

# ARCHIVER_VERSION = "3.0.0"


# def dynamic_package_version():
#     version = ARCHIVER_VERSION
#     build_number = None
#     try:
#         build_number = os.environ['BUILD_NUMBER_FOR_DEV_PACKAGE_VERSION']
#     except KeyError:
#         pass

#     if build_number:
#         # Not an official release
#         if 'dev' not in version:
#             # If not dev then release candidate
#             version += 'rc'
#         version += build_number

#     return version

from pathlib import Path

DEFAULT_VERSION = "0.0.1"

version_file = Path(__file__).parent / 'version.txt'
ARCHIVER_VERSION = version_file.read_text().strip() if version_file.exists() else DEFAULT_VERSION
