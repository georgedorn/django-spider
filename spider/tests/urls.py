from django.conf.urls.defaults import *
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError


def wrap_headers(func):
    def inner(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        response._headers['status'] = str(response.status_code)
        response._headers['content-length'] = len(response.content)
        response._headers['content-location'] = 'http://testserver%s' % request.path
        return response
    return inner

@wrap_headers
def test_view(request, path):
    links = ['/' + path + '1/', '2/', '?page=3', 'http://not-here.com/4/']
    a_tags = '\n'.join([
        '<a href="%(url)s">%(url)s</a>' % {'url': url} \
            for url in links
    ])
    return HttpResponse('%s\n%s' % (path, a_tags))

@wrap_headers
def test_view_404(request):
    return HttpResponseNotFound(request.path)

@wrap_headers
def test_view_500(request):
    return HttpResponseServerError(request.path)


urlpatterns = patterns('',
    url(r'^404/$', test_view_404),
    url(r'^500/$', test_view_500),
    url(r'(?P<path>.*)', test_view),
)
