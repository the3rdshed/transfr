# -*- coding: utf-8 -*-


from django.contrib.auth.models import User
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.core.urlresolvers import reverse, RegexURLResolver, RegexURLPattern, normalize
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404
from django.conf import settings

from transfr import urls
from transfr.utils import join_url

import operator
import os
import tempfile

class UploadProgressCachedHandler(TemporaryFileUploadHandler):
    '''Subclass of TemporaryFileUploadHandler that also keeps a
    journal of the progress of the upload process, so that it can
    be relayed to the client.'''
    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.total_size = None
        self.filename = None # the session id is the name of the JSON data file
        self.tmpfile = None # File containing JSON data on the upload progress
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
        f.write('{"uploaded": %d, "total": %d, "current_file": "%s", "finished": false}' % \
                (self.uploaded, self.total_size, self.current_file.encode('utf-8')))
        f.close()
    
    def upload_complete(self):
        try:
            os.remove(self.tmpfile)
        except (TypeError, IOError, OSError):
            pass


def total_user_size(user):
    '''Return the total size of a user's files.'''
    return sum(f.safesize() for f in user.file_set.all())

def all_user_sizes(users):
    '''Return a list containing tuples where the first
    element is a user and the second element is the
    size of their file set.  The list is ordered by
    size from the largest to the smallest.
    ''' 
    users_size = []
    for user in users:
        users_size.append((user, total_user_size(user)))
    users_size.sort(key=operator.itemgetter(1), reverse=True)
    return users_size

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

def get_normal_user(id):
    user = get_object_or_404(User, pk=id)
    if user.is_superuser:
        raise Http404
    else:
        return user
