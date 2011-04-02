from djutils.test import TestCase

from spider.utils import (get_domain, relative_to_full, get_urls, is_on_site, 
    filter_urls, ascii_hammer, strip_subdomain)


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
    
    def test_relative_to_full(self):
        self.assertEqual('http://test.com/a/b/', relative_to_full('http://test.com', '/a/b/'))
        self.assertEqual('http://test.com/a/b/', relative_to_full('http://test.com/c/d/?cruft', '/a/b/'))
        self.assertEqual('http://test.com/a/b/', relative_to_full('http://test.com', 'http://test.com/a/b/'))
        self.assertEqual('http://blah.com/a/b/', relative_to_full('http://test.com', 'http://blah.com/a/b/'))
        self.assertEqual('/a/b/', relative_to_full('', '/a/b/'))
    
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
            'r/django/',
            'http://www.google.com/',
            'http://some-link.com/asdf/reddit/',
        ]
        filtered = [
            'http://m.reddit.com/',
            'http://www.reddit.com/',
            'http://www.reddit.com/r/django/',
            'http://reddit.com/r/django/',
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
            'http://m.www.reddit.com/r/django/',
        ]
        domains = [
            'http://m.www.reddit.com/r/django/',
        ]
        for domain in domains:
            self.assertEqual(filter_urls(domain, urls), filtered)
    
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
