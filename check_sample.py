"""check_sample.py：按 sample/timers.json 走一圈，打印验收面。"""
import json
import os
import sys

from timingwheel import TimerWheel


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("sample", "timers.json")
    with open(path, encoding="utf-8") as handle:
        spec = json.load(handle)
    wheel = TimerWheel(spec["slots"], spec["levels"])
    for item in spec["timers"]:
        wheel.schedule(item["id"], item["delay"], item["at"])
    for timer_id in spec["cancel"]:
        wheel.cancel(timer_id)
    order = []
    for moment in spec["advances"]:
        order.extend(wheel.advance(moment)["fired"])
    levels = [(item["id"], wheel.level_of(item["id"])) for item in spec["timers"]
              if item["id"] not in spec["cancel"]]
    before = sorted(wheel.stats()["waiting"] for _ in [0]) and wheel.stats()
    blob = wheel.persist()
    reborn = TimerWheel(spec["slots"], spec["levels"])
    restored = reborn.restore(blob)
    print("触发顺序 =", order)
    print("每个定时器的层级 =", levels)
    print("取消的定时器是否触发 =", any(item in order for item in spec["cancel"]))
    print("重启前等待数 =", before.get("waiting"))
    print("重启后等待数 =", restored.get("waiting"))
    print("重启后已触发 =", restored.get("fired"))
    print("重启后仍等待的定时器 =", sorted(reborn.deadlines))
    print("重复触发次数 =", restored.get("duplicates"))
    print("槽位数 =", spec["slots"])
    print("层级数 =", spec["levels"])
    print("每次推进检查的槽数上限 =", spec["levels"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
