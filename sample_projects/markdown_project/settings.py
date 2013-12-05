import os

PROJECT_ROOT = os.getcwd()

CONTENT_DIR = os.path.join(PROJECT_ROOT,'content')
DEPLOY_DIR = os.path.join(PROJECT_ROOT,'deploy')

# Add specific filenames to ignore here.
IGNORE = (
    'notes.txt', # All files named 'notes.txt' will be ignored.
)


PROCESSORS = {
    # Add handlers for different filetypes here.
    # e.g. template renderers, CSS compressors, JS compilers, etc...
    # '.ext': 'handler',
    '.md': 'handle_markdown',
}

# The Markdown content will be inserted into this markup at the point marked by
# `{{ CONTENT }}`. Another option is to put this markup into a file, and load
# it in like so: `MD_WRAP = open('wrap.file').read()`
MD_WRAP = """<!DOCTYPE html>
<html>
<head>
    <title> - Sample Markdown Project</title>
    <meta type="description" content="" />
    <link rel="stylesheet" href="/css/style.css" type="text/css" media="screen" />
</head>
<body>
    <nav><a href="index.html">Home</a> <a href="about.html">About</a> <a href="contact.html">Contact</a></nav>
{{ CONTENT }}
</body>
</html>
"""
