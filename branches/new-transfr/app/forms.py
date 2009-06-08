# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.forms.fields import email_re
from django.shortcuts import loader
from django.template import Context
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from transfr.app.models import File
import re

FIELDS = (
    ('file', forms.FileField(label=_(u'File'), required=True)),
    ('comments', forms.CharField(label=_(u'Comments'),
                                 required=False,
                                 widget=forms.TextInput(attrs={'class': 'comment'}))),
)


class SingleFileUploadForm(forms.Form):
    '''
    A file upload form where all fields have a number
    appended to them (e.g.: file3) to distinguish between
    different files.
    '''
    def __init__(self, n, *args, **kwargs):
        super(SingleFileUploadForm, self).__init__(*args, **kwargs)
        for field_name, field in FIELDS:
            self.fields['%s%s' % (field_name, n)] = field
    
    def as_ul(self):
        output = [u'<ul class="file-upload">']
        output.append(super(SingleFileUploadForm, self).as_ul())
        output.append(u'</ul>')
        output.append(u'<div class="clear"></div>')
        return mark_safe(u'\n'.join(output))


class MultipleFileUploadForm(forms.Form):
    '''
    A file upload form with multiple copies of
    each field.
    '''
    def __init__(self, user, *args, **kwargs):
        self.user = user
        # Get the ids where a file was specified; the files are
        # the second element of args.
        if args:
            self.ids = list(self.get_field_ids(args[1]))
        else:
            self.ids = []
        self.base_fields = {}
        for id in self.ids:
            for field_name, field in FIELDS:
                self.base_fields['%s%s' % (field_name, id)] = field

        super(MultipleFileUploadForm, self).__init__(*args, **kwargs)

    def get_field_ids(self, files):
        id_re = re.compile(r'(\d+)$')
        for filename in files:
            m = id_re.search(filename)
            if m:
                yield m.group(1)

    def save(self):
        for id in self.ids:
            f = File.objects.create(
                user=self.user,
                comments=self.cleaned_data['comments%s' % id])
            upload = self.cleaned_data['file%s' % id]
            f.file.save(upload.name, upload)
            f.save()
