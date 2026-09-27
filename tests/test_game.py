import unittest
from game import Game, Body


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(seed=3)
        self.game.toggle(True)
        self.game.spawn_timer = 100

    def test_face_loss_freezes_game_until_explicit_resume(self):
        game = self.game
        game.obstacles = [Body(200, 300, 100, 30)]
        game.update(0.02, 0.5, False, False)
        self.assertEqual(game.state, "paused")
        self.assertEqual(game.obstacles[0].y, 300)
        game.update(0.02, 0.5, False, True)
        self.assertEqual(game.state, "paused")
        game.toggle(False)
        self.assertEqual(game.state, "paused")
        game.toggle(True)
        game.update(0.02, 0.5, False, True)
        self.assertGreater(game.obstacles[0].y, 300)

    def test_bullet_destroys_one_obstacle(self):
        game = self.game
        game.obstacles = [Body(200, 300, 0, 30), Body(200, 300, 0, 30)]
        game.bullets = [Body(200, 300, 0, 8)]
        game.update(0.01, 0.5, False, True)
        self.assertEqual(game.score, 25)
        self.assertEqual(len(game.obstacles), 1)
        self.assertFalse(game.bullets)

    def test_collision_invulnerability_gameover_and_restart(self):
        game = self.game
        for lives in (2, 1, 0):
            game.invulnerable = 0
            game.obstacles = [Body(game.player.centerx, game.player.centery, 0, 30)]
            game.update(0.01, 0.5, False, True)
            self.assertEqual(game.lives, lives)
            if lives:
                game.obstacles = [Body(game.player.centerx, game.player.centery, 0, 30)]
                game.update(0.01, 0.5, False, True)
                self.assertEqual(game.lives, lives)
        self.assertEqual(game.state, "gameover")
        game.reset()
        self.assertEqual((game.state, game.score, game.lives), ("ready", 0, 3))
        self.assertFalse(game.obstacles)

    def test_dodge_score_and_player_bounds(self):
        game = self.game
        game.obstacles = [Body(200, game.arena.bottom + 40, 0, 30)]
        game.update(0.02, -3, False, True)
        self.assertEqual(game.score, 10)
        self.assertGreaterEqual(game.player.left, game.arena.left)
        game.update(0.02, 3, False, True)
        self.assertLessEqual(game.player.right, game.arena.right)

    def test_spawning_and_shoot_cooldown(self):
        game = self.game
        game.spawn_timer = 0
        game.update(0.01, 0.5, True, True)
        game.update(0.01, 0.5, True, True)
        self.assertEqual(len(game.obstacles), 1)
        self.assertEqual(len(game.bullets), 1)

    def test_motion_is_consistent_across_frame_rates(self):
        positions = []
        for fps in (10, 30, 120):
            game = Game(seed=1)
            game.toggle(True)
            game.spawn_timer = 100
            game.obstacles = [Body(100, 150, 100, 30)]
            for _ in range(fps):
                game.update(1 / fps, 0.5, False, True)
            positions.append(game.obstacles[0].y)
        for y in positions:
            self.assertAlmostEqual(y, 250)

    def test_difficulty_remains_bounded(self):
        game = self.game
        game.elapsed = 10_000
        game.spawn_timer = 0
        game.update(0.001, 0.5, False, True)
        self.assertLessEqual(game.obstacles[0].speed, 320)
        self.assertGreaterEqual(game.spawn_timer, 0.28)


if __name__ == "__main__":
    unittest.main()
