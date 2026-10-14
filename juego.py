import pygame, random

# ============================================================
#  OPERACION FRONTERA - estrategia por turnos
#  Tu eres el Gobierno. Defiende la Capital, recupera las
#  regiones de los cárteles (ficticios) y cuida el apoyo popular.
# ============================================================

pygame.init()
W, H = 960, 540
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Operación Frontera")
clock = pygame.time.Clock()
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]


def text(t, size, color, x, y, center=False):
    img = font(size).render(t, True, color)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    screen.blit(img, r)


def wrap(t, size, maxw):
    lines, cur = [], ""
    for w in t.split():
        test = (cur + " " + w).strip()
        if font(size).size(test)[0] <= maxw:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------- MAPA ----------------
NAMES = ["Frontera Norte", "Sierra Alta", "Valle Seco", "Costa Pacífico",
         "Mesa Central", "Puerto Gris", "Cañón Rojo", "Capital",
         "Selva Sur", "Costa Golfo", "Altiplano", "Istmo"]
POS = [(170, 120), (360, 105), (550, 125), (80, 250),
       (270, 235), (470, 245), (610, 270), (330, 360),
       (110, 400), (520, 385), (230, 470), (450, 470)]
INCOME = [3, 2, 3, 2, 3, 3, 2, 4, 2, 3, 2, 2]
URBAN = {0, 5, 7, 9}
EDGES = [(0, 1), (0, 3), (0, 4), (1, 2), (1, 4), (2, 5), (2, 6), (3, 4),
         (3, 8), (4, 5), (4, 7), (5, 6), (5, 7), (5, 9), (6, 9), (7, 8),
         (7, 9), (7, 10), (8, 10), (9, 11), (10, 11)]
CAPITAL = 7
ADJ = {i: set() for i in range(12)}
for a, b in EDGES:
    ADJ[a].add(b)
    ADJ[b].add(a)

# dueños: 0 = Gobierno, 1 = Los Halcones, 2 = Los Costeños, -1 = neutral
OWN_NAMES = {0: "Gobierno", 1: "Los Halcones", 2: "Los Costeños", -1: "Sin control"}
COLORS = {0: (50, 120, 230), 1: (210, 60, 60), 2: (225, 140, 40), -1: (110, 115, 130)}


def new_game():
    return dict(
        owner=[1, 1, 1, 1, 0, 2, 2, 0, -1, 2, 0, 2],
        troops=[4, 3, 3, 3, 5, 3, 3, 8, 2, 3, 4, 3],
        turn=1, money=8, support=70, sel=None, tgt=None, odds=None,
        mode="todo", state="play", msg="",
        log=["Defiende la Capital y libera el país.",
             "Elige tu región y toca una vecina dos veces para mover o atacar."])


def say(g, t):
    g["log"].append(t)
    g["log"] = g["log"][-14:]


def income(g, who):
    base = sum(INCOME[i] for i in range(12) if g["owner"][i] == who)
    if who == 0:
        return max(1, round(base * (0.5 + g["support"] / 200)))
    return int(base * 0.7)


def battle(a, d):
    # cada duelo: dados de 1 a 6, el defensor gana los empates
    while a > 0 and d > 0:
        if random.randint(1, 6) > random.randint(1, 6):
            d -= 1
        else:
            a -= 1
    return a, d


def est_odds(n, d):
    wins = 0
    for _ in range(300):
        if battle(n, d)[0] > 0:
            wins += 1
    return int(wins * 100 / 300)


def do_send(g, src, dst, n):
    who = g["owner"][src]
    g["troops"][src] -= n
    if g["owner"][dst] == who:
        g["troops"][dst] += n
        return "move"
    a, d = battle(n, g["troops"][dst])
    if a > 0:
        g["owner"][dst] = who
        g["troops"][dst] = a
        return "win"
    g["troops"][dst] = d
    return "lose"


def check_end(g):
    if g["state"] != "play":
        return
    if g["owner"][CAPITAL] != 0:
        g["state"], g["msg"] = "lose", "Los cárteles tomaron la Capital."
    elif g["support"] <= 0:
        g["state"], g["msg"] = "lose", "El pueblo perdió la confianza en tu gobierno."
    elif not any(o in (1, 2) for o in g["owner"]):
        g["state"], g["msg"] = "win", "Los cárteles fueron derrotados."


