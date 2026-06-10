"""
Kirchoff Affordable Housing Site Finder — Flask Backend
Three-tier: Browser (JS) → Flask (Python) → MongoDB

Terminal shows every DB read/write in real time.
"""

"""Here we are importing all the required modules to ensure that we can run our application on the web
as well as make calls to our mongo database (this is where we can put in dummy data for now until we 
start making actual API calls"""
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import logging, threading, webbrowser, os

# ── Logging — prints to terminal in real time ─────────────
#Here we are establishing pythons basic logging function to set rules for what it should log in the terminal
logging.basicConfig(
    level=logging.INFO, #Tells our logging system to log only normal operations and to ignore minor debug issues
    format="%(asctime)s  %(levelname)-5s  %(message)s", #Formats each logged message within the terminal to show
    #The time of update or status, the kind of info being reported on, and the actual description of said process
    datefmt="%H:%M:%S", #We only want the hour, minute, and second that this happens
)
log = logging.getLogger("kirchoff") #Lets the system know that this logger just applies to the Kirchhoff related code

app = Flask(__name__) #Initates the backend web Server

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = os.environ.get("MONGO_DB",  "kirchoff_db")
_client   = None

#This function will open up a connection to the database once a request to the databse has been made
#We will also use this to keep that connection open and to reusue the database connection instead
#of opening a new one everytime a request is made
def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) #Mongo has 5 seconds to make a connection, or else it will throw an error
    return _client[DB_NAME]

#Provides a function shortcut for each request to each collection that we have within our system
def col_props():  return get_db().properties
def col_notes():  return get_db().notes
def col_saved():  return get_db().saved_properties
def col_runs():   return get_db().feasibility_runs   # NEW — saves calculator runs

#This prevents our system from sending the objectID assigned to each row in mongodb to the browser to
#prevent any type errors from coming up
NO_ID = {"_id": 0}

#Function will calculate the current time for the sake of our code
def _now():
    return datetime.now().isoformat(timespec="seconds")

def _ts():
    return datetime.now().strftime("%H:%M:%S")

# ── Routes ────────────────────────────────────────────────

#This is our home route which will be where users are directed when they first enter our website
@app.route("/")
def index():
    log.info("SERVE  index.html → browser")
    return render_template("index.html")


#Route used to gain the properties from the database
@app.get("/api/properties")
def get_properties():
    #We use the request.args.get to get the data passed in the url
    #Each line ask for a specific key value, and if it can't find a value for that key, then it will
    #just label it as any
    qct       = request.args.get("qct",     "any")
    terrain   = request.args.get("terrain", "any")
    zoning    = request.args.get("zoning",  "any")
    q         = request.args.get("q",       "").strip().lower()

    #We use the types to convert the string data we get from the url to its respective data type
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_acres = request.args.get("min_acres", type=float)
    max_acres = request.args.get("max_acres", type=float)

    #Here we store all the data values we retrieved from the url into our query list, only storing the
    #data if there was something present in there
    query = {}
    if qct     != "any": query["qct_status"]    = qct
    if terrain != "any": query["terrain_level"] = terrain
    if zoning  != "any": query["zoning"]        = {"$regex": f"^{zoning}$", "$options": "i"} #This will match the users input with data in our system, regardless of whether it be uppercase or lowercase
    price_q = {}
    if min_price: price_q["$gte"] = min_price
    if max_price: price_q["$lte"] = max_price
    if price_q:   query["price"]  = price_q
    acres_q = {}
    if min_acres: acres_q["$gte"] = min_acres
    if max_acres: acres_q["$lte"] = max_acres
    if acres_q:   query["size_acres"] = acres_q

    #Passes our query statment to the property finder, ensuring that mongodb does not send back the
    #objectId
    results = list(col_props().find(query, NO_ID))

    #Here we are essntially taking the address provided by the user and checking to see how many
    #properties contain all those words within their full address. If they do, they will be rendered
    #as an option
    if q:
        terms = q.split()
        results = [p for p in results if all(
            t in f"{p.get('property_id','')} {p.get('address','')} {p.get('city','')} {p.get('zip','')}".lower()
            for t in terms)]

    #This is where we put all the url arguments into a string to log in the terminal
    filter_str = " | ".join(f"{k}={v}" for k, v in query.items()) or "none"

    #Gives us an update and summary of the filtering process
    log.info(f"READ   MongoDB.properties  │ filters: {filter_str}  │ → {len(results)} docs returned")
    return jsonify(results)

