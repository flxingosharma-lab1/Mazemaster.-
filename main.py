"""
☠ MAZEMASTER - Pydroid 3 (pygame) ke liye
=======================================
- Shop me 8 villain skins (6 se 30 star): inhe peeche wala bana sakte ho, aur Pacman game me
  khud villain ban sakte ho. Har item par Buy / Equip / Unequip button
- Full screen
- Home: NORMAL, HARDCORE (50 star), PACMAN (20 star) aur corner me SHOP button
- Normal: level select (jo khele wo dobara khel sakte ho, jo nahi khele wo lock)
- Har level par 3 star: har galti par 1 star kam (kam se kam 1 star milta hai)
- Har 4 ke table wale level: galti karne par Packman peeche dodta hai (jitni galti utna tez)
- Har 7 ke table wale level: star timer se milte hain (10s=3, 20s=2, 30s=1, 30s+ = 0)
- Galat deewar laal hokar vibrate karti hai
- Level khatam: maze ki photo + comment (Unstoppable / Excellence / Try next time) + awaaz
- Shop: star se path ka colour aur peeche dodne wala (ghost / Pac-Man) kharido aur equip karo
- Pacman game: 2 min ka timer, phir 20 sec ka event (Super Speed ya Star Rain)
- Hardcore: sirf 4 life, bahut bade mazes, life level ke beech carry hoti hai
- Har 5 level par maze ki shape badalti hai
- Level 15 ke baad har 3 ke table wale level par prank (portal / raasta band)
- Level, star, hint, shop, hardcore progress sab save hota hai
- Arrowverse (teer-puzzle section): bade picture wale teer-puzzle (Taj Mahal, Arc de Triomphe, Aquarius...) level 1 se hi,
  lobby screen (Daily Challenge, level patti, Continue), zoom + kheenchna, har level hal hone layak
- Roz subah 6 baje ek naya hint
"""
import array
import colorsys
import datetime
import json
import math
import os
import random
import sys
from collections import deque

import pygame

TOTAL_LEVELS = 10000
LEVELS_PER_SHAPE = 5
LEVEL_PAGE = 50          # level list 50-50 ke page me khulti hai
START_HINTS = 3
MAX_HINTS = 10           # jyada hint jama nahi honge
DAILY_HOUR = 6           # subah 6 baje
MAX_DROPS = 5            # normal mode ki boondh
HC_LIVES = 4             # hardcore ki life
HC_UNLOCK_STARS = 50
PRANK_AFTER = 15         # is level ke baad prank shuru
PRANK_EVERY = 3          # har 3 ke table par
CHASE_EVERY = 4          # har 4 ke table wale normal level par galti = Packman peeche dodta hai
TIMED_EVERY = 7          # har 7 ke table wale normal level par star timer se milte hain
PM_CHASE_BASE = 1.1      # Packman ki shuruaati speed (cell / second)
PM_CHASE_STEP = 0.8      # har galti par itni speed badhti hai
PM_UNLOCK_STARS = 20     # Pacman game 20 star par khud khulta hai
PM_PRICE = 30            # Pacman kharidne ke star
PM_ROUND_SEC = 120       # Pacman game ka timer: 2 minute
PM_EVENT_SEC = 20        # uske baad 20 second ka event
PM_N = 13                # Pacman arena ka size (13 x 13)
PM_RUN_SPEED = 4.2
PM_CHASER_SPEED = 3.1
PM_GHOST_SPEED = 2.7
PM_STAR_MAX = 6
PM_SPAWN_EVERY = 7.0

try:
    _base = os.environ.get("ANDROID_PRIVATE") or os.path.dirname(os.path.abspath(__file__))   # APK me app ka private folder
    SAVE_FILE = os.path.join(_base, "maze_save.json")
except NameError:
    SAVE_FILE = "maze_save.json"

try:
    pygame.mixer.pre_init(22050, -16, 1, 512)
except Exception:
    pass
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()
pygame.display.set_caption("☠️MazeMaster")
clock = pygame.time.Clock()

# ---------- colors ----------
BG = (245, 236, 210)
WALL = (70, 45, 30)
PATH = (40, 140, 220)
HINT = (250, 200, 60)
START = (60, 170, 80)
EXIT = (220, 60, 50)
GOLD = (190, 130, 20)
GOLD_STAR = (245, 185, 40)
STAR_OFF = (205, 190, 160)
DROP_ON = (40, 140, 220)
DROP_HC = (205, 70, 60)
DROP_OFF = (210, 195, 160)
BTN = (255, 250, 235)
PHOTO = (255, 252, 240)
PORTAL_A = (150, 70, 210)
PORTAL_B = (240, 140, 30)
PAC_YELLOW = (255, 214, 0)

# shop: (id, naam, rgb, price)   rgb None = special
COLOR_ITEMS = [
    ("blue", "Blue", (40, 140, 220), 0),
    ("green", "Green", (50, 170, 90), 5),
    ("pink", "Pink", (235, 100, 160), 5),
    ("orange", "Orange", (240, 140, 30), 8),
    ("purple", "Purple", (150, 80, 210), 8),
    ("red", "Red", (215, 60, 55), 10),
    ("black", "Black", (45, 45, 55), 10),
    ("rainbow", "Rainbow", None, 25),
]
FOLLOWER_ITEMS = [
    ("none", "Koi nahi", None, 0),
    ("ghost_red", "Red Ghost", (225, 55, 50), 10),
    ("ghost_blue", "Blue Ghost", (60, 160, 235), 10),
    ("ghost_pink", "Pink Ghost", (240, 130, 190), 10),
    ("pacman", "Pac-Man", PAC_YELLOW, PM_PRICE),
]

# ---------- villain skins (khud ke original pixel characters, 12 x 13 pixel) ----------
_FACE = [
    ".osssssssso.",
    ".osesssseso.",
    ".osssmmssso.",
]
_BODY = [
    "..obbbbbbo..",
    ".obbccccbbo.",
    ".osbbccbbso.",
    "..obbbbbbo..",
    "..oddooddo..",
    "..ooo..ooo..",
]
_BASE_PAL = {"o": (25, 18, 30), "w": (255, 255, 255), "m": (120, 30, 40), "r": (230, 60, 50)}

# id: (naam, price, head 4 rows, palette)
VILLAIN_DATA = [
    ("v_slime", "Slime King", 6,
     ["..a..aa..a..", "..aaaaaaaa..", ".oaaaaaaaao.", ".oaccaaccao."],
     {"s": (90, 200, 230), "a": (245, 200, 50), "b": (30, 60, 120), "c": (240, 250, 255),
      "d": (20, 40, 90), "e": (20, 30, 60)}),
    ("v_frost", "Frost Mage", 9,
     [".....aa.....", "....aaaa....", "...aaaaaa...", ".oaaaaaaaao."],
     {"s": (220, 235, 250), "a": (120, 190, 255), "b": (40, 70, 160), "c": (230, 245, 255),
      "d": (25, 40, 110), "e": (30, 60, 140)}),
    ("v_bat", "Shadow Bat", 12,
     [".aa......aa.", ".aaa....aaa.", ".oaaaaaaaao.", ".oaaaaaaaao."],
     {"s": (205, 195, 215), "a": (70, 45, 100), "b": (50, 38, 80), "c": (240, 205, 60),
      "d": (35, 28, 60), "e": (200, 40, 60)}),
    ("v_rust", "Rust Bot", 15,
     ["......r.....", "......c.....", ".oaaaaaaaao.", ".oaaaaaaaao."],
     {"s": (190, 120, 60), "a": (150, 152, 165), "b": (105, 108, 122), "c": (220, 220, 230),
      "d": (70, 72, 85), "e": (30, 30, 40)}),
    ("v_imp", "Lava Imp", 18,
     ["..w......w..", "..ww....ww..", ".oaaaaaaaao.", ".oaaaaaaaao."],
     {"s": (240, 95, 50), "a": (125, 25, 25), "b": (70, 25, 25), "c": (255, 175, 40),
      "d": (45, 15, 15), "e": (255, 235, 90)}),
    ("v_clown", "Candy Clown", 21,
     [".aa......cc.", ".aaa.aa.ccc.", ".oaaaaccccco", ".oaaaaccccco"],
     {"s": (250, 245, 240), "a": (245, 110, 170), "b": (150, 60, 200), "c": (80, 215, 240),
      "d": (250, 215, 60), "e": (30, 30, 50)}),
    ("v_bandit", "Desert Bandit", 25,
     ["....aaaa....", "...aaaaaa...", ".oaaaaaaaao.", ".oaccccccao."],
     {"s": (205, 150, 100), "a": (225, 195, 125), "b": (150, 100, 50), "c": (170, 120, 60),
      "d": (90, 60, 30), "e": (30, 20, 15)}),
    ("v_ninja", "Cyber Ninja", 30,
     ["............", "...aaaaaa...", ".oaaaaaaaao.", ".oaaaaaaaao."],
     {"s": (30, 30, 42), "a": (22, 22, 32), "b": (32, 32, 48), "c": (0, 230, 160),
      "d": (18, 18, 28), "e": (0, 255, 210)}),
]
VILLAIN_ART = {}
for _vid, _name, _price, _head, _pal in VILLAIN_DATA:
    _p = dict(_BASE_PAL)
    _p.update(_pal)
    VILLAIN_ART[_vid] = (_head + _FACE + _BODY, _p)
    FOLLOWER_ITEMS.append((_vid, _name, _p["a"], _price))
HUNTERS = ["pacman"] + [v[0] for v in VILLAIN_DATA]     # inme se koi equip ho to Pacman game me tum shikari ho
COLOR_MAP = {i[0]: i[2] for i in COLOR_ITEMS if i[2]}
GHOST_COL = {i[0]: i[2] for i in FOLLOWER_ITEMS if i[0].startswith("ghost_")}

unit = min(W, H)
font_title = pygame.font.Font(None, int(unit * 0.16))
font_logo = pygame.font.Font(None, int(unit * 0.12))
font_big = pygame.font.Font(None, int(unit * 0.07))
font_mid = pygame.font.Font(None, int(unit * 0.05))
font_small = pygame.font.Font(None, int(unit * 0.036))

