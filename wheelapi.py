"""wheelapi.py：对外门面（老接口 schedule/advance 的返回结构不能改）。"""
from __future__ import annotations

from timingwheel import TimerWheel


class Scheduler:
    def __init__(self, slots: int = 8, levels: int = 3):
        self.wheel = TimerWheel(slots, levels)

    def schedule(self, timer_id: str, delay: int, at: int) -> dict:
        return self.wheel.schedule(timer_id, delay, at)

    def advance(self, now: int) -> dict:
        return self.wheel.advance(now)

    def cancel(self, timer_id: str) -> dict:
        return self.wheel.cancel(timer_id)

    def snapshot(self) -> bytes:
        return self.wheel.persist()

    def rebuild(self, blob: bytes = None) -> dict:
        return self.wheel.restore(blob)
