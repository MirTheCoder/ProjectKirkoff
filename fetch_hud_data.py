"""
fetch_hud_data.py  —  Download real 2024 QCT and DDA boundary data for Connecticut.

Run once before starting the app:
    python fetch_hud_data.py

Saves to:
    static/data/ct_qct.geojson   (Qualified Census Tracts)
    static/data/ct_dda.geojson   (Difficult Development Areas)

The app will automatically use these instead of the placeholder polygons.
Requires:  pip install requests
"""
import json
import time
import requests
from pathlib import Path

#This will give us the location where we can store data, and if the location does not exist, then we will create it
OUT = Path(__file__).parent / "static" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# ── HUD ArcGIS REST services (VTyQ9soqVukalItT = HUD org on ArcGIS Online) ──
# Multiple candidate URLs tried in order — HUD occasionally renames services
HUD_ORG  = "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services" #Leaving this url here in case we need to go back to the base services page to see the url to a service and the scopes pertaining to that service/info

#This will be our url for getting QCT geographical points in order to plot them on our map
QCT_URL  = "https://services.arcgis.com/VTyQ9soqVukalItT/ArcGIS/rest/services/QUALIFIED_CENSUS_TRACTS_2026/FeatureServer/0/query"
#This will be the url base for getting the dda geographical points in order to plot them on our map
DDA_URL = "https://services.arcgis.com/VTyQ9soqVukalItT/ArcGIS/rest/services/Difficult_Development_Areas_2026/FeatureServer/0/query"
#This will be a url that allows us to get all flood zone areas
FLOOD_URL = "https://egis.hud.gov/arcgis/rest/services/cpdmaps/HudEnvFemaFlood/MapServer/1/query"


#This is the function we will use for testing to query hud data in order to draw qct and dda areas within our map
def fetchLayerQCT():
    QCTArray = []
    offset = 0
    #We essentially create a loop that will keep requesting data until we get all the qct areas
    while True:
        where = "STATE='09'" # Tells system that we are honing in on the state of Connecticut, 09 is the state code for Connecticut
        url = QCT_URL
        response = {"ok": False}


        try:
            # Here is where we make the actual request to the hud data open api
            response = requests.get(url, params={
                "where": where,
                "outFields": "*",  # Gives us all available data columns
                "returnGeometry": "true",
                "outSR": "4326",  # Tells our source to send back coordinates as latitude and longitude
                "f": "json",  # Ask the hud source to return geo data as clean JSON info
                "resultOffset": offset, #Keeping it as 0 for demo practice purposes
                "resultRecordCount": 50,  # asking for 50 items at a time
            }, timeout=30) #Adding a cool down between request to ensure that we don't raise any red flags
        except Exception as e:
            print("Error while trying to request HUD DATA: ", e)


        if response.status_code == 200:
            response = response.json()
            if(len(response["features"]) < 50):
                #Want to only add to the Array if there is data within the array
                if(len(response["features"]) > 0):
                    QCTArray.extend(response)
                break
            else:
                offset += 50
                time.sleep(0.5)
                QCTArray.extend(response["features"]) #We will add every batch of results to the QCTArray
    return QCTArray


def fetchLayerDDA():
    offset = 0
    DDAArray = []

    while True:
        where = "ZCTA5 LIKE '06%'"  # Tells system that we are honing in on the state of Connecticut, 09 is the state code for Connecticut
        url = DDA_URL
        response = {"ok": False}
        try:
            # Here is where we make the actual request to the hud data open api
            response = requests.get(url, params={
                "where": where,
                "outFields": "*",  # Gives us all available data columns
                "returnGeometry": "true",
                "outSR": "4326",  # Tells our source to send back coordinates as latitude and longitude
                "f": "json",  # Ask the hud source to return geo data as clean JSON info
                "resultOffset": offset,  # Keeping it as 0 for demo practice purposes
                "resultRecordCount": 20,  # asking for 10 items just to see how our computer handles the call
            }, timeout=30)
        except Exception as e:
            print("Error while trying to request HUD DATA: ", e)

        if response.status_code == 200:
            response = response.json()
            if (len(response["features"]) < 20):
                # Want to only add to the Array if there is data within the array
                if (len(response["features"]) > 0):
                    DDAArray.extend(response)
                break
            else:
                offset += 20
                time.sleep(0.5)
                DDAArray.extend(response["features"])  # We will add every batch of results to the QCTArray
    return DDAArray



def fetchFloodZones():
    FLOODArray = []
    offset = 0
    #We essentially create a loop that will keep requesting data until we get all the qct areas
    while True:
        where = "STATE='09'" # Tells system that we are honing in on the state of Connecticut, 09 is the state code for Connecticut
        url = FLOOD_URL
        response = {"ok": False}

        #We will only retrieve 1000 records in order to relieve our computer of stress
        try:
            # Here is where we make the actual request to the hud data open api
            response = requests.get(url, params={
                # Crucial: geometryType tells the API that the geometry string is a bounding box
                "geometryType": "esriGeometryEnvelope",

                # Crucial: spatialReference MUST live inside the geometry JSON string, this is the bounding box for Connecticut
                "geometry": '{"xmin":-73.727, "ymin":40.98, "xmax":-71.787, "ymax":42.05, "spatialReference":{"wkid":4326}}',

                # Tells the server how to evaluate your bounding box geometry
                "spatialRel": "esriSpatialRelIntersects",

                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "json",
                "resultOffset": offset,
                "resultRecordCount": 1000,
            }, timeout=30) #Adding a cool down between request to ensure that we don't raise any red flags
        except Exception as e:
            print("Error while trying to request HUD DATA: ", e)

        if response.status_code: #We want to first check and see if we get a response in the first place
            if response.status_code == 200:
                response = response.json()
                if(len(response["features"]) < 1000):
                    #Want to only add to the Array if there is data within the array
                    if(len(response["features"]) > 0):
                        FLOODArray.extend(response)
                    break
                else:
                    offset += 1000
                    time.sleep(0.2)
                    FLOODArray.extend(response["features"]) #We will add every batch of results to the QCTArray
                    break #Doing this for now since the amount of data we have on flood zones is so much that it makes it hard for our computer to render it
    print("Number of Flood Zones: ", len(FLOODArray))
    return FLOODArray

