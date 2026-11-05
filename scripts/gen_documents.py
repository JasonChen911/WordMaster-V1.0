# -*- coding: utf-8 -*-
"""生成：典型单词 CSV + 用户验证数据报告 DOCX + PDF。"""
import csv
import json
from pathlib import Path

OUT = Path(r"C:\Users\Administrator\Desktop\WordMaster备份\WordMaster最终版\相关材料\用户验证数据")
OUT.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════════════════════════════════════
# 1) 典型单词完整学习轨迹 CSV
# ════════════════════════════════════════════════════════════════
CSV_ROWS = [
    ["日期/时间", "单词", "事件类型", "用户答案/评分", "正确与否", "FSRS状态state",
     "stability", "difficulty", "lapses", "due", "是否使用AI提示", "是否进行AI诊断",
     "系统采取的下一步", "后续学习结果"],
    ["2026-08-07 18:37:20", "absurd", "首次学习(study_record, 旧系统)", "too_easy", "正确",
     "", "", "", "", "", "否", "否", "进入旧系统复习阶段 stage=1", "50天后FSRS复习时暴露遗忘"],
    ["2026-09-26 18:05:48", "absurd", "FSRS复习(learning_event, review)", "unknown / again", "错误",
     "1(Learning)", "0.212", "6.4133", "1", "2026-09-26 18:06:48", "否", "否",
     "记入错词本(mistake_records: daily/meaning)", "系统推送选择题练习"],
    ["2026-09-26 20:08:14", "absurd", "选择题练习(meaning_choice)", "A", "正确",
     "", "", "", "", "", "否", "否", "再次推送同词练习", "再次答对"],
    ["2026-09-26 20:08:26", "absurd", "选择题练习(meaning_choice)", "B", "正确",
     "", "", "", "", "", "否", "否", "巩固完成", "连续两次答对，重新掌握"],
]

csv_path = OUT / "典型单词完整学习轨迹.csv"
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    csv.writer(f).writerows(CSV_ROWS)
print("saved CSV:", csv_path.name)


# ════════════════════════════════════════════════════════════════
# 2) DOCX
# ════════════════════════════════════════════════════════════════
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BRAND = RGBColor(0x4F, 0x46, 0xE5)
INK = RGBColor(0x1F, 0x29, 0x37)
GRAY = RGBColor(0x6B, 0x72, 0x80)


def set_cn(run, name="微软雅黑"):
    run.font.name = name
    r = run._element.rPr
    rf = r.find(qn("w:rFonts"))
    if rf is None:
        rf = r.makeelement(qn("w:rFonts"), {})
        r.append(rf)
    rf.set(qn("w:eastAsia"), name)


def add_h(doc, text, level=1):
    p = doc.add_paragraph()
    p.space_before = Pt(0)
    r = p.add_run(text)
    r.font.bold = True
    r.font.color.rgb = INK if level == 1 else BRAND
    r.font.size = Pt(16 if level == 1 else 13)
    set_cn(r)
    return p


def add_p(doc, text, size=10.5, bold=False, color=INK, indent=0):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.4
    if indent:
        p.paragraph_format.left_indent = Cm(0.5)
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    set_cn(r)
    return p


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.font.size = Pt(10.5)
    set_cn(r)
    return p


def style_cell(cell, text, bold=False, size=9.5, color=INK, fill=None):
    cell.text = ""
    p = cell.paragraphs[0]
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    set_cn(r)
    if fill:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = tcPr.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:fill"): fill})
        tcPr.append(shd)


def make_table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        style_cell(hdr[i], h, bold=True, size=9.5, color=RGBColor(0xFF, 0xFF, 0xFF), fill="4F46E5")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            style_cell(cells[i], str(v), size=9.5)
    return t


doc = Document()
# 默认字体
normal = doc.styles["Normal"]
normal.font.name = "微软雅黑"
normal.font.size = Pt(10.5)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")

# ── 封面 ──
for _ in range(6):
    doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("WordMaster 用户验证数据报告"); r.font.size = Pt(28); r.font.bold = True; r.font.color.rgb = BRAND; set_cn(r)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("使用数据 · FSRS 效果 · 典型案例"); r.font.size = Pt(14); r.font.color.rgb = GRAY; set_cn(r)
doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("数据性质：产品内测阶段真实使用记录（单一开发者自测）"); r.font.size = Pt(11); r.font.color.rgb = GRAY; set_cn(r)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("统计时间：2026-09-27"); r.font.size = Pt(11); r.font.color.rgb = GRAY; set_cn(r)
doc.add_page_break()

