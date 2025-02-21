"""Test cases for robots.txt parsing and integration."""

import unittest
from unittest.mock import patch, Mock
import responses
from utils import RobotsParser
from crawler import crawl
from sitemap import SitemapManager

class TestRobotsParser(unittest.TestCase):
    """Test suite for robots.txt parsing and rule checking."""

    def setUp(self):
        self.base_url = "https://example.com"
        self.robots_url = "https://example.com/robots.txt"

    @responses.activate
    def test_robots_parser_no_robots_txt(self):
        """Test behavior when no robots.txt exists."""
        responses.add(responses.GET, self.robots_url, status=404)
        
        parser = RobotsParser(self.base_url)
        self.assertTrue(parser.is_allowed("/any/path"))
        self.assertEqual(parser.crawl_delay, 0)

    @responses.activate
    def test_robots_parser_with_rules(self):
        """Test parsing of robots.txt rules."""
        robots_content = """
        User-agent: *
        Disallow: /private/
        Allow: /public/
        Crawl-delay: 2
        
        User-agent: testbot
        Disallow: /test/
        Allow: /test/public/
        """
        responses.add(responses.GET, self.robots_url, body=robots_content, status=200)
        
        parser = RobotsParser(self.base_url)
        
        # Test disallow rules
        self.assertFalse(parser.is_allowed("/private/page"))
        self.assertTrue(parser.is_allowed("/public/page"))
        self.assertTrue(parser.is_allowed("/other/page"))
        
        # Test crawl delay
        self.assertEqual(parser.crawl_delay, 2)

    @responses.activate
    def test_respect_crawl_delay(self):
        """Test that crawl delay is respected."""
        robots_content = """
        User-agent: *
        Crawl-delay: 0.1
        """
        responses.add(responses.GET, self.robots_url, body=robots_content, status=200)
        
        parser = RobotsParser(self.base_url)
        import time
        
        start_time = time.time()
        parser.respect_crawl_delay()
        parser.respect_crawl_delay()
        end_time = time.time()
        
        # Should have waited at least 0.1 seconds between requests
        self.assertGreaterEqual(end_time - start_time, 0.1)

class TestCrawlerRobotsIntegration(unittest.TestCase):
    """Test integration of robots.txt with crawler."""

    def setUp(self):
        self.base_url = "https://example.com"
        self.sitemap = SitemapManager(self.base_url)
        self.robots_parser = RobotsParser(self.base_url)

    @patch('crawler.fetch_page')
    def test_crawler_respects_robots(self, mock_fetch):
        """Test that crawler respects robots.txt rules."""
        # Mock fetch_page to return some HTML content
        mock_fetch.return_value = "<html><body><a href='/allowed'>Link</a></body></html>"
        
        # Mock robots.txt parser
        mock_robots = Mock()
        mock_robots.is_allowed.side_effect = lambda url: not url.startswith("/disallowed")
        mock_robots.respect_crawl_delay = Mock()
        
        # Test crawling
        crawl("https://example.com/test", self.sitemap, self.base_url, mock_robots)
        
        # Verify robots.txt was checked
        mock_robots.is_allowed.assert_called()
        # Verify crawl delay was respected
        mock_robots.respect_crawl_delay.assert_called()

if __name__ == '__main__':
    unittest.main()
