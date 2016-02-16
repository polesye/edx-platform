"""
Asset compilation and collection.
"""

from __future__ import print_function
from datetime import datetime
import argparse
import glob
import traceback

from paver import tasks
from paver.easy import sh, path, task, cmdopts, needs, consume_args, call_task, no_help
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from .utils.envs import Env
from .utils.cmd import cmd, django_cmd

# setup baseline paths

ALL_SYSTEMS = ['lms', 'studio']
COFFEE_DIRS = ['lms', 'cms', 'common']

# Directories that contain SASS files that need to be compiled, each element in a list of paths is a tuple with the
# following format
#   (sass_dir, css_dir)
# where sass_dir points to source sass files and css_dir points to destination dir where css files should be put.
SASS_DIRECTORIES = {
    "COMMON": [
        (path("common/static/sass"), path("common/static/css"))
    ],
    "LMS": [
        (path("lms/static/sass"), path("lms/static/css")),
        (path("lms/static/themed_sass"), path("lms/static/css")),
        (path("lms/static/certificates/sass"), path("lms/static/certificates/css")),
    ],
    "CMS": [
        (path("cms/static/sass"), path("cms/static/css")),
    ],
    "THEME_LMS": [

    ],
    "THEME_CMS": [

    ],
}

# Directories that needs to be added LOOKUP Path while compiling sass, each element of the list is a path object
# containing the path to be added to lookup paths
SASS_LOOKUP_DIRECTORIES = {
    "COMMON": [
        path("common/static"),
        path("common/static/sass"),
    ],
    "LMS": [
        path("lms/static/sass/partials"),
        path("lms/static/sass"),
        path("lms/static/themed_sass"),
        path("lms/static/certificates/sass"),
    ],
    "CMS": [
        path("cms/static/sass/partials"),
        path("cms/static/sass"),
        path("lms/static/sass/partials"),  # TODO: remove usage of base/_variables.scss from
        # common/static/xmodule/modules/css/_module-styles.scss and also this line.
    ],
    "THEME_LMS": [

    ],
    "THEME_CMS": [

    ],
}


def configure_paths():
    """Configure our paths based on settings.  Called immediately."""
    edxapp_env = Env()
    if edxapp_env.feature_flags.get('USE_CUSTOM_THEME', False):
        theme_name = edxapp_env.env_tokens.get('THEME_NAME', '')
        parent_dir = path(edxapp_env.REPO_ROOT).abspath().parent
        theme_root = parent_dir / "themes" / theme_name
        COFFEE_DIRS.append(theme_root)
        sass_dir = theme_root / "static" / "sass"
        css_dir = theme_root / "static" / "css"
        if sass_dir.isdir():
            css_dir.mkdir_p()
            SASS_DIRECTORIES['THEME'].append((sass_dir, css_dir))
            SASS_LOOKUP_DIRECTORIES['THEME'].append(sass_dir)

    if edxapp_env.env_tokens.get("COMPREHENSIVE_THEME_DIR", ""):
        theme_dir = path(edxapp_env.env_tokens["COMPREHENSIVE_THEME_DIR"])
        lms_sass = theme_dir / "lms" / "static" / "sass"
        lms_css = theme_dir / "lms" / "static" / "css"
        if lms_sass.isdir():
            lms_css.mkdir_p()
            SASS_DIRECTORIES['THEME_LMS'].append(("lms/static/sass", lms_css))
            SASS_DIRECTORIES['THEME_LMS'].append((lms_sass, lms_css))
            SASS_LOOKUP_DIRECTORIES['THEME_LMS'].append(lms_sass / "partials")
            SASS_LOOKUP_DIRECTORIES['THEME_LMS'].append(lms_sass)

        cms_sass = theme_dir / "cms" / "static" / "sass"
        cms_css = theme_dir / "cms" / "static" / "css"
        if cms_sass.isdir():
            cms_css.mkdir_p()
            SASS_DIRECTORIES['THEME_CMS'].append(("cms/static/sass", cms_css))
            SASS_DIRECTORIES['THEME_CMS'].append((cms_sass, cms_css))
            SASS_LOOKUP_DIRECTORIES['THEME_CMS'].append(cms_sass / "partials")
            SASS_LOOKUP_DIRECTORIES['THEME_CMS'].append(cms_sass)

configure_paths()


