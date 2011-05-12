import os, datetime

PROJECT_ROOT = os.getcwd()

# Django needs absolute paths for template rendering
CONTENT_DIR = os.path.join(PROJECT_ROOT,'content')
DEPLOY_DIR = os.path.join(PROJECT_ROOT,'deploy')

# Add specific filenames to ignore here.
IGNORE = (
    'notes.txt', # All files named 'notes.txt' will be ignored.
)


PROCESSORS = {
    # Add handlers for different filetypes here.
    # e.g. template renderers, CSS compressors, JS compilers, etc...
    # '.ext': handler,
    '.django': 'handle_django',
}

# Django template rendering stuff
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT,'content'),
    os.path.join(PROJECT_ROOT,'templates'),
)

CONTEXT = {
    'pub_date': datetime.datetime(2010,11,1),
    'urls': {
        'static'            : '/static/',
        'home'              : '/',
        'project'           : '/project-qwerty/',
        'project_gallery'   : '/project-qwerty/gallery.html'
    }
}
