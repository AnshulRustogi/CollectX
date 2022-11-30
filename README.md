# CollectX

## How to run
1) Create a empty mysql database named collectx 
2) Update mysql connection details in db.py
3) Generate client id and client secret file from google for google authentication and update in server.py (<a href="https://developers.google.com/identity/protocols/oauth2/service-account">Link</a>)<br>
  
4) Manually insert two google id's into collectx.person using the below mysql command:
  ```
  insert into person values (FULL_NAME, GOOGLE_EMAIL_ID, PHONE_NUMBER, 'm')
  ```
5) Generate key from openrouteserivce for using their distance matrix in order to calculate distances, save the key in a new file
  ```
  echo "KEY_FROM_OPENROUTESERVICE" > key
  ```
5) Create a new virtual environment and install the required libraries
  ```
  pip install -r requirements.txt
  ```
6) Run 
```
  python3 server.py
```

## Technology/Languages used
* Python
* Flask
* Google Authentication


### About the files

* <b>Folder: Static, template</b>: These folder contains the basic crux of static HTML, CSS and JS files for all the webpages in the app.
* <b>db.py</b>: Contains Database class which helps with the connection with MySQL database and also the functions which are used by Worker and Manager object to interact with the database and retrieve/update the necessary information.
* <b>map_generation.py</b>: Generates the map using folium with information regarding the next day garbage collection time using the routes stored in the database.
* <b>overtime_request.py</b>: Contains functions with help manager to generate overtime request for the next week by looking at the numbers of workers present each day in the next week and using multiple travelling salesman algorithm to calculate the optimal numbers of workers required (if any) to visit all the bins present in the city.
* <b>worker.py</b>: Contains the classes for Worker and Manager along with their respective member functions.
* <b>server.py</b>: Contains the main app class with all the hyperlinks and the functions associated with the hyperlinks along with various methods to responds to post requests raised with the hyperlinks. 