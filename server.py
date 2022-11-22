import os
import pathlib
import re
import requests
from flask import Flask, session, abort, redirect, request, render_template
from flask_assets import Environment, Bundle
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from worker import Worker, Manager, Person
from db import Database
import datetime
import threading
import os
alert = None
alert_message = None

db = Database()

#Check if time is for manager to generate overtime request
'''
valid_overtime_request_raise_manager = False
t = 9
#If today is Saturday and it's before 3 PM then raise overtime is valid
#if datetime.datetime.today().weekday() == 5 and datetime.datetime.now().hour < 15:
if datetime.datetime.today().weekday() == 1 and datetime.datetime.now().hour < t:
    valid_overtime_request_raise_manager = True

#Check if Sunday
is_sunday = True
if datetime.datetime.today().weekday() == 5:
    is_sunday = False

is_saturday = False
if datetime.datetime.today().weekday() == 1:
    is_saturday = False

#Check if it's valid time for worker to accepted overtime 
valid_overtime_request_accept_worker = False
if datetime.datetime.today().weekday() == 1 and datetime.datetime.now().hour >= t:
    valid_overtime_request_accept_worker = True

is_weekday = False
if datetime.datetime.today().weekday() <= 5:
    #Change before presentation
    is_weekday = False
'''

is_weekday = datetime.datetime.today().weekday() <= 5
is_sunday = datetime.datetime.today().weekday() == 5
is_saturday = not is_weekday and not is_sunday  
t = 17
valid_overtime_request_raise_manager = (datetime.datetime.now().hour < t) and is_saturday
valid_overtime_request_accept_worker = is_saturday and not valid_overtime_request_raise_manager 

class User:
                   
    def __init__(self, email):
        if Person.get_role(db, email) == 'w':
            self.user = Worker(db, email)
        elif Person.get_role(db, email) == 'm':
            self.user = Manager(db, email)
        else:
            self.user = Person(db, None)
        #else:
        #    self.user = None
        self.photo = session["photo"]

        #super().__init__(email)
        
    def load_user(self):
        return {"name": self.name,
                "email": self.email,
                "phone": self.phone,
                "role": self.role}

    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        print(self.user)
        return self.user.email
    def get_role(self):
        return self.user.role

app = Flask("CollectX")  #naming our application
assets     = Environment(app)
assets.url = app.static_url_path

scss       = Bundle('css/form.scss', filters='pyscss', output='css/profile_form.css')

assets.config['SECRET_KEY'] = 'SDL-CollectX'
assets.config['PYSCSS_LOAD_PATHS'] = assets.load_path
assets.config['PYSCSS_STATIC_URL'] = assets.url
assets.config['PYSCSS_STATIC_ROOT'] = assets.directory
assets.config['PYSCSS_ASSETS_URL'] = assets.url
assets.config['PYSCSS_ASSETS_ROOT'] = assets.directory

assets.register('scss_all', scss)

app.secret_key = "SDL-CollectX"  #it is necessary to set a password when dealing with OAuth 2.0
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  #this is to set our environment to https because OAuth 2.0 only supports https environments


GOOGLE_CLIENT_ID = "404997951228-bm3hrsq5dudpdkgkdicl3kh2hvtev8g1.apps.googleusercontent.com"  #enter your client id you got from Google console
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")  #set the path to where the .json file you got Google console is

flow = Flow.from_client_secrets_file(  #Flow is OAuth 2.0 a class that stores all the information on how we want to authorize our users
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],  #here we are specifing what do we get after the authorization
    redirect_uri="http://127.0.0.1:5000/callback"  #and the redirect URI is the point where the user will end up after the authorization
)

login_manager = LoginManager()  #this is a class that will help us to manage our users
login_manager.init_app(app)  #we are initializing our login manager

@login_manager.user_loader  #this is a decorator that will help us to load the user
def load_user(email_id):
    return User(email_id)

@app.route("/login")  #the page where the user can login
def login():
    global alert, alert_message
    #If user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect('/index')
    authorization_url, state = flow.authorization_url()  #asking the flow class for the authorization (login) url
    session["state"] = state
    
    return redirect(authorization_url)

@app.route("/callback")  #this is the page that will handle the callback process meaning process after the authorization
def callback():
    global alert, alert_message
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  #state does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    
    session["google_id"] = id_info.get("sub")  #defing the results to show on the page
    session["email"] = id_info.get("email")
    session["photo"] = id_info.get("picture")
    db = Database()
    print("Email: " + id_info["email"])
    print("Exists: " + str(db.check_person(id_info["email"])))
    if not db.check_person(id_info["email"]):
        global alert_message, alert
        logout_user()
        session.clear()
        alert_message = "You are not authorized to use this application"
        alert = True
        return redirect("/index")
    alert = False

    login_user(User(session["email"]))
    return redirect("/")  #the final page where the authorized users will end up

