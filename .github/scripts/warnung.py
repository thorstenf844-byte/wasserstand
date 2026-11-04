"""Push-Warnung bei niedrigem Hoch- oder Niedrigwasser (Pegel Norderney, Riffgat).

Liest norderney.json (BSH-Vorhersage) und schickt über ntfy eine Nachricht,
wenn in den nächsten 3 Tagen ein Hochwasser unter 5,90 m oder ein
Niedrigwasser unter 3,40 m erwartet wird. Jedes Ereignis wird nur einmal
gemeldet; gemeldete Ereignisse stehen in warnungen.json.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

GRENZE_HOCHWASSER_CM = 590   # Warnung, wenn ein Hochwasser darunter liegt
GRENZE_NIEDRIGWASSER_CM = 340  # Warnung, wenn ein Niedrigwasser darunter liegt
TAGE_VORAUS = 3
SEITE = "https://thorstenf844-byte.github.io/wasserstand/wasserstand-norderney.html"
GEMELDET = "warnungen.json"
BERLIN = ZoneInfo("Europe/Berlin")
WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def zahl(wert):
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


def wert(ereignis):
    for feld, quelle in (("forecast_value", "BSH"), ("mos_forecast_r0_value", "Modell"), ("tidal_prediction_value", "Gezeiten")):
        v = zahl(ereignis.get(feld))
        if v is not None:
            return v, quelle
    return None, None


def meter(cm):
    return f"{cm / 100:.2f}".replace(".", ",") + " m"


def zeit(t):
    t = t.astimezone(BERLIN)
    return f"{WOCHENTAGE[t.weekday()]} {t.day}.{t.month}., {t:%H:%M} Uhr"


def veroeffentlichen(nachricht):
    daten = json.dumps(nachricht).encode()
    anfrage = urllib.request.Request("https://ntfy.sh/", data=daten, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(anfrage, timeout=30) as antwort:
        antwort.read()


def senden(kanal, titel, text):
    nachricht = {"topic": kanal, "title": titel, "message": text, "click": SEITE, "tags": ["ocean"], "priority": 4}
    veroeffentlichen(nachricht)
    # E-Mail-Kopien laufen über einen Nebenkanal, damit das Handy die Nachricht nicht doppelt bekommt.
    adressen = [a.strip() for a in os.environ.get("NTFY_EMAILS", "").replace(";", ",").split(",") if a.strip()]
    for adresse in adressen:
        try:
            veroeffentlichen({**nachricht, "topic": kanal + "-mail", "message": text + "\n\nAktueller Stand: " + SEITE, "email": adresse})
            print("E-Mail verschickt an Adresse", adressen.index(adresse) + 1)
        except Exception as fehler:
            grund = fehler.read().decode(errors="replace") if hasattr(fehler, "read") else ""
            print("E-Mail an Adresse", adressen.index(adresse) + 1, "fehlgeschlagen:", fehler, grund, file=sys.stderr)


def main():
    kanal = os.environ.get("NTFY_TOPIC", "").strip()
    if not kanal:
        print("Kein ntfy-Kanal hinterlegt (Geheimnis NTFY_TOPIC fehlt) – keine Warnung verschickt.")
        return

    if os.environ.get("TEST") == "true":
        senden(kanal, "Test: Pegel Norderney", "Die Warnung ist eingerichtet. Du bekommst eine Nachricht, wenn ein Hochwasser unter "
               + meter(GRENZE_HOCHWASSER_CM) + " oder ein Niedrigwasser unter " + meter(GRENZE_NIEDRIGWASSER_CM) + " erwartet wird.")
        print("Testnachricht verschickt.")

    with open("norderney.json", encoding="utf-8") as f:
        vorhersage = json.load(f)
    try:
        with open(GEMELDET, encoding="utf-8") as f:
            gemeldet = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        gemeldet = {}

    jetzt = datetime.now(timezone.utc)
    bis = jetzt + timedelta(days=TAGE_VORAUS)
    neu = []
    for e in vorhersage.get("high_water_low_water", []):
        t = datetime.fromisoformat(e["event_timestamp"])
        if not (jetzt < t <= bis):
            continue
        cm, quelle = wert(e)
        if cm is None:
            continue
        hoch = e["event"] == "HW"
        if cm >= (GRENZE_HOCHWASSER_CM if hoch else GRENZE_NIEDRIGWASSER_CM):
            continue
        schluessel = e["event"] + " " + e["event_timestamp"]
        if schluessel in gemeldet:
            continue
        gemeldet[schluessel] = cm
        neu.append(f"{'Hochwasser' if hoch else 'Niedrigwasser'} {zeit(t)}: {meter(cm)} ({quelle})")

    # Vergangene Ereignisse aus der Liste entfernen
    gemeldet = {k: v for k, v in gemeldet.items()
                if datetime.fromisoformat(k.split(" ", 1)[1]) > jetzt - timedelta(days=2)}

    if neu:
        titel = "Niedriger Wasserstand erwartet" if len(neu) == 1 else f"{len(neu)} niedrige Wasserstände erwartet"
        senden(kanal, titel, "\n".join(neu) + "\n\nGrenzen: Hochwasser unter " + meter(GRENZE_HOCHWASSER_CM)
               + ", Niedrigwasser unter " + meter(GRENZE_NIEDRIGWASSER_CM) + ".")
        print("Warnung verschickt:\n" + "\n".join(neu))
    else:
        print("Keine neue Warnung.")

    with open(GEMELDET, "w", encoding="utf-8") as f:
        json.dump(gemeldet, f, ensure_ascii=False, indent=1, sort_keys=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as fehler:  # Warnung darf die Datenaktualisierung nicht verhindern
        print("Warnung fehlgeschlagen:", fehler, file=sys.stderr)
