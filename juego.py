import pygame, random, math, sys, os, array, threading, heapq

# ============================================================
#  OPERACION FRONTERA  -  estrategia por turnos en hexagonos
#  Region: Sonoyta - Penasco - Caborca - Mexicali - San Luis R.C.
#  Obra de ficcion: no representa hechos reales.
# ============================================================

pygame.mixer.pre_init(11025, -16, 1, 512)
pygame.init()
W, H = 960, 540
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Operación Frontera")
clock = pygame.time.Clock()
canvas = screen
_fonts = {}


def font(sz):
    if sz not in _fonts:
        _fonts[sz] = pygame.font.SysFont(None, sz)
    return _fonts[sz]


def text(t, sz, col, x, y, center=False, shadow=False):
    if shadow:
        text(t, sz, (0, 0, 0), x + 1, y + 1, center)
    img = font(sz).render(t, True, col)
    r = img.get_rect()
    if center:
        r.center = (int(x), int(y))
    else:
        r.topleft = (int(x), int(y))
    canvas.blit(img, r)


def wrap(t, sz, maxw):
    lines, cur = [], ""
    for w in t.split():
        test = (cur + " " + w).strip()
        if font(sz).size(test)[0] <= maxw:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def circ(col, x, y, r, w=0):
    pygame.draw.circle(canvas, col, (int(x), int(y)), max(1, int(r)), w)


def rect(col, x, y, w, h, width=0, rad=0):
    pygame.draw.rect(canvas, col, (int(x), int(y), max(1, int(w)), max(1, int(h))), width, border_radius=rad)


def line(col, x1, y1, x2, y2, w=1):
    pygame.draw.line(canvas, col, (int(x1), int(y1)), (int(x2), int(y2)), max(1, int(w)))


def poly(col, pts, w=0):
    pygame.draw.polygon(canvas, col, [(int(a), int(b)) for a, b in pts], w)


# ---------------- DATOS ----------------
COLS, ROWS = 13, 10
MAP = [
    "XXXXXXXXXXXXX",
    "CvcCcXXXXXXXX",
    "vvrvdcccXXXXX",
    "mdrvdDDccCdXX",
    "mmr~CpDDmccdd",
    "mm~~~~pDcmcdd",
    "mm~~~~~Ccddcm",
    "mm~~~~~~ccccC",
    "mm~~~~~~~pdCv",
    "mm~~~~~~~~pdv",
]
CITIES = {(0, 1): "Mexicali", (3, 1): "San Luis R.C.", (4, 4): "Golfo S. Clara",
          (9, 3): "Sonoyta", (7, 6): "Pto. Peñasco", (11, 8): "Caborca", (12, 7): "Altar"}
START_OWN = {(0, 1): 1, (3, 1): 1, (4, 4): 1, (9, 3): 2, (11, 8): 2, (12, 7): 2, (7, 6): 0}
START_UNITS = [
    (0, (7, 6), ["INF", "INF", "TRK", "TNK", "ART"]),
    (1, (0, 1), ["INF", "TNK"]), (1, (3, 1), ["INF", "TRK"]), (1, (4, 4), ["INF"]),
    (2, (9, 3), ["INF", "TNK"]), (2, (11, 8), ["INF", "TRK"]), (2, (12, 7), ["INF"]),
]
KINDS = ["INF", "TRK", "TNK", "ART"]
KI = {k: i for i, k in enumerate(KINDS)}
# mov, ataque, defensa, PV, alcance, costo
ST = {"INF": (2, 4, 4, 10, 1, 3), "TRK": (4, 4, 2, 8, 1, 4),
      "TNK": (2, 8, 8, 16, 1, 8), "ART": (1, 7, 2, 7, 2, 6)}
FCOL = [(50, 120, 230), (210, 55, 55), (235, 170, 40)]
FS = ["Gobierno", "Sinaloa", "Los Salazar"]
FN = ["Ejército y Guardia Nacional", "Cártel de Sinaloa", "Los Salazar"]
UN = [
    {"INF": "Infantería", "TRK": "Humvee artillado", "TNK": "Blindado ERC-90", "ART": "Mortero pesado"},
    {"INF": "Sicarios", "TRK": "Camioneta artillada", "TNK": "Narco-tanque", "ART": "Lanzagranadas"},
    {"INF": "Sicarios Salazar", "TRK": "Troca blindada", "TNK": "Narco-tanque Salazar", "ART": "Lanzagranadas"},
]
FDESC = [
    "Presupuesto federal: +5 por turno. La infantería defiende mejor en las ciudades. Empiezas solo con Puerto Peñasco, pero con tropas profesionales y blindados.",
    "Cada ciudad te da +1 de ingreso extra y los narco-tanques cuestan 1 menos. Controlas Mexicali, San Luis Río Colorado y el Golfo de Santa Clara.",
    "Conocen el desierto: moverse por desierto y dunas les cuesta 1 menos. Controlan Sonoyta, Caborca y Altar.",
]
# costo de movimiento por terreno: INF, TRK, TNK, ART (99 = no pasa)
COST = {"c": (1, 1, 1, 1), "C": (1, 1, 1, 1), "v": (1, 1, 1, 1), "d": (1, 2, 2, 1),
        "p": (1, 2, 2, 1), "D": (2, 3, 4, 2), "r": (2, 3, 4, 2), "m": (2, 3, 99, 2)}
DEFB = {"c": 0, "C": 3, "v": 0, "d": 0, "p": 0, "D": 1, "r": -1, "m": 3}
TNAME = {"c": "Carretera", "C": "Ciudad", "v": "Valle agrícola", "d": "Desierto", "p": "Playa",
         "D": "Dunas del Gran Desierto", "r": "Río Colorado", "m": "Sierra",
         "~": "Golfo de California", "X": "Frontera con EE.UU."}
