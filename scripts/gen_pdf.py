# -*- coding: utf-8 -*-
"""生成 WordMaster 用户验证数据报告 PDF（reportlab + 中文字体）。"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = Path(r"C:\Users\Administrator\Desktop\WordMaster备份\WordMaster最终版\相关材料\用户验证数据")

# ── 中文字体 ──
_FONT = None
for name, path in [("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
                   ("MSYH", r"C:\Windows\Fonts\msyh.ttc")]:
    try:
        pdfmetrics.registerFont(TTFont(name, path))
        _FONT = name
        break
    except Exception:
        continue
assert _FONT, "no Chinese font found"

BRAND = colors.HexColor("#4f46e5")
INK = colors.HexColor("#1f2937")
GRAY = colors.HexColor("#6b7280")
LGRAY = colors.HexColor("#9ca3af")
RED = colors.HexColor("#ef4444")
LINE = colors.HexColor("#e5e7eb")

styles = {
    "title": ParagraphStyle("title", fontName=_FONT, fontSize=24, leading=32,
                            textColor=BRAND, alignment=TA_CENTER, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName=_FONT, fontSize=13, leading=20,
                               textColor=GRAY, alignment=TA_CENTER, spaceAfter=4),
    "h1": ParagraphStyle("h1", fontName=_FONT, fontSize=15, leading=22,
                         textColor=INK, spaceBefore=14, spaceAfter=6),
    "body": ParagraphStyle("body", fontName=_FONT, fontSize=10.5, leading=17,
                           textColor=INK, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName=_FONT, fontSize=10.5, leading=16,
                             textColor=INK, leftIndent=14, bulletIndent=4, spaceAfter=3),
    "small": ParagraphStyle("small", fontName=_FONT, fontSize=9, leading=13,
                            textColor=GRAY, spaceAfter=3),
    "note": ParagraphStyle("note", fontName=_FONT, fontSize=9.5, leading=14,
                           textColor=RED, spaceAfter=4),
}

story = []


def H(text):
    story.append(Paragraph(text, styles["h1"]))


def P(text):
    story.append(Paragraph(text, styles["body"]))


def B(text):
    story.append(Paragraph(text, styles["bullet"], bulletText="•"))


def S(text):
    story.append(Paragraph(text, styles["small"]))


def TABLE(headers, rows):
    data = [[Paragraph(f"<b>{h}</b>", ParagraphStyle("th", fontName=_FONT, fontSize=9.5, textColor=colors.white)) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), ParagraphStyle("td", fontName=_FONT, fontSize=9.5, textColor=INK)) for c in row])
    t = Table(data, colWidths=None, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)


# ── 封面 ──
for _ in range(8):
    story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("WordMaster 用户验证数据报告", styles["title"]))
story.append(Paragraph("使用数据 · FSRS 效果 · 典型案例", styles["subtitle"]))
story.append(Spacer(1, 1.2 * cm))
story.append(Paragraph("数据性质：产品内测阶段真实使用记录（单一开发者自测）", styles["subtitle"]))
story.append(Paragraph("统计时间：2026-09-27", styles["subtitle"]))
story.append(PageBreak())

# ── 正文 ──
H("1. 验证目的")
P("本报告用于验证 WordMaster 的核心学习链路是否能在真实使用中正常运转：学习行为能否被准确记录；FSRS 间隔重复算法能否对真实答题动态调度；「学习 → 出错 → 记录 → 辅助 → 重学 → 改善」闭环能否完整跑通。所有数字均来自真实 SQLite 数据库或程序日志，未做编造、估算或补齐。")

H("2. 数据来源与真实性说明")
P("主数据库：C:\\Users\\Administrator\\AppData\\Roaming\\WordMaster\\wordmaster.db（SQLite，12,547 词库），为打包版运行时的真实落库。核心学习行为记录于 learning_events（事实层）、study_records（早期记录）、daily_stats（每日汇总）。")
B("累计答题：study_records（72）+ learning_events（17）= 89，与 daily_stats 累计 90 次基本吻合；")
B("FSRS 复习快照：learning_events.fsrs_after 固化每次复习的 stability / difficulty / due，可反查；")
B("典型案例 absurd 的每条事件均有原始记录可验证（附录 C）。")

H("3. 测试环境与样本说明")
P("测试环境：Windows 11，WordMaster 桌面版（打包 EXE + 本地 SQLite）。")
P("样本性质：当前数据属于产品内测阶段的真实使用记录，由开发者本人自测产生，主要用于验证功能链路与学习闭环是否正常运行，不代表大规模用户实验结果。")
TABLE(["项目", "值"],
      [["使用者", "单一开发者（内测）"], ["词库规模", "12,547 词 / 5 本书"],
       ["实际学习单词", "51 个（去重）"], ["结构化学习事件", "17 条（12 复习 + 5 练习）"],
       ["数据覆盖", "2026-08-06 ~ 2026-09-26"]])
story.append(Spacer(1, 0.3 * cm))

H("4. WordMaster 实际使用概况")
P("内测期间激活 5 本内置词书，真实学习集中在少量单词上：去重后实际学习过 51 个词，累计答题 90 次。每日统计：")
TABLE(["日期", "学习单词数", "正确次数", "复习次数"],
      [["2026-08-07", "35", "34", "35"], ["2026-08-08", "38", "38", "38"],
       ["2026-09-20", "4", "4", "4"], ["2026-09-23", "10", "8", "10"],
       ["2026-09-24", "2", "1", "2"], ["2026-09-26", "1", "0", "1"]])
S("其中 08-07 / 08-08 为旧系统（Ebbinghaus 阶段制）下的批量自测，09-20 之后为 FSRS 系统下的分散复习。")
story.append(Spacer(1, 0.3 * cm))

H("5. 核心使用数据")
TABLE(["指标", "数值", "统计口径"],
      [["累计学习单词数", "51 个", "学习记录+事件去重（非词库导入量）"],
       ["累计答题次数", "90 次", "daily_stats 累计（其中结构化 17 次）"],
       ["AI 提示词使用次数", "4 次", "AI 词义讲解成功生成并缓存"],
       ["AI 诊断使用次数", "0 次", "暂无有效诊断记录（功能不落库）"]])
story.append(Spacer(1, 0.2 * cm))
story.append(Image(str(OUT / "01_核心使用数据.png"), width=16.5 * cm, height=9.28 * cm))

H("6. FSRS 复习效果分析")
P("FSRS 复习准确率 = 75.0%（12 次复习中正确 9 次、错误 3 次；again/hard 计错误，good/easy 计正确）。")
P("平均记忆保持率 = 86.9%（样本 n=12），按 FSRS-5 可提取性公式 R(t)=(1+(19/81)·t/S)^(−0.5) 计算（统计时点 2026-09-27），样本区间 44.7% ~ 95.2%。8 个「too_easy」单词（stability≈8.3 天）保持率约 95%，2 个「unknown」遗忘单词（stability≈0.21 天）约 45% ~ 71%，与模型预测方向一致。")
story.append(Image(str(OUT / "02_FSRS学习效果.png"), width=16.5 * cm, height=9.28 * cm))

H("7. AI 功能实际使用情况")
P("AI 提示词（词义讲解）：13 次请求中 4 次成功落库缓存（preferable / eyewitness / impatient / lamp，2026-08-08）；早期 2 次因未配置 API Key 失败不计入。AI 例句缓存（ai_content_cache）为 0。")
P("AI 学习诊断：当前 0 次。诊断接口（/api/ai/word-analysis 等）采用即时返回、不写库设计，数据库与日志均无诊断调用记录，故该指标「暂无有效数据」。")

H("8. 单词学习前后正确率变化")
P("筛选「具备跨天学习历史、≥2 次答题」的单词：≥4 次用「前2次 vs 最近2次」，2～3 次用「首次 vs 最近」。仅 7 个单词满足条件，其中 absurd（50%→100%）、aboard（0%→100%）改善，其余 5 词前后均正确。其余 12 个多事件单词为单日批量测试，已排除。")
story.append(Image(str(OUT / "03_单词学习前后正确率对比.png"), width=16.5 * cm, height=9.28 * cm))
story.append(Paragraph("样本量过小（仅 7 个跨天单词），本图仅作功能链路验证示意，不构成统计学结论。", styles["note"]))

H("9. 典型案例：一个单词从「反复错」到「逐渐掌握」")
P("遍历真实记录，自动筛选出具备「学习 → 遗忘 → 记录 → 辅助 → 重学」完整轨迹的代表性单词：absurd（荒谬的）。时间线：")
TABLE(["日期/时间", "事件类型", "答案/评分", "正确与否", "FSRS 状态 / 系统动作"],
      [["2026-08-07 18:37", "首次学习", "too_easy", "正确", "旧系统 stage=1"],
       ["2026-09-26 18:05", "FSRS 复习", "unknown / again", "错误", "stability 0.21 · difficulty 6.41 · lapses 1 → 记入错词本"],
       ["2026-09-26 20:08", "选择题练习", "A", "正确", "系统推送练习"],
       ["2026-09-26 20:08", "选择题练习", "B", "正确", "再次巩固"]])
story.append(Spacer(1, 0.2 * cm))
story.append(Image(str(OUT / "04_典型单词学习轨迹.png"), width=16.5 * cm, height=9.28 * cm))
P("这个单词为什么能体现 WordMaster 的数据闭环：")
B("发现问题：首次学习 50 天后 FSRS 复习答「unknown（完全遗忘）」，判定为错误；")
B("记录错误：错误写入 learning_events 与 mistake_records（错词本）；")
B("数据沉淀：FSRS 将 stability 降至 0.21 天、difficulty 升至 6.41、lapses=1；")
B("系统辅助：错词本与练习系统针对该词推送选择题；")
B("再次学习：连续两次答对（A、B），重新掌握。")
P("如实说明：AI 诊断环节在本单词轨迹中无直接数据库时间戳（诊断接口不落库），本案例「辅助」环节体现为错词本与练习推送。")

H("10. WordMaster 学习闭环验证")
B("发现与记录：17 条结构化事件完整记录正确/错误结果；")
B("动态调度：FSRS 对不同答题给出不同 stability / difficulty / due；")
B("辅助与改善：错词本与练习推动薄弱词重新答对（absurd、aboard 前后正确率提升）。")

H("11. 当前数据局限性")
B("样本为单一开发者内测数据，结构化事件仅 17 条，不具备统计学意义；")
B("word_memory_state 在部分会话被重置，记忆保持率改由事件快照计算；")
B("AI 诊断不落库，导致「AI 诊断使用次数」无法可靠统计；")
B("具备跨天前后对比的单词仅 7 个。")

H("12. 结论")
P("在内测数据范围内，WordMaster 核心学习链路运行正常：学习行为可记录、FSRS 可动态调度（复习准确率 75%、记忆保持率 86.9%）、错词本与练习可推动薄弱词重新掌握。当前数据用于验证功能链路，后续需在更大规模真实用户数据上进一步验证。")

# 附录
story.append(PageBreak())
H("附录 A：统计口径")
B("累计学习单词数 = study_records 与 learning_events 中 word_id 去重并集；")
B("累计答题次数 = daily_stats.total_reviews 累计（结构化事实层 17 次单独列出）；")
B("FSRS 复习准确率 = 复习事件中「correct」占比；")
B("平均记忆保持率 = 对每个已复习单词按 FSRS-5 可提取性公式计算后取平均；")
B("AI 提示词 = word_ai_explanations 成功缓存条数；AI 诊断 = 无落库记录，计 0；")
B("前后正确率：≥4 次「前2次 vs 最近2次」，2～3 次「首次 vs 最近」。")

H("附录 B：SQL / 数据来源")
S("SELECT COUNT(*) FROM words;  -- 12,547")
S("SELECT COUNT(*) FROM (SELECT DISTINCT word_id FROM study_records UNION SELECT DISTINCT word_id FROM learning_events);  -- 51")
S("SELECT activity_type, COUNT(*) FROM learning_events GROUP BY activity_type;  -- review 12, meaning_choice 5")
S("SELECT result, COUNT(*) FROM learning_events WHERE activity_type='review' GROUP BY result;  -- correct 9, incorrect 3")
S("SELECT COUNT(*) FROM word_ai_explanations;  -- 4")

H("附录 C：典型案例原始事件摘要")
S("单词 absurd（word_id=2045）原始记录（按时间排序）：")
S("1) study_records: result='too_easy', studied_at='2026-08-07 18:37:20', review_stage=1")
S("2) learning_events: activity_type='review', result='incorrect', rating='again', user_answer='unknown', fsrs_after={'state':1,'stability':0.212,'difficulty':6.4133,'lapses':1}, timestamp='2026-09-26 18:05:48'")
S("3) mistake_records: source='daily', mistake_type='meaning', first_occurred_at='2026-09-26 18:05:48'")
S("4) learning_events: activity_type='meaning_choice', result='correct', user_answer='A', timestamp='2026-09-26 20:08:14'")
S("5) learning_events: activity_type='meaning_choice', result='correct', user_answer='B', timestamp='2026-09-26 20:08:26'")

pdf_path = OUT / "WordMaster用户验证数据报告.pdf"
doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                        leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=2 * cm, bottomMargin=2 * cm,
                        title="WordMaster 用户验证数据报告")
doc.build(story)
print("saved PDF:", pdf_path.name)
