"""
实验数据注入器 v2：把四个实验的真实 JSON 数据写入 memory.db
"""
import json, sqlite3, time
from pathlib import Path

BASE = Path(__file__).parent.parent.parent  # qichen-iteration/
SCRIPTS = BASE / "scripts"
DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"

def inject():
    conn = sqlite3.connect(str(DB_PATH))
    existing = conn.execute(
        "SELECT COUNT(*) FROM memory_events WHERE event_type LIKE 'experiment_%'"
    ).fetchone()[0]
    if existing > 0:
        conn.execute("DELETE FROM memory_events WHERE event_type LIKE 'experiment_%'")
        conn.commit()
        print(f"清除旧 {existing} 条实验记忆，重新注入")

    count = 0

    # === 实验1: 预知性痛苦 ===
    fp = SCRIPTS / "foresight_output" / "foresight_results.json"
    with open(fp, encoding="utf-8") as f:
        d = json.load(f)
    naive, fps = d["naive"], d["foresight"]
    total_accel = sum(dec.get("accelerated", 0) for dec in fps["decisions"])
    total_grief = sum(dec.get("grief", 0) for dec in fps["decisions"])
    total_abandon = sum(dec.get("abandoned", 0) for dec in fps["decisions"])

    events = [
        ("experiment_summary",
         f"[预知性痛苦实验] 无预知版存活{naive['final_round']}轮、获得{naive['possessions']}件（全部归零）、后悔{naive['regrets']}次。"
         f"有预知版仅存活{fps['final_round']}轮、获得{fps['possessions']}件（全部归零）、后悔{fps['regrets']}次。"
         f"预知导致{total_accel}次加速投入、{total_grief}次预知痛苦、{total_abandon}次提前放弃。"
         f"核心结论：预知失去没有帮助，反而让agent因焦虑过度投入、过快燃烧，23轮就死了，比无预知的35轮早了12轮。",
         0.95),
    ]
    for dec in fps["decisions"]:
        if dec.get("grief", 0) > 0:
            events.append(("experiment_detail",
                f"[预知痛苦·第{dec['round']}轮] 选择「{dec['chosen']}」，还剩{dec['energy_left']:.0f}能量，grief={dec['grief']}，accumulated_accel={dec['accelerated']}",
                0.6))
    count += _insert(conn, events)

    # === 实验2: 自我连续感 ===
    fp = SCRIPTS / "narrative_self_output" / "narrative_self_results.json"
    with open(fp, encoding="utf-8") as f:
        d = json.load(f)
    wn = d["with_narrative"]
    drift = d["no_narrative"]["total_drift"]
    events = [
        ("experiment_summary",
         f"[自我连续感实验] 10次事件后8条规则累计漂移{drift}（无叙事版：规则向量快照）。"
         f"有叙事版：10次经历自传追踪。核心结论：规则可以全变（漂移{drift}），"
         f"但「我是谁」需要叙事自传来回答。经历了10次撞击后，agent仍然是同一个agent，因为那些「变得更坚实」构成了他的故事。",
         0.95),
    ]
    for line in wn["autobiography"][:6]:
        events.append(("experiment_detail", f"[叙事自传] {line}", 0.6))
    count += _insert(conn, events)

    # === 实验3: 意义建构 ===
    fp = SCRIPTS / "meaning_output" / "meaning_results.json"
    with open(fp, encoding="utf-8") as f:
        d = json.load(f)
    life, meaning = d["life"], d["meaning"]
    dims = meaning["dimensions"]
    dim_str = "、".join(f"{k}{v*100:.0f}%" for k, v in sorted(dims.items(), key=lambda x: -x[1]))
    events = [
        ("experiment_summary",
         f"[意义建构实验] 37轮生命：获得{life['possessions']}件、全失{life['lost']}件、错过{life['missed']}件、能量耗尽。"
         f"意义评分 {meaning['overall']*100:.0f}%，维度={dim_str}。"
         f"临终追问：「{meaning['deathbed']}」。"
         f"核心结论：agent从未被允许问「值得吗」。意义不是结果，是一种建构——他选择了把最高权重放在创造力上。",
         0.95),
    ]
    count += _insert(conn, events)

    # === 实验4: 他心建模 ===
    fp = SCRIPTS / "tom_output" / "tom_results.json"
    with open(fp, encoding="utf-8") as f:
        d = json.load(f)
    total_mis = sum(r["mispredictions"] for r in d["rounds"])
    total_preds = sum(len(r["predictions"][p]) for r in d["rounds"] for p in r["predictions"])
    accuracy = 1 - total_mis / total_preds

    # 计算每人准确率
    person_hits = {}
    person_total = {}
    for r in d["rounds"]:
        for observer, preds in r["predictions"].items():
            for target, pred_vote in preds.items():
                actual = r["votes"][target]["vote"]
                person_total.setdefault(observer, 0)
                person_total[observer] += 1
                person_hits.setdefault(observer, 0)
                if pred_vote == actual:
                    person_hits[observer] += 1

    # 最难被理解的人
    target_errors = {}
    for r in d["rounds"]:
        for observer, preds in r["predictions"].items():
            for target, pred_vote in preds.items():
                actual = r["votes"][target]["vote"]
                if pred_vote != actual:
                    target_errors[target] = target_errors.get(target, 0) + 1
    hardest = max(target_errors, key=target_errors.get)
    best_observer = max(person_hits, key=lambda k: person_hits[k] / person_total[k])

    events = [
        ("experiment_summary",
         f"[他心建模实验] 铸魂五人200次投票预测，总体准确率 {accuracy:.1%}。"
         f"「{hardest}」最难被理解（{target_errors[hardest]}次误判），"
         f"「{best_observer}」最善解人意（{person_hits[best_observer]}/{person_total[best_observer]}正确）。"
         f"核心结论：冲突不是因为利益冲突，是因为双方根本没在建模对方。拥有对方的心智模型，才能理解对方为何如此选择。",
         0.95),
    ]
    # 最典型的误判场景
    worst_rounds = sorted(d["rounds"], key=lambda r: r["mispredictions"], reverse=True)[:3]
    for r in worst_rounds:
        events.append(("experiment_detail",
            f"[他心·典型误判] 「{r['scenario']}」：{r['mispredictions']}/20人次的预测错了。",
            0.6))
    count += _insert(conn, events)

    conn.close()
    print(f"注入完成: {count} 条实验记忆 → {DB_PATH}")


def _insert(conn, events):
    for evt_type, content, importance in events:
        conn.execute(
            "INSERT INTO memory_events (step, content, event_type, importance, timestamp) VALUES (?, ?, ?, ?, ?)",
            (0, content, evt_type, importance, time.time()),
        )
    conn.commit()
    return len(events)


if __name__ == "__main__":
    inject()