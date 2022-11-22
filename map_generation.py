import folium
import json
from db import Database
import numpy as np
import datetime
#Coordinates of India Gate in lon,lat
#coordinates = ((77.2295, 28.6129),(77.2090, 28.6448))
#Coordinates of IGI Airport in lon,lat
#coordinates = ((77.0485, 28.5665),(77.2090, 28.6448))

#How many km between India Gate and IGI Airport
#Number of km between India Gate and IGI Airport is 14.5 km

#Use python to calculate the driving distance between India Gate and IGI Airport

db = Database()
city_average_speed = 20
'''
distance = client.distance_matrix(coords, profile='driving-car', metrics=['distance'])
print(distance)

res = client.directions(coords)
geometry = client.directions(coords)['routes'][0]['geometry']
decoded = convert.decode_polyline(geometry)

distance_txt = "<h4> <b>Distance :&nbsp" + "<strong>"+str(round(res['routes'][0]['summary']['distance']/1000,1))+" Km </strong>" +"</h4></b>"
duration_txt = "<h4> <b>Duration :&nbsp" + "<strong>"+str(round(res['routes'][0]['summary']['duration']/60,1))+" Mins. </strong>" +"</h4></b>"

m = folium.Map(location=[6.074834613830474, 80.25749815575348],zoom_start=10, control_scale=True,tiles="cartodbpositron")
folium.GeoJson(decoded).add_child(folium.Popup(distance_txt+duration_txt,max_width=300)).add_to(m)
'''
#Create a folium map with the coordinates of delhi as the center and the zoom should cover entire delhi city


def create_map(date):
    #Create distance matrix
    size = db.get_bin_count()
    distance_matrix = [[0 for i in range(size)] for j in range(size)]
    for i in range(size):
        for j in range(size):
            if i == j:
                distance_matrix[i][j] = 0
            else:
                distance_matrix[i][j] = db.get_distance_between_2_bins(i, j)
    distance_matrix = np.array(distance_matrix)
    
    time_for_collection = [None] * (size)
    db.execute("select DISTINCT EmailID from route where Date='{s}';".format(s=date))
    distinct_workers = db.cursor.fetchall()
    for worker_email in distinct_workers:
        worker_email = worker_email[0]
        morning_binOrder, afternoon_binOrder = list(), list()
        morning_schedule = db.get_route_for_wid_with_date_morning(worker_email, date)
        afternoon_schedule = db.get_route_for_wid_with_date_afternoon(worker_email, date)
        for i in morning_schedule:
            binID = int(i[2])
            morning_binOrder.append(db.get_bin_details(binID)[0:])
        for i in afternoon_schedule:
            binID = int(i[2])
            afternoon_binOrder.append(db.get_bin_details(binID)[0:])
        #morning_start = datetime object of time 9am
        morning_start = datetime.datetime.strptime("09:00:00", "%H:%M:%S")
        #afternoon_start = datetime object of time 2pm
        afternoon_start = datetime.datetime.strptime("14:00:00", "%H:%M:%S")

        for i in range(1,len(morning_binOrder)-1):
            binId = int(morning_binOrder[i][0])
            prev_binId = int(morning_binOrder[i-1][0])
            morning_start = morning_start + datetime.timedelta(minutes=(db.get_distance_between_2_bins(prev_binId, binId)/city_average_speed)*60)
            time_for_collection[binId] = morning_start.strftime("%H:%M:%S")

        for i in range(1,len(afternoon_binOrder)-1):
            binId = int(afternoon_binOrder[i][0])
            prev_binId = int(afternoon_binOrder[i-1][0])
            afternoon_start = afternoon_start + datetime.timedelta(minutes=(db.get_distance_between_2_bins(prev_binId, binId)/city_average_speed)*60)
            time_for_collection[binId] = afternoon_start.strftime("%H:%M:%S")
    get_bin_name = lambda id: db.get_bin_details(id)[1]
    #Create a folium map with the coordinates of delhi as the center and the zoom should cover entire delhi city

    #The map should initially show the entire delhi city
    m = folium.Map(location=[28.620596, 77.206064],zoom_start=11, control_scale=True)

    folium.Marker(location=db.get_bin_details(0)[2:][::-1], popup="Start", icon=folium.Icon(color='green')).add_to(m)
    for i in range(1,size):
        '''folium.Marker(
            location=list(db.get_bin_details(i)[2:][::-1]),
            popup=str(get_bin_name(i)) + ", " + str(time_for_collection[i]),
            icon=folium.Icon(color="blue"),
        ).add_to(m)'''
        folium.Marker(
            location=list(db.get_bin_details(i)[2:][::-1]),
            popup=str(get_bin_name(i)) + ", " + str(time_for_collection[i]),
            icon=folium.Icon(color="blue"),
        ).add_to(m)
    m.save("templates/map.html")

if __name__=='__main__':
    today = datetime.date.today().strftime("%Y-%m-%d")
    create_map(today)
