# -*- coding: utf-8 -*-

from django import forms
from django.shortcuts import loader
from django.template import Context
from django.forms.fields import email_re
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _

from transfr.app.models import File

FIELDS = (
    ('file', forms.FileField(label=_(u'File'), required=True)),
    ('comments', forms.CharField(label=_(u'Comments'), required=False)),
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



class MultipleFileUploadForm(forms.Form):
    '''
    A file upload form with multiple copies of
    each field.
    '''
    def __init__(self, user, xs, *args, **kwargs):
        self.user = user
        self.xs = xs
        self.base_fields = {}
        for x in self.xs:
            for field_name, field in FIELDS:
                self.base_fields['%s%s' % (field_name, x)] = field

        super(MultipleFileUploadForm, self).__init__(*args, **kwargs)

    def save(self):
        for x in self.xs:
            f = File()
            f.user = self.user
            f.comments = self.cleaned_data['comments%s' % x]
            upload = self.cleaned_data['file%s' % x]
            f.file.save(upload.name, upload)
            f.save()


class InstructionsForm(forms.Form):
    subject = forms.CharField(label='Sujet',
                              initial='CDD: Instructions pour transfert de fichiers '
                                      '/ file transfer instructions')
    emails = forms.CharField(label='Courriel(s)',
                             help_text=_(u'<span>Note: to send to multiple recipents, '
                                         u'separate the emails with a comma.</span>'))

    def clean_emails(self):
        emails = [e.strip() for e in self.cleaned_data.get('emails').split(',') if e.strip()]
        if not emails:
            raise forms.ValidationError(_(u'Please enter an email'))
        for email in emails:
            if not email_re.search(email):
                raise forms.ValidationError(_(u'%s: invalid email' % email))
        return emails

    def send(self, username, password):
        tpl = loader.get_template('app/instructions.txt')
        msg = tpl.render(Context({'username': username,
                                  'password': password}))
        send_mail(self.cleaned_data['subject'],
                  msg,
                  "studio@centdessin.com",
                  self.cleaned_data['emails'],
                  True)
