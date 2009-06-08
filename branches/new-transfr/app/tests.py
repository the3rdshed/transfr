from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import Http404
from django.test import TestCase
from django.test.client import Client

from transfr.app.models import File, RawPassword
from transfr.app.forms import SingleFileUploadForm, MultipleFileUploadForm
from transfr.app import utils

import datetime
import os
import shutil
import urllib


settings.DEBUG = True

TEST_MEDIA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'fixtures', 'media')
File._meta.fields[1].storage.location = TEST_MEDIA_ROOT

# TestFile {{{1
class TestFile(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.f = File.objects.get(pk=1)

    def test_model(self):
        self.assertEquals(unicode(self.f), u'hello.txt')
        self.assertEquals(self.f.file.name, 'hello.txt')
        self.assertEquals(self.f.comments, 'Hello world')
        self.assertEquals(self.f.modified_date, datetime.datetime(2008, 11, 11, 11, 0, 0))
        self.assertEquals(self.f.user, User.objects.get(pk=2))

    def test_file(self):
        self.assertEquals(self.f.file.size, 14)

    def test_basename(self):
        self.assertEquals(self.f.basename(), 'hello.txt')

    def test_owned_by(self):
        self.assert_(self.f.owned_by(User.objects.get(pk=1)))
        self.assert_(self.f.owned_by(User.objects.get(pk=2)))
        self.assert_(not self.f.owned_by(User.objects.get(pk=3)))

    def test_truncated_name(self):
        self.assertEquals(self.f.truncated_name(), 'hello.txt')
        self.assertEquals(self.f.truncated_name(8), 'he...txt')


# TestSingleFileUploadForm {{{1
class TestSingleFileUploadForm(TestCase):
    def test_init(self):
        f = SingleFileUploadForm(0)
        self.assertEquals(len(f.fields), 2)
        self.assert_('file0' in f.fields)
        self.assert_('comments0' in f.fields)

        f = SingleFileUploadForm(9)
        self.assertEquals(len(f.fields), 2)
        self.assert_('file9' in f.fields)
        self.assert_('comments9' in f.fields)


# TestMultipleFileUploadForm {{{1
class TestMultipleFileUploadForm(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def tearDown(self):
        shutil.rmtree(os.path.join(TEST_MEDIA_ROOT, 'uploads'), True)

    def test_init(self):
        f = MultipleFileUploadForm(self.user)
        self.assertEquals(len(f.fields), 0)
        self.assertEquals(f.user, self.user)
        f = MultipleFileUploadForm(self.user, {}, {'file1': None, 'file3': None})
        self.assertEquals(len(f.fields), 4)
        self.assert_('file1' in f.fields)
        self.assert_('comments1' in f.fields)
        self.assert_('file3' in f.fields)
        self.assert_('comments3' in f.fields)

    def test_save(self):
        post = {'comments0': 'abc', 'comments1': 'def'}
        files = {'file0': SimpleUploadedFile('0.txt', 'text/plain', 'abc'),
                 'file1': SimpleUploadedFile('1.txt', 'text/plain', 'def')}
        f = MultipleFileUploadForm(self.user, post, files)
        self.assert_(f.is_valid())
        f.save()
        self.assertEquals(File.objects.count(), 3)
        file0 = File.objects.get(file__endswith='0.txt')
        file1 = File.objects.get(file__endswith='1.txt')
        self.assertEquals(file0.comments, 'abc')
        self.assertEquals(file1.comments, 'def')

# TestUser {{{1
class TestUser(TestCase):
    # No fixtures
    def test_set_password(self):
        u = User.objects.create_user('test', 'test@test.com', 'test')
        self.assertEquals(RawPassword.objects.count(), 1)
        self.assertEquals(RawPassword.objects.get(user=u).password, 'test')


# TestUrls {{{1
class TestUrls(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.anon = Client()
        self.admin = Client()
        self.admin.login(username='admin', password='admin')
        self.user = Client()
        self.user.login(username='user', password='user')

    def test_users(self):
        self.assertEquals(self.anon.session, {})
        self.assertEquals(self.admin.session['_auth_user_id'], 1)
        self.assertEquals(self.user.session['_auth_user_id'], 2)

    def test_login(self):
        resp = self.anon.get(reverse('login'))
        self.assertEquals(resp.status_code, 200)

        resp = self.user.get(reverse('login'))
        self.assertEquals(resp.status_code, 200)

        resp = self.admin.get(reverse('login'))
        self.assertEquals(resp.status_code, 200)

    def test_logout(self):
        resp = self.anon.get(reverse('logout'))
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp['location'].replace('http://testserver', ''),
                          reverse('disconnected'))

        resp = self.user.get(reverse('logout'))
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp['location'].replace('http://testserver', ''),
                          reverse('disconnected'))

        resp = self.admin.get(reverse('logout'))
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(resp['location'].replace('http://testserver', ''),
                          reverse('disconnected'))

    def test_disconnected(self):
        resp = self.anon.get(reverse('disconnected'))
        self.assertEquals(resp.status_code, 200)

        resp = self.user.get(reverse('disconnected'))
        self.assertEquals(resp.status_code, 200)

        resp = self.admin.get(reverse('disconnected'))
        self.assertEquals(resp.status_code, 200)

    def test_file_list(self):
        resp = self.anon.get(reverse('file_list'))
        self.assertEquals(resp.status_code, 302)
        resp = self.anon.get(reverse('file_list_user', args=[1]))
        self.assertEquals(resp.status_code, 302)

        resp = self.user.get(reverse('file_list'))
        self.assertEquals(resp.status_code, 200)
        resp = self.user.get(reverse('file_list_user', args=[2]))
        self.assertEquals(resp.status_code, 200)
        resp = self.user.get(reverse('file_list_user', args=[1]))
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.get(reverse('file_list'))
        self.assertEquals(resp.status_code, 200)
        resp = self.admin.get(reverse('file_list_user', args=[1]))
        self.assertEquals(resp.status_code, 200)
        resp = self.admin.get(reverse('file_list_user', args=[2]))
        self.assertEquals(resp.status_code, 200)

    def test_manage_users(self):
        resp = self.anon.get(reverse('manage_users'))
        self.assertEquals(resp.status_code, 404)

        resp = self.user.get(reverse('manage_users'))
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.get(reverse('manage_users'))
        self.assertEquals(resp.status_code, 200)

    def test_set_password(self):
        resp = self.anon.get(reverse('set_password', args=[1]))
        self.assertEquals(resp.status_code, 404)

        resp = self.user.get(reverse('set_password', args=[1]))
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.get(reverse('set_password', args=[1]))
        self.assertEquals(resp.status_code, 404)
        resp = self.admin.get(reverse('set_password', args=[2]))
        self.assertEquals(resp.status_code, 200)
        resp = self.admin.get(reverse('set_password', args=[100]))
        self.assertEquals(resp.status_code, 404)

    def test_delete_user(self):
        resp = self.anon.get(reverse('delete_user', args=[1]))
        self.assertEquals(resp.status_code, 404)

        resp = self.user.get(reverse('delete_user', args=[1]))
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.get(reverse('delete_user', args=[2]))
        self.assertEquals(resp.status_code, 200)
        resp = self.admin.get(reverse('delete_user', args=[1]))
        self.assertEquals(resp.status_code, 404)
        resp = self.admin.get(reverse('delete_user', args=[100]))
        self.assertEquals(resp.status_code, 404)


    def test_add_file(self):
        resp = self.anon.get(reverse('add_file', args=[1]))
        self.assertEquals(resp.status_code, 302)

        resp = self.user.get(reverse('add_file', args=[1]))
        self.assertEquals(resp.status_code, 404)
        resp = self.user.get(reverse('add_file', args=[2]))
        self.assertEquals(resp.status_code, 200)
        resp = self.user.get(reverse('add_file', args=[3]))
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.get(reverse('add_file', args=[1]))
        self.assertEquals(resp.status_code, 200)
        resp = self.admin.get(reverse('add_file', args=[2]))
        self.assertEquals(resp.status_code, 200)
        resp = self.admin.get(reverse('add_file', args=[3]))
        self.assertEquals(resp.status_code, 200)
        resp = self.admin.get(reverse('add_file', args=[100]))
        self.assertEquals(resp.status_code, 404)

    def test_delete_file(self):
        resp = self.anon.get(reverse('delete_file'))
        self.assertEquals(resp.status_code, 302)

        resp = self.user.get(reverse('delete_file'))
        self.assertEquals(resp.status_code, 404)
        resp = self.user.post(reverse('delete_file'), {'id': 100})
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.get(reverse('delete_file'))
        self.assertEquals(resp.status_code, 404)
        resp = self.admin.post(reverse('delete_file'), {'id': 100})
        self.assertEquals(resp.status_code, 404)

        c = Client()
        c.login(username='user2', password='user')
        resp = c.post(reverse('delete_file'), {'id': 1})
        self.assertEquals(resp.status_code, 404)

    def test_instruction(self):
        resp = self.anon.get(reverse('instructions', args=[2]))
        self.assertEquals(resp.status_code, 404)

        resp = self.user.get(reverse('instructions', args=[2]))
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.get(reverse('instructions', args=[1]))
        self.assertEquals(resp.status_code, 404)
        resp = self.admin.get(reverse('instructions', args=[2]))
        self.assertEquals(resp.status_code, 200)



# TestViews {{{1
class TestViews(TestCase):
    fixtures = ['test_data']

    def setUp(self):
        self.anon = Client()
        self.admin = Client()
        self.admin.login(username='admin', password='admin')
        self.user = Client()
        self.user.login(username='user', password='user')

    def tearDown(self):
        shutil.rmtree(os.path.join(TEST_MEDIA_ROOT, 'uploads'), True)

    def test_mylogin(self): # {{{2
        resp = self.anon.post(reverse('login'), {})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context[0]['request'].META['PATH_INFO'],
                          urllib.unquote(reverse('login')))

        resp = self.anon.post(reverse('login'), {'username': 'user'})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context[0]['request'].META['PATH_INFO'],
                          urllib.unquote(reverse('login')))

        resp = self.anon.post(reverse('login'), {'password': 'user'})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context[0]['request'].META['PATH_INFO'],
                          urllib.unquote(reverse('login')))

        resp = self.anon.post(reverse('login'), {'username': 'foo', 'password': 'user'})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context[0]['request'].META['PATH_INFO'],
                          urllib.unquote(reverse('login')))

        resp = self.anon.post(reverse('login'), {'username': 'user', 'password': 'foo'})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.context[0]['request'].META['PATH_INFO'],
                          urllib.unquote(reverse('login')))

        resp = self.anon.post(reverse('login'), {'username': 'user', 'password': 'user'})
        self.assertEquals(resp.status_code, 302)

    def test_mylogout(self): # {{{2
        self.assert_(self.user.session.items())
        self.assert_(self.admin.session.items())
        
        self.user.get(reverse('logout'))
        self.admin.get(reverse('logout'))

        self.assert_(not self.user.session.items())
        self.assert_(not self.admin.session.items())
        

    def test_file_list(self): # {{{2
        resp = self.user.get(reverse('file_list'))
        self.assertEquals(resp.context[0]['user_list'].count(), 3)

        resp = self.admin.get(reverse('file_list'))
        self.assertEquals(resp.context[0]['user_list'].count(), 3)
        self.assertEquals(resp.context[0]['user_list'][0], User.objects.get(username='admin'))
        self.assertEquals(resp.context[0]['user_list'][1], User.objects.get(username='user'))
        self.assertEquals(resp.context[0]['user_list'][2], User.objects.get(username='user2'))

    def test_add_file(self): # {{{2
        resp = self.user.post(reverse('add_file', args=[2]), {})
        self.assertEquals(resp.status_code, 302)

        resp = self.user.post(reverse('add_file', args=[1]), {})
        self.assertEquals(resp.status_code, 404)

        # User adds his own file
        resp = self.user.post(reverse('add_file', args=[2]),
                              {'user0': 2,
                               'file0': SimpleUploadedFile('user.txt', 'text/plain', 'user')})
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(File.objects.count(), 2)

        resp = self.admin.post(reverse('add_file', args=[2]),
                               {'user0': 2,
                                'file0': SimpleUploadedFile('admin.txt', 'text/plain', 'admin')})
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(File.objects.count(), 3)
        self.assertEquals(File.objects.get(pk=3).user.username, 'user')

    def test_delete_file(self): # {{{2
        # Create dummy file
        self.user.post(reverse('add_file', args=[2]),
                       {'user0': 2,
                        'file0': SimpleUploadedFile('user.txt', 'text/plain', 'user')})
        self.assertEquals(File.objects.count(), 2)
        resp = self.user.post(reverse('delete_file'), {'ids': 2})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(File.objects.count(), 1)

    def test_manage_users(self): # {{{2
        resp = self.admin.get(reverse('manage_users'))
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(len(resp.context[0]['user_list']), 2)

    def test_add_user(self): # {{{2
        self.assertEquals(User.objects.count(), 3)
        self.assertEquals(RawPassword.objects.count(), 3)
        resp = self.admin.post(reverse('manage_users'),
                               {'username': 'foo',
                                'password1': 'foo',
                                'password2': 'foo'})
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(User.objects.count(), 4)
        self.assertEquals(RawPassword.objects.count(), 4)
        self.assertEquals(RawPassword.objects.get(user__username='foo').password, 'foo')
        
    def test_set_password(self): # {{{2
        resp = self.admin.post(reverse('set_password', args=[3]), {})
        self.assertEquals(resp.status_code, 200)

        resp = self.admin.post(reverse('set_password', args=[3]),
                               {'new_password1': 'bar',
                                'new_password2': 'bar'})
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(RawPassword.objects.get(user__username='user2').password, 'bar')

    def test_delete_user(self): # {{{2
        resp = self.admin.post(reverse('delete_user', args=[1]))
        self.assertEquals(resp.status_code, 404)

        resp = self.admin.post(reverse('delete_user', args=[3]))
        self.assertEquals(resp.status_code, 302)
        self.assertEquals(User.objects.count(), 2)
        self.assertEquals(RawPassword.objects.count(), 2)


# TestUtils {{{1
class TestUtils(TestCase):
    fixtures = ['test_data']

    def test_get_normal_user(self):
        self.assertEquals(User.objects.get(pk=2), utils.get_normal_user(2))
        self.assertRaises(Http404, lambda: utils.get_normal_user(1))
