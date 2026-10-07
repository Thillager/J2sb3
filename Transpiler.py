"""
scratch_transpiler.py  v4.0
════════════════════════════
Java-ähnliche Syntax → Scratch 3 / TurboWarp .sb3

Neu in v4:
  • Zeilennummern in allen Fehlermeldungen
  • elseif-Ketten (else if { } else if { } else { })
  • import "Erweiterung";  für Scratch-Erweiterungen
  • animate("kos1","kos2", secs);  – Animations-Helfer
  • Watch-Modus  (--watch)
  • TurboWarp-Flags  (--turbowarp-new / --turbowarp-replace)
  • Verbesserter Validator mit klaren Fehlermeldungen
"""

import re, json, uuid, zipfile, sys, hashlib, io, os, time, subprocess, platform
from pathlib import Path

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ═══════════════════════════════════════════════════════
#  0.  Hilfsfunktionen
# ═══════════════════════════════════════════════════════
def new_id() -> str:
    return uuid.uuid4().hex[:20]

def md5hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


# ═══════════════════════════════════════════════════════
#  A.  ASSET-MANAGER
# ═══════════════════════════════════════════════════════
class AssetManager:
    PLACEHOLDER_COSTUME_SVG = (
        b'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        b'width="64" height="64" viewBox="0 0 64 64">'
        b'<circle cx="32" cy="32" r="28" fill="#4C97FF" stroke="#3373CC" stroke-width="3"/>'
        b'<text x="32" y="37" text-anchor="middle" font-size="14" fill="white" '
        b'font-family="sans-serif">?</text>'
        b'</svg>'
    )
    SILENT_WAV = (
        b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00'
        b'\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00'
        b'\x10\x00data\x00\x00\x00\x00'
    )
    _LIBRARY_URLS = {
        "costumes":  "https://raw.githubusercontent.com/scratchfoundation/scratch-gui/develop/src/lib/libraries/costumes.json",
        "backdrops": "https://raw.githubusercontent.com/scratchfoundation/scratch-gui/develop/src/lib/libraries/backdrops.json",
        "sounds":    "https://raw.githubusercontent.com/scratchfoundation/scratch-gui/develop/src/lib/libraries/sounds.json",
    }
    _ASSET_SERVER = "https://assets.scratch.mit.edu/internalapi/asset/{md5ext}/get/"
    _CACHE_FILE   = Path.home() / ".scratch_transpiler_library.json"
    _library: dict = {}

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self._files: dict[str, bytes] = {}
        if not AssetManager._library:
            AssetManager._library = self._load_library()

    def _load_library(self) -> dict:
        import urllib.request as _req
        if self._CACHE_FILE.exists():
            age = time.time() - self._CACHE_FILE.stat().st_mtime
            if age < 7 * 86400:
                try:
                    lib = json.loads(self._CACHE_FILE.read_text(encoding="utf-8"))
                    print(f"  📚 Scratch-Bibliothek aus Cache ({len(lib.get('costumes',{}))} Kostüme, "
                          f"{len(lib.get('backdrops',{}))} Hintergründe, "
                          f"{len(lib.get('sounds',{}))} Sounds)")
                    return lib
                except Exception:
                    pass
        print("  📚 Lade Scratch-Bibliothek von GitHub...", end=" ", flush=True)
        result = {"costumes": {}, "backdrops": {}, "sounds": {}}
        try:
            for kind, url in self._LIBRARY_URLS.items():
                with _req.urlopen(url, timeout=10) as r:
                    data = json.loads(r.read())
                for item in data:
                    name = item.get("name", ""); md5 = item.get("md5ext", "")
                    if not md5 or not name: continue
                    fmt = md5.rsplit(".", 1)[-1]; asset_id = md5.rsplit(".", 1)[0]
                    result[kind][name.lower()] = {
                        "name": name, "md5ext": md5, "assetId": asset_id,
                        "dataFormat": fmt,
                        "rotationCenterX": item.get("rotationCenterX", 0),
                        "rotationCenterY": item.get("rotationCenterY", 0),
                        "bitmapResolution": item.get("bitmapResolution", 1),
                    }
            print(f"{sum(len(v) for v in result.values())} Assets ✓")
            try:
                self._CACHE_FILE.write_text(json.dumps(result, separators=(",",":")), encoding="utf-8")
            except Exception:
                pass
        except Exception as e:
            print(f"fehlgeschlagen ({e})")
        return result

    def _lookup(self, name: str, kind: str) -> dict | None:
        return AssetManager._library.get(kind, {}).get(name.lower())

    def _register(self, data: bytes, ext: str) -> tuple[str, str]:
        asset_id = md5hex(data); filename = f"{asset_id}.{ext}"
        self._files[filename] = data
        return asset_id, filename

    def _png_costume(self, data: bytes, name: str) -> dict:
        asset_id, _ = self._register(data, "png")
        cx = cy = 0
        if HAS_PIL:
            try:
                img = PILImage.open(io.BytesIO(data))
                cx, cy = img.width // 2, img.height // 2
            except Exception:
                pass
        return {"assetId": asset_id, "name": name, "bitmapResolution": 2,
                "md5ext": f"{asset_id}.png", "dataFormat": "png",
                "rotationCenterX": cx, "rotationCenterY": cy}

    def load_image(self, path_str: str | None, name: str) -> dict:
        search = name if path_str is None else (
            path_str if ("/" not in path_str and "." not in path_str) else None)
        if search:
            entry = self._lookup(search, "costumes")
            if entry:
                print(f"      → Scratch-Bibliothek: '{entry['name']}' ({entry['md5ext']})")
                return {"assetId": entry["assetId"], "name": name,
                        "bitmapResolution": entry["bitmapResolution"],
                        "md5ext": entry["md5ext"], "dataFormat": entry["dataFormat"],
                        "rotationCenterX": entry["rotationCenterX"],
                        "rotationCenterY": entry["rotationCenterY"]}
            if path_str is None:
                print(f"      ⚠ '{name}' nicht in Scratch-Bibliothek → Platzhalter")
                return self._fallback_costume(name)
        if path_str is None:
            return self._fallback_costume(name)
        path = (self.base_dir / path_str).resolve()
        if not path.exists():
            print(f"      ⚠ Bild nicht gefunden: {path}")
            print(f"         Lege '{path.name}' neben dein Script.")
            return self._fallback_costume(name)
        suffix = path.suffix.lower()
        if suffix == ".svg":
            data = path.read_bytes(); asset_id, _ = self._register(data, "svg")
            cx = cy = 0
            try:
                import re as _re; txt = data.decode("utf-8", errors="ignore")
                w = _re.search(r'width="([0-9.]+)"', txt)
                h = _re.search(r'height="([0-9.]+)"', txt)
                if w and h: cx = int(float(w.group(1)))//2; cy = int(float(h.group(1)))//2
            except Exception:
                pass
            return {"assetId": asset_id, "name": name, "bitmapResolution": 1,
                    "md5ext": f"{asset_id}.svg", "dataFormat": "svg",
                    "rotationCenterX": cx, "rotationCenterY": cy}
        if HAS_PIL:
            try:
                img = PILImage.open(path).convert("RGBA")
                buf = io.BytesIO(); img.save(buf, "PNG")
                return self._png_costume(buf.getvalue(), name)
            except Exception as e:
                print(f"      ⚠ Bildfehler ({path.name}): {e} → Platzhalter")
                return self._fallback_costume(name)
        if suffix == ".png":
            return self._png_costume(path.read_bytes(), name)
        print(f"      ⚠ Pillow nicht installiert → Platzhalter")
        return self._fallback_costume(name)

    def _fallback_costume(self, name: str) -> dict:
        asset_id, _ = self._register(self.PLACEHOLDER_COSTUME_SVG, "svg")
        return {"assetId": asset_id, "name": name, "bitmapResolution": 1,
                "md5ext": f"{asset_id}.svg", "dataFormat": "svg",
                "rotationCenterX": 32, "rotationCenterY": 32}

    def load_backdrop(self, path_str: str | None, name: str) -> dict:
        search = name if path_str is None else (
            path_str if ("/" not in path_str and "." not in path_str) else None)
        if search:
            entry = self._lookup(search, "backdrops")
            if entry:
                print(f"      → Scratch-Bibliothek: '{entry['name']}' ({entry['md5ext']})")
                return {"assetId": entry["assetId"], "name": name,
                        "bitmapResolution": entry["bitmapResolution"],
                        "md5ext": entry["md5ext"], "dataFormat": entry["dataFormat"],
                        "rotationCenterX": entry["rotationCenterX"],
                        "rotationCenterY": entry["rotationCenterY"]}
            if path_str is None:
                WHITE = b'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="360"><rect width="480" height="360" fill="white"/></svg>'
                asset_id, _ = self._register(WHITE, "svg")
                return {"assetId": asset_id, "name": name, "bitmapResolution": 1,
                        "md5ext": f"{asset_id}.svg", "dataFormat": "svg",
                        "rotationCenterX": 240, "rotationCenterY": 180}
        c = self.load_image(path_str, name)
        if HAS_PIL and path_str and Path(path_str).suffix.lower() != ".svg":
            try:
                img = PILImage.open((self.base_dir / path_str).resolve())
                c["rotationCenterX"] = img.width // 2
                c["rotationCenterY"] = img.height // 2
            except Exception:
                c["rotationCenterX"] = 240; c["rotationCenterY"] = 180
        return c

    def load_sound(self, path_str: str | None, name: str) -> dict:
        search = name if path_str is None else (
            path_str if ("/" not in path_str and "." not in path_str) else None)
        if search:
            entry = self._lookup(search, "sounds")
            if entry:
                print(f"      → Scratch-Bibliothek: '{entry['name']}' ({entry['md5ext']})")
                return {"assetId": entry["assetId"], "name": name,
                        "dataFormat": entry["dataFormat"], "format": "",
                        "rate": 44100, "sampleCount": 0, "md5ext": entry["md5ext"]}
            if path_str is None:
                return self._fallback_sound(name)
        if path_str is None:
            return self._fallback_sound(name)
        path = (self.base_dir / path_str).resolve()
        if not path.exists():
            print(f"      ⚠ Sound nicht gefunden: {path} → Stille")
            return self._fallback_sound(name)
        suffix = path.suffix.lower().lstrip(".")
        fmt = {"wav":"wav","mp3":"mp3","ogg":"wav","flac":"wav"}.get(suffix, "wav")
        try:
            data = path.read_bytes(); asset_id, _ = self._register(data, fmt)
            return {"assetId": asset_id, "name": name, "dataFormat": fmt,
                    "format": "", "rate": 44100, "sampleCount": 0,
                    "md5ext": f"{asset_id}.{fmt}"}
        except Exception as e:
            print(f"      ⚠ Soundfehler: {e} → Stille")
            return self._fallback_sound(name)

    def _fallback_sound(self, name: str) -> dict:
        asset_id, _ = self._register(self.SILENT_WAV, "wav")
        return {"assetId": asset_id, "name": name, "dataFormat": "wav",
                "format": "", "rate": 44100, "sampleCount": 0,
                "md5ext": f"{asset_id}.wav"}

    def all_files(self) -> dict:
        return dict(self._files)


