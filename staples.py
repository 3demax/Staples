#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Staples is a simple static site generator based on the idea of processors
mapped to types of files. It includes a basic server for development, and
has no external requirements itself, beyond the Python Standard Library.
Specific processors, such as the included Django template renderer, will
have their own requirements.

Info and source: http://github.com/typeish/Staples

Alec Perkins, type(ish) inc
License: UNLICENSE
"""

__author__ = 'Alec Perkins, type(ish) inc'
__version__ = '0.1a'
__license__ = 'UNLICENSE'

import os, shutil, commands, glob, sys

# Default settings
PROJECT_ROOT = os.getcwd()
CONTENT_DIR = os.path.join(PROJECT_ROOT, 'content')
DEPLOY_DIR = os.path.join(PROJECT_ROOT, 'deploy')
DEPLOY_TRACKING_FILE = os.path.join(PROJECT_ROOT, 'staples_deploy_info.p')

INDEX_FILE = 'index.html'
IGNORE = ()
PROCESSORS = {}

# Look for a settings.py in the current working directory
sys.path.append(PROJECT_ROOT)
try:
    from settings import *
except ImportError:
    if __name__ == "__main__":
        print 'No settings.py found, using defaults.\n'
else:
    if __name__ == "__main__":
        print 'Found settings.py'

verbose=False

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

    traverse_directories(CONTENT_DIR, file_handler=delegate_file, directory_handler=delegate_directory, target_path=CONTENT_DIR, parent_ignored=False, **kwargs)
    
    print '\nBuild done'

def delegate_directory(current_file, parent_ignored=False, target_path=None, **kwargs):
    if verbose:
        print "\nProcessing:", current_file
    f = prep_file(current_file, target_path)
    if os.path.isdir(f['file']):
        if PROCESSORS.get('directory', None):
            PROCESSORS[f['ext']](f, **kwargs)
        else:
            handle_directory(f, **kwargs)

def delegate_file(current_file, parent_ignored=False, target_path=None, **kwargs):
    if verbose:
        print "\nProcessing:", current_file
    f = prep_file(current_file, target_path)

    if is_ignorable(f['name'] + f['ext']):
        if verbose:
            print 'Ignored:', f['file']
    elif f['ext'] in PROCESSORS:
        PROCESSORS[f['ext']](f, **kwargs)
    elif not parent_ignored:
        handle_others(f, **kwargs)
    else:
        if verbose:
            print 'Doing nothing - parent ignored and no processor'


# DEFAULT HANDLERS
# These two functions basically just copy anything they are given over to
# the deploy directory.

def handle_directory(f, parent_ignored=False, **kwargs):
    """
    Directories not starting with an underscore (_) are created in the deploy
    path. If a directory has an underscore, it is traversed, but it and its
    contents are not copied.
    """
    if not f['name'][0] == '_' and not parent_ignored:
        if verbose:
            print 'Making directory: ', f['deploy']
        os.mkdir(f['deploy'])
    else:
        if verbose:
            print 'Not duplicating directory'
        parent_ignored = True
    traverse_directories(f['file'], parent_ignored=parent_ignored)

def handle_others(f, **kwargs):
    """
    Simply copies files from the source path to the deploy path.
    """
    if verbose:
        print 'Copying file to:', f['deploy']
    commands.getoutput(u"cp %s %s" % (f['file'], f['deploy']))


# EXTRA HANDLERS

def handle_django(f, for_deployment=False):
    """
    Renders templates using the Django template rendering engine. If the
    template ends in .django, the resulting output filename has that removed.
    
    Requires:
        Django - any version that can handle the templates you give it
        settings.py - placed in the same directory and defines both
                      TEMPLATE_DIRS and CONTEXT
    """
    
    from django.template.loader import render_to_string
    import settings
    os.environ['DJANGO_SETTINGS_MODULE'] = u"settings"
    deploy_path = f['deploy'].replace('.django','')

    if verbose:
        print 'Rendering:', f['file']
    
    context = {}
    if settings.CONTEXT:
        context = settings.CONTEXT
    context['for_deployment'] = for_deployment
    rendered = render_to_string(f['file'], context)

    if verbose:
        print 'Saving rendered output to:', deploy_path
    fout = open(deploy_path,'w')
    fout.write(rendered)
    fout.close()



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
                if f[2]:
                    delegate_file(f[1], f[0])

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
        traverse_directories(self.target_directory, file_handler=self.update_mtimes, target_path=self.target_directory)
        return self.changed_files

    def update_mtimes(self, current_file, target_path=None):
        """
        Recursively traverses the directory, updating the dictionary of mtimes
        and the list of files changed since the last check.
        """
        try:
            mtime = os.path.getmtime(current_file)
        except OSError:
            # removed
            mtime = None
            try:
                self.file_list.pop(current_file)
            except KeyError:
                pass
            self.changed_files.append((current_file, target_path, False))
        else:
            # added or changed
            if not current_file in self.file_list or self.file_list[current_file] != mtime:
                self.file_list[current_file] = os.stat(current_file).st_mtime
                self.changed_files.append((current_file, target_path, True))


# DEPLOY FUNCTIONS
###############################################################################

from ftplib import FTP, error_perm
ftp = FTP()

def deploy(full=False):
    """
    Initiates a full rebuild of the project, then deploys it using FTP to the
    specified server, using the specified username and password.
    """
    print 'Rebuilding...'
    build(for_deployment=True)
    print '\nDeploying to %s...' % FTP_URL

    try:
        import cPickle as pickle
    except ImportError:
        import pickle

    try:
        last_mtimes_file = open(DEPLOY_TRACKING_FILE)
    except:
        print 'no file'
        last_mtimes = {}
    else:
        try:
            last_mtimes = pickle.load(last_mtimes_file)
            last_mtimes_file.close()
        except:
            last_mtimes = {}

    ftp.connect(FTP_URL)
    ftp.login(user=FTP_USER, passwd=FTP_PWD)

    scanner = DirWatcher(CONTENT_DIR, update=False)
    scanner.file_list = last_mtimes

    if full:
        traverse_directories(DEPLOY_DIR, file_handler=upload_file, directory_handler=make_remote_dir)
    else:
        changed_files = scanner.find_changed_files()
        for f in changed_files:
            f = prep_file(f[0], f[1])

    last_mtimes_file = open(DEPLOY_TRACKING_FILE, 'w')
    pickle.dump(scanner.file_list, last_mtimes_file)
    last_mtimes_file.close()


def upload_file(current_file):
    deploy_path = current_file.replace(DEPLOY_DIR, DEPLOY_ROOT)
    if verbose:
        print 'uploading', deploy_path
    try:
        ftp.delete(deploy_path)
    except:
        pass
    ftp.storbinary('STOR ' + deploy_path, open(current_file))

def make_remote_dir(current_file):
    deploy_path = current_file.replace(DEPLOY_DIR, DEPLOY_ROOT)
    try:
        if verbose:
            print 'making directory', deploy_path
        ftp.mkd(deploy_path)
    except error_perm:
        pass


# HELPERS
###############################################################################

def traverse_directories(t_path, file_handler=None,
                        directory_handler=None, **kwargs):
    """
    Recursively traverses a given directory, passing the current file or
    directory to the given handler, if any. Also passes through additional
    keyword arguments to the handlers.
    """
    for current_file in glob.glob( os.path.join(t_path, '*') ):
        if os.path.isdir(current_file):
            if directory_handler:
                directory_handler(current_file, **kwargs)
            traverse_directories(current_file, file_handler=file_handler,
                            directory_handler=directory_handler, **kwargs)
        else:
            if file_handler:
                file_handler(current_file, **kwargs)

def prep_file(current_file, target_path):
    f = {}

    f['name'], f['ext'] = os.path.splitext(current_file)

    if target_path:
        f['name'] = f['name'].replace(target_path, '')[1:]

    f['file'] = current_file
    f['deploy'] = DEPLOY_DIR + current_file.replace(CONTENT_DIR,'')
    f['deploy_root'] = DEPLOY_DIR
    return f

def is_ignorable(f):
    return f.startswith(".") or f.startswith("_") or f.endswith("~") or f in IGNORE


# CONTROL
###############################################################################

if __name__ == "__main__":
    if 'verbose' in sys.argv:
        verbose = True
    else:
        verbose = False

    if 'runserver' in sys.argv:
        port = 8000
        try:
            port = int(sys.argv[2])
        except:
            pass
        runserver(port)

    elif 'build' in sys.argv:
        if '-d' in sys.argv:
            build(for_deployment=True)
        else:
            build()

    elif 'watch' in sys.argv:
        watch()

    elif 'deploy' in sys.argv:
        deploy()
    elif 'redeploy' in sys.argv:
        deploy(full=True)

    else:
        print """
    Staples Usage:
        build     - `python staples.py build`
        watch     - `python staples.py watch`
        runserver - `python staples.py runserver [port]`'
    
    Add 'verbose' to any command for verbose output.
    e.g. `python staples.py build verbose`
    
    Add '-d' to `build` for building with for_deployment set to True.
    e.g. `python staples.py build -d`
    """
