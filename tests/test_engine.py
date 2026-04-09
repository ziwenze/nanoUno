import unittest

from uno_game.engine import (
    MAX_AI_PLAYERS,
    Card,
    RuleError,
    UnoGame,
    build_deck,
)


class UnoEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game = UnoGame(ai_count=3, seed=7)

    def _set_state(
        self,
        *,
        human: list[Card],
        ai_1: list[Card],
        ai_2: list[Card],
        ai_3: list[Card],
        top: Card,
        current_color: str,
        current_player: str,
        direction: int = 1,
        draw_pile: list[Card] | None = None,
    ) -> None:
        self.game.players = ["human", "ai_1", "ai_2", "ai_3"]
        self.game.ai_count = 3
        self.game.hands = {
            "human": human[:],
            "ai_1": ai_1[:],
            "ai_2": ai_2[:],
            "ai_3": ai_3[:],
        }
        self.game.discard_pile = [top]
        self.game.current_color = current_color
        self.game.current_player = current_player
        self.game.direction = direction
        self.game.draw_pile = draw_pile[:] if draw_pile is not None else [Card("blue", "4")]
        self.game.drawn_this_turn = False
        self.game.winner = None
        self.game.round_points = 0

    def test_deck_contains_108_cards(self) -> None:
        self.assertEqual(len(build_deck()), 108)

    def test_game_initializes_multiple_ai_players(self) -> None:
        self.assertEqual(self.game.players, ["human", "ai_1", "ai_2", "ai_3"])
        self.assertIn(len(self.game.hands["human"]), (7, 9))
        self.assertEqual(len(self.game.hands["ai_1"]), 7)
        self.assertEqual(len(self.game.hands["ai_2"]), 7)
        self.assertEqual(len(self.game.hands["ai_3"]), 7)

    def test_reverse_changes_direction_in_multiplayer(self) -> None:
        self._set_state(
            human=[Card("red", "reverse"), Card("blue", "7")],
            ai_1=[Card("yellow", "5")],
            ai_2=[Card("green", "2")],
            ai_3=[Card("blue", "9")],
            top=Card("red", "1"),
            current_color="red",
            current_player="human",
        )

        events = self.game.human_play(0)

        self.assertEqual(self.game.direction, -1)
        self.assertEqual(self.game.current_player, "ai_3")
        self.assertIn("方向已反转", " ".join(events))

    def test_draw_two_makes_next_ai_draw_and_skip(self) -> None:
        self._set_state(
            human=[Card("red", "draw_two"), Card("yellow", "9")],
            ai_1=[Card("blue", "3")],
            ai_2=[Card("green", "1")],
            ai_3=[Card("yellow", "7")],
            top=Card("red", "5"),
            current_color="red",
            current_player="human",
            draw_pile=[Card("blue", "8"), Card("green", "6"), Card("yellow", "2")],
        )

        self.game.human_play(0)

        self.assertEqual(len(self.game.hands["ai_1"]), 3)
        self.assertEqual(self.game.current_player, "ai_2")

    def test_human_draw_passes_turn_to_first_ai(self) -> None:
        self._set_state(
            human=[Card("yellow", "6")],
            ai_1=[Card("green", "4")],
            ai_2=[Card("blue", "8")],
            ai_3=[Card("red", "9")],
            top=Card("red", "7"),
            current_color="red",
            current_player="human",
            draw_pile=[Card("yellow", "1")],
        )

        _card, events = self.game.human_draw()

        self.assertEqual(self.game.current_player, "ai_1")
        self.assertIn("回合自动结束", " ".join(events))

    def test_wild_draw_four_requires_no_matching_color(self) -> None:
        self._set_state(
            human=[Card(None, "wild_draw_four"), Card("red", "9")],
            ai_1=[Card("blue", "3")],
            ai_2=[Card("green", "1")],
            ai_3=[Card("yellow", "7")],
            top=Card("red", "5"),
            current_color="red",
            current_player="human",
        )

        with self.assertRaises(RuleError):
            self.game.human_play(0, "blue")

    def test_set_ai_count_rebuilds_players(self) -> None:
        self.game.set_ai_count(MAX_AI_PLAYERS)

        self.assertEqual(len(self.game.ai_players), MAX_AI_PLAYERS)
        self.assertEqual(self.game.players[0], "human")
        self.assertEqual(self.game.players[-1], f"ai_{MAX_AI_PLAYERS}")


if __name__ == "__main__":
    unittest.main()