def player_action(g, src, dst):
    n = g["troops"][src] - 1
    if g["mode"] == "mitad":
        n = max(1, n // 2)
    old = g["owner"][dst]
    res = do_send(g, src, dst, n)
    if res == "move":
        say(g, "Moviste %d tropas a %s." % (n, NAMES[dst]))
    else:
        if dst in URBAN:
            g["support"] -= 3
            say(g, "Daño colateral en zona urbana: -3 de apoyo.")
        if res == "win":
            g["support"] += 4 if old != -1 else 2
            say(g, "¡Tomaste %s!" % NAMES[dst])
        else:
            say(g, "Ataque fallido en %s." % NAMES[dst])
    g["support"] = max(0, min(100, g["support"]))
    check_end(g)
    return res


def enemy_turn(g):
    for who in (1, 2):
        regs = [i for i in range(12) if g["owner"][i] == who]
        if not regs:
            continue

        def hostile(i):
            return [j for j in ADJ[i] if g["owner"][j] != who]

        # ataques
        for i in regs:
            if g["owner"][i] != who or g["troops"][i] < 3:
                continue
            tg = hostile(i)
            if not tg:
                continue
            j = min(tg, key=lambda k: g["troops"][k])
            n, d = g["troops"][i] - 1, g["troops"][j]
            if n > d * 1.4 or (n > d and random.random() < 0.25):
                old = g["owner"][j]
                res = do_send(g, i, j, n)
                if old == 0:
                    if res == "win":
                        g["support"] -= 6
                        say(g, "%s tomó %s. -6 de apoyo." % (OWN_NAMES[who], NAMES[j]))
                    else:
                        say(g, "Repeliste el ataque en %s." % NAMES[j])
                elif res == "win":
                    say(g, "%s tomó %s." % (OWN_NAMES[who], NAMES[j]))

        # reclutar en la frontera
        budget = income(g, who)
        border = [i for i in regs if hostile(i)]
        while budget >= 3 and border:
            g["troops"][random.choice(border)] += 1
            budget -= 3
        # tropas del interior se acercan al frente
        for i in regs:
            if not hostile(i) and g["troops"][i] > 1:
                friends = [j for j in ADJ[i] if g["owner"][j] == who]
                near = [j for j in friends if hostile(j)] or friends
                if near:
                    do_send(g, i, random.choice(near), g["troops"][i] - 1)


def end_turn(g):
    enemy_turn(g)
    g["turn"] += 1
    if sum(1 for o in g["owner"] if o == 0) >= 6:
        g["support"] += 1
    r = random.random()
    mine = [i for i in range(12) if g["owner"][i] == 0 and g["troops"][i] > 1]
    if r < 0.12:
        g["money"] += 5
        say(g, "Inteligencia: decomisaste un cargamento (+5).")
    elif r < 0.22:
        g["money"] = max(0, g["money"] - 3)
        say(g, "Corrupción en el presupuesto (-3).")
    elif r < 0.30 and mine:
        i = random.choice(mine)
        g["troops"][i] -= 1
        say(g, "Deserción en %s (-1 soldado)." % NAMES[i])
    elif r < 0.36:
        g["support"] += 5
        say(g, "Campaña social exitosa (+5 de apoyo).")
    g["money"] += income(g, 0)
    g["support"] = max(0, min(100, g["support"]))
    g["sel"], g["tgt"], g["odds"] = None, None, None
    check_end(g)


# ---------------- INTERFAZ ----------------
BTN_REC = pygame.Rect(715, 175, 230, 44)
BTN_MODE = pygame.Rect(715, 227, 230, 38)
BTN_END = pygame.Rect(715, 273, 230, 48)


def region_at(pos):
    for i, (x, y) in enumerate(POS):
        if (pos[0] - x) ** 2 + (pos[1] - y) ** 2 <= 36 * 36:
            return i
    return None


def refresh_odds(g):
    g["odds"] = None
    s, t = g["sel"], g["tgt"]
    if s is not None and t is not None and g["owner"][t] != 0:
        n = g["troops"][s] - 1
        if g["mode"] == "mitad":
            n = max(1, n // 2)
        g["odds"] = est_odds(n, g["troops"][t])


def click(g, pos):
    if g["state"] != "play":
        g.clear()
        g.update(new_game())
        return
    if BTN_REC.collidepoint(pos):
        s = g["sel"]
        if s is not None and g["owner"][s] == 0 and g["money"] >= 3:
            g["money"] -= 3
            g["troops"][s] += 1
            refresh_odds(g)
        return
    if BTN_MODE.collidepoint(pos):
        g["mode"] = "mitad" if g["mode"] == "todo" else "todo"
        refresh_odds(g)
        return
    if BTN_END.collidepoint(pos):
        end_turn(g)
        return
    j = region_at(pos)
    if j is None:
        if pos[0] < 700:
            g["sel"], g["tgt"], g["odds"] = None, None, None
        return
    s = g["sel"]
    if s is not None and g["owner"][s] == 0 and j in ADJ[s] and g["troops"][s] > 1:
        if g["tgt"] == j:
            player_action(g, s, j)
            g["tgt"], g["odds"] = None, None
            if g["state"] == "play" and g["owner"][j] == 0:
                g["sel"] = j
        else:
            g["tgt"] = j
            refresh_odds(g)
    else:
        g["sel"], g["tgt"], g["odds"] = j, None, None


def button(rect, label, enabled=True, color=(50, 90, 170)):
    pygame.draw.rect(screen, color if enabled else (45, 48, 65), rect, border_radius=8)
    text(label, 24, (255, 255, 255) if enabled else (120, 125, 145),
         rect.centerx, rect.centery, True)


def draw(g):
    screen.fill((14, 16, 30))
    pygame.draw.rect(screen, (24, 28, 50), (0, 0, W, 50))
    text("Turno %d" % g["turn"], 28, (255, 255, 255), 12, 15)
    text("Presupuesto: %d (+%d)" % (g["money"], income(g, 0)), 28, (120, 230, 140), 150, 15)
    sp = g["support"]
    sc = (120, 230, 140) if sp >= 40 else (255, 200, 60) if sp >= 20 else (255, 90, 90)
    text("Apoyo popular: %d%%" % sp, 28, sc, 430, 15)

    for a, b in EDGES:
        pygame.draw.line(screen, (60, 70, 100), POS[a], POS[b], 3)

    s, t = g["sel"], g["tgt"]
    valid = set()
    if s is not None and g["owner"][s] == 0 and g["troops"][s] > 1:
        valid = ADJ[s]
    for i, (x, y) in enumerate(POS):
        if i in valid:
            pygame.draw.circle(screen, (255, 230, 80), (x, y), 39, 3)
        if i == t:
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 43, 4)
        pygame.draw.circle(screen, COLORS[g["owner"][i]], (x, y), 33)
        pygame.draw.circle(screen, (10, 10, 20), (x, y), 33, 3)
        if i == s:
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 37, 4)
        text(str(g["troops"][i]), 34, (255, 255, 255), x, y, True)
        text(NAMES[i], 18, (210, 215, 230), x, y + 46, True)

    # panel lateral
    pygame.draw.rect(screen, (24, 28, 50), (700, 50, 260, 490))
    if s is None:
        text("Toca una región", 26, (220, 220, 240), 715, 65)
        for k, ln in enumerate(wrap("Azul = tuyas. Cada ciudad dañada en combate baja el apoyo popular.", 20, 230)):
            text(ln, 20, (170, 175, 195), 715, 95 + k * 20)
    else:
        o = g["owner"][s]
        text(NAMES[s], 28, (255, 255, 255), 715, 62)
        text(OWN_NAMES[o], 24, COLORS[o], 715, 92)
        text("Tropas: %d   Ingreso: %d" % (g["troops"][s], INCOME[s]), 22, (210, 215, 230), 715, 120)
        if s in URBAN:
            text("Zona urbana (-3 apoyo al atacar)", 18, (255, 200, 60), 715, 146)
    mine = s is not None and g["owner"][s] == 0
    button(BTN_REC, "Reclutar +1  (3)", mine and g["money"] >= 3)
    button(BTN_MODE, "Enviar: " + ("todas" if g["mode"] == "todo" else "mitad"), True, (70, 75, 110))
    button(BTN_END, "Fin de turno", True, (30, 140, 80))

    # info del objetivo
    if t is not None and s is not None:
        if g["owner"][t] == 0:
            msg = "Mover tropas a %s. Toca de nuevo para confirmar." % NAMES[t]
        else:
            msg = "Atacar %s: %d%% de victoria. Toca de nuevo para confirmar." % (NAMES[t], g["odds"] or 0)
        for k, ln in enumerate(wrap(msg, 18, 235)[:3]):
            text(ln, 18, (255, 230, 120), 715, 330 + k * 19)

    # registro
    lines = []
    for entry in reversed(g["log"]):
        for ln in reversed(wrap(entry, 18, 235)):
            lines.append(ln)
        if len(lines) >= 7:
            break
    lines = list(reversed(lines[:7]))
    for k, ln in enumerate(lines):
        text(ln, 18, (170, 175, 195), 715, 392 + k * 20)

    if g["state"] != "play":
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 190))
        screen.blit(ov, (0, 0))
        win = g["state"] == "win"
        text("¡VICTORIA!" if win else "DERROTA", 80, (120, 230, 140) if win else (255, 90, 90), W // 2, 190, True)
        text(g["msg"], 30, (255, 255, 255), W // 2, 265, True)
        text("Turnos: %d    Apoyo popular: %d%%" % (g["turn"], g["support"]), 26, (200, 205, 220), W // 2, 315, True)
        text("Toca para jugar de nuevo", 30, (255, 230, 120), W // 2, 400, True)


def main():
    g = new_game()
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                click(g, e.pos)
        draw(g)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
