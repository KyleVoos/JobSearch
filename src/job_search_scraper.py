"""
Add an overview here later.

TODO:
    1) I should be able to change this from being a class and have everything continue to work correctly with
    less complexity.
    2) Split up find_job_title_indeed() and check_entry_level_job() so the functions are not getting
    job data and filtering job results.
    3) Look into multi-threading requests for paginated job results, they are independent of each other so it would work
    its just whether or not there would be a performance benefit and how many threads should I create.
"""
import requests
from bs4 import BeautifulSoup
import re
import urllib


base_url = "https://www.indeed.com/"
# job_titles = ['Software Developer', 'sdet', 'junior software engineer', 'qa engineer']#['Software Developer', 'software engineer', 'sdet', 'junior software engineer', 'junior software developer', 'qa engineer']
# search_locations = ['Portland','Seattle','United States']#]
# titles_to_skip = ['senior', 'front', 'frontend', '2021', 'sr', 'sr.', 'director', 'lead', 'principal', 'manager']
experience_filter = re.compile('[2-9]\s*\+?-?\s*[1-9]?\s*[yY]e?a?[rR][sS]?')
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

    def get_indeed_jobs(self):
        """

        Returns:
             [[str]]: 2d array holding all the results for the job title/location query.
        """
        jobs_per_page = 10
        data = []
        print("Searching for {0} jobs in {1}".format(self.title, self.location))
        url = ("https://www.indeed.com/jobs?q={0}&".format(self.title.replace(' ', '%20')) +
               urllib.parse.urlencode(self.search_filter))
        response = send_request(url)
        if not response:
            return data
        soup = BeautifulSoup(response.content, "html.parser")
        total_pages = get_indeed_jobs_count(soup)
        for page_num in range(0, total_pages, jobs_per_page):
            if page_num == 0:
                self.get_jobmap(response.text)
                page_results = self.get_indeed_job_info(soup)
            else:
                temp_url = "{0}&start={1}".format(url, page_num)
                response = send_request(temp_url)
                if not response:
                    print("request failed with status code " + response.status_code)
                    continue
                self.get_jobmap(response.text)
                soup = BeautifulSoup(response.content, "html.parser")
                page_results = self.get_indeed_job_info(soup)

            data.extend(page_results)

        return data

    def get_indeed_job_info(self, soup):
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
            title, description_url = find_job_title_indeed(card, self.titles_to_skip, self.jobmap)
            if len(title) == 0:
                continue
            job_id = get_job_id_indeed(card)
            company_name = find_company_indeed(card)
            location = find_job_location_indeed(card)
            date_posted = find_job_post_date_indeed(card)
            summary = find_job_post_summary_indeed(card)
            data.append([job_id, title, location, company_name, date_posted, "None", summary, description_url])

        return data

    def get_jobmap(self, text):
        """
        Some of the links for job descriptions are created dynamically, this function finds the JavaScript
        values of the jobmap[] variable in a script of the html doc returned from the original page request.
        All of the jobmap values are found with a regex capture.

        Args:
            text (BeautifulSoup object): The html results from the page request

        Returns:
            No return
        """
        self.jobmap = jobmap_filter.findall(text)


# def get_indeed_jobs(job_title, locations):
#
#     page_num = 0
#     jobs_per_page = 10
#     global jobmap
#     # try:
#     for job in  job_title:
#         for loc in locations:
#             print("Searching for {0} jobs in {1}".format(job, loc))
#             url = "https://www.indeed.com/jobs?q={0}&l={1}&fromage=14".format(job.replace(' ', '%20'),
#                                                                               loc.replace(' ', '+'))
#             response = requests.get(url)
#             total_pages = get_indeed_jobs_count(response)
#             print("total_pages: {0}".format(total_pages))
#             for page_num in range(0, total_pages, jobs_per_page):
#                 print("page_num: {0}".format(page_num))
#                 if page_num == 0:
#                     soup = BeautifulSoup(response.content, "html.parser")
#                     get_jobmap(response.text)
#                     get_indeed_job_info(soup)
#                 else:
#                     temp_url = "{0}&start={1}".format(url, page_num)
#                     # print(temp_url)
#                     response = requests.get(temp_url)
#                     get_jobmap(response.text)
#                     if response.status_code != 200:
#                         print("request failed with status code " + response.status_code)
#                         continue
#                     soup = BeautifulSoup(response.content, "html.parser")
#                     temp = soup
#                     get_indeed_job_info(soup)
#             print("dataframe len: {0}".format(len(dataframe)))
    # except:
    #     print("fail")


