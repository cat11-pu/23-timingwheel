"""timingwheel.py：分层 timingwheel（槽位 + 级联下沉 + 快照/恢复）。

- 第 L 层每个槽覆盖 slots^L 个刻度，槽用绝对窗口号索引；
- advance 只弹出已经过去的非空槽（每层一个小顶堆），不遍历全部定时器；
- 高阶槽到期时把未到期定时器下沉一层，计入 cascades；
- persist/restore 用逐行 JSON 记录，尾部半条记录忽略。
"""
from __future__ import annotations

import heapq
import json


class TimerWheel:
    def __init__(self, slots: int = 8, levels: int = 3):
        self.slots = slots
        self.levels = levels
        self.deadlines = {}          # timer_id -> deadline（仅等待中的）
        self.fired = []              # 已触发，按触发顺序
        self.cascades = 0
        self.duplicates = 0
        self.now = 0
        self._seq = 0                # 加入顺序号
        self._meta = {}              # timer_id -> (deadline, seq)，仅等待中的
        self._levels = {}            # timer_id -> 当前所在层（触发/取消后保留）
        self._cancelled = set()
        self._fired_set = set()
        self._buckets = [dict() for _ in range(levels)]  # 每层：窗口号 -> [(seq, deadline, id)]
        self._heaps = [[] for _ in range(levels)]        # 每层：非空窗口号小顶堆

    def _scale(self, level: int) -> int:
        return self.slots ** level

    def _level_for(self, delay: int) -> int:
        level = 0
        span = self.slots
        while level < self.levels - 1 and delay > span:
            level += 1
            span *= self.slots
        return level

    def _insert(self, timer_id: str, deadline: int, seq: int, level: int) -> None:
        window = deadline // self._scale(level)
        bucket = self._buckets[level]
        if window not in bucket:
            bucket[window] = []
            heapq.heappush(self._heaps[level], window)
        bucket[window].append((seq, deadline, timer_id))
        self._levels[timer_id] = level

    def schedule(self, timer_id: str, delay: int, at: int) -> dict:
        deadline = at + delay
        self._seq += 1
        self.deadlines[timer_id] = deadline
        self._meta[timer_id] = (deadline, self._seq)
        self._cancelled.discard(timer_id)
        self._insert(timer_id, deadline, self._seq, self._level_for(delay))
        return {"deadline": deadline}

    def advance(self, now: int) -> dict:
        """只检查各层已经过去的非空槽，高层未到期者下沉。"""
        if now > self.now:
            self.now = now
        due = []
        for level in range(self.levels - 1, -1, -1):
            limit = now // self._scale(level)
            heap = self._heaps[level]
            buckets = self._buckets[level]
            while heap and heap[0] <= limit:
                window = heapq.heappop(heap)
                for seq, deadline, timer_id in buckets.pop(window, []):
                    if self._meta.get(timer_id) != (deadline, seq):
                        continue  # 已取消或已被重新调度，惰性删除
                    if deadline <= now:
                        due.append((deadline, seq, timer_id))
                    else:
                        self._insert(timer_id, deadline, seq, level - 1)
                        self.cascades += 1
        due.sort()
        fired_ids = []
        for _deadline, _seq, timer_id in due:
            if timer_id in self._fired_set:
                self.duplicates += 1
                continue
            self._fired_set.add(timer_id)
            self.fired.append(timer_id)
            self.deadlines.pop(timer_id, None)
            self._meta.pop(timer_id, None)
            fired_ids.append(timer_id)
        return {"fired": fired_ids}

    def cancel(self, timer_id: str) -> dict:
        existed = timer_id in self.deadlines
        if existed:
            self.deadlines.pop(timer_id, None)
            self._meta.pop(timer_id, None)
            self._cancelled.add(timer_id)
        return {"cancelled": existed}

    def level_of(self, timer_id: str) -> int:
        return self._levels.get(timer_id, 0)

    def persist(self, path: str = None) -> bytes:
        lines = [json.dumps({"type": "meta", "slots": self.slots,
                             "levels": self.levels, "now": self.now, "seq": self._seq})]
        for timer_id, (deadline, seq) in self._meta.items():
            lines.append(json.dumps({"type": "timer", "id": timer_id, "deadline": deadline,
                                     "seq": seq, "level": self._levels.get(timer_id, 0)}))
        for timer_id in self.fired:
            lines.append(json.dumps({"type": "fired", "id": timer_id}))
        for timer_id in sorted(self._cancelled):
            lines.append(json.dumps({"type": "cancelled", "id": timer_id}))
        blob = ("\n".join(lines) + "\n").encode("utf-8")
        if path:
            with open(path, "wb") as handle:
                handle.write(blob)
        return blob

    def restore(self, blob: bytes = None) -> dict:
        if blob:
            for raw in blob.splitlines():
                if not raw.strip():
                    continue
                try:
                    record = json.loads(raw)
                except ValueError:
                    continue  # 尾部半条记录等损坏行直接忽略
                kind = record.get("type")
                if kind == "meta":
                    self.now = record.get("now", 0)
                    self._seq = record.get("seq", 0)
                elif kind == "timer":
                    timer_id = record["id"]
                    if timer_id in self._meta:
                        self.duplicates += 1
                        continue
                    deadline = record["deadline"]
                    seq = record.get("seq", 0)
                    self.deadlines[timer_id] = deadline
                    self._meta[timer_id] = (deadline, seq)
                    level = record.get("level")
                    if level is None:
                        level = self._level_for(deadline)
                    self._insert(timer_id, deadline, seq, level)
                elif kind == "fired":
                    timer_id = record["id"]
                    if timer_id not in self._fired_set:
                        self._fired_set.add(timer_id)
                        self.fired.append(timer_id)
                elif kind == "cancelled":
                    self._cancelled.add(record["id"])
        return {"waiting": len(self.deadlines), "fired": sorted(self.fired),
                "duplicates": self.duplicates}

    def stats(self) -> dict:
        return {"waiting": len(self.deadlines), "fired": len(self.fired),
                "cancelled": len(self._cancelled), "cascades": self.cascades,
                "duplicates": self.duplicates, "slots": self.slots, "levels": self.levels}
