import os
import logging
import pkgutil
import pkg_resources
import ConfigParser
import re

import zc.buildout
import config_enhance
import subprocess
import sys

__ALL__ = ["PlatformVersions", "start", "finish"]

EGG_URI_RE = re.compile ("egg://(?P<egg>[^/]+)/(?P<path>.*)")

LOG = logging.getLogger(__name__)

class PlatformVersions(object):
    '''Coordinate loading and applying versions from a platform version config file.
    '''

    def __init__(self, buildout):
        '''Setup the version update.

        buildout       -- the buildout object
        config_section -- a section in the buildout that contains config info

        source_section -- like 'tes_100', the name of the section to use from the
                          config sources.
        sources        -- list of sources, like
                          "http://somewhere.com/foo/bar"
                          "egg://eggname/path/to/config"
                          "file:///opt/zillow/path/to/config"
        target_section -- like 'versions', the name of the section to modify with
                          the new versions.
        '''
        self.buildout = buildout
        
        self.config_section = None
        self.source_section = None
        self.sources = None
        self.target_section = None
        self.platform_env_var = None

    def parse_config(self):
        self.load_config_section_name()
        self.load_platform_env_var()
        self.load_source_section()
        self.load_source_list()
        self.load_target_section()

    def load_platform_env_var(self):
        # look for an environment variable with the platform to use
        if self._config:
            platform_env_var = self._config.get ("platform-env", None)
            if platform_env_var:
                platform_env_var = platform_env_var.strip ()
                if len(platform_env_var) == 0:
                    platform_env_var = None
            self.platform_env_var = platform_env_var

    def load_config_section_name(self):
        self.config_section = self.buildout['buildout'].get('platform-versions-config', 'platform-versions-config')
        try:
            self._config = self.buildout[self.config_section]
        except:
            self._config = None

    def load_source_section(self):
        self.source_section = self._get_platform ()

    def load_source_list(self):
        source_list = []
        if self._config:
            source_str = self._config.get('sources', '')
            for name in source_str.split("\n"):
                name = name.strip()
                if len(name):
                    source_list.append (name)
            for source in source_list:
                LOG.info ("source: %s", source)
            self.sources = source_list
        else:
            self.sources = []
        return source_list

    def load_target_section(self):
        if 'versions' in self.buildout['buildout']:
            self.target_section = self.buildout['buildout']['versions']
        else:
            self.target_section = 'versions'

    def _get_platform_from_env(self):
        # if we should check for an environment variable, try it
        platform_env = None
        if self.platform_env_var:
            platform_env = os.getenv (self.platform_env_var, None)
            if platform_env is not None and len(platform_env) > 0:
                LOG.debug ("platform picked by environment variable: %s = %s", self.platform_env_var, platform_env)
            else:
                LOG.debug ("environment variable '%s' is not set.", self.platform_env_var)
        return platform_env

    def _get_platform_from_config(self):
        if self.config_section in self.buildout:
            platform_env = self._config.get ("default-platform", None)
            if platform_env:
                platform_env = platform_env.strip()
            if len(platform_env) == 0:
                platform_env = None

            if platform_env is None:
                # if there's no default in the config section, bomb
                LOG.error ("%s", "the configuration ${platform-versions-config:default-platform} is required")
                raise Exception ("Missing required config ${platform-versions-config:default-platform}")
            else:
                LOG.info ("platform picked by ${%s:%s} = %s", self.config_section, "default-platform", platform_env)
        else:
            platform_env = None

        return platform_env 

    def _get_platform(self):
        '''Figure out what the source section name is.'''
        # figure out which section to load version pins from
        
        # if we should check for an environment variable, try it
        platform_env = self._get_platform_from_env ()

        # if there is no environment variable setting, use the default in the config
        # section of the buildout file
        if not platform_env:
            platform_env = self._get_platform_from_config()

        return platform_env

    def load_platform_versions(self):
        new_versions = {}
        cp = ConfigParser.ConfigParser ()
        for file_name in self.sources:
            _load_config (cp, file_name)
        
        config_enhance.enhance(cp)

        if cp.has_section (self.source_section):
            new_versions.update (cp.items (self.source_section))
        else:
            LOG.warn ("'%s' does not exist", self.source_section)
            LOG.warn ("Valid choices are:")

            for section in cp.sections():
                LOG.info ("\t%s", section)

        return new_versions
     
    def load_develop_packages(self):
        pkgs = []
        if self.buildout is not None:
            buildout_section = self.buildout.get("buildout", None)
            if buildout_section is not None:
                develop_str = buildout_section.get("develop", None)
                if develop_str is not None:
                    develop_paths = [vv for vv in develop_str.split() if len(vv)]
                    if len(develop_paths):
                        develop_pkgs = lookup_develop_distributions(develop_paths)
                        pkg_names = [dd for dd in develop_pkgs]
                        pkgs.extend(pkg_names)

        if self._config is not None:
            package_string = self._config.get ("develop-packages", None)
            if package_string is not None:
                pkgs.extend ([(vv.strip(), None) for vv in package_string.split()])

        # report the development packages
        return pkgs
 
    def load_composite_versions(self):
        # record the explicitly pinned versions in this buildout. They'll
        # trump the platform.
        cur_versions = dict (self.buildout[self.target_section])

        # load up the extra versions from various sources
        new_versions = self.load_platform_versions()
        
        # trump with the explicit versions in this project
        new_versions.update (cur_versions)

        # unpin explicitly named develop packages
        for pkg in self.load_develop_packages():
            if pkg[1] is None:
                LOG.info ("Unpinning '%s' for development.", pkg)
                new_versions.pop(pkg[0], None)
            else:
                LOG.info ("Pinning '%s' to '%s' for development.", pkg[0], pkg[1])
                new_versions[pkg[0]] = pkg[1]
        
        self.versions = new_versions
        return self.versions
    
    def apply_new_versions(self):
        '''

        uses members:
        target_section, buildout, versions
        '''
        target = self.buildout[self.target_section]

        # update the versions in the parent buildout
        target.clear ()
        target.update (self.versions)

        # set the new version information for use by easy_install
        zc.buildout.easy_install.default_versions (self.versions)
        
        for k, v in self.versions.iteritems():
            LOG.debug ("'%s' = '%s'", k, v)

    def apply_to_buildout (self):
        self.parse_config()
        self.load_composite_versions()
        self.apply_new_versions()


