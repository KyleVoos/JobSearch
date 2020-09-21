from job_search_scraper import JobSearchScraper
import User_Input.user_input as usr_input
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd


if __name__ == "__main__":

    cols = ['Job_Title', 'Location', 'Company', 'Date', 'Salary', 'Description', 'url']
    dataframe = pd.DataFrame(columns=cols)
    processes = []
    input_vals = usr_input.get_user_input()

    with ThreadPoolExecutor() as executor:
        for job in input_vals.job_titles:
            for loc in input_vals.locations:
                scraper_instance = JobSearchScraper(job, loc, input_vals.title_filter_terms,
                                                    input_vals.search_filters[loc])
                processes.append(executor.submit(scraper_instance.get_indeed_jobs))

    for task in as_completed(processes):
        data = task.result()
        for entry in data:
            dataframe.loc[len(dataframe)] = entry

