import googlemaps
import networkx as nx
import requests
from PIL import Image
from io import BytesIO
import numpy as np
from plotly.graph_objects import Scattermapbox, Figure
import plotly.io as pio

pio.renderers.default = 'browser'

API_KEY = 'AIzaSyAw2UfZPrYZgrEX3XT6wNkHzo8F_vcBUzs'
gmaps = googlemaps.Client(key=API_KEY)

graph = nx.DiGraph()
graph.add_node('Gummersbach TH Köln', y=51.0300, x=7.5650)  # Coordinates for Gummersbach TH Köln
graph.add_node('Berlin', y=52.5200, x=13.4050)              # Coordinates for Berlin

graph.add_edge('Gummersbach TH Köln', 'Berlin', weight=1.0)  # Weight can be arbitrary for this example

def shortest_path(graph, start, end):
    return nx.dijkstra_path(graph, start, end), nx.dijkstra_path_length(graph, start, end)

start = 'Gummersbach TH Köln'
end = 'Berlin'
path, length = shortest_path(graph, start, end)
print(f"Shortest path from {start} to {end}: {path} with total length {length}")

def get_street_view_image(location):
    params = {
        'size': '600x300',  # Image size
        'location': location,  # Location as a string
        'key': API_KEY
    }
    response = requests.get('https://maps.googleapis.com/maps/api/streetview', params=params)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        print(f"Error fetching street view image for {location}: {response.status_code}")
        return None

for node in path:
    location = f"{graph.nodes[node]['y']},{graph.nodes[node]['x']}"
    print(f"Street view for {node}: {location}")
    image = get_street_view_image(location)
    if image:
        image.show()

def get_directions(start, end):
    try:
        directions_result = gmaps.directions(start, end, mode="driving")
        if directions_result:
            return directions_result[0]['overview_polyline']['points']
        else:
            print("No routes found.")
            return None
    except googlemaps.exceptions.ApiError as e:
        print(f"Directions API error: {e}")
        return None

def get_street_view_image(location):
    params = {
        'size': '600x300',
        'location': location,
        'key': API_KEY
    }
    try:
        response = requests.get('https://maps.googleapis.com/maps/api/streetview', params=params)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            print(f"Error fetching street view image for {location}: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"HTTP request error: {e}")
        return None


def decode_polyline(polyline_str):
    index, lat, lng, coordinates = 0, 0, 0, []
    while index < len(polyline_str):
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if not b >= 0x20:
                break
        delta_lat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += delta_lat
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if not b >= 0x20:
                break
        delta_lng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += delta_lng
        coordinates.append((lat / 1e5, lng / 1e5))
    return coordinates

def get_long_lat_from_path(polyline_points):
    lat, long = zip(*polyline_points)
    return long, lat

def plot_lat_long(lat, long, origin_point, destination_point):
    fig = Figure(Scattermapbox(
        name="Path",
        mode="lines",
        lon=long,
        lat=lat,
        marker={'size': 10},
        line=dict(width=4.5, color='blue')))
    fig.add_trace(Scattermapbox(
        name="Source",
        mode="markers",
        lon=[origin_point[1]],
        lat=[origin_point[0]],
        marker={'size': 12, 'color': "red"}))
    fig.add_trace(Scattermapbox(
        name="Destination",
        mode="markers",
        lon=[destination_point[1]],
        lat=[destination_point[0]],
        marker={'size': 12, 'color': 'green'}))

    lat_center = np.mean(lat)
    long_center = np.mean(long)
    fig.update_layout(mapbox_style="open-street-map",
                      mapbox_center_lat=lat_center, mapbox_center_lon=long_center,
                      mapbox_zoom=5)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()

origin_point = (graph.nodes[start]['y'], graph.nodes[start]['x'])
destination_point = (graph.nodes[end]['y'], graph.nodes[end]['x'])
print(f"Origin point: {origin_point}")
print(f"Destination point: {destination_point}")

directions = get_directions(f"{origin_point[0]},{origin_point[1]}", f"{destination_point[0]},{destination_point[1]}")
if directions:
    polyline_points = decode_polyline(directions)
    long, lat = get_long_lat_from_path(polyline_points)
    plot_lat_long(lat, long, origin_point, destination_point)
else:
    print("No directions found between the points.")
