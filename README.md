# Staples - Static Site Processing

Staples is for static sites, particularly ones where each page has a specific layout. It gives direct control of the structure, while still allowing for the advantages of templating and other automated processing. It follows the old-school model of the URLs being based on the directory structure, with `index.html` files and so on. Basically, Staples just passes everything through, but applies processing to specified files.

Loosely based on [aym-cms](https://github.com/lethain/aym-cms), and inspired by [bottle](http://bottle.paws.de) and [Django](http://www.djangoproject.com)


## Installation

The simplest usage is to just include `staples.py` in the project folder. However, Staples operates based on the current working directory, so the `staples.py` file itself can go anywhere that you can run it. It can even be added to your PATH and given executable permissions, turning it into a command. You can also rename it or use an alias to make the command simply `staples`.

Staples is inspired by Django, and uses the `settings.py` method of defining project-specific variables, such as content paths, template directories, deployment settings, etc. While not required, the `settings.py` file is helpful as it also is responsible for mapping the processors to the kinds of files (see Building and Watching). Any processors you have need to be in a spot accessible to Python and imported in settings. See `settings.py` in the sample project for an example of this.


## Usage

* `python staples.py runserver [port]`: run the dev server, with optional port
* `python staples.py build`: build the project
* `python staples.py watch`: build, then watch the content directory for changes and process changed files


## Server

The development server is very, very simple. It just handles requests for static files to `localhost:8000`. By default, the port is `8000`, though you can specify the port you want to use by adding it after runserver: `python staples.py runserver 8080` runs it at `localhost:8080`. Requests for directories will return back the specified INDEX_FILE (default is `index.html`) in that directory.

To use the server, you first have to build the project so that there is a deploy folder to serve from.


## Building and Watching

Everything goes into `content/` and comes out in `deploy/`, or whatever you set the content and deploy directories to be. Files and directories starting with `_` will not be copied (but will be processed). e.g. If your sass directory is `_sass`, the sass files will not be copied, but the sass processor can still compile them into CSS. It should be noted that `build` will delete the deploy directory and everything in it, then replace it with the processed content.

Files and folders will be processed according to the specified settings. The processors are mapped to extensions using a dictionary in `settings.py`.

    PROCESSORS = {
        '.ext': handle_ext,
    }

Any files that aren't handled by a specific processor get handled by the default processor.

`watch` takes `build` a step further. It does an initial build, then watches the content directory for changes. Any changed files are processed.
Note: `watch` does not remove files or folders from the deploy directory that have been removed from the content directory, so a full rebuild is necessary if you want to remove files. (Or, you can manually delete the files from the deploy directory.) Also, changes to extended or included templates may not change the files that use them, depending on the behavior of the processor.


## Processors

There are two default processors, one for files and one for directories. They simply copy over files and directories that don't match ignore parameters. This alone is kind of pointless, so it's helpful to specify processors for different kinds of files. The primary use is rendering templates. You can use any template renderer you like. Staples includes a Django template handler, which requires Django (though you don't need Django if you don't want to use it). "Structure" templates that are inside the content directory, such as a base template or an include, should be prefixed with `_` so they don't get copied over.

### Django Templates
To use the included Django templating, map the processor to the extension of your templates:

    PROCESSORS = {
        '.django': handle_django,
        ...
    }

If you include the `.django` extension in your Django templates, it will get removed, so the secondary extension should be the desired extension of the output. e.g. `index.html.django` or `index.django.html` become `index.html` and `sitemap.xml.django` or `sitemap.django.xml` become `sitemap.xml`

#### Required

* [Django](http://www.djangoproject.com/) - any version that can handle the templates you give it
* settings.py - placed in the same directory and defines TEMPLATE_DIRS

The TEMPLATE_DIRS variable contains all the locations for the renderer to look for templates in:

    TEMPLATE_DIRS = (
        os.path.join(ROOT_PATH,'content'),
        ...
    )

#### Optional

* Context - a dictionary that provides variables and such to the templates when rendered.

Sample context:

    CONTEXT = {
        'pub_date': datetime.datetime(2010,11,1),
        'urls': {
            'static': '/static/'
        }
    }


## Custom Processors

If you have something that needs to be done to a type of file, you can make a processor for it. Simply create a function that takes in a file and outputs whatever it needs to output, then map it to the extension in `settings.py`. You can also override what is done to directories using the `directory` key.

Processors are given a dictionary describing the file. Given a file at `/content/path/foo.bar`, the dictionary looks like this:

    {
        'file':        '/content/path/foo.bar',    # The path of the file
        'name':        'foo',                      # The name of the file
        'ext':         '.bar',                     # The extension of the file, including '.'
        'deploy':      '/deploy/path/foo.bar',     # The deploy path
        'deploy_root': '/deploy'                   # For convenience, the root of the deploy path
    }

The deploy path given does not have to be where the processed output goes. The processor can place the output wherever it likes. (The root of the deploy path is provided as well, for this instance.) Since several operations involve passing the file through, it's convenient to have the deploy path provided.

## Sample Project

The sample project included has some basic templates, styles, and other content in both its "source" form and its deployed form. It uses Django templates, so to try building or watching with it you will need Django. (You can also just remove the '.django' handler from `settings.py`.) You can also try the development server with it. The settings file includes sample FTP settings, though obviously the `deploy` command won't work with them.


## TODO
* Pattern-based matching (wildcards, don't limit to extensions or keywords like 'directory')
* Optional FTP or SSH upload for `python staples.py deploy` and `python staples.py redeploy` commands - needs to save a list of the mtimes.
* Include processors for pystache, Closure Compiler, SASS compiler, etc
* Combine watch and runserver so only one terminal is needed
* DRY-up the file manipulation/traversal code