# ═══════════════════════════════════════════════════════
#  1.  LEXER
# ═══════════════════════════════════════════════════════
KEYWORDS = {
    "public","Sprite","Stage","import",
    "onFlagClicked","onKeyPressed","onSpriteClicked",
    "onBackdropChanged","onBroadcastReceived",
    "repeat","forever","if","else","elseif","repeatUntil",
    "wait","waitUntil","stop","createClone","deleteClone",
    "var","showVar","hideVar","showList","hideList",
    "move","turnLeft","turnRight","goTo","goToSprite",
    "glide","glideToSprite","pointDir","pointTowards",
    "setX","setY","changeX","changeY","bounceOnEdge","setRotationStyle",
    "say","sayFor","think","thinkFor","switchCostume","nextCostume",
    "switchBackdrop","nextBackdrop","setSize","changeSize","animate",
    "show","hide","goToFront","goToBack","goForwardLayers","goBackwardLayers",
    "setEffect","changeEffect","clearEffects",
    "playSound","playSoundUntilDone","stopAllSounds","setVolume","changeVolume",
    "askAndWait","setDragMode","resetTimer",
    "penDown","penUp","setPenColor","changePenColor",
    "setPenSize","changePenSize","stampPen","erasePen",
    "broadcast","broadcastAndWait",
    "define",
    "addCostume","addBackdrop","addSound",
    "random","abs","floor","ceil","sqrt",
    "sin","cos","tan","asin","acos","atan","ln","log","round",
    "length","letter","contains","join",
    "answer","mouseX","mouseY","mouseDown","keyPressed",
    "touching","touchingColor","distanceTo","timer",
    "currentYear","currentMonth","currentDate","currentDayOfWeek",
    "currentHour","currentMinute","currentSecond",
    "loudness","username","true","false",
    "xPosition","yPosition","direction","Math",
}

TOKEN_PATTERNS = [
    ("COMMENT",  r'//[^\n]*'),
    ("COMMENT2", r'/\*.*?\*/'),
    ("NEWLINE",  r'\n'),
    ("NUMBER",   r'\d+(\.\d+)?'),
    ("STRING",   r'"[^"]*"'),
    ("OP2",      r'==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/='),
    ("OP",       r'[+\-*/%<>!]'),
    ("ASSIGN",   r'='),
    ("DOT",      r'\.'),
    ("LPAREN",   r'\('),
    ("RPAREN",   r'\)'),
    ("LBRACE",   r'\{'),
    ("RBRACE",   r'\}'),
    ("LBRACKET", r'\['),
    ("RBRACKET", r'\]'),
    ("SEMI",     r';'),
    ("COMMA",    r','),
    ("IDENT",    r'[A-Za-z_][A-Za-z0-9_]*'),
    ("SKIP",     r'[ \t\r]+'),
    ("MISMATCH", r'.'),
]
MASTER_RE = re.compile(
    '|'.join(f'(?P<{name}>{pat})' for name, pat in TOKEN_PATTERNS),
    re.DOTALL
)

def tokenize(source: str) -> list:
    """
    Gibt Liste von (kind, value, line) zurück.
    line = Zeilennummer (1-basiert).
    """
    tokens = []
    line = 1
    for m in MASTER_RE.finditer(source):
        kind = m.lastgroup; value = m.group()
        if kind == "NEWLINE":
            line += 1; continue
        if kind in ("SKIP", "COMMENT", "COMMENT2"):
            # Zeilenumbrüche in mehrzeiligen Kommentaren zählen
            line += value.count("\n"); continue
        if kind == "MISMATCH":
            raise SyntaxError(f"Zeile {line}: Unbekanntes Zeichen: {value!r}")
        if kind == "IDENT" and value in KEYWORDS:
            kind = "KEYWORD"
        tokens.append((kind, value, line))
    return tokens


# ═══════════════════════════════════════════════════════
#  2.  PARSER
# ═══════════════════════════════════════════════════════

