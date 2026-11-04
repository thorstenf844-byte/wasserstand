# Wasserstand Norderney, Riffgat

Eine kleine Webseite, die beim Öffnen den aktuellen Wasserstand am Pegel **Norderney, Riffgat** zeigt, dazu den Trend, das nächste Hoch- und Niedrigwasser mit erwartetem Pegel, eine Wasserstandskurve und eine Tabelle der kommenden Ereignisse.

**Live-Seite:** https://thorstenf844-byte.github.io/wasserstand/wasserstand-norderney.html

Alle Höhen sind in Metern über Pegelnull (PNP). Das mittlere Hochwasser liegt dort bei etwa 6,26 m, das mittlere Niedrigwasser bei etwa 3,83 m.

## Was in diesem Repository liegt

| Datei | Wofür |
|---|---|
| `wasserstand-norderney.html` | Die Webseite selbst (eine einzige Datei mit allem: Aufbau, Aussehen, Programm). |
| `norderney.json` | Die BSH-Vorhersage, automatisch jede Stunde neu abgelegt. Nicht von Hand bearbeiten. |
| `.github/workflows/wasserstand.yml` | Der Automatik-Ablauf, der die Vorhersage stündlich holt und speichert. |
| `README.md` | Diese Beschreibung. |

## Woher die Daten kommen

- **Gemessener Wasserstand (jetzt):** PEGELONLINE der Wasserstraßen- und Schifffahrtsverwaltung des Bundes. Die Seite fragt ihn bei jedem Öffnen und danach alle 5 Minuten direkt ab.
- **Vorhersage, Gezeiten, Hoch- und Niedrigwasser:** Bundesamt für Seeschifffahrt und Hydrographie (BSH), Lizenz CC BY 4.0.
  Der Browser darf die BSH-Daten nicht direkt abrufen. Deshalb holt GitHub sie jede Stunde (Minute 17) und legt sie als `norderney.json` hier ab. Die Seite liest dann diese Datei.

Bedeutung auf der Seite:
- **Gemessen:** tatsächlich gemessener Wasserstand.
- **Vorhersage:** BSH-Vorhersage inklusive Wetter und Wind („BSH“ oder „Modell“ in der Tabelle).
- **Gezeiten:** reine astronomische Gezeitenvorausberechnung ohne Wetter.

## Wie die Seite online ist

GitHub Pages veröffentlicht die Dateien aus dem Zweig `main` (Einstellungen → Seiten → „Einsatz von einer Zweigstelle aus“, Zweig `main`, Ordner `/ (root)`).
Wichtig: Das Repository muss **öffentlich** bleiben. Bei „Privat“ ist die Seite mit einem kostenlosen Konto nicht mehr erreichbar.

## Wenn etwas nicht stimmt

| Problem | Was prüfen |
|---|---|
| Roter Fehlerhinweis, kein aktueller Wert | PEGELONLINE kurz nicht erreichbar. Später „Jetzt aktualisieren“ tippen. |
| Kurve oder Tabelle fehlen, oder Vorhersage ist sehr alt | Reiter „Actions“ öffnen: Ist der letzte Lauf von „Wasserstandsdaten aktualisieren“ grün? Bei Rot: Lauf öffnen und Fehlermeldung ansehen, oder über „Run workflow“ von Hand starten. |
| Seite gar nicht erreichbar | Einstellungen → Seiten prüfen, ob Pages noch eingeschaltet ist, und ob das Repository öffentlich ist. |
| Automatik läuft nicht mehr | GitHub schaltet geplante Abläufe ab, wenn 60 Tage lang nichts im Repository passiert ist. Unter „Actions“ wieder aktivieren. Durch die stündlichen Speicherungen sollte das normalerweise nicht passieren. |

## Änderungen machen

Änderungen an der Seite gehören in `wasserstand-norderney.html`. Nach dem Speichern („Commit-Änderungen“) dauert es ein bis zwei Minuten, bis die Live-Seite neu ist.
Wer mit Claude weiterarbeitet: in einem neuen Chat dieses Repository verbinden und Claude zuerst diese README lesen lassen.

## Quellen

- PEGELONLINE: https://www.pegelonline.wsv.de
- BSH Wasserstandsvorhersage: https://www.bsh.de (Daten unter CC BY 4.0)
