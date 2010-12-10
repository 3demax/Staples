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
INDEX_FILE = 'index.html'
IGNORE = ()
PROCESSORS = {}

# Look for a settings.py in the current working directory
sys.path.append(PROJECT_ROOT)
try:
    from settings import *
except ImportError:
    print 'No settings.py found, using defaults.\n'
else:
    print 'Found settings.py'


# BUILD FUNCTIONS
###############################################################################
def build():
    print 'Starting build...\n', 'Removing any existing deploy directory'
    shutil.rmtree(DEPLOY_DIR, ignore_errors=True)

    print 'Creating deploy directory: ', DEPLOY_DIR 
    os.mkdir(DEPLOY_DIR)

    print 'Traversing content directory: %s...' % CONTENT_DIR
    scan_directories(CONTENT_DIR)
    
    print '\nBuild done'

def scan_directories(target_path, parent_ignored=False):
    for current_file in glob.glob( os.path.join(target_path, '*') ):
        delegate_file(target_path, current_file, parent_ignored=parent_ignored)

def delegate_file(target_path, current_file, parent_ignored=False):
    print "\nProcessing:", current_file
    f = {}

    f['name'], f['ext'] = os.path.splitext(current_file)

    f['name'] = f['name'].replace(target_path, '')[1:]

    f['file'] = current_file
    f['deploy'] = DEPLOY_DIR + current_file.replace(CONTENT_DIR,'')
    f['deploy_root'] = DEPLOY_DIR

    if os.path.isdir(f['file']):
        if PROCESSORS.get('directory', None):
            PROCESSORS[f['ext']](f)
        else:
            handle_directory(f, parent_ignored=parent_ignored)
    elif f['name'].startswith(".") or f['name'].startswith("_") or f['ext'].endswith("~") or (f['name'] + f['ext']) in IGNORE:
        print 'Ignored:', f['file']
    elif f['ext'] in PROCESSORS:
        PROCESSORS[f['ext']](f)
    elif not parent_ignored:
        handle_others(f)
    else:
        print 'Doing nothing - parent ignored and no processor'

# DEFAULT HANDLERS
# These two functions basically just copy anything they are given over to
# the deploy directory.

def handle_directory(f, parent_ignored):
    """
    Directories not starting with an underscore (_) are created in the deploy
    path. If a directory has an underscore, it is traversed, but it and its
    contents are not copied.
    """
    if not f['name'][0] == '_' and not parent_ignored:
        print 'Making directory: ', f['deploy']
        os.mkdir(f['deploy'])
    else:
        print 'Not duplicating directory'
        parent_ignored = True
    scan_directories(f['file'], parent_ignored=parent_ignored)

def handle_others(f):
    """
    Simply copies files from the source path to the deploy path.
    """
    print 'Copying file to:', f['deploy']
    commands.getoutput(u"cp %s %s" % (f['file'], f['deploy']))


# EXTRA HANDLERS

def handle_django(f):
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

    print 'Rendering:', f['file']
    rendered = render_to_string(f['file'], settings.CONTEXT if settings.CONTEXT else {})

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
    def __init__(self, directory):
        self.target_directory = directory
        self.changed_files = []
        self.file_list = {}
        self.update_mtimes(self.target_directory)

    def find_changed_files(self):
        self.changed_files = []
        self.update_mtimes(self.target_directory)
        return self.changed_files

    def update_mtimes(self, target_path):
        """
        Recursively traverses the directory, updating the dictionary of mtimes
        and the list of files changed since the last check.
        """
        for current_file in glob.glob( os.path.join(target_path, '*') ):
            if os.path.isdir(current_file):
                self.update_mtimes(current_file)
            else:
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

from ftplib import FTP
ftp = FTP()
def deploy():
    """
    Initiates a full rebuild of the project, then deploys it using FTP to the
    specified server, using the specified username and password.
    """
    print 'Rebuilding...'
    build()
    print '\nDeploying to ...'
    ftp.connect(FTP_URL)
    ftp.login(user=FTP_USER, passwd=FTP_PWD)

    traverse_directories(DEPLOY_DIR, file_handler=upload_file,
                        directory_handler=make_remote_dir)



def upload_file(current_file):
    deploy_path = current_file.replace(DEPLOY_DIR, DEPLOY_ROOT)
    print 'uploading', deploy_path
    ftp.storbinary('STOR ' + deploy_path, open(current_file))

def make_remote_dir(current_file):
    deploy_path = current_file.replace(DEPLOY_DIR, DEPLOY_ROOT)
    print 'making directory', deploy_path
    ftp.mkd(deploy_path)


# HELPERS
###############################################################################

def traverse_directories(target_path, file_handler=None,
                        directory_handler=None):
    """
    Recursively traverses a given directory, passing the current file or
    directory to the given handler, if any.
    """
    for current_file in glob.glob( os.path.join(target_path, '*') ):
        if os.path.isdir(current_file):
            if directory_handler:
                directory_handler(current_file)
            traverse_directories(current_file, file_callback=file_callback,
                                directory_callback=directory_callback)
        else:
            if file_handler:
                file_handler(current_file)

# CONTROL
###############################################################################

if __name__ == "__main__":
    if 'runserver' in sys.argv:
        port = 8000
        try:
            port = int(sys.argv[2])
        except:
            pass
        runserver(port)
    elif 'build' in sys.argv:
        build()
    elif 'watch' in sys.argv:
        watch()
    elif 'deploy' in sys.argv:
        deploy()
    else:
        print """
    Staples Usage:
        build     - `python staples.py build`
        watch     - `python staples.py watch`
        runserver - `python staples.py runserver [port]`'
    """