def render_template_with_alert(template, **kwargs):
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    try:
        if current_user.user.db.error!=None and alert!=True:
            print(current_user.user.db.error)
            alert_message = current_user.user.db.error
            alert = True
    except:
        pass
    r = render_template(template, alert=alert, alert_message=alert_message, **kwargs)
    alert = False
    global db
    db = Database()
    return r

@app.route("/index")  #the home page where the login button will be located
def index():
    os.system("python map_generation.py &")
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    return render_template_with_alert("index.html", user=current_user)
    
@app.route("/")  #the home page where the login button will be located
def home_page():
    return redirect("/index")

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    if request.method == 'POST':
        print("POST request received")
        #print(request.form)
        newName = request.form['fullname']
        newPhone = request.form['phone']
        if newName == "" or len(str(newPhone))!=10:
            print("Invalid input")
            alert = True
            alert_message = "Enter valid name and 10-digit phone number"
            return redirect("/profile")
        current_user.user.update_details(newName, newPhone)
        return redirect('/profile')
    return render_template_with_alert("profile.html", user=current_user)


@app.route("/worker_update", methods=['GET', 'POST'])
@login_required
def worker_update():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    if current_user.user.role =="m":
        if request.method == 'POST':
            w_email = request.form['worker_email'].lower()
            request_type = request.form['action_type']
            #If w_email is not a email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", w_email):
                print("Invalid email")
                
                alert_message = "Invalid email"
                alert = True
                return redirect('/worker_update')
            current_user.user.update_worker(w_email, request_type)
            alert = False
            return redirect('/worker_update')
        raised_by_user = current_user.user.pending_request_raised_by_self()
        raised_by_other = current_user.user.pending_request_raised_by_others()
        return render_template_with_alert("worker_change.html", user=current_user, 
            details=current_user.user.get_all_userdetails(),
            raised_by_user=raised_by_user,
            raised_by_other=raised_by_other)
    else:   
        alert = False
        return redirect('/index')

@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/logout")
@login_required
def logout():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    logout_user()
    session.clear()
    alert = False
    return redirect("/")

@login_manager.unauthorized_handler
def unauthorized_callback():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    alert = True
    alert_message = "Kindly login with your registered email"
    return redirect('/')

