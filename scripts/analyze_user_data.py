# -*- coding: utf-8 -*-
"""
WordMaster 用户验证数据 —— 真实数据统计脚本
只读取真实 SQLite 数据库，不编造任何数字。
主库：生产数据库 AppData/Roaming/WordMaster/wordmaster.db
参考：开发库 server/wordmaster.db（用于补充 FSRS 记忆状态，明确标注）
"""
import sqlite3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROD_DB = Path(r"C:\Users\Administrator\AppData\Roaming\WordMaster\wordmaster.db")
DEV_DB = Path(r"C:\Users\Administrator\Desktop\WordMaster备份\WordMaster最终版\WordMaster本体文件\server\wordmaster.db")

# FSRS-5 retrievability: R(t) = (1 + FACTOR * t / S) ** DECAY
FACTOR = 19.0 / 81.0
DECAY = -0.5

STAT_TIME = datetime(2026, 9, 27, 15, 0, 0)  # 统计时点（报告生成时间）


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


def retrievability(stability, last_review, at):
    """FSRS-5 可提取性（记忆保持率），0..1。"""
    if stability is None or last_review is None:
        return None
    try:
        S = float(stability)
        t0 = parse_dt(last_review)
        if S <= 0 or t0 is None:
            return None
        elapsed_days = (at - t0).total_seconds() / 86400.0
        if elapsed_days < 0:
            elapsed_days = 0.0
        r = (1.0 + FACTOR * elapsed_days / S) ** DECAY
        return r
    except Exception:
        return None


def word_of(con, wid):
    cur = con.cursor()
    cur.execute("SELECT english, chinese FROM words WHERE id=?", (wid,))
    r = cur.fetchone()
    return r if r else (None, None)