# Alle bekannten Scratch-Erweiterungen mit ihren Extension-IDs
KNOWN_EXTENSIONS = {
    # Name (lowercase) → extension_id für project.json
    "pen":          "pen",
    "music":        "music",
    "video":        "videoSensing",
    "text2speech":  "text2speech",
    "translate":    "translate",
    "makey":        "makeymakey",
    "microbit":     "microbit",
    "ev3":          "ev3",
    "boost":        "boost",
    "wedo":         "wedo2",
    "gdxfor":       "gdxfor",
    "tts":          "text2speech",
    "text to speech": "text2speech",
    "video sensing": "videoSensing",
    "makey makey":  "makeymakey",
}

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens   # list of (kind, value, line)
        self.pos    = 0
        self.vars:          set  = set()
        self.lists:         set  = set()
        self.custom_blocks: dict = {}
        self.extensions:    list = []   # gesammelte import-Erweiterungen

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else ("EOF", "", 0)

    def current_line(self) -> int:
        return self.peek()[2]

    def consume(self, kind=None, value=None):
        k, v, ln = self.tokens[self.pos]
        if kind  and k != kind:
            raise SyntaxError(f"Zeile {ln}: Erwartet {kind!r}, gefunden {k!r} ({v!r})")
        if value and v != value:
            raise SyntaxError(f"Zeile {ln}: Erwartet {value!r}, gefunden {v!r}")
        self.pos += 1
        return v

    def expect_semi(self):
        if self.peek()[1] == ";": self.consume()

    # ── Top-Level ─────────────────────────────────────
    def parse_program(self):
        targets = []
        while self.peek()[0] != "EOF":
            # import-Anweisung auf Top-Level
            if self.peek()[1] == "import":
                self._parse_import()
            else:
                targets.append(self.parse_target())
        return {"type": "Program", "targets": targets,
                "extensions": list(dict.fromkeys(self.extensions))}

    def _parse_import(self):
        _, _, ln = self.peek()
        self.consume(value="import")
        raw = self.consume("STRING").strip('"')
        self.expect_semi()
        ext_id = KNOWN_EXTENSIONS.get(raw.lower())
        if ext_id:
            if ext_id not in self.extensions:
                self.extensions.append(ext_id)
            print(f"  📦 Import: {raw} → Extension '{ext_id}'")
        else:
            raise SyntaxError(
                f"Zeile {ln}: Unbekannte Erweiterung: \"{raw}\"\n"
                f"     Bekannte Erweiterungen: {', '.join(sorted(KNOWN_EXTENSIONS.keys()))}"
            )

    def parse_target(self):
        ln = self.current_line()
        self.consume(value="public")
        kind = self.consume("KEYWORD")
        if kind not in ("Sprite", "Stage"):
            raise SyntaxError(f"Zeile {ln}: Erwartet 'Sprite' oder 'Stage', gefunden '{kind}'")
        name = self.consume("IDENT")
        self.consume("LBRACE")

        costumes, backdrops, sounds = [], [], []
        scripts, custom_defs = [], []

        while self.peek()[1] != "}":
            v = self.peek()[1]
            if v == "import":
                self._parse_import()
            elif v == "addCostume":
                self.consume(); self.consume("LPAREN")
                cname = self.consume("STRING").strip('"'); path = None
                if self.peek()[1] == ",": self.consume("COMMA"); path = self.consume("STRING").strip('"')
                self.consume("RPAREN"); self.expect_semi()
                costumes.append({"name": cname, "path": path})
            elif v == "addBackdrop":
                self.consume(); self.consume("LPAREN")
                bname = self.consume("STRING").strip('"'); path = None
                if self.peek()[1] == ",": self.consume("COMMA"); path = self.consume("STRING").strip('"')
                self.consume("RPAREN"); self.expect_semi()
                backdrops.append({"name": bname, "path": path})
            elif v == "addSound":
                self.consume(); self.consume("LPAREN")
                sname = self.consume("STRING").strip('"'); path = None
                if self.peek()[1] == ",": self.consume("COMMA"); path = self.consume("STRING").strip('"')
                self.consume("RPAREN"); self.expect_semi()
                sounds.append({"name": sname, "path": path})
            elif v == "var":
                decl = self.parse_var_decl()
                scripts.append({"event": {"type": "EventFlagClicked"}, "body": [decl]})
            elif v == "define":
                cd = self.parse_custom_def()
                custom_defs.append(cd)
                self.custom_blocks[cd["name"]] = cd["params"]
            elif v in ("onFlagClicked","onKeyPressed","onSpriteClicked",
                       "onBackdropChanged","onBroadcastReceived"):
                event, body = self.parse_script()
                scripts.append({"event": event, "body": body})
            else:
                body = self.parse_block()
                scripts.append({"event": {"type": "EventFlagClicked"}, "body": body})

        self.consume("RBRACE")
        return {"type": kind, "name": name,
                "costumes": costumes, "backdrops": backdrops, "sounds": sounds,
                "scripts": scripts, "customDefs": custom_defs}

    def parse_script(self):
        v = self.consume("KEYWORD"); ln = self.current_line()
        if v == "onFlagClicked":
            return {"type": "EventFlagClicked"}, self.parse_block()
        if v == "onKeyPressed":
            self.consume("LPAREN"); key = self.consume("STRING").strip('"'); self.consume("RPAREN")
            return {"type": "EventKeyPressed", "key": key}, self.parse_block()
        if v == "onSpriteClicked":
            return {"type": "EventSpriteClicked"}, self.parse_block()
        if v == "onBackdropChanged":
            self.consume("LPAREN"); bd = self.consume("STRING").strip('"'); self.consume("RPAREN")
            return {"type": "EventBackdropChanged", "backdrop": bd}, self.parse_block()
        if v == "onBroadcastReceived":
            self.consume("LPAREN"); msg = self.consume("STRING").strip('"'); self.consume("RPAREN")
            return {"type": "EventBroadcastReceived", "message": msg}, self.parse_block()
        raise SyntaxError(f"Zeile {ln}: Unbekanntes Event: {v!r}")

    def parse_block(self):
        ln = self.current_line()
        self.consume("LBRACE")
        stmts = []
        while self.peek()[1] != "}":
            if self.peek()[0] == "EOF":
                raise SyntaxError(f"Zeile {ln}: Geschweifte Klammer '{{' nie geschlossen")
            stmts.append(self.parse_statement())
        self.consume("RBRACE")
        return stmts

    def parse_custom_def(self):
        self.consume(value="define"); name = self.consume("IDENT")
        self.consume("LPAREN"); params = []
        while self.peek()[1] != ")":
            params.append(self.consume("IDENT"))
            if self.peek()[1] == ",": self.consume("COMMA")
        self.consume("RPAREN")
        self.custom_blocks[name] = params
        return {"type": "CustomDef", "name": name, "params": params, "body": self.parse_block()}

    # ── Statements ────────────────────────────────────
    def parse_statement(self):
        k, v, ln = self.peek()
        if v == "var":          return self.parse_var_decl()
        if k == "IDENT":
            if self.peek(1)[1] == ".":  return self.parse_list_method()
            _, nv, _ = self.peek(1)
            if nv in ("=","+=","-=","*=","/=","++","--"): return self.parse_assignment()
            if v in self.custom_blocks: return self.parse_custom_call()
            raise SyntaxError(f"Zeile {ln}: Unbekannter Bezeichner: {v!r} – "
                              f"fehlt 'var', '=' oder eine Block-Definition?")
        if v == "repeat":         return self.parse_repeat()
        if v == "forever":        return self.parse_forever()
        if v == "if":             return self.parse_if()
        if v == "repeatUntil":    return self.parse_repeat_until()
        if v == "wait":           return self.parse_wait()
        if v == "waitUntil":      return self.parse_wait_until()
        if v == "stop":           return self.parse_stop()
        if v == "createClone":    return self.parse_create_clone()
        if v == "deleteClone":    return self.parse_delete_clone()
        if v == "showVar":        return self.parse_simple_str_cmd("ShowVar")
        if v == "hideVar":        return self.parse_simple_str_cmd("HideVar")
        if v == "showList":       return self.parse_simple_str_cmd("ShowList")
        if v == "hideList":       return self.parse_simple_str_cmd("HideList")
        if v == "move":           return self.parse_motion_1num("Move")
        if v == "turnLeft":       return self.parse_motion_1num("TurnLeft")
        if v == "turnRight":      return self.parse_motion_1num("TurnRight")
        if v == "goTo":           return self.parse_goto_xy()
        if v == "goToSprite":     return self.parse_simple_str_cmd("GoToSprite")
        if v == "glide":          return self.parse_glide()
        if v == "glideToSprite":  return self.parse_glide_to_sprite()
        if v == "pointDir":       return self.parse_motion_1num("PointDir")
        if v == "pointTowards":   return self.parse_simple_str_cmd("PointTowards")
        if v == "setX":           return self.parse_motion_1num("SetX")
        if v == "setY":           return self.parse_motion_1num("SetY")
        if v == "changeX":        return self.parse_motion_1num("ChangeX")
        if v == "changeY":        return self.parse_motion_1num("ChangeY")
        if v == "bounceOnEdge":   return self.parse_no_arg("BounceOnEdge")
        if v == "setRotationStyle": return self.parse_simple_str_cmd("SetRotationStyle")
        if v == "say":            return self.parse_say()
        if v == "sayFor":         return self.parse_say_for()
        if v == "think":          return self.parse_say(think=True)
        if v == "thinkFor":       return self.parse_say_for(think=True)
        if v == "animate":        return self.parse_animate()
        if v == "switchCostume":  return self.parse_simple_str_cmd("SwitchCostume")
        if v == "nextCostume":    return self.parse_no_arg("NextCostume")
        if v == "switchBackdrop": return self.parse_simple_str_cmd("SwitchBackdrop")
        if v == "nextBackdrop":   return self.parse_no_arg("NextBackdrop")
        if v == "setSize":        return self.parse_motion_1num("SetSize")
        if v == "changeSize":     return self.parse_motion_1num("ChangeSize")
        if v == "show":           return self.parse_no_arg("Show")
        if v == "hide":           return self.parse_no_arg("Hide")
        if v == "goToFront":      return self.parse_no_arg("GoToFront")
        if v == "goToBack":       return self.parse_no_arg("GoToBack")
        if v == "goForwardLayers":  return self.parse_motion_1num("GoForwardLayers")
        if v == "goBackwardLayers": return self.parse_motion_1num("GoBackwardLayers")
        if v == "setEffect":      return self.parse_effect_cmd("SetEffect")
        if v == "changeEffect":   return self.parse_effect_cmd("ChangeEffect")
        if v == "clearEffects":   return self.parse_no_arg("ClearEffects")
        if v == "playSound":          return self.parse_simple_str_cmd("PlaySound")
        if v == "playSoundUntilDone": return self.parse_simple_str_cmd("PlaySoundUntilDone")
        if v == "stopAllSounds":      return self.parse_no_arg("StopAllSounds")
        if v == "setVolume":          return self.parse_motion_1num("SetVolume")
        if v == "changeVolume":       return self.parse_motion_1num("ChangeVolume")
        if v == "askAndWait":         return self.parse_simple_str_cmd("AskAndWait")
        if v == "setDragMode":        return self.parse_simple_str_cmd("SetDragMode")
        if v == "resetTimer":         return self.parse_no_arg("ResetTimer")
        if v == "penDown":        return self.parse_no_arg("PenDown")
        if v == "penUp":          return self.parse_no_arg("PenUp")
        if v == "setPenColor":    return self.parse_motion_1num("SetPenColor")
        if v == "changePenColor": return self.parse_motion_1num("ChangePenColor")
        if v == "setPenSize":     return self.parse_motion_1num("SetPenSize")
        if v == "changePenSize":  return self.parse_motion_1num("ChangePenSize")
        if v == "stampPen":       return self.parse_no_arg("StampPen")
        if v == "erasePen":       return self.parse_no_arg("ErasePen")
        if v == "broadcast":         return self.parse_simple_str_cmd("Broadcast")
        if v == "broadcastAndWait":  return self.parse_simple_str_cmd("BroadcastAndWait")
        raise SyntaxError(f"Zeile {ln}: Unbekanntes Statement: {v!r}")

    # ── Kleine Helfer ─────────────────────────────────
    def parse_no_arg(self, t):
        self.consume()
        if self.peek()[1] == "(": self.consume("LPAREN"); self.consume("RPAREN")
        self.expect_semi(); return {"type": t}

    def parse_simple_str_cmd(self, t):
        ln = self.current_line(); self.consume(); self.consume("LPAREN")
        if self.peek()[0] != "STRING":
            raise SyntaxError(f"Zeile {ln}: {t} erwartet einen String in Anführungszeichen")
        val = self.consume("STRING").strip('"')
        self.consume("RPAREN"); self.expect_semi()
        return {"type": t, "value": val}

    def parse_motion_1num(self, t):
        self.consume(); self.consume("LPAREN")
        expr = self.parse_expr(); self.consume("RPAREN"); self.expect_semi()
        return {"type": t, "value": expr}

    def parse_effect_cmd(self, t):
        ln = self.current_line(); self.consume(); self.consume("LPAREN")
        if self.peek()[0] != "STRING":
            raise SyntaxError(f"Zeile {ln}: {t} erwartet Effektname als String (z.B. \"color\")")
        effect = self.consume("STRING").strip('"')
        self.consume("COMMA"); val = self.parse_expr()
        self.consume("RPAREN"); self.expect_semi()
        return {"type": t, "effect": effect, "value": val}

    def parse_var_decl(self):
        self.consume(value="var"); name = self.consume("IDENT"); value = None
        if self.peek()[1] == "=": self.consume(); value = self.parse_expr()
        self.expect_semi(); self.vars.add(name)
        return {"type": "VarDecl", "name": name, "value": value}

    def parse_assignment(self):
        ln = self.current_line(); name = self.consume("IDENT"); op = self.consume()
        if op in ("++","--"):
            self.expect_semi()
            return {"type": "VarChange", "name": name,
                    "value": {"type": "Num", "value": 1 if op=="++" else -1}}
        expr = self.parse_expr(); self.expect_semi()
        if op == "=": return {"type": "VarSet", "name": name, "value": expr}
        op_map = {"+=":"add","-=":"sub","*=":"mul","/=":"div"}
        if op not in op_map:
            raise SyntaxError(f"Zeile {ln}: Unbekannter Zuweisungsoperator: {op!r}")
        return {"type": "VarChange", "name": name, "value": expr, "compound": op_map[op]}

    def parse_list_method(self):
        ln = self.current_line(); name = self.consume("IDENT"); self.consume("DOT")
        method = self.consume(); self.lists.add(name)
        if method == "add":
            self.consume("LPAREN"); item = self.parse_expr()
            self.consume("RPAREN"); self.expect_semi()
            return {"type": "ListAdd", "list": name, "item": item}
        if method == "delete":
            self.consume("LPAREN"); idx = self.parse_expr()
            self.consume("RPAREN"); self.expect_semi()
            return {"type": "ListDelete", "list": name, "index": idx}
        if method == "insert":
            self.consume("LPAREN"); idx = self.parse_expr(); self.consume("COMMA")
            item = self.parse_expr(); self.consume("RPAREN"); self.expect_semi()
            return {"type": "ListInsert", "list": name, "index": idx, "item": item}
        if method == "replace":
            self.consume("LPAREN"); idx = self.parse_expr(); self.consume("COMMA")
            item = self.parse_expr(); self.consume("RPAREN"); self.expect_semi()
            return {"type": "ListReplace", "list": name, "index": idx, "item": item}
        if method == "show":
            if self.peek()[1] == "(": self.consume("LPAREN"); self.consume("RPAREN")
            self.expect_semi(); return {"type": "ShowList", "value": name}
        if method == "hide":
            if self.peek()[1] == "(": self.consume("LPAREN"); self.consume("RPAREN")
            self.expect_semi(); return {"type": "HideList", "value": name}
        raise SyntaxError(f"Zeile {ln}: Unbekannte Listen-Methode: {name}.{method}()\n"
                          f"     Gültig: add, delete, insert, replace, show, hide")

    def parse_custom_call(self):
        name = self.consume("IDENT"); self.consume("LPAREN"); args = []
        while self.peek()[1] != ")":
            args.append(self.parse_expr())
            if self.peek()[1] == ",": self.consume("COMMA")
        self.consume("RPAREN"); self.expect_semi()
        return {"type": "CustomCall", "name": name, "args": args}

    # ── animate("kos1","kos2", secs) ──────────────────
    def parse_animate(self):
        ln = self.current_line(); self.consume(); self.consume("LPAREN")
        costumes = []
        while self.peek()[0] == "STRING":
            costumes.append(self.consume("STRING").strip('"'))
            if self.peek()[1] == ",": self.consume("COMMA")
        if not costumes:
            raise SyntaxError(f"Zeile {ln}: animate() braucht mindestens einen Kostümnamen")
        secs = self.parse_expr()
        self.consume("RPAREN"); self.expect_semi()
        return {"type": "Animate", "costumes": costumes, "secs": secs}

    # ── Control ───────────────────────────────────────
    def parse_repeat(self):
        self.consume(value="repeat"); self.consume("LPAREN")
        times = self.parse_expr(); self.consume("RPAREN")
        return {"type": "Repeat", "times": times, "body": self.parse_block()}

    def parse_forever(self):
        self.consume(value="forever")
        return {"type": "Forever", "body": self.parse_block()}

    def parse_if(self):
        """
        Parst if / elseif / else Ketten.
        elseif wird in verschachtelte if-else-Blöcke übersetzt
        (Scratch hat kein natives elseif).
        """
        self.consume(value="if"); self.consume("LPAREN")
        cond = self.parse_expr(); self.consume("RPAREN")
        then = self.parse_block()
        else_ = None
        nk, nv, _ = self.peek()
        if nv == "else":
            self.consume()
            if self.peek()[1] == "if":
                # else if → rekursiv parsen → erzeugt verschachteltes if
                else_ = [self.parse_if()]
            else:
                else_ = self.parse_block()
        elif nv == "elseif":
            # elseif als Kurzform (kein Leerzeichen nötig)
            else_ = [self.parse_elseif()]
        return {"type": "If", "cond": cond, "then": then, "else": else_}

    def parse_elseif(self):
        self.consume(value="elseif"); self.consume("LPAREN")
        cond = self.parse_expr(); self.consume("RPAREN")
        then = self.parse_block()
        else_ = None
        nk, nv, _ = self.peek()
        if nv == "else":
            self.consume()
            if self.peek()[1] == "if":
                else_ = [self.parse_if()]
            else:
                else_ = self.parse_block()
        elif nv == "elseif":
            else_ = [self.parse_elseif()]
        return {"type": "If", "cond": cond, "then": then, "else": else_}

    def parse_repeat_until(self):
        self.consume(value="repeatUntil"); self.consume("LPAREN")
        cond = self.parse_expr(); self.consume("RPAREN")
        return {"type": "RepeatUntil", "cond": cond, "body": self.parse_block()}

    def parse_wait(self):
        self.consume(value="wait"); self.consume("LPAREN")
        expr = self.parse_expr(); self.consume("RPAREN"); self.expect_semi()
        return {"type": "Wait", "value": expr}

    def parse_wait_until(self):
        self.consume(value="waitUntil"); self.consume("LPAREN")
        cond = self.parse_expr(); self.consume("RPAREN"); self.expect_semi()
        return {"type": "WaitUntil", "cond": cond}

    def parse_stop(self):
        ln = self.current_line(); self.consume(value="stop"); self.consume("LPAREN")
        if self.peek()[0] != "STRING":
            raise SyntaxError(f"Zeile {ln}: stop() erwartet einen String: \"all\", \"this script\" oder \"other scripts in sprite\"")
        opt = self.consume("STRING").strip('"')
        self.consume("RPAREN"); self.expect_semi()
        return {"type": "Stop", "option": opt}

    def parse_create_clone(self):
        self.consume(value="createClone"); self.consume("LPAREN")
        target = self.consume("STRING").strip('"'); self.consume("RPAREN"); self.expect_semi()
        return {"type": "CreateClone", "target": target}

    def parse_delete_clone(self):
        self.consume(value="deleteClone")
        if self.peek()[1] == "(": self.consume("LPAREN"); self.consume("RPAREN")
        self.expect_semi(); return {"type": "DeleteClone"}

    def parse_goto_xy(self):
        self.consume(value="goTo"); self.consume("LPAREN")
        x = self.parse_expr(); self.consume("COMMA"); y = self.parse_expr()
        self.consume("RPAREN"); self.expect_semi()
        return {"type": "GoToXY", "x": x, "y": y}

    def parse_glide(self):
        self.consume(value="glide"); self.consume("LPAREN")
        secs = self.parse_expr(); self.consume("COMMA")
        x    = self.parse_expr(); self.consume("COMMA")
        y    = self.parse_expr(); self.consume("RPAREN"); self.expect_semi()
        return {"type": "Glide", "secs": secs, "x": x, "y": y}

    def parse_glide_to_sprite(self):
        self.consume(value="glideToSprite"); self.consume("LPAREN")
        secs   = self.parse_expr(); self.consume("COMMA")
        target = self.consume("STRING").strip('"')
        self.consume("RPAREN"); self.expect_semi()
        return {"type": "GlideToSprite", "secs": secs, "target": target}

    def parse_say(self, think=False):
        self.consume(); self.consume("LPAREN"); text = self.parse_expr()
        self.consume("RPAREN"); self.expect_semi()
        return {"type": "Think" if think else "Say", "text": text}

    def parse_say_for(self, think=False):
        self.consume(); self.consume("LPAREN")
        text = self.parse_expr(); self.consume("COMMA"); secs = self.parse_expr()
        self.consume("RPAREN"); self.expect_semi()
        return {"type": "ThinkFor" if think else "SayFor", "text": text, "secs": secs}

    # ── Ausdrücke (Pratt-Parser) ──────────────────────
    #
    # Prioritäten (höher = stärker bindend):
    #   dot-postfix (.contains .length …)  ← nach Arithmetik
    #   5  * / %
    #   4  + -
    #   3  == != < > <= >=
    #   2  &&
    #   1  ||

    def parse_expr(self, min_prec=0):
        if self.peek()[1] == "!" and min_prec == 0:
            self.consume()
            if self.peek()[1] == "(":
                # !(expr)  – volle Klammerung
                self.consume("LPAREN"); operand = self.parse_expr(); self.consume("RPAREN")
            else:
                # !expr  – arithmetisch + dot (Java-style)
                operand = self._parse_arithmetic_and_dot()
            left = {"type": "UnaryOp", "op": "!", "operand": operand}
        else:
            left = self.parse_unary()
            left = self._parse_dot_postfix(left)

        while True:
            _, op, _ = self.peek()
            prec = {"||":1,"&&":2,"==":3,"!=":3,"<":3,">":3,"<=":3,">=":3,
                    "+":4,"-":4,"*":5,"/":5,"%":5}.get(op, -1)
            if prec < min_prec: break
            self.consume()
            right = self.parse_expr(prec + 1)
            right = self._parse_dot_postfix(right)
            left = {"type": "BinOp", "op": op, "left": left, "right": right}
        return left

    def _parse_arithmetic_and_dot(self):
        node = self.parse_primary()
        while True:
            _, op, _ = self.peek()
            if op not in ("*","/","%","+","-"): break
            self.consume(); right = self.parse_primary()
            node = {"type": "BinOp", "op": op, "left": node, "right": right}
        return self._parse_dot_postfix(node)

    def _parse_dot_postfix(self, node):
        while self.peek()[1] == ".":
            method = self.peek(1)[1]
            if method not in ("length","contains","letter","join","indexOf"): break
            self.consume("DOT"); self.consume()
            if method == "length":
                if self.peek()[1] == "(": self.consume("LPAREN"); self.consume("RPAREN")
                if node["type"] == "Var" and node.get("name","") in self.lists:
                    node = {"type": "ListLength", "list": node["name"]}
                else:
                    node = {"type": "StrLength", "value": node}
            elif method == "contains":
                self.consume("LPAREN"); arg = self.parse_expr(); self.consume("RPAREN")
                if node["type"] == "Var" and node.get("name","") in self.lists:
                    node = {"type": "ListContains", "list": node["name"], "item": arg}
                else:
                    node = {"type": "StrContains", "str": node, "sub": arg}
            elif method == "letter":
                self.consume("LPAREN"); n = self.parse_expr(); self.consume("RPAREN")
                node = {"type": "LetterOf", "n": n, "str": node}
            elif method == "join":
                self.consume("LPAREN"); other = self.parse_expr(); self.consume("RPAREN")
                node = {"type": "Join", "a": node, "b": other}
            elif method == "indexOf":
                self.consume("LPAREN"); arg = self.parse_expr(); self.consume("RPAREN")
                node = {"type": "StrContains", "str": node, "sub": arg}
        return node

    def parse_unary(self):
        _, v, _ = self.peek()
        if v == "-":
            self.consume(); return {"type": "UnaryOp", "op": "-", "operand": self.parse_primary()}
        return self.parse_primary()

    def parse_primary(self):
        k, v, ln = self.peek()
        if k == "NUMBER":
            self.consume(); return {"type": "Num", "value": float(v)}
        if k == "STRING":
            self.consume(); return {"type": "Str", "value": v.strip('"')}
        if v == "true":  self.consume(); return {"type": "Bool", "value": True}
        if v == "false": self.consume(); return {"type": "Bool", "value": False}
        if v == "(":
            self.consume("LPAREN"); e = self.parse_expr(); self.consume("RPAREN"); return e
        if v == "Math":
            self.consume(); self.consume("DOT"); method = self.consume()
            self.consume("LPAREN")
            if method == "random":
                a = self.parse_expr(); self.consume("COMMA"); b = self.parse_expr()
                self.consume("RPAREN"); return {"type": "Random", "from": a, "to": b}
            if method == "round":
                x = self.parse_expr(); self.consume("RPAREN"); return {"type": "Round", "value": x}
            if method in ("abs","floor","ceil","sqrt","sin","cos","tan",
                          "asin","acos","atan","ln","log"):
                lbl = "ceiling" if method == "ceil" else method
                x = self.parse_expr(); self.consume("RPAREN")
                return {"type": "MathOp", "op": lbl, "value": x}
            raise SyntaxError(f"Zeile {ln}: Unbekannte Math-Methode: Math.{method}()")
        if v in ("random","abs","floor","ceil","sqrt","sin","cos","tan",
                 "asin","acos","atan","ln","log","round","length","letter",
                 "contains","join"):
            return self.parse_operator_func(v)
        if v in ("answer","mouseX","mouseY","mouseDown","timer","loudness","username"):
            self.consume(); return {"type": "Sensing", "sense": v}
        if v in ("currentYear","currentMonth","currentDate","currentDayOfWeek",
                 "currentHour","currentMinute","currentSecond"):
            self.consume()
            fm = {"currentYear":"YEAR","currentMonth":"MONTH","currentDate":"DATE",
                  "currentDayOfWeek":"DAYOFWEEK","currentHour":"HOUR",
                  "currentMinute":"MINUTE","currentSecond":"SECOND"}
            return {"type": "CurrentDate", "field": fm[v]}
        if v == "keyPressed":
            self.consume(); self.consume("LPAREN"); key = self.consume("STRING").strip('"')
            self.consume("RPAREN"); return {"type": "KeyPressed", "key": key}
        if v == "touching":
            self.consume(); self.consume("LPAREN"); target = self.consume("STRING").strip('"')
            self.consume("RPAREN"); return {"type": "Touching", "target": target}
        if v == "touchingColor":
            self.consume(); self.consume("LPAREN"); color = self.parse_expr()
            self.consume("RPAREN"); return {"type": "TouchingColor", "color": color}
        if v == "distanceTo":
            self.consume(); self.consume("LPAREN"); target = self.consume("STRING").strip('"')
            self.consume("RPAREN"); return {"type": "DistanceTo", "target": target}
        if v in ("xPosition","yPosition","direction"):
            self.consume(); return {"type": "MotionVal", "val": v}
        if k == "IDENT":
            name = self.consume("IDENT")
            if self.peek()[1] == "[":
                self.consume("LBRACKET"); idx = self.parse_expr(); self.consume("RBRACKET")
                return {"type": "ListItem", "list": name, "index": idx}
            return {"type": "Var", "name": name}
        raise SyntaxError(f"Zeile {ln}: Unerwartetes Token: {v!r} (Typ: {k}) – "
                          f"Ausdruck erwartet")

    def parse_operator_func(self, name):
        self.consume(); self.consume("LPAREN")
        if name == "random":
            a = self.parse_expr(); self.consume("COMMA"); b = self.parse_expr()
            self.consume("RPAREN"); return {"type": "Random", "from": a, "to": b}
        if name == "length":
            s = self.parse_expr(); self.consume("RPAREN"); return {"type": "StrLength", "value": s}
        if name == "letter":
            n = self.parse_expr(); self.consume("COMMA"); s = self.parse_expr()
            self.consume("RPAREN"); return {"type": "LetterOf", "n": n, "str": s}
        if name == "contains":
            s = self.parse_expr(); self.consume("COMMA"); sub = self.parse_expr()
            self.consume("RPAREN"); return {"type": "StrContains", "str": s, "sub": sub}
        if name == "join":
            a = self.parse_expr(); self.consume("COMMA"); b = self.parse_expr()
            self.consume("RPAREN"); return {"type": "Join", "a": a, "b": b}
        if name == "round":
            x = self.parse_expr(); self.consume("RPAREN"); return {"type": "Round", "value": x}
        lbl = "ceiling" if name == "ceil" else name
        x = self.parse_expr(); self.consume("RPAREN")
        return {"type": "MathOp", "op": lbl, "value": x}


