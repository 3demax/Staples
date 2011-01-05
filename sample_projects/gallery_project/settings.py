import os, datetime

PROJECT_ROOT = os.getcwd()

CONTENT_DIR = os.path.join(PROJECT_ROOT,'content')
DEPLOY_DIR = os.path.join(PROJECT_ROOT,'deploy')

from processors import handle_gallery
from staples import handle_django

PROCESSORS = {
    '/': handle_gallery,
    '.django': handle_django
}

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT,'content'),
    os.path.join(PROJECT_ROOT,'templates'),
)

GALLERY_INDEX_TEMPLATE = 'gallery_index.html.django'
GALLERY_PAGE_TEMPLATE = 'gallery_photo.html.django' 

GALLERY_INFO_FILE = 'info.json'
THUMBNAIL_PREFIX = 'thumb-'
THUMBNAIL_SIZE = [200,200] # maximum width and maximum height



CONTEXT = {
    'urls': {
        'home': '/',
    }
}



