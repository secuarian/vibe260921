import tkinter as tk
import random
from collections import deque

CELL = 20
COLS = 30
ROWS = 20
SPEED = 110  # ms per move

DIRS = {
    "Up": (0, -1),
    "Down": (0, 1),
    "Left": (-1, 0),
    "Right": (1, 0),
}
OPPOSITE = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}


def inside(p):
    return 0 <= p[0] < COLS and 0 <= p[1] < ROWS


def neighbors(p):
    for name, (dx, dy) in DIRS.items():
        q = (p[0] + dx, p[1] + dy)
        if inside(q):
            yield name, q


def flood_area(start, blocked, limit):
    """start에서 도달 가능한 빈 칸 수 (limit에 도달하면 조기 종료)."""
    seen = {start}
    queue = deque([start])
    while queue and len(seen) < limit:
        cur = queue.popleft()
        for _, nxt in neighbors(cur):
            if nxt not in seen and nxt not in blocked:
                seen.add(nxt)
                queue.append(nxt)
    return len(seen)


def bfs_first_step(start, goal, blocked, forbidden_dir):
    """start에서 goal까지 최단 경로의 첫 방향을 반환. 없으면 None."""
    queue = deque()
    seen = {start}
    for name, nxt in neighbors(start):
        if name == forbidden_dir or nxt in blocked:
            continue
        seen.add(nxt)
        queue.append((nxt, name))
    while queue:
        cur, first = queue.popleft()
        if cur == goal:
            return first
        for _, nxt in neighbors(cur):
            if nxt not in seen and nxt not in blocked:
                seen.add(nxt)
                queue.append((nxt, first))
    return None


