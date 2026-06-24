def propose(candidates, all_tasks, deadline, helpers):
    time_left = helpers.get("time_left")
    rows = list(candidates)
    used_couriers = set()
    covered_tasks = set()
    result = []
    sorted_rows = sorted(rows, key=lambda r: (len(r[1]), r[3] / max(r[4], 0.001), r[3]))
    for task_key, task_ids, courier_id, score, willingness, _ in sorted_rows:
        if time_left is not None and time_left(deadline) <= 0.02:
            break
        if courier_id in used_couriers:
            continue
        if any(t in covered_tasks for t in task_ids):
            continue
        used_couriers.add(courier_id)
        covered_tasks.update(task_ids)
        result.append((task_key, [courier_id]))
        if covered_tasks >= set(all_tasks):
            break
    # 第二阶段：对低意愿任务追加第二骑手（多派）
    # 当前场景平均意愿0.3，所以willingness<0.4都算低
    low_will_entries = []
    for task_key, task_ids, courier_id, score, willingness, _ in rows:
        if time_left is not None and time_left(deadline) <= 0.02:
            break
        if task_key not in [r[0] for r in result]:
            continue
        if willingness < 0.4:
            assigned = [r for r in result if r[0] == task_key]
            if assigned:
                low_will_entries.append((task_key, task_ids, score, willingness))
    for task_key, task_ids, score, willingness in low_will_entries:
        if time_left is not None and time_left(deadline) <= 0.02:
            break
        backup_candidates = []
        for row in rows:
            if row[0] == task_key and row[2] not in used_couriers:
                backup_candidates.append(row)
        if not backup_candidates:
            continue
        backup_candidates.sort(key=lambda r: -r[4])
        best_backup = backup_candidates[0]
        if best_backup[4] > 0.3:  # 只追加意愿高于平均的
            used_couriers.add(best_backup[2])
            for i, (tk, couriers) in enumerate(result):
                if tk == task_key:
                    result[i] = (tk, couriers + [best_backup[2]])
                    break
    return result