# ── 1 验证目的 ──
add_h(doc, "1. 验证目的", 1)
add_p(doc, "本报告用于验证 WordMaster 的核心学习链路是否能够在真实使用中正常运转，具体验证以下三点：")
add_bullet(doc, "学习行为能否被准确记录（学习事件、答题结果、错误记录）；")
add_bullet(doc, "FSRS 间隔重复算法能否对真实答题作出动态调度，并产出可解释的记忆状态；")
add_bullet(doc, "「学习 → 出错 → 记录 → 辅助 → 重学 → 改善」的学习闭环能否完整跑通。")
add_p(doc, "需要强调的是：本报告所有数字均来自 WordMaster 真实 SQLite 数据库或程序日志，未做任何编造、估算或补齐。数据量较小的指标已如实标注。")

# ── 2 数据来源与真实性 ──
add_h(doc, "2. 数据来源与真实性说明", 1)
add_p(doc, "主数据库：C:\\Users\\Administrator\\AppData\\Roaming\\WordMaster\\wordmaster.db（SQLite，12,547 词库）。")
add_p(doc, "该数据库为 WordMaster 打包版运行时的真实落库，项目文档 DATA_REPAIR_REPORT.md 将其标注为「生产」库。核心学习行为记录于 learning_events（事实层）、study_records（早期记录）、daily_stats（每日汇总）三张表。")
add_p(doc, "完整性校验要点：")
add_bullet(doc, "累计答题次数：study_records（72 条）+ learning_events（17 条）= 89，与 daily_stats 累计 90 次基本吻合；")
add_bullet(doc, "FSRS 复习快照：learning_events.fsrs_after 字段固化每次复习的 stability / difficulty / due，可反查；")
add_bullet(doc, "典型案例 absurd 的每条事件均有原始记录可验证（见附录 C）。")

# ── 3 测试环境与样本 ──
add_h(doc, "3. 测试环境与样本说明", 1)
add_p(doc, "测试环境：Windows 11，WordMaster 桌面版（打包 EXE + 本地 SQLite）。")
add_p(doc, "样本性质：当前数据属于产品内测阶段的真实使用记录，由开发者本人自测产生，主要用于验证功能链路与学习闭环是否能够正常运行，不代表大规模用户实验结果。")
make_table(doc,
    ["项目", "值"],
    [
        ["使用者", "单一开发者（内测）"],
        ["词库规模", "12,547 词 / 5 本书"],
        ["实际学习单词", "51 个（去重）"],
        ["结构化学习事件", "17 条（12 复习 + 5 练习）"],
        ["数据覆盖", "2026-08-06 ~ 2026-09-26"],
    ])
doc.add_paragraph()

# ── 4 使用概况 ──
add_h(doc, "4. WordMaster 实际使用概况", 1)
add_p(doc, "内测期间共激活 5 本内置词书（高中 / 四级 / 六级 / 考研 / 托福）。真实学习集中在少量单词上：去重后实际学习过 51 个词，累计答题 90 次。按每日统计：")
make_table(doc,
    ["日期", "学习单词数", "正确次数", "复习次数"],
    [
        ["2026-08-07", "35", "34", "35"],
        ["2026-08-08", "38", "38", "38"],
        ["2026-09-20", "4", "4", "4"],
        ["2026-09-23", "10", "8", "10"],
        ["2026-09-24", "2", "1", "2"],
        ["2026-09-26", "1", "0", "1"],
    ])
add_p(doc, "其中 2026-08-07 / 08-08 两天为旧系统（Ebbinghaus 阶段制）下的批量自测，09-20 之后为 FSRS 系统下的分散复习。", size=9.5, color=GRAY)

# ── 5 核心使用数据 ──
add_h(doc, "5. 核心使用数据", 1)
make_table(doc,
    ["指标", "数值", "统计口径"],
    [
        ["累计学习单词数", "51 个", "学习记录 + 学习事件去重后的单词数（非词库导入量）"],
        ["累计答题次数", "90 次", "daily_stats 累计复习（其中结构化 FSRS 复习 12 次、练习 5 次）"],
        ["AI 提示词使用次数", "4 次", "AI 词义讲解成功生成并落库缓存"],
        ["AI 诊断使用次数", "0 次", "暂无有效诊断记录（功能不落库）"],
    ])