#Route used to add properties to our properties database
@app.post("/api/properties")
def add_property():
    data = request.get_json(force=True) #We use this to make sure that flask parses the incoming payload as json
    def flt(k, d=0): return float(str(data.get(k) or d).replace("$","").replace(",","") or d) #This will convert the users text into raw decimal number notation by removing any unwanted characters. Else, it will revert to the value 0 if nothing is inputed

    #We use this to assign an id to each property based off of the city it is in
    city    = data.get("city", "CT")
    code    = ''.join(c for c in city[:3].upper() if c.isalpha())
    prop_id = f"CT-{code}-{col_props().count_documents({})+1:05d}"
    tlevel  = data.get("terrain_level", "flat")
    qct     = data.get("qct_status",   "none")
    util    = data.get("utilities",    "")

    #We used the recieved values from the property that is added to calculate a score fo it in terms
    #of its fesability
    score = 50
    if tlevel == "flat":                  score += 15
    elif tlevel == "steep":               score -= 22
    if "All Public" in util:              score += 15
    elif "Not Available" in util:         score -= 20

    #Used to see if the property owner qualifies for low income housing tax credits
    if qct == "qct":                      score += 12
    elif qct == "dda":                    score += 8

    #To see if the house sits in a high risk fema zone
    if "AE" in data.get("fema_zone",""): score -= 10

    acres = flt("size_acres") or 1
    price = flt("price")
    if price and acres:
        ppa = price / acres
        if ppa < 150000: score += 8
        elif ppa > 500000: score -= 12
    #Keeps score within a 5% to 99% percent range
    score = max(5, min(99, score))

    prop = {
        "property_id":    prop_id,
        "address":        data.get("address", ""),
        "city":           city, "state": "CT",
        "zip":            data.get("zip", ""),
        "price":          int(flt("price")),
        "size_acres":     round(flt("size_acres"), 2),
        "property_type":  "Land",
        "zoning":         data.get("zoning", "Residential"),
        "utilities":      util,
        "terrain":        {"flat":"Flat (3%)","moderate":"Moderate (8%)","steep":"Steep (18%)"}.get(tlevel,"Flat (3%)"),
        "terrain_level":  tlevel,
        "qct_status":     qct,
        "dda_status":     qct == "dda",
        "fema_zone":      data.get("fema_zone", "Zone X"),
        "feasibility_score": score,
        "lat":            flt("lat", 41.63),
        "lng":            flt("lng", -72.75),
        "image_url":      "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800",
        "last_updated":   datetime.now().strftime("%b %d, %Y %I:%M %p"),
        "zoning_details": None,
        "demographics":   None,
    }
    col_props().insert_one(prop)
    # We remove the id so that the user doesn't see it when we send the response feedback back to them
    prop.pop("_id", None)
    log.info(f"INSERT MongoDB.properties  │ new id={prop_id}  city={city}  score={score}%")
    return jsonify({"ok": True, "property": prop, "message": f"{prop_id} added — score {score}%."})

#This route will handle user notes on specific properties, ensuring that it is tied to the user and
#the specific property being noted on
@app.post("/api/notes")
def add_note():
    body        = request.get_json(force=True)
    text        = body.get("note", "").strip()
    property_id = body.get("property_id")
    user_id     = body.get("user_id", "demo_user_001") #Use demo_user_001 as default in case there isn't a userid set up

    if not text:
        return jsonify({"ok": False, "message": "Note cannot be empty."}), 400
    if not col_props().find_one({"property_id": property_id}, NO_ID):
        return jsonify({"ok": False, "message": "Property not found."}), 404

    #May need to add a check here for userid as well to ensure that the user is logged in before adding
    #a note, but for now we don't have to since we are in the testing and demo phases

    #This is how we will add an identifier to the note
    note_id = f"note_{col_notes().count_documents({})+1:03d}"
    note = {
        "note_id":     note_id,
        "user_id":     user_id,
        "property_id": property_id,
        "note":        text,
        "created_at":  _now(),
    }
    col_notes().insert_one(note)
    #We remove the id so that the user doesn't see it when we send the response feedback back to them
    note.pop("_id", None)
    log.info(f"INSERT MongoDB.notes       │ id={note_id}  property={property_id}  user={user_id}  len={len(text)} chars")
    return jsonify({"ok": True, "message": "Note saved.", "note": note})


