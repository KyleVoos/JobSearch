"""
Add an overview here later.

TODO:
    1) I should be able to change this from being a class and have everything continue to work correctly with
    less complexity. (PARTIALLY DONE)
    2) Split up find_job_title_indeed() and check_entry_level_job() so the functions are not getting
    job data and filtering job results. (DONE)
    3) Look into multi-threading requests for paginated job results, they are independent of each other so it would work
    its just whether or not there would be a performance benefit and how many threads should I create. (PARTIALLY DONE)
"""
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep


base_url = "https://www.indeed.com/"
experience_filter = re.compile('[2-9]\s*\+?-?\s*[1-9]?\s*[yY]e?a?[rR][sS]?')
valid_experience_filter = re.compile('[0-1]\s*\+?-?\s*[1-9]?\s*[yY]e?a?[rR][sS]?')
jobmap_filter = re.compile('jobmap\[[0-9]+\]=\s+{jk:\'(\w+)\'')
jobmap_card_filter = re.compile('jobmap\[([0-9]+)\]')
vjs_filter = re.compile('(vjs=[0-9]+)')


class JobSearchScraper:
    """

    Args:
        title (str): Job title/query being searched.
        location (str): Location of job search.
        titles_filter ([str]): Phrases to filter jobs based on title out of search results.
        search_filter (dict): Dictionary holding search options such as date posted, radius, etc.

    Attributes:
        title (str): Job title/query being searched.
        location (str): Location of job search.
        titles_filter ([str]): Phrases to filter jobs based on title out of search results.
        search_filter (dict): Dictionary holding search options such as date posted, radius, etc.
        jobmap ([str]): JavaScript variables from page results that are used to built dynamic URLs.
    """
    title = ""
    location = ""
    titles_to_skip = []
    search_filter = {}
    jobmap = []

    def __init__(self, title: str, location: str, titles_filter: [str], search_filter: {}):
        self.title = title
        self.location = location
        self.titles_to_skip = titles_filter
        self.search_filter = search_filter

    # def get_indeed_jobs(self):
    #     """
    #
    #     Returns:
    #          [[str]]: 2d array holding all the results for the job title/location query.
    #     """
    #     jobs_per_page = 10
    #     data = []
    #     print("Searching for {0} jobs in {1}".format(self.title, self.location))
    #     url = ("https://www.indeed.com/jobs?q={0}&".format(self.title.replace(' ', '%20')) +
    #            urllib.parse.urlencode(self.search_filter))
    #     response = send_request(url, {})
    #     if not response:
    #         return data
    #     soup = BeautifulSoup(response.content, "html.parser")
    #     total_pages = get_indeed_jobs_count(soup)
    #     print("Searching for {0} jobs in {1} | total pages found: {2}".format(self.title, self.location, total_pages))
    #     for page_num in range(0, total_pages, jobs_per_page):
    #         if page_num == 0:
    #             self.get_jobmap(response.text)
    #             page_results = self.get_indeed_job_info(soup, self.jobmap)
    #         else:
    #             temp_url = "{0}&start={1}".format(url, page_num)
    #             response = send_request(temp_url, {})
    #             if not response:
    #                 print("request failed with status code " + response.status_code)
    #                 continue
    #             self.get_jobmap(response.text)
    #             soup = BeautifulSoup(response.content, "html.parser")
    #             page_results = self.get_indeed_job_info(soup, self.jobmap)
    #
    #         data.extend(page_results)
    #
    #     return data

    def get_indeed_jobs_multithread(self):
        """
        The entry point for a job search. Starts by getting the total number of jobs pages.
        After total job count is found a new thread is spawned for every 50 pages of results,
        (step size is 10, 500 / 10 = 50). Each thread stores its own results which are then combined when
        all threads have finished.

        Returns:
            [[str]]: 2d array holding all the results for the job title/location query.
        """
        data = []
        processes = []

        url = ("https://www.indeed.com/jobs?q={0}&".format(self.title.replace(' ', '%20')))
        response = send_request(url, self.search_filter)
        if not response:
            return data
        soup = BeautifulSoup(response.content, "html.parser")
        total_pages = get_indeed_jobs_count(soup)
        # print("Searching for {0} jobs in {1} | total pages found: {2}".format(self.title, self.location, total_pages))
        with ThreadPoolExecutor() as executor:
            for page_start in range(0, total_pages, 500):
                page_end = page_start + 500 if page_start + 500 < total_pages else total_pages
                processes.append(executor.submit(self.get_jobs_pages, page_start, page_end))

        for task in as_completed(processes):
            data.extend(task.result())

        return data

    def get_jobs_pages(self, start_page: int, end_page: int) -> [[str]]:
        """
        Function that does the requests to get each page of job results. If the HTTP request is successful
        the page is passed to get_indeed_job_info(). After each page has been processed the results are
        added to an array that is returned after execution completes.

        Args:
            start_page (int): Starting job search results page number.
            end_page (int): Ending job search results number.

        Returns:
            [[str]]: 2d array containing all the extracted info for valid entry-level jobs.
        """
        data = []
        print("start_page: {0} | end_page: {1}".format(start_page, end_page))
        print("Searching for {0} jobs in {1}".format(self.title, self.location))
        url = "https://www.indeed.com/jobs?q={0}&".format(self.title.replace(' ', '%20'))
        for page_num in range(start_page, end_page, 10):
            temp_url = "{0}&start={1}".format(url, page_num)
            response = send_request(temp_url, self.search_filter)
            if not response:
                print("request failed with status code {0} | title: {1} | loc: {2}".format(response.status_code,
                                                                                           self.title, self.location))
                continue
            soup = BeautifulSoup(response.content, "html.parser")
            page_results = self.get_indeed_job_info(soup)
            data.extend(page_results)
            print("start_page: {0} | end_page: {1} | page_num: {2} | len(data): {3}".format(start_page, end_page, page_num, len(data)))
            sleep(1.0)

        return data

    def get_indeed_job_info(self, soup: BeautifulSoup):
        """
        Function that iterates through each of the job postings on a page of job search results
        With BeautifulSoup each 'card' is found on the page and then processed individually. Each
        card contains a job posting.

        Args:
            soup: requests result that has been processed by bs4

        Returns:
            [[str]]: Results of search as 2d array of strings
        """
        data = []

        for card in soup.find_all('div', {'class': 'jobsearch-SerpJobCard unifiedRow row result'}):
            title = get_job_title_indeed(card)
            if not check_valid_job_title(title, self.titles_to_skip):
                continue
            job_id = get_job_id_indeed(card)
            description_url = get_description_url(card.find("h2", {"class": "title"}), job_id)
            description_response = send_request(description_url, {})
            if not description_response:
                print("Failed to get job description for {0}: ID: {1}".format(title, job_id))
                continue
            if not check_description_requirements(description_response.text):
                continue
            company_name = find_company_indeed(card)
            location = find_job_location_indeed(card)
            date_posted = find_job_post_date_indeed(card)
            summary = find_job_post_summary_indeed(card)
            data.append([job_id, title, location, company_name, date_posted, "None", summary, description_url])

        return data


