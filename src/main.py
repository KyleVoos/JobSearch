from src.job_search_scraper import JobSearchScraper
import src.User_Input.user_input as usr_input
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd


def start_queries(user_input_vals):
    """
    Function that starts each of the job title/location queries after the user has finished entering input.
    For each job title/location combination a new task is created that is executed by a thread from the
    thread pool. (for now, changing in the future) When the tasks have completed all results added to a pandas
    dataframe.

    Args:
        user_input_vals (InputData object): Instance of InputData holding all the values entered by the user

    Returns:
    """
    with ThreadPoolExecutor() as executor:
        for job in user_input_vals.get_job_titles():
            for loc in user_input_vals.get_locations():
                scraper_instance = JobSearchScraper(job, loc, user_input_vals.get_title_filters(),
                                                    user_input_vals.get_search_filter(loc))
                processes.append(executor.submit(scraper_instance.get_indeed_jobs))

    job_ids_set = set()

    for task in as_completed(processes):
        data = task.result()
        for entry in data:
            if entry[0] not in job_ids_set:
                job_ids_set.add(entry[0])
                dataframe.loc[len(dataframe)] = entry


if __name__ == "__main__":

    cols = ['Job_ID', 'Job_Title', 'Location', 'Company', 'Date', 'Salary', 'Description', 'url']
    dataframe = pd.DataFrame(columns=cols)
    processes = []
    input_vals = usr_input.get_user_input()
    start_queries(input_vals)
