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

### Ausdrücke und Operatoren

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

Die vollständige Syntax- und Funktionsreferenz liegt in dieser README zusammen mit den Beispielen und der CLI-Dokumentation vor. Für die aktuelle Nutzung ist der direkte Aufruf über `python Transpiler.py --help` die beste Referenz, da die Kommandzeilenoptionen und die reale Implementierung immer mit der aktuellen Version übereinstimmen.
