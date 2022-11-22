from worker import Manager, Worker
from server import User
from db import Database
import datetime
import threading
import time
import sys
import argparse

def generate_path(is_sunday):
    global alert, alert_message
    if not is_sunday:
        alert = True
        alert_message = "Path cannot be generated now. Please try after Sunday 00:00:00"
        #return redirect('/route_planning')
        return None

    today = datetime.datetime.today()
    next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
    last_monday = today + datetime.timedelta(days=-today.weekday(), weeks=0)
    dates = []
    for i in range(7):
        dates.append((next_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))

    workers = user.get_all_userdetails()
    worker_timesheet = []
    total_worker_morning = [[],[],[],[],[],[],[]]
    total_worker_afternoon = [[],[],[],[],[],[],[]]

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
                total_worker_morning[i] = total_worker_morning[i] + [worker[1]]
            else:
                present_morning.append((dates[i],False))
            if dates[i] in dates_in_timesheet_afternoon:
                present_afternoon.append((dates[i],True))
                total_worker_afternoon[i] = total_worker_afternoon[i] + [worker[1]]
            else:
                present_afternoon.append((dates[i],False))
        worker_timesheet.append((worker, present_morning, present_afternoon))
    
    if not user.generate_path(dates, total_worker_morning, total_worker_afternoon):
        alert = True
        alert_message = "Path already generated for next week"
        return None
    alert = True
    alert_message = "Path generation started. Please check after 5 minutes"
    return None


if __name__ == "__main__":
    #Take arguments from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', help='Email of the user')
    parser.add_argument('--is_sunday', help='Boolean value to check if overtime request can be raised', default=True)
    
    db = Database()
    user = Manager(db, parser.parse_args().email)

    generate_path(parser.parse_args().is_sunday)
    
