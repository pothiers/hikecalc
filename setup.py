# see https://packaging.python.org/tutorials/packaging-projects/#configuring-metadata
# python3 -m build --wheel; twine upload dist/*

import setuptools
from codecs import open  # To use a consistent encoding
from os import path
import sys
sys.path.append(".")
from hikecalc import __version__

here = path.abspath(path.dirname(__file__))

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Get the long description from the relevant file
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open("requirements.txt") as f:
    install_require = f.read().splitlines()

setuptools.setup(
    name='hikecalc',
    version=__version__, # see hikecalc/__init__.py

    author='The Python Packaging Authority',   # @@@
    author_email='pypa-dev@googlegroups.com',  # @@@

    description='Calculate hikes given various constraints.',
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/pothiers/hikecalc',

    project_urls={
        "Documentation":"https://hikecalc.readthedocs.io/en/latest/",
        },

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: End Users/Desktop',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],

    # What does your project relate to?
    keywords='hike plan calculate',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests*']),

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    install_requires=[''],
    python_requires=">=3.6",

    # List additional groups of dependencies here (e.g. development dependencies).
    # You can install these using the following syntax, for example:
    # $ pip install -e .[dev,test]
    extras_require = {
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'hikecalc': ['data/catalinal-distance-list.txt'],
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    #data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'hc=hikecalc.hike_calc:main',
            'hikecalc=hikecalc.cli:main',
        ],
    },
)
