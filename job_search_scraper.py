import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import pymysql
import traceback
import time
from User_Input.user_input import InputData

base_url = "https://www.indeed.com/"
default_websites = ['indeed']
job_titles = ['Software Developer', 'sdet', 'junior software engineer', 'qa engineer']#['Software Developer', 'software engineer', 'sdet', 'junior software engineer', 'junior software developer', 'qa engineer']
search_locations = ['Portland','Seattle','United States']#]
titles_to_skip = ['senior', 'front', 'frontend', '2021', 'sr', 'sr.', 'director', 'lead', 'principal', 'manager']
experience_filter = re.compile('[2-9]\s*\+?-?\s*[1-9]?\s*[yY]e?a?[rR][sS]?')
jobmap_filter = re.compile('jobmap\[[0-9]+\]=\s+{jk:\'(\w+)\'') #('jobmap\[[0-9]?\]=\s+{(.*)+}')'jobmap\[[0-9]+\]=\s+{.+}'
# re.compile('jobmap\[[0-9]?\]\s+=\s+{(.*)+}')
jobmap = []
cols = ['Job_Title', 'Location', 'Company', 'Date', 'Salary', 'Description', 'url']
dataframe = pd.DataFrame(columns=cols)


def find_jobs(website, job_title, locations):
    if website == 'indeed':
        result = get_indeed_jobs(job_title, locations)


def get_indeed_jobs(job_title, locations):

    page_num = 0
    jobs_per_page = 10
    global jobmap
    # try:
    for job in  job_title:
        for loc in locations:
            print("Searching for {0} jobs in {1}".format(job, loc))
            url = "https://www.indeed.com/jobs?q={0}&l={1}&fromage=14".format(job.replace(' ', '%20'),
                                                                              loc.replace(' ', '+'))
            response = requests.get(url)
            total_pages = get_indeed_jobs_count(response)
            print("total_pages: {0}".format(total_pages))
            for page_num in range(0, total_pages, jobs_per_page):
                print("page_num: {0}".format(page_num))
                if page_num == 0:
                    soup = BeautifulSoup(response.content, "html.parser")
                    get_jobmap(response.text)
                    get_indeed_job_info(soup)
                else:
                    temp_url = "{0}&start={1}".format(url, page_num)
                    # print(temp_url)
                    response = requests.get(temp_url)
                    get_jobmap(response.text)
                    if response.status_code != 200:
                        print("request failed with status code " + response.status_code)
                        continue
                    soup = BeautifulSoup(response.content, "html.parser")
                    temp = soup
                    get_indeed_job_info(soup)
            print("dataframe len: {0}".format(len(dataframe)))
    # except:
    #     print("fail")


def get_jobmap(text):
    
    global jobmap

    # get_jobmap_start_time = time.perf_counter()
    jobmap = jobmap_filter.findall(text)
    # get_jobmap_end_time = time.perf_counter()
    # print("get_jobmap RT: {0}".format(get_jobmap_end_time - get_jobmap_start_time))


def get_indeed_job_info(soup):

    data = []
    # try:
    for card in soup.find_all('div', {'class':'jobsearch-SerpJobCard unifiedRow row result'}):
        title, description_url = find_job_title_indeed(card)
        if len(title) == 0:
            continue
        company_name = find_company_indeed(card)
        location = find_job_location_indeed(card)
        date_posted = find_job_post_date_indeed(card)
        summary = find_job_post_summary_indeed(card)
        data.append([title, location, company_name, date_posted, "not implemented", summary, description_url])
    add_to_dataframe(data)
    # except:
    #     print("get_indeed_job_info() exception")


def add_to_dataframe(job_data):

    global dataframe

    # add_dataframe_start = time.perf_counter()
    for job in job_data:
        dataframe.loc[len(dataframe)] = job
    # print("dataframe len: {0}".format(len(dataframe)))
    # add_dataframe_end = time.perf_counter()
    # print("add_to_dataframe RT: {0}".format(add_dataframe_end - add_dataframe_start))

 
def find_job_title_indeed(card):
    
    title_text = card.find("h2", {"class":"title"})
    title = title_text.text.lower().strip()

    if not any(ele in title for ele in titles_to_skip):
        valid, job_description_url = check_entry_level_job(title_text)
        if valid:
            if title.find('\n') != -1:
                title = title.split('\n')[0]
            return title, job_description_url
    # print("invalid job title: " + title)
    return "", ""


def check_entry_level_job(soup):
    
    # try:
    # check_entry_time = time.perf_counter()
    for link in soup.find_all("a"):
        job_description_url = link.get('href')
        if job_description_url.find('pagead') != -1:
            jobmap_id = re.search('jobmap\[([0-9]+)\]', link.attrs['onclick']).group(1)
            vjs = re.search('(vjs=[0-9]+)', job_description_url).group(1)
            job_description_url = "/viewjob?jk={0}&{1}".format(jobmap[int(jobmap_id)], vjs)
            # build_link_time = time.perf_counter()
            # print("check entry level RT: {0}".format(build_link_time - check_entry_time))
        job_description_url = "https://www.indeed.com" + job_description_url
        # check_entry_time = time.perf_counter()
        # response = requests.get(job_description_url)
        # desc_soup = BeautifulSoup(response.content, "html.parser")
        # desc_text = desc_soup.find('div', id='jobDescriptionText')
        # check = experience_filter.search(desc_text.text)
        # check_entry_time_end = time.perf_counter()
        # diff1 = (check_entry_time_end - check_entry_time)
        # print("check entry level RT (with bs4: {0}".format(check_entry_time_end - check_entry_time))
        # check_entry_time = time.perf_counter()
        response = requests.get(job_description_url)
        check = experience_filter.search(response.text)
        # check_entry_time_end2 = time.perf_counter()
        # print("check entry level RT (without bs4: {0}".format(check_entry_time_end2 - check_entry_time))
        # diff2 = (check_entry_time_end2 - check_entry_time)
        # if diff1 < diff2:
        #     print("with bs4 faster by {0}s".format(diff2 - diff1))
        # else:
        #     print("without bs4 faster by {0}s".format(diff1 - diff2))
        if not check:
            return True, job_description_url
        # print("experience requirement found: " + check.group())
    # except:
    #     print("check_entry_level_job() ex")

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


# def parse_input(input):
#
#     if len(input) < 5:
#         return None
#
#     try:
#         input = str(val).lower().strip().replace(' ', '').split(',')
#         return input
#     except:
#         print("failed to parse " + input)
#         return None

if __name__ == "__main__":

    # website = []
    # titles = []
    # location = []
    # print("NOTICE: For multiple values separate entries by a comma.")
    # val = input("Enter website to search from (indeed): ")
    # website = parse_input(val)
    # if val == None:
    #     website = default_websites
    # val = input("Enter job title(s): ")
    # titles = parse_input(val)
    # if val == None:
    #     titles = job_titles
    # val = input("Enter location(s): ")
    # location = parse_input(val)
    # if val == None:
    #     location = search_locations
    # find_jobs(website, titles, location)
    
    find_jobs("indeed", job_titles, search_locations)
    dataframe.drop_duplicates(subset=None, keep="first", inplace=True)
    dataframe.to_csv("test.csv", columns=cols)