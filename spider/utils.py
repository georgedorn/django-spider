import httplib2
import lxml.html
import Queue
import re
import socket
import threading
import time

from django.conf import settings

from spider.exceptions import UnfetchableURLException, OffsiteLinkException

from djutils.decorators import memoize

STORE_CONTENT = getattr(settings, 'SPIDER_STORE_CONTENT', True)

domain_re = re.compile('(([a-z]+://)[^/\?]+)*')
subdomain_re = re.compile('([a-z]+://)(.*?\.)+([^\/\?]+\.[^\/\?\.]+([\/\?].*)?)')

def get_domain(url):
    match = re.search(domain_re, url)
    if match:
        return match.group()
    return ''

def get_host(url):
    domain = get_domain(url)
    if domain:
        return domain.split('://')[1]
    return ''

def relative_to_full(example_url, url):
    """
    Given a url which may or may not be a relative url, convert it to a full
    url path given another full url as an example
    """
    # remove any hashes
    url = re.sub('(#[^\/]+)', '', url)
    
    # does this url specify a protocol?  if so, it's already a full url
    if re.match('[a-z]+:\/\/', url):
        return url
    
    # if the url doesn't start with a slash it's probably relative to the
    # current url, so join them and return
    if not url.startswith('/'):
        # check to see if there is a slash after the protocol -- we'll use the
        # slash to determine the current working directory for this relative url
        if re.match('^[a-z]+:\/\/(.+?)\/', example_url):
            return '/'.join((example_url.rpartition('/')[0], url))
    
    # it starts with a slash, so join it with the domain if possible
    domain = get_domain(example_url)
    
    if domain:
        return '/'.join((domain, url.lstrip('/')))
    
    return url

def get_urls(content):
    # retrieve all link hrefs from html
    parsed = lxml.html.fromstring(content)
    return parsed.xpath('//a/@href')

def strip_subdomain(url):
    match = subdomain_re.search(url)
    if match:
        return subdomain_re.sub('\\1\\3', url)
    return url

@memoize
def is_on_site(source_url, url):
    source_domain = get_domain(source_url)
    if not source_domain:
        raise ValueError('%s must contain "protocol://host"' % source_url)
    
    if url.startswith('/'):
        return True
    
    if '://' not in url:
        if url.startswith('mailto') or url.startswith('javascript'):
            return False
        return True
    
    domain = get_domain(url)
    if domain and domain == source_domain:
        return True
    
    # try stripping out any subdomains
    if domain and strip_subdomain(domain) == strip_subdomain(source_domain):
        return True
    
    return False

def filter_urls(source, urls):
    return [
        relative_to_full(source, url) \
            for url in urls \
                if is_on_site(source, url)
    ]

def fetch_url(url, timeout):
    sock = httplib2.Http(timeout=timeout)
    return sock.request(url)

def crawl(source_url, url, timeout):
    try:
        headers, content = fetch_url(url, timeout)
    except socket.error:
        raise UnfetchableURLException
    
    if headers['status'] == '200':
        if is_on_site(source_url, headers['content-location']):
            urls = get_urls(content)
            return headers, content, filter_urls(url, urls)
        else:
            raise OffsiteLinkException
    
    return headers, content, []

def ascii_hammer(content):
    return ''.join([c for c in content if ord(c) < 128])


class SpiderThread(threading.Thread):
    def __init__(self, url_queue, response_queue, finish_event, session):
        threading.Thread.__init__(self)

        self.url_queue = url_queue
        self.response_queue = response_queue
        self.finish_event = finish_event
        
        # load data from the session obj passed in
        self.source_url = session.spider_profile.url
        self.timeout = session.spider_profile.timeout
    
    def run(self):
        while not self.finish_event.is_set():
            self.process_queue()

    def process_queue(self):
        try:
            url, source, depth = self.url_queue.get(timeout=self.timeout)
        except Queue.Empty:
            pass
        else:
            try:
                crawl_start = time.time()
                headers, content, urls = crawl(self.source_url, url, self.timeout)
                response_time = time.time() - crawl_start
            except (UnfetchableURLException, OffsiteLinkException, AttributeError):
                pass
            else:
                content = STORE_CONTENT and ascii_hammer(content) or ''
                results = dict(
                    url=url,
                    source_url=source,
                    content=content,
                    response_status=int(headers['status']),
                    response_time=response_time,
                    content_length=int(headers['content-length']),
                )
                self.response_queue.put((results, urls, depth))
            
            self.url_queue.task_done()
