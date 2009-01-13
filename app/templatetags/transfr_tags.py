from django import template
from django.conf import settings

from transfr.app import utils
from transfr.utils import join_url

import os

register = template.Library()

@register.filter
def total_size(user):
    return utils.total_size(user)

@register.simple_tag
def icon(name):
    return '<img src="%s" alt="" border="0">&nbsp;' \
            % join_url(settings.MEDIA_URL, 'icons', settings.ICONS,
                       name + '.png')


@register.simple_tag
def button(name, href="#", title="", className=""):
    return '<a class="ui-default-state %s" href="%s">%s' % (className, href, icon(name))

@register.simple_tag
def endbutton():
    return '</a>'
