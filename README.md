# Kirchoff Affordable Housing Site Finder Demo

This is a Flask + HTML + Tailwind CSS + JavaScript demo for the CMPT330L final project.
It includes an interactive Leaflet map, demo property data, filters, property details,
saved properties, notes, and a feasibility calculator.

## Run

```bash
cd kirchoff_demo
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The app will automatically open in your default browser at:

```text
http://127.0.0.1:5000
```

If it does not open automatically, copy that link into Chrome or Edge.

## Demo clicks

1. Click a map pin to update the property panel.
2. Use filters on the left, then click **Apply Filters**.
3. Click **Save Property** and then **Saved Properties**.
4. Click **Add Note**, type a note, and save it.
5. Click **Run Feasibility Calculator** and press **Recalculate**.

## Database note

The demo uses `data/db.json` as a local NoSQL-style database so the presentation runs easily.
For a production version, the same structure can map to Firebase Firestore collections:
`properties`, `notes`, `saved_properties`, `users`, `hud_data`, and `property_images`.


## Requirements
- Make sure you have nodejs installed in order to properly use the tailwind css
- Then run this command to initialize a package management file
```text
npm init -y
```

-Next, install the tailwind CSS compiler library into your project workspace and make it a dependecy in your package.json file
```text
npm install -D tailwindcss@latest
```

- Next, you will run this code below to have tailwind actually read the rules in src.css and then create a css that follows the rules and fits the pages it is monitoring
```text
npx tailwindcss -i ./static/css/src.css -o ./static/css/style.css --watch
```

- If you have the npm version 7 or higher, make sure to add this to the script block within your package.json file so that it has the exact root to where the tailwind engine program is:
`"build:css": "tailwindcss -i ./static/css/src.css -o ./static/css/style.css --watch"`
- You also will need to run this code:
```text
npm install @tailwindcss/cli
```
- and then you can run this code to have tailwind begin to create the required css files
```text
npm run build:css
```


- If you have anything under version 7 for npm, then you don't have to worry and instead can run this commanding your terminal
```text
npx tailwindcss -i ./static/css/src.css -o ./static/css/style.css --watch
```

## API DEMO KEY/MAPS

- Use this link to obtain the demo key (with limited usages) in order to test out the Google Maps api for the project:
https://developers.google.com/maps/documentation/javascript/demo-key
- This link also provides tutorials on how to incorporate the api calls for the Google Maps api along with how to implement their maps


## HELPFUL WEBSITES FOR API DOCUMENTATION AND EXPLANATION

-We also have leaflet as well, and here is the link to their open source that explains exactly how to use it:
https://leafletjs.com/

-We also use this websites map tiles to give our leaflet a background to draw our map on, plus giving attribute to ensure that we give credit back to the website:
https://cloud.maptiler.com/maps/streets-v4/

-Here is a YouTube link that shows how to use leaflet in conjunction with maptiler:
https://www.youtube.com/watch?v=wVnimcQsuwk&list=PLGHe6Moaz52PUNP4DtIshALDogSURIlYB


-Here is the link to the openapi documentation for the hud open source data:
https://hudgis-hud.opendata.arcgis.com/datasets/77572a4428384d2697c476564dcf53f0_0/api

## GEOCODING API TESTING 
- Here we are gonna use a temporary replacement for google maps api
https://geocode.maps.co/



