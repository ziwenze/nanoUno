from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

from .engine import (
    COLORS,
    COLOR_NAMES,
    MAX_AI_PLAYERS,
    MIN_AI_PLAYERS,
    PLAYER_HUMAN,
    Card,
    RuleError,
    UnoGame,
)

TABLE_BG = "#0f5d42"
PANEL_BG = "#144f3d"
TABLE_SURFACE = "#0c513b"
TABLE_INNER = "#0b4634"
SURFACE_BG = "#f3ead7"
TEXT_DARK = "#1f2933"
CARD_COLORS = {
    "red": ("#d94f45", "#fff7f0"),
    "yellow": ("#f1c84c", "#3d3113"),
    "green": ("#2f9d57", "#f5fff7"),
    "blue": ("#3772d6", "#f8fbff"),
    "wild": ("#2e3440", "#f8fafc"),
    "back": ("#43526a", "#f8fafc"),
}
AI_BACK_STYLE = {
    "shadow": "#0d2f25",
    "border": "#f7f2e6",
    "outer": "#1f3f90",
    "inner": "#0f2f6e",
    "red": "#d83f35",
    "gold": "#f0c24a",
    "green": "#2f9d57",
    "white": "#fffaf0",
    "text": "#1a1f2a",
}
CARD_TITLES = {
    "skip": "Skip",
    "reverse": "Rev",
    "draw_two": "+2",
    "wild": "Wild",
    "wild_draw_four": "W+4",
}
CARD_ACCENTS = {
    "red": "#a92f28",
    "yellow": "#c79a1c",
    "green": "#1e7a40",
    "blue": "#2057b9",
    "wild": "#1e2430",
}
HAND_VIEWPORT_HEIGHT = 220
PLAYER_CARD_WIDTH = 118
PLAYER_CARD_HEIGHT = 178
PLAYER_CARD_STEP = 86


class UnoApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("UNO - 多 AI 人机对战")
        self.geometry("1380x900")
        self.minsize(1180, 780)
        self.configure(bg=TABLE_BG)

        self.game = UnoGame(ai_count=1)
        self.ai_job: str | None = None
        self.started = False
        self.winner_announced = False

        self.status_var = tk.StringVar()
        self.turn_var = tk.StringVar()
        self.direction_var = tk.StringVar()
        self.color_var = tk.StringVar()
        self.deck_var = tk.StringVar()
        self.player_var = tk.StringVar()
        self.ai_var = tk.StringVar()
        self.ai_count_var = tk.StringVar()

        self.top_ai_frame: tk.Frame
        self.left_ai_frame: tk.Frame
        self.right_ai_frame: tk.Frame
        self.hand_frame: tk.Frame
        self.hand_canvas: tk.Canvas
        self.hand_window: int
        self.log: ScrolledText
        self.draw_button: tk.Canvas
        self.pass_button: tk.Canvas
        self.add_ai_button: tk.Button
        self.remove_ai_button: tk.Button
        self.discard_card: tk.Label
        self.current_color_badge: tk.Label
        self.start_overlay: tk.Frame
        self.start_overlay_hint: tk.Label
        self.hand_content_width = 0
        self.draw_action_enabled = False
        self.pass_action_enabled = False

        self._build_layout()
        self._show_start_overlay()
        self._refresh_pre_game_ui()

    def _build_layout(self) -> None:
        header = tk.Frame(self, bg=TABLE_BG)
        header.pack(fill="x", padx=18, pady=(18, 8))

        title_stack = tk.Frame(header, bg=TABLE_BG)
        title_stack.pack(side="left")
        tk.Label(
            title_stack,
            text="UNO",
            font=("Helvetica", 28, "bold"),
            fg="#f8fafc",
            bg=TABLE_BG,
        ).pack(anchor="w")
        tk.Label(
            title_stack,
            text="围桌布局，多 AI 人机对战",
            font=("Helvetica", 12),
            fg="#d1fae5",
            bg=TABLE_BG,
        ).pack(anchor="w")

        action_row = tk.Frame(header, bg=TABLE_BG)
        action_row.pack(side="right")
        self.remove_ai_button = tk.Button(
            action_row,
            text="减少 AI",
            command=lambda: self.change_ai_count(-1),
            width=10,
            bg="#f8fafc",
            fg=TEXT_DARK,
            relief="flat",
            font=("Helvetica", 11, "bold"),
            padx=8,
            pady=8,
        )
        self.remove_ai_button.pack(side="left", padx=(0, 8))
        tk.Label(
            action_row,
            textvariable=self.ai_count_var,
            width=12,
            bg="#0c3d2f",
            fg="#ecfdf5",
            font=("Helvetica", 11, "bold"),
            pady=9,
        ).pack(side="left", padx=(0, 8))
        self.add_ai_button = tk.Button(
            action_row,
            text="增加 AI",
            command=lambda: self.change_ai_count(1),
            width=10,
            bg="#f8fafc",
            fg=TEXT_DARK,
            relief="flat",
            font=("Helvetica", 11, "bold"),
            padx=8,
            pady=8,
        )
        self.add_ai_button.pack(side="left", padx=(0, 8))
        tk.Button(
            action_row,
            text="新开一局",
            command=self.start_game,
            width=12,
            bg="#f7b538",
            fg=TEXT_DARK,
            relief="flat",
            font=("Helvetica", 11, "bold"),
            padx=10,
            pady=8,
        ).pack(side="left")

        info_bar = tk.Frame(self, bg=PANEL_BG)
        info_bar.pack(fill="x", padx=18, pady=(0, 12))
        self._stat_label(info_bar, self.turn_var).pack(side="left", padx=(14, 8), pady=10)
        self._stat_label(info_bar, self.direction_var).pack(side="left", padx=8, pady=10)
        self._stat_label(info_bar, self.color_var).pack(side="left", padx=8, pady=10)
        self._stat_label(info_bar, self.deck_var).pack(side="left", padx=8, pady=10)
        self._stat_label(info_bar, self.ai_var).pack(side="left", padx=8, pady=10)
        self._stat_label(info_bar, self.player_var).pack(side="left", padx=8, pady=10)

        board = tk.Frame(self, bg=TABLE_BG)
        board.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        left_panel = tk.Frame(board, bg=PANEL_BG, padx=16, pady=16)
        left_panel.pack(side="left", fill="both", expand=True)

        right_panel = tk.Frame(board, bg="#e9dfc7", width=320, padx=14, pady=14)
        right_panel.pack(side="right", fill="y", padx=(14, 0))
        right_panel.pack_propagate(False)

        table_frame = tk.Frame(
            left_panel,
            bg=TABLE_SURFACE,
            highlightthickness=2,
            highlightbackground="#1e7b60",
            padx=14,
            pady=14,
        )
        table_frame.pack(fill="x", pady=(0, 18))

        self.top_ai_frame = tk.Frame(table_frame, bg=TABLE_SURFACE, height=150)
        self.top_ai_frame.pack(fill="x")
        self.top_ai_frame.pack_propagate(False)

        middle_row = tk.Frame(table_frame, bg=TABLE_SURFACE)
        middle_row.pack(fill="x", pady=(10, 0))

        self.left_ai_frame = tk.Frame(middle_row, bg=TABLE_SURFACE, width=150, height=260)
        self.left_ai_frame.pack(side="left", fill="y")
        self.left_ai_frame.pack_propagate(False)

        center_zone = tk.Frame(middle_row, bg=TABLE_SURFACE)
        center_zone.pack(side="left", expand=True, fill="both", padx=18)

        self.right_ai_frame = tk.Frame(middle_row, bg=TABLE_SURFACE, width=150, height=260)
        self.right_ai_frame.pack(side="right", fill="y")
        self.right_ai_frame.pack_propagate(False)

        table_inner = tk.Frame(
            center_zone,
            bg=TABLE_INNER,
            padx=20,
            pady=18,
            highlightthickness=2,
            highlightbackground="#1b6c54",
        )
        table_inner.pack(expand=True)

        tk.Label(
            table_inner,
            text="桌面中心",
            font=("Helvetica", 12, "bold"),
            fg="#d1fae5",
            bg=TABLE_INNER,
        ).pack(pady=(0, 12))

        center_cards = tk.Frame(table_inner, bg=TABLE_INNER)
        center_cards.pack()

        draw_frame = tk.Frame(center_cards, bg=TABLE_INNER)
        draw_frame.pack(side="left")
        self.draw_button = tk.Canvas(
            draw_frame,
            width=126,
            height=154,
            bg=TABLE_INNER,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.draw_button.pack()
        self.draw_button.bind("<Button-1>", lambda _event: self.on_draw_clicked())

        discard_frame = tk.Frame(center_cards, bg=TABLE_INNER)
        discard_frame.pack(side="left", padx=18)
        tk.Label(
            discard_frame,
            text="弃牌堆",
            font=("Helvetica", 12, "bold"),
            fg="#f8fafc",
            bg=TABLE_INNER,
        ).pack(pady=(0, 8))
        self.discard_card = tk.Label(
            discard_frame,
            width=12,
            height=6,
            bd=3,
            relief="groove",
            font=("Helvetica", 12, "bold"),
        )
        self.discard_card.pack()

        control_frame = tk.Frame(center_cards, bg=TABLE_INNER)
        control_frame.pack(side="left", padx=(6, 0), fill="y")
        tk.Label(
            control_frame,
            text="当前颜色",
            font=("Helvetica", 12, "bold"),
            fg="#f8fafc",
            bg=TABLE_INNER,
        ).pack(anchor="w")
        self.current_color_badge = tk.Label(
            control_frame,
            width=12,
            pady=10,
            font=("Helvetica", 12, "bold"),
            relief="flat",
        )
        self.current_color_badge.pack(anchor="w", pady=(8, 14))
        self.pass_button = tk.Canvas(
            control_frame,
            width=126,
            height=92,
            bg=TABLE_INNER,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.pass_button.pack(anchor="w")
        self.pass_button.bind("<Button-1>", lambda _event: self.on_pass_clicked())

        self.start_overlay = tk.Frame(
            table_frame,
            bg="#082f25",
            padx=32,
            pady=28,
            highlightthickness=2,
            highlightbackground="#f7b538",
        )
        tk.Label(
            self.start_overlay,
            text="UNO",
            bg="#082f25",
            fg="#fff7e6",
            font=("Helvetica", 26, "bold italic"),
        ).pack()
        tk.Label(
            self.start_overlay,
            text="先设置 AI 数量，再点击开始游戏",
            bg="#082f25",
            fg="#d1fae5",
            font=("Helvetica", 12),
            pady=10,
        ).pack()
        self.start_overlay_hint = tk.Label(
            self.start_overlay,
            text="支持 1 到 5 名 AI",
            bg="#082f25",
            fg="#fde68a",
            font=("Helvetica", 11, "bold"),
            pady=4,
        )
        self.start_overlay_hint.pack()
        tk.Button(
            self.start_overlay,
            text="开始游戏",
            command=self.start_game,
            width=14,
            bg="#f7b538",
            fg=TEXT_DARK,
            relief="flat",
            font=("Helvetica", 12, "bold"),
            padx=10,
            pady=10,
        ).pack(pady=(12, 0))

        status_panel = tk.Frame(left_panel, bg="#f1efe8", padx=14, pady=12)
        status_panel.pack(fill="x", pady=(0, 18))
        tk.Label(
            status_panel,
            text="状态",
            font=("Helvetica", 12, "bold"),
            bg="#f1efe8",
            fg=TEXT_DARK,
        ).pack(anchor="w")
        tk.Label(
            status_panel,
            textvariable=self.status_var,
            wraplength=820,
            justify="left",
            bg="#f1efe8",
            fg=TEXT_DARK,
            font=("Helvetica", 12),
        ).pack(anchor="w", pady=(8, 0))

        tk.Label(
            left_panel,
            text="你的手牌",
            font=("Helvetica", 14, "bold"),
            fg="#f8fafc",
            bg=PANEL_BG,
        ).pack(anchor="w", pady=(2, 10))

        hand_outer = tk.Frame(left_panel, bg=PANEL_BG, height=HAND_VIEWPORT_HEIGHT + 22)
        hand_outer.pack(fill="x")
        hand_outer.pack_propagate(False)
        self.hand_canvas = tk.Canvas(
            hand_outer,
            bg=PANEL_BG,
            highlightthickness=0,
            height=HAND_VIEWPORT_HEIGHT,
        )
        hand_scroll = tk.Scrollbar(hand_outer, orient="horizontal", command=self.hand_canvas.xview)
        self.hand_canvas.configure(xscrollcommand=hand_scroll.set)
        self.hand_canvas.pack(fill="x")
        hand_scroll.pack(fill="x", pady=(6, 0))
        self.hand_frame = tk.Frame(self.hand_canvas, bg=PANEL_BG)
        self.hand_window = self.hand_canvas.create_window((0, 0), window=self.hand_frame, anchor="nw")
        self.hand_frame.bind(
            "<Configure>",
            lambda _event: self.hand_canvas.configure(scrollregion=self.hand_canvas.bbox("all")),
        )
        self.hand_canvas.bind(
            "<Configure>",
            lambda event: self.hand_canvas.itemconfigure(
                self.hand_window,
                width=max(event.width, self.hand_content_width),
                height=event.height,
            ),
        )

        tk.Label(
            right_panel,
            text="对局日志",
            font=("Helvetica", 14, "bold"),
            bg="#e9dfc7",
            fg=TEXT_DARK,
        ).pack(anchor="w")
        tk.Label(
            right_panel,
            text="AI 会围坐在牌桌四周。支持 1 到 5 名 AI 和多人方向反转。",
            font=("Helvetica", 11),
            bg="#e9dfc7",
            fg="#5b4b2f",
            wraplength=270,
            justify="left",
        ).pack(anchor="w", pady=(4, 10))
        self.log = ScrolledText(
            right_panel,
            wrap="word",
            state="disabled",
            bg="#fffdf6",
            fg=TEXT_DARK,
            font=("Helvetica", 11),
            relief="flat",
            padx=10,
            pady=10,
        )
        self.log.pack(fill="both", expand=True)

    def _stat_label(self, parent: tk.Widget, variable: tk.StringVar) -> tk.Label:
        return tk.Label(
            parent,
            textvariable=variable,
            bg=PANEL_BG,
            fg="#ecfdf5",
            font=("Helvetica", 11, "bold"),
        )

    def _begin_round(self, events: list[str], first_launch: bool = False) -> None:
        self._cancel_ai_job()
        self.started = True
        self.start_overlay.place_forget()
        self.winner_announced = False
        self._clear_log()
        self._append_events(events)
        self.refresh_ui()
        if not first_launch:
            self.status_var.set(events[-1] if events else "新的一局已经开始。")
        self.maybe_schedule_ai()

    def start_game(self) -> None:
        self._begin_round(self.game.start_new_game())

    def change_ai_count(self, delta: int) -> None:
        new_count = max(MIN_AI_PLAYERS, min(MAX_AI_PLAYERS, self.game.ai_count + delta))
        if new_count == self.game.ai_count:
            self.status_var.set(
                f"AI 数量已经是{'上限' if new_count == MAX_AI_PLAYERS else '下限'} {new_count}。"
            )
            return
        if self.started:
            events = self.game.set_ai_count(new_count)
            events.insert(0, f"AI 数量已调整为 {new_count}。")
            self._begin_round(events)
            return
        self.game = UnoGame(ai_count=new_count)
        self.status_var.set(f"AI 数量已设置为 {new_count}，点击“开始游戏”即可发牌。")
        self._refresh_pre_game_ui()

    def _show_start_overlay(self) -> None:
        self.start_overlay.place(relx=0.5, rely=0.5, anchor="center")

    def _refresh_pre_game_ui(self) -> None:
        self.turn_var.set("当前回合：未开始")
        self.direction_var.set("方向：顺时针")
        self.color_var.set("生效颜色：未开始")
        self.deck_var.set("抽牌堆：未开始")
        self.ai_var.set(f"AI：{self.game.ai_count} 名")
        self.player_var.set("你的手牌：未发牌")
        self.ai_count_var.set(f"AI x {self.game.ai_count}")
        self.start_overlay_hint.configure(text=f"当前准备：{self.game.ai_count} 名 AI")
        self.add_ai_button.configure(state="normal" if self.game.ai_count < MAX_AI_PLAYERS else "disabled")
        self.remove_ai_button.configure(state="normal" if self.game.ai_count > MIN_AI_PLAYERS else "disabled")
        self._style_action_button(self.draw_button, enabled=False, kind="draw")
        self._style_action_button(self.pass_button, enabled=False, kind="pass")
        self.current_color_badge.configure(text="未开始", bg="#cbd5e1", fg=TEXT_DARK)
        self.discard_card.configure(text="等待\n开始", bg="#e5e7eb", fg=TEXT_DARK)
        self._clear_ai_frames()
        for child in self.hand_frame.winfo_children():
            child.destroy()
        self._clear_log()
        self.log.configure(state="normal")
        self.log.insert("end", "• 点击“开始游戏”后发牌。\n• 顶部可先调整 AI 数量。\n\n")
        self.log.configure(state="disabled")
        self.status_var.set("点击“开始游戏”后开始本局。")
        self._show_start_overlay()

    def _clear_ai_frames(self) -> None:
        for frame in (self.top_ai_frame, self.left_ai_frame, self.right_ai_frame):
            for child in frame.winfo_children():
                child.destroy()

    def refresh_ui(self) -> None:
        if not self.started:
            self._refresh_pre_game_ui()
            return
        self.turn_var.set(f"当前回合：{self.game.player_name(self.game.current_player)}")
        self.direction_var.set(f"方向：{'顺时针' if self.game.direction == 1 else '逆时针'}")
        self.color_var.set(f"生效颜色：{COLOR_NAMES[self.game.current_color]}")
        self.deck_var.set(f"抽牌堆：{self.game.deck_count} 张")
        self.ai_var.set(f"AI：{self.game.ai_count} 名 / 总牌 {self.game.total_ai_cards} 张")
        self.player_var.set(f"你的手牌：{len(self.game.hands[PLAYER_HUMAN])} 张")
        self.ai_count_var.set(f"AI x {self.game.ai_count}")

        self._render_ai_table()
        self._render_discard()
        self._render_player_hand()

        self._style_action_button(self.draw_button, enabled=self.game.can_human_draw(), kind="draw")
        self._style_action_button(self.pass_button, enabled=self.game.can_human_pass(), kind="pass")
        self.add_ai_button.configure(state="normal" if self.game.ai_count < MAX_AI_PLAYERS else "disabled")
        self.remove_ai_button.configure(state="normal" if self.game.ai_count > MIN_AI_PLAYERS else "disabled")

        color_bg, color_fg = CARD_COLORS[self.game.current_color]
        self.current_color_badge.configure(
            text=COLOR_NAMES[self.game.current_color],
            bg=color_bg,
            fg=color_fg,
        )

        if self.game.winner and not self.winner_announced:
            self.winner_announced = True
            messagebox.showinfo(
                "对局结束",
                f"{self.game.player_name(self.game.winner)} 赢了。\n本轮得分：{self.game.round_points}",
            )

    def _style_action_button(self, button: tk.Canvas, enabled: bool, kind: str) -> None:
        if kind == "draw":
            self.draw_action_enabled = enabled
            border = "#ffe39a" if enabled else "#27433a"
            face = "#2f67db" if enabled else "#294238"
            accent = "#6ea0ff" if enabled else "#38584d"
            text = "#fff8ea" if enabled else "#9fb8ae"
            shadow = "#13284f" if enabled else "#1f312b"
            button.configure(cursor="hand2" if enabled else "arrow")
            button.delete("all")
            self._rounded_rect(button, 8, 10, 116, 146, 18, fill=shadow, outline="", smooth=True)
            self._rounded_rect(button, 6, 6, 112, 140, 18, fill=face, outline=border, width=3, smooth=True)
            button.create_oval(28, 24, 92, 96, fill=accent, outline="")
            button.create_text(60, 58, text="+1", fill="#ffffff", font=("Helvetica", 20, "bold"))
            button.create_text(60, 114, text="抽牌", fill=text, font=("Helvetica", 15, "bold"))
            button.create_text(60, 130, text="无可出牌时", fill=text, font=("Helvetica", 9, "bold"))
            return

        self.pass_action_enabled = enabled
        border = "#ffe39a" if enabled else "#27433a"
        face = "#f7b538" if enabled else "#314740"
        accent = "#ffd873" if enabled else "#476159"
        text = TEXT_DARK if enabled else "#9fb8ae"
        shadow = "#5e4314" if enabled else "#22342f"
        button.configure(cursor="hand2" if enabled else "arrow")
        button.delete("all")
        self._rounded_rect(button, 8, 10, 116, 84, 18, fill=shadow, outline="", smooth=True)
        self._rounded_rect(button, 6, 6, 112, 78, 18, fill=face, outline=border, width=3, smooth=True)
        button.create_polygon(24, 42, 46, 26, 46, 36, 88, 36, 88, 48, 46, 48, 46, 58, fill=accent, outline="")
        button.create_text(60, 60, text="结束回合", fill=text, font=("Helvetica", 13, "bold"))

    def _render_ai_table(self) -> None:
        self._clear_ai_frames()

        left_players, top_players, right_players = self._ai_slots()

        for column in range(max(3, len(top_players))):
            self.top_ai_frame.grid_columnconfigure(column, weight=1)
        for index, player in enumerate(top_players):
            panel = self._create_ai_panel(self.top_ai_frame, player, orientation="top")
            panel.grid(row=0, column=index, padx=8, pady=6)

        for player in left_players:
            panel = self._create_ai_panel(self.left_ai_frame, player, orientation="side")
            panel.pack(anchor="center", pady=4)

        for player in right_players:
            panel = self._create_ai_panel(self.right_ai_frame, player, orientation="side")
            panel.pack(anchor="center", pady=4)

    def _ai_slots(self) -> tuple[list[str], list[str], list[str]]:
        players = self.game.ai_players
        if len(players) <= 3:
            return [], players, []
        if len(players) == 4:
            return [players[0]], players[1:3], [players[3]]
        return [players[0]], players[1:4], [players[4]]

    def _create_ai_panel(self, parent: tk.Widget, player: str, orientation: str) -> tk.Frame:
        is_current = self.game.current_player == player and not self.game.winner
        panel_bg = "#0b4132" if is_current else "#0e4636"

        if orientation == "top":
            panel = tk.Frame(
                parent,
                width=220,
                height=126,
                bg=panel_bg,
                highlightthickness=3 if is_current else 1,
                highlightbackground="#f7b538" if is_current else "#2e7d67",
                padx=10,
                pady=10,
            )
            panel.grid_propagate(False)
        else:
            panel = tk.Frame(
                parent,
                width=132,
                height=238,
                bg=panel_bg,
                highlightthickness=3 if is_current else 1,
                highlightbackground="#f7b538" if is_current else "#2e7d67",
                padx=8,
                pady=8,
            )
            panel.pack_propagate(False)

        header = tk.Frame(panel, bg=panel_bg)
        header.pack(fill="x")
        tk.Label(
            header,
            text=self.game.player_name(player),
            bg=panel_bg,
            fg="#f8fafc",
            font=("Helvetica", 11, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text="当前" if is_current else "",
            bg=panel_bg,
            fg="#fde68a",
            font=("Helvetica", 10, "bold"),
        ).pack(side="right")

        if orientation == "top":
            canvas = tk.Canvas(
                panel,
                width=194,
                height=66,
                bg=panel_bg,
                highlightthickness=0,
                bd=0,
            )
            canvas.pack(fill="x", pady=(8, 4))
            self._draw_ai_fan_horizontal(canvas, len(self.game.hands[player]), panel_bg)
        else:
            canvas = tk.Canvas(
                panel,
                width=104,
                height=172,
                bg=panel_bg,
                highlightthickness=0,
                bd=0,
            )
            canvas.pack(pady=(8, 6))
            self._draw_ai_fan_vertical(canvas, len(self.game.hands[player]), panel_bg)

        tk.Label(
            panel,
            text=f"{len(self.game.hands[player])} 张手牌",
            bg=panel_bg,
            fg="#d1fae5",
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="e" if orientation == "top" else "center")
        return panel

    def _render_discard(self) -> None:
        top_card = self.game.top_card
        bg, fg = self._face_colors(top_card)
        self.discard_card.configure(text=self._card_text(top_card), bg=bg, fg=fg)

    def _render_player_hand(self) -> None:
        for child in self.hand_frame.winfo_children():
            child.destroy()

        playable = (
            set(self.game.playable_indices(PLAYER_HUMAN))
            if self.game.current_player == PLAYER_HUMAN
            else set()
        )
        card_count = len(self.game.hands[PLAYER_HUMAN])
        content_width = (
            16 + PLAYER_CARD_WIDTH + max(0, card_count - 1) * PLAYER_CARD_STEP + 16
            if card_count
            else max(self.hand_canvas.winfo_width(), PLAYER_CARD_WIDTH + 32)
        )
        self.hand_content_width = content_width
        self.hand_frame.configure(width=content_width, height=HAND_VIEWPORT_HEIGHT)
        self.hand_canvas.itemconfigure(
            self.hand_window,
            width=max(self.hand_canvas.winfo_width(), content_width),
            height=HAND_VIEWPORT_HEIGHT,
        )

        for index, card in enumerate(self.game.hands[PLAYER_HUMAN]):
            is_enabled = index in playable and not self.game.winner
            card_canvas = tk.Canvas(
                self.hand_frame,
                width=PLAYER_CARD_WIDTH,
                height=PLAYER_CARD_HEIGHT,
                bg=PANEL_BG,
                bd=0,
                highlightthickness=0,
                cursor="hand2" if is_enabled else "arrow",
            )
            card_canvas.place(x=16 + (index * PLAYER_CARD_STEP), y=12)
            self._draw_player_card(card_canvas, card, is_enabled)
            self._bind_card_click(card_canvas, index, is_enabled)

    def _card_text(self, card: Card) -> str:
        title = CARD_TITLES.get(card.rank, card.rank)
        if card.rank.isdigit():
            title = card.rank
        if card.color:
            return f"{COLOR_NAMES[card.color]}\n{title}"
        return title

    def _face_colors(self, card: Card) -> tuple[str, str]:
        if card.color:
            return CARD_COLORS[card.color]
        return CARD_COLORS["wild"]

    def _draw_player_card(self, canvas: tk.Canvas, card: Card, is_enabled: bool) -> None:
        primary, corner_text = self._face_colors(card)
        accent = CARD_ACCENTS["wild"] if card.is_wild else CARD_ACCENTS[card.color]
        glow = "#ffe7a0" if is_enabled else "#29463a"

        self._rounded_rect(canvas, 18, 18, 118, 180, 20, fill="#0f2319", outline="", smooth=True)
        self._rounded_rect(
            canvas,
            12,
            12,
            112,
            172,
            20,
            fill="#ffffff",
            outline=glow,
            width=4 if is_enabled else 2,
            smooth=True,
        )

        if card.is_wild:
            self._draw_wild_face(canvas, card)
        else:
            self._draw_standard_face(canvas, card, primary, corner_text, accent)

    def _draw_standard_face(
        self,
        canvas: tk.Canvas,
        card: Card,
        primary: str,
        corner_text: str,
        accent: str,
    ) -> None:
        self._rounded_rect(canvas, 17, 17, 107, 167, 16, fill=primary, outline="", smooth=True)
        canvas.create_polygon(17, 42, 107, 20, 107, 52, 17, 74, fill=accent, outline="")
        canvas.create_polygon(17, 126, 107, 104, 107, 166, 17, 166, fill=accent, outline="")
        canvas.create_oval(30, 46, 94, 132, fill="#ffffff", outline="")

        corner_value = self._corner_label(card)
        canvas.create_text(30, 31, text=corner_value, font=("Helvetica", 16, "bold"), fill=corner_text)
        canvas.create_text(94, 149, text=corner_value, font=("Helvetica", 16, "bold"), fill=corner_text)

        if card.rank.isdigit():
            self._card_text_shadow(
                canvas,
                61,
                90,
                card.rank,
                font=("Helvetica", 42, "bold italic"),
                fill=primary,
                shadow=accent,
                offset=2,
            )
            return

        if card.rank == "skip":
            canvas.create_oval(43, 67, 79, 103, outline=primary, width=4)
            canvas.create_line(47, 99, 75, 71, fill=primary, width=5)
            return

        if card.rank == "reverse":
            self._card_text_shadow(
                canvas,
                61,
                88,
                "↺↻",
                font=("Helvetica", 25, "bold"),
                fill=primary,
                shadow=accent,
                offset=2,
            )
            return

        if card.rank == "draw_two":
            self._draw_draw_two_icon(canvas, primary, accent)

    def _draw_wild_face(self, canvas: tk.Canvas, card: Card) -> None:
        self._rounded_rect(canvas, 17, 17, 107, 167, 16, fill="#111111", outline="", smooth=True)
        canvas.create_oval(30, 46, 94, 132, fill="#ffffff", outline="")
        canvas.create_polygon(30, 88, 60, 48, 60, 104, 30, 136, fill="#d94f45", outline="")
        canvas.create_polygon(60, 48, 94, 78, 94, 98, 60, 70, fill="#3772d6", outline="")
        canvas.create_polygon(30, 136, 60, 104, 60, 150, 30, 150, fill="#f1c84c", outline="")
        canvas.create_polygon(60, 104, 94, 132, 94, 150, 60, 122, fill="#2f9d57", outline="")
        canvas.create_text(30, 31, text="◔", font=("Helvetica", 16, "bold"), fill="#ffffff")
        canvas.create_text(94, 149, text="◔", font=("Helvetica", 16, "bold"), fill="#ffffff")

        if card.rank == "wild_draw_four":
            canvas.create_text(82, 149, text="+4", font=("Helvetica", 10, "bold"), fill="#ffffff")
            self._draw_draw_four_overlay(canvas)
        else:
            self._card_text_shadow(
                canvas,
                61,
                89,
                "Wild",
                font=("Helvetica", 18, "bold italic"),
                fill="#111111",
                shadow="#c8c2b8",
                offset=2,
            )

    def _draw_draw_two_icon(self, canvas: tk.Canvas, primary: str, accent: str) -> None:
        self._rounded_rect(canvas, 46, 70, 70, 106, 6, fill="#ffffff", outline=primary, width=2, smooth=True)
        self._rounded_rect(canvas, 56, 62, 80, 98, 6, fill="#ffffff", outline=primary, width=2, smooth=True)
        canvas.create_text(51, 76, text="+2", anchor="nw", font=("Helvetica", 10, "bold"), fill=primary)
        canvas.create_line(58, 66, 72, 66, fill=accent, width=2)
        canvas.create_line(58, 70, 72, 70, fill=accent, width=2)

    def _draw_draw_four_overlay(self, canvas: tk.Canvas) -> None:
        colors = ("#d94f45", "#3772d6", "#f1c84c", "#2f9d57")
        positions = ((42, 78), (52, 68), (60, 82), (70, 72))
        for (x, y), color in zip(positions, colors):
            self._rounded_rect(canvas, x, y, x + 18, y + 28, 5, fill="#ffffff", outline="#1f2430", width=1, smooth=True)
            self._rounded_rect(canvas, x + 2, y + 2, x + 16, y + 26, 4, fill=color, outline="", smooth=True)

    def _corner_label(self, card: Card) -> str:
        if card.rank.isdigit():
            return card.rank
        return {
            "skip": "⊘",
            "reverse": "⇄",
            "draw_two": "+2",
        }.get(card.rank, CARD_TITLES.get(card.rank, card.rank))

    def _center_label(self, card: Card) -> str:
        if card.rank.isdigit():
            return card.rank
        return {
            "skip": "⊘",
            "reverse": "↺↻",
            "draw_two": "+2",
        }.get(card.rank, CARD_TITLES.get(card.rank, card.rank))

    def _card_text_shadow(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        text: str,
        font: tuple[str, int, str],
        fill: str,
        shadow: str | None = None,
        offset: int = 2,
    ) -> None:
        shadow_fill = shadow or "#1a1f2a"
        canvas.create_text(x + offset, y + offset, text=text, font=font, fill=shadow_fill)
        canvas.create_text(x, y, text=text, font=font, fill=fill)

    def _rounded_rect(
        self,
        canvas: tk.Canvas,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        radius: float,
        **kwargs: object,
    ) -> None:
        points = [
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1,
        ]
        canvas.create_polygon(points, splinesteps=36, **kwargs)

    def _draw_ai_fan_horizontal(self, canvas: tk.Canvas, count: int, panel_bg: str) -> None:
        if count <= 0:
            canvas.create_text(97, 33, text="已出完", fill="#d1fae5", font=("Helvetica", 11, "bold"))
            return

        visible = min(count, 7)
        scale = 0.46
        step = 17 if visible <= 5 else 14
        card_width = 82 * scale
        total_width = card_width + step * (visible - 1)
        start_x = max(10, int((194 - total_width) / 2))
        for index in range(visible):
            self._draw_ai_card_back(canvas, start_x + (step * index), 4, scale, panel_bg)
        if count > visible:
            canvas.create_text(
                start_x + total_width + 12,
                34,
                text=f"+{count - visible}",
                fill="#f8fafc",
                font=("Helvetica", 10, "bold"),
            )

    def _draw_ai_fan_vertical(self, canvas: tk.Canvas, count: int, panel_bg: str) -> None:
        if count <= 0:
            canvas.create_text(52, 86, text="已出完", fill="#d1fae5", font=("Helvetica", 11, "bold"))
            return

        visible = min(count, 5)
        scale = 0.56
        step = 22
        card_height = 120 * scale
        total_height = card_height + step * (visible - 1)
        start_y = max(6, int((172 - total_height) / 2))
        for index in range(visible):
            self._draw_ai_card_back(canvas, 18, start_y + (step * index), scale, panel_bg)
        if count > visible:
            canvas.create_text(
                52,
                start_y + total_height + 10,
                text=f"+{count - visible}",
                fill="#f8fafc",
                font=("Helvetica", 10, "bold"),
            )

    def _draw_ai_card_back(
        self,
        canvas: tk.Canvas,
        offset_x: float,
        offset_y: float,
        scale: float,
        panel_bg: str,
    ) -> None:
        def sx(value: float) -> float:
            return offset_x + (value * scale)

        def sy(value: float) -> float:
            return offset_y + (value * scale)

        canvas.create_rectangle(sx(10), sy(12), sx(88), sy(126), fill=AI_BACK_STYLE["shadow"], outline="")
        canvas.create_rectangle(sx(6), sy(6), sx(84), sy(120), fill=AI_BACK_STYLE["border"], outline="")
        canvas.create_rectangle(sx(10), sy(10), sx(80), sy(116), fill=AI_BACK_STYLE["outer"], outline="")
        canvas.create_rectangle(sx(14), sy(14), sx(76), sy(112), fill=AI_BACK_STYLE["inner"], outline="")

        canvas.create_polygon(
            sx(20),
            sy(100),
            sx(57),
            sy(28),
            sx(72),
            sy(28),
            sx(35),
            sy(100),
            fill=AI_BACK_STYLE["red"],
            outline="",
        )
        canvas.create_polygon(
            sx(18),
            sy(110),
            sx(62),
            sy(34),
            sx(78),
            sy(34),
            sx(34),
            sy(110),
            fill=AI_BACK_STYLE["gold"],
            outline="",
        )
        canvas.create_oval(sx(16), sy(18), sx(32), sy(34), fill=AI_BACK_STYLE["green"], outline="")
        canvas.create_oval(sx(58), sy(92), sx(74), sy(108), fill=AI_BACK_STYLE["red"], outline="")
        canvas.create_oval(sx(20), sy(36), sx(70), sy(94), fill=AI_BACK_STYLE["white"], outline="")
        canvas.create_oval(sx(24), sy(40), sx(66), sy(90), fill=AI_BACK_STYLE["gold"], outline="")
        canvas.create_text(
            sx(45),
            sy(65),
            text="UNO",
            fill=AI_BACK_STYLE["text"],
            font=("Helvetica", max(7, int(16 * scale)), "bold italic"),
        )
        canvas.create_rectangle(sx(12), sy(118), sx(78), sy(124), fill=panel_bg, outline="")

    def _bind_card_click(self, widget: tk.Widget, index: int, is_enabled: bool) -> None:
        if not is_enabled:
            return
        widget.bind("<Button-1>", lambda _event, idx=index: self.on_card_clicked(idx))

    def _append_events(self, events: list[str]) -> None:
        if not events:
            return
        self.log.configure(state="normal")
        for event in events:
            self.log.insert("end", f"• {event}\n")
        self.log.insert("end", "\n")
        self.log.configure(state="disabled")
        self.log.see("end")
        self.status_var.set(events[-1])

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def on_card_clicked(self, index: int) -> None:
        try:
            card = self.game.hands[PLAYER_HUMAN][index]
            chosen_color = self.ask_color() if card.is_wild else None
            if card.is_wild and not chosen_color:
                return
            events = self.game.human_play(index, chosen_color)
        except RuleError as exc:
            self.status_var.set(str(exc))
            return
        self._append_events(events)
        self.refresh_ui()
        self.maybe_schedule_ai()

    def on_draw_clicked(self) -> None:
        if not self.started:
            self.status_var.set("请先点击“开始游戏”。")
            return
        if not self.draw_action_enabled:
            self.status_var.set("当前不能抽牌。只有在没有可出手牌时才能抽。")
            return
        try:
            _card, events = self.game.human_draw()
        except RuleError as exc:
            self.status_var.set(str(exc))
            return
        self._append_events(events)
        self.refresh_ui()
        self.maybe_schedule_ai()

    def on_pass_clicked(self) -> None:
        if not self.started:
            self.status_var.set("请先点击“开始游戏”。")
            return
        if not self.pass_action_enabled:
            self.status_var.set("当前不能结束回合。")
            return
        try:
            events = self.game.human_pass()
        except RuleError as exc:
            self.status_var.set(str(exc))
            return
        self._append_events(events)
        self.refresh_ui()
        self.maybe_schedule_ai()

    def maybe_schedule_ai(self) -> None:
        if self.game.winner or self.game.current_player == PLAYER_HUMAN:
            self._cancel_ai_job()
            return
        if self.ai_job is None:
            self.ai_job = self.after(850, self.run_ai_turn)

    def run_ai_turn(self) -> None:
        self.ai_job = None
        if self.game.winner or self.game.current_player == PLAYER_HUMAN:
            return
        try:
            events = self.game.ai_turn()
        except RuleError as exc:
            self.status_var.set(str(exc))
            return
        self._append_events(events)
        self.refresh_ui()
        self.maybe_schedule_ai()

    def _cancel_ai_job(self) -> None:
        if self.ai_job is not None:
            self.after_cancel(self.ai_job)
            self.ai_job = None

    def ask_color(self) -> str | None:
        dialog = tk.Toplevel(self)
        dialog.title("选择颜色")
        dialog.configure(bg=SURFACE_BG)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        choice: dict[str, str | None] = {"value": None}
        tk.Label(
            dialog,
            text="请选择新的颜色",
            bg=SURFACE_BG,
            fg=TEXT_DARK,
            font=("Helvetica", 12, "bold"),
            padx=20,
            pady=16,
        ).pack()

        button_row = tk.Frame(dialog, bg=SURFACE_BG)
        button_row.pack(padx=18, pady=(0, 18))

        for color in COLORS:
            bg, fg = CARD_COLORS[color]
            tile = tk.Frame(
                button_row,
                width=84,
                height=84,
                bg=bg,
                highlightthickness=3,
                highlightbackground="#f7f3ea",
                cursor="hand2",
            )
            tile.pack(side="left", padx=6)
            tile.pack_propagate(False)

            label = tk.Label(
                tile,
                text=COLOR_NAMES[color],
                bg=bg,
                fg=fg,
                font=("Helvetica", 12, "bold"),
            )
            label.place(relx=0.5, rely=0.5, anchor="center")

            for widget in (tile, label):
                widget.bind(
                    "<Button-1>",
                    lambda _event, chosen=color: self._finish_color_dialog(dialog, choice, chosen),
                )

        dialog.wait_window()
        return choice["value"]

    def _finish_color_dialog(
        self,
        dialog: tk.Toplevel,
        choice: dict[str, str | None],
        color: str,
    ) -> None:
        choice["value"] = color
        dialog.destroy()


def main() -> None:
    app = UnoApp()
    app.mainloop()
