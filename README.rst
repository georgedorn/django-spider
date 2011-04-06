=============
django-spider
=============

a multi-threaded spider with a web interface

.. image:: http://charlesleifer.com/media/images/photos/grass-spider.png

list of sessions for a site
---------------------------

.. image:: http://charlesleifer.com/media/images/photos/spider_session.png


session detail
--------------

.. image:: http://charlesleifer.com/media/images/photos/spider_detail.png


dependencies:
-------------

* `httplib2 <http://code.google.com/p/httplib2/>`_
* `lxml <http://lxml.de/lxmlhtml.html#parsing-html>`_
* `django-utils <http://github.com/coleifer/django-utils>`_


running
-------

first, make sure you pip install the requirements::

    pip install httplib2
    pip install lxml
    pip install -e git+https://github.com/coleifer/django-utils.git#egg=djutils
    pip install -e git+https://github.com/coleifer/django-spider.git#egg=spider

add ``djutils`` and ``spider`` to your settings file and make sure you run
``manage.py syncdb``.

add ``spider.urls`` to your root urlconf::

    from django.conf import settings
    from django.conf.urls.defaults import *
    from django.contrib import admin

    admin.autodiscover()

    urlpatterns = patterns('',
        url(r'^admin/', include(admin.site.urls)),
        url(r'', include('spider.urls')),
    )

make sure the media in the spider app is copied into your static media directory.

start up the `task queue <http://charlesleifer.com/docs/djutils/django-utils/queue.html>`_::

    # assume your cwd is the root dir of virtualenv
    export DJANGO_SETTINGS_MODULE=mysite.settings
    ./bin/python ./src/djutils/djutils/queue/bin/consumer.py start -l ./logs/queue.log -p ./run/queue.pid