# ---------- layout ----------
TOP_H = int(H * 0.12)
BOT_H = int(H * 0.16)
MARGIN = int(W * 0.04)
AREA = pygame.Rect(MARGIN, TOP_H, W - 2 * MARGIN, H - TOP_H - BOT_H)
BTN_R = int(unit * 0.07)
RESTART_BTN = (int(W * 0.30), H - BOT_H // 2)
HINT_BTN = (int(W * 0.70), H - BOT_H // 2)
BACK_BTN = (int(W * 0.08), TOP_H // 2)
SOUND_R = int(BTN_R * 0.75)
SOUND_BTN = (int(W * 0.92), TOP_H // 2)

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


# ======================================================================
#  SHAPES  (x, y  -1 se 1 ke beech; y neeche ki taraf badhta hai)
# ======================================================================
def _poly(points):
    def inside(x, y):
        res = False
        j = len(points) - 1
        for i in range(len(points)):
            xi, yi = points[i]
            xj, yj = points[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
                res = not res
            j = i
        return res
    return inside


def _star(x, y):
    pts = []
    for i in range(10):
        a = math.radians(-90 + 36 * i)
        r = 1.0 if i % 2 == 0 else 0.5
        pts.append((r * math.cos(a), r * math.sin(a)))
    return _poly(pts)(x, y)


def _heart(x, y):
    u = x * 1.2
    v = -y * 1.25 + 0.15
    return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0


_hexagon = _poly([(math.cos(math.radians(60 * i)), math.sin(math.radians(60 * i))) for i in range(6)])
_triangle = _poly([(0, -1), (1, 1), (-1, 1)])
_house = _poly([(-0.9, -0.1), (0, -1), (0.9, -0.1), (0.9, 1), (-0.9, 1)])
_arrow = _poly([(0, -1), (0.95, -0.1), (0.4, -0.1), (0.4, 1), (-0.4, 1), (-0.4, -0.1), (-0.95, -0.1)])
_tshape = _poly([(-1, -1), (1, -1), (1, -0.4), (0.38, -0.4), (0.38, 1), (-0.38, 1), (-0.38, -0.4), (-1, -0.4)])
_fish_tail = _poly([(0.5, 0), (1, -0.55), (1, 0.55)])

SHAPES = [
    ("Circle", lambda x, y: x * x + y * y <= 1),
    ("Heart", _heart),
    ("Diamond", lambda x, y: abs(x) + abs(y) <= 1),
    ("Star", _star),
    ("Triangle", _triangle),
    ("Plus", lambda x, y: abs(x) <= 0.38 or abs(y) <= 0.38),
    ("Ring", lambda x, y: 0.4 <= math.hypot(x, y) <= 1),
    ("Arrow", _arrow),
    ("House", _house),
    ("Hexagon", _hexagon),
    ("Fish", lambda x, y: ((x + 0.15) / 0.75) ** 2 + (y / 0.55) ** 2 <= 1 or _fish_tail(x, y)),
    ("Moon", lambda x, y: x * x + y * y <= 1 and (x - 0.45) ** 2 + (y + 0.1) ** 2 > 0.75 ** 2),
    ("T Shape", _tshape),
    ("Mushroom", lambda x, y: (y <= 0.1 and x * x + (y - 0.1) ** 2 <= 1) or (abs(x) <= 0.35 and 0 <= y <= 1)),
]


def shape_for_level(level):
    """Return (name, func, flipx, flipy). Har 5 level par naya shape."""
    block = (level - 1) // LEVELS_PER_SHAPE
    if block == 0:
        return "Square", (lambda x, y: True), False, False
    idx = (block - 1) % len(SHAPES)
    cycle = (block - 1) // len(SHAPES)
    name, func = SHAPES[idx]
    return name, func, bool(cycle & 1), bool((cycle >> 1) & 1)


# ======================================================================
#  SOUND  (khud banai hui awaazein, koi file nahi chahiye)
# ======================================================================
class Sfx:
    RATE = 22050

    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.steps = []
        self.channels = 1
        self._voice_cache = {}
        self._init_tts()
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            freq, fmt, ch = pygame.mixer.get_init()
            if fmt != -16:
                return
            self.RATE = freq
            self.channels = ch
            t = self._tone
            s = self._seq
            self.steps = [self._make(t(420 + i * 35, 0.05, 0.25)) for i in range(12)]
            self.sounds = {
                "hit": self._make(t(110, 0.18, 0.5, "square")),
                "win": self._make(s(t(523, 0.1), t(659, 0.1), t(784, 0.1), t(1047, 0.28))),
                "lose": self._make(s(t(392, 0.15), t(330, 0.15), t(262, 0.3))),
                "hint": self._make(s(t(880, 0.08), t(1320, 0.2, 0.35))),
                "daily": self._make(s(t(659, 0.1), t(880, 0.1), t(1175, 0.22))),
                "click": self._make(t(600, 0.03, 0.3)),
                "star": self._make(t(1100, 0.14, 0.35)),
                "portal": self._make(s(t(400, 0.06), t(550, 0.06), t(750, 0.06), t(1000, 0.14))),
                "prank": self._make(s(t(300, 0.1, 0.4, "square"), t(200, 0.12, 0.4, "square"), t(500, 0.15))),
                "chomp": self._make(s(t(300, 0.06, 0.3, "square"), t(220, 0.06, 0.3, "square"))),
                "caught": self._make(s(t(500, 0.08, 0.4, "square"), t(400, 0.08, 0.4, "square"),
                                       t(300, 0.1, 0.4, "square"), t(180, 0.3, 0.45, "square"))),
                "event": self._make(s(t(440, 0.08), t(660, 0.08), t(880, 0.08), t(1320, 0.25, 0.4))),
                "buy": self._make(s(t(988, 0.07, 0.35), t(1319, 0.2, 0.35))),
                "ghost": self._make(s(t(300, 0.06, 0.35), t(600, 0.06, 0.35), t(900, 0.1, 0.35))),
            }
            self.ok = True
            try:
                for w in ("Unstoppable", "Excellence", "Try next time"):
                    self._robot(w)
            except Exception:
                pass
        except Exception:
            self.ok = False

    def _tone(self, freq, dur, vol=0.4, kind="sine"):
        n = int(self.RATE * dur)
        out = []
        atk = max(1, int(self.RATE * 0.005))
        for i in range(n):
            env = min(1.0, i / atk) * (1 - i / n) ** 1.5
            s = math.sin(2 * math.pi * freq * i / self.RATE)
            if kind == "square":
                s = 0.5 if s >= 0 else -0.5
            out.append(int(32767 * vol * env * s))
        return out

    @staticmethod
    def _seq(*parts):
        out = []
        for p in parts:
            out.extend(p)
        return out

    def _make(self, samples):
        if self.channels == 2:
            dbl = []
            for s in samples:
                dbl.append(s)
                dbl.append(s)
            samples = dbl
        return pygame.mixer.Sound(buffer=array.array("h", samples).tobytes())

    def play(self, name, enabled=True):
        if not (self.ok and enabled):
            return
        try:
            self.sounds[name].play()
        except Exception:
            pass

    def step(self, n, enabled=True):
        if not (self.ok and enabled):
            return
        try:
            self.steps[n % len(self.steps)].play()
        except Exception:
            pass


    # ---------- bolna (text-to-speech) ----------
    _VOWELS = {"a": (730, 1090), "e": (530, 1840), "i": (270, 2290),
               "o": (570, 840), "u": (300, 870), "y": (300, 2100)}
    _HISS = set("sfhckptxqz")

    def _init_tts(self):
        """Pehle phone ki asli awaaz (Android TTS), phir pyttsx3, nahi to robot awaaz."""
        self.tts = None
        self.tts_kind = None
        self.tts_lang = False
        try:
            from jnius import autoclass
            app = autoclass("android.app.ActivityThread").currentApplication()
            tts_cls = autoclass("android.speech.tts.TextToSpeech")
            self.tts = tts_cls(app.getApplicationContext(), None)
            self.tts_kind = "android"
            return
        except Exception:
            self.tts = None
        try:
            import pyttsx3  # noqa: F401
            self.tts_kind = "pyttsx3"
        except Exception:
            self.tts_kind = None

    def _robot(self, text):
        """Agar asli TTS na ho to khud ki banayi robot awaaz (vowel formants)."""
        key = text.lower()
        if key in self._voice_cache:
            return self._voice_cache[key]
        rate = self.RATE
        two_pi = 2 * math.pi
        period = 1.0 / 125.0
        out = []
        for ch in key:
            if ch in self._VOWELS:
                f1, f2 = self._VOWELS[ch]
                n = int(rate * 0.15)
                for i in range(n):
                    tau = (i / rate) % period
                    env = min(1.0, i / (rate * 0.012)) * min(1.0, (n - i) / (rate * 0.04))
                    v = (math.sin(two_pi * f1 * tau) * math.exp(-260 * tau)
                         + 0.7 * math.sin(two_pi * f2 * tau) * math.exp(-420 * tau))
                    out.append(int(32767 * 0.9 * env * v))
            elif ch.isalpha():
                n = int(rate * 0.07)
                prev = 0.0
                for i in range(n):
                    env = min(1.0, i / (rate * 0.008)) * min(1.0, (n - i) / (rate * 0.02))
                    if ch in self._HISS:
                        x = random.uniform(-1, 1)
                        v = (x - prev) * 0.35
                        prev = x
                    else:
                        v = 0.5 * math.sin(two_pi * 170 * i / rate)
                    out.append(int(32767 * 0.5 * env * v))
            else:
                out.extend([0] * int(rate * 0.09))
        if not out:
            return None
        out = [max(-32767, min(32767, s)) for s in out]
        snd = self._make(out)
        self._voice_cache[key] = snd
        return snd

    def speak(self, text, enabled=True):
        if not enabled:
            return
        said = text.rstrip("!. ")
        spoken = False
        try:
            if self.tts_kind == "android" and self.tts is not None:
                from jnius import autoclass
                if not self.tts_lang:
                    res = self.tts.setLanguage(autoclass("java.util.Locale").US)
                    self.tts_lang = res >= 0
                spoken = self.tts.speak(said, 0, None, "maze") == 0
            elif self.tts_kind == "pyttsx3":
                import threading
                import pyttsx3

                def run():
                    try:
                        eng = pyttsx3.init()
                        eng.say(said)
                        eng.runAndWait()
                    except Exception:
                        pass
                threading.Thread(target=run, daemon=True).start()
                spoken = True
        except Exception:
            spoken = False
        if not spoken and self.ok:
            try:
                snd = self._robot(said)
                if snd:
                    snd.play()
            except Exception:
                pass


# ======================================================================
#  SAVE / DAILY HINT
# ======================================================================
def day_token(now=None):
    """Din subah 6 baje badalta hai."""
    now = now or datetime.datetime.now()
    shifted = now - datetime.timedelta(hours=DAILY_HOUR)
    return shifted.date().toordinal()


class Save:
    def __init__(self):
        self.level = 1               # normal mode ka sabse aage ka khula level
        self.hints = START_HINTS
        self.last_day = day_token()
        self.sound = True
        self.stars = {}              # level -> best star (0..3)
        self.hc_level = 1            # hardcore run ka current level
        self.hc_lives = HC_LIVES     # hardcore run ki bachi life
        self.hc_best = 0             # hardcore me sabse jyada cleared level
        self.last_cleared = 0
        self.bonus = 0               # Pacman game se mile star
        self.spent = 0               # shop me kharch hue star
        self.color = "blue"          # equip kiya hua path colour
        self.follower = "none"       # equip kiya hua peeche dodne wala
        self.owned = {"color": {"blue"}, "follower": {"none"}}
        self.pm_best = 0             # Pacman game me ek round ke sabse jyada star
        self.ar_level = 1            # Arrowverse ka sabse aage ka khula level
        self.ar_streak = 0           # Arrowverse: lagatar jeet (lobby me 'x Win')
        self.ar_daily = 0            # jis din ka Daily Challenge inaam le liya
        self.load()
        self.check_daily()

    def total_stars(self):
        """Ab tak kamaye hue star (unlock ke liye). Kharch karne se ye kam nahi hote."""
        return sum(self.stars.values()) + self.bonus

    def balance(self):
        """Shop me kharch karne layak star."""
        return max(0, self.total_stars() - self.spent)

    def hc_unlocked(self):
        return self.total_stars() >= HC_UNLOCK_STARS

    def pm_unlocked(self):
        return self.total_stars() >= PM_UNLOCK_STARS

    # ---- shop ----
    def owns(self, kind, item):
        return item in self.owned[kind]

    def buy(self, kind, item, price):
        if self.owns(kind, item):
            return True
        if self.balance() < price:
            return False
        self.spent += price
        self.owned[kind].add(item)
        self.write()
        return True

    def equip(self, kind, item):
        if not self.owns(kind, item):
            return
        if kind == "color":
            self.color = item
        else:
            self.follower = item
        self.write()

    def load(self):
        try:
            with open(SAVE_FILE, "r") as f:
                d = json.load(f)
            self.level = min(TOTAL_LEVELS, max(1, int(d.get("level", 1))))
            self.hints = max(0, int(d.get("hints", START_HINTS)))
            self.last_day = int(d.get("last_day", day_token()))
            self.sound = bool(d.get("sound", True))
            self.stars = {int(k): max(0, min(3, int(v))) for k, v in d.get("stars", {}).items()}
            self.hc_level = max(1, int(d.get("hc_level", 1)))
            self.hc_lives = int(d.get("hc_lives", HC_LIVES))
            if self.hc_lives <= 0 or self.hc_lives > HC_LIVES:
                self.hc_lives = HC_LIVES
            self.hc_best = max(0, int(d.get("hc_best", 0)))
            self.bonus = max(0, int(d.get("bonus", 0)))
            self.spent = max(0, int(d.get("spent", 0)))
            self.pm_best = max(0, int(d.get("pm_best", 0)))
            self.ar_level = max(1, int(d.get("ar_level", 1)))
            self.ar_streak = max(0, int(d.get("ar_streak", 0)))
            self.ar_daily = max(0, int(d.get("ar_daily", 0)))
            self.owned = {
                "color": set(d.get("owned_color", [])) | {"blue"},
                "follower": set(d.get("owned_follower", [])) | {"none"},
            }
            self.color = d.get("color", "blue")
            self.follower = d.get("follower", "none")
            if self.color not in self.owned["color"]:
                self.color = "blue"
            if self.follower not in self.owned["follower"]:
                self.follower = "none"
        except Exception:
            pass  # pehli baar ya file kharab: default

    def write(self):
        try:
            tmp = SAVE_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump({
                    "level": self.level, "hints": self.hints, "last_day": self.last_day,
                    "sound": self.sound, "stars": {str(k): v for k, v in self.stars.items()},
                    "hc_level": self.hc_level, "hc_lives": self.hc_lives, "hc_best": self.hc_best,
                    "bonus": self.bonus, "spent": self.spent, "pm_best": self.pm_best, "ar_level": self.ar_level,
                    "ar_streak": self.ar_streak, "ar_daily": self.ar_daily,
                    "color": self.color, "follower": self.follower,
                    "owned_color": sorted(self.owned["color"]),
                    "owned_follower": sorted(self.owned["follower"]),
                }, f)
            os.replace(tmp, SAVE_FILE)
        except Exception:
            pass

    def check_daily(self):
        """Har subah 6 baje ka ek hint; game band tha tab ke din bhi gine jayenge."""
        today = day_token()
        if today > self.last_day:
            if self.hints < MAX_HINTS:
                self.hints = min(MAX_HINTS, self.hints + (today - self.last_day))
            self.last_day = today
            self.write()
            return True
        if today < self.last_day:  # phone ka time peeche kiya gaya
            self.last_day = today
            self.write()
        return False


# ======================================================================
#  MAZE
# ======================================================================
def edge_line(a, b):
    """Do padosi cells ke beech ki deewar ki line (grid units me)."""
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        c = max(c1, c2)
        return (c, r1, c, r1 + 1)
    r = max(r1, r2)
    return (c1, r, c1 + 1, r)


class Maze:
    def __init__(self, level, hardcore=False):
        self.level = level
        self.hardcore = hardcore
        if hardcore:
            self.shape_name, func, flipx, flipy = shape_for_level(level + LEVELS_PER_SHAPE)
            n = min(14 + level // 2, 30)          # bahut bade mazes
            seed = level * 104729 + 77
        else:
            self.shape_name, func, flipx, flipy = shape_for_level(level)
            n = min(7 + level // 40, 24)
            if self.shape_name != "Square":
                n = max(n, 11)
            seed = level * 7919 + 13
        self.n = n
        self.cs = min(AREA.width, AREA.height) // n
        self.ox = AREA.x + (AREA.width - n * self.cs) // 2
        self.oy = AREA.y + (AREA.height - n * self.cs) // 2

        self.cells = self._build_mask(func, flipx, flipy)
        rng = random.Random(seed)                  # har level ka maze hamesha same
        self.base_open = self._generate(self.cells, rng)
        self.open = {k: set(v) for k, v in self.base_open.items()}
        a = self._farthest(min(self.cells))
        b = self._farthest(a)
        self.start, self.exit = (a, b) if a <= b else (b, a)

        self.portal = None
        self.block = None
        self._setup_prank(random.Random(seed + 5))

        self.drops = HC_LIVES if hardcore else MAX_DROPS
        self.mistakes = 0
        self._wall_cache = None
        self.chase = (not hardcore) and level % CHASE_EVERY == 0     # galti = Packman
        self.timed = (not hardcore) and level % TIMED_EVERY == 0     # star timer se
        self.col_id = "blue"
        self.fol_id = "none"
        self.reset()

    def reset(self, keep_lives=False):
        self.open = {k: set(v) for k, v in self.base_open.items()}
        self.segs = self._wall_segments()
        self._wall_cache = None
        self.path = [self.start]
        if not keep_lives:
            self.drops = HC_LIVES if self.hardcore else MAX_DROPS
            self.mistakes = 0
        self.hint_cells = []
        self.hint_until = 0
        self.blocked_cell = None
        self.prank_done = False
        self.fx = []
        self.shakes = []          # galat deewarein: (a, b, kab_tak)
        self.pm = None            # peeche dodta Packman
        self.alert_until = 0
        self.fol_pos = 0.0
        self.elapsed = 0.0
        self.started = False

    # ---- construction ----
    def _build_mask(self, func, flipx, flipy):
        n = self.n
        inside = set()
        for r in range(n):
            for c in range(n):
                x = (c + 0.5) / n * 2 - 1
                y = (r + 0.5) / n * 2 - 1
                if flipx:
                    x = -x
                if flipy:
                    y = -y
                if func(x, y):
                    inside.add((r, c))
        # sabse bada juda hua hissa rakho
        best = set()
        left = set(inside)
        while left:
            seed = min(left)
            comp = {seed}
            q = deque([seed])
            while q:
                r, c = q.popleft()
                for dr, dc in DIRS:
                    nb = (r + dr, c + dc)
                    if nb in left and nb not in comp:
                        comp.add(nb)
                        q.append(nb)
            left -= comp
            if len(comp) > len(best):
                best = comp
        if len(best) < n * n * 0.2:
            best = {(r, c) for r in range(n) for c in range(n)}
        return best

    def _generate(self, mask, rng):
        op = {cell: set() for cell in mask}
        first = min(mask)
        seen = {first}
        stack = [first]
        while stack:
            r, c = stack[-1]
            nb = [(r + dr, c + dc) for dr, dc in DIRS
                  if (r + dr, c + dc) in mask and (r + dr, c + dc) not in seen]
            if nb:
                nx = rng.choice(nb)
                op[(r, c)].add(nx)
                op[nx].add((r, c))
                seen.add(nx)
                stack.append(nx)
            else:
                stack.pop()
        return op

    def _farthest(self, src):
        dist = {src: 0}
        q = deque([src])
        last = src
        while q:
            cur = q.popleft()
            last = cur
            for nb in self.open[cur]:
                if nb not in dist:
                    dist[nb] = dist[cur] + 1
                    q.append(nb)
        return last

    def _bfs(self, src, dst):
        prev = {src: None}
        q = deque([src])
        while q:
            cur = q.popleft()
            if cur == dst:
                break
            for nb in self.open[cur]:
                if nb not in prev:
                    prev[nb] = cur
                    q.append(nb)
        if dst not in prev:
            return []
        out = []
        cur = dst
        while cur is not None:
            out.append(cur)
            cur = prev[cur]
        return out[::-1]

    def _component(self, src, banned):
        """src se wo cells jo banned edge ke bina jude hain."""
        x, y = banned
        seen = {src}
        q = deque([src])
        while q:
            cur = q.popleft()
            for nb in self.base_open[cur]:
                if nb in seen:
                    continue
                if (cur == x and nb == y) or (cur == y and nb == x):
                    continue
                seen.add(nb)
                q.append(nb)
        return seen

    def _setup_prank(self, rng):
        """Level 15 ke baad har 3 ke table par: portal ya band hota raasta."""
        if self.hardcore or self.level <= PRANK_AFTER or self.level % PRANK_EVERY:
            return
        sol = self._bfs(self.start, self.exit)
        length = len(sol)
        if length < 10:
            return
        if (self.level // PRANK_EVERY) % 2 == 1:
            center = length // 2
            for k in sorted(range(2, length - 3), key=lambda i: abs(i - center)):
                edge = (sol[k], sol[k + 1])
                comp_a = self._component(self.start, edge)
                pairs = []
                for u in comp_a:
                    for dr, dc in DIRS:
                        v = (u[0] + dr, u[1] + dc)
                        if v in self.cells and v not in comp_a and v not in self.base_open[u]:
                            pairs.append((u, v))
                pairs = [p for p in pairs if p[0] != sol[k]] or pairs
                if pairs:
                    self.block = {"edge": edge, "trigger": sol[k], "open": rng.choice(sorted(pairs))}
                    return
        # portal (ya block na ban paya to bhi portal)
        self.portal = (sol[int(length * 0.25)], sol[int(length * 0.7)])

    def _wall_segments(self):
        segs = set()
        for (r, c) in self.cells:
            op = self.open[(r, c)]
            if (r + 1, c) not in op:
                segs.add((c, r + 1, c + 1, r + 1))
            if (r - 1, c) not in op:
                segs.add((c, r, c + 1, r))
            if (r, c + 1) not in op:
                segs.add((c + 1, r, c + 1, r + 1))
            if (r, c - 1) not in op:
                segs.add((c, r, c, r + 1))
        return list(segs)

    # ---- helpers ----
    def center(self, cell):
        r, c = cell
        return (self.ox + c * self.cs + self.cs // 2, self.oy + r * self.cs + self.cs // 2)

    def cell_at(self, pos):
        x, y = pos
        c = (x - self.ox) // self.cs
        r = (y - self.oy) // self.cs
        cell = (int(r), int(c))
        return cell if cell in self.cells else None

    # ---- drawing ----
    def _wall_thickness(self, cs):
        return max(2, cs // 9)

    def _draw_walls(self, surf, ox, oy, cs):
        t = self._wall_thickness(cs)
        for gx0, gy0, gx1, gy1 in self.segs:
            p1 = (ox + gx0 * cs, oy + gy0 * cs)
            p2 = (ox + gx1 * cs, oy + gy1 * cs)
            pygame.draw.line(surf, WALL, p1, p2, t)
            pygame.draw.circle(surf, WALL, p1, t // 2)
            pygame.draw.circle(surf, WALL, p2, t // 2)

    def draw_to(self, surf, ox, oy, cs, now, live=True):
        def ctr(cell):
            return (ox + cell[1] * cs + cs // 2, oy + cell[0] * cs + cs // 2)

        if live and now < self.hint_until:
            for cell in self.hint_cells:
                pygame.draw.circle(surf, HINT, ctr(cell), max(3, cs // 4))

        # portal
        if self.portal:
            pulse = (now // 90) % 6 if live else 0
            for cell, col in zip(self.portal, (PORTAL_A, PORTAL_B)):
                p = ctr(cell)
                pygame.draw.circle(surf, col, p, int(cs * 0.42) + pulse // 2)
                pygame.draw.circle(surf, BG, p, int(cs * 0.28))
                pygame.draw.circle(surf, col, p, int(cs * 0.16))

        # path (teleport wali jagah line nahi) - shop se kharida hua colour
        w = max(4, cs // 3)
        colfn = self._path_color_fn(now)
        for i in range(len(self.path) - 1):
            a, b = self.path[i], self.path[i + 1]
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1:
                pygame.draw.line(surf, colfn(i), ctr(a), ctr(b), w)
        for i, cell in enumerate(self.path):
            pygame.draw.circle(surf, colfn(i), ctr(cell), w // 2)
        pygame.draw.circle(surf, START, ctr(self.start), max(5, cs // 3), 0)
        pygame.draw.circle(surf, EXIT, ctr(self.exit), max(5, cs // 3), 0)

        # deewarein
        if live and cs == self.cs:
            if self._wall_cache is None:
                t = self._wall_thickness(cs)
                off = t + 2
                size = self.n * cs + 2 * off
                cache = pygame.Surface((size, size), pygame.SRCALPHA)
                self._draw_walls(cache, off, off, cs)
                self._wall_cache = (cache, off)
            cache, off = self._wall_cache
            surf.blit(cache, (ox - off, oy - off))
        else:
            self._draw_walls(surf, ox, oy, cs)

        # prank effect: band hui deewar laal, khuli hui jagah hari
        if live:
            for a, b, kind, until in self.fx:
                if now < until:
                    gx0, gy0, gx1, gy1 = edge_line(a, b)
                    col = (220, 50, 40) if kind == "close" else (50, 190, 80)
                    thick = self._wall_thickness(cs) + 4 + (now // 120) % 3
                    pygame.draw.line(surf, col, (ox + gx0 * cs, oy + gy0 * cs),
                                     (ox + gx1 * cs, oy + gy1 * cs), thick)

    def _path_color_fn(self, now):
        if self.col_id == "rainbow":
            def fn(i):
                r, g, b = colorsys.hsv_to_rgb((i * 0.035 + now / 1800.0) % 1.0, 0.75, 0.95)
                return (int(r * 255), int(g * 255), int(b * 255))
            return fn
        col = COLOR_MAP.get(self.col_id, PATH)
        return lambda i: col

    def draw(self, now):
        self.draw_to(screen, self.ox, self.oy, self.cs, now, True)
        self._draw_extras(screen, now)

    def _draw_extras(self, surf, now):
        """Galat deewar (laal + vibrate), peeche wala follower aur Packman."""
        ox, oy, cs = self.ox, self.oy, self.cs
        self.shakes = [s for s in self.shakes if now < s[2]]
        t = self._wall_thickness(cs) + 3
        for a, b, until in self.shakes:
            gx0, gy0, gx1, gy1 = edge_line(a, b)
            left = max(0.0, (until - now) / 1200.0)
            amp = cs * 0.09 * (0.35 + 0.65 * left)
            dx = math.sin(now / 16.0) * amp
            dy = math.cos(now / 21.0) * amp
            p1 = (int(ox + gx0 * cs + dx), int(oy + gy0 * cs + dy))
            p2 = (int(ox + gx1 * cs + dx), int(oy + gy1 * cs + dy))
            col = (235, 35, 30) if (now // 90) % 2 == 0 else (255, 95, 70)
            pygame.draw.line(surf, col, p1, p2, t)
            pygame.draw.circle(surf, col, p1, t // 2)
            pygame.draw.circle(surf, col, p2, t // 2)

        # cosmetic follower (shop se kharida) - Packman chase me hide
        if self.fol_id != "none" and self.pm is None:
            gx, gy, ang = self.path_point(self.fol_pos)
            c = (int(ox + gx * cs), int(oy + gy * cs))
            if self.fol_id == "pacman":
                draw_pacman(surf, c, cs * 0.36, ang, abs(math.sin(now / 110.0)), PAC_YELLOW)
            elif self.fol_id in GHOST_COL:
                draw_ghost(surf, c, cs * 0.34, GHOST_COL[self.fol_id], now)
            elif self.fol_id in VILLAIN_ART:
                bob = int(math.sin(now / 160.0) * cs * 0.04)
                draw_villain(surf, (c[0], c[1] + bob), cs * 0.95, self.fol_id, math.cos(ang) < -0.3)

        # peeche dodta Packman
        if self.pm is not None:
            gx, gy, ang = self.path_point(self.pm["pos"])
            c = (int(ox + gx * cs), int(oy + gy * cs))
            if not (self.pm["wait"] > 0 and (now // 120) % 2):
                if self.fol_id in VILLAIN_ART:        # jo skin equip hai wahi marne aata hai
                    bob = int(math.sin(now / 90.0) * cs * 0.05)
                    draw_villain(surf, (c[0], c[1] + bob), cs * 1.15, self.fol_id, math.cos(ang) < -0.3)
                elif self.fol_id in GHOST_COL:
                    draw_ghost(surf, c, cs * 0.45, GHOST_COL[self.fol_id], now)
                else:
                    draw_pacman(surf, c, cs * 0.45, ang, abs(math.sin(now / 90.0)), PAC_YELLOW)

    def render_thumbnail(self):
        """Level khatam hone par dikhne wali maze ki photo."""
        pad = int(self.cs * 0.7)
        size = self.n * self.cs + 2 * pad
        surf = pygame.Surface((size, size))
        surf.fill(PHOTO)
        self.draw_to(surf, pad, pad, self.cs, 0, False)
        return surf

    # ---- gameplay ----
    def try_step(self, cell, now):
        """Return 'ok', 'hit', 'win', 'lose', 'portal', 'prank' ya None."""
        head = self.path[-1]
        if cell == head:
            return None
        if len(self.path) >= 2 and cell == self.path[-2]:
            self.path.pop()
            self.blocked_cell = None
            return "ok"
        if abs(cell[0] - head[0]) + abs(cell[1] - head[1]) != 1:
            return None
        if cell in self.path:
            return None
        if cell in self.open[head]:
            self.path.append(cell)
            self.started = True
            self.blocked_cell = None
            if cell == self.exit:
                return "win"
            if self.portal and cell == self.portal[0] and self.portal[1] not in self.path:
                self.path.append(self.portal[1])
                return "portal"
            if self.block and not self.prank_done and cell == self.block["trigger"]:
                self._fire_block(now)
                return "prank"
            return "ok"
        if self.blocked_cell != cell:   # ek hi deewar par baar-baar galti nahi gini jayegi
            self.blocked_cell = cell
            self.drops -= 1
            self.mistakes += 1
            self.shakes.append((head, cell, now + 1200))     # wo deewar laal + vibrate
            self.shakes = self.shakes[-6:]
            if self.chase and self.pm is None:
                self._spawn_pm(now)
            return "lose" if self.drops <= 0 else "hit"
        return None

    def _fire_block(self, now):
        a, b = self.block["edge"]
        self.open[a].discard(b)
        self.open[b].discard(a)
        u, v = self.block["open"]
        self.open[u].add(v)
        self.open[v].add(u)
        self.prank_done = True
        self.segs = self._wall_segments()
        self._wall_cache = None
        self.fx = [(a, b, "close", now + 3000), (u, v, "open", now + 3000)]

    # ---- Packman (har 4 ke table wale level) + timer + follower ----
    def _spawn_pm(self, now):
        head = len(self.path) - 1
        self.pm = {"pos": max(0.0, head - 6.0), "wait": 1.2, "new": True}
        self.alert_until = now + 1700

    def path_point(self, idx):
        """Path ke float index par position (grid units me) aur disha ka angle."""
        n = len(self.path)
        idx = max(0.0, min(float(idx), n - 1.0))
        i = int(idx)
        f = idx - i
        a = self.path[i]
        b = self.path[min(i + 1, n - 1)]
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:      # portal: seedha kood
            f = 1.0 if f > 0.5 else 0.0
        x = a[1] + 0.5 + (b[1] - a[1]) * f
        y = a[0] + 0.5 + (b[0] - a[0]) * f
        if a != b:
            ang = math.atan2(b[0] - a[0], b[1] - a[1])
        elif i > 0:
            p = self.path[i - 1]
            ang = math.atan2(a[0] - p[0], a[1] - p[1])
        else:
            ang = 0.0
        return x, y, ang

    def update(self, dt, now):
        """Return 'caught' agar Packman ne pakad liya."""
        if self.timed and self.started:
            self.elapsed += dt
        head = len(self.path) - 1
        target = max(0.0, head - 2.0)
        self.fol_pos += (target - self.fol_pos) * min(1.0, dt * 8.0)
        if self.fol_pos > head:
            self.fol_pos = float(head)
        pm = self.pm
        if pm is not None:
            if pm["wait"] > 0:
                pm["wait"] -= dt
            else:
                speed = PM_CHASE_BASE + PM_CHASE_STEP * self.mistakes     # jitni galti utna tez
                pm["pos"] = min(float(head), pm["pos"] + speed * dt)
                if head - pm["pos"] < 0.4:
                    return "caught"
        return None

    def show_hint(self, now):
        sp = self._bfs(self.path[-1], self.exit)
        if len(sp) > 1:
            self.hint_cells = sp[1:11]
            self.hint_until = now + 2500
            return True
        return False


# ======================================================================
#  UI helpers
# ======================================================================
def rrect(surf, color, rect, radius, width=0):
    try:
        pygame.draw.rect(surf, color, rect, width, border_radius=radius)
    except TypeError:
        pygame.draw.rect(surf, color, rect, width)


def put_text(font, text, color, center):
    img = font.render(text, True, color)
    screen.blit(img, img.get_rect(center=center))


def draw_star(surf, cx, cy, r, color, edge=None):
    pts = []
    for i in range(10):
        a = math.radians(-90 + 36 * i)
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    pygame.draw.polygon(surf, color, pts)
    if edge:
        pygame.draw.polygon(surf, edge, pts, max(1, int(r * 0.08)))


def draw_star_row(cx, cy, r, count, total=3):
    gap = int(r * 2.3)
    for i in range(total):
        x = cx + int((i - (total - 1) / 2) * gap)
        draw_star(screen, x, cy, r, GOLD_STAR if i < count else STAR_OFF, (150, 105, 20) if i < count else None)


def draw_lock(surf, cx, cy, s, color):
    pygame.draw.arc(surf, color, (int(cx - s * 0.55), int(cy - s * 1.0), int(s * 1.1), int(s * 1.1)),
                    0, math.pi, max(2, int(s * 0.2)))
    rrect(surf, color, (int(cx - s * 0.8), int(cy - s * 0.3), int(s * 1.6), int(s * 1.2)), max(2, int(s * 0.2)))


def draw_button_circle(pos, r=None):
    r = r or BTN_R
    pygame.draw.circle(screen, BTN, pos, r)
    pygame.draw.circle(screen, (225, 210, 175), pos, r, 3)


def draw_icon_restart(pos, r=None):
    r = r or BTN_R
    draw_button_circle(pos, r)
    x, y = pos
    rad = int(r * 0.45)
    a1 = 5.6
    pygame.draw.arc(screen, WALL, (x - rad, y - rad, 2 * rad, 2 * rad), 0.6, a1, max(4, int(r * 0.13)))
    px, py = x + rad * math.cos(a1), y - rad * math.sin(a1)
    d = (-math.sin(a1), -math.cos(a1))
    pp = (math.cos(a1), -math.sin(a1))
    s = r * 0.3
    pygame.draw.polygon(screen, WALL, [(px + d[0] * s * 1.1, py + d[1] * s * 1.1),
                                       (px + pp[0] * s * 0.9, py + pp[1] * s * 0.9),
                                       (px - pp[0] * s * 0.9, py - pp[1] * s * 0.9)])


def draw_icon_home(pos, r=None):
    r = r or BTN_R
    draw_button_circle(pos, r)
    x, y = pos
    s = r * 0.45
    pygame.draw.polygon(screen, WALL, [(x - s * 1.25, y - s * 0.1), (x, y - s * 1.2), (x + s * 1.25, y - s * 0.1)])
    pygame.draw.rect(screen, WALL, (x - s * 0.85, y - s * 0.1, s * 1.7, s * 1.1))
    pygame.draw.rect(screen, BTN, (x - s * 0.22, y + s * 0.3, s * 0.44, s * 0.7))


def draw_icon_next(pos, r=None):
    r = r or BTN_R
    draw_button_circle(pos, r)
    x, y = pos
    s = r * 0.45
    pygame.draw.polygon(screen, WALL, [(x - s * 0.7, y - s * 1.0), (x - s * 0.7, y + s * 1.0), (x + s * 1.0, y)])


def draw_icon_bulb(pos, count):
    draw_button_circle(pos)
    x, y = pos
    pygame.draw.circle(screen, GOLD if count > 0 else (170, 160, 140), (x, y - 4), int(BTN_R * 0.4), 3)
    pygame.draw.rect(screen, WALL, (x - 8, y + int(BTN_R * 0.4) - 4, 16, 8), 0)
    badge = (x + int(BTN_R * 0.8), y - int(BTN_R * 0.8))
    pygame.draw.circle(screen, (230, 80, 80), badge, int(BTN_R * 0.38))
    put_text(font_small, str(count), (255, 255, 255), badge)


def draw_icon_sound(pos, on, r=None):
    r = r or SOUND_R
    draw_button_circle(pos, r)
    x, y = pos
    s = r // 3
    pygame.draw.polygon(screen, GOLD, [(x - s * 1.6, y - s * 0.6), (x - s * 0.7, y - s * 0.6),
                                      (x + s * 0.4, y - s * 1.4), (x + s * 0.4, y + s * 1.4),
                                      (x - s * 0.7, y + s * 0.6), (x - s * 1.6, y + s * 0.6)])
    if on:
        pygame.draw.arc(screen, GOLD, (int(x - s * 0.2), int(y - s * 0.9), int(s * 2), int(s * 1.8)), -0.9, 0.9, 3)
        pygame.draw.arc(screen, GOLD, (int(x - s * 0.2), int(y - s * 1.5), int(s * 3), int(s * 3)), -0.9, 0.9, 3)
    else:
        pygame.draw.line(screen, (200, 60, 50), (x + s * 0.7, y - s * 0.9), (x + s * 2, y + s * 0.9), 4)
        pygame.draw.line(screen, (200, 60, 50), (x + s * 0.7, y + s * 0.9), (x + s * 2, y - s * 0.9), 4)


def draw_icon_back(pos):
    x, y = pos
    s = int(unit * 0.035)
    pygame.draw.line(screen, GOLD, (x + s, y), (x - s, y), 5)
    pygame.draw.line(screen, GOLD, (x - s, y), (x, y - s), 5)
    pygame.draw.line(screen, GOLD, (x - s, y), (x, y + s), 5)


def draw_drops(drops, maxd, cx, y, hard=False):
    r = int(unit * 0.022)
    gap = int(unit * 0.065)
    for i in range(maxd):
        col = (DROP_HC if hard else DROP_ON) if i < drops else DROP_OFF
        px = cx + int((i - (maxd - 1) / 2) * gap)
        pygame.draw.circle(screen, col, (px, y + r // 2), r)
        pygame.draw.polygon(screen, col, [(px, y - r * 2), (px - r, y), (px + r, y)])


def inside_btn(pos, center, r):
    return (pos[0] - center[0]) ** 2 + (pos[1] - center[1]) ** 2 <= (r * 1.45) ** 2     # phone ungli ke liye bada tap area


def inside_rect(pos, rect):
    x, y, w, h = rect
    return x <= pos[0] <= x + w and y <= pos[1] <= y + h


def show_message(text, color, ms=1100):
    overlay = pygame.Surface((W, int(H * 0.14)), pygame.SRCALPHA)
    overlay.fill((40, 30, 20, 200))
    screen.blit(overlay, (0, H // 2 - int(H * 0.07)))
    put_text(font_mid if len(text) > 22 else font_big, text, color, (W // 2, H // 2))
    pygame.display.flip()
    pygame.time.wait(ms)
    pygame.event.clear()


def quit_game(save):
    save.write()
    pygame.quit()
    sys.exit()


_last_daily = [0]


def daily_check(save, sfx):
    """Roz subah 6 baje ka hint (game khula ho tab bhi). True = message dikhaya."""
    now = pygame.time.get_ticks()
    if now - _last_daily[0] > 5000:
        _last_daily[0] = now
        if save.check_daily():
            sfx.play("daily", save.sound)
            show_message("Naya daily hint mila!", (250, 220, 120), 1200)
            return True
    return False


# ======================================================================
#  HOME
# ======================================================================
def draw_icon_shop(pos, r=None):
    r = r or BTN_R
    draw_button_circle(pos, r)
    x, y = pos
    s = r * 0.42
    pygame.draw.arc(screen, WALL, (int(x - s * 0.55), int(y - s * 1.25), int(s * 1.1), int(s * 1.1)),
                    0, math.pi, max(3, int(r * 0.08)))
    rrect(screen, GOLD, (int(x - s * 0.95), int(y - s * 0.45), int(s * 1.9), int(s * 1.5)), max(3, int(s * 0.25)))
    draw_star(screen, x, int(y + s * 0.3), s * 0.38, (255, 245, 200))


def draw_skull(surf, cx, cy, r):
    """Chhoti si khopdi (font me emoji nahi chalta, isliye khud banayi)."""
    bone = (245, 240, 225)
    dark = (40, 30, 30)
    pygame.draw.circle(surf, bone, (cx, cy - r // 6), r)
    pygame.draw.rect(surf, bone, (cx - int(r * 0.55), cy + int(r * 0.45), int(r * 1.1), int(r * 0.75)), border_radius=max(2, r // 6))
    pygame.draw.circle(surf, dark, (cx - int(r * 0.38), cy - int(r * 0.1)), max(2, int(r * 0.26)))
    pygame.draw.circle(surf, dark, (cx + int(r * 0.38), cy - int(r * 0.1)), max(2, int(r * 0.26)))
    pygame.draw.polygon(surf, dark, [(cx, cy + int(r * 0.12)), (cx - int(r * 0.1), cy + int(r * 0.32)), (cx + int(r * 0.1), cy + int(r * 0.32))])
    for k in (-2, 0, 2):
        x = cx + int(k * r * 0.2)
        pygame.draw.line(surf, dark, (x, cy + int(r * 0.7)), (x, cy + int(r * 1.15)), max(1, r // 14))
    pygame.draw.circle(surf, dark, (cx, cy - r // 6), r, max(2, r // 12))


def home_screen(save, sfx):
    bh = int(H * 0.105)
    normal_rect = (int(W * 0.1), int(H * 0.27), int(W * 0.8), bh)
    hc_rect = (int(W * 0.1), int(H * 0.395), int(W * 0.8), bh)
    pm_rect = (int(W * 0.1), int(H * 0.52), int(W * 0.8), bh)
    ar_rect = (int(W * 0.1), int(H * 0.645), int(W * 0.8), bh)
    sound_pos = (W // 2, int(H * 0.905))
    shop_pos = (int(W * 0.88), int(H * 0.075))
    while True:
        daily_check(save, sfx)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                quit_game(save)
            if e.type == pygame.MOUSEBUTTONDOWN:
                if inside_rect(e.pos, normal_rect):
                    sfx.play("click", save.sound)
                    return "normal"
                if inside_rect(e.pos, hc_rect):
                    if save.hc_unlocked():
                        sfx.play("click", save.sound)
                        return "hardcore"
                    sfx.play("hit", save.sound)
                    show_message("Hardcore ke liye %d star chahiye" % HC_UNLOCK_STARS, (255, 200, 120), 1300)
                if inside_rect(e.pos, pm_rect):
                    if save.pm_unlocked():
                        sfx.play("click", save.sound)
                        return "pacman"
                    sfx.play("hit", save.sound)
                    show_message("Pacman ke liye %d star chahiye" % PM_UNLOCK_STARS, (255, 200, 120), 1300)
                if inside_rect(e.pos, ar_rect):
                    sfx.play("click", save.sound)
                    return "arrows"
                if inside_btn(e.pos, shop_pos, BTN_R):
                    sfx.play("click", save.sound)
                    return "shop"
                if inside_btn(e.pos, sound_pos, SOUND_R):
                    save.sound = not save.sound
                    save.write()
                    sfx.play("click", save.sound)

        screen.fill(BG)
        _tw = font_logo.size("MAZEMASTER")[0]
        put_text(font_logo, "MAZEMASTER", GOLD, (W // 2 + int(unit * 0.05), int(H * 0.14)))
        draw_skull(screen, W // 2 + int(unit * 0.05) - _tw // 2 - int(unit * 0.07), int(H * 0.14), int(unit * 0.05))
        draw_star(screen, W // 2 - int(unit * 0.08), int(H * 0.225), int(unit * 0.05), GOLD_STAR, (150, 105, 20))
        put_text(font_big, "x %d" % save.balance(), WALL, (W // 2 + int(unit * 0.07), int(H * 0.225)))

        draw_icon_shop(shop_pos)
        put_text(font_small, "Shop", WALL, (shop_pos[0], shop_pos[1] + BTN_R + int(unit * 0.035)))

        rrect(screen, (210, 160, 60), normal_rect, int(unit * 0.04))
        put_text(font_big, "NORMAL", WALL, (W // 2, normal_rect[1] + int(normal_rect[3] * 0.36)))
        put_text(font_small, "Level %d  |  %d star" % (save.level, save.total_stars()), WALL,
                 (W // 2, normal_rect[1] + int(normal_rect[3] * 0.72)))

        if save.hc_unlocked():
            rrect(screen, (170, 50, 40), hc_rect, int(unit * 0.04))
            put_text(font_big, "HARDCORE", (255, 240, 220), (W // 2, hc_rect[1] + int(hc_rect[3] * 0.36)))
            put_text(font_small, "%d life  |  Best: %d  |  Level %d" % (HC_LIVES, save.hc_best, save.hc_level),
                     (255, 225, 200), (W // 2, hc_rect[1] + int(hc_rect[3] * 0.72)))
        else:
            rrect(screen, (200, 190, 165), hc_rect, int(unit * 0.04))
            put_text(font_big, "HARDCORE", (140, 128, 105), (W // 2 + int(unit * 0.04), hc_rect[1] + int(hc_rect[3] * 0.36)))
            draw_lock(screen, W // 2 - int(unit * 0.25), hc_rect[1] + int(hc_rect[3] * 0.36), int(unit * 0.03), (140, 128, 105))
            put_text(font_small, "Locked: %d / %d star" % (save.total_stars(), HC_UNLOCK_STARS), (140, 128, 105),
                     (W // 2, hc_rect[1] + int(hc_rect[3] * 0.72)))

        if save.pm_unlocked():
            rrect(screen, (245, 205, 50), pm_rect, int(unit * 0.04))
            put_text(font_big, "PACMAN", WALL, (W // 2 + int(unit * 0.05), pm_rect[1] + int(pm_rect[3] * 0.36)))
            draw_pacman(screen, (W // 2 - int(unit * 0.2), pm_rect[1] + int(pm_rect[3] * 0.36)), int(unit * 0.04), 0.0,
                        abs(math.sin(pygame.time.get_ticks() / 200.0)), (60, 40, 20))
            put_text(font_small, "2 min + event  |  Best: %d star" % save.pm_best, WALL,
                     (W // 2, pm_rect[1] + int(pm_rect[3] * 0.72)))
        else:
            rrect(screen, (200, 190, 165), pm_rect, int(unit * 0.04))
            put_text(font_big, "PACMAN", (140, 128, 105), (W // 2 + int(unit * 0.04), pm_rect[1] + int(pm_rect[3] * 0.36)))
            draw_lock(screen, W // 2 - int(unit * 0.22), pm_rect[1] + int(pm_rect[3] * 0.36), int(unit * 0.03), (140, 128, 105))
            put_text(font_small, "Locked: %d / %d star" % (save.total_stars(), PM_UNLOCK_STARS), (140, 128, 105),
                     (W // 2, pm_rect[1] + int(pm_rect[3] * 0.72)))

        rrect(screen, (70, 150, 120), ar_rect, int(unit * 0.04))
        put_text(font_big, "ARROWVERSE", (255, 250, 235), (W // 2, ar_rect[1] + int(ar_rect[3] * 0.36)))
        put_text(font_small, "Teer nikalo  |  Level %d" % save.ar_level, (225, 245, 235),
                 (W // 2, ar_rect[1] + int(ar_rect[3] * 0.72)))
        ax, ay, s_ = W // 2 - int(unit * 0.36), ar_rect[1] + int(ar_rect[3] * 0.36), int(unit * 0.035)
        pygame.draw.line(screen, (255, 250, 235), (ax - s_, ay), (ax + s_, ay), 5)
        pygame.draw.polygon(screen, (255, 250, 235), [(ax + s_ * 1.9, ay), (ax + s_* 0.7, ay - s_), (ax + s_ * 0.7, ay + s_)])

        draw_icon_sound(sound_pos, save.sound)
        pygame.display.flip()
        clock.tick(60)


# ======================================================================
#  LEVEL SELECT (normal mode)
# ======================================================================
def level_select(save, sfx):
    cols = 5
    gap = int(W * 0.02)
    pad = MARGIN
    cell = (W - 2 * pad - gap * (cols - 1)) // cols
    header = int(H * 0.11)
    view_h = H - header
    vis_max = min(TOTAL_LEVELS, (save.level // LEVEL_PAGE + 1) * LEVEL_PAGE)
    rows = (vis_max + cols - 1) // cols
    content_h = gap + rows * (cell + gap)
    max_scroll = max(0, content_h - view_h)
    row_cur = (save.level - 1) // cols
    scroll = min(max_scroll, max(0, row_cur * (cell + gap) - view_h // 2 + cell // 2))
    pressed = False
    moved = 0
    last_y = 0
    press_pos = (0, 0)
    star_r = max(4, int(cell * 0.09))

    def level_at(pos):
        x, y = pos
        if y < header:
            return None
        c = (x - pad) // (cell + gap)
        if c < 0 or c >= cols or (x - pad) - c * (cell + gap) > cell:
            return None
        yy = y - header - gap + scroll
        r = int(yy // (cell + gap))
        if r < 0 or yy - r * (cell + gap) > cell:
            return None
        lv = r * cols + int(c) + 1
        return lv if lv <= vis_max else None

    while True:
        if daily_check(save, sfx):
            pressed = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None
            if e.type == pygame.MOUSEBUTTONDOWN:
                if inside_btn(e.pos, BACK_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    return None
                pressed = True
                moved = 0
                press_pos = e.pos
                last_y = e.pos[1]
            if e.type == pygame.MOUSEMOTION and pressed:
                dy = e.pos[1] - last_y
                last_y = e.pos[1]
                moved += abs(dy)
                scroll = min(max_scroll, max(0, scroll - dy))
            if e.type == pygame.MOUSEBUTTONUP and pressed:
                pressed = False
                if moved < int(unit * 0.02):
                    lv = level_at(press_pos)
                    if lv is not None:
                        if lv <= save.level:
                            sfx.play("click", save.sound)
                            return lv
                        sfx.play("hit", save.sound)
                        show_message("Pehle pichle level khelo!", (255, 200, 120), 900)
                        pressed = False

        screen.fill(BG)
        first_row = max(0, int(scroll // (cell + gap)))
        last_row = min(rows - 1, int((scroll + view_h) // (cell + gap)) + 1)
        for r in range(first_row, last_row + 1):
            for c in range(cols):
                lv = r * cols + c + 1
                if lv > vis_max:
                    break
                x = pad + c * (cell + gap)
                y = header + gap + r * (cell + gap) - int(scroll)
                if lv <= save.level:
                    cur = lv == save.level
                    rrect(screen, (255, 235, 170) if cur else BTN, (x, y, cell, cell), int(cell * 0.18))
                    rrect(screen, GOLD if cur else (225, 210, 175), (x, y, cell, cell), int(cell * 0.18),
                          4 if cur else 2)
                    put_text(font_mid, str(lv), WALL, (x + cell // 2, y + int(cell * 0.38)))
                    if lv % CHASE_EVERY == 0:      # peela dot = Packman level
                        pygame.draw.circle(screen, PAC_YELLOW, (x + int(cell * 0.18), y + int(cell * 0.16)),
                                           max(3, int(cell * 0.07)))
                    if lv % TIMED_EVERY == 0:      # neela dot = timer level
                        pygame.draw.circle(screen, (60, 130, 230), (x + int(cell * 0.82), y + int(cell * 0.16)),
                                           max(3, int(cell * 0.07)))
                    got = save.stars.get(lv, 0)
                    for i in range(3):
                        sx = x + cell // 2 + (i - 1) * int(star_r * 2.3)
                        draw_star(screen, sx, y + int(cell * 0.75), star_r,
                                  GOLD_STAR if i < got else STAR_OFF, (150, 105, 20) if i < got else None)
                else:
                    rrect(screen, (212, 202, 178), (x, y, cell, cell), int(cell * 0.18))
                    put_text(font_small, str(lv), (160, 148, 122), (x + cell // 2, y + int(cell * 0.25)))
                    draw_lock(screen, x + cell // 2, y + int(cell * 0.68), cell * 0.16, (150, 138, 112))
        # header
        pygame.draw.rect(screen, BG, (0, 0, W, header))
        pygame.draw.line(screen, (225, 210, 175), (0, header), (W, header), 3)
        draw_icon_back(BACK_BTN)
        put_text(font_big, "Levels", GOLD, (W // 2, header // 2))
        draw_star(screen, int(W * 0.78), header // 2, int(unit * 0.04), GOLD_STAR, (150, 105, 20))
        put_text(font_mid, str(save.balance()), WALL, (int(W * 0.88), header // 2))
        pygame.display.flip()
        clock.tick(60)


# ======================================================================
#  GAMEPLAY
# ======================================================================
def stars_for_time(sec):
    """Har 7 ke table wale level: 10s se kam=3, 20s se kam=2, 30s se kam=1, uske baad 0."""
    if sec < 10:
        return 3
    if sec < 20:
        return 2
    if sec < 30:
        return 1
    return 0


def comment_for(mistakes):
    """Galtiyon ki jagah comment."""
    if mistakes == 0:
        return "Unstoppable!", (150, 70, 210)
    if mistakes <= 2:
        return "Excellence!", (40, 160, 90)
    return "Try next time", (225, 110, 40)


def chaser_name(fol_id):
    """Marne aane wale ka naam: equip ki hui skin, warna Packman."""
    if fol_id in ("none", "pacman"):
        return "PACKMAN"
    for item in FOLLOWER_ITEMS:
        if item[0] == fol_id:
            return item[1].upper()
    return "PACKMAN"


def draw_frame(maze, save, now, flash_until, hard):
    screen.fill(BG)
    draw_icon_back(BACK_BTN)
    if hard:
        put_text(font_mid, "HARDCORE", DROP_HC, (int(W * 0.30), TOP_H // 2 - int(unit * 0.015)))
        put_text(font_small, "Level %d" % maze.level, WALL, (int(W * 0.30), TOP_H // 2 + int(unit * 0.035)))
    else:
        put_text(font_mid, "Level %d" % maze.level, GOLD, (int(W * 0.30), TOP_H // 2 - int(unit * 0.015)))
        put_text(font_small, maze.shape_name, WALL, (int(W * 0.30), TOP_H // 2 + int(unit * 0.035)))
    drops_y = TOP_H // 2 - int(unit * 0.02)
    draw_drops(maze.drops, HC_LIVES if hard else MAX_DROPS, int(W * 0.63), drops_y, hard)
    row_y = TOP_H // 2 + int(unit * 0.07)
    if not hard:
        if maze.timed:
            draw_star_row(int(W * 0.63), row_y, int(unit * 0.028), stars_for_time(maze.elapsed))
            tcol = (50, 150, 70) if maze.elapsed < 10 else ((200, 140, 20) if maze.elapsed < 20 else (205, 70, 50))
            put_text(font_small, "%.1fs" % maze.elapsed, tcol, (int(W * 0.86), row_y))
        else:
            draw_star_row(int(W * 0.63), row_y, int(unit * 0.028), max(1, 3 - maze.mistakes))
    if maze.chase:
        if maze.pm is None:
            put_text(font_small, "Galti mat karna!", (170, 120, 10), (int(W * 0.28), row_y))
        else:
            put_text(font_small, chaser_name(maze.fol_id) + "!", (200, 40, 30), (int(W * 0.28), row_y))
    draw_icon_sound(SOUND_BTN, save.sound)
    maze.draw(now)
    if now < maze.alert_until:
        txt = font_big.render(chaser_name(maze.fol_id) + " AA RAHA HAI!", True, (200, 30, 25))
        box = txt.get_rect(center=(W // 2, AREA.y + int(unit * 0.07)))
        rrect(screen, (255, 245, 200), box.inflate(40, 20), 14)
        screen.blit(txt, box)
    pygame.draw.rect(screen, (222, 200, 150), (0, H - BOT_H, W, BOT_H))
    draw_icon_restart(RESTART_BTN)
    put_text(font_small, "Restart", WALL, (RESTART_BTN[0], RESTART_BTN[1] + BTN_R + int(unit * 0.035)))
    draw_icon_bulb(HINT_BTN, save.hints)
    put_text(font_small, "Hint", WALL, (HINT_BTN[0], HINT_BTN[1] + BTN_R + int(unit * 0.035)))
    if now < flash_until:
        flash = pygame.Surface((W, H), pygame.SRCALPHA)
        flash.fill((220, 40, 40, 70))
        screen.blit(flash, (0, 0))
    pygame.display.flip()


def result_screen(maze, save, sfx, hard, stars):
    """Level poora: maze ki photo + stars + comment (likha aane ke baad awaaz) + Restart / Next / Home."""
    thumb = maze.render_thumbnail()
    side = min(W - 2 * MARGIN, int(H * 0.42))
    inset = int(unit * 0.02)
    inner = side - 2 * inset
    photo = pygame.transform.smoothscale(thumb, (inner, inner))
    px, py = W // 2 - side // 2, int(H * 0.25)
    can_next = hard or maze.level < TOTAL_LEVELS
    if hard:
        buttons = [("Home", int(W * 0.3), "home", draw_icon_home)]
        if can_next:
            buttons.append(("Next", int(W * 0.7), "next", draw_icon_next))
    else:
        buttons = [("Restart", int(W * 0.2), "restart", draw_icon_restart),
                   ("Home", int(W * 0.5), "home", draw_icon_home)]
        if can_next:
            buttons.append(("Next", int(W * 0.8), "next", draw_icon_next))
    by = int(H * 0.86)
    shown = 0
    t0 = pygame.time.get_ticks()
    comment, ccol = comment_for(maze.mistakes)
    t_comment = t0 + 500 + (0 if hard else 450 * stars)     # stars ke baad comment likhna shuru
    spoken = False
    while True:
        now = pygame.time.get_ticks()
        target = 0 if hard else min(stars, int((now - t0) / 450) + 1)
        if target > shown:
            shown = target
            sfx.play("star", save.sound)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "home"
            if e.type == pygame.MOUSEBUTTONDOWN:
                for label, bx, action, icon in buttons:
                    if inside_btn(e.pos, (bx, by), BTN_R):
                        sfx.play("click", save.sound)
                        return action

        typed = 0 if now < t_comment else int((now - t_comment) / 70) + 1
        typed = min(typed, len(comment))
        if typed >= len(comment) and not spoken:      # likha poora aaya -> ab bolo
            spoken = True
            sfx.speak(comment, save.sound)

        screen.fill(BG)
        if hard:
            put_text(font_big, "Hardcore Level %d Clear!" % maze.level, GOLD, (W // 2, int(H * 0.07)))
            draw_drops(maze.drops, HC_LIVES, W // 2, int(H * 0.15), True)
            put_text(font_small, "Bachi hui life", WALL, (W // 2, int(H * 0.2)))
        else:
            put_text(font_big, "Level %d Clear!" % maze.level, GOLD, (W // 2, int(H * 0.07)))
            draw_star_row(W // 2, int(H * 0.15), int(unit * 0.075), shown)
        rrect(screen, PHOTO, (px, py, side, side), 18)
        rrect(screen, (225, 210, 175), (px, py, side, side), 18, 4)
        screen.blit(photo, (px + inset, py + inset))

        cy = py + side + int(unit * 0.065)
        if typed:
            full_w = font_big.size(comment)[0]
            img = font_big.render(comment[:typed], True, ccol)
            screen.blit(img, (W // 2 - full_w // 2, cy - img.get_height() // 2))
        if hard:
            put_text(font_small, "Levels cleared: %d" % maze.level, WALL, (W // 2, cy + int(unit * 0.07)))
        elif maze.timed:
            put_text(font_small, "Time: %.1fs" % maze.elapsed, WALL, (W // 2, cy + int(unit * 0.07)))
        for label, bx, action, icon in buttons:
            icon((bx, by))
            put_text(font_small, label, WALL, (bx, by + BTN_R + int(unit * 0.035)))
        pygame.display.flip()
        clock.tick(60)


def hc_over_screen(save, sfx, cleared):
    buttons = [("Retry", int(W * 0.3), "retry", draw_icon_restart),
               ("Home", int(W * 0.7), "home", draw_icon_home)]
    by = int(H * 0.8)
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "home"
            if e.type == pygame.MOUSEBUTTONDOWN:
                for label, bx, action, icon in buttons:
                    if inside_btn(e.pos, (bx, by), BTN_R):
                        sfx.play("click", save.sound)
                        return action
        screen.fill(BG)
        put_text(font_title, "GAME", DROP_HC, (W // 2, int(H * 0.15)))
        put_text(font_title, "OVER", DROP_HC, (W // 2, int(H * 0.15) + int(unit * 0.15)))
        draw_drops(0, HC_LIVES, W // 2, int(H * 0.36), True)
        put_text(font_big, "Hardcore khatam", WALL, (W // 2, int(H * 0.45)))
        put_text(font_mid, "Levels cleared: %d" % cleared, WALL, (W // 2, int(H * 0.54)))
        put_text(font_mid, "Best: %d" % save.hc_best, GOLD, (W // 2, int(H * 0.61)))
        for label, bx, action, icon in buttons:
            icon((bx, by))
            put_text(font_small, label, WALL, (bx, by + BTN_R + int(unit * 0.035)))
        pygame.display.flip()
        clock.tick(60)


def play_level(save, sfx, mode, level):
    """Return: normal -> 'restart' / 'next' / 'home' / 'levels'; hardcore -> 'next' / 'home' / 'over'."""
    hard = mode == "hardcore"
    back_action = "home" if hard else "levels"
    maze = Maze(level, hard)
    maze.col_id = save.color
    maze.fol_id = save.follower
    if hard:
        maze.drops = save.hc_lives
    dragging = False
    flash_until = 0
    last = pygame.time.get_ticks()
    last_chomp = 0

    if maze.chase or maze.timed:
        draw_frame(maze, save, last, 0, hard)
        if maze.chase:
            show_message("%s level! Galti = %s peeche" % (chaser_name(maze.fol_id).title(), chaser_name(maze.fol_id).title()), (255, 215, 70), 1100)
        if maze.timed:
            show_message("Timer level! <10s=3  <20s=2  <30s=1", (150, 200, 255), 1300)
        last = pygame.time.get_ticks()

    while True:
        now = pygame.time.get_ticks()
        dt = min(0.05, (now - last) / 1000.0)
        last = now
        if daily_check(save, sfx):
            dragging = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return back_action

            if e.type == pygame.MOUSEBUTTONDOWN:
                pos = e.pos
                if inside_btn(pos, BACK_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    return back_action
                elif inside_btn(pos, SOUND_BTN, SOUND_R):
                    save.sound = not save.sound
                    save.write()
                    sfx.play("click", save.sound)
                elif inside_btn(pos, RESTART_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    # normal: level pura restart; hardcore: sirf path saaf (life wapas nahi)
                    maze.reset(keep_lives=hard)
                elif inside_btn(pos, HINT_BTN, BTN_R):
                    if save.hints > 0:
                        if maze.show_hint(now):
                            save.hints -= 1
                            save.write()
                            sfx.play("hint", save.sound)
                    else:
                        sfx.play("hit", save.sound)
                        show_message("Hint khatam! Kal subah 6 baje milega", (255, 200, 120), 1200)
                        dragging = False
                        last = pygame.time.get_ticks()
                else:
                    dragging = True
                    maze.blocked_cell = None

            if e.type == pygame.MOUSEBUTTONUP:
                dragging = False
                maze.blocked_cell = None

            if dragging and e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                cell = maze.cell_at(e.pos)
                if not cell:
                    continue
                res = maze.try_step(cell, now)
                if res == "ok":
                    sfx.step(len(maze.path), save.sound)
                elif res == "hit":
                    flash_until = now + 150
                    sfx.play("hit", save.sound)
                    if hard:
                        save.hc_lives = maze.drops
                        save.write()
                    if maze.pm is not None and maze.pm.get("new"):
                        maze.pm["new"] = False
                        sfx.play("event", save.sound)
                elif res == "lose":
                    flash_until = now + 150
                    sfx.play("lose", save.sound)
                    draw_frame(maze, save, now, flash_until, hard)
                    dragging = False
                    if hard:
                        cleared = save.hc_level - 1
                        save.hc_best = max(save.hc_best, cleared)
                        save.last_cleared = cleared
                        save.hc_level = 1
                        save.hc_lives = HC_LIVES
                        save.write()
                        show_message("Saari life khatam!", (255, 150, 130), 1200)
                        return "over"
                    show_message("Try again!", (255, 200, 120))
                    maze.reset()
                    last = pygame.time.get_ticks()
                elif res == "portal":
                    sfx.play("portal", save.sound)
                    draw_frame(maze, save, now, flash_until, hard)
                    show_message("Portal! Aage teleport ho gaye", (215, 170, 255), 900)
                    dragging = False
                    last = pygame.time.get_ticks()
                elif res == "prank":
                    sfx.play("prank", save.sound)
                    draw_frame(maze, save, now, flash_until, hard)
                    show_message("Raasta band! Naya raasta khula", (255, 170, 130), 1300)
                    dragging = False
                    last = pygame.time.get_ticks()
                elif res == "win":
                    sfx.play("win", save.sound)
                    draw_frame(maze, save, now, flash_until, hard)
                    dragging = False
                    stars = 0
                    if hard:
                        save.hc_level = level + 1
                        save.hc_best = max(save.hc_best, level)
                    else:
                        if maze.timed:                       # 7 ke table: star sirf timer se
                            stars = stars_for_time(maze.elapsed)
                        else:
                            stars = max(1, 3 - maze.mistakes)
                        if stars > save.stars.get(level, 0):
                            save.stars[level] = stars
                        if level == save.level and level < TOTAL_LEVELS:
                            save.level = level + 1
                    save.write()
                    return result_screen(maze, save, sfx, hard, stars)

        # timer, follower aur Packman ki chaal
        if maze.update(dt, now) == "caught":
            sfx.play("caught", save.sound)
            draw_frame(maze, save, now, flash_until, hard)
            show_message("%s ne pakad liya! Level restart" % chaser_name(maze.fol_id).title(), (255, 215, 70), 1300)
            dragging = False
            maze.reset()
            last = pygame.time.get_ticks()
        elif maze.pm is not None and maze.pm["wait"] <= 0 and now - last_chomp > 360:
            last_chomp = now
            sfx.play("chomp", save.sound)

        draw_frame(maze, save, now, flash_until, hard)
        clock.tick(60)


# ======================================================================
#  SPRITES (Pac-Man / Ghost / Runner)
# ======================================================================
def draw_pacman(surf, pos, r, ang, mouth, color=PAC_YELLOW):
    """mouth: 0 (band) se 1 (poora khula)."""
    x, y = pos
    half = 0.08 + 0.62 * max(0.0, min(1.0, mouth))
    sweep = 2 * math.pi - 2 * half
    pts = [(x, y)]
    for i in range(17):
        a = ang + half + sweep * i / 16
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    pygame.draw.polygon(surf, color, pts)
    ea = ang - 1.15
    pygame.draw.circle(surf, (30, 30, 30), (int(x + r * 0.45 * math.cos(ea)), int(y + r * 0.45 * math.sin(ea))),
                       max(2, int(r * 0.12)))


def draw_ghost(surf, pos, r, color, now=0, scared=False):
    x, y = int(pos[0]), int(pos[1])
    r = max(3, int(r))
    body = (70, 90, 225) if scared else color
    pygame.draw.circle(surf, body, (x, y - r // 8), r)
    pygame.draw.rect(surf, body, (x - r, y - r // 8, 2 * r, r))
    wob = int(math.sin(now / 120.0) * r * 0.08)
    for dx in (-2, 0, 2):
        pygame.draw.circle(surf, body, (x + dx * r // 3, y + int(r * 0.78) + wob), max(2, r // 3))
    for s in (-1, 1):
        ex, ey = x + s * int(r * 0.38), y - int(r * 0.25)
        pygame.draw.circle(surf, (255, 255, 255), (ex, ey), max(2, int(r * 0.27)))
        pygame.draw.circle(surf, (20, 20, 60), (ex + s, ey), max(1, int(r * 0.12)))


_VCACHE = {}


def draw_villain(surf, pos, height, vid, flip=False):
    """Pixel villain sprite, pos par center, height pixels ooncha."""
    art, pal = VILLAIN_ART[vid]
    rows, cols = len(art), len(art[0])
    k = max(1, int(height / rows))
    key = (vid, k, flip)
    img = _VCACHE.get(key)
    if img is None:
        base = pygame.Surface((cols, rows), pygame.SRCALPHA)
        for y, row in enumerate(art):
            for x, ch in enumerate(row):
                if ch in pal:
                    base.set_at((x, y), pal[ch])
        img = pygame.transform.scale(base, (cols * k, rows * k))
        if flip:
            img = pygame.transform.flip(img, True, False)
        _VCACHE[key] = img
    surf.blit(img, img.get_rect(center=(int(pos[0]), int(pos[1]))))


def draw_runner(surf, pos, r, ang, color):
    x, y = int(pos[0]), int(pos[1])
    r = max(3, int(r))
    pygame.draw.circle(surf, color, (x, y), r)
    pygame.draw.circle(surf, (255, 255, 255), (x, y), r, max(2, r // 8))
    for s in (-1, 1):
        ea = ang + s * 0.7
        ex, ey = x + int(r * 0.45 * math.cos(ea)), y + int(r * 0.45 * math.sin(ea))
        pygame.draw.circle(surf, (255, 255, 255), (ex, ey), max(2, int(r * 0.24)))
        pygame.draw.circle(surf, (20, 20, 40), (ex, ey), max(1, int(r * 0.11)))


# ======================================================================
#  SHOP  (star se path ka colour aur peeche dodne wala)
# ======================================================================
def draw_item_preview(kind, item, cx, cy, r, now):
    iid, name, rgb, price = item
    if kind == "color":
        if rgb:
            pygame.draw.line(screen, rgb, (cx - r, cy), (cx + r, cy), max(4, int(r * 0.34)))
            pygame.draw.circle(screen, rgb, (cx - r, cy), max(2, int(r * 0.17)))
            pygame.draw.circle(screen, rgb, (cx + r, cy), max(2, int(r * 0.17)))
        else:
            n = 8
            for i in range(n):
                x = cx - r + int(2 * r * i / (n - 1))
                rr, gg, bb = colorsys.hsv_to_rgb((i / float(n) + now / 2500.0) % 1.0, 0.75, 0.95)
                pygame.draw.circle(screen, (int(rr * 255), int(gg * 255), int(bb * 255)), (x, cy), max(3, int(r * 0.2)))
    elif iid == "none":
        pygame.draw.circle(screen, (170, 160, 140), (cx, cy), int(r * 0.6), 4)
        pygame.draw.line(screen, (170, 160, 140), (cx - int(r * 0.42), cy + int(r * 0.42)),
                         (cx + int(r * 0.42), cy - int(r * 0.42)), 4)
    elif iid == "pacman":
        draw_pacman(screen, (cx, cy), int(r * 0.65), 0.0, abs(math.sin(now / 150.0)), PAC_YELLOW)
    elif iid in VILLAIN_ART:
        draw_villain(screen, (cx, cy + int(math.sin(now / 200.0) * r * 0.05)), r * 1.7, iid)
    else:
        draw_ghost(screen, (cx, cy), r * 0.6, rgb, now)


def shop_screen(save, sfx):
    header = int(H * 0.11)
    gap = int(unit * 0.025)
    tab_y = header + gap
    tab_h = int(H * 0.06)
    half = (W - 2 * MARGIN - gap) // 2
    tabs = {"color": (MARGIN, tab_y, half, tab_h),
            "follower": (MARGIN + half + gap, tab_y, half, tab_h)}
    tab_names = {"color": "Colour", "follower": "Peeche wala"}
    tab = "color"
    cw = half
    ch = int(H * 0.17)
    top = tab_y + tab_h + gap
    scroll = 0
    pressed = False
    moved = 0
    last_y = 0
    press_pos = (0, 0)
    note = ""
    note_until = 0
    tap_limit = int(unit * 0.02)

    def layout(tab_now, scroll_now):
        its = COLOR_ITEMS if tab_now == "color" else FOLLOWER_ITEMS
        default = "blue" if tab_now == "color" else "none"
        content_h = ((len(its) + 1) // 2) * (ch + gap)
        mx = max(0, content_h - (H - top) + int(H * 0.08))
        sc = max(0, min(scroll_now, mx))
        rs = []
        for i in range(len(its)):
            row, col = divmod(i, 2)
            rs.append((MARGIN + col * (cw + gap), top + row * (ch + gap) - sc, cw, ch))
        eq = save.color if tab_now == "color" else save.follower
        return its, default, mx, rs, eq

    while True:
        now = pygame.time.get_ticks()
        items, default_id, max_scroll, rects, equipped = layout(tab, scroll)
        scroll = max(0, min(scroll, max_scroll))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return
            if e.type == pygame.MOUSEBUTTONDOWN:
                if inside_btn(e.pos, BACK_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    return
                hit_tab = False
                for key, rect in tabs.items():
                    if inside_rect(e.pos, rect):
                        hit_tab = True
                        if key != tab:
                            tab = key
                            scroll = 0
                            sfx.play("click", save.sound)
                if not hit_tab and e.pos[1] >= top:
                    pressed = True
                    moved = 0
                    press_pos = e.pos
                    last_y = e.pos[1]
            if e.type == pygame.MOUSEMOTION and pressed:
                dy = e.pos[1] - last_y
                last_y = e.pos[1]
                moved += abs(dy)
                scroll = max(0, min(max_scroll, scroll - dy))
            if e.type == pygame.MOUSEBUTTONUP and pressed:
                pressed = False
                if moved < tap_limit:
                    for item, rect in zip(items, rects):
                        if not inside_rect(press_pos, rect):
                            continue
                        iid, name, rgb, price = item
                        if save.owns(tab, iid):
                            if equipped != iid:
                                save.equip(tab, iid)
                                sfx.play("click", save.sound)
                                note, note_until = "%s equip ho gaya" % name, now + 1300
                            elif iid != default_id:
                                save.equip(tab, default_id)      # Unequip
                                sfx.play("click", save.sound)
                                note, note_until = "%s unequip ho gaya" % name, now + 1300
                        elif save.buy(tab, iid, price):
                            save.equip(tab, iid)
                            sfx.play("buy", save.sound)
                            note, note_until = "%s mil gaya + equip!" % name, now + 1500
                        else:
                            sfx.play("hit", save.sound)
                            note, note_until = "Star kam hain! %d chahiye" % price, now + 1500
                        break

        # tab ya scroll badal gaya ho to list dobara banao (warna purani tab ke item naye tab me bante the)
        items, default_id, max_scroll, rects, equipped = layout(tab, scroll)
        scroll = max(0, min(scroll, max_scroll))
        rects = layout(tab, scroll)[3]

        screen.fill(BG)
        screen.set_clip(pygame.Rect(0, top, W, H - top))
        for item, rect in zip(items, rects):
            iid, name, rgb, price = item
            x, y, w, h = rect
            if y > H or y + h < top:
                continue
            is_eq = equipped == iid
            owned = save.owns(tab, iid)
            rrect(screen, BTN, rect, int(unit * 0.035))
            rrect(screen, (60, 170, 80) if is_eq else (225, 210, 175), rect, int(unit * 0.035), 5 if is_eq else 2)
            draw_item_preview(tab, item, x + int(w * 0.26), y + int(h * 0.36), int(h * 0.3), now)
            put_text(font_small, name, WALL, (x + int(w * 0.70), y + int(h * 0.22)))
            if tab == "follower" and iid in HUNTERS:
                put_text(font_small, "Pacman me bano", (150, 120, 60), (x + int(w * 0.70), y + int(h * 0.42)))
            brect = (x + int(w * 0.08), y + int(h * 0.62), int(w * 0.84), int(h * 0.30))
            bcy = brect[1] + brect[3] // 2
            if is_eq and iid != default_id:
                rrect(screen, (205, 90, 70), brect, int(unit * 0.025))
                put_text(font_small, "Unequip", (255, 255, 255), (x + w // 2, bcy))
            elif is_eq:
                rrect(screen, (150, 205, 150), brect, int(unit * 0.025))
                put_text(font_small, "Equipped", WALL, (x + w // 2, bcy))
            elif owned:
                rrect(screen, (60, 170, 80), brect, int(unit * 0.025))
                put_text(font_small, "Equip", (255, 255, 255), (x + w // 2, bcy))
            else:
                ok = save.balance() >= price
                rrect(screen, (235, 170, 60) if ok else (210, 200, 175), brect, int(unit * 0.025))
                draw_star(screen, x + int(w * 0.30), bcy, int(unit * 0.024), GOLD_STAR, (150, 105, 20))
                put_text(font_small, "%d  Buy" % price, WALL if ok else (140, 128, 105), (x + int(w * 0.62), bcy))
        screen.set_clip(None)

        pygame.draw.rect(screen, BG, (0, 0, W, top))
        pygame.draw.line(screen, (225, 210, 175), (0, header), (W, header), 3)
        draw_icon_back(BACK_BTN)
        put_text(font_big, "Shop", GOLD, (W // 2, header // 2))
        draw_star(screen, int(W * 0.78), header // 2, int(unit * 0.04), GOLD_STAR, (150, 105, 20))
        put_text(font_mid, str(save.balance()), WALL, (int(W * 0.88), header // 2))
        for key, rect in tabs.items():
            on = key == tab
            rrect(screen, (210, 160, 60) if on else (225, 212, 180), rect, int(unit * 0.03))
            put_text(font_mid, tab_names[key], WALL if on else (140, 128, 105),
                     (rect[0] + rect[2] // 2, rect[1] + rect[3] // 2))
        if now < note_until:
            bar = pygame.Rect(0, H - int(H * 0.07), W, int(H * 0.07))
            pygame.draw.rect(screen, (60, 45, 30), bar)
            put_text(font_mid, note, (255, 240, 200), bar.center)
        pygame.display.flip()
        clock.tick(60)


# ======================================================================
#  PACMAN GAME
# ======================================================================
LAST_ROUND = [None]


def bfs_dist(open_, src):
    dist = {src: 0}
    q = deque([src])
    while q:
        cur = q.popleft()
        for nb in open_[cur]:
            if nb not in dist:
                dist[nb] = dist[cur] + 1
                q.append(nb)
    return dist


class Mover:
    """Arena me chalne wala (player / Packman / ghost): cell se cell tak smooth."""

    def __init__(self, cell):
        self.cell = cell
        self.nxt = cell
        self.t = 0.0
        self.dir = (0, 0)
        self.want = (0, 0)
        self.wait = 0.0
        self.ang = 0.0

    def pos(self):
        r0, c0 = self.cell
        r1, c1 = self.nxt
        return (c0 + (c1 - c0) * self.t + 0.5, r0 + (r1 - r0) * self.t + 0.5)

    def near_cell(self):
        return self.nxt if self.t > 0.5 else self.cell

    def turn_back(self):
        self.cell, self.nxt = self.nxt, self.cell
        self.t = 1.0 - self.t
        self.dir = (-self.dir[0], -self.dir[1])
        self.ang = math.atan2(self.dir[0], self.dir[1])

    def advance(self, dt, speed, open_, chooser):
        dist = speed * dt
        guard = 0
        while dist > 0 and guard < 8:
            guard += 1
            if self.nxt == self.cell:
                d = chooser(self)
                if not d:
                    break
                nb = (self.cell[0] + d[0], self.cell[1] + d[1])
                if nb not in open_[self.cell]:
                    break
                self.nxt = nb
                self.t = 0.0
                self.dir = d
                self.ang = math.atan2(d[0], d[1])
            room = 1.0 - self.t
            if dist >= room:
                dist -= room
                self.cell = self.nxt
                self.t = 0.0
            else:
                self.t += dist
                dist = 0


class Arena:
    def __init__(self):
        n = PM_N
        self.n = n
        self.cs = min(AREA.width, AREA.height) // n
        self.ox = AREA.x + (AREA.width - n * self.cs) // 2
        self.oy = AREA.y + (AREA.height - n * self.cs) // 2
        self.cells = {(r, c) for r in range(n) for c in range(n)}
        rng = random.Random()
        self.open = self._generate(rng)
        self.segs = self._segments()
        self._ws = None

    def _generate(self, rng):
        op = {cell: set() for cell in self.cells}
        first = (0, 0)
        seen = {first}
        stack = [first]
        while stack:
            r, c = stack[-1]
            nb = [(r + dr, c + dc) for dr, dc in DIRS
                  if (r + dr, c + dc) in self.cells and (r + dr, c + dc) not in seen]
            if nb:
                nx = rng.choice(nb)
                op[(r, c)].add(nx)
                op[nx].add((r, c))
                seen.add(nx)
                stack.append(nx)
            else:
                stack.pop()
        # kuch deewarein tod do: loop bante hain, ghoom ghoom kar bach sakte ho
        walls = []
        for (r, c) in self.cells:
            for dr, dc in ((1, 0), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in self.cells and nb not in op[(r, c)]:
                    walls.append(((r, c), nb))
        rng.shuffle(walls)
        for a, b in walls[:len(walls) // 4]:
            op[a].add(b)
            op[b].add(a)
        return op

    def _segments(self):
        segs = set()
        for (r, c) in self.cells:
            op = self.open[(r, c)]
            if (r + 1, c) not in op:
                segs.add((c, r + 1, c + 1, r + 1))
            if (r - 1, c) not in op:
                segs.add((c, r, c + 1, r))
            if (r, c + 1) not in op:
                segs.add((c + 1, r, c + 1, r + 1))
            if (r, c - 1) not in op:
                segs.add((c, r, c, r + 1))
        return list(segs)

    def wall_surface(self):
        if self._ws is None:
            s = pygame.Surface((W, H), pygame.SRCALPHA)
            t = max(2, self.cs // 9)
            for gx0, gy0, gx1, gy1 in self.segs:
                p1 = (self.ox + gx0 * self.cs, self.oy + gy0 * self.cs)
                p2 = (self.ox + gx1 * self.cs, self.oy + gy1 * self.cs)
                pygame.draw.line(s, WALL, p1, p2, t)
                pygame.draw.circle(s, WALL, p1, t // 2)
                pygame.draw.circle(s, WALL, p2, t // 2)
            self._ws = s
        return self._ws


PLAYER_COLORS = [(225, 60, 55), (50, 130, 230), (50, 170, 90), (240, 150, 30)]
PLAYER_KEYS = [
    {pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0), pygame.K_LEFT: (0, -1), pygame.K_RIGHT: (0, 1)},
    {pygame.K_w: (-1, 0), pygame.K_s: (1, 0), pygame.K_a: (0, -1), pygame.K_d: (0, 1)},
    {pygame.K_i: (-1, 0), pygame.K_k: (1, 0), pygame.K_j: (0, -1), pygame.K_l: (0, 1)},
    {pygame.K_t: (-1, 0), pygame.K_g: (1, 0), pygame.K_f: (0, -1), pygame.K_h: (0, 1)},
]


def hunter_skin(save):
    """Pacman banne wale ki skin: jo equip hai (villain / Pac-Man), warna jo kharida hua ho."""
    if save.follower in HUNTERS and save.owns("follower", save.follower):
        return save.follower
    for h in HUNTERS:
        if save.owns("follower", h):
            return h
    return None


def draw_skin(surf, pos, size, skin, ang, now):
    """Pacman ya villain sprite (size = lagbhag cell ki chaudai)."""
    if skin in VILLAIN_ART:
        draw_villain(surf, pos, size * 1.0, skin, math.cos(ang) < -0.3)
    else:
        draw_pacman(surf, pos, size * 0.4, ang, abs(math.sin(now / 100.0)), PAC_YELLOW)


class Stick:
    """Ek player ka joystick (uske apne corner me)."""

    def __init__(self, idx, center, r):
        self.idx = idx
        self.c = center
        self.r = r
        self.fid = None
        self.knob = center

    def hit(self, pos):
        return (pos[0] - self.c[0]) ** 2 + (pos[1] - self.c[1]) ** 2 <= (self.r * 1.7) ** 2

    def move(self, pos, rd):
        dx, dy = pos[0] - self.c[0], pos[1] - self.c[1]
        d = math.hypot(dx, dy)
        if d > self.r:
            dx, dy = dx * self.r / d, dy * self.r / d
            d = self.r
        self.knob = (self.c[0] + dx, self.c[1] + dy)
        if d > self.r * 0.3:
            if abs(dx) >= abs(dy):
                rd.set_dir(self.idx, (0, 1 if dx > 0 else -1))
            else:
                rd.set_dir(self.idx, (1 if dy > 0 else -1, 0))

    def release(self):
        self.fid = None
        self.knob = self.c


def make_sticks(n):
    jr = int(min(unit * 0.11, W * 0.12))
    m = MARGIN + int(jr * 1.25)
    top_y = TOP_H + int(jr * 1.25)
    bot_y = H - int(jr * 1.4)
    pos = [(m, bot_y), (W - m, bot_y), (m, top_y), (W - m, top_y)]
    return [Stick(i, pos[i], jr) for i in range(n)]


class PacmanRound:
    """Ek round: 2 min timer, phir 20 sec ka event (Super Speed ya Star Rain).
    n player (1-4). hunter = Pacman banne wale player ka number (0..n-1) ya None = computer Pacman.
    Computer Pacman: sab player bhaagne wale, pakde gaye to out. Player Pacman: wo baaki players
    (aur akele me ghost) ko pakadta hai, har pakad par +2 star."""

    def __init__(self, n, hunter, skin):
        self.arena = Arena()
        self.n = n
        self.hunter = hunter
        self.skin = skin
        self.versus = hunter is not None and n > 1
        a = self.arena
        starts = {1: [(6, 6)], 2: [(6, 5), (6, 7)], 3: [(6, 5), (6, 7), (5, 6)],
                  4: [(6, 5), (6, 7), (5, 6), (7, 6)]}[n]
        self.players = []
        for i in range(n):
            cell = (0, 0) if (self.versus and i == hunter) else starts[i]
            self.players.append(Mover(cell))
        self.freeze = 2.0 if self.versus else 0.0
        self.alive = [True] * n
        self.stars = [0] * n
        self.mini = [0] * n
        self.ghosts = 0
        self.catches = 0
        self.enemies = []
        if hunter is None:
            cells = [(0, 0)]
        elif n == 1:
            cells = [(0, 0), (a.n - 1, a.n - 1)]
        else:
            cells = []
        for cell in cells:
            e = Mover(cell)
            e.wait = 2.0
            self.enemies.append(e)
        self.items = {}
        self.t = 0.0
        self.phase = "run"
        self.event = None
        self.banner_until = 0.0
        self.over = None
        self.spawn_t = PM_SPAWN_EVERY
        for _ in range(5):
            self._spawn_star()

    def earned(self, i):
        v = self.stars[i] + self.mini[i] // 5
        if i == self.hunter:
            v += 2 * (self.ghosts + self.catches)
        return v

    def total(self):
        """Save me jo star jodte hain: sabse jyada kamane wale player ke."""
        return max(self.earned(i) for i in range(self.n))

    def _alive_cells(self):
        return [self.players[i].near_cell() for i in range(self.n) if self.alive[i]]

    def _spawn_star(self):
        a = self.arena
        ref = self._alive_cells()
        if not ref:
            return
        ref_cell = random.choice(ref)
        d = bfs_dist(a.open, ref_cell)
        taken = set(self._alive_cells())
        free = [c for c in a.cells if c not in self.items and c not in taken]
        far = [c for c in free if d.get(c, 0) >= 4] or free
        if far:
            self.items[random.choice(sorted(far))] = "star"

    def set_dir(self, i, d):
        pl = self.players[i]
        pl.want = d
        if pl.nxt != pl.cell and d == (-pl.dir[0], -pl.dir[1]):
            pl.turn_back()

    def update(self, dt, sfx, on):
        if self.over:
            return
        a = self.arena
        self.t += dt

        if self.phase == "run" and self.t >= PM_ROUND_SEC:
            self.phase = "event"
            self.event = random.choice(("speed", "rain"))
            self.banner_until = self.t + 2.5
            if self.event == "rain":
                taken = set(self._alive_cells())
                for c in a.cells:
                    if c not in self.items and c not in taken:
                        self.items[c] = "mini"
            sfx.play("event", on)
        elif self.phase == "event" and self.t >= PM_ROUND_SEC + PM_EVENT_SEC:
            self.over = "done"
            return

        mult = 1.8 if (self.phase == "event" and self.event == "speed") else 1.0

        def chooser(m):
            for d in (m.want, m.dir):
                if d != (0, 0) and (m.cell[0] + d[0], m.cell[1] + d[1]) in a.open[m.cell]:
                    return d
            return None

        if self.freeze > 0:
            self.freeze -= dt
        for i, pl in enumerate(self.players):
            if not self.alive[i]:
                continue
            if self.versus and i == self.hunter and self.freeze > 0:
                continue
            base = PM_RUN_SPEED
            if self.versus:
                base *= 1.05 if i == self.hunter else 0.95
            pl.advance(dt, base * mult, a.open, chooser)
            kind = self.items.pop(pl.near_cell(), None)
            if kind == "star":
                self.stars[i] += 1
                sfx.play("star", on)
            elif kind == "mini":
                self.mini[i] += 1
                if self.mini[i] % 5 == 0:
                    sfx.play("star", on)

        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = PM_SPAWN_EVERY
            if sum(1 for v in self.items.values() if v == "star") < PM_STAR_MAX + self.n - 1:
                self._spawn_star()

        alive = [i for i in range(self.n) if self.alive[i]]

        # player Pacman vs baaki players
        if self.versus:
            hp = self.players[self.hunter].pos()
            for i in alive:
                if i == self.hunter:
                    continue
                px, py = self.players[i].pos()
                if (hp[0] - px) ** 2 + (hp[1] - py) ** 2 < 0.55 ** 2:
                    self.alive[i] = False
                    self.catches += 1
                    sfx.play("ghost", on)
            if not any(self.alive[i] for i in range(self.n) if i != self.hunter):
                self.over = "caught"
                sfx.play("caught", on)
                return

        if not self.enemies:
            return
        dists = {i: bfs_dist(a.open, self.players[i].near_cell()) for i in alive}

        def pick(m):
            nbs = list(a.open[m.cell])
            if not nbs:
                return None
            back = (m.cell[0] - m.dir[0], m.cell[1] - m.dir[1])
            fwd = [x for x in nbs if x != back] or nbs
            if self.hunter is not None:       # akele shikari ke ghost bhaagte hain
                dp = dists[self.hunter]
                nb = max(fwd, key=lambda x: dp.get(x, 0) + random.random() * 1.2)
            elif random.random() < 0.06:
                nb = random.choice(fwd)
            else:
                nb = min(nbs, key=lambda x: min(dists[i].get(x, 999) for i in alive) + random.random() * 0.1)
            return (nb[0] - m.cell[0], nb[1] - m.cell[1])

        for e in self.enemies:
            if e.wait > 0:
                e.wait -= dt
                continue
            e.advance(dt, PM_GHOST_SPEED if self.hunter is not None else PM_CHASER_SPEED, a.open, pick)
            ex, ey = e.pos()
            for i in list(alive):
                px, py = self.players[i].pos()
                if (ex - px) ** 2 + (ey - py) ** 2 >= 0.55 ** 2:
                    continue
                if self.hunter is not None:              # ghost pakda
                    self.ghosts += 1
                    sfx.play("ghost", on)
                    far = max(sorted(a.cells), key=lambda x: dists[i].get(x, 0))
                    e.cell = e.nxt = far
                    e.t = 0.0
                    e.dir = (0, 0)
                    e.wait = 2.0
                    break
                self.alive[i] = False                    # Pacman ne is player ko pakda
                alive.remove(i)
                sfx.play("caught", on)
            if self.hunter is None and not alive:
                self.over = "caught"
                return


def draw_sticks(sticks, rd, now):
    for st in sticks:
        col = PLAYER_COLORS[st.idx]
        out = not rd.alive[st.idx]
        base = (170, 160, 140) if out else col
        pygame.draw.circle(screen, base, st.c, st.r, 5)
        pygame.draw.circle(screen, base, st.c, int(st.r * 0.55), 2)
        pygame.draw.circle(screen, base, (int(st.knob[0]), int(st.knob[1])), int(st.r * 0.42))
        pygame.draw.circle(screen, (255, 255, 255), (int(st.knob[0]), int(st.knob[1])), int(st.r * 0.42), 3)
        put_text(font_mid, "OUT" if out else str(st.idx + 1), (255, 255, 255), (int(st.knob[0]), int(st.knob[1])))


def pm_draw(rd, save, now, sticks):
    a = rd.arena
    cs = a.cs
    ox, oy = a.ox, a.oy
    screen.fill(BG)
    draw_icon_back(BACK_BTN)
    if rd.phase == "run":
        left = max(0, PM_ROUND_SEC - rd.t)
        m, s = divmod(int(math.ceil(left)), 60)
        put_text(font_big, "%d:%02d" % (m, s), WALL, (W // 2, TOP_H // 2 - int(unit * 0.012)))
        if rd.hunter is None:
            tip = "Pacman se bacho!"
        elif rd.versus:
            tip = "P%d Pacman hai - pakdo / bacho!" % (rd.hunter + 1)
        else:
            tip = "Ghost pakdo!"
        put_text(font_small, tip, GOLD, (W // 2, TOP_H // 2 + int(unit * 0.05)))
    else:
        left = max(0, PM_ROUND_SEC + PM_EVENT_SEC - rd.t)
        col = (220, 60, 40) if (now // 250) % 2 else (240, 150, 30)
        put_text(font_big, "%ds" % int(math.ceil(left)), col, (W // 2, TOP_H // 2 - int(unit * 0.012)))
        put_text(font_small, "SUPER SPEED" if rd.event == "speed" else "STAR RAIN", col,
                 (W // 2, TOP_H // 2 + int(unit * 0.05)))
    if rd.n == 1:
        draw_star(screen, int(W * 0.78), TOP_H // 2 - int(unit * 0.01), int(unit * 0.04), GOLD_STAR, (150, 105, 20))
        put_text(font_mid, "x %d" % rd.earned(0), WALL, (int(W * 0.89), TOP_H // 2 - int(unit * 0.01)))
        if rd.mini[0]:
            put_text(font_small, "mini %d/5" % (rd.mini[0] % 5), (170, 130, 40),
                     (int(W * 0.84), TOP_H // 2 + int(unit * 0.05)))
    else:
        step = int(W * 0.095)
        x0 = int(W * 0.64)
        for i in range(rd.n):
            x = x0 + i * step
            col = PLAYER_COLORS[i] if rd.alive[i] else (170, 160, 140)
            pygame.draw.circle(screen, col, (x, TOP_H // 2 - int(unit * 0.012)), int(unit * 0.022))
            put_text(font_small, str(rd.earned(i)), WALL, (x, TOP_H // 2 + int(unit * 0.045)))

    screen.blit(a.wall_surface(), (0, 0))

    for (r, c), kind in rd.items.items():
        p = (ox + c * cs + cs // 2, oy + r * cs + cs // 2)
        if kind == "star":
            draw_star(screen, p[0], p[1], int(cs * 0.3), GOLD_STAR, (150, 105, 20))
        else:
            draw_star(screen, p[0], p[1], max(3, int(cs * 0.14)), (255, 225, 130))

    for i, pl in enumerate(rd.players):
        if not rd.alive[i]:
            continue
        gx, gy = pl.pos()
        pp = (int(ox + gx * cs), int(oy + gy * cs))
        if rd.phase == "event" and rd.event == "speed":
            pygame.draw.circle(screen, (255, 240, 120), pp, int(cs * 0.6), 3)
        if i == rd.hunter:
            if rd.versus and rd.freeze > 0 and (now // 120) % 2:
                continue
            draw_skin(screen, pp, cs, rd.skin, pl.ang, now)
            if rd.n > 1:
                pygame.draw.circle(screen, PLAYER_COLORS[i], pp, int(cs * 0.55), 3)
        else:
            col = PLAYER_COLORS[i] if rd.n > 1 else COLOR_MAP.get(save.color, (40, 140, 220))
            draw_runner(screen, pp, cs * 0.36, pl.ang, col)
        if rd.n > 1:
            put_text(font_small, str(i + 1), PLAYER_COLORS[i], (pp[0], pp[1] - int(cs * 0.62)))

    for e in rd.enemies:
        if e.wait > 0 and (now // 120) % 2:
            continue
        ex, ey = e.pos()
        p = (int(ox + ex * cs), int(oy + ey * cs))
        if rd.hunter is not None:
            draw_ghost(screen, p, cs * 0.38, (225, 55, 50), now, True)
        else:
            draw_pacman(screen, p, cs * 0.42, e.ang, abs(math.sin(now / 90.0)), PAC_YELLOW)

    if rd.t < 6:
        put_text(font_small, "Apne corner ke joystick se chalo", WALL, (W // 2, H - int(BOT_H * 0.5)))
    if rd.phase == "event" and rd.t < rd.banner_until:
        txt = "SUPER SPEED!" if rd.event == "speed" else "STAR RAIN! Har jagah star"
        img = font_big.render(txt, True, (200, 40, 30))
        box = img.get_rect(center=(W // 2, H // 2))
        rrect(screen, (255, 245, 200), box.inflate(50, 30), 16)
        screen.blit(img, box)
    draw_sticks(sticks, rd, now)
    pygame.display.flip()


def pm_finish(save, rd):
    earned = rd.total()
    save.bonus += earned
    save.pm_best = max(save.pm_best, earned)
    save.write()
    return earned


def pm_play(save, sfx, n, hunter, skin):
    """Return (outcome, earned): outcome 'done' / 'caught' / 'home'."""
    rd = PacmanRound(n, hunter, skin)
    LAST_ROUND[0] = rd
    sticks = make_sticks(n)
    anchor = None
    seen_finger = False
    last = pygame.time.get_ticks()
    thr = max(8, int(unit * 0.02))
    FD = getattr(pygame, "FINGERDOWN", None)
    FM = getattr(pygame, "FINGERMOTION", None)
    FU = getattr(pygame, "FINGERUP", None)

    def press(fid, pos):
        for st in sticks:
            if st.fid is None and st.hit(pos):
                st.fid = fid
                st.move(pos, rd)
                return True
        return False

    while True:
        now = pygame.time.get_ticks()
        dt = min(0.05, (now - last) / 1000.0)
        last = now
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pm_finish(save, rd)
                quit_game(save)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "home", pm_finish(save, rd)
                for i in range(n):
                    if e.key in PLAYER_KEYS[i]:
                        rd.set_dir(i, PLAYER_KEYS[i][e.key])
            # --- multi-touch (har ungli apne joystick par) ---
            if FD is not None and e.type in (FD, FM, FU):
                if not seen_finger:
                    seen_finger = True
                    for st in sticks:
                        if st.fid == ("m",):
                            st.release()
                fid = ("f", e.finger_id)
                pos = (e.x * W, e.y * H)
                if e.type == FD:
                    press(fid, pos)
                elif e.type == FM:
                    for st in sticks:
                        if st.fid == fid:
                            st.move(pos, rd)
                else:
                    for st in sticks:
                        if st.fid == fid:
                            st.release()
            # --- mouse (computer ya purana pygame) ---
            if e.type == pygame.MOUSEBUTTONDOWN:
                if inside_btn(e.pos, BACK_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    return "home", pm_finish(save, rd)
                if not seen_finger:
                    if not press(("m",), e.pos) and n == 1:
                        anchor = e.pos
                elif n == 1 and not any(st.hit(e.pos) for st in sticks):
                    anchor = e.pos
            if e.type == pygame.MOUSEBUTTONUP:
                anchor = None
                if not seen_finger:
                    for st in sticks:
                        if st.fid == ("m",):
                            st.release()
            if e.type == pygame.MOUSEMOTION:
                if not seen_finger:
                    for st in sticks:
                        if st.fid == ("m",):
                            st.move(e.pos, rd)
                if anchor is not None and n == 1:
                    dx, dy = e.pos[0] - anchor[0], e.pos[1] - anchor[1]
                    if max(abs(dx), abs(dy)) >= thr:
                        if abs(dx) >= abs(dy):
                            rd.set_dir(0, (0, 1 if dx > 0 else -1))
                        else:
                            rd.set_dir(0, (1 if dy > 0 else -1, 0))
                        anchor = e.pos
        rd.update(dt, sfx, save.sound)
        pm_draw(rd, save, now, sticks)
        if rd.over:
            return rd.over, pm_finish(save, rd)
        clock.tick(60)


def pm_menu(save, sfx):
    buy_rect = (int(W * 0.1), int(H * 0.575), int(W * 0.8), int(H * 0.09))
    who_rect = (int(W * 0.1), int(H * 0.685), int(W * 0.8), int(H * 0.09))
    start_rect = (int(W * 0.1), int(H * 0.795), int(W * 0.8), int(H * 0.10))
    names = {i[0]: i[1] for i in FOLLOWER_ITEMS}
    while True:
        owns_pm = save.owns("follower", "pacman")
        mine = [h for h in HUNTERS if save.owns("follower", h)]
        skin = hunter_skin(save)
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "home"
            if e.type == pygame.MOUSEBUTTONDOWN:
                if inside_btn(e.pos, BACK_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    return "home"
                if inside_rect(e.pos, start_rect):
                    sfx.play("click", save.sound)
                    return "start"
                if inside_rect(e.pos, buy_rect) and not owns_pm:
                    if save.buy("follower", "pacman", PM_PRICE):
                        save.equip("follower", "pacman")
                        sfx.play("buy", save.sound)
                        show_message("Ab tum Pacman bhi ban sakte ho!", PAC_YELLOW, 1200)
                    else:
                        sfx.play("hit", save.sound)
                        show_message("Star kam hain! %d chahiye" % PM_PRICE, (255, 200, 120), 1200)
                if inside_rect(e.pos, who_rect) and len(mine) > 1:
                    cur = mine.index(skin) if skin in mine else 0
                    save.equip("follower", mine[(cur + 1) % len(mine)])
                    sfx.play("click", save.sound)

        screen.fill(BG)
        draw_icon_back(BACK_BTN)
        draw_star(screen, int(W * 0.78), TOP_H // 2, int(unit * 0.04), GOLD_STAR, (150, 105, 20))
        put_text(font_mid, str(save.balance()), WALL, (int(W * 0.88), TOP_H // 2))
        put_text(font_logo, "PACMAN", GOLD, (W // 2, int(H * 0.15)))
        mid = (W // 2, int(H * 0.28))
        if skin in VILLAIN_ART:
            draw_villain(screen, mid, unit * 0.2, skin)
        else:
            draw_pacman(screen, mid, int(unit * 0.08), 0.0, abs(math.sin(now / 220.0)), PAC_YELLOW)
        lines = ["1 se 4 player - har ek ka apna corner joystick",
                 "Pacman computer banega ya koi player (Pacman kharidna padega)",
                 "2 min ka timer, phir 20 sec ka event:",
                 "Super Speed ya Star Rain (har jagah star)"]
        for i, ln in enumerate(lines):
            put_text(font_small, ln, WALL if i < 2 else (120, 100, 70), (W // 2, int(H * (0.395 + 0.036 * i))))
        if owns_pm:
            rrect(screen, (150, 205, 150), buy_rect, int(unit * 0.035))
            put_text(font_mid, "Pacman tumhare paas hai", WALL, (W // 2, buy_rect[1] + buy_rect[3] // 2))
        else:
            ok = save.balance() >= PM_PRICE
            rrect(screen, (235, 170, 60) if ok else (205, 195, 170), buy_rect, int(unit * 0.035))
            put_text(font_mid, "Pacman kharido", WALL, (W // 2 - int(unit * 0.06), buy_rect[1] + buy_rect[3] // 2))
            draw_star(screen, W // 2 + int(unit * 0.22), buy_rect[1] + buy_rect[3] // 2, int(unit * 0.035),
                      GOLD_STAR, (150, 105, 20))
            put_text(font_mid, str(PM_PRICE), WALL, (W // 2 + int(unit * 0.30), buy_rect[1] + buy_rect[3] // 2))
        if mine:
            rrect(screen, (225, 205, 150), who_rect, int(unit * 0.035))
            put_text(font_mid, "Skin: " + names.get(skin, "Pac-Man"), WALL,
                     (W // 2, who_rect[1] + who_rect[3] // 2 - (int(unit * 0.012) if len(mine) > 1 else 0)))
            if len(mine) > 1:
                put_text(font_small, "tap karke badlo", (130, 105, 60), (W // 2, who_rect[1] + int(who_rect[3] * 0.82)))
        else:
            put_text(font_small, "Shop se villain ya Pacman kharido, phir Pacman bano",
                     (130, 105, 60), (W // 2, who_rect[1] + who_rect[3] // 2))
        rrect(screen, (60, 170, 80), start_rect, int(unit * 0.04))
        put_text(font_big, "START", (255, 255, 255), (W // 2, start_rect[1] + start_rect[3] // 2))
        put_text(font_small, "Best: %d star" % save.pm_best, GOLD, (W // 2, int(H * 0.935)))
        pygame.display.flip()
        clock.tick(60)


def pm_players_screen(save, sfx):
    """Kitne player? 1 / 2 / 3 / 4. Return number ya None (back)."""
    size = int(min(W * 0.36, H * 0.17))
    gap = int(W * 0.06)
    x0 = W // 2 - size - gap // 2
    rects = []
    for i in range(4):
        r, c = divmod(i, 2)
        rects.append((x0 + c * (size + gap), int(H * 0.34) + r * (size + gap), size, size))
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None
            if e.type == pygame.MOUSEBUTTONDOWN:
                if inside_btn(e.pos, BACK_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    return None
                for i, rect in enumerate(rects):
                    if inside_rect(e.pos, rect):
                        sfx.play("click", save.sound)
                        return i + 1
        screen.fill(BG)
        draw_icon_back(BACK_BTN)
        put_text(font_big, "Kitne player?", GOLD, (W // 2, int(H * 0.17)))
        put_text(font_small, "Har player ka alag rang aur alag corner me joystick", WALL, (W // 2, int(H * 0.235)))
        for i, rect in enumerate(rects):
            rrect(screen, (235, 200, 110), rect, int(unit * 0.04))
            put_text(font_title, str(i + 1), WALL, (rect[0] + size // 2, rect[1] + int(size * 0.42)))
            dot = max(5, int(size * 0.07))
            for k in range(i + 1):
                dx = int((k - i / 2.0) * dot * 3)
                pygame.draw.circle(screen, PLAYER_COLORS[k], (rect[0] + size // 2 + dx, rect[1] + int(size * 0.8)), dot)
        pygame.display.flip()
        clock.tick(60)


def pm_pacman_screen(save, sfx, n):
    """Pacman kaun banega? Return -1 (computer), player index ya None (back)."""
    can = hunter_skin(save) is not None
    bh = int(H * 0.095)
    rects = [(int(W * 0.1), int(H * 0.30), int(W * 0.8), bh)]
    for i in range(n):
        rects.append((int(W * 0.1), int(H * 0.30) + (i + 1) * (bh + int(H * 0.02)), int(W * 0.8), bh))
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None
            if e.type == pygame.MOUSEBUTTONDOWN:
                if inside_btn(e.pos, BACK_BTN, BTN_R):
                    sfx.play("click", save.sound)
                    return None
                for k, rect in enumerate(rects):
                    if inside_rect(e.pos, rect):
                        if k == 0:
                            sfx.play("click", save.sound)
                            return -1
                        if can:
                            sfx.play("click", save.sound)
                            return k - 1
                        sfx.play("hit", save.sound)
                        show_message("Pehle Pacman ya villain kharido!", (255, 200, 120), 1300)
        screen.fill(BG)
        draw_icon_back(BACK_BTN)
        put_text(font_big, "Pacman kaun banega?", GOLD, (W // 2, int(H * 0.17)))
        put_text(font_small, "Baaki sab bachne wale honge", WALL, (W // 2, int(H * 0.235)))
        for k, rect in enumerate(rects):
            if k == 0:
                rrect(screen, (200, 190, 220), rect, int(unit * 0.035))
                draw_pacman(screen, (rect[0] + int(unit * 0.09), rect[1] + bh // 2), int(bh * 0.32), 0.0,
                            abs(math.sin(pygame.time.get_ticks() / 220.0)), (60, 40, 20))
                put_text(font_mid, "Computer", WALL, (W // 2 + int(unit * 0.04), rect[1] + bh // 2))
            else:
                col = PLAYER_COLORS[k - 1]
                rrect(screen, col if can else (205, 195, 170), rect, int(unit * 0.035))
                put_text(font_mid, "Player %d" % k, (255, 255, 255) if can else (140, 128, 105),
                         (W // 2 + int(unit * 0.04), rect[1] + bh // 2))
                if not can:
                    draw_lock(screen, rect[0] + int(unit * 0.09), rect[1] + int(bh * 0.55), int(unit * 0.03),
                              (140, 128, 105))
        if not can:
            put_text(font_small, "Player ke liye Pacman ya villain kharido", (130, 105, 60),
                     (W // 2, rects[-1][1] + bh + int(H * 0.04)))
        pygame.display.flip()
        clock.tick(60)


def pm_result(save, sfx, outcome, rd, earned):
    buttons = [("Retry", int(W * 0.3), "retry", draw_icon_restart),
               ("Home", int(W * 0.7), "home", draw_icon_home)]
    by = int(H * 0.86)
    sfx.play("win" if outcome == "done" else "lose", save.sound)
    if rd.hunter is None:
        title = "Time up! Bach gaye!" if outcome == "done" else ("Pakde gaye!" if rd.n == 1 else "Sab pakde gaye!")
        tcol = (40, 160, 90) if outcome == "done" else DROP_HC
    else:
        title = "Time up!" if outcome == "done" else ("Khatam!" if rd.n == 1 else "Pacman jeeta!")
        tcol = (40, 160, 90) if outcome == "done" else GOLD
    best = max(range(rd.n), key=rd.earned)
    while True:
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "home"
            if e.type == pygame.MOUSEBUTTONDOWN:
                for label, bx, action, icon in buttons:
                    if inside_btn(e.pos, (bx, by), BTN_R):
                        sfx.play("click", save.sound)
                        return action
        screen.fill(BG)
        put_text(font_big, title, tcol, (W // 2, int(H * 0.10)))
        if rd.skin in VILLAIN_ART:
            draw_villain(screen, (W // 2, int(H * 0.22)), unit * 0.2, rd.skin)
        else:
            draw_pacman(screen, (W // 2, int(H * 0.22)), int(unit * 0.08), 0.0, abs(math.sin(now / 200.0)), PAC_YELLOW)
        draw_star(screen, W // 2 - int(unit * 0.1), int(H * 0.34), int(unit * 0.05), GOLD_STAR, (150, 105, 20))
        put_text(font_title, "+%d" % earned, WALL, (W // 2 + int(unit * 0.12), int(H * 0.34)))
        if rd.n > 1:
            put_text(font_small, "(sabse jyada star wale player ke jude)", (130, 105, 60), (W // 2, int(H * 0.40)))
        for i in range(rd.n):
            y = int(H * 0.47) + i * int(H * 0.075)
            col = PLAYER_COLORS[i] if rd.n > 1 else WALL
            if rd.n > 1:
                pygame.draw.circle(screen, col, (int(W * 0.14), y), int(unit * 0.025))
            bits = ["star %d" % rd.stars[i], "mini %d" % rd.mini[i]]
            if i == rd.hunter:
                bits.append("pakde %d" % (rd.ghosts + rd.catches))
            tag = " *" if (rd.n > 1 and i == best) else ""
            put_text(font_small, "%s%s  =  %d   (%s)" % ("P%d" % (i + 1) if rd.n > 1 else "Tum", tag, rd.earned(i),
                                                          ", ".join(bits)), col, (W // 2 + int(unit * 0.03), y))
        put_text(font_small, "Best: %d star" % save.pm_best, GOLD, (W // 2, int(H * 0.47) + rd.n * int(H * 0.075)))
        for label, bx, action, icon in buttons:
            icon((bx, by))
            put_text(font_small, label, WALL, (bx, by + BTN_R + int(unit * 0.035)))
        pygame.display.flip()
        clock.tick(60)


def pacman_screen(save, sfx):
    while True:
        if pm_menu(save, sfx) != "start":
            return
        step = "players"
        n = 1
        who = -1
        while True:
            if step == "players":
                n = pm_players_screen(save, sfx)
                if n is None:
                    break                       # Pacman menu par wapas
                step = "who"
            elif step == "who":
                who = pm_pacman_screen(save, sfx, n)
                if who is None:
                    step = "players"
                    continue
                step = "play"
            else:
                hunter = None if who < 0 else who
                skin = hunter_skin(save) if hunter is not None else None
                outcome, earned = pm_play(save, sfx, n, hunter, skin)
                if outcome == "home":
                    break
                if pm_result(save, sfx, outcome, LAST_ROUND[0], earned) != "retry":
                    return


# ======================================================================
#  ARROW ESCAPE v2  -  bade picture wale levels (Taj Mahal, Arc, Aquarius...)
#  Har level ek tasveer hai jo hazaaron chhote teeron se bani hai.
#  Teer par tap karo: wo apne raaste par (mudte hue) bahar nikalta hai.
#  Agar nok ke saamne koi aur teer ho to galti (1 boondh kam).
#  Do ungli se zoom / ek ungli se kheencho / neeche + - button bhi hain.
# ======================================================================
AR_PAL = {
    1: (110, 68, 44), 2: (48, 98, 196), 3: (142, 72, 204), 4: (236, 168, 38), 5: (104, 156, 236),
    6: (44, 152, 88), 7: (208, 56, 52), 8: (236, 104, 164), 9: (32, 58, 120), 10: (32, 168, 168),
    11: (112, 112, 128), 12: (52, 52, 64), 13: (122, 200, 92), 14: (250, 206, 70),
}
AR_NPAL = 14
AR_MAX_CELLS = 9000          # grid me kul cells ki had (phone slow na ho)


class ArCanvas:
    """x: 0..1 (chaudai), y: 0..hh (unchai), dono ek hi naap me. Cell = ek chhota chorus."""

    def __init__(self, cols, hh):
        self.cols = cols
        self.hh = hh
        self.rows = max(10, int(round(cols * hh)))
        self.g = [[0] * cols for _ in range(self.rows)]

    def paint(self, fn, col, box=None):
        cols, rows, g = self.cols, self.rows, self.g
        if box is None:
            c0, r0, c1, r1 = 0, 0, cols, rows
        else:
            c0 = max(0, int(box[0] * cols) - 1)
            c1 = min(cols, int(box[2] * cols) + 2)
            r0 = max(0, int(box[1] * cols) - 1)
            r1 = min(rows, int(box[3] * cols) + 2)
        for r in range(r0, r1):
            y = (r + 0.5) / cols
            row = g[r]
            for c in range(c0, c1):
                if fn((c + 0.5) / cols, y):
                    row[c] = col

    def rect(self, x0, y0, x1, y1, col, sym=False):
        self.paint(lambda x, y: x0 <= x <= x1 and y0 <= y <= y1, col, (x0, y0, x1, y1))
        if sym:
            self.rect(1 - x1, y0, 1 - x0, y1, col)

    def ell(self, cx, cy, rx, ry, col, sym=False):
        self.paint(lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1, col,
                   (cx - rx, cy - ry, cx + rx, cy + ry))
        if sym:
            self.ell(1 - cx, cy, rx, ry, col)

    def circ(self, cx, cy, r, col, sym=False):
        self.ell(cx, cy, r, r, col, sym)

    def poly(self, pts, col, sym=False):
        f = _poly(pts)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        self.paint(f, col, (min(xs), min(ys), max(xs), max(ys)))
        if sym:
            self.poly([(1 - x, y) for x, y in pts], col)

    def line(self, x0, y0, x1, y1, w, col, sym=False):
        dx, dy = x1 - x0, y1 - y0
        l2 = dx * dx + dy * dy or 1e-9
        h = w / 2.0

        def f(x, y):
            t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / l2))
            px, py = x0 + t * dx, y0 + t * dy
            return (x - px) ** 2 + (y - py) ** 2 <= h * h
        self.paint(f, col, (min(x0, x1) - h, min(y0, y1) - h, max(x0, x1) + h, max(y0, y1) + h))
        if sym:
            self.line(1 - x0, y0, 1 - x1, y1, w, col)

    def ring(self, cx, cy, r0, r1, col, a0=0, a1=360, sym=False):
        def f(x, y):
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy
            if d2 < r0 * r0 or d2 > r1 * r1:
                return False
            if a1 - a0 >= 360:
                return True
            a = math.degrees(math.atan2(dy, dx)) % 360
            return (a - a0) % 360 <= (a1 - a0)
        self.paint(f, col, (cx - r1, cy - r1, cx + r1, cy + r1))
        if sym:
            na = (180 - a1) % 360
            self.ring(1 - cx, cy, r0, r1, col, na, na + (a1 - a0))

    def band(self, y0, y1, amp, freq, col, x0=0.0, x1=1.0, phase=0.0):
        """Lehrati patti (paani / retile teele)."""
        self.paint(lambda x, y: y0 + amp * math.sin(x * freq + phase) <= y <= y1 + amp * math.sin(x * freq + phase),
                   col, (x0, y0 - amp, x1, y1 + amp))


# ---------------------------------------------------------------- scenes
def sc_heart(cv):
    def heart(s, cy):
        def f(x, y):
            u = (x - 0.5) / s * 1.2
            v = -(y - cy) / s * 1.25 + 0.15
            return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0
        return f
    cv.paint(heart(0.52, 0.56), 7)
    cv.paint(heart(0.42, 0.58), 8)
    cv.paint(heart(0.32, 0.60), 7)
    cv.paint(heart(0.22, 0.62), 14)
    cv.paint(heart(0.12, 0.64), 8)


def sc_taj(cv):
    cv.rect(0.0, 0.84, 1.0, 0.97, 1)
    cv.rect(0.04, 0.87, 0.30, 0.94, 3)
    cv.rect(0.70, 0.87, 0.96, 0.94, 3)
    cv.rect(0.36, 0.87, 0.64, 0.94, 4)
    cv.rect(0.03, 0.79, 0.97, 0.84, 4)
    cv.rect(0.075, 0.36, 0.125, 0.80, 3, sym=True)             # minaar
    cv.rect(0.06, 0.42, 0.14, 0.45, 4, sym=True)
    cv.rect(0.06, 0.58, 0.14, 0.61, 4, sym=True)
    cv.rect(0.06, 0.72, 0.14, 0.75, 4, sym=True)
    cv.ell(0.10, 0.34, 0.04, 0.045, 1, sym=True)
    cv.rect(0.092, 0.22, 0.108, 0.30, 4, sym=True)
    cv.ell(0.5, 0.38, 0.17, 0.20, 5)                           # bada gumbad
    cv.rect(0.485, 0.07, 0.515, 0.19, 4)
    cv.circ(0.5, 0.10, 0.03, 4)
    cv.rect(0.26, 0.47, 0.74, 0.79, 2)                         # mukhya imarat
    cv.rect(0.26, 0.44, 0.74, 0.47, 4)
    cv.ell(0.31, 0.38, 0.045, 0.05, 3, sym=True)               # chhatri
    cv.rect(0.296, 0.42, 0.324, 0.44, 3, sym=True)
    cv.rect(0.305, 0.28, 0.315, 0.34, 4, sym=True)
    cv.rect(0.40, 0.53, 0.60, 0.79, 1)                         # iwan
    cv.ell(0.5, 0.53, 0.10, 0.06, 1)
    cv.rect(0.44, 0.61, 0.56, 0.79, 4)
    cv.ell(0.5, 0.61, 0.06, 0.05, 4)
    cv.rect(0.475, 0.67, 0.525, 0.79, 12)
    cv.ell(0.5, 0.67, 0.025, 0.03, 12)
    cv.rect(0.29, 0.58, 0.36, 0.76, 5, sym=True)
    cv.ell(0.325, 0.58, 0.035, 0.04, 5, sym=True)
    cv.rect(0.305, 0.64, 0.345, 0.74, 9, sym=True)


def sc_arc(cv):
    cv.rect(0.10, 0.10, 0.90, 1.12, 1)
    cv.rect(0.07, 0.05, 0.93, 0.12, 12)                        # chhat
    for k in range(7):
        cv.rect(0.10 + k * 0.115, 0.02, 0.10 + k * 0.115 + 0.07, 0.06, 12)
    cv.rect(0.10, 0.15, 0.90, 0.30, 2)                         # frieze
    for k in range(6):
        cv.rect(0.13 + k * 0.13, 0.18, 0.13 + k * 0.13 + 0.07, 0.27, 5)
    cv.rect(0.08, 0.33, 0.92, 0.36, 12)
    cv.rect(0.35, 0.40, 0.65, 1.12, 4)                         # darwaze ka frame
    cv.ell(0.5, 0.45, 0.15, 0.13, 4)
    cv.rect(0.38, 0.46, 0.62, 1.12, 0)                         # darwaza (khali)
    cv.ell(0.5, 0.47, 0.12, 0.10, 0)
    cv.rect(0.12, 0.66, 0.34, 0.69, 12)
    cv.rect(0.66, 0.66, 0.88, 0.69, 12)
    cv.rect(0.14, 0.42, 0.31, 0.62, 2)                         # relief panel
    cv.rect(0.69, 0.42, 0.86, 0.62, 2)
    cv.rect(0.17, 0.46, 0.28, 0.58, 5)
    cv.rect(0.72, 0.46, 0.83, 0.58, 5)
    cv.rect(0.19, 0.49, 0.26, 0.55, 9)
    cv.rect(0.74, 0.49, 0.81, 0.55, 9)
    for xs in (0.14, 0.69):                                    # neeche ki murtiyan
        cv.rect(xs, 0.74, xs + 0.17, 1.04, 2)
        cv.ell(xs + 0.085, 0.74, 0.085, 0.07, 2)
        cv.rect(xs + 0.03, 0.80, xs + 0.14, 1.0, 3)
        cv.ell(xs + 0.085, 0.80, 0.055, 0.05, 3)
        cv.rect(xs + 0.06, 0.88, xs + 0.11, 1.0, 14)
    cv.rect(0.10, 1.06, 0.90, 1.12, 12)


def sc_eiffel(cv):
    def hw(y):                                                  # tower ki aadhi chaudai
        t = max(0.0, (y - 0.08) / 1.34)
        return 0.03 + 0.40 * t ** 2.0
    cv.paint(lambda x, y: 0.08 <= y <= 1.42 and abs(x - 0.5) <= hw(y), 1, (0.05, 0.08, 0.95, 1.42))
    cv.paint(lambda x, y: 0.40 <= y <= 1.42 and abs(x - 0.5) <= hw(y) - 0.075, 0, (0.05, 0.4, 0.95, 1.42))
    for yy in (0.28, 0.5, 0.78, 1.08, 1.34):
        cv.paint(lambda x, y, yy=yy: yy <= y <= yy + 0.03 and abs(x - 0.5) <= hw(y) + 0.03, 4,
                 (0.05, yy, 0.95, yy + 0.03))
    for yy in (0.62, 0.92, 1.2):                                # X jaali ki patti
        cv.paint(lambda x, y, yy=yy: yy <= y <= yy + 0.025 and abs(x - 0.5) <= hw(y) - 0.04, 5,
                 (0.05, yy, 0.95, yy + 0.025))
    cv.ell(0.5, 1.42, 0.22, 0.24, 0)
    cv.rect(0.485, 0.01, 0.515, 0.10, 12)
    cv.circ(0.5, 0.03, 0.02, 7)


def sc_aquarius(cv):
    cv.rect(0.03, 0.02, 0.97, 1.43, 2)
    cv.rect(0.07, 0.06, 0.93, 1.39, 0)
    cv.rect(0.10, 0.09, 0.90, 1.36, 5)
    cv.rect(0.13, 0.12, 0.87, 1.33, 0)
    for xs in (0.16, 0.78):
        cv.rect(xs, 0.15, xs + 0.06, 0.21, 11)
    for k in range(2):                                           # kumbh ka chinh
        y0 = 0.22 + k * 0.09
        for j in range(4):
            cv.line(0.37 + j * 0.065, y0, 0.37 + j * 0.065 + 0.0325, y0 - 0.04, 0.022, 9)
            cv.line(0.37 + j * 0.065 + 0.0325, y0 - 0.04, 0.37 + (j + 1) * 0.065, y0, 0.022, 9)
    cv.ell(0.80, 0.62, 0.11, 0.15, 3)                            # handle
    cv.ell(0.80, 0.62, 0.06, 0.10, 0)
    cv.ell(0.56, 0.66, 0.22, 0.26, 3)                            # ghada
    cv.ell(0.56, 0.66, 0.15, 0.19, 8)
    cv.ell(0.56, 0.66, 0.07, 0.12, 14)
    cv.rect(0.47, 0.36, 0.65, 0.48, 3)
    cv.rect(0.44, 0.32, 0.68, 0.37, 4)
    cv.poly([(0.36, 0.58), (0.42, 0.56), (0.42, 0.66), (0.30, 1.05), (0.20, 1.05)], 5)   # dhaar
    cv.poly([(0.38, 0.62), (0.42, 0.62), (0.35, 1.05), (0.28, 1.05)], 2)
    cv.line(0.36, 0.60, 0.26, 1.05, 0.02, 14)
    for i, (y0, col) in enumerate(((1.04, 5), (1.12, 2), (1.20, 10), (1.28, 9))):
        cv.band(y0, y0 + 0.07, 0.022, 34, col, 0.13, 0.87, i * 1.3)


def sc_rocket(cv):
    cv.poly([(0.33, 0.90), (0.14, 1.20), (0.34, 1.12)], 7, sym=True)    # par
    cv.poly([(0.40, 1.08), (0.60, 1.08), (0.50, 1.46)], 4)               # lau
    cv.poly([(0.44, 1.08), (0.56, 1.08), (0.50, 1.30)], 14)
    cv.ell(0.5, 0.62, 0.20, 0.50, 5)                                     # dhaancha
    cv.paint(lambda x, y: y <= 0.34 and ((x - 0.5) / 0.20) ** 2 + ((y - 0.62) / 0.50) ** 2 <= 1, 7, (0.3, 0.1, 0.7, 0.35))
    cv.paint(lambda x, y: 0.88 <= y <= 0.95 and ((x - 0.5) / 0.20) ** 2 + ((y - 0.62) / 0.50) ** 2 <= 1, 7, (0.3, 0.88, 0.7, 0.95))
    cv.rect(0.38, 1.04, 0.62, 1.12, 11)
    cv.circ(0.5, 0.58, 0.10, 9)
    cv.circ(0.5, 0.58, 0.07, 10)
    cv.circ(0.47, 0.55, 0.02, 5)
    for (sx, sy) in ((0.1, 0.2), (0.88, 0.3), (0.15, 0.6), (0.9, 0.7), (0.08, 0.95), (0.92, 1.1), (0.78, 0.1), (0.25, 0.1)):
        cv.circ(sx, sy, 0.02, 14)


def sc_cat(cv):
    cv.poly([(0.12, 0.50), (0.16, 0.12), (0.42, 0.34)], 4, sym=True)
    cv.poly([(0.19, 0.42), (0.21, 0.2), (0.34, 0.34)], 8, sym=True)
    cv.ell(0.5, 0.62, 0.38, 0.34, 4)
    cv.poly([(0.5, 0.30), (0.46, 0.42), (0.54, 0.42)], 1)
    cv.poly([(0.38, 0.34), (0.40, 0.44), (0.44, 0.38)], 1)
    cv.poly([(0.62, 0.34), (0.60, 0.44), (0.56, 0.38)], 1)
    cv.circ(0.34, 0.58, 0.085, 6, sym=True)
    cv.ell(0.34, 0.58, 0.03, 0.065, 12, sym=True)
    cv.ell(0.5, 0.88, 0.2, 0.09, 14)
    cv.poly([(0.45, 0.70), (0.55, 0.70), (0.5, 0.77)], 8)
    cv.line(0.5, 0.77, 0.5, 0.82, 0.02, 12)
    cv.line(0.5, 0.82, 0.44, 0.85, 0.02, 12)
    cv.line(0.5, 0.82, 0.56, 0.85, 0.02, 12)
    for k in range(3):
        cv.line(0.30, 0.74 + k * 0.045, 0.06, 0.70 + k * 0.08, 0.018, 12, sym=True)


def sc_sailboat(cv):
    cv.circ(0.78, 0.24, 0.14, 4)
    cv.circ(0.78, 0.24, 0.09, 14)
    cv.rect(0.495, 0.14, 0.515, 0.80, 12)
    cv.poly([(0.48, 0.18), (0.48, 0.74), (0.14, 0.74)], 5)
    cv.poly([(0.53, 0.28), (0.53, 0.74), (0.74, 0.74)], 7)
    cv.poly([(0.505, 0.14), (0.62, 0.18), (0.505, 0.22)], 4)
    cv.poly([(0.16, 0.80), (0.84, 0.80), (0.70, 0.96), (0.30, 0.96)], 1)
    cv.rect(0.22, 0.83, 0.78, 0.86, 14)
    for i, (y0, col) in enumerate(((0.94, 5), (1.02, 2), (1.10, 10), (1.18, 9))):
        cv.band(y0, y0 + 0.07, 0.02, 30, col, 0.0, 1.0, i * 1.1)
    for (gx, gy) in ((0.18, 0.2), (0.3, 0.12)):
        cv.line(gx, gy, gx + 0.04, gy - 0.03, 0.015, 12)
        cv.line(gx + 0.04, gy - 0.03, gx + 0.08, gy, 0.015, 12)


def sc_tree(cv):
    cv.poly([(0.44, 1.05), (0.56, 1.05), (0.54, 0.62), (0.46, 0.62)], 1)
    cv.poly([(0.46, 0.80), (0.26, 0.58), (0.29, 0.55), (0.48, 0.72)], 1)
    cv.poly([(0.54, 0.76), (0.72, 0.52), (0.75, 0.55), (0.56, 0.82)], 1)
    cv.ell(0.5, 1.12, 0.46, 0.08, 6)
    cv.circ(0.50, 0.34, 0.27, 6)
    cv.circ(0.28, 0.50, 0.20, 6)
    cv.circ(0.72, 0.50, 0.20, 6)
    cv.circ(0.50, 0.52, 0.24, 6)
    cv.circ(0.42, 0.32, 0.15, 13)
    cv.circ(0.30, 0.50, 0.09, 13)
    cv.circ(0.62, 0.48, 0.10, 13)
    for (ax, ay) in ((0.38, 0.28), (0.60, 0.26), (0.30, 0.52), (0.72, 0.52), (0.50, 0.48), (0.55, 0.62), (0.42, 0.62)):
        cv.circ(ax, ay, 0.032, 7)
    cv.circ(0.86, 0.14, 0.07, 14)


def sc_castle(cv):
    cv.rect(0.30, 0.42, 0.70, 1.02, 11)
    for k in range(6):
        cv.rect(0.30 + k * 0.0725, 0.37, 0.30 + k * 0.0725 + 0.04, 0.42, 11)
    for xs in (0.06, 0.74):
        cv.rect(xs, 0.30, xs + 0.20, 1.02, 11)
        cv.rect(xs + 0.04, 0.50, xs + 0.16, 0.54, 12)
        cv.poly([(xs - 0.02, 0.30), (xs + 0.10, 0.08), (xs + 0.22, 0.30)], 7)
        cv.rect(xs + 0.095, 0.0, xs + 0.105, 0.09, 12)
        cv.poly([(xs + 0.105, 0.0), (xs + 0.18, 0.03), (xs + 0.105, 0.06)], 4)
    cv.poly([(0.38, 0.40), (0.50, 0.16), (0.62, 0.40)], 3)
    cv.rect(0.495, 0.04, 0.505, 0.17, 12)
    cv.poly([(0.505, 0.04), (0.58, 0.07), (0.505, 0.10)], 14)
    cv.rect(0.42, 0.75, 0.58, 1.02, 1)
    cv.ell(0.5, 0.75, 0.08, 0.08, 1)
    cv.rect(0.46, 0.82, 0.54, 1.02, 12)
    cv.circ(0.5, 0.82, 0.04, 12)
    cv.ell(0.38, 0.58, 0.025, 0.045, 14, sym=True)
    cv.circ(0.5, 0.60, 0.05, 14)
    cv.rect(0.0, 1.02, 1.0, 1.10, 6)
    cv.rect(0.40, 1.02, 0.60, 1.10, 1)


def sc_butterfly(cv):
    cv.ell(0.27, 0.34, 0.23, 0.30, 3, sym=True)
    cv.ell(0.33, 0.76, 0.15, 0.20, 8, sym=True)
    cv.circ(0.25, 0.32, 0.09, 4, sym=True)
    cv.circ(0.25, 0.32, 0.045, 7, sym=True)
    cv.circ(0.31, 0.75, 0.06, 5, sym=True)
    cv.circ(0.20, 0.45, 0.025, 14, sym=True)
    cv.ell(0.5, 0.56, 0.04, 0.40, 12)
    cv.circ(0.5, 0.16, 0.055, 12)
    cv.line(0.48, 0.12, 0.40, 0.02, 0.016, 12, sym=True)
    cv.circ(0.39, 0.02, 0.02, 7, sym=True)


def sc_lighthouse(cv):
    cv.poly([(0.36, 1.12), (0.64, 1.12), (0.57, 0.46), (0.43, 0.46)], 7)
    for k, col in ((0, 5), (1, 5), (2, 5)):
        y0 = 0.58 + k * 0.2
        cv.paint(lambda x, y, y0=y0: y0 <= y <= y0 + 0.1 and abs(x - 0.5) <= 0.07 + (y - 0.46) / 0.66 * 0.07,
                 col, (0.3, y0, 0.7, y0 + 0.1))
    cv.rect(0.38, 0.43, 0.62, 0.47, 12)
    cv.rect(0.43, 0.32, 0.57, 0.43, 4)
    cv.rect(0.47, 0.34, 0.53, 0.41, 14)
    cv.poly([(0.41, 0.32), (0.5, 0.18), (0.59, 0.32)], 12)
    cv.circ(0.5, 0.16, 0.03, 12)
    cv.poly([(0.58, 0.37), (0.97, 0.18), (0.97, 0.52)], 14, sym=True)
    cv.ell(0.5, 1.15, 0.42, 0.10, 11)
    cv.ell(0.25, 1.17, 0.18, 0.08, 12)
    cv.ell(0.78, 1.17, 0.18, 0.08, 12)
    cv.band(1.26, 1.36, 0.02, 30, 2)
    cv.band(1.34, 1.42, 0.02, 30, 9, 0.0, 1.0, 1.4)


def sc_owl(cv):
    cv.rect(0.03, 1.08, 0.97, 1.15, 1)
    cv.poly([(0.20, 0.42), (0.24, 0.10), (0.42, 0.28)], 1, sym=True)
    cv.ell(0.5, 0.66, 0.34, 0.44, 1)
    cv.ell(0.5, 0.78, 0.22, 0.28, 4)
    for k in range(4):
        cv.rect(0.40, 0.66 + k * 0.1, 0.60, 0.70 + k * 0.1, 14)
    cv.ell(0.16, 0.70, 0.09, 0.26, 11)
    cv.ell(0.84, 0.70, 0.09, 0.26, 11)
    cv.circ(0.35, 0.44, 0.16, 4, sym=True)
    cv.circ(0.35, 0.44, 0.11, 10, sym=True)
    cv.circ(0.35, 0.44, 0.06, 12, sym=True)
    cv.poly([(0.45, 0.50), (0.55, 0.50), (0.5, 0.64)], 7)
    cv.poly([(0.38, 1.06), (0.44, 1.06), (0.42, 1.12)], 14, sym=True)


def sc_windmill(cv):
    cv.poly([(0.36, 1.22), (0.64, 1.22), (0.57, 0.58), (0.43, 0.58)], 1)
    cv.rect(0.40, 0.90, 0.60, 0.94, 4)
    cv.rect(0.38, 1.06, 0.62, 1.10, 4)
    cv.poly([(0.40, 0.58), (0.5, 0.42), (0.60, 0.58)], 7)
    cv.rect(0.45, 1.04, 0.55, 1.22, 12)
    cv.circ(0.5, 0.80, 0.03, 5)
    hub = (0.5, 0.52)
    for a in (35, 125, 215, 305):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        nx, ny = -sa, ca
        L = 0.46
        pts = [(hub[0] + nx * 0.015, hub[1] + ny * 0.015), (hub[0] + ca * L + nx * 0.015, hub[1] + sa * L + ny * 0.015),
               (hub[0] + ca * L + nx * 0.115, hub[1] + sa * L + ny * 0.115), (hub[0] + nx * 0.115, hub[1] + ny * 0.115)]
        cv.poly(pts, 5)
        cv.line(hub[0] + ca * 0.02, hub[1] + sa * 0.02, hub[0] + ca * L, hub[1] + sa * L, 0.02, 9)
    cv.circ(hub[0], hub[1], 0.04, 7)
    cv.ell(0.5, 1.25, 0.48, 0.08, 6)
    cv.circ(0.15, 0.15, 0.07, 14)


def sc_pyramids(cv):
    cv.circ(0.78, 0.2, 0.12, 7)
    cv.circ(0.78, 0.2, 0.08, 14)
    cv.poly([(0.04, 0.88), (0.44, 0.24), (0.44, 0.88)], 4)
    cv.poly([(0.44, 0.24), (0.84, 0.88), (0.44, 0.88)], 1)
    for k in range(7):
        y0 = 0.32 + k * 0.08
        cv.paint(lambda x, y, y0=y0: y0 <= y <= y0 + 0.02 and x <= 0.44 and x >= 0.44 - (y - 0.24) * 0.625, 14, (0.04, y0, 0.44, y0 + 0.02))
    cv.poly([(0.66, 0.88), (0.86, 0.58), (0.86, 0.88)], 4)
    cv.poly([(0.86, 0.58), (1.0, 0.88), (0.86, 0.88)], 1)
    cv.band(0.86, 1.0, 0.03, 12, 14)
    cv.band(0.94, 1.0, 0.025, 9, 4, 0.0, 1.0, 2.0)
    cv.rect(0.12, 0.70, 0.14, 0.88, 6)
    cv.circ(0.13, 0.68, 0.04, 6)


def sc_crown(cv):
    cv.poly([(0.10, 0.70), (0.10, 0.22), (0.30, 0.46), (0.50, 0.10), (0.70, 0.46), (0.90, 0.22), (0.90, 0.70)], 4)
    cv.rect(0.10, 0.70, 0.90, 0.84, 14)
    cv.rect(0.10, 0.84, 0.90, 0.90, 1)
    for (x, y, r) in ((0.10, 0.20, 0.05), (0.5, 0.08, 0.055), (0.90, 0.20, 0.05)):
        cv.circ(x, y, r, 7)
    cv.circ(0.5, 0.50, 0.075, 7)
    cv.circ(0.5, 0.50, 0.035, 8)
    cv.circ(0.30, 0.58, 0.045, 2, sym=True)
    for k in range(5):
        cv.circ(0.18 + k * 0.16, 0.77, 0.03, 3 if k % 2 == 0 else 10)
    cv.poly([(0.30, 0.46), (0.40, 0.70), (0.30, 0.70)], 14, sym=True)


def sc_whale(cv):
    cv.poly([(0.74, 0.60), (0.96, 0.38), (0.98, 0.50), (0.88, 0.60), (0.98, 0.72), (0.96, 0.82)], 2)
    cv.ell(0.46, 0.62, 0.38, 0.24, 2)
    cv.paint(lambda x, y: y >= 0.66 and ((x - 0.46) / 0.38) ** 2 + ((y - 0.62) / 0.24) ** 2 <= 1, 5, (0.08, 0.66, 0.84, 0.9))
    cv.paint(lambda x, y: y >= 0.72 and ((x - 0.46) / 0.38) ** 2 + ((y - 0.62) / 0.24) ** 2 <= 1 and int(x * 30) % 2 == 0,
             10, (0.08, 0.72, 0.84, 0.9))
    cv.circ(0.25, 0.56, 0.035, 12)
    cv.circ(0.25, 0.56, 0.015, 5)
    cv.poly([(0.46, 0.76), (0.56, 0.80), (0.52, 0.94)], 9)
    cv.line(0.34, 0.40, 0.34, 0.20, 0.03, 5)
    cv.line(0.34, 0.20, 0.24, 0.10, 0.03, 5)
    cv.line(0.34, 0.20, 0.44, 0.10, 0.03, 5)
    cv.circ(0.22, 0.08, 0.025, 5)
    cv.circ(0.46, 0.08, 0.025, 5)
    cv.band(0.90, 1.02, 0.02, 28, 9)
    cv.band(0.80, 0.86, 0.02, 28, 2, 0.0, 0.2, 1.0)
    cv.band(0.80, 0.86, 0.02, 28, 2, 0.8, 1.0, 1.0)


def sc_flower(cv):
    cv.rect(0.475, 0.58, 0.525, 1.18, 6)
    cv.poly([(0.5, 1.0), (0.22, 0.82), (0.24, 0.96)], 13)
    cv.poly([(0.5, 0.90), (0.78, 0.70), (0.76, 0.86)], 13)
    for k in range(8):
        a = math.radians(k * 45)
        cv.circ(0.5 + 0.22 * math.cos(a), 0.36 + 0.22 * math.sin(a), 0.105, 8 if k % 2 == 0 else 7)
    cv.circ(0.5, 0.36, 0.16, 4)
    cv.circ(0.5, 0.36, 0.10, 14)
    cv.circ(0.5, 0.36, 0.04, 1)
    cv.poly([(0.30, 1.10), (0.70, 1.10), (0.64, 1.38), (0.36, 1.38)], 7)
    cv.rect(0.27, 1.06, 0.73, 1.12, 1)
    cv.rect(0.36, 1.20, 0.64, 1.24, 14)


def sc_anchor(cv):
    cv.ring(0.5, 0.17, 0.06, 0.12, 12)
    cv.rect(0.465, 0.27, 0.535, 1.12, 2)
    cv.rect(0.28, 0.36, 0.72, 0.43, 2)
    cv.ring(0.5, 0.78, 0.29, 0.37, 2, 0, 180)
    cv.poly([(0.10, 0.80), (0.24, 0.74), (0.14, 0.60)], 9)
    cv.poly([(0.90, 0.80), (0.76, 0.74), (0.86, 0.60)], 9)
    cv.rect(0.465, 0.45, 0.535, 0.55, 5)
    cv.rect(0.465, 0.66, 0.535, 0.76, 5)
    cv.ring(0.5, 0.17, 0.0, 0.05, 0)
    cv.band(1.16, 1.32, 0.03, 20, 9)
    cv.band(1.22, 1.32, 0.03, 20, 5, 0.0, 1.0, 1.0)


def sc_icecream(cv):
    cv.poly([(0.28, 0.72), (0.72, 0.72), (0.5, 1.40)], 4)
    cv.paint(lambda x, y: (int((x + y) * 16) % 3 == 0) and 0.74 <= y and abs(x - 0.5) <= (1.40 - y) * 0.33 - 0.01,
             1, (0.28, 0.74, 0.72, 1.40))
    cv.circ(0.5, 0.58, 0.25, 8)
    cv.circ(0.32, 0.72, 0.07, 8)
    cv.circ(0.5, 0.74, 0.07, 8)
    cv.circ(0.68, 0.72, 0.07, 8)
    cv.circ(0.5, 0.38, 0.20, 5)
    cv.circ(0.5, 0.2, 0.15, 14)
    cv.circ(0.5, 0.05, 0.05, 7)
    for (sx, sy) in ((0.4, 0.55), (0.6, 0.5), (0.5, 0.66), (0.44, 0.34), (0.58, 0.40), (0.5, 0.18)):
        cv.circ(sx, sy, 0.018, 3)


# (naam, unchai/chaudai, function)
AR_SCENES = [
    ("Taj Mahal", 0.98, sc_taj), ("Arc de Triomphe", 1.16, sc_arc), ("Aquarius", 1.46, sc_aquarius),
    ("Heart", 1.12, sc_heart), ("Rocket", 1.50, sc_rocket), ("Cat", 1.10, sc_cat),
    ("Sailboat", 1.22, sc_sailboat), ("Eiffel Tower", 1.46, sc_eiffel), ("Castle", 1.12, sc_castle),
    ("Tree", 1.22, sc_tree), ("Butterfly", 1.10, sc_butterfly), ("Lighthouse", 1.44, sc_lighthouse),
    ("Owl", 1.18, sc_owl), ("Windmill", 1.32, sc_windmill), ("Pyramids", 1.04, sc_pyramids),
    ("Crown", 0.96, sc_crown), ("Whale", 1.06, sc_whale), ("Flower", 1.42, sc_flower),
    ("Anchor", 1.40, sc_anchor), ("Ice Cream", 1.46, sc_icecream),
]
AR_NSC = len(AR_SCENES)


def ar_canvas(scene_idx, cols, flipx=False, shift=0):
    """Tasveer ka grid banao. g[r][c] = rang number (0 = khali)."""
    name, hh, fn = AR_SCENES[scene_idx % AR_NSC]
    cols = max(20, min(cols, int((AR_MAX_CELLS / hh) ** 0.5)))
    cv = ArCanvas(cols, hh)
    fn(cv)
    if flipx:
        cv.g = [row[::-1] for row in cv.g]
    if shift:
        cv.g = [[0 if v == 0 else ((v - 1 + shift) % AR_NPAL) + 1 for v in row] for row in cv.g]
    return cv


# ---------------------------------------------------------------- paths + solvable arrows
def ar_tile_paths(g, rows, cols, rng, maxlen):
    """Har rang ke hisse ko lambe, mudte hue raaston me baant do."""
    pid = {}
    paths = []

    def nbs(p):
        r, c = p
        v = g[r][c]
        out = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and g[rr][cc] == v and (rr, cc) not in pid:
                out.append((rr, cc))
        return out

    cells = [(r, c) for r in range(rows) for c in range(cols) if g[r][c]]
    deg = {}
    for p in cells:
        deg[p] = len(nbs(p))
    rng.shuffle(cells)
    cells.sort(key=lambda p: deg[p])
    for start in cells:
        if start in pid:
            continue
        path = [start]
        pid[start] = len(paths)
        paths.append(path)
        target = rng.randint(3, maxlen)
        mine = len(paths) - 1
        while len(path) < target:
            back = len(path) >= 2 and rng.random() < 0.3
            ends = [path[0], path[-1]] if back else [path[-1], path[0]]
            moved = False
            for end in ends:
                options = nbs(end)
                if not options:
                    continue
                if len(path) >= 2:
                    prev = path[1] if end == path[0] else path[-2]
                    straight = (end[0] + (end[0] - prev[0]), end[1] + (end[1] - prev[1]))
                else:
                    straight = None
                if straight in options and rng.random() < 0.55:
                    nxt = straight
                elif rng.random() < 0.5:
                    nxt = min(options, key=lambda q: (len(nbs(q)), rng.random()))
                else:
                    nxt = rng.choice(options)
                pid[nxt] = mine
                if len(path) >= 2 and end == path[0]:
                    path.insert(0, nxt)
                else:
                    path.append(nxt)
                moved = True
                break
            if not moved:
                break
    # akele cells ko padosi raaste ke sire se jod do
    for p in [pt for pt in paths if len(pt) == 1]:
        cell = p[0]
        for dr, dc in rng.sample(DIRS, 4):
            q = (cell[0] + dr, cell[1] + dc)
            j = pid.get(q)
            if j is None or paths[j] is p:
                continue
            other = paths[j]
            if len(other) >= maxlen + 4 or g[q[0]][q[1]] != g[cell[0]][cell[1]]:
                continue
            if other[-1] == q:
                other.append(cell)
            elif other[0] == q:
                other.insert(0, cell)
            else:
                continue
            pid[cell] = j
            p.clear()
            break
    # bache hue akele cells ko aapas me jodo
    for p in [pt for pt in paths if len(pt) == 1]:
        if not p:
            continue
        cell = p[0]
        for dr, dc in rng.sample(DIRS, 4):
            q = (cell[0] + dr, cell[1] + dc)
            j = pid.get(q)
            if j is None or paths[j] is p or len(paths[j]) != 1 or g[q[0]][q[1]] != g[cell[0]][cell[1]]:
                continue
            paths[j].insert(0, cell)
            pid[cell] = j
            p.clear()
            break
    return [p for p in paths if p]


def ar_options(cells):
    """Teer ke possible (cells, dir): sir kis taraf ho."""
    if len(cells) == 1:
        return [(cells, d) for d in DIRS]
    a, b = cells[-2], cells[-1]
    o1 = (cells, (b[0] - a[0], b[1] - a[1]))
    rv = cells[::-1]
    a, b = rv[-2], rv[-1]
    o2 = (rv, (b[0] - a[0], b[1] - a[1]))
    return [o1, o2]


def ar_ray(head, d, rows, cols):
    r, c = head
    r += d[0]
    c += d[1]
    while 0 <= r < rows and 0 <= c < cols:
        yield (r, c)
        r += d[0]
        c += d[1]


def ar_build(g, rows, cols, rng, maxlen):
    """Tasveer ke cells se teer banao. Hamesha hal hone layak (sab ek-ek karke nikal sakte hain)."""
    paths = ar_tile_paths(g, rows, cols, rng, maxlen)
    arrows = []
    occ = {}
    for i, p in enumerate(paths):
        for cell in p:
            occ[cell] = i
    for i, p in enumerate(paths):
        best = None
        for cells, d in ar_options(p):
            blocked = sum(1 for q in ar_ray(cells[-1], d, rows, cols) if q in occ and occ[q] != i)
            key = blocked + rng.random() * 3.0
            if best is None or key < best[0]:
                best = (key, cells, d)
        arrows.append({"cells": list(best[1]), "dir": best[2]})
    n = len(arrows)
    deps = [set() for _ in range(n)]
    dependents = [set() for _ in range(n)]

    def calc(i, remocc):
        s = set()
        a = arrows[i]
        for q in ar_ray(a["cells"][-1], a["dir"], rows, cols):
            j = remocc.get(q)
            if j is not None and j != i:
                s.add(j)
        return s

    for i in range(n):
        deps[i] = calc(i, occ)
        for j in deps[i]:
            dependents[j].add(i)
    alive = set(range(n))
    remocc = dict(occ)
    queue = deque(i for i in alive if not deps[i])
    while alive:
        while queue:
            i = queue.popleft()
            if i not in alive or deps[i]:
                continue
            alive.discard(i)
            for cell in arrows[i]["cells"]:
                remocc.pop(cell, None)
            for k in dependents[i]:
                if k in alive:
                    deps[k].discard(i)
                    if not deps[k]:
                        queue.append(k)
        if not alive:
            break
        # atak gaye: koi teer ghuma do jiska raasta khali ho jaye
        fixed = False
        cand = list(alive)
        rng.shuffle(cand)
        for i in cand:
            a = arrows[i]
            for cells, d in ar_options(a["cells"]):
                if cells == a["cells"] and d == a["dir"]:
                    continue
                if all(remocc.get(q) in (None, i) for q in ar_ray(cells[-1], d, rows, cols)):
                    for j in deps[i]:
                        dependents[j].discard(i)
                    a["cells"], a["dir"] = list(cells), d
                    deps[i] = set()
                    queue.append(i)
                    fixed = True
                    break
            if fixed:
                break
        if fixed:
            continue
        # koi teer ghuma nahi sakta: sabse upar wale cell ko alag karke upar nikalo
        top = min(cell for i in alive for cell in arrows[i]["cells"])
        i = remocc[top]
        cells_i = arrows[i]["cells"]
        k = cells_i.index(top)
        for j in deps[i]:
            dependents[j].discard(i)
        affected = [x for x in dependents[i] if x in alive]
        dependents[i] = set()
        alive.discard(i)
        arrows[i] = None
        new_ids = []
        for part, up in ((cells_i[:k], False), ([top], True), (cells_i[k + 1:], False)):
            if not part:
                continue
            if up:
                arrows.append({"cells": [top], "dir": (-1, 0)})
            else:
                opts = ar_options(part)
                cells, d = min(opts, key=lambda o: sum(1 for q in ar_ray(o[0][-1], o[1], rows, cols)
                                                       if q in remocc) + rng.random())
                arrows.append({"cells": list(cells), "dir": d})
            deps.append(set())
            dependents.append(set())
            nid = len(arrows) - 1
            alive.add(nid)
            for cell in part:
                remocc[cell] = nid
            new_ids.append(nid)
        for x in new_ids + affected:
            deps[x] = calc(x, remocc)
            for j in deps[x]:
                dependents[j].add(x)
        for x in alive:
            if not deps[x]:
                queue.append(x)
    return [a for a in arrows if a is not None]


# ---------------------------------------------------------------- level specs
AR_BROWN = (190, 112, 52)
AR_PURPLE = (132, 70, 176)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def ar_label(level):
    if level <= 5:
        return "Easy", (60, 150, 90), 5
    if level <= 20:
        return "Hard", (140, 80, 200), 4
    return "Extreme", (40, 60, 120), 5


def ar_spec_level(level):
    """Level 1 se hi bada picture; level badhne par grid aur lambe raaste badhte hain."""
    cycle = (level - 1) // AR_NSC
    label, lcol, lives = ar_label(level)
    return {"kind": "level", "level": level, "scene": (level - 1) % AR_NSC,
            "cols": min(40 + 2 * (level - 1), 96), "flip": bool(cycle & 1), "shift": (cycle >> 1) * 4,
            "seed": level * 9176 + 31 + cycle * 13, "maxlen": min(10 + level, 30),
            "label": label, "lcol": lcol, "lives": lives, "title": "Level %d" % level}


def ar_spec_daily(token):
    rng = random.Random(token * 7919 + 5)
    return {"kind": "daily", "level": 0, "scene": rng.randrange(AR_NSC), "cols": 64, "flip": rng.random() < 0.5,
            "shift": rng.choice((0, 0, 4, 8)), "seed": token * 31 + 7, "maxlen": 24,
            "label": "Extreme", "lcol": (40, 60, 120), "lives": 5, "title": "Daily Challenge"}


def ar_spec_free():
    rng = random.Random()
    return {"kind": "free", "level": 0, "scene": rng.randrange(AR_NSC), "cols": rng.randint(40, 72),
            "flip": rng.random() < 0.5, "shift": rng.choice((0, 0, 4, 8)), "seed": rng.randrange(10 ** 8),
            "maxlen": rng.randint(12, 26), "label": "Free Art", "lcol": (60, 150, 90), "lives": 5,
            "title": "Free Art"}


# ---------------------------------------------------------------- puzzle
ARA = pygame.Rect(MARGIN // 2, int(H * 0.145), W - MARGIN, H - int(H * 0.145) - BOT_H)
AR_TINTS = (0.0, 0.0, 0.3, 0.5)


def _ar_draw_arrow(surf, pts, d, col, w, cs):
    dr, dc = d
    if len(pts) == 1:
        x, y = pts[0]
        pts = [(x - dc * cs * 0.45, y - dr * cs * 0.45), (x, y)]
    pygame.draw.lines(surf, col, False, pts, max(1, w))
    if w >= 4:
        rad = w // 2
        lim = cs * cs * 0.2
        for k in range(1, len(pts) - 1):
            p0, p1, p2 = pts[k - 1], pts[k], pts[k + 1]
            if abs((p1[0] - p0[0]) * (p2[1] - p1[1]) - (p1[1] - p0[1]) * (p2[0] - p1[0])) > lim:
                pygame.draw.circle(surf, col, (int(p1[0]), int(p1[1])), rad)
    hx, hy = pts[-1]
    hs = max(2.5, cs * 0.42)
    ux, uy = dc, dr
    tip = (hx + ux * hs * 1.15, hy + uy * hs * 1.15)
    bx, by = hx - ux * hs * 0.1, hy - uy * hs * 0.1
    pygame.draw.polygon(surf, col, [tip, (bx - uy * hs * 0.85, by + ux * hs * 0.85),
                                    (bx + uy * hs * 0.85, by - ux * hs * 0.85)])


class ArrowPuzzle:
    def __init__(self, spec):
        self.spec = spec
        self.level = spec["level"]
        cv = ar_canvas(spec["scene"], spec["cols"], spec["flip"], spec["shift"])
        self.cv = cv
        self.rows, self.cols = cv.rows, cv.cols
        rng = random.Random(spec["seed"])
        built = ar_build(cv.g, self.rows, self.cols, rng, spec["maxlen"])
        self.arrows = []
        self.omap = {}
        for i, a in enumerate(built):
            cells = a["cells"]
            r, c = cells[-1]
            base = AR_PAL[cv.g[r][c]]
            t = rng.choice(AR_TINTS)
            col = tuple(int(v + (255 - v) * t) for v in base)
            rs = [p[0] for p in cells]
            cs_ = [p[1] for p in cells]
            self.arrows.append({"cells": cells, "dir": a["dir"], "col": col, "alive": True, "moving": False,
                                "s": 0.0, "bb": (min(rs), min(cs_), max(rs), max(cs_)), "path": None, "exit": 0})
            for cell in cells:
                self.omap[cell] = i
        self.left = len(self.arrows)
        self.max_drops = spec["lives"]
        self.drops = self.max_drops
        self.mistakes = 0
        self.flash = []
        self.hint_idx = None
        self.hint_until = 0
        self.cs0 = min(ARA.width / float(self.cols), ARA.height / float(self.rows))
        self.zmax = max(3.0, 80.0 / self.cs0)
        self.zoom = 1.0
        self.vcx = self.cols / 2.0
        self.vcy = self.rows / 2.0
        try:
            self.cache = pygame.Surface(ARA.size).convert()
        except Exception:
            self.cache = pygame.Surface(ARA.size)
        self.cache_vc = None
        self.cache_zoom = None
        self.dirty = True

    # ---- view ----
    @property
    def cs(self):
        return self.cs0 * self.zoom

    def clamp(self):
        cs = self.cs
        for axis, size, total in (("x", ARA.width, self.cols), ("y", ARA.height, self.rows)):
            half = size / 2.0 / cs
            if half >= total / 2.0 - 1:
                v = total / 2.0
            else:
                v = getattr(self, "vc" + axis)
                v = max(half - 2.0, min(total - half + 2.0, v))
            setattr(self, "vc" + axis, v)

    def reset_view(self):
        self.zoom = 1.0
        self.vcx, self.vcy = self.cols / 2.0, self.rows / 2.0
        self.dirty = True

    def zoom_at(self, factor, px, py):
        cs = self.cs
        wx = self.vcx + (px - ARA.centerx) / cs
        wy = self.vcy + (py - ARA.centery) / cs
        self.zoom = max(1.0, min(self.zmax, self.zoom * factor))
        cs2 = self.cs
        self.vcx = wx - (px - ARA.centerx) / cs2
        self.vcy = wy - (py - ARA.centery) / cs2
        self.clamp()

    def pan_px(self, dx, dy):
        cs = self.cs
        self.vcx -= dx / cs
        self.vcy -= dy / cs
        self.clamp()

    def to_screen(self, wx, wy):
        cs = self.cs
        return (ARA.centerx + (wx - self.vcx) * cs, ARA.centery + (wy - self.vcy) * cs)

    # ---- game ----
    def ray_len(self, a):
        return sum(1 for _ in ar_ray(a["cells"][-1], a["dir"], self.rows, self.cols))

    def blocker(self, i):
        a = self.arrows[i]
        for q in ar_ray(a["cells"][-1], a["dir"], self.rows, self.cols):
            j = self.omap.get(q)
            if j is not None and j != i:
                return j
        return None

    def tap(self, pos, now):
        """'ok' / 'hit' / 'lose' / None"""
        cs = self.cs
        fc = self.vcx + (pos[0] - ARA.centerx) / cs - 0.5
        fr = self.vcy + (pos[1] - ARA.centery) / cs - 0.5
        r0, c0 = int(math.floor(fr)), int(math.floor(fc))
        best = None
        for r in range(r0 - 1, r0 + 3):
            for c in range(c0 - 1, c0 + 3):
                i = self.omap.get((r, c))
                if i is None:
                    continue
                d = (r - fr) ** 2 + (c - fc) ** 2
                if best is None or d < best[0]:
                    best = (d, i)
        th = max(0.8, 20.0 / cs)
        if best is None or best[0] > th * th:
            return None
        i = best[1]
        j = self.blocker(i)
        a = self.arrows[i]
        if j is None:
            a["moving"] = True
            rl = self.ray_len(a)
            n = len(a["cells"])
            pts = [(c + 0.5, r + 0.5) for r, c in a["cells"]]
            tx, ty = pts[-1]
            dr, dc = a["dir"]
            for k in range(1, rl + n + 5):
                pts.append((tx + dc * k, ty + dr * k))
            a["path"] = pts
            a["exit"] = rl + n + 1
            for cell in a["cells"]:
                self.omap.pop(cell, None)
            if self.hint_idx == i:
                self.hint_idx = None
            self.dirty = True
            return "ok"
        self.drops -= 1
        self.mistakes += 1
        self.flash = [(k, u) for k, u in self.flash if u > now] + [(i, now + 700), (j, now + 700)]
        return "lose" if self.drops <= 0 else "hit"

    def update(self, dt):
        for a in self.arrows:
            if a["alive"] and a["moving"]:
                a["s"] += (14.0 + a["s"] * 2.5) * dt
                if a["s"] >= a["exit"]:
                    a["alive"] = False
                    a["moving"] = False
                    self.left -= 1

    def solved(self):
        return self.left <= 0

    def hint(self, now):
        best = None
        for i, a in enumerate(self.arrows):
            if a["alive"] and not a["moving"] and self.blocker(i) is None:
                r, c = a["cells"][-1]
                d = (c + 0.5 - self.vcx) ** 2 + (r + 0.5 - self.vcy) ** 2
                if best is None or d < best[0]:
                    best = (d, i, r, c)
        if best is None:
            return False
        self.hint_idx = best[1]
        self.hint_until = now + 3500
        px, py = self.to_screen(best[3] + 0.5, best[2] + 0.5)
        if not ARA.collidepoint(px, py):
            self.vcx, self.vcy = best[3] + 0.5, best[2] + 0.5
            self.clamp()
        return True

    # ---- draw ----
    def _render_static(self):
        cs = self.cs
        surf = self.cache
        surf.fill(BG)
        ax = ARA.width / 2.0 - self.vcx * cs
        ay = ARA.height / 2.0 - self.vcy * cs
        w = max(1, int(cs * 0.26))
        c_lo = self.vcx - ARA.width / 2.0 / cs - 1
        c_hi = self.vcx + ARA.width / 2.0 / cs + 1
        r_lo = self.vcy - ARA.height / 2.0 / cs - 1
        r_hi = self.vcy + ARA.height / 2.0 / cs + 1
        for a in self.arrows:
            if not a["alive"] or a["moving"]:
                continue
            r0, c0, r1, c1 = a["bb"]
            if c1 < c_lo or c0 > c_hi or r1 < r_lo or r0 > r_hi:
                continue
            pts = [(ax + (c + 0.5) * cs, ay + (r + 0.5) * cs) for r, c in a["cells"]]
            _ar_draw_arrow(surf, pts, a["dir"], a["col"], w, cs)
        self.cache_vc = (self.vcx, self.vcy)
        self.cache_zoom = self.zoom
        self.dirty = False

    def draw(self, now, panning=False):
        cs = self.cs
        if self.dirty or self.cache_zoom != self.zoom or (not panning and self.cache_vc != (self.vcx, self.vcy)):
            self._render_static()
        ox = int(round((self.cache_vc[0] - self.vcx) * cs))
        oy = int(round((self.cache_vc[1] - self.vcy) * cs))
        screen.set_clip(ARA)
        if ox or oy:
            screen.fill(BG, ARA)
        screen.blit(self.cache, (ARA.x + ox, ARA.y + oy))
        w = max(1, int(cs * 0.26))
        bad = {k for k, u in self.flash if u > now}
        for i in bad:
            a = self.arrows[i]
            if not a["alive"] or a["moving"]:
                continue
            col = (235, 35, 30) if (now // 90) % 2 == 0 else (255, 120, 80)
            sh = math.sin(now / 18.0) * cs * 0.08
            pts = [self.to_screen(c + 0.5, r + 0.5) for r, c in a["cells"]]
            pts = [(x + sh, y) for x, y in pts]
            _ar_draw_arrow(screen, pts, a["dir"], col, w + 2, cs)
        if self.hint_idx is not None and now < self.hint_until:
            a = self.arrows[self.hint_idx]
            r, c = a["cells"][-1]
            hx, hy = self.to_screen(c + 0.5, r + 0.5)
            rad = int(max(cs * 0.9, unit * 0.03) * (1.0 + 0.15 * math.sin(now / 120.0)))
            pygame.draw.circle(screen, HINT, (int(hx), int(hy)), rad, max(3, int(unit * 0.008)))
        for a in self.arrows:
            if not (a["alive"] and a["moving"]):
                continue
            P = a["path"]
            n = len(a["cells"])
            s = a["s"]
            i0 = int(s)
            f = s - i0

            def lerp(p, q):
                return (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)
            if n == 1:
                wp = [lerp(P[i0], P[i0 + 1])]
            else:
                wp = [lerp(P[i0], P[i0 + 1])] + P[i0 + 1:i0 + n] + [lerp(P[i0 + n - 1], P[i0 + n])]
            pts = [self.to_screen(x, y) for x, y in wp]
            _ar_draw_arrow(screen, pts, a["dir"], a["col"], w, cs)
        screen.set_clip(None)


# ---------------------------------------------------------------- icons / thumbnails
AR_BACK = (int(W * 0.08), int(H * 0.05))
AR_HEX = (int(W * 0.92), int(H * 0.05))
AR_HINT = (int(W * 0.88), int(H * 0.107))
AR_BTN_Y = H - BOT_H // 2
AR_RESTART = (int(W * 0.16), AR_BTN_Y)
AR_ZOUT = (int(W * 0.39), AR_BTN_Y)
AR_ZIN = (int(W * 0.61), AR_BTN_Y)
AR_FIT = (int(W * 0.84), AR_BTN_Y)
_ar_thumb_cache = {}


def ar_thumb(cv, bw, bh):
    px = max(2, min(bw // cv.cols, bh // cv.rows))
    surf = pygame.Surface((cv.cols * px, cv.rows * px), pygame.SRCALPHA)
    for r in range(cv.rows):
        row = cv.g[r]
        for c in range(cv.cols):
            v = row[c]
            if v:
                surf.fill(AR_PAL[v], (c * px, r * px, px, px))
    return surf


def draw_icon_hex(pos, on=True, r=None):
    r = r or int(BTN_R * 0.75)
    x, y = pos
    pts = [(x + r * math.cos(math.radians(60 * i + 30)), y + r * math.sin(math.radians(60 * i + 30))) for i in range(6)]
    pygame.draw.polygon(screen, AR_BROWN, pts, max(3, int(r * 0.12)))
    pygame.draw.circle(screen, AR_BROWN, (x, y), int(r * 0.38), max(3, int(r * 0.12)))
    if not on:
        pygame.draw.line(screen, (200, 60, 50), (x - r * 0.7, y + r * 0.7), (x + r * 0.7, y - r * 0.7), max(3, int(r * 0.14)))


def draw_icon_zoom(pos, plus):
    draw_button_circle(pos)
    x, y = pos
    s = int(BTN_R * 0.4)
    wd = max(4, int(BTN_R * 0.13))
    pygame.draw.line(screen, WALL, (x - s, y), (x + s, y), wd)
    if plus:
        pygame.draw.line(screen, WALL, (x, y - s), (x, y + s), wd)


def draw_icon_fit(pos):
    draw_button_circle(pos)
    x, y = pos
    s = int(BTN_R * 0.42)
    k = int(s * 0.55)
    wd = max(4, int(BTN_R * 0.12))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = x + sx * s, y + sy * s
            pygame.draw.line(screen, WALL, (cx, cy), (cx - sx * k, cy), wd)
            pygame.draw.line(screen, WALL, (cx, cy), (cx, cy - sy * k), wd)


def draw_crown(cx, cy, s, color):
    pts = [(cx - s, cy + s * 0.6), (cx - s, cy - s * 0.5), (cx - s * 0.5, cy), (cx, cy - s * 0.8),
           (cx + s * 0.5, cy), (cx + s, cy - s * 0.5), (cx + s, cy + s * 0.6)]
    pygame.draw.polygon(screen, color, pts)


def draw_tiger(rect, rank):
    x, y, w, h = rect
    rrect(screen, (245, 125, 75), rect, int(w * 0.22))
    rrect(screen, (255, 200, 110), rect, int(w * 0.22), max(3, int(w * 0.05)))
    cx, cy = x + w // 2, y + int(h * 0.50)
    r = int(w * 0.30)
    for sx in (-1, 1):
        pygame.draw.circle(screen, (250, 160, 50), (cx + sx * int(r * 0.85), cy - int(r * 0.85)), int(r * 0.35))
    pygame.draw.circle(screen, (252, 175, 60), (cx, cy), r)
    pygame.draw.circle(screen, (255, 240, 220), (cx, cy + int(r * 0.35)), int(r * 0.5))
    for sx in (-1, 1):
        pygame.draw.circle(screen, (40, 30, 30), (cx + sx * int(r * 0.42), cy - int(r * 0.1)), max(2, int(r * 0.13)))
        pygame.draw.line(screen, (120, 60, 20), (cx + sx * int(r * 0.95), cy - int(r * 0.2)),
                         (cx + sx * int(r * 0.7), cy - int(r * 0.1)), max(2, int(r * 0.1)))
    pygame.draw.polygon(screen, (220, 80, 80), [(cx - int(r * 0.12), cy + int(r * 0.15)), (cx + int(r * 0.12), cy + int(r * 0.15)), (cx, cy + int(r * 0.3))])
    bp = (cx, y + h - int(h * 0.08))
    pygame.draw.circle(screen, (225, 60, 50), bp, int(w * 0.13))
    put_text(font_small, str(rank), (255, 255, 255), bp)


def ar_loading(text):
    screen.fill(BG)
    put_text(font_big, text, GOLD, (W // 2, H // 2))
    pygame.display.flip()
    pygame.event.pump()


# ---------------------------------------------------------------- play screen
def arrow_frame(puz, save, now, flash_until, panning=False):
    spec = puz.spec
    screen.fill(BG)
    draw_icon_back(AR_BACK)
    put_text(font_big, spec["title"], AR_BROWN, (W // 2, int(H * 0.036)))
    put_text(font_small, spec["label"], spec["lcol"], (W // 2, int(H * 0.068)))
    draw_icon_hex(AR_HEX, save.sound)
    r = int(unit * 0.022)
    gap = int(unit * 0.065)
    draw_drops(puz.drops, puz.max_drops, MARGIN + r * 2 + int((puz.max_drops - 1) / 2.0 * gap), int(H * 0.108))
    put_text(font_small, "Bache: %d" % max(0, puz.left), WALL, (int(W * 0.56), int(H * 0.108)))
    draw_icon_bulb(AR_HINT, save.hints)
    pygame.draw.line(screen, (225, 210, 175), (MARGIN, int(H * 0.14)), (W - MARGIN, int(H * 0.14)), 2)
    puz.draw(now, panning)
    pygame.draw.rect(screen, (222, 200, 150), (0, H - BOT_H, W, BOT_H))
    draw_icon_restart(AR_RESTART)
    put_text(font_small, "Restart", WALL, (AR_RESTART[0], AR_RESTART[1] + BTN_R + int(unit * 0.035)))
    draw_icon_zoom(AR_ZOUT, False)
    put_text(font_small, "Zoom -", WALL, (AR_ZOUT[0], AR_ZOUT[1] + BTN_R + int(unit * 0.035)))
    draw_icon_zoom(AR_ZIN, True)
    put_text(font_small, "Zoom +", WALL, (AR_ZIN[0], AR_ZIN[1] + BTN_R + int(unit * 0.035)))
    draw_icon_fit(AR_FIT)
    put_text(font_small, "Fit", WALL, (AR_FIT[0], AR_FIT[1] + BTN_R + int(unit * 0.035)))
    if now < flash_until:
        fl = pygame.Surface((W, H), pygame.SRCALPHA)
        fl.fill((220, 40, 40, 70))
        screen.blit(fl, (0, 0))
    pygame.display.flip()


def arrow_result(puz, save, sfx, reward):
    buttons = [("Restart", int(W * 0.2), "restart", draw_icon_restart),
               ("Home", int(W * 0.5), "home", draw_icon_home),
               ("Next", int(W * 0.8), "next", draw_icon_next)]
    by = int(H * 0.86)
    comment, ccol = comment_for(puz.mistakes)
    thumb = ar_thumb(puz.cv, int(W * 0.8), int(H * 0.36))
    t0 = pygame.time.get_ticks()
    spoken = False
    name = AR_SCENES[puz.spec["scene"] % AR_NSC][0]
    while True:
        now = pygame.time.get_ticks()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "home"
            if e.type == pygame.MOUSEBUTTONDOWN:
                for label, bx, action, icon in buttons:
                    if inside_btn(e.pos, (bx, by), BTN_R):
                        sfx.play("click", save.sound)
                        return action
        if not spoken and now - t0 > 400:
            spoken = True
            sfx.speak(comment, save.sound)
        screen.fill(BG)
        put_text(font_big, "%s Clear!" % puz.spec["title"], GOLD, (W // 2, int(H * 0.07)))
        put_text(font_mid, comment, ccol, (W // 2, int(H * 0.125)))
        screen.blit(thumb, thumb.get_rect(center=(W // 2, int(H * 0.36))))
        put_text(font_small, name, (150, 130, 105), (W // 2, int(H * 0.575)))
        put_text(font_mid, "Galtiyan: %d" % puz.mistakes, WALL, (W // 2, int(H * 0.64)))
        if reward:
            draw_star(screen, W // 2 - int(unit * 0.06), int(H * 0.72), int(unit * 0.05), GOLD_STAR, (150, 105, 20))
            put_text(font_big, "+%d" % reward, WALL, (W // 2 + int(unit * 0.08), int(H * 0.72)))
        for label, bx, action, icon in buttons:
            icon((bx, by))
            put_text(font_small, label, WALL, (bx, by + BTN_R + int(unit * 0.035)))
        pygame.display.flip()
        clock.tick(60)


_ar_tip_shown = [False]


def arrow_play(save, sfx, spec):
    """Return 'restart' / 'next' / 'home'."""
    ar_loading("Picture ban rahi hai...")
    puz = ArrowPuzzle(spec)
    if not _ar_tip_shown[0]:
        _ar_tip_shown[0] = True
        show_message("Do ungli se zoom, ek ungli se kheencho", (255, 215, 70), 1500)
    flash_until = 0
    last = pygame.time.get_ticks()
    slop = int(unit * 0.025)
    down = None
    last_pos = None
    dragging = False
    multi = False
    fingers = {}
    pinch = None
    multi_t = -10000          # aakhri baar do-ungli (zoom) kab hua
    FD = getattr(pygame, "FINGERDOWN", None)
    FM = getattr(pygame, "FINGERMOTION", None)
    FU = getattr(pygame, "FINGERUP", None)
    WHEEL = getattr(pygame, "MOUSEWHEEL", None)
    while True:
        now = pygame.time.get_ticks()
        dt = min(0.05, (now - last) / 1000.0)
        last = now
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "home"
            elif WHEEL is not None and e.type == WHEEL:
                mx, my = pygame.mouse.get_pos()
                puz.zoom_at(1.18 ** e.y, mx, my)
                puz.dirty = True
            elif FD is not None and e.type == FD:
                # purani atki hui ungliyan hata do (warna tap hamesha 'zoom' samajh kar band ho jata tha)
                fingers = {k: v for k, v in fingers.items() if now - v[2] < 2500}
                fingers[e.finger_id] = (e.x * W, e.y * H, now)
                if len(fingers) >= 2:
                    multi = True
                    multi_t = now
                    down = None
                    dragging = False
                    pinch = None
            elif FM is not None and e.type == FM and e.finger_id in fingers:
                fingers[e.finger_id] = (e.x * W, e.y * H, now)
                if len(fingers) >= 2:
                    multi_t = now
                    vals = list(fingers.values())[:2]
                    (x1, y1, _t1), (x2, y2, _t2) = vals
                    dist = math.hypot(x2 - x1, y2 - y1)
                    mid = ((x1 + x2) / 2.0, (y1 + y2) / 2.0)
                    if pinch and pinch[0] > 5:
                        puz.zoom_at(dist / pinch[0], mid[0], mid[1])
                        puz.pan_px(mid[0] - pinch[1][0], mid[1] - pinch[1][1])
                        puz.dirty = True
                    pinch = (dist, mid)
            elif FU is not None and e.type == FU:
                fingers.pop(e.finger_id, None)
                if len(fingers) < 2:
                    pinch = None
                if not fingers:
                    multi = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if getattr(e, "button", 1) in (4, 5):
                    puz.zoom_at(1.18 if e.button == 4 else 1 / 1.18, e.pos[0], e.pos[1])
                    puz.dirty = True
                    continue
                pos = e.pos
                if inside_btn(pos, AR_BACK, BTN_R):
                    sfx.play("click", save.sound)
                    return "home"
                elif inside_btn(pos, AR_HEX, SOUND_R):
                    save.sound = not save.sound
                    save.write()
                    sfx.play("click", save.sound)
                elif inside_btn(pos, AR_RESTART, BTN_R):
                    sfx.play("click", save.sound)
                    return "restart"
                elif inside_btn(pos, AR_ZIN, BTN_R):
                    puz.zoom_at(1.4, ARA.centerx, ARA.centery)
                    puz.dirty = True
                elif inside_btn(pos, AR_ZOUT, BTN_R):
                    puz.zoom_at(1 / 1.4, ARA.centerx, ARA.centery)
                    puz.dirty = True
                elif inside_btn(pos, AR_FIT, BTN_R):
                    puz.reset_view()
                elif inside_btn(pos, AR_HINT, BTN_R):
                    if save.hints > 0:
                        if puz.hint(now):
                            save.hints -= 1
                            save.write()
                            sfx.play("hint", save.sound)
                            puz.dirty = True
                    else:
                        sfx.play("hit", save.sound)
                        show_message("Hint khatam! Kal subah 6 baje milega", (255, 200, 120), 1200)
                        last = pygame.time.get_ticks()
                elif ARA.collidepoint(pos):
                    down = pos
                    last_pos = pos
                    dragging = False
            elif e.type == pygame.MOUSEMOTION:
                if down is not None and not multi:
                    if not dragging and (abs(e.pos[0] - down[0]) > slop or abs(e.pos[1] - down[1]) > slop):
                        dragging = True
                    if dragging:
                        puz.pan_px(e.pos[0] - last_pos[0], e.pos[1] - last_pos[1])
                    last_pos = e.pos
            elif e.type == pygame.MOUSEBUTTONUP:
                if getattr(e, "button", 1) in (4, 5):
                    continue
                if down is not None and not dragging and not multi and now - multi_t > 220:
                    res = puz.tap(e.pos, now)
                    if res == "ok":
                        sfx.step(8, save.sound)
                    elif res == "hit":
                        flash_until = now + 150
                        sfx.play("hit", save.sound)
                    elif res == "lose":
                        flash_until = now + 150
                        sfx.play("lose", save.sound)
                        save.ar_streak = 0
                        save.write()
                        arrow_frame(puz, save, now, flash_until)
                        show_message("Try again!", (255, 200, 120))
                        return "restart"
                if dragging:
                    puz.dirty = True
                down = None
                dragging = False
                if len(fingers) < 2:
                    multi = False
        puz.update(dt)
        arrow_frame(puz, save, now, flash_until, panning=dragging)
        if puz.solved():
            sfx.play("win", save.sound)
            reward = 0
            if spec["kind"] == "level" and spec["level"] == save.ar_level:
                reward = 1
                save.ar_level = spec["level"] + 1
            elif spec["kind"] == "daily" and save.ar_daily != day_token():
                reward = 3
                save.ar_daily = day_token()
            save.bonus += reward
            save.ar_streak += 1
            save.write()
            return arrow_result(puz, save, sfx, reward)
        clock.tick(60)


# ---------------------------------------------------------------- lobby (Amaze GO jaisa)
def _ar_time_left():
    now = datetime.datetime.now()
    nxt = now.replace(hour=DAILY_HOUR, minute=0, second=0, microsecond=0)
    if nxt <= now:
        nxt += datetime.timedelta(days=1)
    mins = int((nxt - now).total_seconds() // 60)
    return "%dh%02dm" % (mins // 60, mins % 60)


def _draw_wifi_off(cx, cy, s, color):
    for k in (1, 2, 3):
        rr = int(s * k * 0.33)
        pygame.draw.arc(screen, color, (cx - rr, cy - rr, 2 * rr, 2 * rr), math.radians(45), math.radians(135), max(3, int(s * 0.09)))
    pygame.draw.circle(screen, color, (cx, cy), max(3, int(s * 0.07)))
    pygame.draw.line(screen, color, (cx - s * 0.5, cy - s * 0.6), (cx + s * 0.5, cy + s * 0.25), max(3, int(s * 0.1)))


def _draw_trophy(cx, cy, s):
    sil = (225, 228, 235)
    pygame.draw.rect(screen, (50, 50, 55), (cx - s * 0.5, cy + s * 0.55, s, s * 0.28))
    pygame.draw.polygon(screen, (80, 80, 90), [(cx - s * 0.32, cy + s * 0.55), (cx + s * 0.32, cy + s * 0.55),
                                               (cx + s * 0.18, cy + s * 0.2), (cx - s * 0.18, cy + s * 0.2)])
    draw_star(screen, cx - s * 0.1, cy - s * 0.05, s * 0.5, sil, (150, 150, 160))
    draw_star(screen, cx + s * 0.38, cy - s * 0.25, s * 0.3, sil, (150, 150, 160))
    draw_star(screen, cx + s * 0.2, cy - s * 0.62, s * 0.22, sil, (150, 150, 160))


def arrow_lobby(save, sfx, sel):
    """Return (choice, sel): 'play' / 'daily' / 'free' / 'back'."""
    sel = max(1, min(sel, save.ar_level))
    cw = int(W * 0.41)
    gap = int(W * 0.05)
    cx0 = int(W * 0.06)
    cy0 = int(H * 0.085)
    ch = int(H * 0.255)
    max_scroll = max(0, cw + gap - int(W * 0.35))
    scroll = 0.0
    avatar = (int(W * 0.06), int(H * 0.012), int(W * 0.12), int(W * 0.12))
    thumbs = {}
    cont = (int(W * 0.13), int(H * 0.757), int(W * 0.74), int(H * 0.076))
    strip_y = int(H * 0.70)
    home_pos = (W // 2, int(H * 0.915))
    down = None
    moved = False
    last_x = 0
    while True:
        daily_check(save, sfx)
        today = day_token()
        daily_done = (save.ar_daily == today)
        cards = []
        for i in range(3):
            cards.append((cx0 + i * (cw + gap) - int(scroll), cy0, cw, ch))
        btns = []
        for (x, y, w, h) in cards:
            btns.append((x + int(w * 0.07), y + int(h * 0.72), int(w * 0.86), int(h * 0.21)))
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                quit_game(save)
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "back", sel
            if e.type == pygame.MOUSEBUTTONDOWN:
                down = e.pos
                last_x = e.pos[0]
                moved = False
            if e.type == pygame.MOUSEMOTION and down is not None:
                if abs(e.pos[0] - down[0]) > int(unit * 0.025) and cy0 <= down[1] <= cy0 + ch:
                    moved = True
                if moved:
                    scroll = max(0, min(max_scroll, scroll - (e.pos[0] - last_x)))
                last_x = e.pos[0]
            if e.type == pygame.MOUSEBUTTONUP and down is not None:
                pos = e.pos
                if not moved:
                    if inside_rect(pos, btns[0]):
                        sfx.play("hit", save.sound)
                        show_message("Glory League ke liye internet chahiye", (255, 200, 120), 1300)
                    elif inside_rect(pos, btns[1]):
                        sfx.play("click", save.sound)
                        return "daily", sel
                    elif inside_rect(pos, btns[2]):
                        sfx.play("click", save.sound)
                        return "free", sel
                    elif inside_rect(pos, cont):
                        sfx.play("click", save.sound)
                        return "play", sel
                    elif inside_btn(pos, (int(W * 0.055), strip_y), int(unit * 0.045)):
                        sel = max(1, sel - 1)
                        sfx.play("click", save.sound)
                    elif inside_btn(pos, (int(W * 0.945), strip_y), int(unit * 0.045)):
                        sel = min(save.ar_level, sel + 1)
                        sfx.play("click", save.sound)
                    elif inside_btn(pos, AR_HEX, SOUND_R):
                        save.sound = not save.sound
                        save.write()
                        sfx.play("click", save.sound)
                    elif inside_btn(pos, home_pos, BTN_R):
                        sfx.play("click", save.sound)
                        return "back", sel
                down = None
                moved = False

        screen.fill(BG)
        draw_tiger(avatar, 1 + (save.ar_level - 1) // 10)
        pill = (int(W * 0.34), int(H * 0.018), int(W * 0.32), int(H * 0.04))
        rrect(screen, (236, 222, 192), pill, int(pill[3] * 0.5))
        dx, dy = pill[0] + int(pill[2] * 0.22), pill[1] + int(pill[3] * 0.5)
        rr = int(unit * 0.02)
        pygame.draw.circle(screen, DROP_ON, (dx, dy + rr // 2), rr)
        pygame.draw.polygon(screen, DROP_ON, [(dx, dy - rr * 2), (dx - rr, dy), (dx + rr, dy)])
        put_text(font_mid, str(save.hints), AR_BROWN, (pill[0] + int(pill[2] * 0.62), dy))
        draw_icon_hex(AR_HEX, save.sound)

        # cards
        gx, gy, gw, gh = cards[0]
        rrect(screen, (250, 160, 60), cards[0], int(unit * 0.04))
        put_text(font_mid, "Glory League", (255, 245, 225), (gx + gw // 2, gy + int(gh * 0.12)))
        tp = (gx + int(gw * 0.12), gy + int(gh * 0.2), int(gw * 0.45), int(gh * 0.1))
        rrect(screen, (235, 135, 50), tp, int(tp[3] * 0.5))
        put_text(font_small, _ar_time_left(), (255, 245, 225), (tp[0] + tp[2] // 2, tp[1] + tp[3] // 2))
        _draw_wifi_off(gx + gw // 2, gy + int(gh * 0.5), int(gw * 0.34), (255, 225, 175))
        rrect(screen, (250, 240, 220), btns[0], int(unit * 0.03))
        put_text(font_mid, "Play", AR_BROWN, (btns[0][0] + btns[0][2] // 2, btns[0][1] + btns[0][3] // 2))

        dx0, dy0, dw, dh = cards[1]
        rrect(screen, (205, 85, 65), cards[1], int(unit * 0.04))
        put_text(font_mid, "Daily Challenge", (255, 240, 225), (dx0 + dw // 2, dy0 + int(dh * 0.12)))
        d_now = datetime.date.today()
        put_text(font_big, "%s %d" % (MONTHS[d_now.month - 1], d_now.day), (255, 245, 230), (dx0 + int(dw * 0.3), dy0 + int(dh * 0.3)))
        _draw_trophy(dx0 + int(dw * 0.72), dy0 + int(dh * 0.5), int(dw * 0.34))
        rrect(screen, (250, 232, 210), btns[1], int(unit * 0.03))
        put_text(font_mid, "Replay" if daily_done else "Start", (190, 70, 50), (btns[1][0] + btns[1][2] // 2, btns[1][1] + btns[1][3] // 2))

        fx, fy, fw, fh = cards[2]
        if fx < W:
            rrect(screen, (110, 185, 90), cards[2], int(unit * 0.04))
            pygame.draw.circle(screen, (255, 225, 110), (fx + int(fw * 0.75), fy + int(fh * 0.3)), int(fw * 0.12))
            put_text(font_mid, "Free Art", (255, 255, 240), (fx + fw // 2, fy + int(fh * 0.12)))
            pygame.draw.rect(screen, (80, 150, 70), (fx, fy + int(fh * 0.55), fw, int(fh * 0.2)))
            rrect(screen, (245, 250, 230), btns[2], int(unit * 0.03))
            put_text(font_mid, "Play", (60, 130, 60), (btns[2][0] + btns[2][2] // 2, btns[2][1] + btns[2][3] // 2))

        # beech ka hissa: title + agle level ki tasveer
        put_text(font_logo, "ARROWVERSE", (160, 140, 115), (W // 2, int(H * 0.405)))
        key = sel
        if key not in thumbs:
            sp = ar_spec_level(sel)
            thumbs[key] = ar_thumb(ar_canvas(sp["scene"], 40, sp["flip"], sp["shift"]), int(W * 0.46), int(H * 0.2))
        th = thumbs[key]
        screen.blit(th, th.get_rect(center=(W // 2, int(H * 0.54))))
        put_text(font_small, AR_SCENES[ar_spec_level(sel)["scene"]][0], (160, 140, 115), (W // 2, int(H * 0.65)))

        # level patti
        rrect(screen, (236, 220, 190), (int(W * 0.1), strip_y - int(H * 0.022), int(W * 0.8), int(H * 0.044)), int(H * 0.022))
        for k in range(5):
            lv = sel + k
            px = int(W * (0.185 + 0.157 * k))
            locked = lv > save.ar_level
            if k == 0:
                pygame.draw.circle(screen, AR_PURPLE, (px, strip_y), int(W * 0.054))
                put_text(font_mid, str(lv), (255, 255, 255), (px, strip_y))
            else:
                col = (200, 180, 150) if locked else AR_BROWN
                pygame.draw.circle(screen, col, (px, strip_y), int(W * 0.04))
                put_text(font_small, str(lv), (255, 245, 225), (px, strip_y))
        if sel > 1:
            put_text(font_big, "<", AR_BROWN, (int(W * 0.055), strip_y))
        if sel < save.ar_level:
            put_text(font_big, ">", AR_BROWN, (int(W * 0.945), strip_y))

        rrect(screen, AR_PURPLE, cont, int(unit * 0.035))
        put_text(font_big, "Continue", (255, 245, 255), (cont[0] + cont[2] // 2, cont[1] + int(cont[3] * 0.36)))
        put_text(font_small, "Level %d" % sel, (205, 180, 225), (cont[0] + cont[2] // 2, cont[1] + int(cont[3] * 0.74)))
        badge = (int(W * 0.67), int(H * 0.737), int(W * 0.27), int(H * 0.037))
        rrect(screen, (232, 140, 40), badge, int(badge[3] * 0.5))
        draw_crown(badge[0] + int(badge[2] * 0.16), badge[1] + badge[3] // 2, int(badge[3] * 0.3), (255, 215, 80))
        put_text(font_small, "x%d Win" % save.ar_streak, (255, 250, 235), (badge[0] + int(badge[2] * 0.6), badge[1] + badge[3] // 2))

        draw_icon_home(home_pos)
        put_text(font_small, "Home", WALL, (home_pos[0], home_pos[1] + BTN_R + int(unit * 0.035)))
        pygame.display.flip()
        clock.tick(60)


def arrow_screen(save, sfx):
    sel = save.ar_level
    while True:
        choice, sel = arrow_lobby(save, sfx, sel)
        if choice == "back":
            return
        if choice == "daily":
            spec = ar_spec_daily(day_token())
        elif choice == "free":
            spec = ar_spec_free()
        else:
            spec = ar_spec_level(sel)
        while True:
            act = arrow_play(save, sfx, spec)
            if act == "restart":
                continue
            if act == "next":
                if spec["kind"] == "level":
                    sel = min(spec["level"] + 1, save.ar_level)
                    spec = ar_spec_level(sel)
                    continue
                if spec["kind"] == "free":
                    spec = ar_spec_free()
                    continue
            break


# ======================================================================
#  MAIN
# ======================================================================
_load_pos = [0.0]


def startup_loading(target, text, ms=450):
    """Game shuru hone ki loading screen: khopdi + MAZEMASTER + bharti hui patti."""
    start = _load_pos[0]
    t0 = pygame.time.get_ticks()
    while True:
        k = min(1.0, (pygame.time.get_ticks() - t0) / float(max(1, ms)))
        frac = start + (target - start) * k
        screen.fill(BG)
        cy = int(H * 0.36)
        bob = int(math.sin(pygame.time.get_ticks() / 220.0) * unit * 0.012)
        draw_skull(screen, W // 2, cy - int(unit * 0.16) + bob, int(unit * 0.11))
        put_text(font_logo, "MAZEMASTER", GOLD, (W // 2, cy + int(unit * 0.08)))
        bw, bh = int(W * 0.7), max(10, int(H * 0.022))
        bx, by = (W - bw) // 2, int(H * 0.62)
        rrect(screen, (222, 205, 170), (bx, by, bw, bh), bh // 2)
        fw = max(bh, int(bw * frac))
        rrect(screen, GOLD_STAR, (bx, by, fw, bh), bh // 2)
        put_text(font_mid, text, WALL, (W // 2, by + int(H * 0.06)))
        put_text(font_small, "%d%%" % int(frac * 100), (150, 125, 95), (W // 2, by + int(H * 0.105)))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        clock.tick(60)
        if k >= 1.0:
            break
    _load_pos[0] = target


def main():
    startup_loading(0.25, "Game khul raha hai...")
    save = Save()
    startup_loading(0.6, "Progress load ho raha hai...")
    sfx = Sfx()
    startup_loading(0.9, "Awaaz taiyar ho rahi hai...")
    startup_loading(1.0, "Tayyar!", 350)
    try:
        run(save, sfx)
    finally:
        save.write()          # app band ho ya phone background me jaye, progress save rahe


def run(save, sfx):
    state = "home"
    cur = 1
    while True:
        if state == "home":
            choice = home_screen(save, sfx)
            if choice == "normal":
                state = "levels"
            elif choice == "hardcore":
                state = "hardcore"
            elif choice == "pacman":
                pacman_screen(save, sfx)
            elif choice == "arrows":
                arrow_screen(save, sfx)
            elif choice == "shop":
                shop_screen(save, sfx)

        elif state == "levels":
            lv = level_select(save, sfx)
            if lv is None:
                state = "home"
            else:
                cur = lv
                state = "normal_play"

        elif state == "normal_play":
            act = play_level(save, sfx, "normal", cur)
            if act == "next" and cur + 1 <= min(save.level, TOTAL_LEVELS):
                cur += 1
            elif act == "restart":
                pass
            elif act == "levels" or act == "next":
                state = "levels"
            else:
                state = "home"

        elif state == "hardcore":
            act = play_level(save, sfx, "hardcore", save.hc_level)
            if act == "over":
                state = "hardcore" if hc_over_screen(save, sfx, save.last_cleared) == "retry" else "home"
            elif act != "next":
                state = "home"


if __name__ == "__main__":
    main()
