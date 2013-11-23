Buildout Platform Versions (BPV)
================================

BPV lets you switch between sets of pinned dependencies more easily.

It's useful for testing a build with several dependency chains. For
example, you might be using one freeze of Turbogears in production, but
you might also want to test a new freeze in development.

Simple Example
--------------

Suppose that we're using flup 1.0.2 in production. We want the
production build to continue to use the old flup. But, we want to flip
between the production flup and a new flup on the dev box.

Developers can build and test with [production], [dev], or
[newest\_flup] by setting an environment variable

::

    export PLATFORM\_ENVIRONMENT\_VARIABLE=dev

Or writing a custom develop.cfg. Here's how BPV gets the job done:

buildout.cfg
~~~~~~~~~~~~

::

    [buildout]

    extensions = buildout_platform_versions

    # optionally
    # platform-versions-config = WHATEVER_SECTION

    [platform-versions-config]
    default-platform = production
    sources =
        some_config_enhance_file.cfg
        another_config_enhance_file.cfg
    platform-env = PLATFORM_ENVIRONMENT_VARIABLE

some\_config\_enhance\_file.cfg
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    [base]
    simplejson = 2.2.1
    flup = 1.0.2
    WebOb = 1.1.1
    Jinja2 = 2.6
    pymongo = 2.1

another\_config\_enhance\_file.cfg
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    [production]
    # the production environment uses the base config
    <<= <base

    [dev_flup]
    # wait, there's a new flup to try
    flup = 1.0.3dev

    [dev]
    # on dev boxes, we'll try the new flup
    <<= <production
        +dev_flup

    [newest_flup]
    # we'll unpin and check for a new flup
    <<= <production
        -dev_flup

Version File Sources
====================

BPV can read version rosters from a number of sources. We're
particularly proud of the egg source:

::

    egg://eggname/path/to/versions.cfg
    http://somewhere.com/versions/more_versions.cfg
    file:///home/me/config/local_versions.cfg
    relative_versions.cfg

The egg protocol support is hand crafted. Everything else relies on
urllib. If no protocol is specified, BPV assumes the sources are local
files relative to the buildout working directory.

A more complicated example
==========================

Using BPV to twiddle a single file is a bit overkill. Its power is more
evident when you have some big freezes to manage and need a longer
transition period:

::

    [TG2.1-v1]
    # frozen 2012-08-12
    TurboGears2 = 2.1.1
    transaction = 1.2.0
    tgext.admin = 0.3.12
    tgext.crud = 0.3.13
    ...

    [TG2.1-v2]
    # frozen 2013-04-01
    TurboGears2 = 2.1.1
    transaction = 1.4.1
    tgext.admin = 0.5.4
    tgext.crud = 1.0.2
    ...

    [production]
    # production versions are collected from a bunch of
    # frozen projects
    <<= +TG2.1-v1
        +several

    [dev]
    # in dev, use the production versions. But, remove
    # all the pins for the first freeze of TG, insert the
    # pins from the new freeze.
    <<= +production
        -TG2.1-v1
        <TG2.1-v2

Develop Eggs
===============

BPV loads the current version of develop eggs listed in {buildout:develop} and
uses those versions to override the explicit pins loaded from other sources.

It will also check for develop-packages listed in the platform-versions-config
section and unpin those entirely, so that they pick up whatever the highest
version is.

::

    [platform-versions-config]
    default-platform = production
    sources =
        some_config_enhance_file.cfg
        another_config_enhance_file.cfg
    develop-packages = flup
        tgext.admin




Related Projects
================

[config-enhance][https://github.com/zillow/config-enhance]
[buildout][https://github.com/buildout/buildout]

Source Code
===========

[contribute][https://github.com/zillow/buildout-platform-versions]
