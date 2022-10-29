import mysql.connector
from mysql.connector import errorcode
import sys
import os
import time
from datetime import datetime

#Create a class database to connec to MYSQL database
class Database:

    def __init__(self):
        self.error = None
        #Connect to database
        try:
            #mongodb+srv://root:<password>@cluster0.jkh5rrc.mongodb.net/?retryWrites=true&w=majority
            self.cnx = mysql.connector.connect(user='root', password='password', 
                            host='localhost', database='collectx')
            print("Connected to database")

            self.cursor = self.cnx.cursor()
            if not self.cnx.is_connected():
                print("Not connected to database")
                sys.exit(1)
            self.cursor = self.cnx.cursor()
            #Check if all the tables exist
            self.tables = ["Person", "MCD", "Timesheet", "worker_update_request", "recieve_overtime", "overtime_accepted", "BaseDisplay", "Bins", "Route","EdgeBetween2Bin"]
            self.tables = [x.lower() for x in self.tables]
            if not self.check_table(self.tables):
                print("Tables not found")
                #Create new tables
                if not self.create_table():
                    print("Failed to create tables")
                    sys.exit(1)
                print("Tables created")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        
        #self.cursor = self.cnx.cursor()
        #Check if all the tables exist
        if not self.check_table(self.tables):
            print("Table does not exist")
            sys.exit(1)

    def execute(self, query, args=None):
        try:
            if args is None:
                
                self.cursor.execute(query)
            else:
                
                self.cursor.execute(query, args)
        except mysql.connector.Error as err:
            self.error = err
            print(err)
            print("Error")
            print(query, args)

    #Check if tables exists
    def check_table(self, table_name: list) -> bool:
        self.cursor.execute("SHOW TABLES")
        #Create a list of all the tables
        tables = [x[0].lower() for x in self.cursor.fetchall()]
        #Check if all the table name given in table_name exist in the database
        for table in table_name:
            if table not in tables:
                print(table)
                return False
        return True

    #Creating new tables
    def create_table(self):
        #Delete all old tables if they exist
        try:
            for table in self.tables:
                self.execute("DROP TABLE IF EXISTS {}".format(table))
            print("All tables deleted")
        except mysql.connector.Error as err:
            print("Failed to drop table: {}".format(err))
            sys.exit(1)
        #Create new tables
        try:
            #Create Person table
            self.execute("CREATE TABLE Person(Name VARCHAR(100), EmailID VARCHAR(150) PRIMARY KEY, Phone_Number BIGINT, Role VARCHAR(1))")
            #Create MCD table
            self.execute("CREATE TABLE MCD(EmailID VARCHAR(150) PRIMARY KEY, Role VARCHAR(255))")
            #Create Timesheet table
            #Timesheet refers to table Person(EmailID) as foreign key
            self.execute("CREATE TABLE Timesheet(EmailID VARCHAR(150), Date DATE, start_time TIME, end_time TIME, " + 
                                "PRIMARY KEY (EmailID, Date, start_time, end_time))")
            #Create worker_update_request table
            self.execute("CREATE TABLE worker_update_request(valid VARCHAR(1), EmailID VARCHAR(150), Request_type VARCHAR(1), " 
                + "approved_by_mg1 VARCHAR(150), approved_by_mg2 VARCHAR(150), PRIMARY KEY (valid, EmailID, Request_type))")
            #Create recieve_overtime table
            self.execute("CREATE TABLE recieve_overtime(valid VARCHAR(1), overtime_id INT AUTO_INCREMENT PRIMARY KEY, date DATE, start_time TIME, end_time TIME, number_of_required_worker INT, accepted_till_now INT)")
            #Create overtime_accepted table
            self.execute("CREATE TABLE overtime_accepted(overtime_id INT, EmailID VARCHAR(150), " +
                "PRIMARY KEY (overtime_id, EmailID))")
            #Create Bins table
            self.execute("CREATE TABLE Bins(binID INT PRIMARY KEY, Name char(150), Longitude varchar(30), Latitude varchar(30))")
            #Create BaseDisplay table
            self.execute("CREATE TABLE BaseDisplay(date DATE, binID INT, collectionTime TIME)")
            #Create Route table
            self.execute("CREATE TABLE Route(Date DATE, EmailID VARCHAR(150), binID VARCHAR(255), sequence INT)")
            #Create EdgeBetween2Bin
            self.execute("CREATE TABLE EdgeBetween2Bin(binID1 INT, binID2 INT, DISTANCE FLOAT, PRIMARY KEY (binID1, binID2))")
            return True
        except mysql.connector.Error as err:
            print("Error in creating tables")
            print(err)
            return False

    #Add/Remove new worker in Person table
    def add_remove_worker(self, mgr_email: str, w_name: str, w_email: str, w_phone: int, w_role: str, w_add: bool) -> bool:
        #Check if manager exists
        if not self.check_manager(mgr_email):
            self.error = "Manager does not exist"
            print("Manager does not exist")
            return False
        try:
            if w_add:
                #Check if the worker is already present in Person table
                self.execute("SELECT * FROM Person WHERE EmailID = %s", (w_email,))
                if self.cursor.fetchone():
                    self.error = "Worker/Manager already exists"
                    print("Worker already present in Person table")
                    return False
                #Check if the worker is already present in worker_update_request table
                self.execute("SELECT * FROM worker_update_request WHERE valid=1 AND EmailID = %s", (w_email,))
                if self.cursor.fetchone():
                    #If a entry in table exists then check if mrg_id1 is not the same as mgr_email
                    self.execute("SELECT * FROM worker_update_request WHERE valid=1 AND EmailID = %s AND approved_by_mg1 = %s AND approved_by_mg2!= %s AND request_type='a'", (w_email, mgr_email,mgr_email,))
                    if self.cursor.fetchone():
                        self.error = "Request already raised for this worker by the current manager"
                        print("Request already raised for this worker by the current manager")
                        return False
                    
                    # set mgr_id2 = mgr_id and set valid to 0
                    #Then add the person to the persons table
                    self.execute("UPDATE worker_update_request SET approved_by_mg2 = %s, valid = 0 WHERE EmailID = %s", (mgr_email, w_email))
                    self.execute("INSERT INTO Person VALUES (%s, %s, %s, %s)", (w_name, w_email, w_phone, w_role))
                    self.cnx.commit()
                    self.error = None
                    return True

                else:
                    #Add the request in worker_update_request table
                    self.execute("INSERT INTO worker_update_request VALUES(%s, %s, %s, %s, %s)", ('1', w_email, 'a', mgr_email, '0'))
                    self.cnx.commit()
                    self.error = None
                    return True
                
            else:
                #Do similar steps as done for adding for removing a worker
                self.execute("SELECT * FROM Person WHERE EmailID = %s", (w_email,))
                if not self.cursor.fetchone():
                    self.error = "Worker does not exist"
                    print("Worker not present in Person table")
                    return False
                self.execute("SELECT * FROM worker_update_request WHERE valid=1 AND EmailID = %s", (w_email,))
                if self.cursor.fetchone():
                    self.execute("SELECT * FROM worker_update_request WHERE valid=1 AND EmailID = %s AND approved_by_mg1 = %s AND approved_by_mg2!= %s AND request_type='r'", (w_email, mgr_email,mgr_email,))
                    if self.cursor.fetchone():
                        self.error = "Request already raised for this worker by the current manager"
                        print("Request already raised for this worker by this manager")
                        return False
                    self.execute("UPDATE worker_update_request SET approved_by_mg2 = %s, valid = 0 WHERE EmailID = %s", (mgr_email, w_email))
                    self.execute("DELETE FROM Person WHERE EmailID = %s", (w_email,))
                    self.execute("DELETE FROM timesheet WHERE EmailID = %s", (w_email,))
                    self.cnx.commit()
                    self.error = None
                    return True
                else:
                    self.execute("INSERT INTO worker_update_request VALUES(%s, %s, %s, %s, %s)", ('1', w_email, 'r', mgr_email, '0'))
                    self.cnx.commit()
                    self.error = None
                    return True

        except mysql.connector.Error as err:
            print("Error in adding/removing worker")
            print("Error in add_remove_worker")
            print(err)
            return False
            
    #Add/Remove new worker in MCD table
    def add_remove_mcd(self, email: str, role: str, add:bool) -> bool:
        if add:
            #Add the worker in MCD table
            self.execute("INSERT INTO MCD VALUES(%s, %s)", (email, role))
            self.cnx.commit()
            self.error = None
            return True
        else:
            #Remove the worker from MCD table
            self.execute("DELETE FROM MCD WHERE EmailID = %s", (email,))
            self.cnx.commit()
            self.error = None
            return True

    def remove_timesheet(self, email: str, date: str, start_time: str, end_time: str) -> bool:
        #Remove the timesheet of the worker
        date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
        self.execute("DELETE FROM Timesheet WHERE EmailID = %s AND date = %s AND start_time = %s AND end_time = %s", (email, date, start_time, end_time))
        self.cnx.commit()
        self.error = None
        return True

    #Add/Remove new worker in Timesheet table
    def add_timesheet(self, email: str, date: str, start_time: str, end_time: str) -> bool:
        date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
        #Check if the worker is already present in Timesheet table and if email id belongs to worker
        if not self.check_worker(email):
            self.error = "Worker does not exist"
            print("Not a worker")
            return False
        #Check if time entered by worker is clashing with any other entry
        if self.check_timesheet_clash(email, date, start_time, end_time):
            self.error = "Time entered by worker is clashing with other entry"
            print("Time entered by worker is clashing with any other entry")
            return False
        start_time = start_time + ":00"
        end_time = end_time + ":00"
        
        self.execute("INSERT INTO Timesheet VALUES(%s, %s, %s, %s)", (email, date, start_time, end_time))
        self.cnx.commit()
        self.error = None
        return True

    #Check if worker exists in Person table and it's role is W
    def check_worker(self, email: str) -> bool:
        self.execute("SELECT * FROM Person WHERE EmailID = %s AND role = 'W'", (email,))
        if self.cursor.fetchone():
            return True
        return False

    #Check if manager exists in Person table and it's role is M
    def check_manager(self, email: str) -> bool:
        self.execute("SELECT * FROM Person WHERE EmailID = %s AND role = 'M'", (email,))
        if self.cursor.fetchone():
            return True
        return False
    
    #Check if person exist in person table
    def check_person(self, email: str) -> bool:
        self.execute("SELECT * FROM Person WHERE EmailID = %s", (email,))
        try:
            len(self.cursor.fetchone())
            return True
        except:
            return False
   
   #Create overtime request
    def create_overtime_request(self, date: str, start_time: str, end_time: str, number_of_required_worker: str) -> bool:
        #Check if the request is already present in overtime_request table
        self.execute("SELECT * FROM overtime_request WHERE Date = %s AND start_time = %s AND end_time = %s", (date, start_time, end_time))
        if self.cursor.fetchone():
            self.error = "Request already present"
            print("Request already present in overtime_request table")
            return False
        #Add the request in overtime_request table
        self.execute("INSERT INTO overtime_request (valid, date, start_time, end_time, number_of_required_worker, accepted_till_now) VALUES(1, %s, %s, %s, %s, 0)", (date, start_time, end_time, number_of_required_worker))
        self.cnx.commit()
        self.error = None
        return True
    
    #Check if some date, start_time, end_time for a worker is clashing with a already present entry in Timesheet table for that worker
    def check_timesheet_clash(self, email: str, date: str, start_time: str, end_time: str) -> bool:
        #Change date format to "%d-%m-%y"
        #date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
        self.execute("SELECT * FROM Timesheet WHERE EmailID = %s AND Date = %s", (email, date))

        timesheet = self.cursor.fetchall()
        #convert start_time and end_time to datetime object
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()
        for row in timesheet:
            #convert start_time and end_time of each row in Timesheet table to datetime object
            date1 = row[1]
            start_time1 = (datetime.min + row[2]).time()
            end_time1 = (datetime.min + row[3]).time()
            #Check if start_time and end_time of request is clashing with any entry in Timesheet table
            if start_time1 <= start_time <= end_time1 or start_time1 <= end_time <= end_time1:
                return True
        return False

    #Recieve overtime request
    def recieve_overtime_request(self, overtime_id:int, w_email: str, date: str, new_start_time: str, new_end_time: str) -> bool:
        #date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
        
        #First check if worker exists in Person table and it's role is W
        if not self.check_worker(w_email):
            self.error = "Worker does not exist"
            print("Not a worker")
            return False
        #Check if the submitted date, start_time and end_time clashes with it's submitted timesheet
        if self.check_timesheet_clash(w_email, date, new_start_time, new_end_time):
            self.error = "Time entered by worker is clashing with other entry"
            print("Time entered by worker is clashing with any other entry")
            return False
        
        #Check if worker has already accepted the overtime request and exists in overtime_accepted table
        self.execute("SELECT * FROM overtime_accepted where EmailID=%s AND overtime_id=%s", (w_email, overtime_id))
        if not self.cursor.fetchone():
            self.error = "Worker has not accepted the overtime request"
            print("Worker has already accepted the overtime request")
            return False
        #Add the overtime in overtime_accepted
        self.execute("INSERT INTO overtime_accepted VALUES(%s, %s)", (overtime_id, w_email))
        self.cnx.commit()
        #Add the time to timesheet
        new_start_time = new_start_time + ":00"
        new_end_time = new_end_time + ":00"
        self.execute("INSERT INTO Timesheet VALUES(%s, %s, %s, %s)", (w_email, date, new_start_time, new_end_time))
        self.cnx.commit()
        #Increase accepted till now by 1
        self.execute("UPDATE overtime_request SET accepted_till_now = accepted_till_now + 1 WHERE overtime_id = %s", (overtime_id,))
        self.cnx.commit()
        #Check if accepted till now is equal to number of required worker and if yes then update valid to 0
        self.execute("SELECT * FROM overtime_request WHERE overtime_id = %s", (overtime_id,))
        if self.cursor.fetchone()[4] == self.cursor.fetchone()[5]:
            self.execute("UPDATE overtime_request SET valid = 0 WHERE overtime_id = %s", (overtime_id,))
            self.cnx.commit()
        self.error = None
        return True

    def get_information_all_workers(self):
        self.execute("SELECT * FROM Person WHERE role = 'W'")
        details = self.cursor.fetchall()
        #Putting details into dictionary
        details_dict = {}
        for i in details:
            details_dict[i[1]] = i
        return details_dict

    def get_information_all_managers(self):
        self.execute("SELECT * FROM Person WHERE role = 'M'")
        details = self.cursor.fetchall()
        #Putting details into dictionary
        details_dict = {}
        for i in details:
            details_dict[i[1]] = i
        return details_dict

    def get_information_all_overtime_requests(self):
        self.execute("SELECT * FROM recieve_overtime")
        details = self.cursor.fetchall()
        #Putting details into dictionary
        details_dict = {}
        for i in details:
            details_dict[i[1]] = i
        return details_dict

    def get_information_all_timesheets(self):
        self.execute("SELECT * FROM Timesheet")
        details = self.cursor.fetchall()
        #Putting details into dictionary
        details_dict = {}
        for i in details:
            details_dict[i[0]] = i
        return details_dict

    def get_information_all_overtime_accepted(self) -> dict:
        self.execute("SELECT * FROM overtime_accepted")
        details = self.cursor.fetchall()
        #Putting details into dictionary
        details_dict = {}
        for i in details:
            details_dict[i[0]] = i
        return details_dict

    def get_all_bins(self) -> dict:
        self.execute("SELECT * FROM bins")
        details = self.cursor.fetchall()
        #Putting details into dictionary
        details_dict = {}
        for i in details:
            details_dict[i[0]] = i[1:]
        return details_dict

    def get_all_edges(self) -> list:
        self.execute("SELECT * FROM edges")
        details = self.cursor.fetchall()
        details_list = []
        for i in details:
            details_list.append(i)
        return details_list

    def insert_bin(self, binID: int, binName: str, lon="", lat=""):
        try:
            self.execute("INSERT INTO bins VALUES(%s, %s, %s, %s)", (binID, binName, lon, lat))
            self.cnx.commit()
            self.error = None
            return True
        except mysql.connector.Error as err:
            self.error = "Error while inserting a new bin"
            print("Something went wrong while inserting into bins: {}".format(err))
            print(err)
            return False
    
    def insert_edge(self, binID1: int, binID2: int, distance: int):
        try:
            self.execute("INSERT INTO EdgeBetween2Bin VALUES(%s, %s, %s)", (binID1, binID2, distance))
            self.cnx.commit()
            return True
        except mysql.connector.Error as err:
            self.error = "Error while inserting a new edge"
            print("Something went wrong while inserting into EdgeBetween2Bin: {}".format(err))
            print(err)
            return False
    
    def get_all_routes(self) -> dict:
        self.execute("SELECT * FROM route")
        details = self.cursor.fetchall()
        #Putting details into list
        details_list = {}
        for i in details:
            details_list.append(i)
        return details_list
    
    def get_route_for_wid(self, emailId: str)-> list:
        self.execute("SELECT * FROM route WHERE EmailID = %s", (emailId,))
        details = self.cursor.fetchall()
        details_list = {}
        for i in details:
            details_list.append(i)
        return details_list

    def get_route_for_wid_with_date(self, emailId: str, date: str) -> list:
        self.execute("SELECT * FROM route WHERE EmailID = %s AND Date = %s", (emailId, date))
        details = self.cursor.fetchall()
        details_list = {}
        for i in details:
            details_list.append(i)
        return details_list
    
    def get_route_for_date(self, date: str) -> list:
        self.execute("SELECT * FROM route WHERE Date = %s", (date,))
        details = self.cursor.fetchall()
        #Putting details into list
        details_list = {}
        for i in details:
            details_list.append(i)
        return details_list

    #Get all details for email from Person table
    def get_details_for_email(self, email: str) -> list:
        self.execute("SELECT * FROM Person WHERE EmailID = %s", (email,))
        details = self.cursor.fetchall()
        return details

    #Get person name for email from Person table
    def get_name(self, email: str) -> str:
        self.execute("SELECT * FROM Person WHERE EmailID = %s", (email,))
        details = self.cursor.fetchall()
        return details[0][0]

    #Get person role for email from Person table
    def get_role(self, email: str):
        self.execute("SELECT * FROM Person WHERE EmailID = %s", (email,))
        details = self.cursor.fetchall()
        try:    
            return details[0][3]
        except:
            return None

    #Get person phone number for email from Person table
    def get_phone(self, email: str) -> str:
        self.execute("SELECT * FROM Person WHERE EmailID = %s", (email,))
        details = self.cursor.fetchall()
        return details[0][2]

    #Update details in Person table
    def update_details(self, email: str, name: str, phone: str) -> bool:
        try:
            self.execute("UPDATE Person SET Name = %s, Phone_number = %s WHERE EmailID = %s", (name, phone, email))
            self.cnx.commit()
            self.error = None
            return True
        except Exception as e:
            self.error = "Error while updating details"
            print(e)
            return False

    #Get all details for email from Timesheet table
    def get_timesheet_for_email(self, email: str) -> list:
        self.execute("SELECT * FROM Timesheet WHERE EmailID = %s", (email,))
        details = self.cursor.fetchall()
        details_list = []
        for i in details:
            details_list.append(i[1:])
        return details_list

    #Get all valid overtime requests and whose date is after now present in recieve_overtime table
    def get_available_overtime_worker(self) -> list:
        self.execute("SELECT * FROM recieve_overtime WHERE valid = 1 AND date > NOW()")
        details = self.cursor.fetchall()
        details_list = []
        for i in details:
            details_list.append(i[1:5])
        return details_list

    #Get all pending request in worker_update_request
    def get_pending_request_by_mgr(self, mgr_email: str) -> list:
        self.execute("SELECT * FROM worker_update_request WHERE valid = 1 AND (approved_by_mg1=%s OR approved_by_mg2 = %s)", (mgr_email,mgr_email,))
        details = self.cursor.fetchall()
        details_list = []
        for i in details:
            details_list.append(i)
        return details_list
    
    #Get all pending request in worker_update_request not raised by current mgr_email
    def get_pending_request_not_by_mgr(self, mgr_email: str) -> list:
        self.execute("SELECT * FROM worker_update_request WHERE valid = 1 AND approved_by_mg1!=%s", (mgr_email,))
        details = self.cursor.fetchall()
        details_list = []
        for i in details:
            details_list.append(i)
        return details_list

    #Get all valid overtime requests and whose date is after now present in recieve_overtime table
    def get_available_overtime_manager(self) -> list:
        self.execute("SELECT * FROM recieve_overtime WHERE valid = 1 AND date > NOW()")
        details = self.cursor.fetchall()
        details_list = []
        for i in details:
            details_list.append(i)
        return details_list