#This function will obtain the notes pertaining to the property in question and order them descending based off the time they came in
@app.get("/api/notes/<property_id>")
def get_notes(property_id):
    notes = list(col_notes().find({"property_id": property_id}, NO_ID).sort("created_at", DESCENDING))
    log.info(f"READ   MongoDB.notes       │ property={property_id}  → {len(notes)} notes")
    return jsonify(notes)

#This function will allow users to save properties that they are interested in
@app.post("/api/saved-properties")
def save_property():
    body        = request.get_json(force=True)
    property_id = body.get("property_id")
    #May want to add a user_id portion here in order to assign the user to the saved property

    if not col_props().find_one({"property_id": property_id}, NO_ID):
        return jsonify({"ok": False, "message": "Property not found."}), 404

    save_id = f"save_{col_saved().count_documents({})+1:03d}"
    save = {"save_id": save_id, "user_id": "demo_user_001",
            "property_id": property_id, "saved_at": _now()}

    #Used to ensure that we are not saving duplicate houses to the same user
    try:
        col_saved().insert_one(save)
        log.info(f"INSERT MongoDB.saved       │ id={save_id}  property={property_id}  user=demo_user_001")
        msg = "Property saved to your list."
    except DuplicateKeyError:
        log.info(f"SKIP   MongoDB.saved       │ property={property_id} already saved — no-op")
        msg = "Already in your saved list."

    return jsonify({"ok": True, "message": msg})


#Used to get the saved properties for a specific user
@app.get("/api/saved-properties")
def get_saved_properties():
    #Gets the property_ids that are saved under the user, making sure not to return the objectID
    saved_ids = [s["property_id"] for s in col_saved().find({"user_id": "demo_user_001"}, NO_ID)]
    #Collects all the properties that have a match to any of the property ids in the list
    props     = list(col_props().find({"property_id": {"$in": saved_ids}}, NO_ID))
    log.info(f"READ   MongoDB.saved       │ user=demo_user_001  → {len(props)} saved properties")
    return jsonify(props)

#Function is used to calculate the fesabilty of a property
@app.post("/api/feasibility")
def feasibility():
    data = request.get_json(force=True)
    def flt(k, d=0): return float(str(data.get(k) or d).replace("$","").replace(",","") or d)

    units          = flt("units")
    rent           = flt("rent")
    vacancy        = flt("vacancy", 5)   / 100
    expenses       = flt("expenses", 32) / 100
    total_cost     = flt("total_cost")
    land_cost      = flt("land_cost")
    ami            = flt("ami", 91300) #Area Median Income
    target_ami_pct = flt("target_ami", 60) / 100

    gross_income        = units * rent * 12 #maximum possible income that can be collected
    effective_income    = gross_income * (1 - vacancy) #Provides a more realistic peak income
    noi                 = effective_income * (1 - expenses) #Factors in expenses to get the net income
    max_affordable_rent = round(ami * target_ami_pct / 12 * 0.30) #This calculates the maximum that the rent can be in comparison to the target families income and how much they make in comparison to the average median income
    rent_over_ami       = rent > max_affordable_rent

    cap_rate = dscr = per_unit_cost = tc_equity = score = 0
    if total_cost > 0:
        cap_rate      = round(noi / total_cost * 100, 2) #calculates how much income a property generates relative to its cost and value
        annual_debt   = total_cost * 0.90 * 0.035
        dscr          = round(noi / max(1, annual_debt), 2) #Used to see how much money a property has to pay off their bank loan (since usually banks give a loan for properties)
        per_unit_cost = round(total_cost / max(1, units))
        tc_equity     = round(max(0, total_cost - land_cost) * 0.09 * 10)
        dscr_score    = min(45, max(0, (dscr - 0.80) / 0.65 * 45))
        cap_score     = min(30, max(0, cap_rate / 6.5 * 30))
        overage       = max(0, (rent - max_affordable_rent) / max(1, max_affordable_rent))
        afford_score  = max(0, 25 - overage * 60) if rent_over_ami else 25
        score         = min(100, round(dscr_score + cap_score + afford_score))

    #Final feasability calculations based off total score
    label = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    log.info(f"CALC   Feasibility          │ units={int(units)}  rent=${rent:.0f}  noi=${noi:,.0f}  dscr={dscr}  → {label} ({score}%)")

    return jsonify({
        "gross_income": round(gross_income, 2), "effective_income": round(effective_income, 2),
        "noi": round(noi, 2), "cap_rate": cap_rate, "score": score, "label": label,
        "max_affordable_rent": max_affordable_rent, "rent_over_ami": rent_over_ami,
        "dscr": dscr, "per_unit_cost": per_unit_cost, "tc_equity_estimate": tc_equity,
        "message": f"Feasibility: {label} ({score}%)",
    })


