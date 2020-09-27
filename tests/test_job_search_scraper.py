"""
TODO:
    1) Add mock html documents to unit test BeautifulSoup.
    2) Look into integration tests for BeautifulSoup and requests.
    3) Look into unit tests for requests.
"""
import unittest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import src.job_search_scraper as job_scraper
from pathlib import Path
from mmap import mmap, ACCESS_READ


class JobScraperTests(unittest.TestCase):

    def setUp(self):
        self.scraper = job_scraper.JobSearchScraper("junior software engineer", "portland", [], {})
        f = (Path(__file__).parent / "data/test_job_card_valid.html").open()
        self.valid_card = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/test_job_card_invalid.html").open()
        self.invalid_card = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/job_count_test_files/test_search_count_pages_valid.html").open()
        self.valid_search_count_pages = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/job_count_test_files/test_search_count_pages_comma_valid.html").open()
        self.valid_search_count_pages_comma = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/job_count_test_files/test_search_count_pages_invalid.html").open()
        self.invalid_search_count_pages = BeautifulSoup(f.read(), "html.parser")
        f.close()
        f = (Path(__file__).parent / "data/test_job_search_fullpage.html").open()
        self.fullpage = BeautifulSoup(f.read(), "html.parser")
        self.search_fullpage = mmap(f.fileno(), 0, access=ACCESS_READ).read().decode("utf-8")
        f.close()

    @patch.multiple('src.job_search_scraper',
                    get_job_title_indeed=MagicMock(return_value=".net developer (oregon state)"),
                    check_valid_job_title=MagicMock(return_value=True),
                    get_description_url=MagicMock(
                        return_value="https://www.indeed.com/viewjob?jk=09c72f50e34a9383&vjs=3"),
                    get_job_id_indeed=MagicMock(return_value="09c72f50e34a9383"),
                    find_company_indeed=MagicMock(return_value="Hexacta"),
                    find_job_location_indeed=MagicMock(return_value="Oregon City, OR"),
                    find_job_post_date_indeed=MagicMock(return_value="24 days ago"),
                    find_job_post_summary_indeed=MagicMock(return_value="Design, develop and maintain complex"
                                                                        " software systems. Keep abreast of software"
                                                                        " development language revisions and"
                                                                        " technological advances."))
    def test_get_indeed_job_info_single(self):
        result = self.scraper.get_indeed_job_info(self.valid_card, [])
        arr = [["09c72f50e34a9383", ".net developer (oregon state)", "Oregon City, OR", "Hexacta", "24 days ago",
               "None", "Design, develop and maintain complex software systems. Keep abreast of software development"
                       " language revisions and technological advances.",
               "https://www.indeed.com/viewjob?jk=09c72f50e34a9383&vjs=3"]]
        self.assertEqual(result, arr)

    @patch.multiple('src.job_search_scraper',
                    get_job_title_indeed=MagicMock(side_effect=["title1", "title2", "title3", "title4", "title5"]),
                    check_valid_job_title=MagicMock(side_effect=[True, True, False, True, False]),
                    get_description_url=MagicMock(side_effect=["url1", "url2", "url3"]),
                    get_job_id_indeed=MagicMock(side_effect=["id1", "id2", "id3"]),
                    find_company_indeed=MagicMock(side_effect=["comp1", "comp2", "comp3"]),
                    find_job_location_indeed=MagicMock(side_effect=["loc1", "loc2", "loc3"]),
                    find_job_post_date_indeed=MagicMock(side_effect=["date1", "date2", "date3"]),
                    find_job_post_summary_indeed=MagicMock(side_effect=["summary1", "summary2", "summary3"]))
    def test_get_indeed_job_info_multiple(self):
        result = self.scraper.get_indeed_job_info(self.fullpage, [])
        arr = [["id1", "title1", "loc1", "comp1", "date1", "None", "summary1", "url1"],
               ["id2", "title2", "loc2", "comp2", "date2", "None", "summary2", "url2"],
               ["id3", "title4", "loc3", "comp3", "date3", "None", "summary3", "url3"]]
        self.assertEqual(result, arr)

    def test_find_company_indeed_valid(self):
        result = job_scraper.find_company_indeed(self.valid_card)
        self.assertEqual(result, "Hexacta")

    def test_find_company_indeed_invalid(self):
        result = job_scraper.find_company_indeed(self.invalid_card)
        self.assertEqual(result, "")

    def test_find_job_location_indeed_valid(self):
        result = job_scraper.find_job_location_indeed(self.valid_card)
        self.assertEqual(result, "Oregon City, OR")

    def test_find_job_location_indeed_invalid(self):
        result = job_scraper.find_job_location_indeed(self.invalid_card)
        self.assertEqual(result, "")

    def test_find_job_post_date_indeed_valid(self):
        result = job_scraper.find_job_post_date_indeed(self.valid_card)
        self.assertEqual(result, "24 days ago")

    def test_find_job_post_date_indeed_invalid(self):
        result = job_scraper.find_job_post_date_indeed(self.invalid_card)
        self.assertEqual(result, "")

    def test_get_job_id_indeed(self):
            card = self.valid_card.find('div', {'class': 'jobsearch-SerpJobCard unifiedRow row result'})
            result = job_scraper.get_job_id_indeed(card)
            self.assertEqual(result, "09c72f50e34a9383")

    def test_send_request_valid(self):
        with patch('src.job_search_scraper.requests.get') as mock_request:
            url = "http://google.com"
            mock_request.return_value.status_code = 200
            mock_request.return_value.content = "Some mock content"
            response = job_scraper.send_request(url, {})
            self.assertIsNotNone(response)

    def test_send_request_invalid(self):
        with patch('src.job_search_scraper.requests.get') as mock_request:
            url = "http://google.com"
            mock_request.return_value.status_code = 404
            response = job_scraper.send_request(url, {})
            self.assertIsNone(response)
            mock_request.assert_called_once_with(url, params={})

    def test_check_description_requirements(self):
        result = job_scraper.check_description_requirements("the is the 5 things I don't need. 4+ lorum ipsum")
        self.assertTrue(result)
        result = job_scraper.check_description_requirements(".NET 4+ years of production experience")
        self.assertFalse(result)
        result = job_scraper.check_description_requirements(".NET 3-5 years")
        self.assertFalse(result)

    def test_find_job_post_summary_indeed_valid(self):
        result = job_scraper.find_job_post_summary_indeed(self.valid_card)
        correct_res = "Design, develop and maintain complex software systems. Keep abreast of software development " \
                      "language revisions and technological advances."
        self.assertEqual(result, correct_res)

    def test_get_indeed_jobs_count_valid(self):
        result = job_scraper.get_indeed_jobs_count(self.valid_search_count_pages)
        self.assertEqual(result, 589)

    def test_get_indeed_jobs_count_comma(self):
        result = job_scraper.get_indeed_jobs_count(self.valid_search_count_pages_comma)
        self.assertEqual(result, 5989)

    def test_get_indeed_jobs_count_invalid(self):
        result = job_scraper.get_indeed_jobs_count(self.invalid_search_count_pages)
        self.assertEqual(result, -1)

    def test_get_job_title_indeed_valid(self):
        result = job_scraper.get_job_title_indeed(self.valid_card)
        self.assertEqual(result, ".net developer (oregon state)")

    def test_get_job_title_indeed_invalid(self):
        result = job_scraper.get_job_title_indeed(self.invalid_card)
        self.assertEqual(result, "")

    def test_check_valid_job_title_true(self):
        result = job_scraper.check_valid_job_title(".net developer (oregon state)", ["senior", "sr."])
        self.assertTrue(result)

    def test_check_valid_job_title_false(self):
        result = job_scraper.check_valid_job_title(".net developer (oregon state)", ["senior", ".net"])
        self.assertFalse(result)

    # @patch('src.job_search_scraper.get_description_url')
    # def test_find_job_title_indeed_filter(self, mock_return):
    #     mock_return.return_value = True, "https://placeholder.xyz"
    #     result = job_scraper.find_job_title_indeed(self.invalid_card, ['.net'], [])
    #     self.assertEqual(result, ("", ""))
    #     mock_return.assert_not_called()

    @unittest.skip
    def test_get_jobmap_valid(self):
        self.scraper.get_jobmap(self.search_fullpage)
        jobmap_ids = [
            '09c72f50e34a9383', '4c24de303832bb3b', '62bd365536499f30', '1b49f0b4774b984e', '5e6c17abae07208b',
            'c60aa68eb3872bac', '27bd456c574c3733', 'd7f10650ff426126', '37ff0493102ff545', '9032a7f27be9fb14',
            '3e617ed9345ab519', '65d6ab603cf5416d', '5b9883ee8f907146', '4cf15a0a73ed4489', '48f0254f3fee04a4',
        ]
        self.assertEqual(self.scraper.jobmap, jobmap_ids)

    def test_get_job_id_indeed_valid(self):
        card = self.valid_card.find('div', {'class': 'jobsearch-SerpJobCard unifiedRow row result'})
        result = job_scraper.get_job_id_indeed(card)
        self.assertEqual(result, "09c72f50e34a9383")

    def test_get_job_id_indeed_invalid(self):
        card = self.invalid_card.find('div', {'class': 'jobsearch-SerpJobCard unifiedRow row result'})
        result = job_scraper.get_job_id_indeed(card)
        self.assertEqual(result, "")
        # shouldn't be possible but testing to make sure it still works
        result = job_scraper.get_job_id_indeed(self.invalid_card)
        self.assertEqual(result, "")


if __name__ == '__main__':
    unittest.main()
