# -*- coding: utf-8 -*-
"""前后正确率对比 + 典型单词完整时间线（生产库）。"""
import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROD_DB = Path(r"C:\Users\Administrator\AppData\Roaming\WordMaster\wordmaster.db")

# 正确性权重（与 words.py 一致）
RESULT_SCORE = {"too_easy": 1.0, "know": 1.0, "fuzzy": 0.5, "unknown": 0.0,
                "correct": 1.0, "incorrect": 0.0}


def parse_dt(s):
    if not s:
        return None
    s = str(s).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def main():
    con = sqlite3.connect(PROD_DB)
    cur = con.cursor()

    # 汇总每个单词的所有答题事件（study_records + learning_events），按时间排序
    cur.execute("""
        SELECT word_id, result, studied_at AS ts FROM study_records
        UNION ALL
        SELECT word_id,
               CASE WHEN result='correct' THEN 'correct' WHEN result='incorrect' THEN 'incorrect' ELSE result END,
               timestamp FROM learning_events
    """)
    events = {}
    for wid, result, ts in cur.fetchall():
        t = parse_dt(ts)
        if t is None:
            continue
        events.setdefault(wid, []).append((t, result))

    # 计算每个单词的前后正确率（前N vs 最近N，N=2；不足则首次 vs 最近）
    words = {}
    for wid, evs in events.items():
        evs.sort(key=lambda x: x[0])
        if len(evs) < 2:
            continue
        scores = [RESULT_SCORE.get(r, 0.0) for _, r in evs]
        en, cn = cur.execute("SELECT english, chinese FROM words WHERE id=?", (wid,)).fetchone()
        N = 2
        first_scores = scores[:N]
        last_scores = scores[-N:]
        first_acc = sum(first_scores) / len(first_scores)
        last_acc = sum(last_scores) / len(last_scores)
        words[wid] = {
            "english": en, "chinese": cn,
            "n_events": len(evs),
            "first_n": N, "last_n": N,
            "first_acc": round(first_acc, 3), "last_acc": round(last_acc, 3),
            "delta": round((last_acc - first_acc) * 100, 1),
            "events": [(t.strftime("%m-%d %H:%M"), r) for t, r in evs],
        }

    # 按事件数排序输出
    print("=== 有 ≥2 次答题的单词（前N vs 最近N，N=2）===")
    for wid in sorted(words, key=lambda w: (-words[w]["n_events"], words[w]["english"])):
        w = words[wid]
        print(f"{w['english']:<14} n={w['n_events']} 首次{w['first_n']}次={w['first_acc']:.0%} 最近{w['last_n']}次={w['last_acc']:.0%} Δ={w['delta']:+.1f}pp  | {w['events']}")

    print()
    print("=== 典型单词 absurd (2045) 完整时间线 ===")
    cur.execute("""
        SELECT 'study_record', result, studied_at, review_stage FROM study_records WHERE word_id=2045
        UNION ALL
        SELECT 'learning_event', activity_type || '/' || result || '/' || rating, timestamp, fsrs_after FROM learning_events WHERE word_id=2045
        UNION ALL
        SELECT 'mistake_record', source || '/' || mistake_type, first_occurred_at, last_occurred_at FROM mistake_records WHERE word_id=2045
    """)
    for row in cur.fetchall():
        print(row)

    print()
    print("=== 典型单词 absorb (2130) 完整时间线 ===")
    cur.execute("""
        SELECT 'study_record', result, studied_at, review_stage FROM study_records WHERE word_id=2130
        UNION ALL
        SELECT 'learning_event', activity_type || '/' || result || '/' || rating, timestamp, fsrs_after FROM learning_events WHERE word_id=2130
        UNION ALL
        SELECT 'mistake_record', source || '/' || mistake_type, first_occurred_at, last_occurred_at FROM mistake_records WHERE word_id=2130
    """)
    for row in cur.fetchall():
        print(row)

    print()
    print("=== absurd 的 learning_events 完整字段 ===")
    cur.execute("SELECT * FROM learning_events WHERE word_id=2045 ORDER BY id")
    for row in cur.fetchall():
        print(row)

    # 保存结果
    out = {"before_after": {wid: {k: v for k, v in words[wid].items() if k != "events"} for wid in words},
           "before_after_events": {wid: words[wid] for wid in words}}
    out_path = Path(r"C:\Users\Administrator\Desktop\WordMaster备份\WordMaster最终版\相关材料\用户验证数据\_before_after.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    # 验证 union 去重
    cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT word_id FROM study_records UNION SELECT DISTINCT word_id FROM learning_events)")
    print("\n去重学习单词数(union):", cur.fetchone()[0])
    cur.execute("SELECT COUNT(DISTINCT word_id) FROM study_records")
    print("study_records 去重:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(DISTINCT word_id) FROM learning_events")
    print("learning_events 去重:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM (SELECT word_id FROM study_records INTERSECT SELECT word_id FROM learning_events)")
    print("交集:", cur.fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