# ═══════════════════════════════════════════════════════
#  3.  CODE-GENERATOR
# ═══════════════════════════════════════════════════════
class ScratchGenerator:
    def __init__(self):
        self.blocks:       dict = {}
        self.variables:    dict = {}
        self.lists:        dict = {}
        self.broadcasts:   dict = {}
        self.custom_procs: dict = {}

    def _add(self, bid, opcode, parent, nxt,
             inputs=None, fields=None, top=False, x=0, y=0, mutation=None):
        b = {"opcode": opcode, "next": nxt, "parent": parent,
             "inputs": inputs or {}, "fields": fields or {},
             "shadow": False, "topLevel": top}
        if top: b["x"] = x; b["y"] = y
        if mutation: b["mutation"] = mutation
        self.blocks[bid] = b; return bid

    def _iv(self, node):
        if node["type"] == "Num":
            v = node["value"]
            return [4, str(int(v) if isinstance(v, float) and v.is_integer() else v)]
        if node["type"] == "Str":  return [10, node["value"]]
        if node["type"] == "Bool": return [10, "true" if node["value"] else "false"]
        return None

    def _input(self, node, parent_id, slot=1):
        iv = self._iv(node)
        if iv: return [slot, iv]
        return [slot, self.gen_expr(node, parent_id)]

    def _bool_input(self, node, parent_id):
        iv = self._iv(node)
        if iv: return [2, iv]
        return [2, self.gen_expr(node, parent_id)]

    def _var_id(self, n):
        if n not in self.variables: self.variables[n] = new_id()
        return self.variables[n]

    def _list_id(self, n):
        if n not in self.lists: self.lists[n] = new_id()
        return self.lists[n]

    def _broadcast_id(self, n):
        if n not in self.broadcasts: self.broadcasts[n] = new_id()
        return self.broadcasts[n]

    def _menu_shadow(self, opcode, field_name, value, parent_id):
        mid = new_id()
        self.blocks[mid] = {"opcode": opcode, "next": None, "parent": parent_id,
                            "inputs": {}, "fields": {field_name: [value, None]},
                            "shadow": True, "topLevel": False}
        return mid

    def _gen_seq(self, stmts, parent_id):
        if not stmts: return None
        ids = [new_id() for _ in stmts]
        for i, stmt in enumerate(stmts):
            par = parent_id if i == 0 else ids[i-1]
            nxt = ids[i+1] if i+1 < len(ids) else None
            real = self.gen_stmt(stmt, par, nxt)
            if real != ids[i]:
                self.blocks[ids[i]] = self.blocks.pop(real)
                b = self.blocks[ids[i]]
                for f in ("next","parent"):
                    if b[f] == real: b[f] = ids[i]
                for sb in self.blocks.values():
                    for f in ("next","parent"):
                        if sb.get(f) == real: sb[f] = ids[i]
                    for inp in sb.get("inputs",{}).values():
                        if isinstance(inp,list) and len(inp)>1 and inp[1]==real:
                            inp[1] = ids[i]
        return ids[0]

    def gen_hat(self, event, x=0, y=0):
        bid = new_id(); t = event["type"]
        if t == "EventFlagClicked":
            self._add(bid, "event_whenflagclicked", None, None, top=True, x=x, y=y)
        elif t == "EventKeyPressed":
            self._add(bid, "event_whenkeypressed", None, None,
                      fields={"KEY_OPTION": [event["key"], None]}, top=True, x=x, y=y)
        elif t == "EventSpriteClicked":
            self._add(bid, "event_whenthisspriteclicked", None, None, top=True, x=x, y=y)
        elif t == "EventBackdropChanged":
            self._add(bid, "event_whenbackdropswitchesto", None, None,
                      fields={"BACKDROP": [event["backdrop"], None]}, top=True, x=x, y=y)
        elif t == "EventBroadcastReceived":
            bid2 = self._broadcast_id(event["message"])
            self._add(bid, "event_whenbroadcastreceived", None, None,
                      fields={"BROADCAST_OPTION": [event["message"], bid2]}, top=True, x=x, y=y)
        elif t == "CustomDefHat":
            self._add(bid, "procedures_definition", None, None,
                      inputs={"custom_block": [1, event["proto_id"]]}, top=True, x=x, y=y)
        return bid

    # ── animate() expandieren ─────────────────────────
    def _expand_animate(self, node, parent_id, next_id):
        """
        animate("kos1","kos2","kos3", 0.1)
        wird zu:
          switchCostume("kos1"); wait(0.1);
          switchCostume("kos2"); wait(0.1);
          switchCostume("kos3"); wait(0.1);
        """
        stmts = []
        for cname in node["costumes"]:
            stmts.append({"type": "SwitchCostume", "value": cname})
            stmts.append({"type": "Wait", "value": node["secs"]})
        return self._gen_seq(stmts, parent_id)

    def gen_stmt(self, node, parent_id, next_id):
        t = node["type"]; bid = new_id()

        # Animate → expandieren
        if t == "Animate":
            first = self._expand_animate(node, parent_id, next_id)
            # Letzten Block mit next_id verbinden
            if first:
                cur = first
                while self.blocks[cur]["next"]:
                    cur = self.blocks[cur]["next"]
                self.blocks[cur]["next"] = next_id
                if next_id: self.blocks.get(next_id, {})  # next parent wird später gesetzt
            return first or bid

        # Variablen
        if t == "VarDecl":
            inp = self._input(node["value"], bid) if node["value"] else [1,[10,""]]
            self._add(bid, "data_setvariableto", parent_id, next_id,
                inputs={"VALUE": inp}, fields={"VARIABLE": [node["name"], self._var_id(node["name"])]})
            return bid
        if t == "VarSet":
            self._add(bid, "data_setvariableto", parent_id, next_id,
                inputs={"VALUE": self._input(node["value"], bid)},
                fields={"VARIABLE": [node["name"], self._var_id(node["name"])]})
            return bid
        if t == "VarChange":
            if node.get("compound") in (None, "add"):
                self._add(bid, "data_changevariableby", parent_id, next_id,
                    inputs={"VALUE": self._input(node["value"], bid)},
                    fields={"VARIABLE": [node["name"], self._var_id(node["name"])]})
            else:
                op_m = {"sub":"-","mul":"*","div":"/"}
                inner = {"type":"BinOp","op":op_m[node["compound"]],
                         "left":{"type":"Var","name":node["name"]},"right":node["value"]}
                self._add(bid, "data_setvariableto", parent_id, next_id,
                    inputs={"VALUE": self._input(inner, bid)},
                    fields={"VARIABLE": [node["name"], self._var_id(node["name"])]})
            return bid
        if t == "ShowVar":
            self._add(bid, "data_showvariable", parent_id, next_id,
                fields={"VARIABLE": [node["value"], self._var_id(node["value"])]}); return bid
        if t == "HideVar":
            self._add(bid, "data_hidevariable", parent_id, next_id,
                fields={"VARIABLE": [node["value"], self._var_id(node["value"])]}); return bid

        # Listen
        if t == "ListAdd":
            self._add(bid, "data_addtolist", parent_id, next_id,
                inputs={"ITEM": self._input(node["item"], bid)},
                fields={"LIST": [node["list"], self._list_id(node["list"])]}); return bid
        if t == "ListDelete":
            self._add(bid, "data_deleteoflist", parent_id, next_id,
                inputs={"INDEX": self._input(node["index"], bid)},
                fields={"LIST": [node["list"], self._list_id(node["list"])]}); return bid
        if t == "ListInsert":
            self._add(bid, "data_insertatlist", parent_id, next_id,
                inputs={"INDEX": self._input(node["index"],bid),"ITEM": self._input(node["item"],bid)},
                fields={"LIST": [node["list"], self._list_id(node["list"])]}); return bid
        if t == "ListReplace":
            self._add(bid, "data_replaceitemoflist", parent_id, next_id,
                inputs={"INDEX": self._input(node["index"],bid),"ITEM": self._input(node["item"],bid)},
                fields={"LIST": [node["list"], self._list_id(node["list"])]}); return bid
        if t == "ShowList":
            self._add(bid, "data_showlist", parent_id, next_id,
                fields={"LIST": [node["value"], self._list_id(node["value"])]}); return bid
        if t == "HideList":
            self._add(bid, "data_hidelist", parent_id, next_id,
                fields={"LIST": [node["value"], self._list_id(node["value"])]}); return bid

        # Control
        if t == "Repeat":
            inner = self._gen_seq(node["body"], bid)
            self._add(bid, "control_repeat", parent_id, next_id,
                inputs={"TIMES": self._input(node["times"], bid),
                        "SUBSTACK": [2, inner] if inner else {}}); return bid
        if t == "Forever":
            inner = self._gen_seq(node["body"], bid)
            self._add(bid, "control_forever", parent_id, next_id,
                inputs={"SUBSTACK": [2, inner] if inner else {}}); return bid
        if t == "If":
            cond = self._bool_input(node["cond"], bid)
            then = self._gen_seq(node["then"], bid)
            if node["else"]:
                else_ = self._gen_seq(node["else"], bid)
                self._add(bid, "control_if_else", parent_id, next_id,
                    inputs={"CONDITION": cond,
                            "SUBSTACK":  [2, then]  if then  else {},
                            "SUBSTACK2": [2, else_] if else_ else {}})
            else:
                self._add(bid, "control_if", parent_id, next_id,
                    inputs={"CONDITION": cond, "SUBSTACK": [2, then] if then else {}})
            return bid
        if t == "RepeatUntil":
            cond = self._bool_input(node["cond"], bid); inner = self._gen_seq(node["body"], bid)
            self._add(bid, "control_repeat_until", parent_id, next_id,
                inputs={"CONDITION": cond, "SUBSTACK": [2, inner] if inner else {}}); return bid
        if t == "Wait":
            self._add(bid, "control_wait", parent_id, next_id,
                inputs={"DURATION": self._input(node["value"], bid)}); return bid
        if t == "WaitUntil":
            self._add(bid, "control_wait_until", parent_id, next_id,
                inputs={"CONDITION": self._bool_input(node["cond"], bid)}); return bid
        if t == "Stop":
            self._add(bid, "control_stop", parent_id, next_id,
                fields={"STOP_OPTION": [node["option"], None]},
                mutation={"tagName":"mutation","children":[],"hasnext":"false"}); return bid
        if t == "CreateClone":
            mid = self._menu_shadow("control_create_clone_of_menu","CLONE_OPTION",node["target"],bid)
            self._add(bid, "control_create_clone_of", parent_id, next_id,
                inputs={"CLONE_OPTION": [1, mid]}); return bid
        if t == "DeleteClone":
            self._add(bid, "control_delete_this_clone", parent_id, next_id); return bid

        # Motion
        if t == "Move":
            self._add(bid,"motion_movesteps",parent_id,next_id,inputs={"STEPS":self._input(node["value"],bid)}); return bid
        if t == "TurnLeft":
            self._add(bid,"motion_turnleft",parent_id,next_id,inputs={"DEGREES":self._input(node["value"],bid)}); return bid
        if t == "TurnRight":
            self._add(bid,"motion_turnright",parent_id,next_id,inputs={"DEGREES":self._input(node["value"],bid)}); return bid
        if t == "GoToXY":
            self._add(bid,"motion_gotoxy",parent_id,next_id,
                inputs={"X":self._input(node["x"],bid),"Y":self._input(node["y"],bid)}); return bid
        if t == "GoToSprite":
            mid = self._menu_shadow("motion_goto_menu","TO",node["value"],bid)
            self._add(bid,"motion_goto",parent_id,next_id,inputs={"TO":[1,mid]}); return bid
        if t == "Glide":
            self._add(bid,"motion_glidesecstoxy",parent_id,next_id,
                inputs={"SECS":self._input(node["secs"],bid),
                        "X":self._input(node["x"],bid),"Y":self._input(node["y"],bid)}); return bid
        if t == "GlideToSprite":
            mid = self._menu_shadow("motion_glideto_menu","TO",node["target"],bid)
            self._add(bid,"motion_glideto",parent_id,next_id,
                inputs={"SECS":self._input(node["secs"],bid),"TO":[1,mid]}); return bid
        if t == "PointDir":
            self._add(bid,"motion_pointindirection",parent_id,next_id,
                inputs={"DIRECTION":self._input(node["value"],bid)}); return bid
        if t == "PointTowards":
            mid = self._menu_shadow("motion_pointtowards_menu","TOWARDS",node["value"],bid)
            self._add(bid,"motion_pointtowards",parent_id,next_id,inputs={"TOWARDS":[1,mid]}); return bid
        if t == "SetX":
            self._add(bid,"motion_setx",parent_id,next_id,inputs={"X":self._input(node["value"],bid)}); return bid
        if t == "SetY":
            self._add(bid,"motion_sety",parent_id,next_id,inputs={"Y":self._input(node["value"],bid)}); return bid
        if t == "ChangeX":
            self._add(bid,"motion_changexby",parent_id,next_id,inputs={"DX":self._input(node["value"],bid)}); return bid
        if t == "ChangeY":
            self._add(bid,"motion_changeyby",parent_id,next_id,inputs={"DY":self._input(node["value"],bid)}); return bid
        if t == "BounceOnEdge":
            self._add(bid,"motion_ifonedgebounce",parent_id,next_id); return bid
        if t == "SetRotationStyle":
            self._add(bid,"motion_setrotationstyle",parent_id,next_id,
                fields={"STYLE":[node["value"],None]}); return bid

        # Looks
        if t == "Say":
            self._add(bid,"looks_say",parent_id,next_id,inputs={"MESSAGE":self._input(node["text"],bid)}); return bid
        if t == "SayFor":
            self._add(bid,"looks_sayforsecs",parent_id,next_id,
                inputs={"MESSAGE":self._input(node["text"],bid),"SECS":self._input(node["secs"],bid)}); return bid
        if t == "Think":
            self._add(bid,"looks_think",parent_id,next_id,inputs={"MESSAGE":self._input(node["text"],bid)}); return bid
        if t == "ThinkFor":
            self._add(bid,"looks_thinkforsecs",parent_id,next_id,
                inputs={"MESSAGE":self._input(node["text"],bid),"SECS":self._input(node["secs"],bid)}); return bid
        if t == "SwitchCostume":
            mid = self._menu_shadow("looks_costume","COSTUME",node["value"],bid)
            self._add(bid,"looks_switchcostumeto",parent_id,next_id,inputs={"COSTUME":[1,mid]}); return bid
        if t == "NextCostume":
            self._add(bid,"looks_nextcostume",parent_id,next_id); return bid
        if t == "SwitchBackdrop":
            mid = self._menu_shadow("looks_backdrops","BACKDROP",node["value"],bid)
            self._add(bid,"looks_switchbackdropto",parent_id,next_id,inputs={"BACKDROP":[1,mid]}); return bid
        if t == "NextBackdrop":
            self._add(bid,"looks_nextbackdrop",parent_id,next_id); return bid
        if t == "SetSize":
            self._add(bid,"looks_setsizeto",parent_id,next_id,inputs={"SIZE":self._input(node["value"],bid)}); return bid
        if t == "ChangeSize":
            self._add(bid,"looks_changesizeby",parent_id,next_id,inputs={"CHANGE":self._input(node["value"],bid)}); return bid
        if t == "Show":
            self._add(bid,"looks_show",parent_id,next_id); return bid
        if t == "Hide":
            self._add(bid,"looks_hide",parent_id,next_id); return bid
        if t == "GoToFront":
            self._add(bid,"looks_gotofrontback",parent_id,next_id,fields={"FRONT_BACK":["front",None]}); return bid
        if t == "GoToBack":
            self._add(bid,"looks_gotofrontback",parent_id,next_id,fields={"FRONT_BACK":["back",None]}); return bid
        if t == "GoForwardLayers":
            self._add(bid,"looks_goforwardbackwardlayers",parent_id,next_id,
                inputs={"NUM":self._input(node["value"],bid)},fields={"FORWARD_BACKWARD":["forward",None]}); return bid
        if t == "GoBackwardLayers":
            self._add(bid,"looks_goforwardbackwardlayers",parent_id,next_id,
                inputs={"NUM":self._input(node["value"],bid)},fields={"FORWARD_BACKWARD":["backward",None]}); return bid
        if t == "SetEffect":
            self._add(bid,"looks_seteffectto",parent_id,next_id,
                inputs={"VALUE":self._input(node["value"],bid)},
                fields={"EFFECT":[node["effect"].upper(),None]}); return bid
        if t == "ChangeEffect":
            self._add(bid,"looks_changeeffectby",parent_id,next_id,
                inputs={"CHANGE":self._input(node["value"],bid)},
                fields={"EFFECT":[node["effect"].upper(),None]}); return bid
        if t == "ClearEffects":
            self._add(bid,"looks_cleargraphiceffects",parent_id,next_id); return bid

        # Sound
        if t == "PlaySound":
            mid = self._menu_shadow("sound_sounds_menu","SOUND_MENU",node["value"],bid)
            self._add(bid,"sound_play",parent_id,next_id,inputs={"SOUND_MENU":[1,mid]}); return bid
        if t == "PlaySoundUntilDone":
            mid = self._menu_shadow("sound_sounds_menu","SOUND_MENU",node["value"],bid)
            self._add(bid,"sound_playuntildone",parent_id,next_id,inputs={"SOUND_MENU":[1,mid]}); return bid
        if t == "StopAllSounds":
            self._add(bid,"sound_stopallsounds",parent_id,next_id); return bid
        if t == "SetVolume":
            self._add(bid,"sound_setvolumeto",parent_id,next_id,inputs={"VOLUME":self._input(node["value"],bid)}); return bid
        if t == "ChangeVolume":
            self._add(bid,"sound_changevolumeby",parent_id,next_id,inputs={"CHANGE":self._input(node["value"],bid)}); return bid

        # Sensing
        if t == "AskAndWait":
            self._add(bid,"sensing_askandwait",parent_id,next_id,
                inputs={"QUESTION":[1,[10,node["value"]]]}); return bid
        if t == "SetDragMode":
            self._add(bid,"sensing_setdragmode",parent_id,next_id,
                fields={"DRAG_MODE":[node["value"],None]}); return bid
        if t == "ResetTimer":
            self._add(bid,"sensing_resettimer",parent_id,next_id); return bid

        # Pen
        if t == "PenDown":
            self._add(bid,"pen_penDown",parent_id,next_id); return bid
        if t == "PenUp":
            self._add(bid,"pen_penUp",parent_id,next_id); return bid
        if t == "SetPenColor":
            self._add(bid,"pen_setPenColorToColor",parent_id,next_id,
                inputs={"COLOR":self._input(node["value"],bid)}); return bid
        if t == "ChangePenColor":
            self._add(bid,"pen_changePenColorBy",parent_id,next_id,
                inputs={"COLOR":self._input(node["value"],bid)}); return bid
        if t == "SetPenSize":
            self._add(bid,"pen_setPenSizeTo",parent_id,next_id,
                inputs={"SIZE":self._input(node["value"],bid)}); return bid
        if t == "ChangePenSize":
            self._add(bid,"pen_changePenSizeBy",parent_id,next_id,
                inputs={"SIZE":self._input(node["value"],bid)}); return bid
        if t == "StampPen":
            self._add(bid,"pen_stamp",parent_id,next_id); return bid
        if t == "ErasePen":
            self._add(bid,"pen_clear",parent_id,next_id); return bid

        # Broadcast
        if t == "Broadcast":
            mid = self._broadcast_id(node["value"])
            self._add(bid,"event_broadcast",parent_id,next_id,
                inputs={"BROADCAST_INPUT":[1,[11,node["value"],mid]]}); return bid
        if t == "BroadcastAndWait":
            mid = self._broadcast_id(node["value"])
            self._add(bid,"event_broadcastandwait",parent_id,next_id,
                inputs={"BROADCAST_INPUT":[1,[11,node["value"],mid]]}); return bid

        # Custom blocks
        if t == "CustomCall":
            proccode = self.custom_procs.get(node["name"],
                           node["name"]+" "+" ".join(["%s"]*len(node["args"])))
            arg_ids  = [new_id() for _ in node["args"]]
            inputs   = {aid: self._input(arg, bid) for aid, arg in zip(arg_ids, node["args"])}
            mutation = {"tagName":"mutation","children":[],"proccode":proccode,
                        "argumentids":json.dumps(arg_ids),"warp":"false"}
            self._add(bid,"procedures_call",parent_id,next_id,inputs=inputs,mutation=mutation)
            return bid

        raise ValueError(f"Unbekannter Statement-Typ: {t!r}")

    def gen_expr(self, node, parent_id):
        bid = new_id(); t = node["type"]
        if t == "Num":
            v = node["value"]
            s = str(int(v) if isinstance(v,float) and v.is_integer() else v)
            self._add(bid,"math_number",parent_id,None,fields={"NUM":[s,None]})
            self.blocks[bid]["shadow"] = True; return bid
        if t == "Str":
            self._add(bid,"text",parent_id,None,fields={"TEXT":[node["value"],None]})
            self.blocks[bid]["shadow"] = True; return bid
        if t == "Bool":
            if node["value"]:
                self._add(bid,"operator_equals",parent_id,None,
                    inputs={"OPERAND1":[1,[10,"1"]],"OPERAND2":[1,[10,"1"]]}); return bid
            inner = new_id()
            self._add(inner,"operator_not",parent_id,None,inputs={})
            self._add(bid,"operator_not",parent_id,None,inputs={"OPERAND":[2,inner]}); return bid
        if t == "Var":
            vid = self._var_id(node["name"])
            self._add(bid,"data_variable",parent_id,None,
                fields={"VARIABLE":[node["name"],vid]}); return bid
        if t == "MotionVal":
            op = {"xPosition":"motion_xposition","yPosition":"motion_yposition",
                  "direction":"motion_direction"}[node["val"]]
            self._add(bid,op,parent_id,None); return bid
        if t == "BinOp":
            op = node["op"]
            op_map = {"+":"operator_add","-":"operator_subtract","*":"operator_multiply",
                      "/":"operator_divide","%":"operator_mod","<":"operator_lt",
                      ">":"operator_gt","==":"operator_equals","&&":"operator_and","||":"operator_or"}
            l = self._input(node["left"],bid); r = self._input(node["right"],bid)
            if op == "!=":
                eq = new_id()
                self._add(eq,"operator_equals",bid,None,inputs={"OPERAND1":l,"OPERAND2":r})
                self._add(bid,"operator_not",parent_id,None,inputs={"OPERAND":[2,eq]}); return bid
            if op in ("&&","||"):
                self._add(bid,op_map[op],parent_id,None,inputs={"OPERAND1":l,"OPERAND2":r})
            elif op in ("+","-","*","/","%"):
                self._add(bid,op_map[op],parent_id,None,inputs={"NUM1":l,"NUM2":r})
            else:
                self._add(bid,op_map[op],parent_id,None,inputs={"OPERAND1":l,"OPERAND2":r})
            return bid
        if t == "UnaryOp":
            if node["op"] == "!":
                self._add(bid,"operator_not",parent_id,None,
                    inputs={"OPERAND":self._bool_input(node["operand"],bid)}); return bid
            self._add(bid,"operator_subtract",parent_id,None,
                inputs={"NUM1":[1,[4,"0"]],"NUM2":self._input(node["operand"],bid)}); return bid
        if t == "Random":
            self._add(bid,"operator_random",parent_id,None,
                inputs={"FROM":self._input(node["from"],bid),"TO":self._input(node["to"],bid)}); return bid
        if t == "Round":
            self._add(bid,"operator_round",parent_id,None,
                inputs={"NUM":self._input(node["value"],bid)}); return bid
        if t == "MathOp":
            self._add(bid,"operator_mathop",parent_id,None,
                inputs={"NUM":self._input(node["value"],bid)},
                fields={"OPERATOR":[node["op"],None]}); return bid
        if t == "StrLength":
            self._add(bid,"operator_length",parent_id,None,
                inputs={"STRING":self._input(node["value"],bid)}); return bid
        if t == "LetterOf":
            self._add(bid,"operator_letter_of",parent_id,None,
                inputs={"LETTER":self._input(node["n"],bid),"STRING":self._input(node["str"],bid)}); return bid
        if t == "StrContains":
            self._add(bid,"operator_contains",parent_id,None,
                inputs={"STRING1":self._input(node["str"],bid),"STRING2":self._input(node["sub"],bid)}); return bid
        if t == "Join":
            self._add(bid,"operator_join",parent_id,None,
                inputs={"STRING1":self._input(node["a"],bid),"STRING2":self._input(node["b"],bid)}); return bid
        if t == "Sensing":
            sm = {"answer":("sensing_answer",{}),"mouseX":("sensing_mousex",{}),"mouseY":("sensing_mousey",{}),
                  "mouseDown":("sensing_mousedown",{}),"timer":("sensing_timer",{}),
                  "loudness":("sensing_loudness",{}),"username":("sensing_username",{})}
            opcode, fields = sm[node["sense"]]
            self._add(bid,opcode,parent_id,None,fields=fields); return bid
        if t == "CurrentDate":
            self._add(bid,"sensing_current",parent_id,None,
                fields={"CURRENTMENU":[node["field"],None]}); return bid
        if t == "KeyPressed":
            mid = self._menu_shadow("sensing_keyoptions","KEY_OPTION",node["key"],bid)
            self._add(bid,"sensing_keypressed",parent_id,None,
                inputs={"KEY_OPTION":[1,mid]}); return bid
        if t == "Touching":
            mid = self._menu_shadow("sensing_touchingobjectmenu","TOUCHINGOBJECTMENU",node["target"],bid)
            self._add(bid,"sensing_touchingobject",parent_id,None,
                inputs={"TOUCHINGOBJECTMENU":[1,mid]}); return bid
        if t == "TouchingColor":
            self._add(bid,"sensing_touchingcolor",parent_id,None,
                inputs={"COLOR":self._input(node["color"],bid)}); return bid
        if t == "DistanceTo":
            mid = self._menu_shadow("sensing_distancetomenu","DISTANCETOMENU",node["target"],bid)
            self._add(bid,"sensing_distanceto",parent_id,None,
                inputs={"DISTANCETOMENU":[1,mid]}); return bid
        if t == "ListItem":
            self._add(bid,"data_itemoflist",parent_id,None,
                inputs={"INDEX":self._input(node["index"],bid)},
                fields={"LIST":[node["list"],self._list_id(node["list"])]}); return bid
        if t == "ListLength":
            self._add(bid,"data_lengthoflist",parent_id,None,
                fields={"LIST":[node["list"],self._list_id(node["list"])]}); return bid
        if t == "ListContains":
            self._add(bid,"data_listcontainsitem",parent_id,None,
                inputs={"ITEM":self._input(node["item"],bid)},
                fields={"LIST":[node["list"],self._list_id(node["list"])]}); return bid
        raise ValueError(f"Unbekannter Ausdrucks-Typ: {t!r}")

    def gen_custom_def(self, cdef, x=0, y=0):
        proto_id  = new_id(); param_ids = [new_id() for _ in cdef["params"]]
        proccode  = cdef["name"] + "".join(f" %s" for _ in cdef["params"])
        self.custom_procs[cdef["name"]] = proccode
        proto_inputs = {}
        for pid, pname in zip(param_ids, cdef["params"]):
            ab = new_id()
            self.blocks[ab] = {"opcode":"argument_reporter_string_number","next":None,
                "parent":proto_id,"inputs":{},"fields":{"VALUE":[pname,None]},
                "shadow":True,"topLevel":False}
            proto_inputs[pid] = [1, ab]
        self.blocks[proto_id] = {"opcode":"procedures_prototype","next":None,"parent":None,
            "inputs":proto_inputs,"fields":{},"shadow":True,"topLevel":False,
            "mutation":{"tagName":"mutation","children":[],"proccode":proccode,
                "argumentids":json.dumps(param_ids),"argumentnames":json.dumps(cdef["params"]),
                "argumentdefaults":json.dumps([""]*len(cdef["params"])),"warp":"false"}}
        hat_id = new_id()
        self._add(hat_id,"procedures_definition",None,None,
            inputs={"custom_block":[1,proto_id]},top=True,x=x,y=y)
        first = self._gen_seq(cdef["body"], hat_id)
        self.blocks[hat_id]["next"] = first
        return hat_id

    def gen_target(self, target_node):
        self.blocks = {}; self.variables = {}; self.lists = {}
        self.broadcasts = {}; self.custom_procs = {}
        for cdef in target_node.get("customDefs",[]):
            self.custom_procs[cdef["name"]] = cdef["name"]+"".join(" %s" for _ in cdef["params"])
        x_off = 0
        for cdef in target_node.get("customDefs",[]):
            self.gen_custom_def(cdef, x=x_off, y=-300); x_off += 300
        x_off = 0
        for script in target_node.get("scripts",[]):
            hat_id = self.gen_hat(script["event"], x=x_off, y=0)
            first  = self._gen_seq(script["body"], hat_id)
            self.blocks[hat_id]["next"] = first
            x_off += 300
        return self.blocks, self.variables, self.lists, self.broadcasts


