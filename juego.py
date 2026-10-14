import pygame, random
pygame.init()
W, H = 800, 480
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Atrapa estrellas")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 40)

def reset():
    return {"x": W // 2, "items": [], "score": 0, "lives": 3, "t": 0}

s = reset()
running = True
while running:
    dt = clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.MOUSEBUTTONDOWN and s["lives"] <= 0:
            s = reset()
    if s["lives"] > 0:
        s["x"] = max(40, min(W - 40, pygame.mouse.get_pos()[0]))
        s["t"] += dt
        if s["t"] > max(250, 800 - s["score"] * 15):
            s["t"] = 0
            s["items"].append([random.randint(15, W - 15), 0, random.random() < 0.25])
        speed = 3 + s["score"] * 0.1
        for it in s["items"][:]:
            it[1] += speed
            if it[1] > H - 50 and abs(it[0] - s["x"]) < 50:
                s["items"].remove(it)
                if it[2]:
                    s["lives"] -= 1
                else:
                    s["score"] += 1
            elif it[1] > H:
                s["items"].remove(it)
                if not it[2]:
                    s["lives"] -= 1
    screen.fill((15, 15, 35))
    pygame.draw.rect(screen, (80, 200, 255), (s["x"] - 40, H - 40, 80, 20))
    for x, y, bomb in s["items"]:
        pygame.draw.circle(screen, (230, 40, 40) if bomb else (255, 220, 50), (int(x), int(y)), 15)
    screen.blit(font.render(f"Puntos: {s['score']}  Vidas: {max(s['lives'],0)}", True, (255, 255, 255)), (10, 10))
    if s["lives"] <= 0:
        screen.blit(font.render("GAME OVER - toca para reiniciar", True, (255, 255, 255)), (180, 220))
    pygame.display.flip()
pygame.quit()
