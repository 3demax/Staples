#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Staples is a simple static site generator based on the idea of processors
mapped to types of files. It includes a basic server for development, and
has no external requirements itself, beyond the Python Standard Library.
Specific processors, such as the included Django template renderer, will
have their own requirements.

Info and source: https://github.com/typeish/staples

type(ish), inc.
Version: 0.1.0
License: UNLICENSE
"""

__author__      = 'type(ish), inc. <http://typeish.net>'
__version__     = '0.1.0'
__license__     = 'UNLICENSE'


import commands, datetime, glob, os, shutil, sys, thread



# Some colors for friendlier output
# see: http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
CHEADER     = '\033[95m' # purple
COKBLUE     = '\033[94m' # blue
COKGREEN    = '\033[92m' # green
CWARNING    = '\033[93m' # yellow
CFAIL       = '\033[91m' # red
CEND        = '\033[0m'

def stamp(message, color=CEND):
    now = datetime.datetime.now().strftime('%H:%M:%S')
    print '%s%s: %s%s' % (color, now, message, CEND)

# Look for a settings.py in the current working directory
sys.path.append(os.getcwd())

class Settings(object):
    """
    Settings class, preloaded with defaults.
    """
    # Default settings
    PROJECT_ROOT    = os.getcwd()
    CONTENT_DIR     = os.path.join(PROJECT_ROOT, 'content')
    DEPLOY_DIR      = os.path.join(PROJECT_ROOT, 'deploy')

    REMOTE_ROOT     = ''

    INDEX_FILE      = 'index.html'
    IGNORE          = ()
    PROCESSORS      = {}
    WATCH_INTERVAL  = 1  # seconds

settings = Settings()



try:
    import settings as ext_settings
except ImportError:
    stamp('No settings.py found, using defaults.\n', color=CWARNING)
else:
    stamp('Using settings file %s' % ext_settings.__file__, color=COKGREEN)
    for attr, val in ext_settings.__dict__.items():
        setattr(settings,attr,val)



class File(object):
    """
    An object that describes a file to be operated on, with some attributes
    that help manipulate the paths and names.
    """

    def __init__(self, file_path, parent_ignored=False, **kwargs):
        self.source = file_path
        self.rel_path = file_path.replace(settings.CONTENT_DIR,'').lstrip('/')
        self.rel_parent, self.name = os.path.split(self.source)
        self.ext = os.path.splitext(self.name)[1]
        self.parent_ignored = parent_ignored

    def process(self, **kwargs):
        """
        Identifies the appropriate processor for the file and calls it.
        settings.PROCESSORS must be a dictionary mapping file name patters, as
        strings, with processor function names, also strings. The processor must
        be importable if it's not one of the included functions.
        """
        procs = settings.PROCESSORS

        if self.name in procs:
            proc = procs[self.name]
        elif self.is_directory:
            if '/' in procs:
                proc = procs['/']
            else:
                proc = 'handle_directory'

        elif self.ext in procs:
            proc = procs[self.ext]
        elif '*' in procs:
            proc = procs['*']
        else:
            proc = 'handle_others'
        
        global_vars = globals()
        if proc in global_vars:
            handler_func = global_vars[proc]
        else:
            handler_func = __import__(proc)

        return handler_func(self, **kwargs)
        

    @property
    def deploy_path(self): return os.path.join(settings.DEPLOY_DIR, self.rel_path)

    @property
    def remote_path(self): return os.path.join(settings.REMOTE_ROOT, self.rel_path)

    @property
    def mtime(self): return os.path.getmtime(self.source)

    @property
    def is_directory(self): return os.path.isdir(self.source)

    @property
    def ignorable(self):
        return ( self.name.startswith(".") or self.name.startswith("_")
                or self.name.endswith("~") or self.name in settings.IGNORE )




# BUILD FUNCTIONS
###############################################################################

def build(**kwargs):
    stamp('Starting build...\n')
    stamp('Removing any existing deploy directory')
    shutil.rmtree(settings.DEPLOY_DIR, ignore_errors=True)

    stamp('Creating deploy directory: ', settings.DEPLOY_DIR)
    os.mkdir(settings.DEPLOY_DIR)

    stamp('Traversing content directory: %s...' % settings.CONTENT_DIR)

    build_directories(settings.CONTENT_DIR, **kwargs)

    stamp('Build done', color=COKGREEN)

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
        raise ValueError(CFAIL + "Stripping '%s' will cause the file name to be blank." % ext + CEND)
    return os.path.join(dirname, basename)


# DEFAULT HANDLERS
# These two functions just copy anything they are given over to
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
        print("[processing file] \"%s\" " % (f.source))
        commands.getoutput("cp \"%s\" \"%s\"" % (f.source, f.deploy_path)) #now supporting non-ascii characters in filepath


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
    if not f.ignorable and not f.parent_ignored:
        from django.template.loader import render_to_string
        import settings

        os.environ['DJANGO_SETTINGS_MODULE'] = u"settings"
        deploy_path = strip_extension(f.deploy_path, "django")

        context = {}
        if settings.CONTEXT:
            context = settings.CONTEXT
        context["for_deployment"] = for_deployment
        rendered = render_to_string(f.source, context)
        fout = open("%s" % deploy_path,"w")
        fout.write(rendered.encode('utf8')) #now supporting utf8-encoded text
        fout.close()

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
            wrap = settings.MD_WRAP
        except:
            wrap = ''

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
                wrap = wrap.replace(tag, tag + info[k])

        fout.write( wrap.replace('{{ CONTENT }}', rendered) )
        fout.close()



# WATCH FUNCTIONS
###############################################################################

import datetime, time

def watch():
    """
    Initiates a full rebuild of the project, then watches for changed files.
    Once a second, it polls all of the files in the content directory.
    """
    watcher = DirWatcher(settings.CONTENT_DIR)
    build()
    print 'Watching %s...' % settings.CONTENT_DIR
    while True:
        time.sleep(settings.WATCH_INTERVAL)
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
                self.update_mtimes(f.source)
            else:
                mtime = f.mtime
                if not f.source in self.file_list or self.file_list[f.source] != mtime:
                    self.file_list[f.source] = mtime
                    self.changed_files.append(f)

def spawn_child_watcher(*args, **kwargs):
    """
    Start the watcher in a separate thread. Used by runserver.
    """
    thread.start_new_thread(watch, args)




# DEVELOPMENT SERVER
###############################################################################

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import mimetypes

class HandleRequests(BaseHTTPRequestHandler):
    """
    A stupid-simple webserver that serves up static files, and nothing else.
    Requests for a directory will return the contents of the INDEX_FILE.
    Any query parameters are simply stripped from the request path. Only GET
    is supported.
    """
    def do_GET(self):
        try:
            # Ignore any query params (eg as used by livereload)
            self.path = self.path.split('?')[0]
            
            if len(self.path) > 0 and self.path[-1] == '/':
                self.path = self.path + settings.INDEX_FILE
            file_path = settings.DEPLOY_DIR + self.path
            
            # Set the mimetype appropriately. This test is needed to support
            # the text/cache-manifest type used by appcache manifest files.
            if len(self.path) - self.path.rfind('.manifest') == 9:
                mtype= 'text/cache-manifest'
            else:
                mtype = mimetypes.guess_type(file_path)[0]
            
            f = open(file_path)
            self.send_response(200)
            self.send_header('Content-type', mtype)
            self.end_headers()
            self.wfile.write(f.read())
            f.close()

        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

        return

def runserver(port=8000, in_cwd=False, and_watch=False):
    """
    Runs the web server at the specified port (default port 8000).
    """
    if in_cwd:
        settings.DEPLOY_DIR = os.getcwd()
    if and_watch:
        spawn_child_watcher()
    try:
        server = HTTPServer(('', port), HandleRequests)
        stamp('Running server on :%s...\n^C to quit\n\n' % port,color=COKBLUE)
        server.serve_forever()
    except KeyboardInterrupt:
        stamp('Shutting down server', color=COKBLUE)
        server.socket.close()



# CONTROL
###############################################################################

def main():
    if 'runserver' in sys.argv:
        port = 8000
        try:
            port = int(sys.argv[2])
        except:
            pass
        in_cwd = '--cwd' in sys.argv
        and_watch = 'watch' in sys.argv
        runserver(port=port, in_cwd=in_cwd, and_watch=and_watch)

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
        build     - `staples build`
        watch     - `staples watch`
        runserver - `staples runserver [PORT] [watch] [--cwd]`

    Add '-d' to `build` for building with for_deployment set to True.
        e.g. `staples build -d`
    
    Add 'watch' to 'runserver' (after the port if any) to also run the build
    and watch routines.
        e.g. `staples runserver 8000 watch`

    Add '--cwd' to `runserver` (after the port if any) to override the
    DEPLOY_DIR with the current working directory.
        e.g. `staples runserver 8000 --cwd`
    """

if __name__ == '__main__':
    main()