def sass_source_directories(systems=None):
    """
    Determine the applicable set of SASS directories to be
    compiled for the specified list of systems.

    Args:
        systems: A list of systems (defaults to all)

    Returns:
        A list of SASS directories to be compiled.
    """
    if not systems:
        systems = ALL_SYSTEMS
    applicable_directories = []

    applicable_directories.extend(SASS_DIRECTORIES['COMMON'])
    if "lms" in systems:
        # If Theme is enabled compile sass for the theme only
        if SASS_DIRECTORIES['THEME_LMS']:
            applicable_directories.extend(SASS_DIRECTORIES['THEME_LMS'])
        # If Theme is disabled compile sass lms only
        else:
            applicable_directories.extend(SASS_DIRECTORIES['LMS'])
    if "studio" in systems or "cms" in systems:
        # If Theme is enabled compile sass for the theme only
        if SASS_DIRECTORIES['THEME_CMS']:
            applicable_directories.extend(SASS_DIRECTORIES['THEME_CMS'])
        # If Theme is disabled compile sass cms only
        else:
            applicable_directories.extend(SASS_DIRECTORIES['CMS'])

    return applicable_directories


def sass_lookup_directories(systems=None):
    """
    Determine the sass directories to be added to sass lookup paths.

    Args:
        systems: A list of systems (defaults to all)

    Returns:
        A list of SASS directories to be added to SASS lookup path.
    """
    if not systems:
        systems = ALL_SYSTEMS
    system_sass_lookup_directories = []
    system_sass_lookup_directories.extend(SASS_LOOKUP_DIRECTORIES['COMMON'])

    if "lms" in systems:
        # Put theme sass at the top so that theme directories have highest priority on sass file lookup.
        system_sass_lookup_directories.extend(SASS_LOOKUP_DIRECTORIES['THEME_LMS'])
        system_sass_lookup_directories.extend(SASS_LOOKUP_DIRECTORIES['LMS'])
    if "studio" in systems or "cms" in systems:
        # Put theme sass at the top so that theme directories have highest priority on sass file lookup.
        system_sass_lookup_directories.extend(SASS_LOOKUP_DIRECTORIES['THEME_CMS'])
        system_sass_lookup_directories.extend(SASS_LOOKUP_DIRECTORIES['CMS'])

    return system_sass_lookup_directories


class CoffeeScriptWatcher(PatternMatchingEventHandler):
    """
    Watches for coffeescript changes
    """
    ignore_directories = True
    patterns = ['*.coffee']

    def register(self, observer):
        """
        register files with observer
        """
        dirnames = set()
        for filename in sh(coffeescript_files(), capture=True).splitlines():
            dirnames.add(path(filename).dirname())
        for dirname in dirnames:
            observer.schedule(self, dirname)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_coffeescript(event.src_path)
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()


