from django.conf.urls.defaults import *


urlpatterns = patterns('spider.views',
    url(r'^$',
        'profile_list',
        name='profiles_profile_list'
    ),
    url(r'^(?P<profile_id>\d+)/$',
        'profile_detail',
        name='profiles_profile_detail'
    ),
    url(r'^(?P<profile_id>\d+)/new/$',
        'session_create',
        name='profiles_session_create'
    ),
    url(r'^(?P<profile_id>\d+)/(?P<session_id>\d+)/$',
        'session_detail',
        name='profiles_session_detail'
    ),
    url(r'^(?P<profile_id>\d+)/(?P<session_id>\d+)/(?P<url_result_id>\d+)/$',
        'url_result_detail',
        name='profiles_url_result_detail'
    ),
)
