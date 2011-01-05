# Staples
## Just the basics of static site processing

Staples is for static sites, particularly ones where each page has a specific layout. It gives direct control of the structure, while still allowing for the advantages of templating and other automated processing. It follows the old-school model of the URLs being based on the directory structure, with `index.html` files and so on. Basically, Staples just passes everything through, but applies processing to specified files.

Loosely based on [aym-cms](https://github.com/lethain/aym-cms), and inspired by [bottle](http://bottle.paws.de) and [Django](http://www.djangoproject.com)



## Installation

The core is entirely contained within the file `staples.py`. The simplest usage is to just include `staples.py` in the project folder. However, Staples operates based on the current working directory, so the `staples.py` file itself can go anywhere that you can run it. It can even be added to your PATH and given executable permissions, turning it into a command. You can also rename it or use an alias to make the command simply `staples`.

Staples is inspired by Django, and uses the `settings.py` method of defining project-specific variables, such as content paths, template directories, deployment settings, etc. While not required, the `settings.py` file is helpful as it also is responsible for mapping the processors to the kinds of files (see Building and Watching). Any processors you have need to be in a spot accessible to Python and imported in settings. See `settings.py` in the sample projects for an example of this.



## Usage

* `python staples.py runserver [port]`: run the dev server, with optional port
* `python staples.py build`: build the project
* `python staples.py watch`: build, then watch the content directory for changes and process changed files

Add `-v` to any command for verbose output, e.g. `python staples.py watch -v`.

## Server

The development server is very, very simple. It just handles requests for static files to `localhost:8000`. By default, the port is `8000`, though you can specify the port you want to use by adding it after runserver: `python staples.py runserver 8080` runs it at `localhost:8080`. Requests for directories will return back the specified INDEX_FILE (default is `index.html`) in that directory.

To use the server, you first have to build the project so that there is a deploy folder to serve from.



## Building and Watching

Everything goes into `content/` and comes out in `deploy/`, or whatever you set the content and deploy directories to be. Files and directories starting with `_` will not be copied (but will be processed). e.g. If your sass directory is `_sass`, the sass files will not be copied, but the sass processor can still compile them into CSS. It should be noted that `build` will delete the deploy directory and everything in it, then replace it with the processed content.

Files and folders will be processed according to the specified settings. The processors are mapped to extensions using a dictionary in `settings.py`. Here, the extension `.ext` is mapped to the processor function `handle_ext`.

    PROCESSORS = {
        '.ext': handle_ext,
    }

Any files that aren't handled by a specific processor get handled by the default processor.

`watch` takes `build` a step further. It does an initial build, then watches the content directory for changes. Any changed files are processed.
Note: `watch` does not remove files or folders from the deploy directory that have been removed from the content directory, so a full rebuild is necessary if you want to remove files. (Or, you can manually delete the files from the deploy directory.) Also, changes to extended or included templates may not change the files that use them, depending on the behavior of the processor.



## Processors

There are two default processors, one for files and one for directories. They simply copy over files and directories that don't match ignore parameters. This alone is kind of pointless, so it's helpful to specify processors for different kinds of files. The primary use is rendering templates. You can use any template renderer you like. Staples includes a Django template processor, which requires Django (though you don't need Django if you don't want to use it). Staples also includes a Markdown processor, which requires the `markdown` Python module.

You can override the default processors by mapping the desired handlers to '/' for directories and '*' for files.

### Django Processor
To use the included Django processor, `handle_django`, map the processor to the extension of your templates:

    PROCESSORS = {
        '.django': handle_django,
        ...
    }

If you include the `.django` extension in your Django templates, it will get removed, so the secondary extension should be the desired extension of the output. e.g. `index.html.django` or `index.django.html` become `index.html` and `sitemap.xml.django` or `sitemap.django.xml` become `sitemap.xml`

The Django processor demonstrates two ways to use structure templates. The first is simply including it in the content directory, but prepended with `_` so it does not get copied over. The second, more semantic way, is to have a folder outside the content directory that is included in the TEMPLATE_DIRS variable. These templates can be referenced by templates inside the content directory, but are not touched by the general processing action.

See [Included Processors](https://github.com/typeish/staples/wiki/Processors) for more information.


### Markdown Processor
To use the included markdown processor, `handle_markdown`, map the processor to the extension of your source files:

    PROCESSORS = {
        '.md': handle_markdown,
        ...
    }

Whichever extension you map the handler to will be replaced by .html in the output files. e.g. `index.md` becomes `index.html`.

See [Included Processors](https://github.com/typeish/staples/wiki/Processors) for more information.



## Custom Processors

If you have something that needs to be done to a type of file, you can make a processor for it. Simply create a function that takes in a file and outputs whatever it needs to output, then map it to the extension in `settings.py`. You can also override what is done to directories using the `/` key.

Processors are given a File object describing the file. See the source for the attributes available.

The deploy path given does not have to be where the processed output goes. The processor can place the output wherever it likes. Since most operations involve passing the file through in some way, it's convenient to have the deploy path provided.



## Sample Projects

There are sample projects that demonstrate how to use the included processors. Each has basic templates, styles, and other content in both the source form and deployed form, for comparison. Logically, the sample Django project requires Django, and the sample Markdown project requires `markdown`. There is also a basic project with no settings, included simply for demonstration.



## TODO

* Pattern-based matching (wildcards, don't limit to extensions or keywords like 'directory')
* Optional FTP or SSH upload for `python staples.py deploy` and `python staples.py redeploy` commands - needs to save a list of the mtimes.
* Include processors for pystache, Closure Compiler, SASS compiler, etc



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
