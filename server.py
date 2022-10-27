import os
import pathlib
import requests
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from worker import Worker, Manager, Person
from db import Database
db = Database()
alert = None
alert_message = None
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
    #If user is already logged in, redirect to home page
    if current_user.is_authenticated:
        print("Voila")
        return redirect('/index')
    authorization_url, state = flow.authorization_url()  #asking the flow class for the authorization (login) url
    session["state"] = state
    
    return redirect(authorization_url)


@app.route("/callback")  #this is the page that will handle the callback process meaning process after the authorization
def callback():
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
    s = render_template("index.html", user=current_user, alert=alert, alert_message=alert_message)
    alert = False
    alert_message = ""
    return s

@app.route("/")  #the home page where the login button will be located
def home_page():
    return render_template("index.html", user=current_user, alert=alert, alert_message=alert_message)

@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        print("POST request received")
        #print(request.form)
        newName = request.form['fullname']
        newPhone = request.form['phone']
        current_user.user.update_details(newName, newPhone)
        return redirect('/profile')
    return render_template("profile.html", user=current_user)

@app.route("/worker_update", methods=['GET', 'POST'])
@login_required
def worker_update():
    if current_user.user.role =="M":
        if request.method == 'POST':
            w_email = request.form['worker_email']
            request_type = request.form['action_type']
            #current_user.user.update_worker(newEmail, newName, newPhone, newRole, newPass)
            current_user.user.update_worker(w_email, request_type)
            return redirect('/worker_update')
        raised_by_user = current_user.user.pending_request_raised_by_self()
        raised_by_other = current_user.user.pending_request_raised_by_others()
        return render_template("worker_change.html", user=current_user, 
            details=current_user.user.get_all_userdetails(),
            raised_by_user=raised_by_user,
            raised_by_other=raised_by_other)
    else:   
        return redirect('/index')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect("/")

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/')


if __name__ == "__main__":  #and the final closing function
    app.run(debug=True)