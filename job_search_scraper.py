import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import urllib
import pymysql

base_url = "https://www.indeed.com/"
# default_websites = ['indeed']
# job_titles = ['Software Developer', 'sdet', 'junior software engineer', 'qa engineer']#['Software Developer', 'software engineer', 'sdet', 'junior software engineer', 'junior software developer', 'qa engineer']
# search_locations = ['Portland','Seattle','United States']#]
# titles_to_skip = ['senior', 'front', 'frontend', '2021', 'sr', 'sr.', 'director', 'lead', 'principal', 'manager']
experience_filter = re.compile('[2-9]\s*\+?-?\s*[1-9]?\s*[yY]e?a?[rR][sS]?')
jobmap_filter = re.compile('jobmap\[[0-9]+\]=\s+{jk:\'(\w+)\'') #('jobmap\[[0-9]?\]=\s+{(.*)+}')'jobmap\[[0-9]+\]=\s+{.+}'
# # re.compile('jobmap\[[0-9]?\]\s+=\s+{(.*)+}')
# jobmap = []
# cols = ['Job_Title', 'Location', 'Company', 'Date', 'Salary', 'Description', 'url']
# dataframe = pd.DataFrame(columns=cols)


class JobSearchScraper:
    title = ""
    location = ""
    titles_to_skip = []
    search_filter = {}
    jobmap = []
    # dataframe = pd.DataFrame(columns=cols)
    data = []

    def __init__(self, title: str, location: str, titles_filter: [str], search_filter: {}):
        self.title = title
        self.location = location
        self.titles_to_skip = titles_filter
        self.search_filter = search_filter

    def get_indeed_jobs(self):
        page_num = 0
        jobs_per_page = 10
        print("Searching for {0} jobs in {1}".format(self.title, self.location))
        url = ("https://www.indeed.com/jobs?q={0}".format(self.title.replace(' ', '%20')) + urllib.parse.urlencode(self.search_filter))
        response = requests.get(url)
        total_pages = get_indeed_jobs_count(response)
        print("total_pages {0} for search {1} in {2}".format(total_pages, self.title, self.location))
        for page_num in range(0, total_pages, jobs_per_page):
            if page_num == 0:
                soup = BeautifulSoup(response.content, "html.parser")
                self.get_jobmap(response.text)
                page_results = self.get_indeed_job_info(soup)
            else:
                temp_url = "{0}&start={1}".format(url, page_num)
                # print(temp_url)
                response = requests.get(temp_url)
                self.get_jobmap(response.text)
                if response.status_code != 200:
                    print("request failed with status code " + response.status_code)
                    continue
                soup = BeautifulSoup(response.content, "html.parser")
                page_results = self.get_indeed_job_info(soup)

            self.data.extend(page_results)

        return self.data

    def get_indeed_job_info(self, soup):

        data = []
        # try:
        for card in soup.find_all('div', {'class': 'jobsearch-SerpJobCard unifiedRow row result'}):
            title, description_url = find_job_title_indeed(card, self.titles_to_skip, self.jobmap)
            if len(title) == 0:
                continue
            company_name = find_company_indeed(card)
            location = find_job_location_indeed(card)
            date_posted = find_job_post_date_indeed(card)
            summary = find_job_post_summary_indeed(card)
            data.append([title, location, company_name, date_posted, "not implemented", summary, description_url])

        return data


    def get_jobmap(self, text):
        self.jobmap = jobmap_filter.findall(text)


# def find_jobs(website, job_title, locations):
#     if website == 'indeed':
#         result = get_indeed_jobs(job_title, locations)


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


# def get_jobmap(text):
#
#     global jobmap
#     jobmap = jobmap_filter.findall(text)


# def get_indeed_job_info(soup):
#
#     data = []
#     # try:
#     for card in soup.find_all('div', {'class':'jobsearch-SerpJobCard unifiedRow row result'}):
#         title, description_url = find_job_title_indeed(card)
#         if len(title) == 0:
#             continue
#         company_name = find_company_indeed(card)
#         location = find_job_location_indeed(card)
#         date_posted = find_job_post_date_indeed(card)
#         summary = find_job_post_summary_indeed(card)
#         data.append([title, location, company_name, date_posted, "not implemented", summary, description_url])
    # add_to_dataframe(data)
    # except:
    #     print("get_indeed_job_info() exception")


def add_to_dataframe(job_data):

    global dataframe
    for job in job_data:
        dataframe.loc[len(dataframe)] = job

 
def find_job_title_indeed(card, titles_to_skip: [str], jobmap: [str]):
    
    title_text = card.find("h2", {"class":"title"})
    title = title_text.text.lower().strip()

    if not any(ele in title for ele in titles_to_skip):
        valid, job_description_url = check_entry_level_job(title_text, jobmap)
        if valid:
            if title.find('\n') != -1:
                title = title.split('\n')[0]
            return title, job_description_url
    # print("invalid job title: " + title)
    return "", ""


def check_entry_level_job(soup, jobmap: [str]):

    for link in soup.find_all("a"):
        job_description_url = link.get('href')
        if job_description_url.find('pagead') != -1:
            jobmap_id = re.search('jobmap\[([0-9]+)\]', link.attrs['onclick']).group(1)
            vjs = re.search('(vjs=[0-9]+)', job_description_url).group(1)
            job_description_url = "/viewjob?jk={0}&{1}".format(jobmap[int(jobmap_id)], vjs)
        job_description_url = "https://www.indeed.com" + job_description_url
        response = requests.get(job_description_url)
        check = experience_filter.search(response.text)
        if not check:
            return True, job_description_url

    return False, ""
    
    
def find_company_indeed(card):
    
    company_text = card.find('span', class_='company')
    if not company_text:
        company_text = card.find('div', class_='company')
    company = company_text.text.strip()
    
    return company


def find_job_location_indeed(card):
    
    location_text = card.find('span', class_='location')
    if not location_text:
        location_text = card.find('div', class_='location')
    location = location_text.text.strip()
    
    return location

    
def find_job_post_date_indeed(card):
    
    date_text = card.find('span', class_='date')
    date = date_text.text.strip()
    
    return date


def find_job_post_summary_indeed(card):

    summary_text = card.find('div', class_='summary')
    summary = summary_text.text.strip().replace('\n', '')

    return summary


def get_indeed_jobs_count(page):

    try:
        soup = BeautifulSoup(page.text, "lxml")
        text = soup.find('div', {'id': 'searchCountPages'}).get_text()
        total_jobs = int(text.split("of ")[1].split(' ')[0].replace(',', ''))
        return total_jobs
    except:
        print("failed to find total job coount for indeed search")
        return -1


# def start_search(job_title: str, location: str, search_filters: {}, title_filters: [str]):


# if __name__ == "__main__":
#
#     find_jobs("indeed", job_titles, search_locations)
#     dataframe.drop_duplicates(subset=None, keep="first", inplace=True)
#     dataframe.to_csv("test.csv", columns=cols)