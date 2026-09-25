# timingwheel

纯 Python 标准库的分层 timingwheel：第 L 层每槽覆盖 `slots^L` 个刻度，
`advance` 只检查经过的非空槽，高阶槽到期时定时器下沉一层（计入 `cascades`）。

## 用法

    wheel = TimerWheel(slots=8, levels=3)
    wheel.schedule("t1", 3, 0)      # -> {"deadline": 3}
    wheel.advance(4)["fired"]       # -> ["t1"]
    wheel.cancel("t2")              # -> {"cancelled": True/False}
    wheel.level_of("t1")            # 当前所在层
    blob = wheel.persist()          # 快照（可选 path 落盘）
    TimerWheel().restore(blob)      # -> {"waiting", "fired", "duplicates"}

## 测试

    python3 -m unittest discover -s tests -v

## 场景自检

    python3 check_sample.py
