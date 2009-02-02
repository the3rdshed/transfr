# -*- coding: utf-8 -*-

from django.core.files.uploadhandler import FileUploadHandler
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.utils import simplejson
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext as _

from transfr import settings
from transfr.app.models import File, RawPassword
from transfr.app.forms import SingleFileUploadForm, MultipleFileUploadForm, InstructionsForm
from transfr.app.utils import total_size, superuser_required, render

import tempfile
import os
import operator
import re
import pdb

@login_required
def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    filename = request.COOKIES['sessionid']
    tmpfile  = os.path.join(tempfile.gettempdir(), filename)
    try:
        f = open(tmpfile, 'r')
        data = f.readlines()
        f.close()
    except Exception, e:
        data = "{'uploaded': '1', 'total': '1', finished: true}"

    return HttpResponse(data)

def mylogin(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('file_list'))
        else:
            return render(request, 'app/login.html',
                          {'message': _(u"Incorrect username or password")})
    else:
        return render(request, 'app/login.html')

def mylogout(request):
    logout(request)
    return HttpResponseRedirect(reverse('disconnected'))

def disconnected(request):
    return render(request, 'app/disconnected.html')

@login_required
def file_list(request):
    module_thumbnails = settings.THUMBNAIL_MODULE
    if request.user.is_superuser:
        users = User.objects.all()
    else:
        users = User.objects.filter(pk=request.user.id)
    return render(request, 'app/file_list.html',
                  {'users': users,
                   'module_thumbnails': module_thumbnails,
                  })


def get_field_numbers(files):
    number_re = re.compile(r'(\d+)$')
    for filename in files:
        m = number_re.search(filename)
        if m:
            yield m.group(1)

def select_fields(post, xs):
    new_post = {}
    for x in xs:
        comments = post.get('comments%s' % x)
        if comments is not None:
            new_post['comments%s' % x] = comments
    return new_post


@login_required
def add_file(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    # Only superusers or the owner can upload files to that profile.
    if not request.user.is_superuser and request.user != user:
        raise Http404

    if request.method == 'POST':
        xs = sorted(get_field_numbers(request.FILES))
        new_post = select_fields(request.POST, xs)
        form = MultipleFileUploadForm(user, xs, new_post, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('file_list'))
    else:
        form = SingleFileUploadForm(0)
    return render(request, 'app/add_file.html',
                  {'form': form, 'user_id': user_id})

@login_required
def additional_upload_form(request, n):
    form = SingleFileUploadForm(n)
    return HttpResponse(form.as_ul())


@login_required
def help(request):
    return render(request, 'app/help.html')

@login_required
def delete_file(request):
    if request.method != 'POST':
        raise Http404
    files = get_list_or_404(File, pk__in=request.POST.getlist('ids'))
    owner = files[0].user
    for file in files:
        if file.owned_by(request.user):
            file.delete()
    return HttpResponse(simplejson.dumps([owner.id,
                                          owner.file_set.count(),
                                          filesizeformat(total_size(owner))]))

@login_required
def view_thumbnail(request, id):
    file = get_object_or_404(File, pk=id)
    _, extension = os.path.splitext(file.file.path)

    if extension in settings.THUMBNAIL_SUPPORTED:
        is_supported = 'true'
    else:
        is_supported = 'false'
    if extension in settings.THUMBNAIL_ARCHIVES:
        is_archive = 'true'
    else:
        is_archive = 'false'

    return render(request, 'app/view_thumbnail.json', {
        'file': file, 
        'is_supported': is_supported,
        'is_archive': is_archive,
        })


@superuser_required
def send_instructions(request, id):
    user = get_object_or_404(User, pk=id)
    if user.is_superuser:
        raise Http404
    if request.method == 'POST':
        form = InstructionsForm(request.POST)
        if form.is_valid():
            form.send(user.username, 
                      RawPassword.objects.get(user=user).password)
            return HttpResponseRedirect(reverse('file_list'))
    else:
        form = InstructionsForm()
    return render(request, 'app/send_instructions.html',
                  {'form': form})

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

    user_list = []
    for user in User.objects.all():
        user_list.append((user,
                          RawPassword.objects.get(user=user),
                          user.file_set.count(),
                          total_size(user)))
    
    return render(request, 'app/manage_users.html',
                  {'user_list': user_list,
                   'form': form,
                   'chart_url': get_stats()
                  })

def get_stats(threshold=5):
    userlist = [(user.username, total_size(user))
                for user in User.objects.all()]
    userlist.sort(key=operator.itemgetter(1), reverse=True)

    labels = []
    sizes = []
    others = 0
    for (i, (username, size)) in enumerate(userlist):
        if i < threshold:
            labels.append(username)
            sizes.append(size)
        else:
            others += size
    if len(labels) == threshold:
        labels.append('Autres')
        sizes.append(others)

    total = float(sum(sizes) or 1)
    values = [str(size / total * 100) for size in sizes]
    return 'http://chart.apis.google.com/chart?cht=p3&chd=t:%s&chs=340x100&chl=%s' \
            % (','.join(values), '|'.join(labels))

@superuser_required
def set_password(request, id):
    user = get_object_or_404(User, pk=id)
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
    user = get_object_or_404(User, pk=id)
    if user.is_superuser:
        raise Http404

    if request.method == 'POST':
        user.delete()
        return HttpResponseRedirect(reverse('manage_users'))
    else:
        return render(request, 'app/delete_user.html',
                      {'show_form': True,
                       'this_user': user,
                      })

