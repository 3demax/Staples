import os

PROJECT_ROOT = os.getcwd()

# Django needs absolute paths for template rendering
CONTENT_DIR = os.path.join(PROJECT_ROOT,'content')
DEPLOY_DIR = os.path.join(PROJECT_ROOT,'deploy')

# Add specific filenames to ignore here.
IGNORE = (
    'notes.txt', # All files named 'notes.txt' will be ignored.
)


# import the included Django processor from staples
from staples import handle_django

PROCESSORS = {
    # Add handlers for different filetypes here.
    # e.g. template renderers, CSS compressors, JS compilers, etc...
    # '.ext': handler,
    '.django': handle_django,
}

# Django template rendering stuff
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT,'content'),
)

CONTEXT = {
    'urls': {
        'static': '/static/',
        'home': '/',
    }
}

# Set this to be the name of the file used for serving directories.
# Standard practice is to use 'index.html', though if your production
# server uses something else, you can customize this setting accordingly.
INDEX_FILE = 'index.html'

# Deploy information
FTP_URL = 'ftp.example.com'
REMOTE_ROOT = '/example.com'
FTP_USER = 'user'
FTP_PWD = 'password'
