from djutils.test import TestCase

from spider.utils import (get_domain, get_host, relative_to_full, get_urls,
    is_on_site, filter_urls, ascii_hammer, strip_subdomain)


class SpiderUtilsTestCase(TestCase):
    def test_get_domain(self):
        test_data = (
            ('http://www.reddit.com', 'http://www.reddit.com'),
            ('http://www.reddit.com/', 'http://www.reddit.com'),
            ('http://www.reddit.com/r/django', 'http://www.reddit.com'),
            ('http://reddit.com', 'http://reddit.com'),
            ('http://reddit.com/', 'http://reddit.com'),
            ('http://reddit.com/r/django', 'http://reddit.com'),
            ('www.reddit.com', ''),
            ('www.reddit.com/', ''),
            ('www.reddit.com/r/django', ''),
            ('reddit.com', ''),
            ('reddit.com/', ''),
            ('reddit.com/r/django/', ''),
        )
        
        for given, expected in test_data:
            self.assertEqual(get_domain(given), expected)
    
    def test_get_host(self):
        test_data = (
            ('http://www.reddit.com/', 'www.reddit.com'),
            ('http://reddit.com', 'reddit.com'),
            ('http://m.www.reddit.com', 'm.www.reddit.com'),
            ('http://www.reddit.com/r/django/', 'www.reddit.com'),
            ('www.reddit.com', ''),
            ('reddit.com', ''),
        )
        
        for given, expected in test_data:
            self.assertEqual(get_host(given), expected)
    
    def test_relative_to_full(self):
        test_data = (
            # test passing in a domain + a full path
            (('http://test.com', '/a/b/'), 'http://test.com/a/b/'),
            
            # test passing in a deep url + a full path
            (('http://test.com/c/d/?cruft', '/a/b/'), 'http://test.com/a/b/'),
            
            # test passing in a domain + a full url
            (('http://test.com', 'http://test.com/a/b/'), 'http://test.com/a/b/'),
            
            # test passing in a domain + a link to another site
            (('http://test.com', 'http://blah.com/a/b/'), 'http://blah.com/a/b/'),
            
            # test when the link is relative to the current page
            (('http://test.com', 'index.htm'), 'http://test.com/index.htm'),
            (('http://test.com/blog/', 'index.htm'), 'http://test.com/blog/index.htm'),
            
            # test passing in a relative link that only has a querystring
            (('http://test.com/blog/', '?page=4'), 'http://test.com/blog/?page=4'),
            (('http://test.com/blog/?page=2', '?page=3'), 'http://test.com/blog/?page=3'),
            
            # test when no domain is present
            (('', '/a/b/'), '/a/b/'),
            (('example.com', '/a/b/'), '/a/b/'),
            (('example.com/', '/a/b/'), '/a/b/'),
            (('example.com/', 'a/b/'), 'a/b/'),
        )
        for (example, url), expected in test_data:
            self.assertEqual(relative_to_full(example, url), expected)
    
    def test_get_urls(self):
        html = """<html><head></head><body><a href="/blog/">Awesome blog</a> <a href="http://www.google.com/">Google</a></body></html>"""
        
        self.assertEqual(get_urls(html), [
            '/blog/',
            'http://www.google.com/'
        ])
    
    def test_is_on_site(self):
        test_data = (
            # source url, given url
            ('http://reddit.com', 'http://reddit.com', True),
            ('http://reddit.com/', 'http://reddit.com', True),
            ('http://reddit.com', 'http://reddit.com/', True),
            ('http://reddit.com', 'http://reddit.com/r/django/', True),
            ('http://reddit.com', 'http://reddit.com?x=3', True),
            ('http://reddit.com', '/', True),
            ('http://reddit.com', '/r/django', True),
            ('http://reddit.com', '', True),
            ('http://reddit.com', '?page=2', True),
            ('http://reddit.com', 'http://www.reddit.com/', True),
            ('http://www.reddit.com/', 'http://reddit.com', True),
            ('http://www.reddit.com/r/django/', 'http://reddit.com/r/python/', True),
            ('http://m.www.reddit.com/r/django/', 'http://reddit.com/r/python/', True),
            
            ('http://reddit.com', 'http://www.google.com', False),
            ('http://reddit.com/r/django', 'http://www.google.com/', False),
        )
        
        for source, given, expected in test_data:
            self.assertEqual(is_on_site(source, given), expected)
    
    def test_filter_urls(self):
        urls = [
            'http://m.reddit.com/',
            'http://www.reddit.com/',
            'http://www.reddit.com/r/django/',
            '/r/django/',
            'http://www.google.com/',
            'http://some-link.com/asdf/reddit/',
        ]
        filtered = [
            'http://m.reddit.com/',
            'http://www.reddit.com/',
            'http://www.reddit.com/r/django/',
            'http://reddit.com/r/django/',
        ]
        domains = [
            'http://reddit.com/r/django/',
            'http://reddit.com/',
            'http://reddit.com',
        ]
        for domain in domains:
            self.assertEqual(filter_urls(domain, urls), filtered)
        
        filtered = [
            'http://m.reddit.com/',
            'http://www.reddit.com/',
            'http://www.reddit.com/r/django/',
            'http://www.reddit.com/r/django/',
        ]
        domains = [
            'http://www.reddit.com/r/django/',
            'http://www.reddit.com/',
            'http://www.reddit.com',
        ]
        for domain in domains:
            self.assertEqual(filter_urls(domain, urls), filtered)
        
        filtered = [
            'http://m.reddit.com/',
            'http://www.reddit.com/',
            'http://www.reddit.com/r/django/',
            'http://m.www.reddit.com/r/django/',
        ]
        domains = [
            'http://m.www.reddit.com/r/django/',
        ]
        for domain in domains:
            self.assertEqual(filter_urls(domain, urls), filtered)
        
        urls = ['?page=2']
        test_data = (
            ('http://m.reddit.com', ['http://m.reddit.com/?page=2']),
            ('http://m.reddit.com/r/django/?page=2', ['http://m.reddit.com/r/django/?page=2']),
            ('http://reddit.com/r/django/?page=2', ['http://reddit.com/r/django/?page=2']),
            ('http://reddit.com/?page=2', ['http://reddit.com/?page=2']),
        )
        for (source, expected) in test_data:
            self.assertEqual(filter_urls(source, urls), expected)
    
    def test_ascii_hammer(self):
        test_data = (
            ('abcdefghijklmnopqrstuvwxyz0123456789', 'abcdefghijklmnopqrstuvwxyz0123456789'),
            ('<html><body><h1>It works!!!</h1></body></html>', '<html><body><h1>It works!!!</h1></body></html>'),
            ('Snowman! \xe2', 'Snowman! '),
            ('Furren \xd0 \xd5 \xd9', 'Furren   '),
        )
        
        for given, expected in test_data:
            self.assertEqual(ascii_hammer(given), expected)

    def test_strip_subdomain(self):
        test_data = (
            ('http://reddit.com/r/django/', 'http://reddit.com/r/django/'),
            ('http://reddit.com/', 'http://reddit.com/'),
            ('http://reddit.com', 'http://reddit.com'),
            ('http://www.reddit.com/', 'http://reddit.com/'),
            ('http://www.reddit.com', 'http://reddit.com'),
            ('http://m.www.reddit.com/', 'http://reddit.com/'),
            ('http://m.www.reddit.com', 'http://reddit.com'),
            ('http://www.reddit.com/r/django/', 'http://reddit.com/r/django/'),
            ('http://m.www.reddit.com/r/django/', 'http://reddit.com/r/django/'),
            ('/r/django/', '/r/django/'),
        )
        
        for url, expected in test_data:
            self.assertEqual(strip_subdomain(url), expected)
