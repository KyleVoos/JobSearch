"""
TODO:
    1) Add mock html documents to unit test BeautifulSoup.
    2) Look into integration tests for BeautifulSoup and requests.
    3) Look into unit tests for requests.
"""
import unittest
from bs4 import BeautifulSoup
import src.job_search_scraper as job_scraper
from pathlib import Path


class JobScraperTests(unittest.TestCase):

    def setUp(self):
        f = (Path(__file__).parent / "data/test_job_card_valid.html").open()
        self.valid_card = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/test_search_count_pages_valid.html").open()
        self.valid_search_count_pages = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/test_search_count_pages_comma_valid.html").open()
        self.valid_search_count_pages_comma = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/test_search_count_pages_invalid.html").open()
        self.invalid_search_count_pages = BeautifulSoup(f.read(), "html.parser")
        f.close()

    def test_find_company_indeed_valid(self):
        result = job_scraper.find_company_indeed(self.valid_card)
        self.assertEqual(result, "Hexacta")

    def test_find_job_location_indeed_valid(self):
        result = job_scraper.find_job_location_indeed(self.valid_card)
        self.assertEqual(result, "Oregon City, OR")

    def test_find_job_post_date_indeed_valid(self):
        result = job_scraper.find_job_post_date_indeed(self.valid_card)
        self.assertEqual(result, "24 days ago")

    def test_get_indeed_jobs_count_valid(self):
        result = job_scraper.get_indeed_jobs_count(self.valid_search_count_pages)
        self.assertEqual(result, 589)

    def test_get_indeed_jobs_count_comma(self):
        result = job_scraper.get_indeed_jobs_count(self.valid_search_count_pages_comma)
        self.assertEqual(result, 5989)

    def test_get_indeed_jobs_count_invalid(self):
        result = job_scraper.get_indeed_jobs_count(self.invalid_search_count_pages)
        self.assertEqual(result, -1)


if __name__ == '__main__':
    unittest.main()