TCOL = {"~": (35, 80, 140), "X": (40, 42, 58), "d": (214, 190, 130), "D": (228, 205, 140),
        "m": (130, 120, 105), "v": (120, 170, 85), "r": (80, 150, 215), "c": (170, 165, 150),
        "p": (238, 225, 180), "C": (150, 150, 160)}
MAXU = 10

# ---------------- HEXAGONOS ----------------
R = 28
HW = 1.7320508 * R
HV = 1.5 * R
X0, Y0 = 44, 82


def hc(c, r):
    return (X0 + c * HW + (HW / 2 if r % 2 else 0), Y0 + r * HV)


def hex_pts(x, y, rr=R):
    return [(x + rr * math.cos(math.radians(60 * i - 30)), y + rr * math.sin(math.radians(60 * i - 30))) for i in range(6)]


def nbrs(c, r):
    if r % 2 == 0:
        d = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
    else:
        d = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]
    return [(c + a, r + b) for a, b in d if 0 <= c + a < COLS and 0 <= r + b < ROWS]


def hdist(a, b):
    def cube(c, r):
        x = c - (r - (r & 1)) // 2
        return x, -x - r, r
    ax, ay, az = cube(*a)
    bx, by, bz = cube(*b)
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))


def hex_at(pos):
    best, bd = None, (R * 0.95) ** 2
    for r in range(ROWS):
        for c in range(COLS):
            x, y = hc(c, r)
            d = (pos[0] - x) ** 2 + (pos[1] - y) ** 2
            if d < bd:
                best, bd = (c, r), d
    return best


# ---------------- LOGICA ----------------
class Unit:
    def __init__(s, k, f, c, r):
        s.k, s.f, s.c, s.r = k, f, c, r
        s.hp = ST[k][3]
        s.mp = ST[k][0]
        s.moved = False
        s.acted = False

    @property
    def pos(s):
        return (s.c, s.r)


def ua(g, p):
    for u in g["units"]:
        if u.c == p[0] and u.r == p[1]:
            return u
    return None


def log(g, f, t):
    g["events"].append((g["turn"], f, t))


def ucost(f, k):
    c = ST[k][5]
    if f == 1 and k == "TNK":
        c -= 1
    return c


def mcost(u, ch):
    c = COST[ch][KI[u.k]]
    if u.f == 2 and ch in "dD" and c < 99:
        c = max(1, c - 1)
    return c


def income(g, f):
    n = sum(1 for o in g["owner"].values() if o == f)
    if n == 0:
        return 0
    return 2 + n * (5 if f == 1 else 4) + (5 if f == 0 else 0)


def nunits(g, f):
    return sum(1 for u in g["units"] if u.f == f)


def new_game(pf):
    g = dict(player=pf, units=[], owner=dict(START_OWN), money=[10, 10, 10], turn=1,
             sel=None, scity=None, tgt=None, insp=None, reach={}, hexsel=None,
             events=[], st=[dict(des=0, per=0, dan=0, civ=0) for _ in range(3)],
             alive=[True, True, True], state="play", msg="", rep0=0, rscroll=0, rnew=False)
    for f, city, kinds in START_UNITS:
        free = [city]
        seen = {city}
        i = 0
        while i < len(free):
            for q in nbrs(*free[i]):
                if q not in seen and MAP[q[1]][q[0]] not in "X~":
                    seen.add(q)
                    free.append(q)
            i += 1
        for k in kinds:
            for p in free:
                if not ua(g, p):
                    g["units"].append(Unit(k, f, p[0], p[1]))
                    break
    log(g, pf, "Comienza la guerra por la frontera. Mandas: %s." % FN[pf])
    return g


def start_turn(g, f):
    inc = income(g, f)
    g["money"][f] += inc
    n = 0
    for u in g["units"]:
        if u.f != f:
            continue
        u.mp = ST[u.k][0]
        u.moved = False
        u.acted = False
        if g["owner"].get(u.pos) == f and u.hp < ST[u.k][3]:
            u.hp = min(ST[u.k][3], u.hp + 3)
            n += 1
    log(g, f, "%s: ingresos +%d (presupuesto %d)%s." % (
        FS[f], inc, g["money"][f], ", %d unidades se recuperan en sus ciudades" % n if n else ""))


def reach(g, u):
    full = ST[u.k][0]
    best = {u.pos: u.mp}
    heap = [(-u.mp, u.pos)]
    while heap:
        nr, p = heapq.heappop(heap)
        rem = -nr
        if best.get(p, -1) > rem:
            continue
        for q in nbrs(*p):
            ch = MAP[q[1]][q[0]]
            if ch in "X~":
                continue
            o = ua(g, q)
            if o and o.f != u.f:
                continue
            cost = mcost(u, ch)
            if cost >= 99 or (cost > rem and rem != full):
                continue
            n2 = max(0, rem - cost)
            if n2 > best.get(q, -1):
                best[q] = n2
                heapq.heappush(heap, (-n2, q))
    return {p: r for p, r in best.items() if p == u.pos or not ua(g, p)}


def in_range(u, t):
    if u.acted or (u.k == "ART" and u.moved):
        return False
    return 1 <= hdist(u.pos, t.pos) <= ST[u.k][4]


def dmg_calc(a, d, dpos=None, counter=False):
    p = dpos or d.pos
    td = MAP[p[1]][p[0]]
    power = ST[a.k][1] * (0.5 + 0.5 * a.hp / ST[a.k][3])
    res = ST[d.k][2] + DEFB.get(td, 0)
    if d.f == 0 and d.k == "INF" and td == "C":
        res += 1
    base = power * 10.0 / (10.0 + res)
    return base * 0.7 if counter else base


def remove_unit(g, u):
    if u in g["units"]:
        g["units"].remove(u)
    if g["sel"] is u:
        g["sel"], g["reach"] = None, {}
    if g["tgt"] is u:
        g["tgt"] = None
    if g["insp"] is u:
        g["insp"] = None