@app.route("/worker_timesheet", methods=['GET', 'POST'])
@login_required
def worker_timesheet():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    if current_user.user.role == "w":
        today = datetime.datetime.today()
        next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        last_monday = today + datetime.timedelta(days=-today.weekday(), weeks=0)
        #Create list of dates for next week and append the dates as string
        dates = []
        present_morning = []
        present_afternoon = []
        timesheet = current_user.user.get_timesheet()
        #dates_in_timesheet = [x[0].strftime("%d-%m-%Y") for x in timesheet]
        dates_in_timesheet_morning = [x[0].strftime("%d-%m-%Y") for x in timesheet if x[1]== datetime.timedelta(hours=8)]
        dates_in_timesheet_afternoon = [x[0].strftime("%d-%m-%Y") for x in timesheet if x[1]== datetime.timedelta(hours=14)]
        submitted_once = False
        for i in range(7):
            dates.append((next_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))
            if dates[i] in dates_in_timesheet_morning:
                present_morning.append((dates[i],True))
            else:
                present_morning.append((dates[i],False))
            if dates[i] in dates_in_timesheet_afternoon:
                date = datetime.datetime.strptime(dates[i], "%d-%m-%Y").strftime("%Y-%m-%d")
                present_afternoon.append((current_user.user.check_available_overtime(date),dates[i],True))
                submitted_once = True
            else:
                date = datetime.datetime.strptime(dates[i], "%d-%m-%Y").strftime("%Y-%m-%d")
                present_afternoon.append((current_user.user.check_available_overtime(date),dates[i],False))

        prev_dates = []
        prev_present_morning = []
        prev_present_afternoon = []
        prev_timesheet = current_user.user.get_timesheet()
        #dates_in_timesheet = [x[0].strftime("%d-%m-%Y") for x in timesheet]
        prev_dates_in_timesheet_morning = [x[0].strftime("%d-%m-%Y") for x in prev_timesheet if x[1]== datetime.timedelta(hours=8)]
        prev_dates_in_timesheet_afternoon = [x[0].strftime("%d-%m-%Y") for x in prev_timesheet if x[1]== datetime.timedelta(hours=14)]
        for i in range(7):
            prev_dates.append((last_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))
            if prev_dates[i] in prev_dates_in_timesheet_morning:
                prev_present_morning.append((prev_dates[i],True))
            else:
                prev_present_morning.append((prev_dates[i],False))
            if prev_dates[i] in prev_dates_in_timesheet_afternoon:
                prev_date = datetime.datetime.strptime(prev_dates[i], "%d-%m-%Y").strftime("%Y-%m-%d")
                prev_present_afternoon.append((current_user.user.check_available_overtime(prev_date),prev_dates[i],True))
            else:
                prev_date = datetime.datetime.strptime(prev_dates[i], "%d-%m-%Y").strftime("%Y-%m-%d")
                prev_present_afternoon.append((current_user.user.check_available_overtime(prev_date),prev_dates[i],False))
    
        

        if request.method == 'POST':
            #If today date is after Saturday then redirect to worker_timesheet with error that timesheet can be filled only till Saturday
            if is_sunday:
                alert = True
                alert_message = "Kindly wait till Monday to fill the timesheet for the next week. This week timesheet can be filled till Saturday."
                return redirect('/worker_timesheet')
            if not is_weekday and not valid_overtime_request_accept_worker:
                alert = True
                alert_message = "Kindly wait till Monday to fill the timesheet for the next week or overtime request cannot be accepted now. Please try after {t}:00:00".format(t=t)
                return redirect('/worker_timesheet')
            #if submitted_once:
            #    alert = True
            #    alert_message = "Timesheet already submitted for this week"
            #    return redirect('/worker_timesheet')

            valid_afternoon = []
            if valid_overtime_request_accept_worker:
                #Update in database
                for date_timeslot in request.form.getlist('working_dates'):
                    date, timeslot = date_timeslot.split("_")
                    if timeslot == "afternoon":
                        #pass
                        date = datetime.datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
                        if not current_user.user.check_available_overtime(date):
                            alert = True
                            alert_message = "Overtime request already accepted for {d}. Better luck next time!".format(d=date)
                            return redirect('/worker_timesheet')

            current_user.user.remove_timesheet(dates_in_timesheet_morning, dates_in_timesheet_afternoon)
            newWorkingDates = request.form.getlist('working_dates')
            current_user.user.update_timesheet(newWorkingDates)
        
            return redirect('/worker_timesheet')


        timesheet = current_user.user.get_timesheet()
        dates_in_timesheet = [x[0].strftime("%d-%m-%Y") for x in timesheet]
        present = []
        for i in range(7):
            if dates[i] in dates_in_timesheet:
                present.append((dates[i], True))
            else:
                present.append((dates[i],False))
        
        return render_template_with_alert("worker_timesheet.html", user=current_user,
            dates=dates, 
            prev_dates = prev_dates,
            is_working_week_morning=present_morning,
            is_working_week_afternoon=present_afternoon,
            prev_is_working_week_morning=prev_present_morning,
            prev_is_working_week_afternoon=prev_present_afternoon,
            valid_overtime_request_accept_worker=valid_overtime_request_accept_worker,
            valid_overtime_request_raise_manager=valid_overtime_request_raise_manager,
            is_sunday=is_sunday,
            is_weekday=is_weekday)
    else:
        return redirect('/index')

@app.route("/route_planning", methods=['GET', 'POST'])
@login_required
def route_planning(overtime=False):
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    #If the user is a manager
    #Find all worker timesheet for next week
    if current_user.user.role == "m":

        today = datetime.datetime.today()
        next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        last_monday = today + datetime.timedelta(days=-today.weekday(), weeks=0)
        #Create list of dates for next week and append the dates as string
        dates = []
        for i in range(7):
            dates.append((next_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))
        #Get all the workers
        workers = current_user.user.get_all_userdetails()
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
        print(total_worker_afternoon)
        data = [] * len(dates)
        all_false = False
        if is_saturday:
            overtime = True
        for i in range(len(dates)):
            temp = current_user.user.get_required_worker_and_accepted_worker(dates[i])
            if temp==None:
                data.append((False, "No overtime request/Overtime not generated"))
            else:
                s = "Required workers: {r}".format(r=temp[0]) , "Workers Present: {a}".format(a=temp[1])
                data.append((True, s))
                all_false = True
        #Convert dates[0] to datetime object
        current_user.user.db.execute("SELECT * FROM route WHERE date = '{}'".format(datetime.datetime.strptime(dates[0], "%d-%m-%Y").strftime("%Y-%m-%d")))
        x = current_user.user.db.cursor.fetchall()
        paths_generated = False
        if x != []:
            print("Already exists")
            paths_generated = True
        return render_template_with_alert("route_planning.html", user=current_user,
            dates=dates, 
            workers_timesheet = worker_timesheet,
            total_worker_morning=total_worker_morning,
            total_worker_afternoon=total_worker_afternoon,
            valid_overtime_request_raise_manager=valid_overtime_request_raise_manager,
            is_sunday=is_sunday,
            overtime_data = data,
            is_weekday=is_weekday,
            valid_overtime_request_accept_worker=valid_overtime_request_accept_worker,
            is_saturday=is_saturday,
            paths_generated=paths_generated,
            overtime_already_generated=all_false)