doc.add_paragraph()
try:
    doc.add_picture(str(OUT / "01_核心使用数据.png"), width=Inches(6.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
except Exception as e:
    add_p(doc, f"[图表 01 嵌入失败：{e}]", color=GRAY)

# ── 6 FSRS 效果 ──
add_h(doc, "6. FSRS 复习效果分析", 1)
add_p(doc, "FSRS 复习准确率 = 75.0%（12 次复习中正确 9 次、错误 3 次）。正确/错误映射遵循 FSRS 评分：again / hard 计为错误，good / easy 计为正确。")
add_p(doc, "平均记忆保持率 = 86.9%（样本 n=12），按 FSRS-5 可提取性公式 R(t)=(1+(19/81)·t/S)^(−0.5) 计算，统计时点 2026-09-27。12 个样本的保持率区间为 44.7% ~ 95.2%。")
add_p(doc, "分层观察：8 个答「too_easy」的单词（已进入复习态，stability≈8.3 天）保持率约 95%；2 个答「unknown」的遗忘单词（stability≈0.21 天）保持率仅 45% ~ 71%，与 FSRS 模型预测方向一致。")
doc.add_picture(str(OUT / "02_FSRS学习效果.png"), width=Inches(6.0))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

# ── 7 AI 功能 ──
add_h(doc, "7. AI 功能实际使用情况", 1)
add_p(doc, "AI 提示词（词义讲解）：内测期间共 13 次调用请求，其中 4 次成功生成并写入缓存（preferable、eyewitness、impatient、lamp，均为 2026-08-08）；早期 2 次因未配置 API Key 失败，不计入使用次数。AI 例句缓存（ai_content_cache）为 0。")
add_p(doc, "AI 学习诊断：当前为 0 次。原因是诊断类接口（/api/ai/word-analysis、/api/ai/analyze-errors、/api/ai/insights）采用即时返回、不写库的设计，数据库与日志中均无诊断调用记录，故该指标「暂无有效数据」。")

# ── 8 前后正确率 ──
add_h(doc, "8. 单词学习前后正确率变化", 1)
add_p(doc, "筛选「具备跨天学习历史、≥2 次答题」的单词进行前后对比：≥4 次用「前 2 次 vs 最近 2 次」，2～3 次用「首次 vs 最近」。")
add_p(doc, "结果仅 7 个单词满足条件：absurd 由 50% 提升到 100%，aboard 由 0% 提升到 100%，其余 5 个单词（absorb、abrupt、absence、absent、abstract）前后均正确、无变化。其余 12 个多事件单词为单日批量测试记录，已排除。", bold=False)
doc.add_picture(str(OUT / "03_单词学习前后正确率对比.png"), width=Inches(6.0))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_p(doc, "样本量过小（仅 7 个跨天单词），本图仅作功能链路验证示意，不构成统计学结论。", size=9.5, color=RGBColor(0xEF, 0x44, 0x44))

# ── 9 典型案例 ──
add_h(doc, "9. 典型案例：一个单词从「反复错」到「逐渐掌握」", 1)
add_p(doc, "通过遍历真实学习记录，自动筛选出具备「学习 → 遗忘 → 记录 → 辅助 → 重学」完整轨迹的代表性单词：absurd（荒谬的）。完整时间线如下：")
make_table(doc,
    ["日期/时间", "事件类型", "答案/评分", "正确与否", "FSRS 状态 / 系统动作"],
    [
        ["2026-08-07 18:37", "首次学习", "too_easy", "正确", "旧系统 stage=1"],
        ["2026-09-26 18:05", "FSRS 复习", "unknown / again", "错误", "stability 0.21 · difficulty 6.41 · lapses 1 → 记入错词本"],
        ["2026-09-26 20:08", "选择题练习", "A", "正确", "系统推送练习"],
        ["2026-09-26 20:08", "选择题练习", "B", "正确", "再次巩固"],
    ])
doc.add_picture(str(OUT / "04_典型单词学习轨迹.png"), width=Inches(6.0))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
add_p(doc, "这个单词为什么能体现 WordMaster 的数据闭环：", bold=True)
add_bullet(doc, "发现问题：首次学习 50 天后，FSRS 复习时用户答「unknown（完全遗忘）」，系统判定为错误；")
add_bullet(doc, "记录错误：该次错误被自动写入 learning_events（错误事件）与 mistake_records（错词本，source=daily）；")
add_bullet(doc, "学习行为沉淀：FSRS 将 stability 降至 0.21 天、difficulty 升至 6.41、lapses 计为 1，标记该词为薄弱词；")
add_bullet(doc, "系统辅助：错词本与练习系统针对该词推送选择题练习；")
add_bullet(doc, "再次学习：用户连续两次答对（答案 A、B），重新掌握该词。")
add_p(doc, "需要如实说明：AI 诊断环节在本单词轨迹中无直接数据库时间戳（诊断接口不落库），因此本案例的「辅助」环节体现为错词本与练习推送，而非 AI 诊断。")

# ── 10 闭环验证 ──
add_h(doc, "10. WordMaster 学习闭环验证", 1)
add_p(doc, "综合以上数据，WordMaster 的「发现 → 记录 → 沉淀 → 调度 → 辅助 → 重学 → 改善」闭环在内测数据中得到验证：")
add_bullet(doc, "发现与记录：17 条结构化事件完整记录了复习与练习的正确/错误结果；")
add_bullet(doc, "动态调度：FSRS 对不同答题给出不同 stability / difficulty / due（如 absurd 遗忘后 stability 降到 0.21、due 缩至 1 分钟）；")
add_bullet(doc, "辅助与改善：错词本与练习系统推动薄弱词重新答对（absurd、aboard 前后正确率提升）。")

# ── 11 局限性 ──
add_h(doc, "11. 当前数据局限性", 1)
add_bullet(doc, "样本为单一开发者内测数据，量级小（结构化事件仅 17 条），不具备统计学意义，不可外推为大规模用户结论；")
add_bullet(doc, "FSRS 记忆状态表（word_memory_state）在部分会话中被重置，记忆保持率改由事件快照计算；")
add_bullet(doc, "AI 诊断功能不落库，导致「AI 诊断使用次数」无法从数据库可靠统计；")
add_bullet(doc, "具备跨天前后对比的单词仅 7 个，前后正确率对比图样本不足。")

# ── 12 结论 ──
add_h(doc, "12. 结论", 1)
add_p(doc, "在内测数据范围内，WordMaster 的核心学习链路运行正常：学习行为可记录、FSRS 可动态调度（复习准确率 75%、平均记忆保持率 86.9%）、错词本与练习系统可推动薄弱词重新掌握。当前数据属于产品内测阶段的真实使用记录，主要用于验证功能链路，后续需在更大规模真实用户数据上进一步验证。")

# ── 附录 A ──
doc.add_page_break()
add_h(doc, "附录 A：统计口径", 1)
add_p(doc, "1. 累计学习单词数 = study_records 与 learning_events 中 word_id 去重并集；")
add_p(doc, "2. 累计答题次数 = daily_stats.total_reviews 累计（结构化事实层 17 次单独列出）；")
add_p(doc, "3. FSRS 复习准确率 = 复习事件中「correct」占比；")
add_p(doc, "4. 平均记忆保持率 = 对每个已复习单词按 FSRS-5 可提取性公式计算后取平均；")
add_p(doc, "5. AI 提示词 = word_ai_explanations 成功缓存条数；")
add_p(doc, "6. AI 诊断 = 无落库记录，计 0；")
add_p(doc, "7. 前后正确率：≥4 次「前2次 vs 最近2次」，2～3 次「首次 vs 最近」。")

# ── 附录 B ──
add_h(doc, "附录 B：SQL / 数据来源", 1)
add_p(doc, "主要 SQL（完整口径见《数据来源与统计口径.md》）：", size=9.5, color=GRAY)
add_p(doc, "SELECT COUNT(*) FROM words;  -- 12,547", size=9.5)
add_p(doc, "SELECT COUNT(*) FROM (SELECT DISTINCT word_id FROM study_records UNION SELECT DISTINCT word_id FROM learning_events);  -- 51", size=9.5)
add_p(doc, "SELECT activity_type, COUNT(*) FROM learning_events GROUP BY activity_type;  -- review 12, meaning_choice 5", size=9.5)
add_p(doc, "SELECT result, COUNT(*) FROM learning_events WHERE activity_type='review' GROUP BY result;  -- correct 9, incorrect 3", size=9.5)
add_p(doc, "SELECT COUNT(*) FROM word_ai_explanations;  -- 4", size=9.5)

# ── 附录 C ──
add_h(doc, "附录 C：典型案例原始事件摘要", 1)
add_p(doc, "单词 absurd（word_id=2045）原始记录（已按时间排序）：", size=9.5, color=GRAY)
for line in [
    "1) study_records: result='too_easy', studied_at='2026-08-07 18:37:20', review_stage=1",
    "2) learning_events: activity_type='review', result='incorrect', rating='again', user_answer='unknown', fsrs_after={'state':1,'stability':0.212,'difficulty':6.4133,'lapses':1}, timestamp='2026-09-26 18:05:48'",
    "3) mistake_records: source='daily', mistake_type='meaning', first_occurred_at='2026-09-26 18:05:48'",
    "4) learning_events: activity_type='meaning_choice', result='correct', user_answer='A', timestamp='2026-09-26 20:08:14'",
    "5) learning_events: activity_type='meaning_choice', result='correct', user_answer='B', timestamp='2026-09-26 20:08:26'",
]:
    add_p(doc, line, size=9.0)

docx_path = OUT / "WordMaster用户验证数据报告.docx"
doc.save(str(docx_path))
print("saved DOCX:", docx_path.name)