def main():
    con = sqlite3.connect(PROD_DB)
    cur = con.cursor()

    out = {}

    # ── 词库总量 ──
    cur.execute("SELECT COUNT(*) FROM words")
    out["words_total"] = cur.fetchone()[0]

    # ── study_records ──
    cur.execute("SELECT COUNT(*) FROM study_records")
    out["study_records_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT word_id) FROM study_records")
    out["study_records_distinct_words"] = cur.fetchone()[0]
    cur.execute("SELECT MIN(studied_at), MAX(studied_at) FROM study_records")
    out["study_records_range"] = cur.fetchone()

    # ── learning_events ──
    cur.execute("SELECT COUNT(*) FROM learning_events")
    out["learning_events_total"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT word_id) FROM learning_events")
    out["learning_events_distinct_words"] = cur.fetchone()[0]
    cur.execute("SELECT activity_type, COUNT(*) FROM learning_events GROUP BY activity_type ORDER BY 2 DESC")
    out["learning_events_by_activity"] = cur.fetchall()
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM learning_events")
    out["learning_events_range"] = cur.fetchone()

    # 事实层复习事件（activity_type='review'）
    cur.execute("SELECT COUNT(*) FROM learning_events WHERE activity_type='review'")
    out["review_events_total"] = cur.fetchone()[0]
    cur.execute("SELECT result, COUNT(*) FROM learning_events WHERE activity_type='review' GROUP BY result")
    out["review_events_by_result"] = cur.fetchall()
    cur.execute("SELECT rating, COUNT(*) FROM learning_events WHERE activity_type='review' GROUP BY rating")
    out["review_events_by_rating"] = cur.fetchall()

    # ── 累计学习单词数 = study_records ∪ learning_events 去重 ──
    cur.execute("""
        SELECT COUNT(*) FROM (
            SELECT DISTINCT word_id FROM study_records
            UNION
            SELECT DISTINCT word_id FROM learning_events
        )
    """)
    out["learned_words_union"] = cur.fetchone()[0]

    # ── FSRS 准确率（复习事件，activity_type='review'）──
    cur.execute("SELECT result, COUNT(*) FROM learning_events WHERE activity_type='review' GROUP BY result")
    rev = dict(cur.fetchall())
    correct = rev.get("correct", 0)
    incorrect = rev.get("incorrect", 0)
    out["fsrs_correct"] = correct
    out["fsrs_incorrect"] = incorrect
    out["fsrs_accuracy"] = round(correct / (correct + incorrect), 4) if (correct + incorrect) else None

    # ── 记忆保持率（从 learning_events 的 fsrs_after 快照）──
    cur.execute("""
        SELECT word_id, timestamp, fsrs_after FROM learning_events
        WHERE activity_type='review' AND fsrs_after != ''
        ORDER BY timestamp
    """)
    ret_rows = []
    ret_values = []
    for wid, ts, fsrs_after in cur.fetchall():
        try:
            fa = json.loads(fsrs_after)
        except Exception:
            continue
        stability = fa.get("stability")
        last_review = fa.get("last_review") or ts
        r = retrievability(stability, last_review, STAT_TIME)
        en, cn = word_of(con, wid)
        ret_rows.append({
            "word_id": wid, "english": en, "stability": stability,
            "last_review": last_review, "retrievability": r,
            "state": fa.get("state"), "difficulty": fa.get("difficulty"),
        })
        if r is not None:
            ret_values.append(r)
    out["retention_rows"] = ret_rows
    out["retention_n"] = len(ret_values)
    out["retention_avg"] = round(sum(ret_values) / len(ret_values), 4) if ret_values else None

    # ── word_memory_state（生产库当前 FSRS 状态）──
    cur.execute("SELECT COUNT(*) FROM word_memory_state")
    out["prod_memory_state_count"] = cur.fetchone()[0]

    # ── mistake_records ──
    cur.execute("SELECT COUNT(*) FROM mistake_records")
    out["mistake_records_total"] = cur.fetchone()[0]
    cur.execute("SELECT source, COUNT(*) FROM mistake_records GROUP BY source")
    out["mistake_records_by_source"] = cur.fetchall()

    # ── daily_stats ──
    cur.execute("SELECT date, words_studied, words_mastered, correct_count, total_reviews, minutes_studied FROM daily_stats ORDER BY date")
    out["daily_stats"] = cur.fetchall()
    cur.execute("SELECT SUM(words_studied), SUM(total_reviews), SUM(correct_count) FROM daily_stats")
    out["daily_stats_totals"] = cur.fetchone()

    # ── AI 提示/提词 ──
    cur.execute("SELECT COUNT(*) FROM word_ai_explanations")
    out["ai_explanations_count"] = cur.fetchone()[0]
    cur.execute("SELECT word, created_at FROM word_ai_explanations ORDER BY created_at")
    out["ai_explanations_rows"] = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM ai_content_cache")
    out["ai_content_cache_count"] = cur.fetchone()[0]

    # ── 学生/教师预览 demo 数据 ──
    cur.execute("SELECT COUNT(*) FROM students")
    out["students_count"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM student_word_stats")
    out["student_word_stats_count"] = cur.fetchone()[0]

    # ── 教材/词书 ──
    cur.execute("SELECT id, book_name, word_count, is_builtin, is_active FROM books ORDER BY id")
    out["books"] = cur.fetchall()

    # ── 每个单词的答题次数（用于前后对比筛选）──
    cur.execute("""
        SELECT word_id, COUNT(*) AS cnt FROM (
            SELECT word_id FROM study_records
            UNION ALL
            SELECT word_id FROM learning_events
        ) GROUP BY word_id HAVING cnt >= 2 ORDER BY cnt DESC
    """)
    out["words_with_multi_events"] = cur.fetchall()

    con.close()

    # ── 参考：开发库 FSRS 记忆状态 ──
    dev = sqlite3.connect(DEV_DB)
    dcur = dev.cursor()
    dcur.execute("SELECT COUNT(*) FROM word_memory_state")
    out["dev_memory_state_count"] = dcur.fetchone()[0]
    dcur.execute("SELECT word_id, state, step, stability, difficulty, due, last_review, reps, lapses FROM word_memory_state ORDER BY word_id")
    dev_mem = []
    for row in dcur.fetchall():
        wid, state, step, stability, difficulty, due, lr, reps, lapses = row
        en, cn = word_of(dev, wid)
        r = retrievability(stability, lr, STAT_TIME)
        dev_mem.append({"word_id": wid, "english": en, "state": state, "stability": stability,
                        "difficulty": difficulty, "last_review": lr, "reps": reps, "lapses": lapses,
                        "retrievability": r})
    out["dev_memory_state_rows"] = dev_mem
    dev.close()

    # 输出 JSON
    out_path = Path(r"C:\Users\Administrator\Desktop\WordMaster备份\WordMaster最终版\相关材料\用户验证数据\_analysis_result.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # 打印摘要
    print("=" * 70)
    print("WordMaster 用户验证数据 —— 统计结果")
    print("=" * 70)
    print(f"词库总量(words): {out['words_total']}")
    print(f"study_records 总记录: {out['study_records_total']}, 去重单词: {out['study_records_distinct_words']}, 范围: {out['study_records_range']}")
    print(f"learning_events 总记录: {out['learning_events_total']}, 去重单词: {out['learning_events_distinct_words']}, 范围: {out['learning_events_range']}")
    print(f"learning_events 按类型: {out['learning_events_by_activity']}")
    print(f"复习事件(review)总数: {out['review_events_total']}, 按result: {out['review_events_by_result']}, 按rating: {out['review_events_by_rating']}")
    print(f"累计学习单词数(study∪event 去重): {out['learned_words_union']}")
    print(f"FSRS 准确率: 正确{out['fsrs_correct']} 错误{out['fsrs_incorrect']} = {out['fsrs_accuracy']}")
    print(f"记忆保持率: 样本{out['retention_n']}, 平均{out['retention_avg']}")
    print(f"生产库 word_memory_state: {out['prod_memory_state_count']}")
    print(f"mistake_records: {out['mistake_records_total']} 按source: {out['mistake_records_by_source']}")
    print(f"daily_stats totals(学习/复习/正确): {out['daily_stats_totals']}")
    print(f"AI解释缓存(word_ai_explanations): {out['ai_explanations_count']}")
    print(f"AI例句缓存(ai_content_cache): {out['ai_content_cache_count']}")
    print(f"students: {out['students_count']}, student_word_stats: {out['student_word_stats_count']}")
    print(f"books: {out['books']}")
    print(f"多事件单词(>=2次): {out['words_with_multi_events']}")
    print(f"开发库 word_memory_state: {out['dev_memory_state_count']}")
    print()
    print("记忆保持率明细(生产库 learning_events fsrs_after):")
    for r in out["retention_rows"]:
        print(f"  {r['english']:<12} stability={r['stability']} R={r['retrievability']}")
    print()
    print("开发库 word_memory_state 明细:")
    for r in out["dev_memory_state_rows"]:
        print(f"  {r['english']:<12} S={r['stability']} reps={r['reps']} lapses={r['lapses']} R={r['retrievability']}")


if __name__ == "__main__":
    main()
