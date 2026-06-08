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
