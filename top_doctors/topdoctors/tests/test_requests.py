# to start python -m tests.tests from parent folder
import os
import unittest

from scrapy.http import Request, TextResponse

from spiders.Topdoctors import TopdoctorsSpider


TEST_RESPONSES_DIR = os.path.join(
    os.path.sep,
    os.path.dirname(os.path.realpath(__file__)),
    'test_responses')


def response_from_file(file_path, url=None):
    """Create a Scrapy fake HTTP response from a HTML file"""
    if not url:
        url = 'http://www.example.com'

    request = Request(url=url)

    full_file_path = os.path.join(TEST_RESPONSES_DIR, file_path)
    with open(full_file_path, 'r') as f:
        body = f.read()
    response = TextResponse(
        url=url, request=request, body=body, encoding='utf-8')
    return response


class TopdoctorsSpiderTest(unittest.TestCase):

    def setUp(self):
        self.spider = TopdoctorsSpider()

    def test_parse_specializations_spain(self):
        print("fsdf")
        response = response_from_file(
            file_path="specializations\es_specializations.html",
            url="https://www.topdoctors.es/sitemap/especialistas")

        requests = list(self.spider.parse(response))
        self.assertEqual(len(requests), 71)

    def test_parse_specializations_italy(self):
        response = response_from_file(
            file_path="specializations\it_specializations.html",
            url="https://www.topdoctors.it/sitemap/specializzazioni-mediche")

        requests = list(self.spider.parse(response))
        self.assertEqual(len(requests), 49)


if __name__ == "__main__":
    unittest.main()
