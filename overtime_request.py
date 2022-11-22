from worker import Manager, Worker
from server import User
from db import Database
import datetime
import threading
import time
import sys
import argparse

def generate_overtime(valid_overtime_request_raise_manager):
    #if current_user.user.role != "m":
    #    return redirect('/index')
    global alert, alert_message
    if not valid_overtime_request_raise_manager:
        alert = True
        alert_message = "Overtime request cannot be raised now. Please try before {t}:00:00".format(t=t)
        return None
        #return redirect('/route_planning')
    
    today = datetime.datetime.today()
    next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
    last_monday = today + datetime.timedelta(days=-today.weekday(), weeks=0)
    #Create list of dates for next week and append the dates as string
    dates = []
    for i in range(7):
        dates.append((next_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))
    #Get all the workers
    workers = user.get_all_userdetails()
    #For each worker get the timesheet
    worker_timesheet = []
    total_worker_morning = [0,0,0,0,0,0,0]
    total_worker_afternoon = [0,0,0,0,0,0,0]
    #Create for loop overs keys in workers
    for worker in workers:
        worker = worker[0:2]
        present_morning = []
        present_afternoon = []
        timesheet = Worker(Database(), worker[1]).get_timesheet()
        dates_in_timesheet_morning = [x[0].strftime("%d-%m-%Y") for x in timesheet if x[1]== datetime.timedelta(hours=8)]
        dates_in_timesheet_afternoon = [x[0].strftime("%d-%m-%Y") for x in timesheet if x[1]== datetime.timedelta(hours=14)]
        for i in range(7):
            if dates[i] in dates_in_timesheet_morning:
                present_morning.append((dates[i],True))
                total_worker_morning[i] += 1
            else:
                present_morning.append((dates[i],False))
            if dates[i] in dates_in_timesheet_afternoon:
                present_afternoon.append((dates[i],True))
                total_worker_afternoon[i] += 1
            else:
                present_afternoon.append((dates[i],False))
        worker_timesheet.append((worker, present_morning, present_afternoon))

    if not user.raise_overtime_request(dates, total_worker_morning):
        alert = True
        alert_message = "Overtime request already raised for next week"
        return None
        #return redirect('/route_planning')
    #requirement = current_user.user.raise_overtime_request(dates, total_worker_morning)
    #current_user.user.raise_overtime_request(dates, total_worker_morning)
    alert = True 
    alert_message = "Overtime request raised successfully"
    #return redirect('/route_planning')
    return None

if __name__ == "__main__":
    #Take arguments from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', help='Email of the user')
    parser.add_argument('--valid_overtime_request_raise_manager', help='Boolean value to check if overtime request can be raised', default=True)
    
    db = Database()
    user = Manager(db, parser.parse_args().email)
    generate_overtime(True)