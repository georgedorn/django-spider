from djutils.test import TestCase

from spider import utils as spider_utils
from spider.models import SpiderProfile, SpiderSession, URLResult
from spider.utils import crawl


class SpideringTestCase(TestCase):
    urls = 'spider.tests.urls'
    
    def setUp(self):
        TestCase.setUp(self)
        
        #  /~\
        # C oo
        # _( ^)
        #/   ~\
        # monkey patch the fetcher to use the test client
        def monkeypatched_fetch(url, timeout):
            url = url.replace('http://testserver', '')
            response = self.client.get(url)
            return response._headers, response.content
        
        self.orig_fetch = spider_utils.fetch_url
        spider_utils.fetch_url = monkeypatched_fetch
    
    def tearDown(self):
        TestCase.tearDown(self)
        
        spider_utils.fetch_url = self.orig_fetch
    
    def test_crawler(self):
        # these should all be equivalent to the crawler
        url_pairs = (
            ('http://testserver/', 'http://testserver/'),
            ('http://testserver/', 'http://testserver'),
            ('http://testserver', 'http://testserver/'),
            ('http://testserver', 'http://testserver'),
        )
        for (src, dst) in url_pairs:
            h, c, urls = crawl(src, dst, 1)
            self.assertEqual(urls, [
                'http://testserver/1/',
                'http://testserver/2/',
                'http://testserver/?page=3',
            ])
        
        # test a sub-page
        headers, content, urls = crawl('http://testserver/', 'http://testserver/1/', 1)
        self.assertEqual(urls, [
            'http://testserver/1/1/',
            'http://testserver/1/2/',
            'http://testserver/1/?page=3',
        ])
        
        # test a deeper sub-page!
        header, content, urls = crawl('http://testserver/1/', 'http://testserver/1/2/', 2)
        self.assertEqual(urls, [
            'http://testserver/1/2/1/',
            'http://testserver/1/2/2/',
            'http://testserver/1/2/?page=3',
        ])
    
    def test_crawling_404(self):
        headers, content, urls = crawl('http://testserver/', 'http://testserver/404/', 1)
        self.assertEqual(urls, [])
        self.assertEqual(headers['status'], '404')
    
    def test_crawling_500(self):
        headers, content, urls = crawl('http://testserver/', 'http://testserver/500/', 1)
        self.assertEqual(urls, [])
        self.assertEqual(headers['status'], '500')
    
    def test_spider(self):
        profile = SpiderProfile.objects.create(
            title='test server',
            url='http://testserver/',
            time_limit=.5,
            depth=1,
            timeout=.25,
        )
        results = profile.spider()

        self.assertEqual(results, {
            'http://testserver/': 200, # depth 0
            
            'http://testserver/1/': 200, # depth 1
            'http://testserver/2/': 200,
            'http://testserver/?page=3': 200
        })
        
        latest_session = profile.sessions.all()[0]
        self.assertEqual(latest_session.results.count(), 4)
        self.assertEqual(dict(
                (obj.url, obj.response_status) \
                    for obj in latest_session.results.all()
            ), results
        )
        
        profile.depth = 2
        profile.save()
        results = profile.spider()
        
        self.assertEqual(results, {
            'http://testserver/': 200, # depth 0
            
            'http://testserver/1/': 200, # depth 1
            'http://testserver/2/': 200,
            'http://testserver/?page=3': 200,
            
            'http://testserver/1/1/': 200, # depth 2
            'http://testserver/1/2/': 200,
            'http://testserver/1/?page=3': 200,
            
            'http://testserver/2/1/': 200,
            'http://testserver/2/2/': 200,
            'http://testserver/2/?page=3': 200,
        })
        
        latest_session = profile.sessions.all()[0]
        self.assertEqual(latest_session.results.count(), 10)
        self.assertEqual(dict(
                (obj.url, obj.response_status) \
                    for obj in latest_session.results.all()
            ), results
        )

        profile.depth = 3
        profile.save()
        results = profile.spider()
        
        self.assertEqual(results, {
            'http://testserver/': 200, # depth 0
            
            'http://testserver/1/': 200, # depth 1
            'http://testserver/2/': 200,
            'http://testserver/?page=3': 200,
            
            'http://testserver/1/1/': 200, # depth 2
            'http://testserver/1/2/': 200,
            'http://testserver/1/?page=3': 200,
            
            'http://testserver/2/1/': 200,
            'http://testserver/2/2/': 200,
            'http://testserver/2/?page=3': 200,
            
            'http://testserver/1/1/1/': 200, # depth 3
            'http://testserver/1/1/2/': 200,
            'http://testserver/1/1/?page=3': 200,
            
            'http://testserver/1/2/1/': 200,
            'http://testserver/1/2/2/': 200,
            'http://testserver/1/2/?page=3': 200,
            
            'http://testserver/2/1/1/': 200,
            'http://testserver/2/1/2/': 200,
            'http://testserver/2/1/?page=3': 200,
            
            'http://testserver/2/2/1/': 200,
            'http://testserver/2/2/2/': 200,
            'http://testserver/2/2/?page=3': 200,
        })
        
        latest_session = profile.sessions.all()[0]
        self.assertEqual(latest_session.results.count(), 22)
        self.assertEqual(dict(
                (obj.url, obj.response_status) \
                    for obj in latest_session.results.all()
            ), results
        )
