"""
Kirchoff Affordable Housing Site Finder — Flask Backend
Three-tier: Browser (JS) → Flask (Python) → MongoDB

Terminal shows every DB read/write in real time.
"""
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import logging, threading, webbrowser, os

# ── Logging — prints to terminal in real time ─────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("kirchoff")

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = os.environ.get("MONGO_DB",  "kirchoff_db")
_client   = None

def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client[DB_NAME]

def col_props():  return get_db().properties
def col_notes():  return get_db().notes
def col_saved():  return get_db().saved_properties
def col_runs():   return get_db().feasibility_runs   # NEW — saves calculator runs

NO_ID = {"_id": 0}

def _now():
    return datetime.now().isoformat(timespec="seconds")

def _ts():
    return datetime.now().strftime("%H:%M:%S")

# ── Routes ────────────────────────────────────────────────

@app.route("/")
def index():
    log.info("SERVE  index.html → browser")
    return render_template("index.html")


@app.get("/api/properties")
def get_properties():
    qct       = request.args.get("qct",     "any")
    terrain   = request.args.get("terrain", "any")
    zoning    = request.args.get("zoning",  "any")
    q         = request.args.get("q",       "").strip().lower()
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_acres = request.args.get("min_acres", type=float)
    max_acres = request.args.get("max_acres", type=float)

    query = {}
    if qct     != "any": query["qct_status"]    = qct
    if terrain != "any": query["terrain_level"] = terrain
    if zoning  != "any": query["zoning"]        = {"$regex": f"^{zoning}$", "$options": "i"}
    price_q = {}
    if min_price: price_q["$gte"] = min_price
    if max_price: price_q["$lte"] = max_price
    if price_q:   query["price"]  = price_q
    acres_q = {}
    if min_acres: acres_q["$gte"] = min_acres
    if max_acres: acres_q["$lte"] = max_acres
    if acres_q:   query["size_acres"] = acres_q

    results = list(col_props().find(query, NO_ID))
    if q:
        terms = q.split()
        results = [p for p in results if all(
            t in f"{p.get('property_id','')} {p.get('address','')} {p.get('city','')} {p.get('zip','')}".lower()
            for t in terms)]

    filter_str = " | ".join(f"{k}={v}" for k, v in query.items()) or "none"
    log.info(f"READ   MongoDB.properties  │ filters: {filter_str}  │ → {len(results)} docs returned")
    return jsonify(results)


@app.post("/api/properties")
def add_property():
    data = request.get_json(force=True)
    def flt(k, d=0): return float(str(data.get(k) or d).replace("$","").replace(",","") or d)

    city    = data.get("city", "CT")
    code    = ''.join(c for c in city[:3].upper() if c.isalpha())
    prop_id = f"CT-{code}-{col_props().count_documents({})+1:05d}"
    tlevel  = data.get("terrain_level", "flat")
    qct     = data.get("qct_status",   "none")
    util    = data.get("utilities",    "")

    score = 50
    if tlevel == "flat":                  score += 15
    elif tlevel == "steep":               score -= 22
    if "All Public" in util:              score += 15
    elif "Not Available" in util:         score -= 20
    if qct == "qct":                      score += 12
    elif qct == "dda":                    score += 8
    if "AE" in data.get("fema_zone",""): score -= 10
    acres = flt("size_acres") or 1
    price = flt("price")
    if price and acres:
        ppa = price / acres
        if ppa < 150000: score += 8
        elif ppa > 500000: score -= 12
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
    prop.pop("_id", None)
    log.info(f"INSERT MongoDB.properties  │ new id={prop_id}  city={city}  score={score}%")
    return jsonify({"ok": True, "property": prop, "message": f"{prop_id} added — score {score}%."})


