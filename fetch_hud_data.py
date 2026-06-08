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

OUT = Path(__file__).parent / "static" / "data"
OUT.mkdir(parents=True, exist_ok=True)

# ── HUD ArcGIS REST services (VTyQ9soqVukalItT = HUD org on ArcGIS Online) ──
# Multiple candidate URLs tried in order — HUD occasionally renames services
HUD_ORG  = "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services"

LAYERS = {
    "ct_qct": {
        "label": "Qualified Census Tracts (QCT)",
        "candidates": [
            f"{HUD_ORG}/QCT_2024/FeatureServer/0/query",
            f"{HUD_ORG}/QCT_Current/FeatureServer/0/query",
            f"{HUD_ORG}/SADDA_QCT_2024/FeatureServer/0/query",
            f"{HUD_ORG}/TDAT_AGOL/FeatureServer/0/query",
        ],
        "where": "STUSAB='CT'",
        "where_alt": "STATE_NAME='Connecticut'",
    },
    "ct_dda": {
        "label": "Difficult Development Areas (DDA)",
        "candidates": [
            f"{HUD_ORG}/DDA_2024/FeatureServer/0/query",
            f"{HUD_ORG}/DDA_Current/FeatureServer/0/query",
            f"{HUD_ORG}/SADDA_DDA_2024/FeatureServer/0/query",
            f"{HUD_ORG}/TDAT_AGOL/FeatureServer/1/query",
        ],
        "where": "STUSAB='CT'",
        "where_alt": "STATE_NAME='Connecticut'",
    },
}


def query_service(url: str, where: str) -> list | None:
    """Query one ArcGIS FeatureServer endpoint; paginate if needed. Returns features list or None."""
    features = []
    offset   = 0
    while True:
        try:
            r = requests.get(url, params={
                "where":             where,
                "outFields":         "*",
                "returnGeometry":    "true",
                "outSR":             "4326",
                "f":                 "geojson",
                "resultOffset":      offset,
                "resultRecordCount": 1000,
            }, timeout=25)
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
        features.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
        time.sleep(0.25)

    return features if features else None


def fetch_layer(name: str, cfg: dict) -> bool:
    """Try each candidate URL until one returns data. Save GeoJSON. Return success."""
    print(f"\n{'─'*55}")
    print(f"Fetching {cfg['label']} for Connecticut…")

    for url in cfg["candidates"]:
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