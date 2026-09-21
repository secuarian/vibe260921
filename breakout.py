import tkinter as tk

WIDTH, HEIGHT = 480, 600
PADDLE_W, PADDLE_H = 90, 12
BALL_R = 8
ROWS, COLS = 6, 10
BRICK_W = WIDTH // COLS
BRICK_H = 22
COLORS = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#3498db", "#9b59b6"]
FPS_MS = 16


class Breakout:
    def __init__(self, root):
        self.root = root
        root.title("블럭깨기")
        root.resizable(False, False)
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#111")
        self.canvas.pack()
        self.left = self.right = False
        root.bind("<KeyPress-Left>", lambda e: setattr(self, "left", True))
        root.bind("<KeyRelease-Left>", lambda e: setattr(self, "left", False))
        root.bind("<KeyPress-Right>", lambda e: setattr(self, "right", True))
        root.bind("<KeyRelease-Right>", lambda e: setattr(self, "right", False))
        root.bind("<Motion>", self.on_mouse)
        root.bind("<space>", self.on_space)
        root.bind("<KeyPress-p>", self.toggle_pause)
        root.bind("<KeyPress-P>", self.toggle_pause)
        self.new_game()
        self.loop()

    def new_game(self):
        self.canvas.delete("all")
        self.score = 0
        self.lives = 3
        self.level_speed = 5
        self.state = "ready"  # ready, playing, over, won
        self.bricks = {}
        for r in range(ROWS):
            for c in range(COLS):
                x1, y1 = c * BRICK_W, 50 + r * BRICK_H
                item = self.canvas.create_rectangle(
                    x1 + 1, y1 + 1, x1 + BRICK_W - 1, y1 + BRICK_H - 1,
                    fill=COLORS[r % len(COLORS)], outline="")
                self.bricks[item] = True
        px = (WIDTH - PADDLE_W) / 2
        self.paddle = self.canvas.create_rectangle(
            px, HEIGHT - 40, px + PADDLE_W, HEIGHT - 40 + PADDLE_H,
            fill="#ecf0f1", outline="")
        self.ball = self.canvas.create_oval(0, 0, BALL_R * 2, BALL_R * 2,
                                            fill="#fff", outline="")
        self.hud = self.canvas.create_text(10, 10, anchor="nw", fill="#fff",
                                           font=("Arial", 14), text="")
        self.msg = self.canvas.create_text(WIDTH / 2, HEIGHT / 2, fill="#fff",
                                           font=("Arial", 18, "bold"), text="")
        self.reset_ball()

    def reset_ball(self):
        p = self.canvas.coords(self.paddle)
        cx = (p[0] + p[2]) / 2
        self.canvas.coords(self.ball, cx - BALL_R, p[1] - BALL_R * 2,
                           cx + BALL_R, p[1])
        self.dx, self.dy = self.level_speed * 0.7, -self.level_speed
        self.state = "ready"
        self.canvas.itemconfig(self.msg, text="스페이스바로 시작\n← → 또는 마우스로 이동")
        self.update_hud()

    def update_hud(self):
        self.canvas.itemconfig(self.hud, text=f"점수: {self.score}   목숨: {self.lives}")

    def on_space(self, _):
        if self.state == "ready":
            self.state = "playing"
            self.canvas.itemconfig(self.msg, text="")
        elif self.state in ("over", "won"):
            self.new_game()

    def toggle_pause(self, _=None):
        if self.state == "playing":
            self.state = "paused"
            self.canvas.itemconfig(self.msg, text="일시정지\nP를 눌러 계속")
        elif self.state == "paused":
            self.state = "playing"
            self.canvas.itemconfig(self.msg, text="")

    def on_mouse(self, e):
        if self.state in ("ready", "playing"):
            self.move_paddle_to(e.x - PADDLE_W / 2)

    def move_paddle_to(self, x):
        x = max(0, min(WIDTH - PADDLE_W, x))
        self.canvas.coords(self.paddle, x, HEIGHT - 40, x + PADDLE_W, HEIGHT - 40 + PADDLE_H)
        if self.state == "ready":
            self.reset_ball_position()

    def reset_ball_position(self):
        p = self.canvas.coords(self.paddle)
        cx = (p[0] + p[2]) / 2
        self.canvas.coords(self.ball, cx - BALL_R, p[1] - BALL_R * 2,
                           cx + BALL_R, p[1])

    def loop(self):
        if self.state in ("ready", "playing"):
            if self.left:
                self.move_paddle_to(self.canvas.coords(self.paddle)[0] - 8)
            if self.right:
                self.move_paddle_to(self.canvas.coords(self.paddle)[0] + 8)
        if self.state == "playing":
            self.step()
        self.root.after(FPS_MS, self.loop)

    def step(self):
        self.canvas.move(self.ball, self.dx, self.dy)
        x1, y1, x2, y2 = self.canvas.coords(self.ball)

        if x1 <= 0:
            self.dx = abs(self.dx)
        elif x2 >= WIDTH:
            self.dx = -abs(self.dx)
        if y1 <= 0:
            self.dy = abs(self.dy)

        # 패들 충돌: 맞은 위치에 따라 반사 각도 변경
        px1, py1, px2, py2 = self.canvas.coords(self.paddle)
        if self.dy > 0 and y2 >= py1 and y1 <= py2 and x2 >= px1 and x1 <= px2:
            offset = ((x1 + x2) / 2 - (px1 + px2) / 2) / (PADDLE_W / 2)
            speed = (self.dx ** 2 + self.dy ** 2) ** 0.5
            self.dx = offset * speed * 0.8
            self.dy = -abs((speed ** 2 - self.dx ** 2) ** 0.5)
            self.canvas.move(self.ball, 0, py1 - y2)

        # 벽돌 충돌
        for item in self.canvas.find_overlapping(x1, y1, x2, y2):
            if item in self.bricks:
                bx1, by1, bx2, by2 = self.canvas.coords(item)
                overlap_x = min(x2, bx2) - max(x1, bx1)
                overlap_y = min(y2, by2) - max(y1, by1)
                if overlap_x < overlap_y:
                    self.dx = -self.dx
                else:
                    self.dy = -self.dy
                self.canvas.delete(item)
                del self.bricks[item]
                self.score += 10
                self.update_hud()
                break

        if not self.bricks:
            self.state = "won"
            self.canvas.itemconfig(self.msg, text="클리어! 🎉\n스페이스바로 다시 시작")
        elif y1 > HEIGHT:
            self.lives -= 1
            self.update_hud()
            if self.lives <= 0:
                self.state = "over"
                self.canvas.itemconfig(self.msg, text="게임 오버\n스페이스바로 다시 시작")
            else:
                self.reset_ball()


if __name__ == "__main__":
    root = tk.Tk()
    Breakout(root)
    root.mainloop()
