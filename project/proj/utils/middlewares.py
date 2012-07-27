# -*- coding:utf-8 -*-
__author__ = 'michael'


from django.conf import settings
from django.http import HttpResponsePermanentRedirect, get_host, HttpResponseRedirect
import os

SSL = 'SSL'

def is_secure(request):
    if 'HTTP_X_FORWARDED_SSL' in request.META:
        return request.META['HTTP_X_FORWARDED_SSL'] == 'on'
    return False

class SSLRedirect:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if SSL in view_kwargs:
            secure = view_kwargs[SSL]
            del view_kwargs[SSL]
        else:
            secure = False

        if not secure == is_secure(request):
            return self._redirect(request, secure)

    def _redirect(self, request, secure):
        protocol = secure and "https" or "http"
        newurl = "%s://%s%s" % (protocol,get_host(request),request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError,\
            """Django can't perform a SSL redirect while maintaining POST data.
  Please structure your views so that redirects only occur during GETs."""

        return HttpResponsePermanentRedirect(newurl) #I have not had time to test this, but it appears to work better.



class HttpsRedirect(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        system_secure = request.META.get('SYSTEM_S', None)
        if not system_secure:
            newurl = u'https://%s%s' % (get_host(request),request.get_full_path())
            return HttpResponseRedirect(newurl)
        else:
            del(request.META['SYSTEM_S'])

