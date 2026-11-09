"""Push-Warnung bei auffälligem Hoch- oder Niedrigwasser (Pegel Norderney, Riffgat).

Liest norderney.json (BSH-Vorhersage) und schickt über ntfy eine Nachricht,
wenn in den nächsten 3 Tagen eine Sturmflut (Hochwasser über 7,00 m),
ein niedriges Hochwasser (unter 5,80 m) oder ein Niedrigwasser unter 3,40 m
erwartet wird. Jedes Ereignis wird nur einmal
gemeldet; gemeldete Ereignisse stehen in warnungen.json.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

GRENZE_HOCHWASSER_CM = 580   # Warnung, wenn ein Hochwasser darunter liegt
GRENZE_HOCHWASSER_HOCH_CM = 700  # Warnung, wenn ein Hochwasser darüber liegt
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


def senden(kanal, titel, text, prioritaet=4):
    nachricht = {"topic": kanal, "title": titel, "message": text, "click": SEITE, "tags": ["ocean"], "priority": prioritaet}
    veroeffentlichen(nachricht)



def main():
    kanal = os.environ.get("NTFY_TOPIC", "").strip()
    if not kanal:
        print("Kein ntfy-Kanal hinterlegt (Geheimnis NTFY_TOPIC fehlt) – keine Warnung verschickt.")
        return

    if os.environ.get("TEST") == "true":
        senden(kanal, "Test: Pegel Norderney", "Die Warnung ist eingerichtet. Du bekommst eine Nachricht, wenn eine Sturmflut über "
               + meter(GRENZE_HOCHWASSER_HOCH_CM) + ", ein niedriges Hochwasser unter " + meter(GRENZE_HOCHWASSER_CM) + " oder ein Niedrigwasser unter " + meter(GRENZE_NIEDRIGWASSER_CM) + " erwartet wird.")
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
    arten = []
    for e in vorhersage.get("high_water_low_water", []):
        t = datetime.fromisoformat(e["event_timestamp"])
        if not (jetzt < t <= bis):
            continue
        cm, quelle = wert(e)
        if cm is None:
            continue
        hoch = e["event"] == "HW"
        zu_hoch = hoch and cm > GRENZE_HOCHWASSER_HOCH_CM
        zu_niedrig = cm < (GRENZE_HOCHWASSER_CM if hoch else GRENZE_NIEDRIGWASSER_CM)
        if not (zu_hoch or zu_niedrig):
            continue
        schluessel = e["event"] + " " + e["event_timestamp"]
        if schluessel in gemeldet:
            continue
        art = "Sturmflut" if zu_hoch else ("Niedriges Hochwasser" if hoch else "Niedrigwasser")
        if art not in arten:
            arten.append(art)
        gemeldet[schluessel] = cm
        mittel = zahl(vorhersage.get("mean_high_water" if hoch else "mean_low_water"))
        abstand = ""
        if mittel is not None:
            d = round(cm - mittel)
            abstand = f"{abs(d)} cm {'unter' if d < 0 else 'über'} {'MHW' if hoch else 'MNW'}, " if d else f"genau {'MHW' if hoch else 'MNW'}, "
        neu.append(f"{art} {zeit(t)}: {meter(cm)} ({abstand}{quelle})")

    # Vergangene Ereignisse aus der Liste entfernen
    gemeldet = {k: v for k, v in gemeldet.items()
                if datetime.fromisoformat(k.split(" ", 1)[1]) > jetzt - timedelta(days=2)}

    if neu:
        reihenfolge = ["Sturmflut", "Niedriges Hochwasser", "Niedrigwasser"]
        namen = [a if i == 0 else a.replace("Niedriges", "niedriges") for i, a in enumerate(sorted(arten, key=reihenfolge.index))]
        titel = (", ".join(namen[:-1]) + " und " + namen[-1] if len(namen) > 1 else namen[0]) + " erwartet"
        senden(kanal, titel, "\n".join(neu) + "\n\nAlarmgrenzen: Sturmflut über " + meter(GRENZE_HOCHWASSER_HOCH_CM)
               + ", niedriges Hochwasser unter " + meter(GRENZE_HOCHWASSER_CM) + ", Niedrigwasser unter " + meter(GRENZE_NIEDRIGWASSER_CM) + ".",
               5 if "Sturmflut" in arten else 4)
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
