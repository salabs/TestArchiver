import setuptools

from test_archiver.version import dynamic_package_version

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name="testarchiver",
    version=dynamic_package_version(),
    author="Tommi Oinonen",
    author_email="salabs-mail@siili.com",
    description="Tools for serialising test results to SQL database ",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/salabs/TestArchiver",
    license="Apache License 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing",
    ],
    keywords='robotframework test report history',

    packages=setuptools.find_packages(),
    python_requires='>=3.0',
    install_requires=['psycopg2-binary>=2.8.5'],
    include_package_data=True,
    zip_safe=False,

    scripts=['helpers/diff2change_context_list.py'],
    entry_points={
        'console_scripts': [
            'testarchiver=test_archiver.output_parser:main',
            'testarchive_schematool=test_archiver.database:main',
        ]
    },
)