def attack(g, a, d):
    ta = TNAME[MAP[d.r][d.c]]
    dist = hdist(a.pos, d.pos)
    dm = max(1, round(dmg_calc(a, d) * random.uniform(0.8, 1.2)))
    d.hp -= dm
    g["st"][a.f]["dan"] += dm
    t = "%s (%s) ataca a %s (%s) en %s: -%d PV" % (UN[a.f][a.k], FS[a.f], UN[d.f][d.k], FS[d.f], ta, dm)
    if d.hp > 0 and dist <= ST[d.k][4]:
        cm = max(1, round(dmg_calc(d, a, counter=True) * random.uniform(0.8, 1.2)))
        a.hp -= cm
        g["st"][d.f]["dan"] += cm
        t += "; contraataque -%d PV" % cm
    a.acted = True
    a.mp = 0
    if d.hp <= 0:
        t += ". ¡%s destruido!" % UN[d.f][d.k]
        g["st"][a.f]["des"] += 1
        g["st"][d.f]["per"] += 1
        remove_unit(g, d)
    if a.hp <= 0:
        t += " El atacante también cae."
        g["st"][d.f]["des"] += 1
        g["st"][a.f]["per"] += 1
        remove_unit(g, a)
    log(g, a.f, t)


def move_unit(g, u, p, rem):
    u.c, u.r = p
    u.mp = 0 if u.k == "ART" else rem
    u.moved = True
    o = g["owner"].get(p)
    if o is not None and o != u.f:
        g["owner"][p] = u.f
        g["st"][u.f]["civ"] += 1
        log(g, u.f, "¡%s toma %s a %s!" % (FS[u.f], CITIES[p], FS[o]))


def recruit(g, f, k, pos):
    c = ucost(f, k)
    if g["money"][f] < c or ua(g, pos) or g["owner"].get(pos) != f or nunits(g, f) >= MAXU:
        return False
    u = Unit(k, f, pos[0], pos[1])
    u.acted = True
    u.mp = 0
    g["units"].append(u)
    g["money"][f] -= c
    log(g, f, "%s recluta %s en %s (-%d)." % (FS[f], UN[f][k], CITIES[pos], c))
    return True


def check_elim(g):
    for f in range(3):
        if g["alive"][f] and not any(o == f for o in g["owner"].values()):
            g["alive"][f] = False
            n = nunits(g, f)
            for u in [x for x in g["units"] if x.f == f]:
                remove_unit(g, u)
            log(g, f, "%s pierde su última ciudad y se desintegra (%d unidades)." % (FS[f], n))


def check_end(g):
    if g["state"] != "play":
        return
    p = g["player"]
    if not g["alive"][p]:
        g["state"], g["msg"] = "lose", "Perdiste todas tus ciudades."
    elif not any(g["alive"][f] for f in range(3) if f != p):
        g["state"], g["msg"] = "win", "¡Controlas toda la frontera!"


def ai_unit(g, u):
    if u not in g["units"] or u.acted:
        return
    foes = [x for x in g["units"] if x.f != u.f]
    tc = [p for p, o in g["owner"].items() if o != u.f]
    if not foes and not tc:
        return
    opts = reach(g, u)
    if u.hp <= ST[u.k][3] * 0.4 and g["owner"].get(u.pos) == u.f:
        opts = {u.pos: opts.get(u.pos, u.mp)}
    best = None
    for p, rem in opts.items():
        moved = p != u.pos
        base = DEFB.get(MAP[p[1]][p[0]], 0) * 0.4 + (7 if p in tc else 0)
        att = None
        if not (u.k == "ART" and moved):
            for t in foes:
                d = hdist(p, t.pos)
                if 1 <= d <= ST[u.k][4]:
                    dm = dmg_calc(u, t)
                    kill = dm >= t.hp
                    cn = 0 if (kill or d > ST[t.k][4]) else dmg_calc(t, u, dpos=p, counter=True)
                    val = dm + (6 if kill else 0) - 0.8 * cn
                    if att is None or val > att[0]:
                        att = (val, t)
        if att:
            sc = base + att[0] + 2
        else:
            dc = min([hdist(p, c) for c in tc] or [0])
            df = min([hdist(p, t.pos) for t in foes] or [0])
            sc = base - 0.6 * dc - 0.2 * df
        sc += random.random() * 0.3
        if best is None or sc > best[0]:
            best = (sc, p, rem, att[1] if att else None)
    if best is None:
        return
    _, p, rem, t = best
    if p != u.pos:
        move_unit(g, u, p, rem)
    if t is not None and t in g["units"] and in_range(u, t):
        attack(g, u, t)


def ai_turn(g, f):
    if not g["alive"][f]:
        return
    start_turn(g, f)
    cities = [p for p, o in g["owner"].items() if o == f and not ua(g, p)]
    random.shuffle(cities)
    w = {"INF": 4, "TRK": 3, "TNK": 3, "ART": 2}
    for p in cities:
        opts = [k for k in KINDS if ucost(f, k) <= g["money"][f]]
        if not opts or nunits(g, f) >= MAXU:
            break
        recruit(g, f, random.choices(opts, [w[k] for k in opts])[0], p)
    mine = [u for u in g["units"] if u.f == f]
    foes = [x for x in g["units"] if x.f != f]
    mine.sort(key=lambda u: min([hdist(u.pos, t.pos) for t in foes] or [0]))
    for u in mine:
        ai_unit(g, u)


def end_turn(g):
    p = g["player"]
    g["rep0"] = len(g["events"])
    for f in range(3):
        if f != p and g["state"] == "play":
            ai_turn(g, f)
            check_elim(g)
            check_end(g)
    if g["state"] == "play":
        g["turn"] += 1
        start_turn(g, p)
        g["sel"] = g["scity"] = g["tgt"] = g["insp"] = None
        g["reach"] = {}
    g["rscroll"] = 0
    g["rnew"] = True


