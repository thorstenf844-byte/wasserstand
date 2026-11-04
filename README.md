# Wasserstand Norderney, Riffgat

Eine kleine Webseite, die beim Öffnen den aktuellen Wasserstand am Pegel **Norderney, Riffgat** zeigt, dazu den Trend, das nächste Hoch- und Niedrigwasser mit erwartetem Pegel, eine Wasserstandskurve (umschaltbar: 3 Tage oder alle Tage der BSH-Vorhersage, etwa 6 Tage) und eine Tabelle der kommenden Ereignisse.

**Live-Seite:** https://thorstenf844-byte.github.io/wasserstand/wasserstand-norderney.html

Alle Höhen sind in Metern über Pegelnull (PNP). Das mittlere Hochwasser liegt dort bei etwa 6,26 m, das mittlere Niedrigwasser bei etwa 3,83 m.

## Was in diesem Repository liegt

| Datei | Wofür |
|---|---|
| `wasserstand-norderney.html` | Die Webseite selbst (eine einzige Datei mit allem: Aufbau, Aussehen, Programm). |
| `norderney.json` | Die BSH-Vorhersage, automatisch jede Stunde neu abgelegt. Nicht von Hand bearbeiten. |
| `.github/workflows/wasserstand.yml` | Der Automatik-Ablauf, der die Vorhersage stündlich holt und speichert. |
| `.github/scripts/warnung.py` | Prüft stündlich die Vorhersage und schickt eine Push-Warnung (siehe unten). |
| `warnungen.json` | Merkliste, welche Ereignisse schon gemeldet wurden. Wird automatisch geschrieben. |
| `README.md` | Diese Beschreibung. |

## Woher die Daten kommen

- **Gemessener Wasserstand (jetzt):** PEGELONLINE der Wasserstraßen- und Schifffahrtsverwaltung des Bundes. Die Seite fragt ihn bei jedem Öffnen und danach alle 5 Minuten direkt ab.
- **Vorhersage, Gezeiten, Hoch- und Niedrigwasser:** Bundesamt für Seeschifffahrt und Hydrographie (BSH), Lizenz CC BY 4.0.
  Der Browser darf die BSH-Daten nicht direkt abrufen. Deshalb holt GitHub sie jede Stunde (Minute 17) und legt sie als `norderney.json` hier ab. Die Seite liest dann diese Datei.

Bedeutung auf der Seite:
- **Gemessen:** tatsächlich gemessener Wasserstand.
- **Vorhersage:** BSH-Vorhersage inklusive Wetter und Wind („BSH“ oder „Modell“ in der Tabelle).
- **Gezeiten:** reine astronomische Gezeitenvorausberechnung ohne Wetter.

## Push-Warnung

Nach jeder stündlichen Aktualisierung prüft `warnung.py` die nächsten 3 Tage. Wird ein **Hochwasser unter 5,90 m** oder ein **Niedrigwasser unter 3,40 m** erwartet, kommt eine Push-Nachricht über die App **ntfy** aufs Handy. Jedes Ereignis wird nur einmal gemeldet.

- Dieselben Fälle zeigt die Webseite oben als gelben Warnhinweis an, und in der Tabelle sind die betroffenen Höhen markiert.
- Die Grenzen stehen oben in `.github/scripts/warnung.py` (`GRENZE_HOCHWASSER_CM`, `GRENZE_NIEDRIGWASSER_CM`, `TAGE_VORAUS`). Bei einer Änderung auch in `wasserstand-norderney.html` anpassen (`LIMIT_HW`, `LIMIT_NW`, `WARN_DAYS`).
- Der Name des ntfy-Kanals ist als Geheimnis `NTFY_TOPIC` hinterlegt (Einstellungen → Geheimnisse und Variablen → Actions). Er steht bewusst nicht im Repository.
- Weitere Empfänger: einfach in der ntfy-App denselben Kanal abonnieren.
- Test: Actions → „Wasserstandsdaten aktualisieren“ → „Run workflow“ → Haken bei „Testnachricht aufs Handy schicken“.

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
