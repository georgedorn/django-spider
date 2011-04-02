from djutils.test import TestCase

from spider.models import SpiderProfile, SpiderSession, URLResult


class SpiderModelTestCase(TestCase):
    fixtures = ['spider_tests.json']
    
    def test_results_with_status(self):
        # spidering reddit on 4/1
        s1 = SpiderSession.objects.get(pk=1)
        
        self.assertEqual([r.url for r in s1.results_with_status(200)], [
            'http://reddit.com/',
            'http://reddit.com/r/django/',
            'http://reddit.com/r/python/',
        ])
        
        self.assertEqual([r.url for r in s1.results_with_status(404)], [
            'http://reddit.com/r/not-here/',
        ])
        
        self.assertEqual([r.url for r in s1.results_with_status(500)], [
            'http://reddit.com/r/error/',
        ])
    
    def test_new_this_session(self):
        # spidering reddit on 4/1
        s1 = SpiderSession.objects.get(pk=1)
        
        self.assertEqual([r.url for r in s1.new_this_session(200)], [
            'http://reddit.com/',
            'http://reddit.com/r/django/',
            'http://reddit.com/r/python/',
        ])
        
        self.assertEqual([r.url for r in s1.new_this_session(404)], [
            'http://reddit.com/r/not-here/',
        ])
        
        self.assertEqual([r.url for r in s1.new_this_session(500)], [
            'http://reddit.com/r/error/',
        ])
        
        # spidering reddit on 4/2
        s2 = SpiderSession.objects.get(pk=2)
        
        self.assertEqual([r.url for r in s2.new_this_session(200)], [])
        self.assertEqual([r.url for r in s2.new_this_session(404)], [])
        self.assertEqual([r.url for r in s2.new_this_session(500)], [])
        
        # grab the 404 from session 2
        s2_404 = URLResult.objects.get(session=s2, response_status=404)
        s2_404.response_status = 200
        s2_404.save()
        
        self.assertEqual([r.url for r in s2.new_this_session(200)], [
            'http://reddit.com/r/not-here/'
        ])
        
        s2_200_1 = URLResult.objects.get(session=s2, url='http://reddit.com/')
        s2_200_1.response_status = 404
        s2_200_1.save()

        self.assertEqual([r.url for r in s2.new_this_session(404)], [
            'http://reddit.com/'
        ])
        
        s2_200_2 = URLResult.objects.get(session=s2, url='http://reddit.com/r/django/')
        s2_200_2.response_status = 500
        s2_200_2.save()

        self.assertEqual([r.url for r in s2.new_this_session(500)], [
            'http://reddit.com/r/django/'
        ])
        
        new_res = URLResult.objects.create(
            session=s2,
            url='http://reddit.com/r/new-result/',
            response_status=500,
            response_time=0.5,
            content_length=1
        )

        self.assertEqual([r.url for r in s2.new_this_session(500)], [
            'http://reddit.com/r/new-result/',
            'http://reddit.com/r/django/',
        ])
    
    def test_previous_status(self):
        r1 = URLResult.objects.get(pk=1)
        self.assertEqual(r1.previous_status(), None)
        
        r6 = URLResult.objects.get(pk=6)
        self.assertEqual(r6.previous_status(), 200)
    
    def test_short_url(self):
        s1 = SpiderSession.objects.get(pk=1)
        
        short_urls = [
            '/',
            '/r/django/',
            '/r/python/',
            '/r/error/',
            '/r/not-here/',
        ]
        
        for result, expected in zip(s1.results.all().order_by('id'), short_urls):
            self.assertEqual(result.short_url(), expected)
