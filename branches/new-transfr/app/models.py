from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

import os

class File(models.Model):
    file = models.FileField(_(u'File'), upload_to='uploads/%Y/%m')
    comments = models.TextField(_(u'Comments'), blank=True)
    modified_date = models.DateTimeField(_(u'Modification date'), auto_now=True)
    user = models.ForeignKey(User)

    class Meta:
        ordering = ['-modified_date']

    def __unicode__(self):
        return self.file.name

    def basename(self):
        return os.path.basename(self.file.name)

    def owned_by(self, user):
        return user.is_superuser or user == self.user

    def truncated_name(self, n=50):
        basename = self.basename()
        if len(basename) < n:
            return basename
        else:
            return basename[:n-6] + '...' + basename[-3:]

    def safesize(self):
        try:
            return self.file.size
        except (OSError, IOError):
            return 0

class RawPassword(models.Model):
    user = models.ForeignKey(User, related_name='password_user')
    password = models.CharField(_(u'Password'), max_length=100)

    def __repr__(self):
        return '<RawPassword: %s>' % self.user


# We monkey-patch (yuck) User.set_password with our
# own version which also saves the raw password in
# the RawPassword table.
def set_password(user, raw_password):
    if user.id is None:
        user.save()
    user.set_password_orig(raw_password)

    try:
        rp = RawPassword.objects.get(user=user)
        rp.password = raw_password
        rp.save()
    except RawPassword.DoesNotExist:
        RawPassword.objects.create(user=user,
                                   password=raw_password)

User.set_password_orig = User.set_password
User.set_password = set_password
