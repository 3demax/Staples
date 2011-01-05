from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
import Image
import glob, os, commands

from staples import handle_others, File
import settings

try:
    import json
except ImportError:
    from django.utils import simplejson as json



def handle_gallery(f, **kwargs):

    os.environ['DJANGO_SETTINGS_MODULE'] = u"settings"

    os.mkdir(f.deploy_path)

    gallery_info_file = open(os.path.join(f.source, settings.GALLERY_INFO_FILE))
    gallery_info = gallery_info_file.read()
    gallery_info_file.close()
    gallery_info = json.loads(gallery_info)
    captions = gallery_info.get("captions", {})
    
    i = 1;
    photo_list = []
    
    # "discover" the photos in the gallery
    for file in glob.glob( os.path.join(f.source, '*') ):
        file = File(file, **kwargs)
        if file.name != settings.GALLERY_INFO_FILE:
            ctx = {
                'num': i,
                'url': file.name,
                'gallery_index': '/' + f.rel_path + '/',
                'gallery': gallery_info,
                'caption': captions.get(file.name, None),
                'file': file
            }
            photo_list.append(ctx)
            i += 1
    
    # render out pages and copy images
    for photo in photo_list:
        context = {}
        context.update(settings.CONTEXT)
        ctx = photo
        if photo['num'] > 1:
            ctx['prev'] = '%s.html' % str(photo['num'] - 1)
        if photo['num'] < len(photo_list):
            ctx['next'] = '%s.html' % str(photo['num'] + 1)
        context.update(ctx)
        rendered = render_to_string(settings.GALLERY_PAGE_TEMPLATE, context)
        deploy_path = os.path.join(f.deploy_path,'%s.html' % str(photo['num']))
        fout = open(deploy_path, 'w')
        fout.write(rendered)
        fout.close()
        cm = u'cp "%s" "%s"' % (photo['file'].source, photo['file'].deploy_path)
        commands.getoutput(cm)

        thumbnail_file = os.path.join(f.deploy_path, settings.THUMBNAIL_PREFIX + photo['file'].name)
        img = Image.open(photo['file'].source)
        img.thumbnail(settings.THUMBNAIL_SIZE, Image.ANTIALIAS)
        img.save(thumbnail_file)


    
    context = settings.CONTEXT if settings.CONTEXT else {}
    context.update({
        'photo_list': photo_list,
        'gallery': gallery_info,
        'thumbnail_prefix': settings.THUMBNAIL_PREFIX
    })
    
    rendered = render_to_string(settings.GALLERY_INDEX_TEMPLATE, context)
    deploy_path = os.path.join(f.deploy_path,'index.html')
    fout = open(deploy_path, 'w')
    fout.write(rendered)
    fout.close()

        # add photo to index list
    # add index to context
    # build index

    # build a gallery using a folder of images, creating an index.html file
    # with all of the images, and an N.html file for each image with the full
    # sized image, up to CONTEXT.max_width


    # 
    # verbose = globals().get('verbose', False)
    # if not f.ignorable and not f.parent_ignored:
    #     from django.template.loader import render_to_string
    #     import settings
    #     os.environ['DJANGO_SETTINGS_MODULE'] = u"settings"
    #     deploy_path = f.deploy_path.replace('.django','')
    # 
    #     if verbose:
    #         print 'Rendering:', f.rel_path
    # 
    #     context = {}
    #     if settings.CONTEXT:
    #         context = settings.CONTEXT
    #     context['for_deployment'] = for_deployment
    #     rendered = render_to_string(f.source, context)
    # 
    #     if verbose:
    #         print 'Saving rendered output to:', deploy_path
    #     fout = open(deploy_path,'w')
    #     fout.write(rendered)
    #     fout.close()
    # elif verbose:
    #     print 'Ignoring:', f.rel_path