# ---------------- SPRITES ----------------
def sprite(k, f, cx, cy, sc=1.0):
    col = FCOL[f]
    dk = tuple(int(v * 0.55) for v in col)
    lt = tuple(min(255, int(v * 1.25) + 20) for v in col)
    S = lambda v: v * sc
    blk = (35, 35, 42)
    if k == "INF":
        circ((228, 188, 150), cx, cy - S(8), S(4))
        rect(dk, cx - S(4), cy - S(13), S(8), S(4))
        rect(col, cx - S(5), cy - S(4), S(10), S(11))
        rect(blk, cx - S(4), cy + S(7), S(3), S(6))
        rect(blk, cx + S(1), cy + S(7), S(3), S(6))
        line(blk, cx - S(8), cy + S(3), cx + S(11), cy - S(5), max(2, S(2)))
    elif k == "TRK":
        rect(col, cx - S(16), cy - S(1), S(32), S(9))
        rect(dk, cx + S(3), cy - S(8), S(12), S(8))
        rect((175, 210, 235), cx + S(8), cy - S(7), S(5), S(5))
        line(blk, cx - S(7), cy - S(1), cx - S(7), cy - S(7), 2)
        line(blk, cx - S(7), cy - S(7), cx - S(16), cy - S(10), max(2, S(3)))
        circ(blk, cx - S(9), cy + S(9), S(4))
        circ(blk, cx + S(9), cy + S(9), S(4))
    elif k == "TNK":
        if f == 0:
            rect(col, cx - S(15), cy - S(3), S(30), S(9))
            rect(dk, cx - S(6), cy - S(10), S(14), S(8))
            line(blk, cx + S(8), cy - S(7), cx + S(21), cy - S(7), max(2, S(3)))
            for dx in (-11, -4, 4, 11):
                circ(blk, cx + S(dx), cy + S(8), S(3.5))
        else:
            rect((55, 55, 62), cx - S(17), cy + S(2), S(34), S(10), 0, 4)
            for dx in (-12, -4, 4, 12):
                circ((90, 90, 98), cx + S(dx), cy + S(7), S(3))
            rect(col, cx - S(14), cy - S(5), S(28), S(9))
            for dx in (-12, -3, 6):
                rect(lt, cx + S(dx), cy - S(4), S(6), S(7))
            rect(dk, cx - S(7), cy - S(12), S(14), S(8))
            line(blk, cx + S(7), cy - S(8), cx + S(21), cy - S(8), max(2, S(3)))
            poly(blk, [(cx + S(14), cy - S(5)), (cx + S(20), cy + S(1)), (cx + S(14), cy + S(2))])
    else:
        line((60, 60, 66), cx - S(4), cy + S(2), cx - S(15), cy + S(10), 3)
        line(blk, cx - S(4), cy + S(3), cx + S(14), cy - S(9), max(3, S(4)))
        poly(dk, [(cx - S(9), cy - S(2)), (cx + S(1), cy - S(7)), (cx + S(3), cy + S(5)), (cx - S(7), cy + S(5))])
        circ(blk, cx - S(4), cy + S(8), S(5))
        circ(col, cx - S(4), cy + S(8), S(2))


def draw_unit(u, x, y, mine=False):
    circ((245, 245, 245), x, y - 1, 19)
    circ(FCOL[u.f], x, y - 1, 19, 3)
    sprite(u.k, u.f, x, y - 1, 0.8)
    mh = ST[u.k][3]
    fr = max(0.0, u.hp / mh)
    rect((20, 20, 25), x - 16, y + 17, 32, 6)
    rect((90, 220, 100) if fr > 0.6 else (240, 200, 60) if fr > 0.3 else (240, 70, 70), x - 15, y + 18, 30 * fr, 4)
    if mine and (u.acted or (u.mp == 0 and u.moved)):
        circ((30, 30, 40), x - 16, y - 16, 4)


# ---------------- MUSICA ----------------
MUSIC = None
MUSIC_FILE = None
MUSIC_ON = True
AUDIO = False
MPLAY = False


def find_music():
    dirs = [os.getcwd()]
    if getattr(sys, "frozen", False):
        dirs.append(os.path.dirname(sys.executable))
    if hasattr(sys, "_MEIPASS"):
        dirs.append(sys._MEIPASS)
    for d in dirs:
        for n in ("musica.ogg", "musica.mp3", "musica.wav"):
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


