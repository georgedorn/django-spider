import httplib2
import Queue
import re
import socket
import sys
import threading
import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from spider.utils import SpiderThread, fetch_url


class SpiderProfile(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=255, help_text='Full URL, including http://')
    time_limit = models.IntegerField(default=60, help_text='Maximum time to run spiders')
    timeout = models.IntegerField(default=10, help_text='Socket and Queue timeout')
    depth = models.IntegerField(default=2, help_text='How many pages deep to follow links')
    threads = models.IntegerField(default=4, help_text='Number of concurrent spiders')

    class Meta:
        ordering = ('title',)

    def __unicode__(self):
        return '%s [%s]' % (self.title, self.url)
    
    def get_absolute_url(self):
        return reverse('profiles_profile_detail', args=[self.pk])
    
    def spider(self):
        session = SpiderSession.objects.create(spider_profile=self)
        return session.spider()
    
    def check_health(self):
        status_check = ProfileStatusCheck.objects.create(spider_profile=self)
        status_check.check_health()
        return status_check
    
    def latest_status(self):
        try:
            return self.status_checks.all()[0]
        except IndexError:
            pass


class SpiderSession(models.Model):
    spider_profile = models.ForeignKey(SpiderProfile, related_name='sessions')
    created_date = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    
    class Meta:
        ordering = ('-created_date',)
    
    def __unicode__(self):
        return '%s [%s]' % (self.spider_profile.title, self.created_date)
    
    def get_absolute_url(self):
        return reverse('profiles_session_detail', args=[self.spider_profile.pk, self.pk])
    
    def spider(self):
        # these were originally args, but thought i'd move them to the profile
        # model:
        timeout = self.spider_profile.timeout
        time_limit = self.spider_profile.time_limit
        depth = self.spider_profile.depth
        threads = self.spider_profile.threads
        
        # a queue to store a 3-tuple of (url to fetch, source url, depth)
        pending_urls = Queue.Queue()
        
        # store a 3-tuple of (unsaved URLResponse, urls found, depth remaining)
        processed_responses = Queue.Queue()
        
        # event triggered when threads should shut down
        finished = threading.Event()
        
        # store the initial time to track how long spider runs for
        start = time.time()
        
        # response statuses keyed by url
        visited = {}
        
        # track what urls are scheduled to ensure we don't hit things twice
        scheduled = set()

        # create a couple of threads to chew on urls
        threads = [
            SpiderThread(pending_urls, processed_responses, finished, self) \
                for x in range(threads)
        ]
        
        # start with the source url
        pending_urls.put((self.spider_profile.url, '', depth))
        scheduled.add(self.spider_profile.url)

        # start our worker threads
        [t.start() for t in threads]
        
        while 1:
            try:
                # pull an item from the response queue
                result_dict, urls, depth = processed_responses.get(timeout=timeout)
            except Queue.Empty:
                pass
            else:
                # save the result
                url_result = URLResult(**result_dict)
                url_result.session = self
                url_result.save()
                
                processed_url = url_result.url
                
                # remove from the list of scheduled items
                scheduled.remove(processed_url)
                
                # store response status in the visited dictionary
                visited[processed_url] = url_result.response_status
                
                # enqueue any urls that need to be checked
                if depth > 0:
                    for url in urls:
                        if url not in visited and url not in scheduled:
                            scheduled.add(url)
                            pending_urls.put((url, processed_url, depth - 1))
            finally:
                if time.time() - start >= time_limit:
                    # set the finished flag
                    finished.set()

                    # wait for all the threads to finish up
                    [t.join() for t in threads]
                    break

        self.complete = True
        self.save()

        return visited
    
    def results_with_status(self, status):
        return self.results.filter(response_status=status)
    
    def results_404(self):
        return self.results_with_status(404)
    
    def results_500(self):
        return self.results_with_status(500)
    
    def results_200(self):
        return self.results_with_status(200)
    
    def new_this_session(self, status):
        # results with the given status that were not present in the previous
        # session
        
        previous_qs = SpiderSession.objects.filter(
            spider_profile=self.spider_profile,
            created_date__lt=self.created_date
        ).order_by('-created_date')
        
        current_results = self.results_with_status(status)
        
        try:
            last_session = previous_qs[0]
        except IndexError:
            return current_results
        
        previous_results = last_session.results_with_status(status)
        
        return current_results.exclude(url__in=previous_results.values('url'))
    
    def new_404(self):
        return self.new_this_session(404)
    
    def new_500(self):
        return self.new_this_session(500)
    
    def new_200(self):
        return self.new_this_session(200)


class URLResult(models.Model):
    session = models.ForeignKey(SpiderSession, related_name='results')
    url = models.CharField(max_length=255)
    source_url = models.CharField(max_length=255)
    content = models.TextField()
    response_status = models.IntegerField()
    response_time = models.FloatField()
    content_length = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    
    # store any urls extracted from the content during spidering
    urls = []
    
    class Meta:
        ordering = ('-session__pk', 'source_url', 'url',)
    
    def __unicode__(self):
        return '%s [%s]' % (self.url, self.response_status)

    def get_absolute_url(self):
        return reverse('profiles_url_result_detail', args=[
            self.session.spider_profile_id, self.session_id, self.pk
        ])
    
    def previous_results(self):
        return URLResult.objects.filter(
            url=self.url,
            created_date__lt=self.created_date
        ).order_by('-created_date')
    
    def previous_status(self):
        previous_qs = self.previous_results()
        
        try:
            most_recent = previous_qs[0]
        except IndexError:
            return None
        else:
            return most_recent.response_status

    def short_url(self):
        return re.sub('^([a-z]+:\/\/)?([^\/]+)', '', self.url)


class ProfileStatusCheck(models.Model):
    spider_profile = models.ForeignKey(SpiderProfile, related_name='status_checks')
    error_fetching = models.BooleanField(default=False)
    response_status = models.IntegerField(blank=True, null=True)
    response_time = models.FloatField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    exception = models.TextField()
    
    class Meta:
        ordering = ('-created_date',)
    
    def __unicode__(self):
        return '%s [%s]' % (self.spider_profile.url, self.response_status)
    
    def check_health(self):
        try:
            start = time.time()
            headers, resp = fetch_url(
                self.spider_profile.url,
                self.spider_profile.timeout
            )
        except (socket.error, AttributeError, httplib2.ServerNotFoundError):
            self.error_fetching = True
            exception = sys.exc_info()[1]
            self.exception = repr(exception)
        else:
            self.response_status = int(headers['status'])
        
        self.response_time = time.time() - start
        self.save()
    
    def is_ok(self):
        return self.response_status == 200
