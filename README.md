# Scratch Transpiler v5.0

Schreibe Scratch-Projekte in einer Java-ähnlichen Syntax und kompiliere sie direkt zu einer `.sb3`-Datei für [Scratch](https://scratch.mit.edu) oder [TurboWarp](https://turbowarp.org).

Der Transpiler unterstützt die wichtigsten Scratch-Bausteine, Assets, Erweiterungen, Variablen, Listen, Events und einen Watch-Modus zum direkten Nachkompilieren bei Änderungen.

---

## Funktionen

- Java-ähnliche Syntax für Scratch-Skripte
- `.sb3`-Export direkt aus einer `.java`-Datei
- Unterstützung für Sprites, Stage, Assets und Sounds
- Import von Scratch-Erweiterungen wie `pen`, `music`, `video`, `text2speech`, `translate`, `microbit`, `ev3`, `boost`, `wedo`, `gdxfor`
- Variablen, Listen, Schleifen und Bedingungen
- Eigene Blöcke (`define` / `void`)
- Watch-Modus für Live-Neukompilierung
- Automatischer Start von Scratch oder TurboWarp nach der Kompilierung
- Verständliche Fehlermeldungen mit Zeilennummern

---

## Voraussetzungen

- Python 3.10+
- Optional: `Pillow` für Rasterbilder wie PNG/JPG/BMP/WebP
- sudo apt install xdotool
  (Linux (nur nötig, wenn --turbowarp-replace / --scratch-replace genutzt wird))

Installation:

```bash
python -m pip install Pillow
```

---

## Verwendung

```bash
python Transpiler.py <eingabe.java> [Optionen]
```

### Optionen

```bash
--out <datei.sb3>         Ausgabedatei (Standard: output.sb3)
--watch                   Watch-Modus: bei jeder Änderung erneut kompilieren

TurboWarp Desktop:
--turbowarp-new           Startet TurboWarp nach der Kompilierung
--turbowarp-replace       Beendet laufende TurboWarp-Instanz und startet neu

Scratch Desktop:
--scratch-new             Startet Scratch Desktop nach der Kompilierung
--scratch-replace         Beendet laufende Scratch-Instanz und startet neu

--help                    Diese Hilfe anzeigen
```

Hinweis: `--turbowarp-*` und `--scratch-*` schließen sich gegenseitig aus.

---

## Beispiele

```bash
# Einmalige Kompilierung
python Transpiler.py meinSpiel.java

# Mit eigener Ausgabedatei
python Transpiler.py meinSpiel.java --out meinSpiel.sb3

# Watch-Modus mit TurboWarp-Refresh
python Transpiler.py meinSpiel.java --watch --turbowarp-replace

# Watch-Modus mit Scratch-Refresh
python Transpiler.py meinSpiel.java --watch --scratch-replace

# Neue TurboWarp-Instanz öffnen
python Transpiler.py meinSpiel.java --turbowarp-new
```

---

## Projektstruktur

```text
mein_projekt/
├── Transpiler.py
├── meinSpiel.java        ← dein Java-ähnlicher Code
├── katze.png             ← lokale Bilder
├── explosion.wav         ← lokale Sounds
├── meinSpiel.sb3         ← erzeugtes Scratch-Projekt
└── ...
```

---

## Einfache Syntax

### Stage und Sprites

```java
public Stage MeineBuehne {
    addBackdrop("Blue Sky");
}

public Sprite Spieler {
    addCostume("Cat-a");

    onFlagClicked {
        move(10);
        say("Hallo!");
    }
}
```

### Erweiterungen importieren

```java
import "pen";
import "music";
import "text2speech";
```

Verfügbare Erweiterungen:

- `"pen"`
- `"music"`
- `"video"` / `"video sensing"`
- `"text2speech"` / `"tts"` / `"text to speech"`
- `"translate"`
- `"makey"` / `"makey makey"`
- `"microbit"`
- `"ev3"`
- `"boost"`
- `"wedo"`
- `"gdxfor"`

### Assets hinzufügen

```java
addCostume("Cat-a");
addCostume("Normal", "bilder/katze.png");

addBackdrop("Blue Sky");
addBackdrop("Nacht", "hintergruende/nacht.png");

addSound("Meow");
addSound("Explosion", "sounds/boom.wav");
```

Unterstützte Formate:

- Bilder: PNG, JPG, JPEG, BMP, GIF, WEBP, SVG
- Audio: WAV, MP3, OGG, FLAC

### Events

```java
onFlagClicked {
    // Wird beim Klick auf die grüne Flagge ausgeführt
}

onKeyPressed("space") {
    // Tastendruck
}

onSpriteClicked {
    // Klick auf Sprite
}

onBackdropChanged("Nacht") {
    // Hintergrundwechsel
}

onBroadcastReceived("spielStart") {
    // Nachricht empfangen
}
```

### Steuerung

```java
repeat(10) {
    move(5);
}

forever {
    move(3);
}

if (punkte > 100) {
    say("Gewonnen!");
} elseif (punkte > 50) {
    say("Gut!");
} else {
    say("Weiter so!");
}

wait(2);
waitUntil(touching("Ball"));
```

### Variablen und Listen

```java
var punkte = 0;
var name = "Spieler";
var aktiv = true;

punkte += 5;
punkte++;

meineListe.add("Eintrag");
meineListe.insert(2, "Neu");
var laenge = meineListe.length;
```

### Bewegung, Aussehen, Sound

```java
move(10);
turnLeft(45);
goTo(0, 0);
setX(100);
changeY(-5);

say("Hallo!");
switchCostume("Cat-b");
setSize(100);
show();
hide();

playSound("Meow");
playSoundUntilDone("Meow");
setVolume(80);
```

### Eigene Blöcke

```java
define zeichneQuadrat(groesse) {
    repeat(4) {
        move(groesse);
        turnRight(90);
    }
}

onFlagClicked {
    zeichneQuadrat(100);
}
```

---

## Vollständige Scratch-Befehlsübersicht

Die Sprache in J2sb3 ist bewusst Java-ähnlich, aber die Semantik entspricht den Scratch-Bausteinen. Die folgende Tabelle listet die wichtigsten Scratch-Befehle mit dem passenden J2sb3-Äquivalent.

### 1) Events und Trigger

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Wenn grüne Flagge angeklickt | `onFlagClicked { ... }` |
| Wenn Taste `x` gedrückt | `onKeyPressed("x") { ... }` |
| Wenn ich angeklickt werde | `onSpriteClicked { ... }` |
| Wenn Bühne zu `X` wechselt | `onBackdropChanged("X") { ... }` |
| Wenn Nachricht `X` empfangen | `onBroadcastReceived("X") { ... }` |
| Sende Nachricht `X` | `broadcast("X");` |
| Sende Nachricht `X` und warte | `broadcastAndWait("X");` |

### 2) Steuerung

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Wiederhole `N` mal | `repeat(N) { ... }` |
| Für immer | `forever { ... }` |
| Wenn `Bedingung` dann | `if (bedingung) { ... }` |
| Wenn `Bedingung` dann, sonst | `if (bed) { ... } else { ... }` |
| Wenn `Bedingung` dann, sonst wenn ... | `if (a) { ... } elseif (b) { ... } else { ... }` |
| Warten `Sekunden` | `wait(sekunden);` |
| Warte bis `Bedingung` | `waitUntil(bedingung);` |
| Wiederhole bis `Bedingung` | `repeatUntil(bedingung) { ... }` |
| Stoppe alles | `stop("all");` |
| Stoppe dieses Skript | `stop("this script");` |
| Stoppe andere Skripte in Sprite | `stop("other scripts in sprite");` |
| Erzeuge Klon von `X` | `createClone("X");` |
| Lösche diesen Klon | `deleteClone();` |

### 3) Bewegung (Motion)

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Bewege `N` Schritte | `move(N);` |
| Drehe nach links `N` Grad | `turnLeft(N);` |
| Drehe nach rechts `N` Grad | `turnRight(N);` |
| Gehe zu x: `X`, y: `Y` | `goTo(X, Y);` |
| Gehe zu Sprite `X` | `goToSprite("X");` |
| Gleite `Sekunden` zu x: `X`, y: `Y` | `glide(Sekunden, X, Y);` |
| Gleite `Sekunden` zu Sprite `X` | `glideToSprite(Sekunden, "X");` |
| Setze Richtung auf `N` Grad | `pointDir(N);` |
| Schau auf `X` | `pointTowards("X");` |
| Setze x auf `X` | `setX(X);` |
| Setze y auf `Y` | `setY(Y);` |
| Ändere x um `N` | `changeX(N);` |
| Ändere y um `N` | `changeY(N);` |
| Pralle am Rand ab | `bounceOnEdge();` |
| Setze Rotationsstil | `setRotationStyle("all around");` |
| Setze x-Position | `xPosition` |
| Setze y-Position | `yPosition` |
| Setze Richtung | `direction` |

### 4) Aussehen (Looks)

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Sag `Text` | `say("Text");` |
| Sag `Text` für `Sekunden` | `sayFor("Text", Sekunden);` |
| Denk `Text` | `think("Text");` |
| Denk `Text` für `Sekunden` | `thinkFor("Text", Sekunden);` |
| Wechsle zu Kostüm `X` | `switchCostume("X");` |
| Nächstes Kostüm | `nextCostume();` |
| Wechsle zu Hintergrund `X` | `switchBackdrop("X");` |
| Nächster Hintergrund | `nextBackdrop();` |
| Setze Größe auf `N` | `setSize(N);` |
| Ändere Größe um `N` | `changeSize(N);` |
| Zeige dich an | `show();` |
| Verstecke dich | `hide();` |
| Bringe nach vorne | `goToFront();` |
| Bringe nach hinten | `goToBack();` |
| Bewege `N` Ebenen nach vorne | `goForwardLayers(N);` |
| Bewege `N` Ebenen nach hinten | `goBackwardLayers(N);` |
| Effekt `X` auf `N` setzen | `setEffect("X", N);` |
| Effekt `X` um `N` ändern | `changeEffect("X", N);` |
| Effekt löschen | `clearEffects();` |

### 5) Klang (Sound)

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Spiel Klang `X` | `playSound("X");` |
| Spiel Klang `X` vollständig | `playSoundUntilDone("X");` |
| Stoppe alle Klänge | `stopAllSounds();` |
| Setze Lautstärke auf `N` | `setVolume(N);` |
| Ändere Lautstärke um `N` | `changeVolume(N);` |

### 6) Ereignisse und Sensoren (Sensing)

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Frage `Text` und warte | `askAndWait("Text");` |
| Setze Ziehmodus | `setDragMode("draggable");` |
| Timer zurücksetzen | `resetTimer();` |
| Antwort | `answer` |
| Maus x | `mouseX` |
| Maus y | `mouseY` |
| Maus gedrückt? | `mouseDown` |
| Taste `X` gedrückt? | `keyPressed("X")` |
| Berührt `X`? | `touching("X")` |
| Berührt Farbe `X`? | `touchingColor(X)` |
| Abstand zu `X` | `distanceTo("X")` |
| Timer | `timer` |
| Lautstärke | `loudness` |
| Benutzername | `username` |
| Aktuelles Jahr | `currentYear` |
| Aktueller Monat | `currentMonth` |
| Aktueller Tag | `currentDate` |
| Aktueller Wochentag | `currentDayOfWeek` |
| Aktuelle Stunde | `currentHour` |
| Aktuelle Minute | `currentMinute` |
| Aktuelle Sekunde | `currentSecond` |

### 7) Stift (Pen)

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Stift herunter | `penDown();` |
| Stift hoch | `penUp();` |
| Setze Stiftfarbe auf `N` | `setPenColor(N);` |
| Ändere Stiftfarbe um `N` | `changePenColor(N);` |
| Setze Stiftbreite auf `N` | `setPenSize(N);` |
| Ändere Stiftbreite um `N` | `changePenSize(N);` |
| Stempel setzen | `stampPen();` |
| Lösche alles | `erasePen();` |

### 8) Variablen und Listen

| Scratch-Block | J2sb3-Äquivalent |
|---|---|
| Variable deklarieren | `var x = 0;` |
| Variable setzen | `x = 5;` |
| Variable erhöhen | `x++;` oder `x += 2;` |
| Variable anzeigen | `showVar;` oder `showVar("x");` |
| Variable verstecken | `hideVar;` oder `hideVar("x");` |
| Liste hinzufügen | `liste.add(item);` |
| Liste einfügen | `liste.insert(index, item);` |
| Listenwert löschen | `liste.delete(index);` |
| Listenwert ersetzen | `liste.replace(index, item);` |
| Länge einer Liste | `meineListe.length` |
| Element aus Liste lesen | `meineListe[0]` |
| Ob Listeneintrag enthalten ist | `meineListe.contains(item)` |
| Liste anzeigen | `showList("name");` |
| Liste verstecken | `hideList("name");` |

### 9) Operatoren und Funktionen

| Scratch-Block / Funktion | J2sb3-Äquivalent |
|---|---|
| Addition | `a + b` |
| Subtraktion | `a - b` |
| Multiplikation | `a * b` |
| Division | `a / b` |
| Modulo | `a % b` |
| Gleich | `a == b` |
| Ungleich | `a != b` |
| Kleiner | `a < b` |
| Größer | `a > b` |
| Kleiner gleich | `a <= b` |
| Größer gleich | `a >= b` |
| Und | `a && b` |
| Oder | `a || b` |
| Nicht | `!a` |
| Zufallszahl | `random(1, 10)` |
| Absolutwert | `Math.abs(-5)` |
| Runde | `Math.round(3.7)` |
| Wurzel | `Math.sqrt(16)` |
| Sinus | `Math.sin(x)` |
| Kosinus | `Math.cos(x)` |
| Tangens | `Math.tan(x)` |
| Logarithmus | `Math.log(x)` |
| Natürlicher Logarithmus | `Math.ln(x)` |
| Länge eines Strings | `length(text)` |
| Zeichen an Position `N` | `letter(N, text)` |
| Enthält Teilstring? | `contains(text, "x")` |
| Verknüpfe Zeichenketten | `join("Hallo", " Welt")` |

### 10) Eigene Blöcke (Custom Blocks)

```java
define quadrat(size) {
    repeat(4) {
        move(size);
        turnRight(90);
    }
}

onFlagClicked {
    quadrat(100);
}
```

Optionale Typannotationen:

```java
define moveTo(number x, number y) {
    goTo(x, y);
}

void sayHello(string name) {
    say("Hallo " + name);
}
```

Typen im Transpiler:

- `number` / `int` / `float` → numerisch
- `string` / `str` → Text
- `boolean` / `bool` → Boolescher Wert

### 11) Unterstützte Scratch-Erweiterungen

```java
import "pen";
import "music";
import "video";
import "text2speech";
import "translate";
import "microbit";
import "ev3";
import "boost";
import "wedo";
import "gdxfor";
```

Dies erlaubt den Import von Scratch-Erweiterungen, die in Scratch-Projekten als Zusatzblöcke verfügbar sind.

---

## Ausdrücke und Operatoren

```java
x + y
x - y
x * y
x / y
x % y

x == y
x != y
x < y
x > y
x <= y
x >= y

a && b
a || b
!a

Math.abs(-5)
Math.round(3.7)
Math.sqrt(16)
Math.random(1, 10)
```

---

## Fehlerbehandlung

Der Transpiler meldet verständliche Fehler mit Zeilennummern:

```text
✗  Syntaxfehler: Zeile 7: Erwartet 'RPAREN', gefunden 'SEMI' (';')
```

```text
✗  Sprite 'Katze': switchCostume("GibtNicht") – nicht definiert.
    Vorhanden: ['Cat-a', 'Cat-b']
```

Warnungen (`⚠`) werden zwar angezeigt, aber die `.sb3`-Datei kann trotzdem erzeugt werden.

---

## Watch-Modus

Der Watch-Modus ist ideal für iterative Entwicklung:

```bash
python Transpiler.py meinSpiel.java --watch --turbowarp-replace
```

1. TurboWarp oder Scratch wird gestartet
2. Du änderst die `.java`-Datei
3. Der Transpiler erkennt die Änderung automatisch
4. Das Projekt wird neu kompiliert
5. Die App wird neu geladen

Mit `Ctrl+C` beendet man den Watch-Modus.

---

## Unterschied zu echtem Java

- Klassen: `class Name {}` → `public Sprite Name {}` / `public Stage Name {}`
- Methoden: `void foo() {}` → `define foo() {}`
- Typdeklaration: `int x = 0;` → `var x = 0;`
- `System.out.println(...)` → `say(...)` oder `print`, je nach Verwendung
- `import java.util.*` → `import "pen";` etc. für Scratch-Erweiterungen

---

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe `LICENSE`.

---

## Hinweis

Die vollständige Syntax- und Funktionsreferenz liegt in dieser README zusammen mit den Beispielen und der CLI-Dokumentation vor. Für die aktuelle Nutzung ist der direkte Aufruf über `python Transpiler.py ...` ausreichend.