# ═══════════════════════════════════════════════════════
#  4.  project.json Zusammenbau
# ═══════════════════════════════════════════════════════
def build_project(ast: dict, asset_mgr: AssetManager) -> dict:
    gen = ScratchGenerator(); targets = []; all_broadcasts = {}

    stage_node = next((t for t in ast["targets"] if t["type"]=="Stage"), None)
    stage_blocks, stage_vars, stage_lists = {}, {}, {}
    if stage_node:
        print(f"  Stage '{stage_node['name']}':")
        stage_blocks, stage_vars, stage_lists, bcast = gen.gen_target(stage_node)
        all_broadcasts.update(bcast)
        backdrops = []
        for bd in stage_node.get("backdrops",[]):
            print(f"    Hintergrund '{bd['name']}'" + (f" ← {bd['path']}" if bd["path"] else ""))
            backdrops.append(asset_mgr.load_backdrop(bd["path"], bd["name"]))
        if not backdrops: backdrops.append(asset_mgr.load_backdrop(None, "Hintergrund1"))
        sounds = [asset_mgr.load_sound(s["path"], s["name"]) for s in stage_node.get("sounds",[])]
    else:
        backdrops = [asset_mgr.load_backdrop(None, "Hintergrund1")]; sounds = []

    targets.append({
        "isStage":True,"name":"Stage",
        "variables":{vid:[name,0]  for name,vid in stage_vars.items()},
        "lists":     {lid:[name,[]] for name,lid in stage_lists.items()},
        "broadcasts":{},"blocks":stage_blocks,"comments":{},"currentCostume":0,
        "costumes":backdrops,"sounds":sounds,"layerOrder":0,"tempo":60,"volume":100,
        "videoTransparency":50,"videoState":"on","textToSpeechLanguage":None,
    })

    for i, snode in enumerate([t for t in ast["targets"] if t["type"]=="Sprite"]):
        print(f"  Sprite '{snode['name']}':")
        blocks, variables, lists, bcast = gen.gen_target(snode)
        all_broadcasts.update(bcast)
        costumes = []
        for c in snode.get("costumes",[]):
            print(f"    Kostüm '{c['name']}'" + (f" ← {c['path']}" if c["path"] else ""))
            costumes.append(asset_mgr.load_image(c["path"], c["name"]))
        if not costumes: costumes.append(asset_mgr.load_image(None, "Kostüm1"))
        sounds = [asset_mgr.load_sound(s["path"], s["name"]) for s in snode.get("sounds",[])]
        targets.append({
            "isStage":False,"name":snode["name"],
            "variables":{vid:[name,0]  for name,vid in variables.items()},
            "lists":     {lid:[name,[]] for name,lid in lists.items()},
            "broadcasts":{},"blocks":blocks,"comments":{},"currentCostume":0,
            "costumes":costumes,"sounds":sounds,"layerOrder":i+1,
            "visible":True,"x":0,"y":0,"size":100,"direction":90,
            "draggable":False,"rotationStyle":"all around",
        })

    targets[0]["broadcasts"] = {bid:name for name,bid in all_broadcasts.items()}

    # Extensions: aus imports + auto-detect pen
    extensions = list(ast.get("extensions", []))
    has_pen = any(any(b.get("opcode","").startswith("pen_")
                      for b in t["blocks"].values()) for t in targets)
    if has_pen and "pen" not in extensions:
        extensions.append("pen")

    return {"targets":targets,"monitors":[],"extensions":extensions,
            "meta":{"semver":"3.0.0","vm":"0.2.0","agent":"scratch-transpiler/4.0"}}


