import sys
from db import Database
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
import openrouteservice
from openrouteservice import convert
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cvxpy as cp
import folium
from tqdm import tqdm
from concurrent import futures
import random
morning_working_hours = 4
afternoon_working_hours = 3
city_average_speed = 20 # km/h
#Refer to Database class in db.py
class Person:
    def __init__(self, db, email=None):
        self.db = db
        self.name = None
        if email==None:
            self.user = None
            self.role = None
        else:
            
            self.email = email
            self.get_information()
            if self.name==None:
                self.update_details()
    
    @staticmethod
    def get_role(db, email: str):
        try:
            return db.get_role(email).lower()
        except:
            return None
    
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
            return
        #Get person's name
        self.name = self.db.get_name(self.email)
        #Get person's phone number
        self.phone = self.db.get_phone(self.email)
        #Get person's address
        try:
            self.role = self.db.get_role(self.email).lower()
        except:
            self.role = None

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

    def update_timesheet(self, present: list):
        for date in present:
            date, timeSlot = date.split('_')
            if timeSlot == 'morning':
                self.update_timesheet_complete(date, "8:00", "12:00")
            else:
                self.update_timesheet_complete(date, "14:00", "16:00")
                self.update_overtime(datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d"),"add")
        return
        
    def update_overtime(self, date,sign):
        self.db.update_overtime(date,sign)

    def remove_timesheet(self, present_moring: list, present_afternoon: list):
        for date in present_moring:
            self.remove_timesheet_complete(date, "8:00", "12:00")
        for date in present_afternoon:
            self.remove_timesheet_complete(date, "14:00", "16:00")
            self.update_overtime(datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d"),"sub")
        return

    def remove_timesheet_complete(self, date: str, start_time, end_time):
        #Convert date to datetime object
        #date_obj = datetime.strptime(date, "%d-%m-%Y")
        #Convert start_time and end_time to datetime.time
        start_time_obj = datetime.strptime(start_time, '%H:%M')
        end_time_obj = datetime.strptime(end_time, '%H:%M')

        #Check if date is future date
        #if date_obj > datetime.now():
        #    print('Date cannot be future date')
        #    return
        #Check if start time is after end time
        if start_time_obj > end_time_obj:
            print('Start time cannot be after end time')
            return
        #Check if start time is before 6am
        #if start_time_obj.hour < 6:
        #    print('Start time cannot be before 6am')
        #    return False
        #Check if end time is after 2pm
        #if end_time_obj.hour > 14:
        #    print('End time cannot be after 2pm')
        #    return True

        #Format start_time and end_time to string
        #date = date.strftime('%Y-%m-%d')
        #start_time = start_time.strftime('%H:%M:%S')
        #end_time = end_time.strftime('%H:%M:%S')
        #Check if there is a clash
        #if self.db.check_timesheet_clash(self.email, date, start_time, end_time):
        #    print('Timesheet clash')
        #    return False
        #Update timesheet
        self.db.remove_timesheet(self.email, date, start_time, end_time)

    def update_timesheet_complete(self, date: str, start_time, end_time):
        #Convert date to datetime object
        #date_obj = datetime.strptime(date, "%d-%m-%Y")
        #Convert start_time and end_time to datetime.time
        start_time_obj = datetime.strptime(start_time, '%H:%M')
        end_time_obj = datetime.strptime(end_time, '%H:%M')

        #Check if date is future date
        #if date_obj > datetime.now():
        #    print('Date cannot be future date')
        #    return
        #Check if start time is after end time
        if start_time_obj > end_time_obj:
            print('Start time cannot be after end time')
            return
        #Check if start time is before 6am
        #if start_time_obj.hour < 6:
        #    print('Start time cannot be before 6am')
        #    return False
        #Check if end time is after 2pm
        #if end_time_obj.hour > 14:
        #    print('End time cannot be after 2pm')
        #    return True

        #Format start_time and end_time to string
        #date = date.strftime('%Y-%m-%d')
        #start_time = start_time.strftime('%H:%M:%S')
        #end_time = end_time.strftime('%H:%M:%S')
        #Check if there is a clash
        if self.db.check_timesheet_clash(self.email, datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d"), start_time, end_time):
            print('Timesheet clash')
            return False
        #Update timesheet
        self.db.add_timesheet(self.email, date, start_time, end_time)
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

    def check_available_overtime(self, date):
        temp = self.db.get_overtime(date)
        if temp == []:
            return False
        else:
            max_worker = temp[0][5]
            accepted_till_now = temp[0][6]

            if accepted_till_now < max_worker:
                return True
            else:
                return False
    
    def get_route_morning(self, date):
        route = self.db.get_route_for_wid_with_date_morning(self.email, date)
        binOrder = []
        for i in route:
            binID = int(i[2])
            binOrder.append(self.db.get_bin_details(binID)[1:])
        for i in range(len(binOrder)):
            binOrder[i] = (binOrder[i][0], float(binOrder[i][1]), float(binOrder[i][2]))
        #link = https://www.google.com/maps/dir/55,+72/28,77/
        final_output = []
        for i in range(len(binOrder)-1):
            name = binOrder[i][0]
            start_coord = str(binOrder[i][2]) + "," + str(binOrder[i][1])
            end_coord = str(binOrder[i+1][2]) + "," + str(binOrder[i+1][1])
            link = "https://www.google.com/maps/dir/" + start_coord + "/" + end_coord
            final_output.append((name, link))
        #final_output.append((binOrder[-1][0], "#"))
        return final_output

    def get_route_afternoon(self, date):
        route = self.db.get_route_for_wid_with_date_afternoon(self.email, date)
        binOrder = []
        for i in route:
            binID = int(i[2])
            binOrder.append(self.db.get_bin_details(binID)[1:])
        for i in range(len(binOrder)):
            binOrder[i] = (binOrder[i][0], float(binOrder[i][1]), float(binOrder[i][2]))
        final_output = []
        for i in range(len(binOrder)-1):
            name = binOrder[i][0]
            start_coord = str(binOrder[i][2]) + "," + str(binOrder[i][1])
            end_coord = str(binOrder[i+1][2]) + "," + str(binOrder[i+1][1])
            link = "https://www.google.com/maps/dir/" + start_coord + "/" + end_coord
            final_output.append((name, link))
        #final_output.append((binOrder[-1][0], "#"))
        return final_output


class Manager(Person):
    def __init__(self, db, email):
        super().__init__(db, email)
        if self.name == None:
            self.ask_details()

    def get_all_userdetails(self):
        return self.db.get_information_all_workers().values()
    
    def get_all_person(self):
        return self.db.get_all_person()
    
    def pending_request_raised_by_self(self):
        return self.db.get_pending_request_by_mgr(self.email)
    
    def pending_request_raised_by_others(self):
        return self.db.get_pending_request_not_by_mgr(self.email)

    def update_worker(self, w_email, request_type):
        return self.db.add_remove_worker(self.email, "Worker Name", w_email, 9876543210, "w", True if request_type == "add" else False)

    #Returns count of numbers of bins
    def get_new_bin_id(self) -> int:
        return self.db.get_bin_count()

    def get_all_bins(self) -> dict:
        return self.db.get_all_bins()

    #Add new bin
    def add_bin(self, bin_id: int, bin_address: str, bin_lat: float, bin_long: float) -> bool:
        self.db.insert_bin(bin_id, bin_address, str(bin_lat), str(bin_long))
        #calculating distance against all already present bin
        for i in range(int(bin_id)):
            #Read key from key file
            with open('key.txt', 'r') as f:
                key = f.read()
            client = openrouteservice.Client(key=key)
            #get lat and long of bin
            i_bin_long, i_bin_lat = self.db.get_bin_lat_long(i)
            i_bin_long, i_bin_lat = float(i_bin_long), float(i_bin_lat)
            #get distance between bin
            distance = client.distance_matrix(locations=((bin_long, bin_lat), (i_bin_long, i_bin_lat)), profile="driving-car", metrics=['distance'])
            print(distance)
            #insert into database
            self.db.insert_distance_between_2_bins(bin_id, i, distance['distances'][0][1]/1000)
            self.db.insert_distance_between_2_bins(i, bin_id, distance['distances'][1][0]/1000)
        return True

    def get_distance_matrix(self):
        size = self.get_new_bin_id()
        distance_matrix = [[0 for i in range(size)] for j in range(size)]
        for i in range(size):
            for j in range(size):
                if i == j:
                    distance_matrix[i][j] = 0
                else:
                    distance_matrix[i][j] = self.db.get_distance_between_2_bins(i, j)
        distance_matrix = np.array(distance_matrix)
        
        return distance_matrix

    def raise_overtime_request(self, dates: list, total_workers: list):
        dates = [datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d") for date in dates]
        dist_mat = self.get_distance_matrix()
        number_of_overtime_worker_required = []
        with futures.ProcessPoolExecutor() as executor:
            number_of_overtime_worker_required = executor.map(get_overtime_number, [dist_mat]*len(dates), total_workers, [i for i in range(len(dates))], dates)
            number_of_overtime_worker_required = list(number_of_overtime_worker_required)
        answer = [0] * len(dates)
        to_add = [False] * len(dates)
        for (index, value, add) in number_of_overtime_worker_required:
            answer[index], to_add[index] = value, add
        #Now update the database
        start_time = "14:00:00"
        end_time = "16:00:00"
        if False in to_add:
            return False
        for i in range(len(dates)):
            date = dates[i]
            if to_add[i]:
                self.db.create_overtime_request(date, start_time, end_time, answer[i])
        #Make the above for loop parallel
        return True

    def get_required_worker_and_accepted_worker(self, date):
        date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
        res = self.db.get_overtime(date)
        if res == []:
            return None
        return res[0][5], res[0][6]

    def generate_path(self, date: list, workers_morning: list, workers_afternoon: list) -> bool:
        date = [datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d") for date in date]
        self.db.execute("SELECT * FROM route WHERE date = '{}'".format(date[1]))
        x = self.db.cursor.fetchall()
        if x != []:
            print("Already exists")
            return False
        dist_mat = self.get_distance_matrix()
        workers_morning_count = [ len(i) for i in workers_morning]
        workers_afternoon_count = [ len(i) for i in workers_afternoon]
        path = []
        with futures.ProcessPoolExecutor() as executor:
            path = executor.map(get_path, date, [dist_mat]*len(date), workers_morning_count, workers_afternoon_count)
            path = list(path)
        
        for i in range(len(workers_morning)):
            workers_morning[i].sort()
            workers_afternoon[i].sort()

        for index, (date_, path_ ) in enumerate(path):
            self.db.execute("SELECT * FROM route WHERE date = '{}'".format(date_))
            x = self.db.cursor.fetchall()
            if x != []:
                print("Already exists")
                return False
            
            morning_w = workers_morning[index]
            afternoon_w = workers_afternoon[index]
            temp = []
            for x in path_.values():
                temp.append(x)
            #Sort temp according to length 
            temp.sort(key = lambda x: len(x))
            #Reverse the list
            temp.reverse()
            for i, (route,w_email) in enumerate(zip(temp,morning_w+afternoon_w)):
                afternoon = False
                if i>=len(morning_w):
                    afternoon = True
                if not self.db.insert_route(date_, w_email, route, afternoon):
                    print("Path already exists")
                    return False
        return True

def get_path(date, dist_mat, morning_worker, afternoon_worker):
    total_worker = morning_worker + afternoon_worker
    paths = get_paths(len(dist_mat), total_worker, dist_mat)
    return (date, paths)      

def generate_paths(x, n, number_of_worker):
        #x = self.get_distance_matrix()
        #n = self.get_new_bin_id()
        max_worker = number_of_worker
        with futures.ProcessPoolExecutor() as executor:
            results = executor.map(get_paths, [n] * (max_worker-3), range(3,max_worker), [x]*(max_worker-3))
            results = list(results)
        return results

def get_overtime_number(dist_mat, worker_today, index, date):
    db = Database()
    res = db.get_overtime(str(date))
    if len(res) != 0:
        return index, res[0][5], False

    x = get_paths(len(dist_mat), worker_today, dist_mat)
    #For each path in x calculate the sum of distance
    total_distance = []
    for path in x.values():
        total_distance.append(sum([dist_mat[path[i]][path[i+1]] for i in range(len(path)-1)]))
    overtime_required = 0
    remaining_nodes = []
    #For each distance check if time taken is more than morning_working_hours
    for worker, distance in enumerate(total_distance):
        if (distance/city_average_speed) > morning_working_hours:
            overtime_required = True
        if (distance/city_average_speed) > morning_working_hours:
            #Keep on removing nodes from x[worker] from the second last node till morning_working_hours is reached and add them to remaining_nodes
            i = len(x[worker])-2
            '''
            while (distance/city_average_speed) > morning_working_hours and i>3:
                distance = distance - dist_mat[x[worker][i]][x[worker][i+1]] - dist_mat[x[worker][i-1]][x[worker][i]]
                distance = distance + dist_mat[x[worker][i-1]][x[worker][i+1]]
                remaining_nodes.append(x[worker][i])
                i -= 1
                x[worker].pop(i+1)
            '''
            #Randomly remove nodes from x[worker] from the second last node till morning_working_hours is reached and add them to remaining_nodes
            while (distance/city_average_speed) > morning_working_hours and len(x[worker])>3:
                i = random.randint(3, len(x[worker])-2)
                distance = distance - dist_mat[x[worker][i]][x[worker][i+1]] - dist_mat[x[worker][i-1]][x[worker][i]]
                distance = distance + dist_mat[x[worker][i-1]][x[worker][i+1]]
                remaining_nodes.append(x[worker][i])
                x[worker].pop(i)
    #Now check the minimum worker required to cover the remaining nodes in the afternoon_working_hours
    #Remaining nodes compress to a single a single list
    remaining_nodes = [0] + remaining_nodes
    remaining_nodes.sort()
    if len(remaining_nodes) <=2 :
        overtime_required = 0
    #Get the distance matrix of remaining nodes
    try:
        if overtime_required==True:
            #Generate dist_mat_dash for remaining nodes
            #dist_mat_dash = [[0 for i in range(len(remaining_nodes[index]))] for j in range(len(remaining_nodes[index]))]
            dist_mat_dash = np.zeros((len(remaining_nodes), len(remaining_nodes)))
            for i in range(len(remaining_nodes)):
                for j in range(len(remaining_nodes)):
                    if i == j:
                        dist_mat_dash[i][j] = 0
                    else:
                        dist_mat_dash[i][j] = dist_mat[remaining_nodes[i]][remaining_nodes[j]]
            dist_mat_dash = np.array(dist_mat_dash)
                #Get the paths for remaining nodes
            x_dash = generate_paths(dist_mat_dash, len(remaining_nodes), max(3, worker_today))
                #For each possibile set of paths in x_dash find the path with minimum total distance travelled and travelling time is less than afternoon_working_hours
            minimum_distance = 1000000000000
            minimum_path = worker_today
            for path in x_dash:
                #print(path)
                total_distance_all_workers = []
                for p in path.values():
                    total_distance_all_workers.append(sum([dist_mat[p[i]][p[i+1]] for i in range(len(p)-1)]))
                #Check if for each worker time of travelling is less than afternoon working hours
                flag = True
                #print(total_distance_all_workers)
                for distance in total_distance_all_workers:
                    if (distance/city_average_speed) > afternoon_working_hours:
                        flag = False
                        break
                if flag:
                    if sum(total_distance_all_workers) < minimum_distance:
                        minimum_distance = sum(total_distance_all_workers)
                        minimum_path = len(path)

            overtime_required = max(minimum_path - 1, 3)
    except:
        print("Error")
        overtime_required=random.randint(3, worker_today-1)
        overtime_required= min(overtime_required, max(worker_today-3,1))
    return (index, overtime_required, True)
               
def get_paths(n, number_of_worker, dist_mat):
    global results
    X = cp.Variable((dist_mat.shape[0], dist_mat.shape[1]), boolean=True)
    
    u = cp.Variable(n, integer=True)
    m = number_of_worker

    ones = np.ones((n,1))

            # Defining the objective function
    objective = cp.Minimize(cp.sum(cp.multiply(dist_mat, X)))

    # Defining the constraints
    constraints = []
    constraints += [X[0,:] @ ones == m]
    constraints += [X[:,0] @ ones == m]
    constraints += [X[1:,:] @ ones == 1]
    constraints += [X[:,1:].T @ ones == 1]
    constraints += [cp.diag(X) == 0]
    constraints += [u[1:] >= 2]
    constraints += [u[1:] <= n]
    constraints += [u[0] == 1]

    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                constraints += [ u[i] - u[j] + 1  <= (n - 1) * (1 - X[i, j]) ]

    # Solving the problem
    prob = cp.Problem(objective, constraints)
    prob.solve(verbose=False)

    # Transforming the solution to paths
    X_sol = np.argwhere(X.value==1)

    ruta = {}
    for i in range(0, m):
        ruta[i] = [0]
        j = i
        a = 10e10
        while a != 0:
            a = X_sol[j,1]
            ruta[i].append(a)
            j = np.where(X_sol[:,0] == a)
            j = j[0][0]
            a = j
    distance = np.sum(np.multiply(dist_mat, X.value))
    #print('The optimal distance is {} with {} workers'.format(distance, m))
    return ruta

if __name__ == '__main__':
    db = Database()
    #user = Manager(db, 'ar794@snu.edu.in')
    #user.generate_path(['22-11-2022'],[['ar794@snu.edu.in','pd597@snu.edu.in']],[['ar794@snu.edu.in']])

    user = Worker(db, 'ar794@snu.edu.in')
    print(user.get_route('2022-11-28'))