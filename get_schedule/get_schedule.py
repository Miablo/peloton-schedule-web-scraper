from __future__ import print_function
from itertools import tee, islice, chain

import os.path

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

import getpass

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

#declaring the variables needed to call new_cal_event
location: ""
summary = ""
start_datetime = ""
end_datetime = ""
description: ""
timeZone = "\'America/New_York\'"

#### TODO ######
### https://app.swaggerhub.com/apis/DovOps/peloton-unofficial-api/
## look into unofficial api to determine if i can grab class schedule that way
## to remove selenium dependency, etc. 
##

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)

def isDay_of_week(arg):
    if "SATURDAY" in arg:
        return True 
    if "SUNDAY" in arg:
        return True
    if "MONDAY" in arg:
        return True 
    if "TUESDAY" in arg:
        return True 
    if "WEDNESDAY" in arg:
        return True 
    if "THURSDAY" in arg:
        return True 
    if "FRIDAY" in arg:
        return True 
    
    return False

def is_part_of_time(arg):
    if "AM" in arg:
        return True
    if "PM" in arg:
        return True 
    if ":" in arg:
        return True

    return False

def isMonth(arg):
    match arg:
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

def convert_to_military_time(arg):
    return arg + 12

ride_sample_data = ['SATURDAY, SEPTEMBER 10\n8:00 AM\nLIVE\nINTERMEDIATE\n20 min Full Body Strength\nROBIN ARZÓN · STRENGTH\n6:00 PM\nINTERMEDIATE\n30 min AFO Upper Body Strength: Muse\nANDY SPEER · STRENGTH\nYOU’RE IN']

def login(loginInfo): #this is the login function
    #loginInfo is a string of what you are logging into
    #userinput of username and password in a secure format
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
#logs into the bu website and pulls all your calendar data
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

    # print(element_id_timestamp)

    driver.find_element("name", "week-0")
    # loop through week-0 div and get dates
    for i in range(0,7): 
        # alway calculate day that starts at 4 GMT
        temp_var =  driver.find_element("name", element_id_timestamp) 
        return_list.append(temp_var.text) #each line is appended to the return_list
        element_id_timestamp = str(int(element_id_timestamp) + 86400)

    driver.find_element("name", "week-1")
    # loop through week-1 div and get dates
    for i in range(0,7): 
        # alway calculate day that starts at 4 GMT
        temp_var =  driver.find_element("name", element_id_timestamp) 
        return_list.append(temp_var.text) #each line is appended to the return_list
        element_id_timestamp = str(int(element_id_timestamp) + 86400)
        
    driver.quit() #quitting the online session
    return return_list


def get_unix_time():
    date_time = date.today()
    unix_time = DateTime.datetime(date_time.year, date_time.month, date_time.day, 00, 00)
    element_id_timestamp = str(time.mktime(unix_time.timetuple()))[:10]

    return element_id_timestamp

def parse_event_data(data): #simplifies the data that get_pelo_data returns

    return_list = ""
    month = 0
    day = 0
    duration = 0
    time_of_day = ""

    for x in data:
        line = x.split()
        # parse data and build event properties
        for previous, current, after in previous_and_next(line):
            # skip day of week
            if isDay_of_week(current):
                if isMonth(after):
                    month = isMonth(after)
                    day = current
            # find time 
            if is_part_of_time(current):
                # maybe find the time and then am / pm 
                # use this to convert the value to the appropriate format?
                # return correct value that can be added to the var require for the response body for the event?
                if is_part_of_time(after):
                    return_list = current + " " + after
                    if after == "AM":
                        print(return_list)
                    if after == "PM":
                        print("PM")

            if current.isnumeric() and isMonth(previous):
                day = current

            if current.isnumeric() and "min" == after or "hr" == after:
                duration = current
                time_of_day = str(current) + " " + after
                print(duration)
                print(time_of_day)

        #instead of return list we can return event body and then have the google api use this event body to create the calendar invite
    return return_list


def calendar_api_call():

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
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 10 events')

        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])

    except HttpError as error:
        print('An error occurred: %s' % error)

### TODO
## Research google api
## determine how build event for calendar event
## create function to pull duration of class and time of class to create end_time var
## determine what part will go into the event name ++ summary 
###
## https://developers.google.com/calendar/api/v3/reference
def new_cal_event(event): 
    # Build event response body for calendar event for each class in schedule
    event = {
      'summary': summary,
      'location': location,
      'description': description,
      'start': {
        'dateTime': start_datetime,
        'timeZone': timeZone,
      },
      'end': {
        'dateTime': end_datetime,
        'timeZone': timeZone,
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
# print(data)
data = parse_event_data(ride_sample_data) #simplifying data
# calendar_api_call()

print("\nYour schedule has been updated. Check your google calendar.\n")
