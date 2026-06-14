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
HUD_ORG  = "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services"

#This will be our url for getting QCT geographical points in order to plot them on our map
QCT_URL  = "https://services.arcgis.com/VTyQ9soqVukalItT/ArcGIS/rest/services/QUALIFIED_CENSUS_TRACTS_2026/FeatureServer/0/query"
#This will be the url base for getting the dda geographical points in order to plot them on our map
DDA_URL = "https://services.arcgis.com/VTyQ9soqVukalItT/ArcGIS/rest/services/Difficult_Development_Areas_2026/FeatureServer/0/query"


#Here we have various url meshes to ensure that if one url link doesn't go through we can then try
#a different candidate
LAYERS = {
    "ct_qct": {
        "label": "Qualified Census Tracts (QCT)",
        "candidates": [
            f"{HUD_ORG}/QCT_2024/FeatureServer/0/query",
            f"{HUD_ORG}/QCT_Current/FeatureServer/0/query",
            f"{HUD_ORG}/SADDA_QCT_2024/FeatureServer/0/query",
            f"{HUD_ORG}/TDAT_AGOL/FeatureServer/0/query",
        ],
        "where": "STUSAB='CT'", #Narrows geospatial data to just the places in connection
        "where_alt": "STATE_NAME='Connecticut'", #Gives the full state name
    },
    "ct_dda": {
        "label": "Difficult Development Areas (DDA)",
        "candidates": [
            f"{HUD_ORG}/DDA_2024/FeatureServer/0/query",
            f"{HUD_ORG}/DDA_Current/FeatureServer/0/query",
            f"{HUD_ORG}/SADDA_DDA_2024/FeatureServer/0/query",
            f"{HUD_ORG}/TDAT_AGOL/FeatureServer/1/query",
        ],
        "where": "STUSAB='CT'", #Narrows geospatial data to just the places in connection
        "where_alt": "STATE_NAME='Connecticut'", #Gives the full state name
    },
}


def query_service(url: str, where: str) -> list | None:
    """Query one ArcGIS FeatureServer endpoint; paginate if needed. Returns features list or None."""
    features = [] #Where we will store our map data
    offset   = 0 #

    #We will keep requesting hud data until the hud data we receive is less than the requested threshold
    while True:
        try:
            r = requests.get(url, params={
                "where":             where,
                "outFields":         "*", #Gives us all available data columns
                "returnGeometry":    "true",
                "outSR":             "4326", #Tells our source to send back coordinates as latitude and longitude
                "f":                 "geojson", #Ask the hud source to return geo data as clean JSON info
                "resultOffset":      offset,
                "resultRecordCount": 1000, #asking for a chunk of 1,000 items
            }, timeout=25) #Request will hang for 25 seconds before ending attempt to connect instead of waiting forever
        except requests.RequestException as exc:
            print(f"    ✗ Request failed: {exc}")
            return None

        if r.status_code != 200:
            print(f"    ✗ HTTP {r.status_code}")
            return None

        try:
            data = r.json()
        except Exception:
            print("    ✗ Response is not JSON")
            return None

        # ArcGIS returns {"error": ...} for invalid services
        if "error" in data:
            print(f"    ✗ ArcGIS error: {data['error'].get('message','unknown')}")
            return None

        batch = data.get("features", [])
        features.extend(batch) #Appends all the geometric data to our features dictionary or array
        if len(batch) < 1000:
            break
        offset += 1000
        time.sleep(0.5) #Creates a cooldown time in between each request to ensure that we don't
        #get caught rapid fire requesting from the hud system

    return features if features else None


def fetch_layer(name: str, cfg: dict) -> bool:
    """Try each candidate URL until one returns data. Save GeoJSON. Return success."""
    print(f"\n{'─'*55}")
    print(f"Fetching {cfg['label']} for Connecticut…") #Tells us which federal dataset we are trying to download

    #Pulls all possible url endpoints that you have in your configuration file to test and see which one works
    for url in cfg["candidates"]:
        #Cleans up url to make it easier to read and also ensures that the print statement adds a result status right next to the url that was tried so that we can know if it worked or not
        short = url.split("/arcgis/")[0].split("/")[-1] + "/" + url.split("FeatureServer")[1]
        print(f"  Trying …{short} ", end="", flush=True)

        # Try primary WHERE clause, then alternate
        for where in (cfg["where"], cfg["where_alt"]):
            features = query_service(url, where)
            if features is not None:
                print(f"→ {len(features)} features ✓")
                geojson = {"type": "FeatureCollection", "features": features}
                out_path = OUT / f"{name}.geojson"
                out_path.write_text(json.dumps(geojson), encoding="utf-8")
                print(f"  Saved → {out_path}")
                return True

        print()  # newline after the failed attempt line

    print(f"\n  ✗ Could not fetch {cfg['label']}.")
    print(f"    Manual fallback: download shapefile from")
    print(f"    https://www.huduser.gov/portal/sadda/sadda_qct.html")
    print(f"    then convert to GeoJSON and save as static/data/{name}.geojson")
    return False

#This is the function we will use for testing to query hud data in order to draw qct and dda areas within our map
def fetchLayerQCT():
    where = "STATE='09'" # Tells system that we are honing in on the state of Connecticut, 09 is the state code for Connecticut
    url = QCT_URL
    offset = 0
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
            "resultRecordCount": 1000,  # asking for 10 items just to see how our computer handles the call
        },)
    except Exception as e:
        print("Error while trying to request HUD DATA: ", e)
    finally:

        if(response.status_code == 200):
            return response.json()
        else:
            return {"ok": False}

def fetchLayerDDA():
    where = "ZCTA5 LIKE '06%'" # Tells system that we are honing in on the state of Connecticut, 09 is the state code for Connecticut
    url = DDA_URL
    offset = 0
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
            "resultRecordCount": 1000,  # asking for 10 items just to see how our computer handles the call
        }, )
    except Exception as e:
        print("Error while trying to request HUD DATA: ", e)
    finally:

        if (response.status_code == 200):
            return response.json()
        else:
            return {"ok": False}


def main():
    print("HUD 2024 QCT / DDA Data Fetcher — Connecticut")
    print("=" * 55)

    results = {name: fetch_layer(name, cfg) for name, cfg in LAYERS.items()}

    print(f"\n{'='*55}")
    print("Summary:")
    for name, ok in results.items():
        status = "✓  saved" if ok else "✗  not fetched (app uses placeholder shapes)"
        print(f"  {name}.geojson  →  {status}")

    if any(results.values()):
        print("\nRestart app.py to load the real boundaries.")


if __name__ == "__main__":
    main()