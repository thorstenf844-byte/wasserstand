"""Windguru-Vorhersage für Norderney (Spot 20) holen und als windguru.json ablegen.

Nutzt die interne JSON-Schnittstelle, die auch die Windguru-Webseite verwendet.
Hinweis: Windguru erlaubt automatische Abrufe laut Nutzungsbedingungen nicht.
Deshalb: nur ein Abruf pro Lauf und Modell, Pausen dazwischen, und bei jeder
Ablehnung sofort aufhören. Die alte windguru.json bleibt dann einfach liegen.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

from curl_cffi import requests

SPOT = 20                       # Windguru-Spot "Norderney"
MAX_MODELLE = 6                 # höchstens so viele Modelle pro Lauf
PAUSE_S = 2.0                   # Pause zwischen zwei Abrufen
API = "https://www.windguru.cz/int/iapi.php"
ZIEL = os.environ.get("WG_ZIEL", "windguru.json")

# Bevorzugte Reihenfolge (Windguru-Modellnummern). Was der Spot nicht hat, fällt weg.
# 3 = GFS 13 km, 45 = ICON 13 km, 117 = ECMWF, 64/86 = ICON 7 km / ICON-D2, 101/106 = AROME/HARMONIE,
# 84 = GWAM (Wellen), 85 = EWAM (Wellen)
BEVORZUGT = [3, 45, 117, 64, 86, 101, 106, 59, 84, 85]

session = requests.Session(impersonate="chrome")


def hole(params, referer):
    r = session.get(API, params=params, headers={"Referer": referer, "Accept": "application/json"}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"Keine JSON-Antwort: {r.text[:200]}")
    if isinstance(data, dict) and data.get("return") == "error":
        raise RuntimeError(f"Windguru-Fehler: {data}")
    return data


def modell_liste():
    data = hole({"q": "forecast_spot", "id_spot": SPOT}, f"https://www.windguru.cz/{SPOT}")
    spot = (data.get("spots") or {}).get(str(SPOT), {})
    vorhanden = []
    for tab in data.get("tabs") or []:
        for m in tab.get("id_model_arr") or []:
            mid = int(m["id_model"])
            if mid != 100 and mid not in vorhanden:
                vorhanden.append(mid)
    for mid in spot.get("models") or []:
        mid = int(mid)
        if mid != 100 and mid not in vorhanden:
            vorhanden.append(mid)
    sortiert = [m for m in BEVORZUGT if m in vorhanden] + [m for m in vorhanden if m not in BEVORZUGT]
    return spot, sortiert


def umwandeln(fc):
    f = fc.get("fcst") or {}
    init = f.get("initstamp")
    stunden = f.get("hours") or []
    if not init or not stunden:
        return None
    zeiten = [datetime.fromtimestamp(init + h * 3600, tz=timezone.utc).strftime("%Y-%m-%dT%H:%MZ") for h in stunden]

    def reihe(name):
        v = f.get(name)
        return v if isinstance(v, list) and len(v) == len(stunden) else None

    werte = {
        "wind_kn": reihe("WINDSPD"),
        "boeen_kn": reihe("GUST"),
        "richtung": reihe("WINDDIR"),
        "temp": reihe("TMPE") or reihe("TMP"),
        "regen_mm": reihe("APCP1") or reihe("APCP"),
        "wolken": reihe("TCDC"),
        "wellen_m": reihe("HTSGW"),
        "wellen_periode_s": reihe("PERPW"),
        "wellen_richtung": reihe("DIRPW"),
    }
    werte = {k: v for k, v in werte.items() if v is not None}
    if not werte:
        return None
    return {
        "id": f.get("id_model") or fc.get("id_model"),
        "name": f.get("model_name") or fc.get("model"),
        "langname": f.get("model_longname"),
        "lauf": f.get("initdate"),
        "naechstes_update": f.get("update_next"),
        "zeiten": zeiten,
        **werte,
    }


def main():
    spot, modelle = modell_liste()
    print("Modelle am Spot:", modelle)
    ergebnis = []
    for mid in modelle:
        if len(ergebnis) >= MAX_MODELLE:
            break
        time.sleep(PAUSE_S)
        try:
            fc = hole({"q": "forecast", "id_spot": SPOT, "id_model": mid}, f"https://www.windguru.cz/{SPOT}")
        except RuntimeError as e:
            print(f"Modell {mid}: {e}")
            if "HTTP 403" in str(e) or "HTTP 429" in str(e):
                break       # gesperrt oder zu viele Abrufe: sofort aufhören
            continue
        m = umwandeln(fc)
        if m:
            ergebnis.append(m)
            print(f"Modell {mid}: {m['name']} · Lauf {m['lauf']} · {len(m['zeiten'])} Stunden")

    if not any("wind_kn" in m for m in ergebnis):
        print("Keine Winddaten bekommen – alte Datei bleibt.")
        return 1

    out = {
        "abgerufen": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "spot": {"id": SPOT, "name": spot.get("spotname") or "Norderney",
                 "lat": spot.get("lat"), "lon": spot.get("lon")},
        "einheiten": {"wind": "kn", "temp": "°C", "regen": "mm/h", "wellen": "m"},
        "modelle": ergebnis,
    }
    with open(ZIEL + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(ZIEL + ".tmp", ZIEL)
    print("Gespeichert:", ZIEL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
