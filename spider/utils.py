import httplib2
import re
import socket
from BeautifulSoup import BeautifulSoup

from spider.exceptions import UnfetchableURLException, OffsiteLinkException

from djutils.decorators import memoize


domain_re = re.compile('(([a-z]+://)[^/\?]+)*')
subdomain_re = re.compile('([a-z]+://)(.*?\.)+([^\/\?]+\.[^\/\?\.]+([\/\?].*)?)')

def get_domain(url):
    match = re.search(domain_re, url)
    if match:
        return match.group()
    return ''

def relative_to_full(example_url, url):
    """
    Given a url which may or may not be a relative url, convert it to a full
    url path given another full url as an example
    """
    # remove any hashes
    url = re.sub('(#[^\/]+)', '', url)
    
    if re.match('[a-z]+:\/\/', url):
        return url
    
    domain = get_domain(example_url)
    
    if domain:
        return '/'.join((domain, url.lstrip('/')))
    
    return url

def get_urls(content):
    # retrieve all link hrefs from html and encoding be damned
    try:
        soup = BeautifulSoup(content)
    except UnicodeEncodeError:
        return []
    
    return [a['href'] for a in soup.findAll('a')]

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

def fetch_url(sock, url):
    return sock.request(url)

def crawl(source_url, url, timeout):
    sock = httplib2.Http(timeout=timeout)
    
    try:
        headers, content = fetch_url(sock, url)
    except socket.error:
        raise UnfetchableURLException
    
    if headers['status'] == '200':
        if is_on_site(source_url, headers['content-location']):
            urls = get_urls(content)
            return headers, content, filter_urls(source_url, urls)
        else:
            raise OffsiteLinkException
    
    return headers, content, []

def ascii_hammer(content):
    return ''.join([c for c in content if ord(c) < 128])