def write_sb3(project: dict, asset_mgr: AssetManager, path: str):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(project, indent=2, ensure_ascii=False))
        for filename, data in asset_mgr.all_files().items():
            zf.writestr(filename, data)
    print(f"  {len(asset_mgr.all_files())} Asset-Datei(en) eingepackt")


# ═══════════════════════════════════════════════════════
#  5.  VALIDATOR
# ═══════════════════════════════════════════════════════
class Validator:
    VALID_EFFECTS       = {"color","fisheye","whirl","pixelate","mosaic","brightness","ghost"}
    VALID_ROTATION      = {"all around","left-right","don't rotate"}
    VALID_STOP          = {"all","this script","other scripts in sprite"}
    VALID_DRAG          = {"draggable","not draggable"}

    def __init__(self, ast, library):
        self.ast = ast; self.library = library
        self.errors: list[str] = []; self.warnings: list[str] = []

    def validate(self) -> bool:
        sprite_names = {t["name"] for t in self.ast["targets"]}
        for target in self.ast["targets"]:
            ctx = f"{'Stage' if target['type']=='Stage' else 'Sprite'} '{target['name']}'"
            costume_names = {c["name"] for c in target.get("costumes",[])}
            sound_names   = {s["name"] for s in target.get("sounds",[])}
            for c in target.get("costumes",[]) + target.get("backdrops",[]):
                if not c.get("path") and self.library:
                    kind = "backdrops" if target["type"]=="Stage" else "costumes"
                    if c["name"].lower() not in self.library.get(kind,{}):
                        self.warnings.append(
                            f"{ctx}: Kostüm/Hintergrund '{c['name']}' nicht in Scratch-Bibliothek – Platzhalter.")
            for s in target.get("sounds",[]):
                if not s.get("path") and self.library:
                    if s["name"].lower() not in self.library.get("sounds",{}):
                        self.warnings.append(f"{ctx}: Sound '{s['name']}' nicht in Bibliothek – Stille.")
            for script in target.get("scripts",[]):
                self._stmts(script["body"], ctx, costume_names, sound_names, sprite_names, target)
            for cdef in target.get("customDefs",[]):
                self._stmts(cdef["body"], f"{ctx} define {cdef['name']}",
                            costume_names, sound_names, sprite_names, target)
        return len(self.errors) == 0

    def _stmts(self, stmts, ctx, cn, sn, sp, target):
        for s in stmts: self._stmt(s, ctx, cn, sn, sp, target)

    def _stmt(self, node, ctx, cn, sn, sp, target):
        t = node["type"]
        if t == "SwitchCostume" and cn and node["value"] not in cn:
            self.errors.append(f"{ctx}: switchCostume(\"{node['value']}\") – nicht definiert. Vorhanden: {sorted(cn)}")
        elif t in ("PlaySound","PlaySoundUntilDone") and sn and node["value"] not in sn:
            self.errors.append(f"{ctx}: playSound(\"{node['value']}\") – nicht definiert. Vorhanden: {sorted(sn)}")
        elif t in ("SetEffect","ChangeEffect") and node["effect"].lower() not in self.VALID_EFFECTS:
            self.errors.append(f"{ctx}: setEffect(\"{node['effect']}\") – ungültig. Gültig: {sorted(self.VALID_EFFECTS)}")
        elif t == "SetRotationStyle" and node["value"] not in self.VALID_ROTATION:
            self.errors.append(f"{ctx}: setRotationStyle(\"{node['value']}\") – Gültig: {sorted(self.VALID_ROTATION)}")
        elif t == "Stop" and node["option"] not in self.VALID_STOP:
            self.errors.append(f"{ctx}: stop(\"{node['option']}\") – Gültig: {sorted(self.VALID_STOP)}")
        elif t == "SetDragMode" and node["value"] not in self.VALID_DRAG:
            self.errors.append(f"{ctx}: setDragMode(\"{node['value']}\") – Gültig: {sorted(self.VALID_DRAG)}")
        elif t == "SetVolume": self._range(node["value"], ctx, "setVolume", 0, 100)
        elif t == "GoToSprite" and node["value"] not in ("_mouse_","_random_") and node["value"] not in sp:
            self.warnings.append(f"{ctx}: Sprite '{node['value']}' nicht definiert.")
        elif t == "CreateClone" and node["target"] != "_myself_" and node["target"] not in sp:
            self.errors.append(f"{ctx}: createClone(\"{node['target']}\") – Sprite nicht gefunden.")
        elif t == "CustomCall":
            defined = {cd["name"] for cd in target.get("customDefs",[])}
            if node["name"] not in defined:
                self.errors.append(f"{ctx}: {node['name']}() – nicht definiert. Definiert: {sorted(defined) or '(keine)'}")
            else:
                cdef = next(cd for cd in target["customDefs"] if cd["name"]==node["name"])
                if len(node["args"]) != len(cdef["params"]):
                    self.errors.append(f"{ctx}: {node['name']}() – {len(cdef['params'])} Arg(e) erwartet, {len(node['args'])} gegeben.")
        elif t == "Animate" and cn:
            for cname in node["costumes"]:
                if cname not in cn:
                    self.errors.append(f"{ctx}: animate() – Kostüm '{cname}' nicht definiert. Vorhanden: {sorted(cn)}")
        for sub in ("body","then","else"):
            if node.get(sub): self._stmts(node[sub], ctx, cn, sn, sp, target)

    def _range(self, expr, ctx, name, lo, hi):
        if expr and expr.get("type") == "Num":
            v = expr["value"]
            if lo is not None and v < lo: self.warnings.append(f"{ctx}: {name}({v}) unter Minimum ({lo}).")
            if hi is not None and v > hi: self.warnings.append(f"{ctx}: {name}({v}) über Maximum ({hi}).")

    def print_report(self):
        if not self.errors and not self.warnings:
            print("    ✓ Keine Probleme gefunden."); return
        for w in self.warnings: print(f"    ⚠  {w}")
        for e in self.errors:   print(f"    ✗  {e}")


