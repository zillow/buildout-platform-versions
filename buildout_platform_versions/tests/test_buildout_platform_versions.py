from zc.buildout.buildout import Buildout

import os
import sys
import nose.tools as nt
from nose.tools import assert_equal
import logging

import buildout_platform_versions as bf

LOG = logging.getLogger(__name__)

def _testfname(fname):
    import os
    return os.path.join (os.path.dirname (__file__), fname)

# empty config shouldn't crash

empty_cfg = '''
'''

file(_testfname("empty.cfg"), "w").write (empty_cfg)

#--

def test_noop():
    buildout = Buildout(_testfname('empty.cfg'), [])

# simple config shouldn't regress

simple_cfg = '''
[buildout]
versions = versions

[versions]
alpha = 1.0
beta = 2.0
'''

file (_testfname("simple.cfg"), "w").write (simple_cfg)

#--

def test_regression():
    buildout = Buildout(_testfname('simple.cfg'), [])
    assert buildout["versions"]["alpha"] == "1.0"
    assert buildout["versions"]["beta"] == "2.0"
    assert_equal (2, len (buildout["versions"]))

# basic use of the extra versions extension 
versions_1_cfg = '''
[current]
beta = 2.0
gamma = 9.0

[next]
<<= <current
gamma = 10.0
'''
file (_testfname("versions_1.cfg"), "w").write(versions_1_cfg)

extra_cfg = '''
[buildout]
parts =
extensions = buildout_platform_versions
versions = versions

[platform-versions-config]
sources = ${buildout:directory}/versions_1.cfg
# default platform to use
default-platform = current
# platform variable to check for a different version
platform-env = ZILLOW_PYTHON_PLATFORM_VERSION

[versions]
alpha = 1.0
'''

file (_testfname("extra.cfg"), "w").write(extra_cfg)

next_cfg = '''
[buildout]
parts =
extensions = buildout_platform_versions
versions = versions

[platform-versions-config]
sources = ${buildout:directory}/versions_1.cfg
# default platform to use
default-platform = next

[versions]
alpha = 1.0
'''

file (_testfname("next.cfg"), "w").write(next_cfg)

develop_packages_cfg = '''
[buildout]
parts =
extensions = buildout_platform_versions
versions = versions

[platform-versions-config]
sources = ${buildout:directory}/versions_1.cfg
# default platform to use
default-platform = next
develop-packages = gamma

[versions]
alpha = 1.0
'''

file (_testfname("develop_packages.cfg"), "w").write(develop_packages_cfg)

develop_eggs_cfg = '''
[buildout]
parts =
extensions = buildout_platform_versions
versions = versions
develop = ${buildout:directory}

[platform-versions-config]
sources = ${buildout:directory}/versions_1.cfg
# default platform to use
default-platform = next

[versions]
alpha = 1.0
'''

file (_testfname("develop_eggs.cfg"), "w").write(develop_eggs_cfg)

gamma_setup_py = '''
import os
import logging
import sys
from setuptools import setup

setup(name="gamma", version="1.0.0.d")
'''

file (_testfname("setup.py"), "w").write(gamma_setup_py)


#--


def test_read_package_name_from_setup_py_bad():
    from buildout_platform_versions import read_package_name_from_setup_py
    vv = read_package_name_from_setup_py ("/some/path/that/doesnt/exist/120i109jsjiasidniosandionwdaw")
    nt.assert_equal (None, vv)

def test_read_package_name_from_pkg_resources_bad():
    from buildout_platform_versions import read_package_name_from_pkg_resources
    vv = read_package_name_from_pkg_resources ("/some/path/that/doesnt/exist/120i109jsjiasidniosandionwdaw")
    nt.assert_equal (None, vv)

def test_platform_versions():
    buildout = Buildout(_testfname('extra.cfg'), [])
    bf.start (buildout)
    #print "platform-versions-config", buildout["platform-versions-config"]
    assert buildout["versions"]["alpha"] == "1.0"
    assert buildout["versions"]["beta"] == "2.0"
    assert buildout["versions"]["gamma"] == "9.0"
    assert len(buildout["versions"]) == 3

def test_next_platform_versions():
    buildout = Buildout(_testfname('next.cfg'), [])
    bf.start (buildout)
    #print "platform-versions-config", buildout["platform-versions-config"]
    assert buildout["versions"]["alpha"] == "1.0"
    assert buildout["versions"]["beta"] == "2.0"
    assert buildout["versions"]["gamma"] == "10.0"
    assert len(buildout["versions"]) == 3

def test_develop_packages_platform_versions():
    buildout = Buildout(_testfname('develop_packages.cfg'), [])
    bf.start (buildout)
    #print "platform-versions-config", buildout["platform-versions-config"]
    assert buildout["versions"]["alpha"] == "1.0"
    assert buildout["versions"]["beta"] == "2.0"
    nt.assert_true (not buildout["versions"].has_key("gamma"))
    assert len(buildout["versions"]) == 2

def test_develop_eggs_platform_versions():
    buildout = Buildout(_testfname('develop_eggs.cfg'), [])
    bf.start (buildout)
    #print "platform-versions-config", buildout["platform-versions-config"]
    assert buildout["versions"]["alpha"] == "1.0"
    assert buildout["versions"]["beta"] == "2.0"
    assert buildout["versions"]["gamma"] == "1.0.0.d"
    assert len(buildout["versions"]) == 3 


def test_platform_versions_env():
    old_env = os.environ.get ("ZILLOW_PYTHON_PLATFORM_VERSION", None)
    os.environ["ZILLOW_PYTHON_PLATFORM_VERSION"] = "next"
    buildout = Buildout(_testfname('extra.cfg'), [])
    bf.start (buildout)
    #print "platform-versions-config", buildout["platform-versions-config"]
    assert buildout["versions"]["alpha"] == "1.0"
    assert buildout["versions"]["beta"] == "2.0"
    assert buildout["versions"]["gamma"] == "10.0"
    assert len(buildout["versions"]) == 3
    if old_env:
        os.environ["ZILLOW_PYTHON_PLATFORM_VERSION"] = old_env
    else:
        del os.environ["ZILLOW_PYTHON_PLATFORM_VERSION"]


