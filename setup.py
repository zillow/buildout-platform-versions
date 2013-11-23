__VERSION__ = "1.2.0"

import os
from setuptools import setup

def read(fname):
    '''Utility function to read the README file.'''
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

install_requires = ["zc.buildout", "config-enhance", "setuptools>=0.6c11"]
tests_require = ["Nose >=1.1.2", "mock >=0.7.2", "NoseXUnit"] + install_requires

setup(
    name = "buildout-platform-versions",
    version = __VERSION__,
    author = "Jonathan Ultis",
    author_email = "jonathanu@zillow.com",
    description = "improved version management",
    zip_safe = True,
    license = read("LICENSE"),
    keywords = "zillow",
    url = "http://github.com/zillow/buildout-platform-versions",
    packages = ['buildout_platform_versions'],
    long_description = read('README.rst'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Topic :: Utilities",
    ],
    install_requires = install_requires,
    tests_require = tests_require,
    test_suite = "nose.collector",
    entry_points = {
        'zc.buildout.extension': ['ext = buildout_platform_versions:start'],
        'zc.buildout.unloadextension': ['ext = buildout_platform_versions:finish'],
        }
    )
