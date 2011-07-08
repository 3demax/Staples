# Staples
## Just the basics of static site processing

Staples is for static sites, particularly ones where each page has a specific layout. It gives direct control of the structure, while still allowing for the advantages of templating and other automated processing. It follows the old-school model of the URLs being based on the directory structure, with `index.html` files and so on. Basically, Staples just passes everything through, but applies processing to specified files.

See the [included sample projects](https://github.com/typeish/staples/tree/master/sample_projects) for examples.

Loosely based on [aym-cms](https://github.com/lethain/aym-cms), and influenced by [bottle](http://bottle.paws.de) and [Django](http://www.djangoproject.com).



## Installation

`python setup.py install` will install Staples as a command `staples`.

Alternatively, the core is entirely contained within the file `staples.py`, so that file can just be included in the project folder and execute it using `python staples.py`. However, Staples operates based on the current working directory, so the `staples.py` file itself can go anywhere that you can run it.

There are no dependencies, beyond the Python Standard Library. However, individual processors will likely have specific dependencies. For example, to use the included Django processor, your environment must have Django.



## Usage

Commands:

* `staples build`: build the project
* `staples watch`: build, then watch the content directory for changes and process changed files
* `staples runserver [PORT] [watch] [--cwd]`: run the dev server, with optional port and file building

Project-specific variables, such as content paths and template directories, are specified in a `settings.py` placed in the project root. This file also maps files and extensions to specific processors. Without `settings.py`, Staples simply copies files from `content` to `deploy`. (This is useful for working on something that needs a server, but no templating or other special processing.)


### Build

Everything goes into `content/` and comes out in `deploy/`, or whatever you set the content and deploy directories to be. It should be noted that `build` will delete the deploy directory and everything in it, then replace it with the processed content.

Files and folders will be processed according to the specified settings. The processors are mapped to extensions or filenames using a dictionary in `settings.py`. Here, the extension `.ext` is mapped to the processor function `handle_ext`.

    PROCESSORS = {
        '.ext': 'handle_ext',
    }

Anything not mapped to a processor will be simply copied over, unless it is ignorable. Files and directories starting with `_` will not be copied (but will be processed). e.g. If your sass source directory is `_sass`, the sass files will not be copied, but the sass processor can still compile them into CSS. You can also explicitly ignore any file or folder using the IGNORE setting.

    IGNORE = (
        'ignored.file', # All files named 'ignored.file' will be ignored.
    )


### Watch

Watching will perform a build, then watch the project for changes, rebuilding changed files as necessary.

Note: `watch` does not (yet) remove files or folders from the deploy directory that have been removed from the content directory, so a full rebuild is necessary if you want to remove files. (Or, you can manually delete the files from the deploy directory.) Also, changes to extended or included templates may not change the files that use them, depending on the behavior of the processor.


### Runserver

There is also a simple development server included. It just handles requests for static files to `localhost:8000` from the deploy directory. By default, the port is `8000`, though you can specify the port you want to use by adding it after runserver: `python staples.py runserver 8080` runs it at `0.0.0.0:8080`. Requests for directories will return back the specified INDEX_FILE (default is `index.html`) in that directory.

Adding 'watch' after the port, if any, will also initiate a build and watch routine, building changed files.

Adding '--cwd' after the port, if any, will override the DEPLOY_DIR as the root for the server, using the current working directory. This is useful if you need to serve a static site that doesn't need compiling, or any specified settings.


## Processors

There are two default processors, one for files and one for directories. They simply copy over files and directories that don't match ignore parameters. This alone is kind of pointless, so it's helpful to specify processors for different kinds of files. The primary use is rendering templates. You can use any template renderer you like. Staples includes a Django template processor, which requires Django, and a Markdown processor, which requires the `markdown` Python module.

You can override the default processors by mapping the desired handlers to '/' for directories and '*' for files.

See [Processors](https://github.com/typeish/staples/wiki/) for more information on using and making processors.

### Django Processor
To use the included Django processor, `handle_django`, map the processor to the extension of your templates:

    PROCESSORS = {
        '.django': 'handle_django',
        ...
    }

If you include the `.django` extension in your Django templates, it will get removed, so the secondary extension should be the desired extension of the output. e.g. `index.html.django` or `index.django.html` become `index.html` and `sitemap.xml.django` or `sitemap.django.xml` become `sitemap.xml`.


### Markdown Processor
To use the included markdown processor, `handle_markdown`, map the processor to the extension of your source files:

    PROCESSORS = {
        '.md': 'handle_markdown',
        ...
    }

Whichever extension you map the handler to will be replaced by .html in the output files. e.g. `index.md` becomes `index.html`.


### Custom Processors

If you have something that needs to be done to a type of file, you can make a processor for it. Simply create a function that takes in a file and outputs whatever it needs to output, then map it to the extension in `settings.py`.

Processors are given a File object describing the file. See the [Staples source](https://github.com/typeish/staples/blob/master/staples.py) for the attributes available.



## Sample Projects

There are sample projects that demonstrate how to use the included processors. Each has basic templates, styles, and other content in both the source form and deployed form, for comparison. Logically, the sample Django project requires Django, and the sample Markdown project requires `markdown`. Also included is a gallery project with a custom gallery processor that demonstrates what a more complicated processor can do.



## LICENSE 

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
