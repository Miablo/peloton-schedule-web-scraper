from itertools import tee, islice, chain

import os.path
import re as r
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdrivermanager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ExpectedConditions
from selenium.webdriver.common.by import By

import time
import datetime as DateTime
from datetime import date

"""
Created on Tue Apr 25 18:45:37 2017
Copyright 2017 Chase Clarke cfclarke@bu.edu

"""

"""

Modified Wed Sep 7 08:45PM 2022
By: Mio Diaz
Program requires python@3.10.*

"""

timeZone = "\'America/New_York\'"

ride_sample_data = ['SATURDAY, SEPTEMBER 10\n8:00 AM\nLIVE\nINTERMEDIATE\n20 min Full Body Strength\nROBIN ARZÓN · STRENGTH\n6:00 PM\nINTERMEDIATE\n30 min AFO Upper Body Strength: Muse\nANDY SPEER · STRENGTH\nYOU’RE IN']

#### TODO ######
### https://app.swaggerhub.com/apis/DovOps/peloton-unofficial-api/
## look into unofficial api to determine if i can grab class schedule that way
## to remove selenium dependency, etc. 

def previous_and_next(some_iterable):
    """

    Parameters
    ----------
    data : list, required
        data gathered during website scrap


    Returns
    -------
    list
        a list of strings used that are the header columns
    """
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])

    return zip(prevs, items, nexts)

def calc_end_time(duration, hour, minutes):
    """

    Parameters
    ----------
    duration : int, required
        duration of class
    hour : string, required
        hour class begins 
    minutes : string, required
        minutes class begins 

    Returns
    -------
    string
        end time string calculated using duration and start time hour / minutes
    """

    if int(hour) <= 23:
        if int(duration) < 60:
            return str(str(hour) + ":" + str(int(minutes) + int(duration)))
        elif int(duration) == 60:
            return str(str(hour + 1) + ":" + str(int(minutes) + (duration - 60)))
    elif int(hour) == 24 and int(duration) == 60:
        return str(str(1) + ":" + minutes)

    return None


def isMonth(month):
    """

    Parameters
    ----------
    data : list, required
        data gathered during website scrap

    Returns
    -------
    list
        a list of strings used that are the header columns
    """
    match month:
        case "JANUARY": 
            return 1 
        case "FEBURARY": 
            return 2 
        case "MARCH": 
            return 3 
        case "APRIL": 
            return 4
        case "MAY": 
            return 5 
        case "JUNE": 
            return 6 
        case "JULY": 
            return 7 
        case "AUGUST": 
            return 8 
        case "SEPTEMBER": 
            return 9 
        case "OCTOBER": 
            return 10 
        case "NOVEMBER": 
            return 11
        case "DECEMBER": 
            return 12
        case default:
            return 0

## Create ISO time format
# >>> from datetime import datetime, timezone

# >>> datetime(2019, 5, 18, 15, 17, 8, 132263).isoformat()
# datetime(year, month, day, hours, minutes, seconds, microseconds)

# '2019-05-18T15:17:08.132263'
# >>> datetime(2019, 5, 18, 15, 17, tzinfo=timezone.utc).isoformat()
# '2019-05-18T15:17:00+00:00'

def convert_to_military_time(time):
    """

    Parameters
    ----------
    time : string, required
        time string found using pattern matching

    Returns
    -------
    string
        the updated string with the new hour replaced in the first element
    """
    return time.replace(time[0], str(int(time[0]) + 12))

def login(loginInfo):
    """Prompts user to enter username and password for their peloton account in the CLI and stores the data in global variables to be used by the scrapper

    Parameters
    ----------
    data : list, required
        data gathered during website scrap

    Returns
    -------
    list
        a list of strings used that are the header columns
    """
    global username_password

    print("#--------------------------------------------#")
    print("Enter your",loginInfo,"login information: ")
    USERNAME = input('Username: ')
    PASSWORD = getpass.getpass('Password:') #getpass makes it more secure as noone can see it being typed
    print("#--------------------------------------------#")
    print("")
    username_password = [USERNAME, PASSWORD]

    if len(username_password) != 0:
        print("Password and username stored successfully")

    return [USERNAME, PASSWORD]