class SnakeGame:
    def __init__(self, root):
        self.root = root
        root.title("Snake: YOU vs AI")
        root.resizable(False, False)
        self.canvas = tk.Canvas(
            root, width=COLS * CELL, height=ROWS * CELL, bg="#111"
        )
        self.canvas.pack()
        root.bind("<Key>", self.on_key)
        self.reset()
        self.tick()

    def reset(self):
        # 사람: 아래쪽 왼쪽에서 오른쪽으로 / AI: 위쪽 오른쪽에서 왼쪽으로
        self.human = [(5 - i, ROWS - 6) for i in range(3)]
        self.ai = [(COLS - 6 + i, 5) for i in range(3)]
        self.human_dir = self.human_pending = "Right"
        self.ai_dir = "Left"
        self.human_score = 0
        self.ai_score = 0
        self.game_over = False
        self.paused = False
        self.result = ""
        self.place_food()
        self.draw()

    def place_food(self):
        taken = set(self.human) | set(self.ai)
        free = [
            (x, y)
            for x in range(COLS)
            for y in range(ROWS)
            if (x, y) not in taken
        ]
        self.food = random.choice(free)

    def on_key(self, event):
        key = event.keysym
        if key in DIRS:
            if key != OPPOSITE[self.human_dir]:
                self.human_pending = key
        elif key in ("space", "p", "P"):
            if not self.game_over:
                self.paused = not self.paused
                self.draw()
        elif key in ("r", "R", "Return") and self.game_over:
            self.reset()

    # ---------------- AI ----------------
    def choose_ai_direction(self):
        head = self.ai[0]
        body_block = set(self.ai[:-1]) | set(self.human[:-1])
        hx, hy = self.human[0]
        # 사람 머리가 다음 턴에 갈 수 있는 칸 (정면충돌 회피용)
        danger = {q for _, q in neighbors((hx, hy))}
        forbidden = OPPOSITE[self.ai_dir]

        def is_safe(direction, blocked):
            dx, dy = DIRS[direction]
            nxt = (head[0] + dx, head[1] + dy)
            if not inside(nxt) or nxt in blocked:
                return False
            # 이동 후 갇히지 않는지 확인 (도달 가능한 칸 >= 몸 길이)
            after = blocked | {nxt}
            return flood_area(nxt, after, len(self.ai) + 1) >= len(self.ai)

        # 1) 위험칸까지 피하며 사과로 가는 최단 경로
        for blocked in (body_block | danger, body_block):
            step = bfs_first_step(head, self.food, blocked, forbidden)
            if step and is_safe(step, blocked):
                return step

        # 2) 사과 경로가 불가능하면 가장 넓은 공간으로 이동
        best, best_area = None, -1
        for name, nxt in neighbors(head):
            if name == forbidden or nxt in body_block:
                continue
            area = flood_area(nxt, body_block | {nxt}, COLS * ROWS)
            if nxt in danger:
                area -= 3
            if area > best_area:
                best, best_area = name, area
        return best or self.ai_dir

    # ---------------- 게임 루프 ----------------
    def tick(self):
        if not self.game_over and not self.paused:
            self.step()
            self.draw()
        self.root.after(SPEED, self.tick)

    def step(self):
        self.human_dir = self.human_pending
        self.ai_dir = self.choose_ai_direction()

        def next_head(snake, d):
            dx, dy = DIRS[d]
            return (snake[0][0] + dx, snake[0][1] + dy)

        h_head = next_head(self.human, self.human_dir)
        a_head = next_head(self.ai, self.ai_dir)
        h_ate = h_head == self.food
        a_ate = a_head == self.food

        new_human = [h_head] + (self.human if h_ate else self.human[:-1])
        new_ai = [a_head] + (self.ai if a_ate else self.ai[:-1])

        h_dead = (
            not inside(h_head)
            or h_head in new_human[1:]
            or h_head in new_ai
        )
        a_dead = (
            not inside(a_head)
            or a_head in new_ai[1:]
            or a_head in new_human
        )

        self.human, self.ai = new_human, new_ai
        if h_ate and not h_dead:
            self.human_score += 10
        if a_ate and not a_dead:
            self.ai_score += 10

        if h_dead or a_dead:
            self.game_over = True
            if h_dead and a_dead:
                if self.human_score > self.ai_score:
                    self.result = "둘 다 충돌 - YOU 승리 (점수)"
                elif self.ai_score > self.human_score:
                    self.result = "둘 다 충돌 - AI 승리 (점수)"
                else:
                    self.result = "무승부"
            elif h_dead:
                self.result = "AI 승리!"
            else:
                self.result = "YOU 승리!"
            return

        if h_ate or a_ate:
            self.place_food()

    def draw_snake(self, snake, head_color, body_color):
        for i, (x, y) in enumerate(snake):
            self.canvas.create_rectangle(
                x * CELL + 1, y * CELL + 1,
                (x + 1) * CELL - 1, (y + 1) * CELL - 1,
                fill=head_color if i == 0 else body_color, outline="",
            )

    def draw(self):
        c = self.canvas
        c.delete("all")
        fx, fy = self.food
        c.create_oval(
            fx * CELL + 2, fy * CELL + 2,
            (fx + 1) * CELL - 2, (fy + 1) * CELL - 2,
            fill="#e33", outline="",
        )
        self.draw_snake(self.human, "#7f7", "#3a3")
        self.draw_snake(self.ai, "#8cf", "#37b")
        c.create_text(
            8, 8, anchor="nw", fill="#7f7",
            font=("Malgun Gothic", 11, "bold"), text=f"YOU: {self.human_score}",
        )
        c.create_text(
            COLS * CELL - 8, 8, anchor="ne", fill="#8cf",
            font=("Malgun Gothic", 11, "bold"), text=f"AI: {self.ai_score}",
        )
        cx, cy = COLS * CELL // 2, ROWS * CELL // 2
        if self.game_over:
            c.create_text(
                cx, cy, fill="white", justify="center",
                font=("Malgun Gothic", 18, "bold"),
                text=(
                    f"GAME OVER\n{self.result}\n"
                    f"YOU {self.human_score} : {self.ai_score} AI\n"
                    "R / Enter: 재시작"
                ),
            )
        elif self.paused:
            c.create_text(
                cx, cy, fill="white",
                font=("Malgun Gothic", 20, "bold"), text="PAUSED",
            )


if __name__ == "__main__":
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()
