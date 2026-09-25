import unittest

from timingwheel import TimerWheel
from wheelapi import Scheduler


class TestTimerWheel(unittest.TestCase):
    def test_schedule_then_advance(self):
        wheel = TimerWheel()
        wheel.schedule("t1", 3, 0)
        self.assertEqual(wheel.advance(5)["fired"], ["t1"])

    def test_advance_nothing_due(self):
        wheel = TimerWheel()
        wheel.schedule("t1", 30, 0)
        self.assertEqual(wheel.advance(5)["fired"], [])

    def test_cancel_prevents_fire(self):
        wheel = TimerWheel()
        wheel.schedule("t1", 3, 0)
        wheel.cancel("t1")
        self.assertEqual(wheel.advance(50)["fired"], [])

    def test_stats_shape(self):
        self.assertIn("waiting", TimerWheel().stats())

    def test_scheduler_wraps_wheel(self):
        scheduler = Scheduler()
        scheduler.schedule("t1", 1, 0)
        self.assertEqual(scheduler.advance(2)["fired"], ["t1"])

    def test_level_of_by_delay(self):
        wheel = TimerWheel()
        wheel.schedule("a", 8, 0)
        wheel.schedule("b", 9, 0)
        wheel.schedule("c", 65, 0)
        self.assertEqual(wheel.level_of("a"), 0)
        self.assertEqual(wheel.level_of("b"), 1)
        self.assertEqual(wheel.level_of("c"), 2)

    def test_cascade_sinks_timer(self):
        wheel = TimerWheel()
        wheel.schedule("a", 9, 0)
        wheel.advance(8)
        self.assertEqual(wheel.level_of("a"), 0)
        self.assertEqual(wheel.cascades, 1)
        self.assertEqual(wheel.advance(9)["fired"], ["a"])

    def test_fire_order_by_deadline_then_seq(self):
        wheel = TimerWheel()
        wheel.schedule("b", 5, 0)
        wheel.schedule("a", 5, 0)
        wheel.schedule("c", 3, 0)
        self.assertEqual(wheel.advance(10)["fired"], ["c", "b", "a"])

    def test_persist_restore_roundtrip(self):
        wheel = TimerWheel()
        wheel.schedule("t1", 3, 0)
        wheel.schedule("t2", 30, 0)
        wheel.schedule("t3", 40, 0)
        wheel.cancel("t3")
        wheel.advance(5)
        reborn = TimerWheel()
        info = reborn.restore(wheel.persist())
        self.assertEqual(info["waiting"], 1)
        self.assertEqual(info["fired"], ["t1"])
        self.assertEqual(info["duplicates"], 0)
        self.assertEqual(dict(reborn.deadlines), {"t2": 30})
        self.assertEqual(reborn.advance(30)["fired"], ["t2"])

    def test_restore_ignores_trailing_partial_record(self):
        wheel = TimerWheel()
        wheel.schedule("t1", 3, 0)
        blob = wheel.persist() + b'{"type":"timer","id":"broken'
        reborn = TimerWheel()
        info = reborn.restore(blob)
        self.assertEqual(info["waiting"], 1)
        self.assertEqual(sorted(reborn.deadlines), ["t1"])


if __name__ == "__main__":
    unittest.main()