def build_song():
    global MUSIC
    try:
        freq, fmt, ch = pygame.mixer.get_init()
        if fmt != -16:
            return
        SR = freq
        beat = 60.0 / 126.0
        eighth = beat / 2
        bars = 16
        total = int(SR * beat * 2 * bars)
        buf = [0.0] * total

        def note(t0, dur, midi, vol, wave):
            f = 440.0 * 2 ** ((midi - 69) / 12.0)
            s0, n = int(t0 * SR), int(dur * SR)
            att = max(1, int(0.008 * SR))
            for i in range(n):
                j = s0 + i
                if j >= total:
                    break
                t = i / SR
                ph = (t * f) % 1.0
                if wave == 0:
                    v = (0.55 if ph < 0.5 else -0.55) + (0.45 if (t * f * 1.006) % 1.0 < 0.5 else -0.45)
                elif wave == 1:
                    v = 4 * abs(ph - 0.5) - 1
                else:
                    v = 2 * ph - 1
                e = min(1.0, i / att)
                if i > n * 0.7:
                    e *= (n - i) / (n * 0.3)
                buf[j] += v * e * vol

        def noise(t0, dur, vol):
            s0, n = int(t0 * SR), int(dur * SR)
            for i in range(n):
                j = s0 + i
                if j >= total:
                    break
                buf[j] += (random.random() * 2 - 1) * vol * (1 - i / n)

        def kick(t0, vol):
            s0, n = int(t0 * SR), int(0.12 * SR)
            for i in range(n):
                j = s0 + i
                if j >= total:
                    break
                k = 1 - i / n
                buf[j] += math.sin(2 * math.pi * 55 * (i / SR) * (1 + k)) * k * vol

        A = [69, 72, 76, 72, 69, 71, 72, 69, 74, 77, 81, 77, 74, 76, 77, 74,
             76, 80, 83, 80, 76, 77, 80, 76, 81, 76, 72, 76, 69, 69, 0, 0]
        B = [76, 77, 76, 72, 69, 72, 76, 72, 74, 77, 81, 77, 74, 72, 74, 77,
             76, 80, 83, 80, 76, 74, 72, 71, 69, 72, 76, 81, 81, 0, 69, 0]
        mel = A + B
        prog = ["Am", "Am", "Dm", "Dm", "E", "E", "Am", "Am"] * 2
        CH = {"Am": (45, 52, (57, 60, 64)), "Dm": (50, 57, (62, 65, 69)), "E": (52, 59, (64, 68, 71))}
        for b in range(bars):
            t0 = b * beat * 2
            root, fifth, stab = CH[prog[b]]
            note(t0, beat * 0.9, root, 0.30, 1)
            note(t0 + beat, beat * 0.9, fifth, 0.28, 1)
            kick(t0, 0.35)
            kick(t0 + beat, 0.25)
            for k in range(2):
                ts = t0 + k * beat + eighth
                for m in stab:
                    note(ts, eighth * 0.85, m, 0.06, 2)
                noise(ts, 0.05, 0.12)
            for k in range(4):
                m = mel[b * 4 + k]
                if m:
                    note(t0 + k * eighth, eighth * 0.92, m, 0.16, 0)
        mx = max(max(buf), -min(buf), 1e-6)
        sc = 0.85 * 32767 / mx
        data = array.array("h")
        for v in buf:
            s = int(v * sc)
            data.append(s)
            if ch == 2:
                data.append(s)
        MUSIC = pygame.mixer.Sound(buffer=data.tobytes())
        MUSIC.set_volume(0.5)
    except Exception:
        MUSIC = None


def init_audio():
    global AUDIO, MUSIC_FILE
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(11025, -16, 1, 512)
        AUDIO = bool(pygame.mixer.get_init())
    except Exception:
        AUDIO = False
    if not AUDIO:
        return
    f = find_music()
    if f:
        try:
            pygame.mixer.music.load(f)
            pygame.mixer.music.set_volume(0.6)
            MUSIC_FILE = f
            return
        except Exception:
            MUSIC_FILE = None
    threading.Thread(target=build_song, daemon=True).start()


def sync_music():
    global MPLAY
    if not AUDIO:
        return
    try:
        if MUSIC_FILE:
            if MUSIC_ON and not MPLAY:
                pygame.mixer.music.play(-1)
                MPLAY = True
            elif not MUSIC_ON and MPLAY:
                pygame.mixer.music.stop()
                MPLAY = False
        elif MUSIC is not None:
            if MUSIC_ON and not MPLAY:
                MUSIC.play(-1)
                MPLAY = True
            elif not MUSIC_ON and MPLAY:
                MUSIC.stop()
                MPLAY = False
    except Exception:
        pass


# ---------------- TERRENO PRE-DIBUJADO ----------------
TERR = None


def build_terrain():
    global canvas, TERR
    TERR = pygame.Surface((W, H))
    canvas = TERR
    canvas.fill((10, 16, 30))
    for r in range(ROWS):
        for c in range(COLS):
            ch = MAP[r][c]
            x, y = hc(c, r)
            poly(TCOL[ch], hex_pts(x, y))
            poly((25, 30, 45), hex_pts(x, y), 1)
            if ch == "m":
                poly((150, 140, 130), [(x - 9, y + 7), (x - 1, y - 8), (x + 7, y + 7)])
                poly((235, 235, 240), [(x - 4, y - 1), (x - 1, y - 8), (x + 2, y - 1)])
            elif ch == "D":
                for k in (-6, 0, 6):
                    line((190, 160, 95), x - 9, y + k, x - 3, y + k - 3, 2)
                    line((190, 160, 95), x - 3, y + k - 3, x + 3, y + k, 2)
                    line((190, 160, 95), x + 3, y + k, x + 9, y + k - 3, 2)
            elif ch == "v":
                for k in (-9, -3, 3, 9):
                    line((70, 120, 50), x + k, y - 6, x + k, y + 6, 2)
            elif ch == "r":
                pts = [(x - 10, y - 3), (x - 3, y + 3), (x + 4, y - 3), (x + 10, y + 3)]
                for a, b in zip(pts, pts[1:]):
                    line((40, 100, 190), a[0], a[1], b[0], b[1], 3)
            elif ch == "X":
                line((58, 60, 78), x - 10, y + 8, x + 10, y - 8, 1)
    for r in range(ROWS):
        for c in range(COLS):
            if MAP[r][c] in "cC":
                x, y = hc(c, r)
                for q in nbrs(c, r):
                    if q > (c, r) and MAP[q[1]][q[0]] in "cC":
                        x2, y2 = hc(*q)
                        line((95, 90, 85), x, y, x2, y2, 4)
    x, y = hc(6, 0)
    text("EE. UU.", 22, (120, 125, 150), x, y, True)
    x, y = hc(4, 7)
    text("Golfo de California", 18, (140, 180, 235), x, y, True)
    x, y = hc(6, 3)
    text("Gran Desierto", 14, (120, 95, 50), x, y + 14, True)
    canvas = screen


# ---------------- INTERFAZ ----------------
STATE = "menu"
G = None
RUN = True
B_END = pygame.Rect(715, 326, 230, 44)
B_REP = pygame.Rect(715, 378, 112, 36)
B_MENU = pygame.Rect(833, 378, 112, 36)
B_MUS = pygame.Rect(850, 8, 100, 34)
RECR = [pygame.Rect(708, 206, 120, 54), pygame.Rect(834, 206, 120, 54),
        pygame.Rect(708, 266, 120, 54), pygame.Rect(834, 266, 120, 54)]
