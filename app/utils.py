# -*- coding: utf-8 -*-

import os, cjson, tempfile

from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern, normalize
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404
from django.conf import settings

from transfr import urls
from transfr.utils import join_url


class UploadProgressCachedHandler(TemporaryFileUploadHandler):
    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.total_size = None
        self.filename = None
        self.tmpfile = None
        self.uploaded = 0
        self.current_file = None

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        if self.total_size is None:
            self.total_size = content_length
        super(UploadProgressCachedHandler, self).handle_raw_input(
            input_data, META, content_length, boundary, encoding)

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        super(UploadProgressCachedHandler, self).new_file(
            field_name, file_name, content_type, content_length, charset)
        self.current_file = file_name
        self.filename = self.request.COOKIES['sessionid']
        self.tmpfile = os.path.join(tempfile.gettempdir(), self.filename)

    def receive_data_chunk(self, raw_data, start):
        super(UploadProgressCachedHandler, self).receive_data_chunk(raw_data, start)
        self.uploaded += len(raw_data)
        f = open(self.tmpfile, 'w')
        f.write("{'uploaded': %d, 'total': %d, 'current_file': '%s', finished: false}" % \
                (self.uploaded, self.total_size, self.current_file))
        f.close()
    
    def upload_complete(self):
        try:
            os.remove(self.tmpfile)
        except (TypeError, IOError, OSError):
            pass


def total_size(user):
    return sum(f.safesize() for f in user.file_set.all())

def superuser_required(view_func):
    def new(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            raise Http404
    return new

def render(request, template_name, *args, **kwargs):
    kwargs['context_instance'] = RequestContext(request)
    return render_to_response(template_name, *args, **kwargs)

class URLDict(object):
    def __init__(self):
        self.dict = None

    def urls_dict(self):
        if self.dict is None:
            self.dict = self.generate_urls_dict('/', {}, urls.urlpatterns)
        return self.dict

    def generate_urls_dict(self, root, d, patterns):
        for pattern in patterns:
            if isinstance(pattern, RegexURLResolver):
                d.update(self.generate_urls_dict(join_url(root, normalize(pattern.regex.pattern)[0][0]),
                                                 {},
                                                 pattern.url_patterns))
            elif isinstance(pattern, RegexURLPattern):
                if pattern.name:
                    s = normalize(pattern.regex.pattern)[0][0]
                    s = s.replace('(', '').replace(')s', '')
                    d[pattern.name] = join_url(root, s)

        return d

ud = URLDict()

def transfr_processor(request):
    '''
    This is a context processor, the items in this
    dictionary will be sent to all templates that use
    RequestContext.  This function must be added to
    TEMPLATE_CONTEXT_PROCESSORS in settings.py
    '''
    return {
        'DEBUG'           : settings.DEBUG,
        'json_urls'       : cjson.encode(ud.urls_dict()),
    }