def send_request(url: str, queries: {}):
    """
    Used to send all HTTP requests. A base URL is passed along with a dictionary that contains any
    query strings that need to be added and encoded which is done by requests.

    Args:
        url (str): The base request URL.
        queries (dict): Dictionary containing the key/value pairs used to build remaining URL query statements.

    Returns:
         requests object: Object returned by the HTTP request after completing. If request was unsuccessful
                            None is returned instead.
    """
    response = requests.get(url, params=queries)

    if response.status_code != 200:
        return None

    return response


def get_job_id_indeed(card: BeautifulSoup) -> str:
    """
    Function to retrieve the job ID from an HTML tag in the <div class='jobsearch-SerpJobCard unifiedRow row result'.
    The job ID appears to be unique for each job and is used to remove duplicate results and later may be
    used as the primary key for an SQL database table.

    Args:
        card (BeautifulSoup object): The individual job posting card being processed.

    Returns:
        str: The job ID if found, otherwise an empty string.
    """
    if card['data-jk']:
        return card['data-jk']

    return ""


def get_job_title_indeed(card: BeautifulSoup) -> str:
    """
    Extracts the jobs title from the portion of HTML containing an individual job card.

    Args:
        card (BeautifulSoup object): The individual job posting card being processed.

    Returns:
         str: The job title extracted, otherwise an empty string.
    """
    title_text = card.find("h2", {"class": "title"})
    if title_text:
        return title_text.text.lower().strip()

    return ""