class SassWatcher(PatternMatchingEventHandler):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    patterns = ['*.scss']
    ignore_patterns = ['common/static/xmodule/*']

    def register(self, observer):
        """
        register files with observer
        """
        for dirname in sass_lookup_directories():
            paths = []
            if '*' in dirname:
                paths.extend(glob.glob(dirname))
            else:
                paths.append(dirname)
            for dirname in paths:
                observer.schedule(self, dirname, recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_sass()      # pylint: disable=no-value-for-parameter
        except Exception:       # pylint: disable=broad-except
            traceback.print_exc()


class XModuleSassWatcher(SassWatcher):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    ignore_patterns = []

    def register(self, observer):
        """
        register files with observer
        """
        observer.schedule(self, 'common/lib/xmodule/', recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()


class XModuleAssetsWatcher(PatternMatchingEventHandler):
    """
    Watches for css and js file changes
    """
    ignore_directories = True
    patterns = ['*.css', '*.js']

    def register(self, observer):
        """
        Register files with observer
        """
        observer.schedule(self, 'common/lib/xmodule/', recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()

        # To refresh the hash values of static xmodule content
        restart_django_servers()


def coffeescript_files():
    """
    return find command for paths containing coffee files
    """
    dirs = " ".join(Env.REPO_ROOT / coffee_dir for coffee_dir in COFFEE_DIRS)
    return cmd('find', dirs, '-type f', '-name \"*.coffee\"')


@task
@no_help
def compile_coffeescript(*files):
    """
    Compile CoffeeScript to JavaScript.
    """
    if not files:
        files = ["`{}`".format(coffeescript_files())]
    sh(cmd(
        "node_modules/.bin/coffee", "--compile", *files
    ))


@task
@no_help
@cmdopts([
    ('system=', 's', 'The system to compile sass for (defaults to all)'),
    ('debug', 'd', 'Debug mode'),
    ('force', '', 'Force full compilation'),
])
def compile_sass(options):
    """
    Compile Sass to CSS.
    """

    # Note: import sass only when it is needed and not at the top of the file.
    # This allows other paver commands to operate even without libsass being
    # installed. In particular, this allows the install_prereqs command to be
    # used to install the dependency.
    import sass

    debug = options.get('debug')
    force = options.get('force')
    systems = getattr(options, 'system', ALL_SYSTEMS)
    if isinstance(systems, basestring):
        systems = systems.split(',')
    if debug:
        source_comments = True
        output_style = 'nested'
    else:
        source_comments = False
        output_style = 'compressed'

    timing_info = []
    system_sass_directories = sass_source_directories(systems)
    system_sass_lookup_directories = sass_lookup_directories(systems)
    dry_run = tasks.environment.dry_run
    for system_sass_dir, system_css_dir in system_sass_directories:
        start = datetime.now()
        css_dir = system_css_dir or system_sass_dir.parent / "css"

        if force:
            if dry_run:
                tasks.environment.info("rm -rf {css_dir}/*.css".format(
                    css_dir=css_dir,
                ))
            else:
                sh("rm -rf {css_dir}/*.css".format(css_dir=css_dir))

        if dry_run:
            tasks.environment.info("libsass {sass_dir}".format(
                sass_dir=system_sass_dir,
            ))
        else:
            sass.compile(
                dirname=(system_sass_dir, css_dir),
                include_paths=system_sass_lookup_directories,
                source_comments=source_comments,
                output_style=output_style,
            )
            duration = datetime.now() - start
            timing_info.append((system_sass_dir, css_dir, duration))

    print("\t\tFinished compiling Sass:")
    if not dry_run:
        for sass_dir, css_dir, duration in timing_info:
            print(">> {} -> {} in {}s".format(sass_dir, css_dir, duration))


def compile_templated_sass(systems, settings):
    """
    Render Mako templates for Sass files.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    """
    for system in systems:
        if system == "studio":
            system = "cms"
        sh(django_cmd(
            system, settings, 'preprocess_assets',
            '{system}/static/sass/*.scss'.format(system=system),
            '{system}/static/themed_sass'.format(system=system)
        ))
        print("\t\tFinished preprocessing {} assets.".format(system))


def process_xmodule_assets():
    """
    Process XModule static assets.
    """
    sh('xmodule_assets common/static/xmodule')
    print("\t\tFinished processing xmodule assets.")


def restart_django_servers():
    """
    Restart the django server.

    `$ touch` makes the Django file watcher thinks that something has changed, therefore
    it restarts the server.
    """
    sh(cmd(
        "touch", 'lms/urls.py', 'cms/urls.py',
    ))


def collect_assets(systems, settings):
    """
    Collect static assets, including Django pipeline processing.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    """
    for sys in systems:
        sh(django_cmd(sys, settings, "collectstatic --noinput > /dev/null"))
        print("\t\tFinished collecting {} assets.".format(sys))


@task
@cmdopts([('background', 'b', 'Background mode')])
def watch_assets(options):
    """
    Watch for changes to asset files, and regenerate js/css
    """
    # Don't watch assets when performing a dry run
    if tasks.environment.dry_run:
        return

    observer = Observer()

    CoffeeScriptWatcher().register(observer)
    SassWatcher().register(observer)
    XModuleSassWatcher().register(observer)
    XModuleAssetsWatcher().register(observer)

    print("Starting asset watcher...")
    observer.start()
    if not getattr(options, 'background', False):
        # when running as a separate process, the main thread needs to loop
        # in order to allow for shutdown by contrl-c
        try:
            while True:
                observer.join(2)
        except KeyboardInterrupt:
            observer.stop()
        print("\nStopped asset watcher.")


@task
@needs(
    'pavelib.prereqs.install_ruby_prereqs',
    'pavelib.prereqs.install_node_prereqs',
)
@consume_args
def update_assets(args):
    """
    Compile CoffeeScript and Sass, then collect static assets.
    """
    parser = argparse.ArgumentParser(prog='paver update_assets')
    parser.add_argument(
        'system', type=str, nargs='*', default=ALL_SYSTEMS,
        help="lms or studio",
    )
    parser.add_argument(
        '--settings', type=str, default="devstack",
        help="Django settings module",
    )
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Disable Sass compression",
    )
    parser.add_argument(
        '--skip-collect', dest='collect', action='store_false', default=True,
        help="Skip collection of static assets",
    )
    parser.add_argument(
        '--watch', action='store_true', default=False,
        help="Watch files for changes",
    )
    args = parser.parse_args(args)

    compile_templated_sass(args.system, args.settings)
    process_xmodule_assets()
    compile_coffeescript()
    call_task('pavelib.assets.compile_sass', options={'system': args.system, 'debug': args.debug})

    if args.collect:
        collect_assets(args.system, args.settings)

    if args.watch:
        call_task('pavelib.assets.watch_assets', options={'background': not args.debug})
