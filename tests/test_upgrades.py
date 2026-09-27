import unittest
from types import SimpleNamespace
from game import Body, Game
from gestures import GestureInterpreter
from controls import InputController
from hand_tracking import HandPoints
from test_gestures import palm


def fist():
    points = palm()
    for base in (5, 9, 13, 17):
        x = points[base][0]
        points[base + 1] = (x, 0.50)
        points[base + 2] = (x, 0.55)
        points[base + 3] = (x, 0.62)
    points[4] = points[8]
    return points


def advance(game, seconds, **kwargs):
    count = round(seconds * 100)
    for _ in range(count):
        game.update(0.01, 0.5, False, True, **kwargs)


class GestureUpgradeTests(unittest.TestCase):
    def test_depth_geometry_recognizes_folded_fingers_despite_extended_projection(self):
        world = [(0, -0.06, 0)] * 21
        for base in (5, 9, 13, 17):
            x = base * 0.005
            world[base:base+4] = [(x, 0, 0), (x, 0.05, 0), (x, 0.025, 0.02), (x, 0, 0.02)]
        for coordinates in (world, [(z, x, y) for x, y, z in world]):
            gesture = GestureInterpreter()
            points = HandPoints(palm(), coordinates)
            self.assertTrue(gesture.update(points, 0).fist)
            result = gesture.update(points, 0.36)
            self.assertTrue(result.shield)
            self.assertFalse(result.shoot or result.toggle)
        for base in (5, 9, 13, 17):
            x = base * 0.005
            world[base:base+4] = [(x, 0, 0), (x, 0.03, 0), (x, 0.055, 0), (x, 0.08, 0)]
        self.assertFalse(GestureInterpreter().update(HandPoints(fist(), world), 0).fist)

    def test_established_fist_tolerates_one_jittering_tip_but_palm_exits(self):
        gesture = GestureInterpreter()
        uncertain = fist()
        uncertain[20] = palm()[20]
        self.assertFalse(gesture.update(uncertain, 0).fist)
        gesture.update(fist(), 0.1)
        self.assertTrue(gesture.update(uncertain, 0.2).fist)
        result = gesture.update(uncertain, 0.46)
        self.assertTrue(result.shield)
        self.assertFalse(result.shoot or result.toggle)
        self.assertFalse(gesture.update(palm(), 0.5).fist)

    def test_fist_hold_conflicts_and_release(self):
        gesture = GestureInterpreter()
        self.assertFalse(gesture.update(fist(), 0).shield)
        result = gesture.update(fist(), 0.36)
        self.assertTrue(result.shield)
        self.assertFalse(result.pinching or result.shoot or result.toggle)
        self.assertFalse(gesture.update(fist(), 12).shield)
        gesture.update(palm(), 12.1)
        gesture.update(fist(), 12.2)
        self.assertTrue(gesture.update(fist(), 12.6).shield)

    def test_fist_palm_center_steering_and_transition_continuity(self):
        gesture = GestureInterpreter()
        gesture.update(palm(), 0)
        before = gesture.x
        result = gesture.update(fist(), 0.1)
        self.assertAlmostEqual(result.x, before)
        moved = [(x + 0.1, y) for x, y in fist()]
        self.assertGreater(gesture.update(moved, 0.2).x, before)
        before_release = gesture.x
        result = gesture.update(palm(), 0.3)
        self.assertAlmostEqual(result.x, before_release)

    def test_loss_during_fist_does_not_reactivate(self):
        gesture = GestureInterpreter()
        gesture.update(fist(), 0)
        gesture.update(None, 0.2)
        gesture.update(fist(), 0.3)
        self.assertFalse(gesture.update(fist(), 1).shield)

    def test_stale_pinch_stops_before_pause_grace(self):
        controller = InputController()
        points = palm()
        points[4] = points[8]
        packet = SimpleNamespace(sequence=1, captured_at=1, hand=points, face=[(0.5, 0.5)])
        controller.update(packet, None, 1, 0.01)
        packet.sequence, packet.captured_at = 2, 1.1
        self.assertTrue(controller.update(packet, None, 1.1, 0.01).shoot)
        result = controller.update(packet, None, 1.35, 0.01)
        self.assertFalse(result.shoot or result.shield or result.toggle)
        self.assertTrue(controller.health.can_continue)

    def test_feedback_is_heuristic_and_edge_based(self):
        controller = InputController()
        points = palm()
        points[8] = (0.99, 0.2)
        packet = SimpleNamespace(sequence=1, captured_at=1, hand=points, face=[(0.5, 0.5)])
        controller.update(packet, None, 1, 0.01)
        self.assertIn('Hint:', controller.feedback)
        self.assertIn('fully into view', controller.feedback)


class CombatUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(seed=2)
        self.game.toggle(True)
        self.game.spawn_timer = 10000

    def test_shield_duration_cooldown_pause_and_reset(self):
        game = self.game
        self.assertTrue(game.activate_shield())
        game.damage()
        self.assertEqual(game.lives, 3)
        advance(game, 1)
        game.pause('test')
        advance(game, 3)
        self.assertAlmostEqual(game.shield_remaining, 1)
        game.toggle(True)
        advance(game, 1.01)
        self.assertAlmostEqual(game.shield_cooldown, 7.99, places=2)
        self.assertFalse(game.activate_shield())
        advance(game, 8)
        self.assertTrue(game.activate_shield())
        game.reset()
        self.assertEqual((game.shield_remaining, game.shield_cooldown), (0, 0))

    def test_armored_hits_and_destruction_scored_once(self):
        game = self.game
        enemy = Body(200, 300, 0, 46, 'armored', 3, 3)
        game.obstacles.append(enemy)
        for i in range(3):
            game.bullets.append(Body(200, 300, 0, 8))
            game.update(0.01, 0.5, False, True)
            self.assertEqual(enemy.hp, 2 - i)
            self.assertEqual(game.score, 0 if i < 2 else 75)
        game.hit_enemy(enemy)
        self.assertEqual(game.score, 75)
        self.assertFalse(game.obstacles)

    def test_combo_multiplier_expiry_damage_and_pause(self):
        game = self.game
        enemy = Body(200, 300, 0, 46, 'armored', 30, 30)
        for _ in range(15):
            game.hit_enemy(enemy)
        self.assertEqual(game.multiplier, 4)
        game.pause('test')
        advance(game, 3)
        self.assertEqual(game.combo_remaining, 2)
        game.toggle(True)
        advance(game, 2.01)
        self.assertEqual(game.multiplier, 1)
        for _ in range(5):
            game.hit_enemy(enemy)
        self.assertEqual(game.multiplier, 2)
        game.damage()
        self.assertEqual(game.multiplier, 1)

    def test_zigzag_is_bounded_and_deterministic(self):
        game = self.game
        enemy = Body(100, 150, 100, 28, 'zigzag', origin_x=100)
        game.obstacles.append(enemy)
        advance(game, 0.5)
        self.assertGreater(enemy.x, 100)
        self.assertGreaterEqual(enemy.rect().left, game.arena.left)
        self.assertAlmostEqual(enemy.y, 200)

    def test_boss_scheduling_suspends_spawns_and_advances_once(self):
        game = self.game
        game.wave, game.wave_time = 4, 19.999
        game.update(0.01, 0.5, False, True)
        self.assertEqual(game.wave, 5)
        self.assertIsNotNone(game.boss)
        boss = game.boss
        advance(game, 0.5)
        self.assertFalse(game.obstacles)
        self.assertEqual(game.wave, 5)
        while boss.hp > 0:
            game.hit_enemy(boss)
        points = game.score
        game.hit_enemy(boss)
        self.assertEqual((game.wave, game.score), (6, points))
        self.assertIsNone(game.boss)
        self.assertFalse(game.hostile_bullets or game.warning_lanes)

    def test_boss_two_telegraphed_patterns_pause_and_reset(self):
        game = self.game
        game.wave = 5
        game.start_boss()
        game.boss_timer = 0
        game.update(0.001, 0.5, False, True)
        self.assertEqual(game.boss_phase, 'warning')
        self.assertEqual(len(game.warning_lanes), 3)
        advance(game, 0.8)
        self.assertEqual(game.lives, 3)
        game.pause('test')
        timer = game.boss_timer
        advance(game, 3)
        self.assertEqual(game.boss_timer, timer)
        game.toggle(True)
        advance(game, 0.9)
        self.assertLess(game.lives, 3)
        game.boss_phase, game.boss_timer, game.attack_index = 'rest', 0, 1
        game.update(0.001, 0.5, False, True)
        self.assertEqual(len(game.fan_paths), 5)
        self.assertFalse(game.hostile_bullets)
        advance(game, 1.21)
        self.assertEqual(len(game.hostile_bullets), 5)
        game.reset()
        self.assertIsNone(game.boss)
        self.assertFalse(game.hostile_bullets or game.fan_paths or game.warning_lanes)

    def test_progressive_enemy_mix(self):
        game = self.game
        kinds = set()
        for wave in (1, 2, 3):
            game.wave = wave
            for _ in range(40):
                game.obstacles.clear()
                game.spawn_enemy()
                kinds.add(game.obstacles[0].kind)
            if wave == 1:
                self.assertEqual(kinds, {'normal'})
        self.assertEqual(kinds, {'normal', 'armored', 'zigzag'})