B_SUB = pygame.Rect(30, 488, 120, 40)
B_BAJ = pygame.Rect(160, 488, 120, 40)
B_CER = pygame.Rect(780, 488, 150, 40)
B_BACK = pygame.Rect(20, 498, 110, 34)
HELP = [
    "OBJETIVO: controla las 7 ciudades de la frontera, o deja a tus dos rivales sin ciudades.",
    "1. Toca una unidad tuya: en verde se marcan los hexágonos a donde puede moverse y en rojo los enemigos que puede atacar.",
    "2. Toca un hexágono verde para mover. Toca un enemigo en rojo para ver el pronóstico y tócalo otra vez para atacar.",
    "3. Toca una ciudad tuya vacía para reclutar unidades. Cada ciudad te da ingresos cada turno y cura a las unidades que estén en ella.",
    "4. Terreno: la sierra y las ciudades dan defensa extra. Dunas, río y sierra frenan a los vehículos y los tanques no cruzan la sierra.",
    "5. La artillería tiene alcance 2 pero no puede moverse y atacar en el mismo turno.",
    "6. Al terminar tu turno juegan los otros dos bandos y recibes un informe detallado de lo que pasó.",
    "MÚSICA: si pones un archivo musica.mp3 junto al .exe, el juego lo usa en lugar de la melodía incluida.",
]


def menu_items():
    it = []
    if G and G["state"] == "play":
        it.append(("CONTINUAR", "cont"))
    it += [("JUGAR", "play"), ("CÓMO JUGAR", "help"),
           ("MÚSICA: " + ("SÍ" if MUSIC_ON else "NO"), "mus"), ("SALIR", "quit")]
    return it


def menu_rect(i):
    return pygame.Rect(330, 200 + i * 66, 300, 54)


def card_rect(i):
    return pygame.Rect(30 + i * 305, 66, 290, 420)


def button(rc, label, enabled=True, col=(50, 90, 170), sz=26):
    rect(col if enabled else (45, 48, 65), rc.x, rc.y, rc.w, rc.h, 0, 8)
    text(label, sz, (255, 255, 255) if enabled else (120, 125, 145), rc.centerx, rc.centery, True)


def backdrop(alpha=185):
    screen.blit(TERR, (0, 0))
    ov = pygame.Surface((W, H), pygame.SRCALPHA)
    ov.fill((5, 8, 18, alpha))
    screen.blit(ov, (0, 0))