@app.post("/api/notes")
def add_note():
    body        = request.get_json(force=True)
    text        = body.get("note", "").strip()
    property_id = body.get("property_id")
    user_id     = body.get("user_id", "demo_user_001")

    if not text:
        return jsonify({"ok": False, "message": "Note cannot be empty."}), 400
    if not col_props().find_one({"property_id": property_id}, NO_ID):
        return jsonify({"ok": False, "message": "Property not found."}), 404

    note_id = f"note_{col_notes().count_documents({})+1:03d}"
    note = {
        "note_id":     note_id,
        "user_id":     user_id,
        "property_id": property_id,
        "note":        text,
        "created_at":  _now(),
    }
    col_notes().insert_one(note)
    note.pop("_id", None)
    log.info(f"INSERT MongoDB.notes       │ id={note_id}  property={property_id}  user={user_id}  len={len(text)} chars")
    return jsonify({"ok": True, "message": "Note saved.", "note": note})


@app.get("/api/notes/<property_id>")
def get_notes(property_id):
    notes = list(col_notes().find({"property_id": property_id}, NO_ID).sort("created_at", DESCENDING))
    log.info(f"READ   MongoDB.notes       │ property={property_id}  → {len(notes)} notes")
    return jsonify(notes)


@app.post("/api/saved-properties")
def save_property():
    body        = request.get_json(force=True)
    property_id = body.get("property_id")

    if not col_props().find_one({"property_id": property_id}, NO_ID):
        return jsonify({"ok": False, "message": "Property not found."}), 404

    save_id = f"save_{col_saved().count_documents({})+1:03d}"
    save = {"save_id": save_id, "user_id": "demo_user_001",
            "property_id": property_id, "saved_at": _now()}
    try:
        col_saved().insert_one(save)
        log.info(f"INSERT MongoDB.saved       │ id={save_id}  property={property_id}  user=demo_user_001")
        msg = "Property saved to your list."
    except DuplicateKeyError:
        log.info(f"SKIP   MongoDB.saved       │ property={property_id} already saved — no-op")
        msg = "Already in your saved list."

    return jsonify({"ok": True, "message": msg})


@app.get("/api/saved-properties")
def get_saved_properties():
    saved_ids = [s["property_id"] for s in col_saved().find({"user_id": "demo_user_001"}, NO_ID)]
    props     = list(col_props().find({"property_id": {"$in": saved_ids}}, NO_ID))
    log.info(f"READ   MongoDB.saved       │ user=demo_user_001  → {len(props)} saved properties")
    return jsonify(props)


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
    ami            = flt("ami", 91300)
    target_ami_pct = flt("target_ami", 60) / 100

    gross_income        = units * rent * 12
    effective_income    = gross_income * (1 - vacancy)
    noi                 = effective_income * (1 - expenses)
    max_affordable_rent = round(ami * target_ami_pct / 12 * 0.30)
    rent_over_ami       = rent > max_affordable_rent

    cap_rate = dscr = per_unit_cost = tc_equity = score = 0
    if total_cost > 0:
        cap_rate      = round(noi / total_cost * 100, 2)
        annual_debt   = total_cost * 0.90 * 0.035
        dscr          = round(noi / max(1, annual_debt), 2)
        per_unit_cost = round(total_cost / max(1, units))
        tc_equity     = round(max(0, total_cost - land_cost) * 0.09 * 10)
        dscr_score    = min(45, max(0, (dscr - 0.80) / 0.65 * 45))
        cap_score     = min(30, max(0, cap_rate / 6.5 * 30))
        overage       = max(0, (rent - max_affordable_rent) / max(1, max_affordable_rent))
        afford_score  = max(0, 25 - overage * 60) if rent_over_ami else 25
        score         = min(100, round(dscr_score + cap_score + afford_score))

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
    props_n  = col_props().count_documents({})
    notes_n  = col_notes().count_documents({})
    saved_n  = col_saved().count_documents({})
    runs_n   = col_runs().count_documents({})

    high   = col_props().count_documents({"feasibility_score": {"$gte": 70}})
    medium = col_props().count_documents({"feasibility_score": {"$gte": 40, "$lt": 70}})
    low_n  = col_props().count_documents({"feasibility_score": {"$lt": 40}})

    qct_n  = col_props().count_documents({"qct_status": "qct"})
    dda_n  = col_props().count_documents({"qct_status": "dda"})
    none_n = col_props().count_documents({"qct_status": "none"})

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

if __name__ == "__main__":
    _startup_log()
    threading.Timer(1.0, open_browser).start()
    app.run(debug=False, host="127.0.0.1", port=5000)