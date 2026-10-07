# Scratch Transpiler v4.0

Schreibe Scratch-Projekte in einer Java-ähnlichen Syntax und kompiliere sie direkt zu einer `.sb3`-Datei, die du in [Scratch](https://scratch.mit.edu) oder [TurboWarp](https://turbowarp.org) öffnen kannst.

---

## Installation & Voraussetzungen

- **Python 3.10+**
- **Pillow** (optional, für Rasterbilder wie PNG/JPG):
  ```bash
  pip install Pillow
  ```

---

## Aufruf

```bash
python scratch_transpiler.py <eingabe.java> [Optionen]
```

### Flags

| Flag | Bedeutung |
|---|---|
| `--out <datei.sb3>` | Ausgabedatei (Standard: `output.sb3`) |
| `--watch` | Watch-Modus: kompiliert automatisch bei jeder Speicherung |
| `--turbowarp-new` | Startet TurboWarp Desktop nach der Kompilierung (bestehende Instanzen bleiben) |
| `--turbowarp-replace` | Beendet laufende TurboWarp-Instanz und startet sie neu (praktisch zum Refreshen) |
| `--scratch-new` | Startet Scratch Desktop nach der Kompilierung (bestehende Instanzen bleiben)
| `--scratch-replace` | Beendet laufende Scratch-Instanz und startet sie neu
| `--help` | Hilfe anzeigen |

### Beispiele

```bash
# Einmalig kompilieren
python scratch_transpiler.py meinSpiel.java

# Mit Ausgabedatei
python scratch_transpiler.py meinSpiel.java --out meinSpiel.sb3

# Watch-Modus + TurboWarp automatisch refreshen
python scratch_transpiler.py meinSpiel.java --watch --turbowarp-replace

# Watch-Modus + Scratch automatisch refreshen
python scratch_transpiler.py meinSpiel.java --watch --scratch-replace

# Neue TurboWarp-Instanz öffnen (alte bleibt)
python scratch_transpiler.py meinSpiel.java --turbowarp-new
```

---

## Dateistruktur

```
mein_projekt/
 ├── scratch_transpiler.py
 ├── meinSpiel.java        ← dein Code
 ├── katze.png             ← Bilder im gleichen Ordner
 ├── explosion.wav         ← Sounds im gleichen Ordner
 └── meinSpiel.sb3         ← wird automatisch erzeugt
```

---

## Vollständige Syntax-Referenz

### Erweiterungen importieren

Scratch-Erweiterungen werden mit `import` am Anfang der Datei oder innerhalb eines Sprites aktiviert:

```java
import "pen";
import "music";
import "text2speech";
```

Verfügbare Erweiterungen:

| Name | Scratch-Erweiterung |
|---|---|
| `"pen"` | Stift |
| `"music"` | Musik |
| `"video"` / `"video sensing"` | Video-Sensing |
| `"text2speech"` / `"tts"` / `"text to speech"` | Text zu Sprache |
| `"translate"` | Übersetzen |
| `"makey"` / `"makey makey"` | Makey Makey |
| `"microbit"` | micro:bit |
| `"ev3"` | LEGO EV3 |
| `"boost"` | LEGO Boost |
| `"wedo"` | LEGO WeDo 2.0 |
| `"gdxfor"` | Go Direct Force & Acceleration |

> **Hinweis:** Die Pen-Erweiterung wird auch automatisch aktiviert wenn du `penDown()` o.ä. verwendest, ohne expliziten Import.

---

### Sprites und Bühne

```java
public Sprite MeinSprite {
    // Inhalt
}

public Stage MeineBuehne {
    // Inhalt
}
```

Jede Datei kann mehrere Sprites und eine Stage enthalten.

---

### Assets hinzufügen

#### Kostüme

```java
// Scratch-Bibliothek (Name aus dem Scratch-Kostüm-Dialog):
addCostume("Cat-a");
addCostume("Balloon1-a");

// Lokale Datei (relativ zur .java-Datei):
addCostume("Normal", "bilder/katze.png");
addCostume("Pose2",  "katze_pose2.svg");

// Ohne Bild → blauer Platzhalter-Kreis:
addCostume("Leer");
```

Unterstützte Bildformate: PNG, JPG, JPEG, BMP, GIF, WEBP, SVG

#### Hintergründe (nur in Stage)

```java
// Scratch-Bibliothek:
addBackdrop("Blue Sky");
addBackdrop("Forest");

// Lokale Datei:
addBackdrop("Nacht", "hintergruende/nacht.png");

// Weißer Platzhalter:
addBackdrop("Leer");
```

#### Sounds

```java
// Scratch-Bibliothek:
addSound("Meow");
addSound("Pop");

// Lokale Datei:
addSound("Explosion", "sounds/boom.wav");

// Stille (Platzhalter):
addSound("KeinSound");
```

Unterstützte Audioformate: WAV, MP3, OGG, FLAC

---

### Events (Hat-Blöcke)

```java
onFlagClicked {
    // Wird beim Klick auf die grüne Flagge ausgeführt
}

onKeyPressed("space") {
    // Wird bei Tastendruck ausgeführt
    // Mögliche Tasten: "space", "left arrow", "right arrow",
    //   "up arrow", "down arrow", "a"-"z", "0"-"9"
}

onSpriteClicked {
    // Wird beim Klick auf diesen Sprite ausgeführt
}

onBackdropChanged("Nacht") {
    // Wird ausgeführt wenn der Hintergrund wechselt
}

onBroadcastReceived("spielStart") {
    // Wird ausgeführt wenn die Nachricht empfangen wird
}
```

---

### Steuerung

#### Schleifen

```java
repeat(10) {
    move(5);
}

forever {
    move(3);
    bounceOnEdge();
}

repeatUntil(touching("_edge_")) {
    move(5);
}
```

#### If / Elseif / Else

```java
if (punkte > 100) {
    say("Gewonnen!");
} elseif (punkte > 50) {
    say("Gut!");
} elseif (punkte > 0) {
    say("Weiter so!");
} else {
    say("Noch keine Punkte.");
}

// Alternativschreibweise mit Leerzeichen:
if (leben > 1) {
    say("Noch am Leben");
} else if (leben == 1) {
    say("Letztes Leben!");
} else {
    say("Game Over!");
}
```

#### Warten

```java
wait(2);                  // 2 Sekunden warten
waitUntil(touching("Ball")); // Warten bis Bedingung erfüllt
```

#### Stop

```java
stop("all");                        // Alles stoppen
stop("this script");                // Nur dieses Skript
stop("other scripts in sprite");    // Andere Skripte dieses Sprites
```

#### Klone

```java
createClone("_myself_");   // Klon von sich selbst
createClone("Ball");       // Klon eines anderen Sprites

// Im Klon-Skript:
onFlagClicked {
    deleteClone();         // Diesen Klon löschen
}
```

---

### Variablen

```java
var punkte = 0;        // Deklarieren und initialisieren
var name = "Spieler";  // Strings auch möglich
var aktiv = true;      // Booleans auch möglich

punkte = 10;           // Zuweisen
punkte += 5;           // Addieren
punkte -= 2;           // Subtrahieren
punkte *= 2;           // Multiplizieren
punkte /= 4;           // Dividieren
punkte++;              // Um 1 erhöhen
punkte--;              // Um 1 verringern

showVar("punkte");     // Variable anzeigen
hideVar("punkte");     // Variable verstecken
```

---

### Listen

```java
meineListe.add("Eintrag");            // Hinzufügen
meineListe.delete(1);                 // Index löschen
meineListe.insert(2, "Neu");          // Einfügen an Position
meineListe.replace(1, "Ersatz");      // Ersetzen
meineListe.show();                    // Liste anzeigen
meineListe.hide();                    // Liste verstecken

// Als Ausdruck:
var laenge = meineListe.length;
var erster = meineListe[1];
var hatEintrag = meineListe.contains("Suche");

showList("meineListe");
hideList("meineListe");
```

---

### Bewegung

```java
move(10);                      // X Schritte gehen
turnLeft(45);                  // Grad nach links drehen
turnRight(90);                 // Grad nach rechts drehen
goTo(0, 0);                    // Zu Koordinaten gehen
goToSprite("_mouse_");         // Zu Maus / Sprite gehen
glide(2, 100, 50);             // In 2 Sek zu (100,50) gleiten
glideToSprite(1.5, "Ziel");    // Zu Sprite gleiten
pointDir(90);                  // In Richtung zeigen (90=rechts)
pointTowards("_mouse_");       // Zur Maus / Sprite zeigen
setX(100);                     // X-Position setzen
setY(-50);                     // Y-Position setzen
changeX(10);                   // X um Wert ändern
changeY(-5);                   // Y um Wert ändern
bounceOnEdge();                // Am Rand abprallen
setRotationStyle("all around");    // Drehstil: "all around",
                                   //   "left-right", "don't rotate"
```

---

### Aussehen

```java
say("Hallo!");                  // Sprechblase (dauerhaft)
sayFor("Hallo!", 2);            // Sprechblase für 2 Sekunden
think("Hmm...");                // Denkblase (dauerhaft)
thinkFor("Hmm...", 1.5);        // Denkblase für 1,5 Sekunden

switchCostume("Cat-b");         // Kostüm wechseln
nextCostume();                  // Nächstes Kostüm
switchBackdrop("Nacht");        // Hintergrund wechseln
nextBackdrop();                 // Nächster Hintergrund

// Animationshelfer – wechselt Kostüme mit Pause dazwischen:
animate("Cat-a", "Cat-b", "Cat-c", 0.1);
//  ↑ Kostümname 1   ↑ 2       ↑ 3    ↑ Sekunden pro Frame

setSize(100);                   // Größe in % setzen
changeSize(10);                 // Größe um % ändern
show();                         // Sprite zeigen
hide();                         // Sprite verstecken
goToFront();                    // Vorderste Ebene
goToBack();                     // Hinterste Ebene
goForwardLayers(2);             // 2 Ebenen vor
goBackwardLayers(1);            // 1 Ebene zurück

// Grafikeffekte:
setEffect("color", 50);         // Effekt setzen
changeEffect("whirl", 20);      // Effekt ändern
clearEffects();                 // Alle Effekte zurücksetzen

// Gültige Effekte: "color", "fisheye", "whirl",
//   "pixelate", "mosaic", "brightness", "ghost"
```

---

### Sound

```java
playSound("Meow");              // Sound starten (nicht warten)
playSoundUntilDone("Meow");     // Warten bis Sound fertig
stopAllSounds();                // Alle Sounds stoppen
setVolume(80);                  // Lautstärke setzen (0–100)
changeVolume(-10);              // Lautstärke ändern
```

---

### Stift (Pen-Erweiterung)

```java
import "pen";

penDown();                      // Stift senken
penUp();                        // Stift heben
setPenColor(0xFF0000);          // Farbe setzen (Hex)
changePenColor(10);             // Farbe ändern
setPenSize(3);                  // Stiftgröße setzen
changePenSize(1);               // Stiftgröße ändern
stampPen();                     // Stempel
erasePen();                     // Alles löschen
```

---

### Sensing (Abfragen)

```java
askAndWait("Wie heißt du?");    // Eingabe abfragen
setDragMode("draggable");       // Ziehbar: "draggable" oder "not draggable"
resetTimer();                   // Timer zurücksetzen
```

---

### Broadcast (Nachrichten)

```java
broadcast("spielStart");           // Nachricht senden
broadcastAndWait("spielStart");    // Senden und warten

onBroadcastReceived("spielStart") {
    // Auf Nachricht reagieren
}
```

---

### Eigene Blöcke (Custom Blocks)

```java
define zeichneQuadrat(groesse) {
    repeat(4) {
        move(groesse);
        turnRight(90);
    }
}

// Aufruf:
onFlagClicked {
    zeichneQuadrat(100);
    zeichneQuadrat(50);
}
```

---

### Ausdrücke & Operatoren

#### Arithmetik

```java
x + y       // Addition
x - y       // Subtraktion
x * y       // Multiplikation
x / y       // Division
x % y       // Modulo (Rest)
```

#### Vergleiche

```java
x == y      // Gleich
x != y      // Ungleich
x < y       // Kleiner als
x > y       // Größer als
x <= y      // Kleiner oder gleich
x >= y      // Größer oder gleich
```

#### Logik

```java
a && b      // Und
a || b      // Oder
!a          // Nicht (Java-style, ohne Klammern)
!(a)        // Nicht (mit Klammern, auch möglich)

// Beispiele:
if (!s.contains("x") && s.length() > 3) { }
if (!(antwort == "ja")) { }
if (!answer/4.contains(".")) { }   // Kein Rest bei Division
```

#### Math-Funktionen

```java
// Als Methoden auf dem Math-Namespace (Java-style):
Math.abs(-5)         // Betrag
Math.round(3.7)      // Runden
Math.floor(3.9)      // Abrunden
Math.ceil(3.1)       // Aufrunden
Math.sqrt(16)        // Wurzel
Math.sin(90)         // Sinus
Math.cos(0)          // Kosinus
Math.tan(45)         // Tangens
Math.asin(1)         // Arcussinus
Math.acos(0)         // Arcuskosinus
Math.atan(1)         // Arcustangens
Math.ln(2.7)         // Natürlicher Logarithmus
Math.log(100)        // Logarithmus (Basis 10)
Math.random(1, 10)   // Zufallszahl zwischen 1 und 10

// Alternativ als Funktionen (beide Stile funktionieren):
abs(-5)
round(3.7)
random(1, 10)
```

#### String-Methoden (Dot-Syntax)

```java
var s = "Hallo Welt";

s.length()              // Länge → 10
s.contains("Welt")      // Enthält → true
s.letter(1)             // Buchstabe an Position 1 → "H"
s.join(" !!!")          // Verketten → "Hallo Welt !!!"

// Auf beliebigen Ausdrücken:
answer.length()
(vorname.join(" ").join(nachname)).length()
```

#### Sensing-Ausdrücke

```java
answer                  // Letzte Eingabe (nach askAndWait)
mouseX                  // Maus X-Position
mouseY                  // Maus Y-Position
mouseDown               // Maustaste gedrückt (true/false)
timer                   // Timer-Wert
loudness                // Lautstärke des Mikrofons
username                // Benutzername

keyPressed("space")           // Taste gedrückt
touching("_edge_")            // Rand berührt
touching("BallSprite")        // Sprite berührt
touchingColor(0xFF0000)       // Farbe berührt
distanceTo("Ziel")            // Entfernung zu Sprite

// Aktuelle Zeit:
currentYear
currentMonth
currentDate
currentDayOfWeek
currentHour
currentMinute
currentSecond

// Sprite-eigene Werte:
xPosition
yPosition
direction
```

---

### Kommentare

```java
// Einzeiliger Kommentar

/*
   Mehrzeiliger
   Kommentar
*/
```

---

## Vollständiges Beispiel

```java
import "pen";

public Stage Buehne {
    addBackdrop("Blue Sky");
}

public Sprite Spieler {
    addCostume("Cat-a");
    addCostume("Cat-b");
    addSound("Meow");

    var punkte = 0;
    var geschwindigkeit = 5;

    onFlagClicked {
        punkte = 0;
        goTo(0, -130);
        setSize(80);
        setRotationStyle("left-right");
        show();

        forever {
            if (keyPressed("left arrow")) {
                changeX(-geschwindigkeit);
                pointDir(-90);
                animate("Cat-a", "Cat-b", 0.1);
            }
            if (keyPressed("right arrow")) {
                changeX(geschwindigkeit);
                pointDir(90);
                animate("Cat-a", "Cat-b", 0.1);
            }

            if (touching("Muenze")) {
                punkte += 1;
                playSound("Meow");

                if (punkte >= 10) {
                    say("Gewonnen!");
                    stop("all");
                } elseif (punkte >= 5) {
                    say("Halbzeit!");
                } else {
                    say(punkte);
                }
            }
        }
    }
}

public Sprite Muenze {
    addCostume("Ball-a");

    define neuePlatzierung() {
        goTo(Math.random(-200, 200), Math.random(-100, 100));
    }

    onFlagClicked {
        forever {
            neuePlatzierung();
            waitUntil(touching("Spieler"));
            hide();
            wait(1);
            show();
        }
    }
}
```

---

## Scratch-Koordinatensystem

```
          Y = 180
             ↑
             |
X = -240 ───┼─── X = 240
             |
          Y = -180
```

- Mitte der Bühne: `(0, 0)`
- Breite: 480 Einheiten (−240 bis 240)
- Höhe: 360 Einheiten (−180 bis 180)

---

## Fehlerbehandlung

Der Transpiler gibt verständliche Fehlermeldungen **mit Zeilennummer** aus:

```
  ✗  Syntaxfehler: Zeile 7: Erwartet 'RPAREN', gefunden 'SEMI' (';')
```

```
  ✗  Sprite 'Katze': switchCostume("GibtNicht") – nicht definiert.
     Vorhanden: ['Cat-a', 'Cat-b']
```

```
  ⚠  Sprite 'Katze': setVolume(200) – über Maximum (100).
```

**Fehler** (`✗`) verhindern die Kompilierung. **Warnungen** (`⚠`) werden angezeigt, die Datei wird trotzdem erzeugt.

---

## Watch-Modus Workflow

Der Watch-Modus ist ideal für die Entwicklung:

```bash
python scratch_transpiler.py meinSpiel.java --watch --turbowarp-replace
```

1. TurboWarp öffnet sich mit deinem Projekt
2. Du änderst und speicherst deine `.java`-Datei
3. Der Transpiler erkennt die Änderung sofort
4. Kompiliert neu
5. Startet TurboWarp mit dem aktualisierten Projekt
6. Weiter bei Schritt 2

Mit `Ctrl+C` beendest du den Watch-Modus.

---

## Unterschiede zu echtem Java

| Feature | Java | Dieser Transpiler |
|---|---|---|
| Klassen | `class Name { }` | `public Sprite Name { }` |
| Methoden | `void method() { }` | `define method() { }` |
| for-Schleife | `for(int i=0;...)` | — (nicht vorhanden, nutze `repeat`) |
| Typen | `int x = 0;` | `var x = 0;` (kein Typ) |
| `System.out` | `System.out.println` | `say(...)` |
| Import | `import java.util.*` | `import "pen";` (Erweiterungen) |
| Dot-Syntax | `str.contains("x")` | ✓ funktioniert gleich |
| `Math.*` | `Math.abs(-1)` | ✓ funktioniert gleich |
| `!` Operator | `!bool` | ✓ und `!expr.method()` auch |