def draw_menu():
    backdrop(170)
    text("OPERACIÓN FRONTERA", 74, (235, 190, 70), W // 2, 78, True, True)
    text("Sonoyta · Peñasco · Caborca · Mexicali · San Luis Río Colorado", 24, (210, 215, 230), W // 2, 135, True, True)
    text("Estrategia por turnos en el desierto de Sonora", 22, (160, 170, 195), W // 2, 162, True, True)
    for i, (lab, act) in enumerate(menu_items()):
        button(menu_rect(i), lab, True, (30, 140, 80) if act in ("play", "cont") else (50, 70, 120), 28)
    text("Obra de ficción. Los hechos y las unidades son ficticios.", 16, (150, 155, 175), W // 2, 522, True)


def draw_help():
    backdrop(215)
    text("CÓMO JUGAR", 44, (235, 190, 70), W // 2, 44, True)
    y = 84
    for ln in HELP:
        for s in wrap(ln, 22, 880):
            text(s, 22, (225, 228, 240), 40, y)
            y += 25
        y += 8
    text("Toca la pantalla para volver", 24, (255, 230, 120), W // 2, 515, True)


def draw_factions():
    backdrop(200)
    text("ELIGE TU FACCIÓN", 36, (235, 190, 70), W // 2, 36, True)
    for i in range(3):
        rc = card_rect(i)
        rect((24, 28, 48), rc.x, rc.y, rc.w, rc.h, 0, 10)
        rect(FCOL[i], rc.x, rc.y, rc.w, 54, 0, 10)
        text(FN[i], 25, (255, 255, 255), rc.centerx, rc.y + 27, True, True)
        y = rc.y + 66
        for s in wrap(FDESC[i], 19, 266):
            text(s, 19, (215, 220, 235), rc.x + 12, y)
            y += 21
        text("Unidades:", 20, (255, 230, 120), rc.x + 12, rc.y + 258)
        for j, k in enumerate(KINDS):
            cx = rc.x + 18 + (j % 2) * 138
            cy = rc.y + 290 + (j // 2) * 62
            circ((245, 245, 245), cx + 20, cy + 22, 21)
            circ(FCOL[i], cx + 20, cy + 22, 21, 3)
            sprite(k, i, cx + 20, cy + 22, 0.95)
            for n, s in enumerate(wrap(UN[i][k], 15, 84)[:2]):
                text(s, 15, (225, 228, 240), cx + 46, cy + 8 + n * 15)
        text("TOCA PARA ELEGIR", 22, (255, 255, 255), rc.centerx, rc.y + 406, True)
    button(B_BACK, "Atrás", True, (60, 65, 95), 22)


def draw_report():
    g = G
    backdrop(225)
    text("INFORME DE GUERRA  -  Turno %d" % g["turn"], 34, (235, 190, 70), W // 2, 30, True)
    heads = ["Facción", "Ciudades", "Unidades", "Ingreso", "Destruidas", "Pérdidas", "Daño"]
    xs = [40, 270, 380, 490, 590, 710, 820]
    for h, x in zip(heads, xs):
        text(h, 22, (180, 190, 215), x, 64)
    for f in range(3):
        y = 92 + f * 28
        st = g["st"][f]
        nc = sum(1 for o in g["owner"].values() if o == f)
        vals = [FS[f] + (" (tú)" if f == g["player"] else ""), nc, nunits(g, f), "+%d" % income(g, f),
                st["des"], st["per"], st["dan"]]
        if not g["alive"][f]:
            vals[0] += " (eliminado)"
        for v, x in zip(vals, xs):
            text(str(v), 22, FCOL[f] if x == 40 else (230, 232, 245), x, y)
    text("Ciudades:  " + "   ".join("%s: %s" % (n, FS[g["owner"][p]]) for p, n in CITIES.items()), 15, (160, 170, 195), 40, 182)
    text("Eventos (lo más nuevo abajo):", 22, (255, 230, 120), 40, 204)
    lines = []
    for i, (t, f, tx) in enumerate(g["events"]):
        new = g["rnew"] and i >= g["rep0"]
        base = FCOL[f]
        col = tuple(min(255, v + 70) for v in base) if new else tuple(int(v * 0.7) + 40 for v in base)
        for k, s in enumerate(wrap("T%d  %s" % (t, tx), 18, 890)):
            lines.append((("   " if k else "") + s, col))
    vis = 13
    end = len(lines) - g["rscroll"]
    start = max(0, end - vis)
    for n, (s, col) in enumerate(lines[start:end]):
        text(s, 18, col, 40, 228 + n * 19)
    button(B_SUB, "Subir", True, (60, 65, 95), 22)
    button(B_BAJ, "Bajar", True, (60, 65, 95), 22)
    button(B_CER, "Cerrar", True, (30, 140, 80), 24)


def draw_panel(g):
    p = g["player"]
    rect((24, 28, 48), 700, 50, 260, 490)
    h = g["hexsel"]
    if h:
        ch = MAP[h[1]][h[0]]
        nm = CITIES[h] + " (ciudad)" if h in CITIES else TNAME[ch]
        text(nm, 22, (255, 255, 255), 712, 56)
        if ch in "X~":
            inf = "Intransitable"
        else:
            cv = COST[ch][2]
            inf = "Def %+d  Mov: inf %d, veh %d%s" % (DEFB[ch], COST[ch][0], COST[ch][1], ", tanque: no" if cv >= 99 else "")
        text(inf, 16, (190, 195, 215), 712, 80)
    u = g["sel"] or g["insp"]
    if u:
        rect((34, 40, 70), 706, 100, 248, 98, 0, 6)
        circ((245, 245, 245), 740, 134, 28)
        circ(FCOL[u.f], 740, 134, 28, 4)
        sprite(u.k, u.f, 740, 134, 1.25)
        text(UN[u.f][u.k], 20, (255, 255, 255), 776, 106)
        text(FS[u.f], 18, FCOL[u.f], 776, 126)
        text("PV %d/%d   Mov %d/%d" % (u.hp, ST[u.k][3], u.mp, ST[u.k][0]), 17, (215, 220, 235), 712, 160)
        text("Atq %d  Def %d  Alc %d" % (ST[u.k][1], ST[u.k][2], ST[u.k][4]), 17, (215, 220, 235), 712, 178)
    if g["sel"] and g["tgt"]:
        a, t = g["sel"], g["tgt"]
        dm = max(1, round(dmg_calc(a, t)))
        msg = "Atacar %s: ~%d daño (le quedan %d PV)." % (UN[t.f][t.k], dm, max(0, t.hp - dm))
        if t.hp - dm > 0 and hdist(a.pos, t.pos) <= ST[t.k][4]:
            msg += " Contraataque ~%d." % max(1, round(dmg_calc(t, a, counter=True)))
        msg += " Toca de nuevo para confirmar."
        for n, s in enumerate(wrap(msg, 16, 240)[:5]):
            text(s, 16, (255, 230, 120), 712, 206 + n * 17)
    elif g["scity"]:
        for i, k in enumerate(KINDS):
            rc = RECR[i]
            c = ucost(p, k)
            ok = g["money"][p] >= c and nunits(g, p) < MAXU
            rect((50, 90, 170) if ok else (45, 48, 65), rc.x, rc.y, rc.w, rc.h, 0, 6)
            circ((245, 245, 245), rc.x + 22, rc.y + 27, 17)
            sprite(k, p, rc.x + 22, rc.y + 27, 0.7)
            for n, s in enumerate(wrap(UN[p][k], 14, 70)[:2]):
                text(s, 14, (255, 255, 255) if ok else (120, 125, 145), rc.x + 44, rc.y + 5 + n * 13)
            text("$%d" % c, 17, (255, 230, 120) if ok else (120, 125, 145), rc.x + 44, rc.y + 34)
    else:
        for n, s in enumerate(wrap("Toca una unidad tuya o una ciudad tuya vacía (para reclutar).", 17, 240)):
            text(s, 17, (160, 170, 195), 712, 208 + n * 18)
    button(B_END, "Fin de turno", True, (30, 140, 80), 26)
    button(B_REP, "Informe", True, (70, 75, 110), 22)
    button(B_MENU, "Menú", True, (70, 75, 110), 22)
    lines = []
    for t, f, tx in g["events"][-8:]:
        for k, s in enumerate(wrap(tx, 15, 240)):
            lines.append((s, tuple(min(255, v + 60) for v in FCOL[f])))
    for n, (s, col) in enumerate(lines[-6:]):
        text(s, 15, col, 712, 424 + n * 17)


def draw_game():
    g = G
    p = g["player"]
    screen.blit(TERR, (0, 0))
    s = g["sel"]
    if s and g["reach"]:
        for q in g["reach"]:
            if q != s.pos:
                x, y = hc(*q)
                poly((90, 235, 120), hex_pts(x, y, R - 3), 3)
    if s and not s.acted:
        for t in g["units"]:
            if t.f != p and in_range(s, t):
                x, y = hc(*t.pos)
                poly((255, 70, 70), hex_pts(x, y, R - 3), 3)
    if g["tgt"]:
        x, y = hc(*g["tgt"].pos)
        poly((255, 255, 255), hex_pts(x, y, R - 1), 4)
    if g["scity"]:
        x, y = hc(*g["scity"])
        poly((255, 230, 80), hex_pts(x, y, R - 2), 4)
    for pos, nm in CITIES.items():
        x, y = hc(*pos)
        o = g["owner"][pos]
        rect((70, 70, 80), x - 11, y - 5, 7, 12)
        rect((100, 100, 115), x - 3, y - 11, 8, 18)
        rect((70, 70, 80), x + 6, y - 2, 6, 9)
        circ((255, 255, 255), x + 15, y - 17, 9)
        circ(FCOL[o], x + 15, y - 17, 7)
        text(nm, 16, (255, 255, 255), x, y + R + 3, True, True)
    for u in g["units"]:
        x, y = hc(*u.pos)
        draw_unit(u, x, y, u.f == p)
    if s:
        x, y = hc(*s.pos)
        circ((255, 255, 255), x, y - 1, 22, 3)
    pygame.draw.rect(screen, (24, 28, 50), (0, 0, W, 50))
    text("Turno %d" % g["turn"], 26, (255, 255, 255), 12, 15)
    text(FS[p], 26, FCOL[p], 120, 15)
    text("Presupuesto: %d (+%d)" % (g["money"][p], income(g, p)), 26, (120, 230, 140), 280, 15)
    text("Ciudades: %d/7" % sum(1 for o in g["owner"].values() if o == p), 26, (230, 230, 245), 560, 15)
    button(B_MUS, "Música: " + ("SÍ" if MUSIC_ON else "NO"), True, (60, 65, 95), 20)
    draw_panel(g)
    if g["state"] != "play":
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 190))
        screen.blit(ov, (0, 0))
        win = g["state"] == "win"
        text("¡VICTORIA!" if win else "DERROTA", 84, (120, 230, 140) if win else (255, 90, 90), W // 2, 190, True)
        text(g["msg"], 30, (255, 255, 255), W // 2, 265, True)
        text("Turnos: %d    Ciudades: %d/7" % (g["turn"], sum(1 for o in g["owner"].values() if o == p)), 26, (200, 205, 220), W // 2, 315, True)
        text("Toca para volver al menú", 30, (255, 230, 120), W // 2, 400, True)


# ---------------- ENTRADA ----------------
def select(g, u):
    g["sel"], g["scity"], g["tgt"], g["insp"] = u, None, None, None
    g["reach"] = reach(g, u) if (u.f == g["player"] and not u.acted and u.mp > 0) else {}


def game_click(pos):
    global STATE, MUSIC_ON
    g = G
    p = g["player"]
    if g["state"] != "play":
        STATE = "menu"
        return
    if B_MUS.collidepoint(pos):
        MUSIC_ON = not MUSIC_ON
        return
    if B_END.collidepoint(pos):
        end_turn(g)
        STATE = "report"
        return
    if B_REP.collidepoint(pos):
        g["rnew"] = False
        g["rscroll"] = 0
        STATE = "report"
        return
    if B_MENU.collidepoint(pos):
        STATE = "menu"
        return
    if g["scity"]:
        for i, rc in enumerate(RECR):
            if rc.collidepoint(pos):
                if recruit(g, p, KINDS[i], g["scity"]):
                    g["scity"] = None
                return
    h = hex_at(pos)
    if h is None:
        if pos[0] < 700:
            g["sel"] = g["scity"] = g["tgt"] = g["insp"] = None
            g["reach"] = {}
        return
    g["hexsel"] = h
    u = ua(g, h)
    s = g["sel"]
    if s is not None:
        if u and u.f != p and in_range(s, u):
            if g["tgt"] is u:
                attack(g, s, u)
                g["tgt"] = None
                g["reach"] = {}
                check_elim(g)
                check_end(g)
            else:
                g["tgt"] = u
            return
        if u is None and h in g["reach"] and h != s.pos and not s.acted:
            move_unit(g, s, h, g["reach"][h])
            g["reach"] = reach(g, s) if s.mp > 0 else {}
            g["tgt"] = None
            return
    if u and u.f == p:
        select(g, u)
    elif u:
        g["insp"], g["sel"], g["scity"], g["tgt"] = u, None, None, None
        g["reach"] = {}
    elif g["owner"].get(h) == p:
        g["scity"], g["sel"], g["insp"], g["tgt"] = h, None, None, None
        g["reach"] = {}
    else:
        g["sel"] = g["scity"] = g["tgt"] = g["insp"] = None
        g["reach"] = {}


def on_click(pos):
    global STATE, G, MUSIC_ON, RUN
    if STATE == "menu":
        for i, (lab, act) in enumerate(menu_items()):
            if menu_rect(i).collidepoint(pos):
                if act == "cont":
                    STATE = "game"
                elif act == "play":
                    STATE = "fac"
                elif act == "help":
                    STATE = "help"
                elif act == "mus":
                    MUSIC_ON = not MUSIC_ON
                elif act == "quit":
                    RUN = False
    elif STATE == "help":
        STATE = "menu"
    elif STATE == "fac":
        if B_BACK.collidepoint(pos):
            STATE = "menu"
            return
        for i in range(3):
            if card_rect(i).collidepoint(pos):
                G = new_game(i)
                STATE = "game"
    elif STATE == "game":
        game_click(pos)
    elif STATE == "report":
        g = G
        if B_SUB.collidepoint(pos):
            g["rscroll"] += 6
        elif B_BAJ.collidepoint(pos):
            g["rscroll"] = max(0, g["rscroll"] - 6)
        elif B_CER.collidepoint(pos):
            STATE = "game"


def main():
    global RUN, STATE
    build_terrain()
    init_audio()
    while RUN:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                RUN = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                on_click(e.pos)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                STATE = "menu" if STATE != "menu" else STATE
        sync_music()
        if STATE == "menu":
            draw_menu()
        elif STATE == "help":
            draw_help()
        elif STATE == "fac":
            draw_factions()
        elif STATE == "report":
            draw_report()
        else:
            draw_game()
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
