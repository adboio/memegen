from sanic import Request
import time
import os
from pathlib import Path

from . import settings, utils
from .models import Template

_template_cache = {
    'templates': None,
    'last_reload': None
}

def should_reload_templates():
    """Check if any template files have been modified since last reload"""
    if _template_cache['last_reload'] is None:
        return True
        
    template_dir = Path("path/to/your/templates")
    latest_mtime = max(
        os.path.getmtime(f) 
        for f in template_dir.rglob('*') 
        if f.is_file()
    )
    
    return latest_mtime > _template_cache['last_reload']

def load_templates():
    """Actually load templates from disk"""
    templates = Template.objects.filter(valid=True, _exclude="_custom")
    return sorted(templates)

def get_cached_templates(force_reload=False):
    """Get templates from cache, reloading if needed"""
    if _template_cache['templates'] is None or force_reload:
        _template_cache['templates'] = load_templates()
        _template_cache['last_reload'] = time.time()
    return _template_cache['templates']

def get_valid_templates(
    request: Request, query: str = "", animated: bool | None = None
) -> list[dict]:
    templates = get_cached_templates()
    
    if query:
        templates = [t for t in templates if t.matches(query)]
    if animated is True:
        templates = [t for t in templates if "animated" in t.styles]
    elif animated is False:
        templates = [t for t in templates if "animated" not in t.styles]
    
    return [template.jsonify(request) for template in templates]

def get_example_images(
    request: Request, query: str = "", *, animated: bool | None = None
) -> list[tuple[str, str]]:
    templates = get_cached_templates()
    
    if query:
        templates = [t for t in templates if t.matches(query)]

    if animated is None:
        animated = utils.urls.flag(request, "animated")
        exact = True
    else:
        exact = False

    images = []
    for template in templates:
        if exact and animated is True and "animated" not in template.styles:
            continue
        if exact and animated is False and "animated" in template.styles:
            continue

        if animated is True:
            extension = settings.DEFAULT_ANIMATED_EXTENSION
        elif "animated" in template.styles and animated is not False:
            extension = settings.DEFAULT_ANIMATED_EXTENSION
        else:
            extension = settings.DEFAULT_STATIC_EXTENSION

        example = template.build_example_url(request, extension=extension)
        self = template.build_self_url(request)
        images.append((example, self))

    return images

def get_test_images(request: Request) -> list[str]:
    animated = utils.urls.flag(request, "animated")
    if animated:
        images = [
            image
            for image in settings.TEST_IMAGES
            if image[2] in settings.ANIMATED_EXTENSIONS
        ]
    else:
        images = settings.TEST_IMAGES

    return [
        request.app.url_for(
            "Images.detail_text",
            template_id=id,
            text_filepath=utils.text.encode(lines) + "." + extension,
        )
        for id, lines, extension in images
    ]