def get_pelo_data(credentials): 
    """

    Parameters
    ----------
    data : list, required
        data gathered during website scrap
    
    Returns
    -------
    list
        a list of strings used that are the header columns
    """
    USERNAME = credentials[0]
    PASSWORD = credentials[1]
    changed_credentials = []
    return_list = []
    temp_url = ""
    login_url = "https://auth.onepeloton.com/login"
    successful_login_url ="https://members.onepeloton.com/schedule/cycling"
    is_logged_in = False

    print("Logging in. Allow up to 30s due to exception handling.")
    #logging into the peloton website using a automated Google Chrome window
   
    #location of automated Chrome exe file
    path = ("/Users/miablo/Downloads/chromedriver")
    s = Service(path)
    driver = webdriver.Chrome(service=s)

    driver.set_page_load_timeout(30)
    driver.get(login_url) #url
    driver.maximize_window()

    driver.implicitly_wait(10)

    driver.find_element("name", "usernameOrEmail").send_keys(USERNAME) #entering the username
    driver.find_element("name", "password").send_keys(PASSWORD) #entering the password

    WebDriverWait(driver, 10).until(ExpectedConditions.element_to_be_clickable((By.XPATH, "//div[@id='__next']/section/div/div/form/button"))).click()

    time.sleep(5)

    temp_url = driver.current_url

    while is_logged_in == False:
        try:
            time.sleep(5)

            print(login_url)
            print(temp_url)

            if (login_url in temp_url): #checking if the login was successful
                driver.quit()

                print("\nIncorrect username or password. Please try again.")
                changed_credentials = login("correct pelo")
                USERNAME = changed_credentials[0]
                PASSWORD = changed_credentials[1]
                print("Logging in. Allow up to 30s due to exception handling.")

                driver = webdriver.Chrome(service=s)

                driver.set_page_load_timeout(30)
                driver.get(login_url) #url

                driver.implicitly_wait(20)
                driver.find_element("name", "usernameOrEmail").send_keys(USERNAME) #entering the username
                driver.find_element("name", "password").send_keys(PASSWORD) #entering the password

                WebDriverWait(driver, 10).until(ExpectedConditions.element_to_be_clickable((By.XPATH, "//div[@id='__next']/section/div/div/form/button"))).click() #clicking the login button

                time.sleep(5)

                temp_url = driver.current_url

            else:
                print("Login successful!\n")
                is_logged_in = True

        except NoSuchElementException:
            print("Login successful!\n")
            is_logged_in = True

    WebDriverWait(driver, 5).until(ExpectedConditions.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/schedule')]"))).click()

    WebDriverWait(driver, 7).until(ExpectedConditions.element_to_be_clickable((By.XPATH, "//div[@id='categories']/nav/div/div/a[2]"))).click()

    # # find all the dates and store that data for use later
    element_id_timestamp = str(get_unix_time())

    driver.find_element("name", "week-0")
    # loop through week-0 div and get dates
    for i in range(0,7): 
        temp_var =  driver.find_element("name", element_id_timestamp) 
        return_list.append(temp_var.text)
        # find timestamp for the next day aka add 24hours to current
        element_id_timestamp = str(int(element_id_timestamp) + 86400)

    driver.find_element("name", "week-1")
    # loop through week-1 div and get dates
    for i in range(0,7): 
        # alway calculate day that starts at 4 GMT
        temp_var =  driver.find_element("name", element_id_timestamp) 
        return_list.append(temp_var.text)
        # find timestamp for the next day aka add 24hours to current
        element_id_timestamp = str(int(element_id_timestamp) + 86400)
        
    driver.quit() #quitting the online session
    return return_list

def get_unix_time():
    """Finds the unix timestamp representation timestamp is required to find all the days in the calendar using the scrapper

    Returns
    -------
    string
        unix timestamp for the day starting at 00:00
    """
    date_time = date.today()
    unix_time = DateTime.datetime(date_time.year, date_time.month, date_time.day, 00, 00)
    element_id_timestamp = str(time.mktime(unix_time.timetuple()))[:10]

    return element_id_timestamp

def parse_event_data(data):
    """Parses the data retrieved for each object in the returned list, splits the string into components and assigns the correct component result to the appropriate response body property in order to build the calendar event {} response body

    Parameters
    ----------
    data : list, required
        data gathered during website scrap

    """
    global month, day, year, mins, time_of_day, length_of_class, summary, class_type,class_title,start_time, end_time, duration

    # duration = 0
    # hour = 0
    # mins = 0
    # time_of_day = ""
    # length_of_class = ""
    # summary = ""
    # class_type = ""
    # class_title = ""
    # start_time = ""
    # end_time = ""

    for x in data:
        # split line at middle dot char
        lines = x.split(chr(int(0x00B7)))
        for line in lines:
            class_string = line.split()

            # parse data and build event properties
            for previous, current, after in previous_and_next(class_string):
                # build numeric date
                if isMonth(current):
                    month = isMonth(current)
                    day = after
                    year = date.today().year
                    
                if(r.match(r"\d{1,2}:\d\d", current) != None):

                    digits = current.split(':')
                    hour = digits[0]
                    minutes = digits[1]
                    time_of_day = after

                    if after == "PM":
                        start_time = convert_to_military_time(current) + " " + after
                        hour = start_time.split(':')[0]

                    else:
                        start_time = current + " " + after

                    
                if current.isnumeric() and isMonth(previous):
                    day = current

                if current.isnumeric() and "min" == after:
                    duration = current
                    length_of_class = str(current) + " " + after
                    summary = line.split(previous)[1]
                 
                    if hour != None and duration != None:
                        end_time = calc_end_time(duration, hour, minutes)

        calendar_api_call()

        #instead of return list we can return event body and then have the google api use this event body to create the calendar invite

def calendar_api_call():
    """

    """
    #start of google API code
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        new_cal_event(service)
        # now = DateTime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        # print('Getting the upcoming 10 events')

        # events_result = service.events().list(calendarId='primary', timeMin=now,
        #                                       maxResults=10, singleEvents=True,
        #                                       orderBy='startTime').execute()
        # events = events_result.get('items', [])

        # if not events:
        #     print('No upcoming events found.')
        #     return

        # # Prints the start and name of the next 10 events
        # for event in events:
        #     start = event['start'].get('dateTime', event['start'].get('date'))
        #     print(start, event['summary'])

    except HttpError as error:
        print('An error occurred: %s' % error)

### TODO
## Research google api
## determine how build event for calendar event
## create function to pull duration of class and time of class to create end_time var
## determine what part will go into the event name ++ summary 
###
## https://developers.google.com/calendar/api/v3/reference
def new_cal_event(service): 
    """


    """
    event = {
      'summary': summary,
      'start': {
        'dateTime': start_time,
        'timeZone': 'GMT-03:00',
      },
      'end': {
        'dateTime': end_time,
        'timeZone': 'GMT-03:00',
      },
      'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=2'
      ],
      'reminders': {
        'useDefault': False,
        'overrides': [
          {'method': 'email', 'minutes': 24 * 60},
          {'method': 'popup', 'minutes': 10},
        ],
      },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()

#executing the functions
# credentials = login("Peloton") #getting username and password
# data = get_pelo_data(credentials) #scraping the website
parse_event_data(ride_sample_data)

print("\nYour schedule has been updated. Check your google calendar.\n")
