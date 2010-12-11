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
