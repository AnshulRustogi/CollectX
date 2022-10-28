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

alert = None
alert_message = None

db = Database()
class User:
    
    def __init__(self, email):
        
        if Person.get_role(db, email) == 'W':
            self.user = Worker(db, email)
        elif Person.get_role(db, email) == 'M':
            self.user = Manager(db, email)
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
        return str(self.user.email)
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


@app.route("/index")  #the home page where the login button will be located
def index():
    global alert, alert_message
    return render_template_with_alert("index.html", user=current_user)
    
def render_template_with_alert(template, **kwargs):
    global alert, alert_message
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

@app.route("/")  #the home page where the login button will be located
def home_page():
    return redirect("/index")


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    global alert, alert_message
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
    global alert_message, alert
    if current_user.user.role =="M":
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

@app.route("/logout")
@login_required
def logout():
    global alert, alert_message
    logout_user()
    session.clear()
    alert = False
    return redirect("/")

@login_manager.unauthorized_handler
def unauthorized_callback():
    global alert, alert_message
    alert = True
    alert_message = "Kindly login with your registered email"
    return redirect('/')

@app.route("/worker_timesheet", methods=['GET', 'POST'])
@login_required
def worker_timesheet():
    global alert, alert_message
    if current_user.user.role == "W":
        today = datetime.datetime.today()
        next_monday = today + datetime.timedelta(days=-today.weekday(), weeks=1)
        #Create list of dates for next week and append the dates as string
        dates = []
        present_morning = []
        present_afternoon = []
        timesheet = current_user.user.get_timesheet()
        #dates_in_timesheet = [x[0].strftime("%d-%m-%Y") for x in timesheet]
        dates_in_timesheet_morning = [x[0].strftime("%d-%m-%Y") for x in timesheet if x[1]== datetime.timedelta(hours=8)]
        dates_in_timesheet_afternoon = [x[0].strftime("%d-%m-%Y") for x in timesheet if x[1]== datetime.timedelta(hours=14)]
        for i in range(7):
            dates.append((next_monday + datetime.timedelta(days=i)).strftime("%d-%m-%Y"))
            if dates[i] in dates_in_timesheet_morning:
                present_morning.append((dates[i],True))
            else:
                present_morning.append((dates[i],False))
            if dates[i] in dates_in_timesheet_afternoon:
                present_afternoon.append((dates[i],True))
            else:
                present_afternoon.append((dates[i],False))

        if request.method == 'POST':
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
        
        #timesheet is a list of tuple of (date, start_time, end_time)
        #timesheet = current_user.user.get_timesheet()
        #print(timesheet)
        #dates_in_timesheet = [x[0] for x in timesheet]
        #present = []
        #For all the dates check if that date is present in timesheet
        #for date in dates:
        #    if date in dates_in_timesheet:
        #        present.append(True)
        #    else:
        #        present.append(False)

        return render_template_with_alert("worker_timesheet.html", user=current_user,
            dates=dates, 
            is_working_week_morning=present_morning,
            is_working_week_afternoon=present_afternoon)
    else:
        return redirect('/index')

@app.route("/route_planning", methods=['GET', 'POST'])
@login_required
def route_planning():
    global alert, alert_message
    #If the user is a manager
    #Find all worker timesheet for next week
    if current_user.user.role == "M":
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
        return render_template_with_alert("route_planning.html", user=current_user,
            dates=dates, 
            workers_timesheet = worker_timesheet,
            total_worker_morning=total_worker_morning,
            total_worker_afternoon=total_worker_afternoon)
if __name__ == "__main__":  #and the final closing function
    app.run(debug=True)