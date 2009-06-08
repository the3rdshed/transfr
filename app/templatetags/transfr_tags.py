from django import template
from django.conf import settings

from transfr.app import utils
from transfr.utils import join_url

import os

register = template.Library()

@register.filter
def total_user_size(user):
    return utils.total_user_size(user)

@register.simple_tag
def icon(name):
    return '<img src="%s" align="absmiddle" alt="" border="0" width="16" height="16">&nbsp;' \
            % join_url(settings.MEDIA_URL, 'icons', 'silk', name + '.png')


@register.simple_tag
def button(name, href="#", class_name=""):
    return '<a class="button %s" href="%s">%s' % (class_name, href, icon(name))

@register.simple_tag
def endbutton():
    return '</a>'

@register.inclusion_tag('app/_percentage.html')
def size_percentage(size, total_size):
    return {'size': size,
            'total_size': total_size,
           }