def check_valid_job_title(title: str, titles_to_skip: [str]) -> bool:
    """
    Determines if the job title extracted contains any of the phrases in titles_to_skip.
    If it does, this job is not included in the results.

    Args:
        title (str): Job title previously extracted.
        titles_to_skip ([str]): List of phrases that should be excluded in job titles.

    Returns:
        bool: True if job title doesn't contains anything in titles_to_skip, otherwise false.
    """
    return not any(ele in title for ele in titles_to_skip)


def get_description_url(soup: BeautifulSoup, job_id: str) -> str:
    """
    Find or builds the url for the job description. The url is extracted from the HTML passed, if the link
    contains 'pagead' its a dynamic link and the description url is programmatically built with the job_id.

    Args:
        soup (BeautifulSoup object):
        job_id (str):

    Returns:
        str: The url extracted from the HTML, or manually built from the job_id if the extracted url was dynamic.
    """
    for link in soup.find_all("a"):
        job_description_url = link.get('href')
        if job_description_url.find('pagead') != -1:
            vjs = vjs_filter.search(job_description_url).group(1)
            job_description_url = "/viewjob?jk={0}&{1}".format(job_id, vjs)
        return "https://www.indeed.com" + job_description_url


def check_description_requirements(text: str) -> bool:
    """
    Uses a regex to check whether the job description has requirements for years of experience or not.

    Args:
        text (str): The HTML doc represented as a string from the HTTP request for the job description.

    Returns:
        bool: True if the job is entry level (the experience filter did not capture anything), otherwise False.
    """
    check = experience_filter.search(text)
    valid_requirement = valid_experience_filter.search(text)

    return check is None or valid_requirement is not None
    
    
def find_company_indeed(card: BeautifulSoup) -> str:
    """
    Processes an individual job card to find the name of the company that posted the job.

    Args:
        card (BeautifulSoup object): A BS4 object consisting of the section of the HTML doc result for a
                                    single job posting (card taken from html div classname).

    Returns:
        str: The company from the job card if found, otherwise empty string.
    """
    company_text = card.find('span', class_='company')
    if not company_text:
        company_text = card.find('div', class_='company')
    if company_text:
        return company_text.text.strip()

    return ""


def find_job_location_indeed(card: BeautifulSoup) -> str:
    """
    Scrapes the jobs location from an individual job card.
    
    Args:
        card (BeautifulSoup object): A BS4 object consisting of the section of the HTML doc result for a
                                    single job posting (card taken from html div classname).

    Returns:
        str: The location scraped from the job card if found, otherwise an empty string.
    """
    location_text = card.find('span', class_='location')
    if not location_text:
        location_text = card.find('div', class_='location')
    if location_text:
        return location_text.text.strip()
    
    return ""

    
def find_job_post_date_indeed(card: BeautifulSoup) -> str:
    """
    Scrapes the date the job was posted from an individual job card.

    Args:
        card (BeautifulSoup object): A BS4 object consisting of the section of the HTML doc result for a
                                    single job posting (card taken from html div classname).

    Returns:
        str: Date scraped from the job card if found, otherwise empty string.
    """
    date_text = card.find('span', class_='date')
    if date_text:
        return date_text.text.strip()
    
    return ""


def find_job_post_summary_indeed(card: BeautifulSoup) -> str:
    """
    Scrapes the summary of the job from an individual job card.

    Args:
        card (BeautifulSoup object): A BS4 object consisting of the section of the HTML doc result for a
                                    single job posting (card taken from html div classname).

    Returns:
         str: Summary scraped from job card if found, otherwise empty string.
    """
    summary_text = card.find('div', class_='summary')
    if summary_text:
        return summary_text.text.replace('\n', '').replace('.', '. ').strip()

    return ""


def get_indeed_jobs_count(soup: BeautifulSoup) -> int:
    """
    Searches the original search query response for the total number of pages of results.

    Args:
        soup (BeautifulSoup object): BS4 object of the original response for title/location search.

    Returns:
         int: Number of total pages of job search results.
    """
    try:
        text = soup.find('div', {'id': 'searchCountPages'}).get_text()
        total_jobs = int(text.split("of ")[1].split(' ')[0].replace(',', ''))
        return total_jobs
    except:
        print("failed to find total job count for indeed search")
        return -1
