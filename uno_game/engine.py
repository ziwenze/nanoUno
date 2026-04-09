from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from random import Random

PLAYER_HUMAN = "human"
MIN_AI_PLAYERS = 1
MAX_AI_PLAYERS = 5

COLORS = ("red", "yellow", "green", "blue")
COLOR_NAMES = {
    "red": "红色",
    "yellow": "黄色",
    "green": "绿色",
    "blue": "蓝色",
}
RANK_NAMES = {
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "skip": "Skip",
    "reverse": "Reverse",
    "draw_two": "+2",
    "wild": "Wild",
    "wild_draw_four": "Wild +4",
}
ACTION_RANKS = ("skip", "reverse", "draw_two")
WILD_RANKS = ("wild", "wild_draw_four")


class RuleError(ValueError):
    """Raised when an attempted move breaks UNO rules."""


@dataclass(frozen=True, slots=True)
class Card:
    color: str | None
    rank: str

    @property
    def is_wild(self) -> bool:
        return self.rank in WILD_RANKS

    @property
    def short_name(self) -> str:
        return RANK_NAMES[self.rank]

    @property
    def label(self) -> str:
        if self.color:
            return f"{COLOR_NAMES[self.color]} {self.short_name}"
        return self.short_name


def build_deck() -> list[Card]:
    deck: list[Card] = []
    for color in COLORS:
        deck.append(Card(color, "0"))
        for number in range(1, 10):
            deck.append(Card(color, str(number)))
            deck.append(Card(color, str(number)))
        for rank in ACTION_RANKS:
            deck.append(Card(color, rank))
            deck.append(Card(color, rank))
    for _ in range(4):
        deck.append(Card(None, "wild"))
        deck.append(Card(None, "wild_draw_four"))
    return deck


def card_points(card: Card) -> int:
    if card.rank.isdigit():
        return int(card.rank)
    if card.rank in ACTION_RANKS:
        return 20
    return 50


