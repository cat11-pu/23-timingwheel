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


if __name__ == "__main__":
    unittest.main()
