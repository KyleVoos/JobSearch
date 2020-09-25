class InputData:
    """


    """
    locations = []
    job_titles = []
    title_filter_terms = []
    search_filters = {}
    ouput_type = None

    def add_job_titles(self, titles: [str]):
        self.job_titles = titles

    def get_job_titles(self):
        return self.job_titles

    def add_search_filter(self, key: str, values: {}):
        self.search_filters[key] = values

    def get_search_filter(self, key: str):
        return self.search_filters[key]

    def add_locations(self, loc: [str]):
        self.locations = loc

    def get_locations(self):
        return self.locations

    def add_title_filter_terms(self, filter_terms: [str]):
        self.title_filter_terms = filter_terms

    def get_title_filters(self):
        return self.title_filter_terms


def parse_input(user_input: str):

    user_input = user_input.strip()

    if not user_input:
        return None

    return user_input


def get_job_titles():

    job_titles = []
    print("Enter job search title(s):")

    while True:
        temp = input()
        if temp:
            temp = ' '.join(temp.split())
            if len(temp) > 0:
                job_titles.append(temp)
        elif not temp and len(job_titles) > 0:
            break

    return job_titles


def get_locations(input_data):

    locations = []
    print("Enter location(s):")

    while True:
        temp = input()
        if temp:
            temp = temp.strip()
            if len(temp) > 0:
                locations.append(temp)
                get_search_filters(temp, input_data)
        elif not temp and len(locations) > 0:
            break

    return locations


def get_search_filters(location: str, input_data: InputData):

    filters = {'l': location}

    if location.lower().find("state") == -1:
        cont = input("Search filters for {0}? (y/n) ".format(location))
        if cont == "Y" or cont == "y":
            print("Date Posted Filter:")
            print("1) Last 24 hours")
            print("2) Last 3 days")
            print("3) Last 7 days")
            print("4) Last 14 days")

            selection = [1, 3, 7, 14]

            while True:
                try:
                    num = int(input("Selection: "))
                    if num > 0 and num < 5:
                        filters['fromage'] = selection[num - 1]
                    break
                except ValueError:
                    print("Invalid Input")

            print("Radius Filter:")
            print("1) Exact Location")
            print("2) 5 Miles")
            print("3) 10 Miles")
            print("4) 15 Miles")
            print("5) 25 Miles")
            print("6) 50 Miles")
            print("7) 100 Miles")

            selection = [0, 5, 10, 15, 25, 50, 100]

            while True:
                try:
                    num = int(input("Selection: "))
                    if num > 0 and num < 8:
                        filters['radius'] = selection[num - 1]
                    break
                except ValueError:
                    print("Invalid Input")

    input_data.add_search_filter(location, filters)


def get_title_filters():

    title_filters = []
    print("Enter terms in job titles to exclude (ex. senior):")

    while True:
        temp = input()
        if temp:
            temp = temp.strip()
            if len(temp) > 0:
                title_filters.append(temp.lower())
        else:
            break

    return title_filters


def get_user_input():

    user_input_vals = InputData()

    print("Indeed Job Scrapper by Kyle Voos\n")
    user_input_vals.add_job_titles(get_job_titles())
    user_input_vals.add_locations(get_locations(user_input_vals))
    user_input_vals.add_title_filter_terms(get_title_filters())

    return user_input_vals


def get_output_result_selection():
    print("How would you like to output the results?")
    print("1) Save to csv file")
    print("2) Email csv file to yourself")
    print("3) Store in local MySQL database")

    while True:
        temp = int(input())
        if temp > 0 and temp < 4:
            return temp


def get_csv_filename():
    result = input("Enter a filename to save as: ")

    return result


def get_user_email():
    email = input("Enter your email address: ")

    return email


def get_user_password():
    password = input("Enter you email password (email is sent from yourself to yourself): ")

    return password