class UnoGame:
    def __init__(self, ai_count: int = 1, seed: int | None = None) -> None:
        self._rng = Random(seed)
        self.ai_count = self._normalize_ai_count(ai_count)
        self.players = self._build_players(self.ai_count)
        self.hands: dict[str, list[Card]] = {player: [] for player in self.players}
        self.draw_pile: list[Card] = []
        self.discard_pile: list[Card] = []
        self.current_color = "red"
        self.current_player = PLAYER_HUMAN
        self.direction = 1
        self.drawn_this_turn = False
        self.winner: str | None = None
        self.round_points = 0
        self.start_new_game()

    @property
    def ai_players(self) -> list[str]:
        return [player for player in self.players if player != PLAYER_HUMAN]

    @property
    def total_ai_cards(self) -> int:
        return sum(len(self.hands[player]) for player in self.ai_players)

    @property
    def top_card(self) -> Card:
        return self.discard_pile[-1]

    @property
    def deck_count(self) -> int:
        return len(self.draw_pile)

    @staticmethod
    def _normalize_ai_count(ai_count: int) -> int:
        return max(MIN_AI_PLAYERS, min(MAX_AI_PLAYERS, int(ai_count)))

    def _build_players(self, ai_count: int) -> list[str]:
        return [PLAYER_HUMAN] + [f"ai_{index}" for index in range(1, ai_count + 1)]

    def set_ai_count(self, ai_count: int) -> list[str]:
        self.ai_count = self._normalize_ai_count(ai_count)
        self.players = self._build_players(self.ai_count)
        self.hands = {player: [] for player in self.players}
        return self.start_new_game()

    def hand(self, player: str) -> list[Card]:
        return list(self.hands[player])

    def is_ai_player(self, player: str) -> bool:
        return player != PLAYER_HUMAN

    def player_name(self, player: str) -> str:
        if player == PLAYER_HUMAN:
            return "你"
        if player.startswith("ai_"):
            return f"AI {player.split('_')[-1]}"
        return player

    def color_name(self, color: str) -> str:
        return COLOR_NAMES[color]

    def next_player(self, from_player: str | None = None, steps: int = 1) -> str:
        base_player = self.current_player if from_player is None else from_player
        index = self.players.index(base_player)
        next_index = (index + (self.direction * steps)) % len(self.players)
        return self.players[next_index]

    def start_new_game(self) -> list[str]:
        self.hands = {player: [] for player in self.players}
        self.draw_pile = build_deck()
        self._rng.shuffle(self.draw_pile)
        self.discard_pile = []
        self.current_player = PLAYER_HUMAN
        self.current_color = "red"
        self.direction = 1
        self.drawn_this_turn = False
        self.winner = None
        self.round_points = 0

        for _ in range(7):
            for player in self.players:
                self.hands[player].append(self.draw_pile.pop())

        events = [f"新的一局开始了，本局共有 {len(self.players)} 名玩家。"]
        events.extend(self._prepare_opening_card())
        return events

    def _prepare_opening_card(self) -> list[str]:
        events: list[str] = []
        while True:
            opening = self.draw_pile.pop()
            if opening.rank == "wild_draw_four":
                self.draw_pile.insert(0, opening)
                self._rng.shuffle(self.draw_pile)
                continue
            self.discard_pile.append(opening)
            break

        if opening.rank == "wild":
            self.current_color = self.best_color_for(PLAYER_HUMAN)
            events.append(
                f"翻开的起始牌是 {opening.label}，起始颜色设为 {self.color_name(self.current_color)}。"
            )
        else:
            self.current_color = opening.color or self.current_color
            events.append(f"翻开的起始牌是 {opening.label}。")

        if opening.rank == "skip":
            self.current_player = self.next_player(from_player=PLAYER_HUMAN)
            events.append("起始牌是 Skip，你的首回合被跳过。")
        elif opening.rank == "reverse":
            if len(self.players) == 2:
                self.current_player = self.next_player(from_player=PLAYER_HUMAN)
                events.append("双人规则下起始牌 Reverse 等同于 Skip，所以 AI 先手。")
            else:
                self.direction *= -1
                self.current_player = self.next_player(from_player=PLAYER_HUMAN)
                events.append(f"起始牌是 Reverse，方向反转，由 {self.player_name(self.current_player)} 先手。")
        elif opening.rank == "draw_two":
            self._draw_cards(PLAYER_HUMAN, 2)
            self.current_player = self.next_player(from_player=PLAYER_HUMAN)
            events.append(f"起始牌是 +2，你先抽两张，接着由 {self.player_name(self.current_player)} 出牌。")
        else:
            self.current_player = PLAYER_HUMAN

        events.append(self.turn_prompt())
        return events

    def turn_prompt(self) -> str:
        if self.winner:
            return "本局已经结束。"
        return f"轮到{self.player_name(self.current_player)}了。"

    def best_color_for(self, player: str) -> str:
        counts = Counter(card.color for card in self.hands[player] if card.color)
        if counts:
            best_count = max(counts.values())
            best_colors = [color for color, count in counts.items() if count == best_count]
            best_colors.sort(key=COLORS.index)
            return best_colors[0]
        return self.current_color if self.current_color in COLORS else "red"

    def playable_indices(self, player: str) -> list[int]:
        return [
            index
            for index, card in enumerate(self.hands[player])
            if self.is_playable(card, player)
        ]

    def is_playable(self, card: Card, player: str) -> bool:
        if card.rank == "wild":
            return True
        if card.rank == "wild_draw_four":
            return not any(
                other.color == self.current_color for other in self.hands[player] if other.color
            )
        if card.color == self.current_color:
            return True
        return card.rank == self.top_card.rank

    def can_human_draw(self) -> bool:
        return (
            self.current_player == PLAYER_HUMAN
            and not self.winner
            and not self.drawn_this_turn
            and not self.playable_indices(PLAYER_HUMAN)
        )

    def can_human_pass(self) -> bool:
        return self.current_player == PLAYER_HUMAN and self.drawn_this_turn and not self.winner

    def human_draw(self) -> tuple[Card, list[str]]:
        if self.winner:
            raise RuleError("本局已经结束。")
        if self.current_player != PLAYER_HUMAN:
            raise RuleError("还没轮到你。")
        if self.drawn_this_turn:
            raise RuleError("你已经抽过牌了。")
        if self.playable_indices(PLAYER_HUMAN):
            raise RuleError("你手里还有可出的牌，按规则现在不能抽牌。")

        card = self._draw_cards(PLAYER_HUMAN, 1)[0]
        events = [f"你抽到了 {card.label}。"]
        if self.is_playable(card, PLAYER_HUMAN):
            self.drawn_this_turn = True
            events.append("这张牌可以立刻打出；如果不想打，可以点击“结束回合”。")
        else:
            self.current_player = self.next_player(from_player=PLAYER_HUMAN)
            events.append("这张牌不能打出，回合自动结束。")
            events.append(self.turn_prompt())
        return card, events

    def human_pass(self) -> list[str]:
        if self.winner:
            raise RuleError("本局已经结束。")
        if self.current_player != PLAYER_HUMAN or not self.drawn_this_turn:
            raise RuleError("当前没有可以结束的抽牌回合。")
        self.drawn_this_turn = False
        self.current_player = self.next_player(from_player=PLAYER_HUMAN)
        return ["你选择保留刚抽到的牌。", self.turn_prompt()]

    def human_play(self, card_index: int, chosen_color: str | None = None) -> list[str]:
        if self.winner:
            raise RuleError("本局已经结束。")
        if self.current_player != PLAYER_HUMAN:
            raise RuleError("还没轮到你。")
        return self._play_card(PLAYER_HUMAN, card_index, chosen_color)

    def ai_turn(self) -> list[str]:
        player = self.current_player
        if self.winner:
            return []
        if not self.is_ai_player(player):
            raise RuleError("现在不是 AI 的回合。")

        playable = self.playable_indices(player)
        if playable:
            index = self._choose_ai_card(player, playable)
            card = self.hands[player][index]
            chosen_color = self.best_color_for(player) if card.is_wild else None
            return self._play_card(player, index, chosen_color)

        events = [f"{self.player_name(player)} 抽了一张牌。"]
        card = self._draw_cards(player, 1)[0]
        if self.is_playable(card, player):
            chosen_color = self.best_color_for(player) if card.is_wild else None
            return events + self._play_card(player, len(self.hands[player]) - 1, chosen_color)

        self.current_player = self.next_player(from_player=player)
        events.append(f"{self.player_name(player)} 不能出牌。")
        events.append(self.turn_prompt())
        return events

    def _play_card(self, player: str, card_index: int, chosen_color: str | None) -> list[str]:
        hand = self.hands[player]
        if not 0 <= card_index < len(hand):
            raise RuleError("牌索引越界。")

        card = hand[card_index]
        if not self.is_playable(card, player):
            raise RuleError(f"{card.label} 现在不能出。")
        if card.is_wild and chosen_color not in COLORS:
            raise RuleError("Wild 牌必须指定新颜色。")

        played = hand.pop(card_index)
        self.discard_pile.append(played)
        self.current_color = chosen_color if played.is_wild else (played.color or self.current_color)
        self.drawn_this_turn = False

        actor = self.player_name(player)
        target = self.next_player(from_player=player)
        target_name = self.player_name(target)
        events = [f"{actor} 打出了 {played.label}。"]

        if played.is_wild:
            events.append(f"颜色改成了 {self.color_name(self.current_color)}。")
        if len(hand) == 1:
            events.append(f"{actor} 自动喊出 UNO！")
        if not hand:
            self.winner = player
            self.round_points = sum(
                card_points(other_card)
                for other_player in self.players
                if other_player != player
                for other_card in self.hands[other_player]
            )
            events.append(f"{actor} 率先出完了所有手牌。")
            events.append(f"本轮得分：{self.round_points}。")
            return events

        if played.rank == "skip":
            if len(self.players) == 2:
                self.current_player = player
            else:
                self.current_player = self.next_player(from_player=target)
            events.append(f"{target_name} 的回合被跳过。")
            events.append(self.turn_prompt())
            return events

        if played.rank == "reverse":
            if len(self.players) == 2:
                self.current_player = player
                events.append("双人规则下 Reverse 等同于 Skip。")
            else:
                self.direction *= -1
                self.current_player = self.next_player(from_player=player)
                events.append("出牌方向已反转。")
            events.append(self.turn_prompt())
            return events

        if played.rank == "draw_two":
            self._draw_cards(target, 2)
            self.current_player = self.next_player(from_player=target)
            events.append(f"{target_name} 抽了 2 张牌并被跳过。")
            events.append(self.turn_prompt())
            return events

        if played.rank == "wild_draw_four":
            self._draw_cards(target, 4)
            self.current_player = self.next_player(from_player=target)
            events.append(f"{target_name} 抽了 4 张牌并被跳过。")
            events.append(self.turn_prompt())
            return events

        self.current_player = target
        events.append(self.turn_prompt())
        return events

    def _choose_ai_card(self, player: str, playable_indices: list[int]) -> int:
        color_counts = Counter(card.color for card in self.hands[player] if card.color)
        target_player = self.next_player(from_player=player)
        target_cards = len(self.hands[target_player])
        table_danger = min(len(self.hands[other]) for other in self.players if other != player)

        def score(index: int) -> tuple[float, float]:
            card = self.hands[player][index]
            score_value = 0.0

            if card.rank in ACTION_RANKS:
                score_value += 12
            if card.rank == "wild":
                score_value -= 5
            if card.rank == "wild_draw_four":
                score_value -= 2
            if table_danger <= 2 and card.rank in ("skip", "reverse", "draw_two", "wild_draw_four"):
                score_value += 18
            if target_cards <= 2 and card.rank in ("skip", "draw_two", "wild_draw_four"):
                score_value += 6
            if target_cards == 1 and card.rank == "wild":
                score_value += 8
            if card.color:
                score_value += color_counts[card.color] * 3
                if card.color == self.current_color:
                    score_value += 3
            if card.rank == self.top_card.rank:
                score_value += 2
            if card.rank.isdigit():
                score_value += 1
            return score_value, -index

        return max(playable_indices, key=score)

    def _draw_cards(self, player: str, count: int) -> list[Card]:
        cards: list[Card] = []
        for _ in range(count):
            if not self.draw_pile:
                self._reshuffle_discard_into_draw()
            if not self.draw_pile:
                break
            cards.append(self.draw_pile.pop())
        if not cards:
            raise RuleError("已经没有可抽的牌了。")
        self.hands[player].extend(cards)
        return cards

    def _reshuffle_discard_into_draw(self) -> None:
        if len(self.discard_pile) <= 1:
            return
        top = self.discard_pile.pop()
        self.draw_pile = self.discard_pile[:]
        self._rng.shuffle(self.draw_pile)
        self.discard_pile = [top]