# ═══════════════════════════════════════════════════════
#  6.  TURBOWARP LAUNCHER
# ═══════════════════════════════════════════════════════
def launch_turbowarp(sb3_path: str, replace: bool):
    sb3_abs = str(Path(sb3_path).resolve())
    system  = platform.system()
    if system == "Windows":
        candidates = [
            r"C:\Program Files\TurboWarp\TurboWarp.exe",
            r"C:\Program Files (x86)\TurboWarp\TurboWarp.exe",
            str(Path.home()/"AppData/Local/Programs/TurboWarp/TurboWarp.exe"),
            str(Path.home()/"AppData/Local/Programs/turbowarp-desktop/TurboWarp.exe"),
        ]
        kill_name = "TurboWarp.exe"
    elif system == "Darwin":
        candidates = [
            "/Applications/TurboWarp.app/Contents/MacOS/TurboWarp",
            str(Path.home()/"Applications/TurboWarp.app/Contents/MacOS/TurboWarp"),
        ]
        kill_name = "TurboWarp"
    else:
        candidates = [
            "/usr/bin/turbowarp-desktop","/usr/local/bin/turbowarp-desktop",
            str(Path.home()/".local/bin/turbowarp-desktop"),"/snap/bin/turbowarp-desktop",
        ]
        kill_name = "turbowarp-desktop"

    tw_exe = next((c for c in candidates if Path(c).exists()), None)
    if tw_exe is None:
        print("  ⚠  TurboWarp Desktop nicht gefunden.")
        print("     https://turbowarp.org/desktop")
        print(f"     Datei manuell öffnen: {sb3_abs}"); return

    if replace:
        print("  ⏹  Beende laufende TurboWarp-Instanzen...")
        if system == "Windows":
            subprocess.run(["taskkill","/F","/IM",kill_name], capture_output=True)
        else:
            subprocess.run(["pkill","-f",kill_name], capture_output=True)
        time.sleep(0.8)

    mode = "Ersetze" if replace else "Starte neue"
    print(f"  ▶  {mode} TurboWarp-Instanz: {Path(sb3_abs).name}")
    if system == "Windows":
        subprocess.Popen([tw_exe, sb3_abs])
    elif system == "Darwin":
        subprocess.Popen(["open","-n","-a","TurboWarp","--args",sb3_abs])
    else:
        subprocess.Popen([tw_exe, sb3_abs])


