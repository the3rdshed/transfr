from django.conf.urls.defaults import *
from django.conf import settings
import os

urlpatterns = patterns('transfr.app.views',
    url(r'^accounts/login/$', 'mylogin', name='login'),
    url(r'^accounts/logout/$', 'mylogout', name='logout'),
    url(r'^disconnected/$', 'disconnected', name='disconnected'),
    url(r'^$', 'file_list', name='file_list'),
    url(r'^add/(\d+)/$', 'add_file', name='add_file'),
    url(r'^additional-form/(\d+)/$', 'additional_upload_form', name='additional_upload_form'),
    url(r'^delete/$', 'delete_file', name='delete_file'),
    url(r'^instructions/(\d+)/$', 'send_instructions', name='send_instructions'),
    url(r'^help/$', 'help', name='help'),
    url(r'^users/$', 'manage_users', name='manage_users'),
    url(r'^users/password/(\d+)/$', 'set_password', name='set_password'),
    url(r'^users/delete/(\d+)/$', 'delete_user', name='delete_user'),
    url(r'^upload/progress/$', 'upload_progress', name='upload_progress'),
    url(r'^thumbnail/(?P<id>\d+)/$', 'view_thumbnail', name='view_thumbnail'),
)

urlpatterns += patterns(
    '',
    url(r'^media-app/(.*)$', 'django.views.static.serve', 
        {'document_root': os.path.join(settings.PROJECT_PATH, 'app', 'media')},
        name='media_app'),

)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}, name="media"),
        url(r'^media-app/(.*)$', 'django.views.static.serve', 
            {'document_root': os.path.join(settings.PROJECT_PATH, 'app', 'media')},
            name='media_app'),

    )


if settings.USE_I18N:
    js_info_dict = {
        'packages': ('transfr.app',),
    }
    urlpatterns += patterns(
        '',
        (r'^i18n/', include('django.conf.urls.i18n')),
        url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, name="jsi18n"),
        #(r'^jsi18n/(?P<packages>\S+?)/$', 'django.views.i18n.javascript_catalog'),
    )
