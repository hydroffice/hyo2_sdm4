import codecs
import os
import re
import numpy as np

# Always prefer setuptools over distutils
from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

# ------------------------------------------------------------------
#                         HELPER FUNCTIONS

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(str(os.path.join(here, *parts)), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M, )
    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")


# ------------------------------------------------------------------
#                          POPULATE SETUP

setup(
    name="hyo2.sdm4",
    version=find_version("hyo2", "sdm4", "__init__.py"),
    license='LGPLv2.1 or CCOM-UNH Industrial Associate license',

    namespace_packages=["hyo2"],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "*.test*", ]),
    package_data={
        "": [
            'sdm4/media/*.png',
        ],
    },
    zip_safe=False,
    setup_requires=[
        "setuptools",
        "wheel",
        "cython",
    ],
    install_requires=[
        "hyo2.abc2>=2.4.3",
        "hyo2.ssm2>=2025.1.6",
        "hyo2.huddl"
    ],
    ext_modules=cythonize([
        Extension("hyo2.sdm4.lib.estimate.casttime.casttime",
                  sources=["hyo2/sdm4/lib/estimate/casttime/casttime.pyx"],
                  include_dirs=[np.get_include()],
                  language='c++',
                  ),
    ], annotate=True),
    python_requires='>=3.11',
    entry_points={
        "gui_scripts": [
            'survey_data_monitor = hyo2.sdm4.app.gui.surveydatamonitor.gui:gui',
        ],
        "console_scripts": [
        ],
    },
    test_suite="tests",

    description="A library to monitor ocean mapping surveys.",
    long_description=(read("README.rst") + "\n\n\"\"\"\"\"\"\"\n\n" +
                      read("HISTORY.rst") + "\n\n\"\"\"\"\"\"\"\n\n" +
                      read("AUTHORS.rst") + "\n\n\"\"\"\"\"\"\"\n\n" +
                      read(os.path.join("docs", "how_to_contribute.rst")))
    ,
    url="https://github.com/hydroffice/hyo2_sdm4",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Office/Business :: Office Suites',
    ],
    keywords="hydrography ocean mapping survey sound speed profiles",
    author="Giuseppe Masetti(UNH,JHC-CCOM)",
    author_email="gmasetti@ccom.unh.edu"
)
