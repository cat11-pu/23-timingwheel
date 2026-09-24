"""timingwheel.py：定时器（基线：平坦列表，无分层、无快照）。"""
from __future__ import annotations


class TimerWheel:
    def __init__(self, slots: int = 8, levels: int = 3):
        self.slots = slots
        self.levels = levels
        self.pending = []
        self.deadlines = {}
        self.fired = []
        self.cascades = 0

    def schedule(self, timer_id: str, delay: int, at: int) -> dict:
        deadline = at + delay
        self.pending.append((deadline, timer_id))
        self.deadlines[timer_id] = deadline
        return {"deadline": deadline}

    def advance(self, now: int) -> dict:
        """基线：每次推进线性扫全部定时器。"""
        due = sorted(item for item in self.pending if item[0] <= now)
        for item in due:
            self.pending.remove(item)
            self.deadlines.pop(item[1], None)
            self.fired.append(item[1])
        return {"fired": [item[1] for item in due]}

    def cancel(self, timer_id: str) -> dict:
        existed = timer_id in self.deadlines
        self.deadlines.pop(timer_id, None)
        self.pending = [item for item in self.pending if item[1] != timer_id]
        return {"cancelled": existed}

    def level_of(self, timer_id: str) -> int:
        """基线：没有层级概念。"""
        return 0

    def persist(self) -> bytes:
        raise NotImplementedError("快照还没实现")

    def restore(self, blob: bytes = None) -> dict:
        raise NotImplementedError("重启恢复还没实现")

    def stats(self) -> dict:
        return {"waiting": len(self.pending), "fired": len(self.fired),
                "cancelled": 0, "cascades": self.cascades, "slots": self.slots, "levels": self.levels}
