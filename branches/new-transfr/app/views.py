# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.files.uploadhandler import FileUploadHandler
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.template.defaultfilters import filesizeformat
from django.utils import simplejson
from django.utils.translation import ugettext as _

from transfr.utils import join_url
from transfr.app.models import File, RawPassword
from transfr.app.forms import SingleFileUploadForm, MultipleFileUploadForm
from transfr.app.utils import (total_user_size, superuser_required, render, all_user_sizes,
                               get_normal_user)

import tempfile
import os
import operator
import mimetypes

@login_required
def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    filename = request.COOKIES['sessionid']
    tmpfile  = os.path.join(tempfile.gettempdir(), filename)
    try:
        f = open(tmpfile, 'r')
        data = f.read()
    except (IOError, OSError):
        data = '{"uploaded": "1", "total": "1", "finished": true}'
    finally:
        f.close()

    return HttpResponse(data)

def mylogin(request):
    if request.method == 'POST':
        form = AuthenticationForm(None, request.POST, label_suffix='')
        if form.is_valid():
            login(request, form.user_cache)
            return HttpResponseRedirect(reverse('file_list'))
    else:
        form = AuthenticationForm(label_suffix='')
    return render(request, 'app/login.html',
                  {'form': form,
                  })

def mylogout(request):
    logout(request)
    return HttpResponseRedirect(reverse('disconnected'))

def disconnected(request):
    return render(request, 'app/disconnected.html')

@login_required
def file_list(request, id=None):
    if id is None:
        if 'current_user_id' in request.session:
            id = request.session['current_user_id']
        else:
            id = request.user.id

    user = get_object_or_404(User, pk=id)
    if user != request.user and not request.user.is_superuser:
        raise Http404
    request.session['current_user_id'] = id
    return render(request, 'app/file_list.html',
                  {'this_user': user,
                   'user_list': User.objects.order_by('username'),
                  })


@login_required
def add_file(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    # Only superusers or the owner can upload files to that profile.
    if request.user != user and not request.user.is_superuser:
        raise Http404

    if request.method == 'POST':
        form = MultipleFileUploadForm(user, request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('file_list_user', args=[user_id]))
    else:
        form = SingleFileUploadForm(1)
    return render(request, 'app/add_file.html',
                  {'form': form,
                   'user_id': user_id,
                  })

@login_required
def additional_upload_form(request, n):
    form = SingleFileUploadForm(n)
    return HttpResponse(form.as_ul())


@login_required
def delete_file(request):
    if request.method != 'POST':
        raise Http404
    files = get_list_or_404(File, pk__in=request.POST.getlist('ids'))
    owner = files[0].user
    for file in files:
        if file.owned_by(request.user):
            file.delete()
    return HttpResponse(simplejson.dumps([owner.file_set.count(),
                                          filesizeformat(total_user_size(owner))]))

@superuser_required
def instructions(request, id):
    user = get_normal_user(id)
    return render(request, 'app/instructions.html',
                  {'this_user': user,
                   'raw_password': RawPassword.objects.get(user=user).password,
                   'address': 'http://' + join_url(request.META.get('HTTP_HOST', ''),
                                                   settings.BASE_URL),
                  })

###
# Users
###
@superuser_required
def manage_users(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('manage_users'))
    else:
        form = UserCreationForm()

    # Remove help text
    form.fields['username'].help_text = ''

    # User list
    all_users = User.objects.exclude(is_superuser=True).order_by('username')
    user_list = []
    for user in all_users:
        user_list.append((user,
                          RawPassword.objects.get(user=user),
                          user.file_set.count(),
                          total_user_size(user)))

    # Space usage by each user, sorted by space.
    user_sizes = all_user_sizes(all_users)
    total_size = sum(us[1] for us in user_sizes) or 1 # 1 to prevent div by 0
    
    return render(request, 'app/manage_users.html',
                  {'user_list': user_list,
                   'form': form,
                   'user_sizes': user_sizes,
                   'total_size': total_size,
                  })


@superuser_required
def set_password(request, id):
    user = get_normal_user(id)

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('manage_users'))
    else:
        form = SetPasswordForm(user)
    return render(request, 'app/set_password.html',
                  {'form': form,
                   'this_user': user,
                  })

@superuser_required
def delete_user(request, id):
    user = get_normal_user(id)
    if request.method == 'POST':
        user.delete()
        return HttpResponseRedirect(reverse('manage_users'))
    else:
        return render(request, 'app/delete_user.html',
                      {'this_user': user,
                      })


# XXX: Not used right now, uses too much memory.
def download_file(request, id):
    f = get_object_or_404(File, pk=id)
    mime = mimetypes.guess_type(f.file.name)[0] or 'application/octet-stream'
    wrapper = FileWrapper(f.file)
    response = HttpResponse(wrapper, content_type=mime)
    response['Content-Disposition'] = 'attachment; filename=%s' % \
            os.path.basename(f.file.name)
    response['Content-Length'] = f.safesize()
    return response


def help(request):
    return render(request, 'app/help.html')

def about(request):
    return render(request, 'app/about.html')