def read_package_name_from_setup_py(path):
    try:
        setup_py = os.path.join (path, "setup.py")
        if os.path.exists (setup_py):
            cmd = [sys.executable, "-S", "-s", setup_py, "--name", "--version"]

            env = { "PYTHONPATH" : ":".join (sys.path) }

            proc = subprocess.Popen(cmd, env = env, stdout=subprocess.PIPE)
            result = proc.communicate()
            vv = result[0]
            if proc.returncode != 0:
                raise Exception("'%s' failed with return code '%d'" % (" ".join(cmd), proc.returncode))
            
            # check_output was added in python 2.7. Use it when available
            #vv = subprocess.check_output([sys.executable, setup_py, "--name", "--version"])
            return vv.split()
    except (Exception, IOError):
        LOG.exception("Unable to run '%s'", setup_py)

def read_package_name_from_pkg_resources(path):
    try:
        vv = pkg_resources.find_distributions(path)
        if vv is not None:
            return vv.split()
    except (Exception, IOError):
        LOG.exception("Unable to execute 'pkg_resources.find_distributions(%s)'" % path)


def lookup_develop_distributions(paths):
    dists = []
    for path in paths:
        # try a few approaches to get a package name out of the path
        pkg = read_package_name_from_setup_py(path)
        if pkg is None:
            pkg = read_package_name_from_pkg_resources(path)
        
        if pkg is None:
            LOG.error ("Unable to find a package name at '%s'", path)
        else:
            dists.append(pkg)

    return dists

def _load_resource (uri):
    mm = EGG_URI_RE.match(uri)
    if mm:
        dd = mm.groupdict()
        egg_name = dd["egg"]
        path = dd["path"]
        data = pkgutil.get_data(egg_name, path)
        return data
    elif "://" in uri:
        # looks like a url
        import urllib2
        return urllib2.urlopen (uri).read ()
    else:
        # looks like a file name
        return file (uri).read ()


def _load_config (cc, uri):
    content = _load_resource (uri)
    import StringIO
    buf = StringIO.StringIO (content)
    cc.readfp (buf, uri)

 
def start(buildout):
    platform = PlatformVersions (buildout)
    platform.apply_to_buildout ()


def finish(buildout):
    pass
    
