# 即时配送派单策略 Playbook（嵌入 system prompt 的 Teacher 知识库）

## 问题
给定一批候选行 `(task_id_list, courier_id, score, willingness)`：为每个任务（或任务组）选骑手，
使「期望成本」最低。score 是罚分（越低越好）；willingness 是骑手接单意愿(0~1)。
一个任务组可派给多个骑手（多派），按 willingness 递归期望聚合：先派意愿高的，未接则回退下一个。
未覆盖任务有重罚（覆盖率优先）。

## 硬约束（绝不能违反）
- 只能写 `def propose(candidates, all_tasks, deadline, helpers)`，返回 `list[tuple[str, list[str]]]`。
- 每个 `(task_key, [courier_id, ...])` 的 `task_key` 必须是候选行里出现过的 `task_id_list` 原文。
- 同一个 courier_id 不能在多个分组里重复使用。
- 同一个 task_id 不能被两个分组重复覆盖。
- 只能用白名单 import：collections / heapq / itertools / math / random / time。禁 os/sys/eval/exec/open/网络/文件。
- 禁 `while`；用 `for` + `helpers["time_left"](deadline)` 做 anytime 截断。

## candidate 行结构（逐字记住）
`(task_key:str, task_ids:tuple, courier_id:str, score:float, willingness:float, row_index:int)`
即 `row[0]=task_key, row[1]=task_ids元组, row[2]=courier_id, row[3]=score, row[4]=willingness, row[5]=行号`。

## 按 regime 的优化方向
- large / medium（任务多）：贪心可行解打底，再对高 score 任务做「多派」降低未接风险；优先低 score、低 len(task_ids) 的行。
- low-willingness（意愿普遍低）：单纯按 score 贪心会大量未接 → 对关键任务多派 2~3 个高 willingness 骑手；排序兼顾 willingness。
- scarce（骑手 ≤ 任务）：骑手是瓶颈 → 优先用 bundle（一个骑手带多任务，len(task_ids)>1）提高覆盖；控制骑手复用。
- small / tiny：可做更细的组合搜索；but 仍要在 deadline 内。

## 常见陷阱（try_error 高频）
- 只覆盖少量任务 → 未覆盖重罚 → 成本暴涨被拒。务必尽量覆盖 all_tasks。
- 重复用同一 courier / 重复覆盖同一 task → 非法被拒。
- 排序键搞反（score 越低越好，不是越高）。
- 不查 deadline 写成重循环 → 超时被拒。

## 一个能通过的最小可行 propose（贪心基线，可在此基础上改进）
```python
def propose(candidates, all_tasks, deadline, helpers):
    time_left = helpers.get("time_left")
    used, covered, result = set(), set(), []
    rows = sorted(candidates, key=lambda r: (len(r[1]), r[3] / max(r[4], 0.001), r[3]))
    for task_key, task_ids, courier_id, score, willingness, _ in rows:
        if time_left is not None and time_left(deadline) <= 0.02:
            break
        if courier_id in used:
            continue
        if any(t in covered for t in task_ids):
            continue
        used.add(courier_id); covered.update(task_ids)
        result.append((task_key, [courier_id]))
        if covered >= set(all_tasks):
            break
    return result
```
目标：在上面基础上，针对当前 regime 提出**一个**小改进假设（如对未接风险高的任务追加第二骑手），用 smoke_test 验证后再 final。