@app.route('/generate_overtime')
def generate_overtime():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    if current_user.user.role != "m":
        return redirect('/index')
    
    global alert, alert_message
    if not valid_overtime_request_raise_manager:
        alert = True
        alert_message = "Overtime request cannot be raised now. Please try before {t}:00:00".format(t=t)
        return redirect('/route_planning')
    '''
    today = datetime.datetime.today()
    next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
    #Create list of dates for next week and append the dates as string
    dates = []
    for i in range(7):
        dates.append((next_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))
    #Get all the workers
    workers = current_user.user.get_all_userdetails()
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

    if not current_user.user.raise_overtime_request(dates, total_worker_morning):
        alert = True
        alert_message = "Overtime request already raised for next week"
        return redirect('/route_planning')
    #requirement = current_user.user.raise_overtime_request(dates, total_worker_morning)
    #current_user.user.raise_overtime_request(dates, total_worker_morning)
    alert = True 
    alert_message = "Overtime request raised successfully"
    '''
    #Run the following command "python overtime_request.py --email current_user.user.email
    os.system("python overtime_request.py --email {e} &".format(e=current_user.user.email))
    alert = True
    alert_message = "Overtime request raised successfully! Please wait for 5 minutes"
    return redirect('/route_planning')

@app.route('/generate_path')
def generate_path():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager

    if current_user.user.role != "m":
        return redirect('/index')

    if not is_sunday:
        alert = True
        alert_message = "Path cannot be generated now. Please try after Sunday 00:00:00"
        return redirect('/route_planning')
    '''
    today = datetime.datetime.today()
    next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
    dates = []
    for i in range(7):
        dates.append((next_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))

    workers = current_user.user.get_all_userdetails()
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
    
    if not current_user.user.generate_path(dates, total_worker_morning, total_worker_afternoon):
        alert = True
        alert_message = "Path already generated for next week"
        return redirect('/route_planning')
    '''
    #Run the following command "python generate_path.py --email current_user.user.email
    os.system("python generate_path.py --email {e} --is_sunday {s}&".format(e=current_user.user.email, s=is_sunday))

    alert = True
    alert_message = "Path generation started. Please check after 5 minutes"
    return redirect('/route_planning')

@app.route("/add_newbin", methods=['GET', 'POST'])
@login_required
def add_newbin():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    if current_user.user.role == "m":
        new_bin_id = current_user.user.get_new_bin_id()
        all_bins = current_user.user.get_all_bins()
        
        if request.method == 'POST':
            bin_id = request.form['bin_id']
            bin_address = request.form['bin_address']
            bin_lat = request.form['bin_lat']
            bin_long = request.form['bin_long']
            current_user.user.add_bin(bin_id, bin_address, bin_lat, bin_long)
            return redirect('/add_newbin')
        temp = []
        for x in all_bins.values():
            if x[1] == None or x[2] == None or x[1] == '' or x[2] == '':
                temp.append((x[0],0,0))
            else:
                temp.append((x[0],float(x[1]),float(x[2])))
        return render_template_with_alert("add_newbin.html", 
            user=current_user,
            new_bin_id=new_bin_id,
            all_bins=temp)
    else:
        return redirect('/index')

@app.route("/assinged_route")
@login_required
def assinged_route():
    global alert, alert_message, is_saturday, is_sunday, is_weekday, valid_overtime_request_accept_worker, valid_overtime_request_raise_manager
    
    if current_user.user.role != "w":
        return redirect('/index')
    
    today = datetime.datetime.today()
    last_monday = today + datetime.timedelta(days=-today.weekday(), weeks=0)
    today = today.strftime("%d-%m-%Y")
        
    dates = []
    data = []
    for i in range(14):
        dates.append((last_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))
        date_temp = (last_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y")
        route_morning = current_user.user.get_route_morning((last_monday + datetime.timedelta(days=i)).strftime("%Y-%m-%d"))
        route_afternoon = current_user.user.get_route_afternoon((last_monday + datetime.timedelta(days=i)).strftime("%Y-%m-%d"))
        data.append((date_temp, route_morning, route_afternoon))
    
    return render_template_with_alert("worker_assigned_route.html", user=current_user,
            all_data=data, dates=dates,
            today_date=today)

        

if __name__ == "__main__":  #and the final closing function
    app.run(debug=True)