@app.post("/api/feasibility/save")
def save_feasibility_run():
    """Persist a feasibility calculator run to MongoDB."""
    body        = request.get_json(force=True)
    property_id = body.get("property_id", "unknown")
    run_id      = f"run_{col_runs().count_documents({})+1:04d}"

    run = {
        "run_id":      run_id,
        "property_id": property_id,
        "user_id":     "demo_user_001",
        "inputs":      body.get("inputs", {}),
        "results":     body.get("results", {}),
        "created_at":  _now(),
    }
    col_runs().insert_one(run)
    run.pop("_id", None)
    log.info(f"INSERT MongoDB.feas_runs   │ id={run_id}  property={property_id}  score={body.get('results',{}).get('score','?')}%")
    return jsonify({"ok": True, "run_id": run_id, "message": f"Feasibility run {run_id} saved."})


@app.get("/api/stats")
def get_stats():
    """Live database stats — used by the Stats Dashboard panel."""
    #Pretty much just calculates the amount of inputs in each section
    props_n  = col_props().count_documents({})
    notes_n  = col_notes().count_documents({})
    saved_n  = col_saved().count_documents({})
    runs_n   = col_runs().count_documents({})

    #Shows us the amount of high, medium, and low fesability scores
    high   = col_props().count_documents({"feasibility_score": {"$gte": 70}})
    medium = col_props().count_documents({"feasibility_score": {"$gte": 40, "$lt": 70}})
    low_n  = col_props().count_documents({"feasibility_score": {"$lt": 40}})

    #Amount of data for each status
    qct_n  = col_props().count_documents({"qct_status": "qct"})
    dda_n  = col_props().count_documents({"qct_status": "dda"})
    none_n = col_props().count_documents({"qct_status": "none"})

    #We get the most recent values for notes, saved properties, and runs as well
    recent_notes = list(col_notes().find({}, NO_ID).sort("created_at", DESCENDING).limit(5))
    recent_saved = list(col_saved().find({}, NO_ID).sort("saved_at",  DESCENDING).limit(5))
    recent_runs  = list(col_runs().find({},  NO_ID).sort("created_at",DESCENDING).limit(5))

    log.info(f"READ   MongoDB.stats        │ props={props_n}  notes={notes_n}  saved={saved_n}  runs={runs_n}")
    return jsonify({
        "counts":  {"properties": props_n, "notes": notes_n, "saved": saved_n, "feasibility_runs": runs_n},
        "feasibility_dist": {"high": high, "medium": medium, "low": low_n},
        "hud_dist":  {"qct": qct_n, "dda": dda_n, "none": none_n},
        "recent_notes": recent_notes,
        "recent_saved": recent_saved,
        "recent_runs":  recent_runs,
    })


# ── Startup ───────────────────────────────────────────────

def _startup_log():
    try:
        db   = get_db()
        p, n, s, r = (
            db.properties.count_documents({}),
            db.notes.count_documents({}),
            db.saved_properties.count_documents({}),
            db.feasibility_runs.count_documents({}) if "feasibility_runs" in db.list_collection_names() else 0,
        )
        log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log.info("  Kirchoff Housing Site Finder — Flask Server ")
        log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log.info(f"  MongoDB  : {MONGO_URI}{DB_NAME}")
        log.info(f"  Database : {DB_NAME}")
        log.info(f"  Collections:")
        log.info(f"    properties       = {p} documents")
        log.info(f"    notes            = {n} documents")
        log.info(f"    saved_properties = {s} documents")
        log.info(f"    feasibility_runs = {r} documents")
        log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log.info("  Server   : http://127.0.0.1:5000")
        log.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    except Exception as e:
        log.error(f"MongoDB connection failed: {e}")

def open_browser():
    if os.environ.get("NO_BROWSER") == "1": return
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__": #Run only if launched from this terminal
    _startup_log()
    threading.Timer(1.0, open_browser).start()
    app.run(debug=False, host="127.0.0.1", port=5000)