# ═══════════════════════════════════════════════════════
#  7.  KOMPILIER-PIPELINE
# ═══════════════════════════════════════════════════════
def compile_once(source: str, base_dir: Path, outfile: str,
                 asset_mgr: AssetManager, verbose=True) -> bool:
    """
    Führt eine vollständige Kompilierung durch.
    Gibt True zurück bei Erfolg, False bei Fehler.
    """
    try:
        if verbose: print("── [1] Tokenisierung & Parsing ────────────")
        tokens = tokenize(source)
        parser = Parser(tokens)
        ast    = parser.parse_program()
        if verbose:
            print(f"    {len(ast['targets'])} Target(s): "
                  + ", ".join(f"{t['type']} {t['name']}" for t in ast["targets"]))
            if ast.get("extensions"):
                print(f"    Extensions: {', '.join(ast['extensions'])}")
    except SyntaxError as e:
        print(f"\n  ✗  Syntaxfehler: {e}")
        print("     Prüfe Klammern, Semikolons, Anführungszeichen und Schlüsselwörter.")
        return False

    if verbose: print("── [2] Validierung ────────────────────────")
    validator = Validator(ast, AssetManager._library)
    ok = validator.validate()
    validator.print_report()
    if not ok:
        print("\n  ✗  Validierung fehlgeschlagen – Fehler oben beheben.")
        return False

    if verbose: print("── [3] Code-Generierung & Assets ──────────")
    project = build_project(ast, asset_mgr)
    total   = sum(len(t["blocks"]) for t in project["targets"])
    if verbose: print(f"    {total} Scratch-Blöcke")

    if verbose: print("── [4] Ausgabe ─────────────────────────────")
    json_path = Path(outfile).with_suffix(".json")
    json_path.write_text(json.dumps(project, indent=2, ensure_ascii=False), encoding="utf-8")
    if verbose: print(f"✓  {json_path}  ({json_path.stat().st_size:,} Bytes)")
    write_sb3(project, asset_mgr, outfile)
    if verbose: print(f"✓  {outfile}  ({Path(outfile).stat().st_size:,} Bytes)")
    return True


# ═══════════════════════════════════════════════════════
#  8.  WATCH-MODUS
# ═══════════════════════════════════════════════════════
def watch_mode(src_path: Path, outfile: str, tw_mode: str | None):
    """
    Beobachtet die Quelldatei und kompiliert bei jeder Änderung neu.
    tw_mode: None | "new" | "replace"
    """
    print(f"👁  Watch-Modus aktiv – beobachte: {src_path}")
    print("   Ctrl+C zum Beenden\n")

    last_mtime = None
    first_run  = True

    while True:
        try:
            mtime = src_path.stat().st_mtime
        except FileNotFoundError:
            print(f"  ⚠  Datei nicht gefunden: {src_path}")
            time.sleep(1); continue

        if mtime != last_mtime:
            last_mtime = mtime
            if not first_run:
                print(f"\n{'─'*45}")
                print(f"🔄  Änderung erkannt – {time.strftime('%H:%M:%S')}")
            first_run = False

            source    = src_path.read_text(encoding="utf-8")
            base_dir  = src_path.parent
            asset_mgr = AssetManager(base_dir)

            success = compile_once(source, base_dir, outfile, asset_mgr)

            if success and tw_mode:
                print("── [5] TurboWarp ───────────────────────────")
                launch_turbowarp(outfile, replace=(tw_mode=="replace"))

            print("\n   Warte auf Änderungen...")

        time.sleep(0.5)


# ═══════════════════════════════════════════════════════
#  9.  MAIN
# ═══════════════════════════════════════════════════════
def print_help():
    print("""
scratch_transpiler.py  v4.0
────────────────────────────────────────────────────────
VERWENDUNG:
  python scratch_transpiler.py <eingabe.java> [Optionen]

OPTIONEN:
  --out <datei.sb3>       Ausgabedatei (Standard: output.sb3)
  --watch                 Watch-Modus: kompiliert bei Dateiänderung neu
  --turbowarp-new         Startet TurboWarp Desktop nach Kompilierung
                          (bestehende Instanzen bleiben offen)
  --turbowarp-replace     Beendet laufende TurboWarp-Instanz und startet neu
  --help                  Diese Hilfe anzeigen

BEISPIELE:
  python scratch_transpiler.py spiel.java
  python scratch_transpiler.py spiel.java --out spiel.sb3 --watch --turbowarp-replace
  python scratch_transpiler.py spiel.java --turbowarp-new

Alle Infos zur Syntax: siehe README.md
""")

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args    = sys.argv[1:]
    infile  = None
    outfile = "output.sb3"
    tw_mode = None
    watch   = False

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--out" and i+1 < len(args):
            outfile = args[i+1]; i += 2
        elif a == "--turbowarp-new":
            tw_mode = "new"; i += 1
        elif a == "--turbowarp-replace":
            tw_mode = "replace"; i += 1
        elif a == "--watch":
            watch = True; i += 1
        elif a in ("--help", "-h"):
            print_help(); sys.exit(0)
        else:
            infile = a; i += 1

    if not infile:
        print("Fehler: Kein Eingabefile angegeben.")
        print_help(); sys.exit(1)

    src_path = Path(infile).resolve()
    if not src_path.exists():
        print(f"Fehler: Datei nicht gefunden: {src_path}"); sys.exit(1)

    # Watch-Modus
    if watch:
        try:
            watch_mode(src_path, outfile, tw_mode)
        except KeyboardInterrupt:
            print("\n👋  Watch-Modus beendet.")
        return

    # Einmaliger Lauf
    source    = src_path.read_text(encoding="utf-8")
    base_dir  = src_path.parent
    asset_mgr = AssetManager(base_dir)

    print(f"Lese: {src_path}")
    success = compile_once(source, base_dir, outfile, asset_mgr)
    if not success:
        sys.exit(1)

    if tw_mode:
        print("── [5] TurboWarp ───────────────────────────")
        launch_turbowarp(outfile, replace=(tw_mode=="replace"))

    print("\n── Fertig! ─────────────────────────────────")
    if not tw_mode:
        print(f"   Öffne {outfile} in TurboWarp oder Scratch.")


if __name__ == "__main__":
    main()
