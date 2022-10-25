import sys
from db import Database
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
#Refer to Database class in db.py
class Person:
    def __init__(self, db, email):
        self.db = db
        self.email = email
        self.get_information()
        if self.name==None:
            self.update_details()
    
    @staticmethod
    def get_role(db, email: str):
        return db.get_role(email)
    
    @staticmethod
    def check_exist(db, email:str):
        return db.check_person(email)
    
    def update_details(self, name: str, phone: str):
        self.db.update_details(self.email, name, phone)
        self.get_information()
        return
    
    def get_information(self):
        #If person with email doesn't exist raise error
        if not self.exists():
            print('Person does not exist')
            sys.exit(1)
        #Get person's name
        self.name = self.db.get_name(self.email)
        #Get person's phone number
        self.phone = self.db.get_phone(self.email)
        #Get person's address
        self.role = self.db.get_role(self.email)

    #Check if person exists
    def exists(self):
        return self.db.check_person(self.email)
    
    def update_information(self, name, phone):
        self.db.update_details(self.email, name, phone)
        self.get_information()
        return

class Worker(Person):
    def __init__(self, db, email):
        super().__init__(db, email)
        if self.name == None:
            self.ask_details()

    def update_timesheet(self, date: str, start_time: datetime, end_time: datetime):
        #Check if date is future date
        if date > datetime.now().strftime('%Y-%m-%d'):
            print('Date cannot be future date')
            return
        #Check if start time is after end time
        if start_time > end_time:
            print('Start time cannot be after end time')
            return
        #Check if start time is before 6am
        if start_time.hour < 6:
            print('Start time cannot be before 6am')
            return False
        #Check if end time is after 10pm
        if end_time.hour > 12:
            print('End time cannot be after 2pm')
            return True

        #Format start_time and end_time to string
        date = date.strftime('%Y-%m-%d')
        start_time = start_time.strftime('%H:%M:%S')
        end_time = end_time.strftime('%H:%M:%S')
        #Check if there is a clash
        if self.db.check_timesheet_clash(self.email, date, start_time, end_time):
            print('Timesheet clash')
            return False
        #Update timesheet
        self.db.update_timesheet(self.email, date, start_time, end_time)
        return True

    def get_timesheet(self):
        return self.db.get_timesheet_for_email(self.email)

    def get_available_overtime(self):
        return self.db.get_available_overtime_worker(self.email)
    
    def submit_overtime(self, overtime_id, date, start_time, end_time):
        #Check if date is future date
        if date > datetime.now().strftime('%Y-%m-%d'):
            print('Date cannot be future date')
            return
        #Check if start time is after end time
        if start_time > end_time:
            print('Start time cannot be after end time')
            return
        #Check if start time is before 6am
        if start_time.hour < 6:
            print('Start time cannot be before 6am')
            return False
        #Check if end time is after 10pm
        if end_time.hour > 14:
            print('End time cannot be after 2pm')
            return True
        
        #Format start_time and end_time to string
        date = date.strftime('%Y-%m-%d')
        start_time = start_time.strftime('%H:%M:%S')
        end_time = end_time.strftime('%H:%M:%S')
        #Check if there is a clash
        if self.db.check_timesheet_clash(self.email, date, start_time, end_time):
            print('Timesheet clash')
            return False
        #Update timesheet
        self.db.recieve_overtime_request(overtime_id, self.email, date, start_time, end_time)
        return True


    def update_details(self, name: str, phone: int):
        self.db.update_details(self.email, name, phone)
        self.get_information()


    
class Manager(Person):
    def __init__(self, db, email):
        super().__init__(db, email)
        if self.name == None:
            self.ask_details()

    def get_all_userdetails(self):
        return self.db.get_information_all_workers().values()
    
    def pending_request_raised_by_self(self):
        return self.db.get_pending_request_by_mgr(self.email)
    
    def pending_request_raised_by_others(self):
        return self.db.get_pending_request_not_by_mgr(self.email)

    def update_worker(self, w_email, request_type):
        return self.db.add_remove_worker(self.email, "", w_email, 0, "w", True if request_type == "add" else False)
