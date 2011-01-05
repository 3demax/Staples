#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Staples is a simple static site generator based on the idea of processors
mapped to types of files. It includes a basic server for development, and
has no external requirements itself, beyond the Python Standard Library.
Specific processors, such as the included Django template renderer, will
have their own requirements.

Info and source: http://github.com/typeish/staples

type(ish) inc
License: UNLICENSE
"""

__author__ = 'type(ish) inc'
__version__ = '0.1a'
__license__ = 'UNLICENSE'

import os, shutil, commands, glob, sys

# Default settings
PROJECT_ROOT = os.getcwd()
CONTENT_DIR = os.path.join(PROJECT_ROOT, 'content')
DEPLOY_DIR = os.path.join(PROJECT_ROOT, 'deploy')

REMOTE_ROOT = ''

INDEX_FILE = 'index.html'
IGNORE = ()
PROCESSORS = {}

# Look for a settings.py in the current working directory
sys.path.append(PROJECT_ROOT)
try:
    import settings
    from settings import *
except ImportError:
    if __name__ == "__main__":
        print 'No settings.py found, using defaults.\n'
else:
    if __name__ == "__main__":
        print 'Using settings file %s' % settings.__file__[:-1]

verbose=False

class File(object):

    def __init__(self, file_path, parent_ignored=False, **kwargs):
        self.source = file_path
        self.rel_path = file_path.replace(CONTENT_DIR,'').lstrip('/')
        self.rel_parent, self.name = os.path.split(self.source)
        self.ext = os.path.splitext(self.name)[1]
        self.parent_ignored = parent_ignored

    def process(self, **kwargs):
        if verbose:
            print 'Processing:', self.rel_path
        if self.is_directory:
            if '/' in PROCESSORS:
                p = PROCESSORS['/']
            else:
                p = handle_directory
        elif self.name in PROCESSORS:
            p = PROCESSORS[self.name]
        elif self.ext in PROCESSORS:
            p = PROCESSORS[self.ext]
        elif '*' in PROCESSORS:
            p = PROCESSORS['*']
        else:
            p = handle_others
        return p(self, **kwargs)

    @property
    def deploy_path(self): return os.path.join(DEPLOY_DIR, self.rel_path)

    @property
    def remote_path(self): return os.path.join(REMOTE_ROOT, self.rel_path)

    @property
    def mtime(self): return os.path.getmtime(self.source)

    @property
    def is_directory(self): return os.path.isdir(self.source)

    @property
    def ignorable(self):
        return ( self.name.startswith(".") or self.name.startswith("_")
                or self.name.endswith("~") or self.name in IGNORE )

# BUILD FUNCTIONS
###############################################################################
def build(**kwargs):
    print 'Starting build...\n'
    if verbose:
        print 'Removing any existing deploy directory'
    shutil.rmtree(DEPLOY_DIR, ignore_errors=True)

    if verbose:
        print 'Creating deploy directory: ', DEPLOY_DIR
    os.mkdir(DEPLOY_DIR)

    if verbose:
        print 'Traversing content directory: %s...' % CONTENT_DIR

    build_directories(CONTENT_DIR, **kwargs)

    print '\nBuild done'

def build_directories(t_path, **kwargs):
    """
    Recursively traverses a given directory, calling the given file's handler.
    Keyword arguments are passed through to the handler.
    """
    for file in glob.glob( os.path.join(t_path, '*') ):
        File(file, **kwargs).process(**kwargs)

# HELPER FUNCTIONS

def strip_extension(filepath, ext):
    """
    Safely strips file extensions.
    """
    if not ext.startswith("."):
        ext = "." + ext
    dirname = os.path.dirname(filepath)
    basename = os.path.basename(filepath).replace(ext, "")
    if not basename:
        raise ValueError("Stripping '%s' will cause the file name to be blank." % ext)
    return os.path.join(dirname, basename)


# DEFAULT HANDLERS
# These two functions basically just copy anything they are given over to
# the deploy directory.

def handle_directory(f, **kwargs):
    """
    Copies directories, unless they are ignorable or their
    parent was ignored.
    """
    if not f.ignorable and not f.parent_ignored:
        try:
            os.mkdir(f.deploy_path)
        except OSError:
            pass
    else:
        kwargs.update({'parent_ignored': True})
    build_directories(f.source, **kwargs)

def handle_others(f, **kwargs):
    """
    Simply copies files from the source path to the deploy path.
    """
    if not f.ignorable and not f.parent_ignored:
        if verbose:
            print 'Copying file to:', f.deploy_path
        commands.getoutput(u"cp %s %s" % (f.source, f.deploy_path))
    elif verbose:
        print 'Ignoring:', f.rel_path


# EXTRA HANDLERS

def handle_django(f, for_deployment=False, **kwargs):
    """
    Renders templates using the Django template rendering engine. If the
    template ends in .django, the resulting output filename has that removed.

    Requires:
        Django - any version that can handle the templates you give it
        settings.py - placed in the same directory and defines both
                      TEMPLATE_DIRS and CONTEXT
    """
    verbose = globals().get('verbose', False)
    if not f.ignorable and not f.parent_ignored:
        from django.template.loader import render_to_string
        import settings

        os.environ['DJANGO_SETTINGS_MODULE'] = u"settings"
        deploy_path = strip_extension(f.deploy_path, "django")

        if verbose:
            print "Rendering:", f.rel_path

        context = {}
        if settings.CONTEXT:
            context = settings.CONTEXT
        context["for_deployment"] = for_deployment
        rendered = render_to_string(f.source, context)

        if verbose:
            print "Saving rendered output to:", deploy_path
        fout = open(deploy_path,"w")
        fout.write(rendered)
        fout.close()
    elif verbose:
        print "Ignoring:", f.rel_path


def handle_gallery(f, **kwargs):
    pass
    # build a gallery using a folder of images, creating an index.html file
    # with all of the images, and an N.html file for each image with the full
    # sized image, up to CONTEXT.max_width

def handle_markdown(f, **kwargs):
    """
    A markdown processor. Requires the `markdown` module. It allows for
    prepend and append code to wrap the rendered page in proper HTML structure.
    Includes support for a meta-information notation in the markdown source
    files for title and meta tags.

    The extension of the source file is replaced with `.html`.
    """
    if not f.ignorable and not f.parent_ignored:
        from markdown import markdown
        import codecs, re
        json = None

        try:
            import simplejson as json
        except ImportError:
            try:
                import json
            except ImportError:
                pass

        try:
            from settings import MD_PRE
        except ImportError:
            pre = ''
        else:
            pre = MD_PRE

        try:
            from settings import MD_POST
        except ImportError:
            post = ''
        else:
            post = MD_POST

        info = {}
        if json:
            text = codecs.open(f.source, mode="r", encoding="utf8").read()

            pattern = re.compile('!INFO.+\/INFO',re.DOTALL)
            result = re.match(pattern,text)
            if result:
                info = result.group()
                text = text.replace(info,'')
                info = info.lstrip('!INFO').rstrip('/INFO')
                info = json.loads(info)

        print 'Rendering:',f.rel_path, 'with INFO' if info else ''
        rendered = markdown(text)

        deploy_path = f.deploy_path.replace(f.ext, '.html')
        fout = open(deploy_path, 'w')
        if len(info) > 0:
            for k in info:
                if k[:4] == 'meta':
                    tag = '<meta type="%s" content="' % k.split('-')[1]
                else:
                    tag = '<%s>' % k
                pre = pre.replace(tag, tag + info[k])

        fout.write(pre + rendered + post)
        fout.close()



# WATCH FUNCTIONS
###############################################################################

import datetime, time

def watch():
    """
    Initiates a full rebuild of the project, then watches for changed files.
    Once a second, it polls all of the files in the content directory.
    """
    watcher = DirWatcher(CONTENT_DIR)
    build()
    print 'Watching %s...' % CONTENT_DIR
    while True:
        time.sleep(1)
        changed = watcher.find_changed_files()
        if len(changed) > 0:
            for f in changed:
                f.process()

class DirWatcher(object):
    """
    Class that keeps track of the files in the content directory, and their
    modification times, so they can be watched for changes.
    """
    def __init__(self, directory, update=True):
        self.target_directory = directory
        self.changed_files = []
        self.file_list = {}
        if update:
            self.update_mtimes(self.target_directory)

    def find_changed_files(self):
        self.changed_files = []
        self.update_mtimes(self.target_directory)
        return self.changed_files


    def update_mtimes(self, current_file):
        """
        Recursively traverses the directory, updating the dictionary of mtimes
        and the list of files changed since the last check.
        """
        for file in glob.glob( os.path.join(current_file, '*') ):
            f = File(file)
            if f.is_directory:
                f.process()
                self.update_mtimes(f.source)
            else:
                mtime = f.mtime
                if not f.source in self.file_list or self.file_list[f.source] != mtime:
                    self.file_list[f.source] = mtime
                    self.changed_files.append(f)


# DEVELOPMENT SERVER
###############################################################################

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import mimetypes

class HandleRequests(BaseHTTPRequestHandler):
    """
    A stupid-simple webserver that serves up static files, and nothing else.
    Requests for a directory will return the contents of the INDEX_FILE.
    """
    def do_GET(self):
        try:
            path_append = ''
            if len(self.path) > 0 and self.path[-1] == '/':
                self.path = self.path + INDEX_FILE
            file_path = DEPLOY_DIR + self.path + path_append
            mtype = mimetypes.guess_type(file_path)[0]
            f = open(file_path)
            self.send_response(200)
            self.send_header('Content-type', mtype)
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return

        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

def runserver(port=8000):
    """
    Runs the web server at localhost and the specified port (default port 8000).
    """
    try:
        server = HTTPServer(('', port), HandleRequests)
        print 'Running server at localhost:%s...' % port
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Shutting down server'
        server.socket.close()


# CONTROL
###############################################################################

# START Autoreloading launcher.
# Borrowed from Peter Hunt and the CherryPy project (http://www.cherrypy.org).
# Some taken from Ian Bicking's Paste (http://pythonpaste.org/).
#
# Portions copyright (c) 2004, CherryPy Team (team@cherrypy.org)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of the CherryPy Team nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os, sys, time

try:
    import thread
except ImportError:
    import dummy_thread as thread

RUN_RELOADER = True

_mtimes = {}
_win = (sys.platform == "win32")

def code_changed():
    global _mtimes, _win
    for filename in filter(lambda v: v, map(lambda m: getattr(m, "__file__", None), sys.modules.values())):
        if filename.endswith(".pyc") or filename.endswith(".pyo"):
            filename = filename[:-1]
        if not os.path.exists(filename):
            continue # File might be in an egg, so it can't be reloaded.
        stat = os.stat(filename)
        mtime = stat.st_mtime
        if _win:
            mtime -= stat.st_ctime
        if filename not in _mtimes:
            _mtimes[filename] = mtime
            continue
        if mtime != _mtimes[filename]:
            _mtimes = {}
            return True
    return False

def reloader_thread():
    while RUN_RELOADER:
        if code_changed():
            sys.exit(3) # force reload
        time.sleep(1)

def restart_with_reloader():
    while True:
        args = [sys.executable] + sys.argv
        if sys.platform == "win32":
            args = ['"%s"' % arg for arg in args]
        new_environ = os.environ.copy()
        new_environ["RUN_MAIN"] = 'true'
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_environ)
        if exit_code != 3:
            return exit_code

def python_reloader(main_func, args, kwargs):
    if os.environ.get("RUN_MAIN") == "true":
        thread.start_new_thread(main_func, args, kwargs)
        try:
            reloader_thread()
        except KeyboardInterrupt:
            pass
    else:
        try:
            sys.exit(restart_with_reloader())
        except KeyboardInterrupt:
            pass

def jython_reloader(main_func, args, kwargs):
    from _systemrestart import SystemRestart
    thread.start_new_thread(main_func, args)
    while True:
        if code_changed():
            raise SystemRestart
        time.sleep(1)

def autoreload_main(main_func, args=None, kwargs=None):
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}
    if sys.platform.startswith('java'):
        reloader = jython_reloader
    else:
        reloader = python_reloader
    reloader(main_func, args, kwargs)
# END Autoreload launcher.

if __name__ == "__main__":
    if '-v' in sys.argv:
        verbose = True
    else:
        verbose = False

    if 'runserver' in sys.argv:
        port = 8000
        try:
            port = int(sys.argv[2])
        except:
            pass
        thread.start_new_thread(watch, ())
        autoreload_main(runserver, (port,))

    elif 'build' in sys.argv:
        if '-d' in sys.argv:
            build(for_deployment=True)
        else:
            build()

    elif 'watch' in sys.argv:
        watch()
    else:
        print """
    Staples Usage:
        build     - `python staples.py build`
        watch     - `python staples.py watch`
        runserver - `python staples.py runserver [port]`'

    Add '-v' to any command for verbose output.
    e.g. `python staples.py build verbose`

    Add '-d' to `build` for building with for_deployment set to True.
    e.g. `python staples.py build -d`
    """