def send_request(url: str):

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response


def get_job_id_indeed(card):

    if card['data-jk']:
        return card['data-jk']

    return ""


def add_to_dataframe(job_data):
    """
    Not being used currently.
    Args:
     job_data:

    Returns:
    """
    global dataframe
    for job in job_data:
        dataframe.loc[len(dataframe)] = job

 
def find_job_title_indeed(card, titles_to_skip: [str], jobmap: [str]):
    """
    Function that currently gets the job title, filters based on it, and calls check_entry_level_job which filters
    based on experience requirements and if its valid gets the job URL.

    Args:
        card (BeautifulSoup object): The individual job posting card being processed.
        titles_to_skip ([str]): Array of strings entered by user used to filter out results based on job title.
        jobmap ([str]):

    Returns:
        str: The job title or empty string is result is being skipped.
        str: URL to individual job posting or empty string if being skipped.
    """
    title_text = card.find("h2", {"class": "title"})
    title = title_text.text.lower().strip()

    if not any(ele in title for ele in titles_to_skip):
        valid, job_description_url = check_entry_level_job(title_text, jobmap)
        if valid:
            if title.find('\n') != -1:
                title = title.split('\n')[0]
            return title, job_description_url
    return "", ""


def check_entry_level_job(soup, jobmap: [str]):
    """
    Function to check if a job is entry-level and extract the job description URL. To check whether a job is
    entry-level or not an HTTP request is made to the job description URL. After the description text is found
    a regex is used to search the text for any strings matching [1+]-[2+], [#] years. If anything is found the
    job is not considered to be entry level and is left out of the results.

    This function is also where the jobmap is used. Because some description URLs are built dynamically, and will
    contain 'pagead' this is used to identify that using the jobmap is needed. Next a regular expression is used to
    capture the jobmap IDs number from the HTML text and the job description URL is built.

    Args:
        soup (BeautifulSoup object): BS4 object of the job card being processed.
        jobmap ([str]): The jobmap for this current instance of the JobSearchScraper class.

    Returns:
         bool: True if a valid entry level job, otherwise False.
         str: Job posting URL if a valid job, otherwise empty string.
    """
    for link in soup.find_all("a"):
        job_description_url = link.get('href')
        if job_description_url.find('pagead') != -1:
            # jobmap_id = re.search('jobmap\[([0-9]+)\]', link.attrs['onclick']).group(1)
            jobmap_id = jobmap_card_filter.search(link.attrs['onclick']).group(1)
            # vjs = re.search('(vjs=[0-9]+)', job_description_url).group(1)
            vjs = vjs_filter.search(job_description_url).group(1)
            job_description_url = "/viewjob?jk={0}&{1}".format(jobmap[int(jobmap_id)], vjs)
        job_description_url = "https://www.indeed.com" + job_description_url
        response = send_request(job_description_url)
        if not response:
            break
        check = experience_filter.search(response.text)
        if not check:
            return True, job_description_url

    return False, ""
    
    
def find_company_indeed(card) -> str:
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


def find_job_location_indeed(card) -> str:
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

    
def find_job_post_date_indeed(card) -> str:
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


def find_job_post_summary_indeed(card) -> str:
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
        return summary_text.text.replace('\n', '').replace('.', '. ').strip();

    return ""


def get_indeed_jobs_count(soup) -> int:
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
        print("failed to find total job coount for indeed search")
        return -1
