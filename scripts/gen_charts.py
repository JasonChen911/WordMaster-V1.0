# -*- coding: utf-8 -*-
"""WordMaster 用户验证数据 —— 4 张高清图表（蓝白简洁风，16:9）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path

OUT = Path(r"C:\Users\Administrator\Desktop\WordMaster备份\WordMaster最终版\相关材料\用户验证数据")
OUT.mkdir(parents=True, exist_ok=True)

# ── 中文字体 ──
for fp in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc",
           r"C:\Windows\Fonts\simhei.ttf"]:
    try:
        font_manager.fontManager.addfont(fp)
    except Exception:
        pass
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

# ── 品牌色（deep indigo-violet + 中性灰）──
BRAND = "#4f46e5"
BRAND_LIGHT = "#a5b4fc"
BRAND_SOFT = "#e0e7ff"
INK = "#1f2937"
GRAY = "#6b7280"
LIGHT = "#9ca3af"
PANEL = "#f5f6fa"
POS = "#10b981"
WARN = "#f59e0b"
NEG = "#ef4444"

DPI = 200
W, H = 12.8, 7.2  # 16:9


def style_axes(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(colors=GRAY, labelsize=13)
    ax.set_facecolor("white")


def watermark(fig):
    fig.text(0.99, 0.02, "数据来源：WordMaster 真实 SQLite 数据库（个人内测）",
             ha="right", va="bottom", fontsize=10, color=LIGHT)


# ═════════════════════ 01 核心使用数据 ═════════════════
def chart01():
    fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="white")
    gs = fig.add_gridspec(2, 4, left=0.06, right=0.94, top=0.68, bottom=0.30,
                          wspace=0.12, hspace=0.30)
    items = [
        ("累计学习单词数", "51", "个", "词库 12,547 词中实际学习过 51 词", BRAND),
        ("累计答题次数", "90", "次", "12 次 FSRS 复习 + 5 次练习 + 72 次早期记录", BRAND),
        ("AI 提示词使用", "4", "次", "AI 词义讲解成功生成并缓存", BRAND),
        ("AI 诊断使用", "0", "次", "暂无有效诊断记录（功能不落库）", LIGHT),
    ]
    for i, (label, num, unit, sub, color) in enumerate(items):
        r, c = divmod(i, 4)
        ax = fig.add_subplot(gs[r, c])
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.text(0, 0.98, label, fontsize=17, color=GRAY, va="top")
        ax.text(0, 0.48, num, fontsize=72, color=color, va="center", fontweight="bold")
        ax.text(0.78, 0.44, unit, fontsize=20, color=color, va="bottom")
        ax.text(0, 0.02, sub, fontsize=12.5, color=LIGHT, va="bottom")
    fig.suptitle("WordMaster 核心使用数据", fontsize=30, color=INK,
                 fontweight="bold", x=0.06, ha="left", y=0.955)
    fig.text(0.06, 0.22, "统计口径：累计学习单词数 = 学习记录 + 学习事件去重后的单词数；累计答题次数 = daily_stats 累计复习统计。",
             fontsize=11.5, color=LIGHT)
    watermark(fig)
    fig.savefig(OUT / "01_核心使用数据.png", facecolor="white")
    plt.close(fig)
    print("saved 01")


# ═════════════════════ 02 FSRS学习效果 ═════════════════
def chart02():
    fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="white")
    fig.suptitle("FSRS 复习效果", fontsize=30, color=INK,
                 fontweight="bold", x=0.06, ha="left", y=0.955)

    # 两个百分比横向条
    ax = fig.add_axes([0.06, 0.42, 0.55, 0.34])
    labels = ["FSRS 复习准确率", "平均记忆保持率"]
    vals = [75.0, 86.9]
    colors = [BRAND, POS]
    y = [1, 0]
    ax.barh(y, vals, height=0.42, color=colors)
    for yy, v, lab, c in zip(y, vals, labels, colors):
        ax.text(v + 1.5, yy, f"{v:.1f}%", va="center", fontsize=34,
                color=c, fontweight="bold")
        ax.text(0.5, yy, lab, va="center", fontsize=18, color="white",
                fontweight="bold")
    ax.set_xlim(0, 105); ax.set_ylim(-0.8, 1.8)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=13, color=GRAY)
    ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(colors=GRAY)

    # 右侧样本量卡
    ax2 = fig.add_axes([0.66, 0.42, 0.28, 0.34])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis("off")
    ax2.add_patch(plt.Rectangle((0, 0), 1, 1, fc=PANEL, ec="none", zorder=0))
    ax2.text(0.5, 0.72, "有效复习样本量", fontsize=16, color=GRAY, ha="center")
    ax2.text(0.5, 0.36, "12", fontsize=64, color=BRAND, ha="center",
             fontweight="bold", va="center")
    ax2.text(0.5, 0.12, "次 FSRS 复习事件", fontsize=13, color=LIGHT, ha="center")

    fig.text(0.06, 0.28,
             "口径：准确率 = 复习事件中「正确」占比（正确 9 次 / 错误 3 次）。\n"
             "记忆保持率 = FSRS-5 可提取性 R(t)，按复习事件 fsrs_after 快照计算（统计时点 2026-09-27），样本 12。",
             fontsize=12, color=LIGHT)
    watermark(fig)
    fig.savefig(OUT / "02_FSRS学习效果.png", facecolor="white")
    plt.close(fig)
    print("saved 02")


# ═════════════════════ 03 前后正确率对比 ═════════════════
def chart03():
    # 7 个跨天单词；n≥4 用「前2次 vs 最近2次」，其余用「首次 vs 最近」
    words = [
        ("absurd\n荒谬的", 50, 100, "前2次 vs 最近2次"),
        ("aboard\n在船上", 0, 100, "首次 vs 最近"),
        ("absorb\n吸收", 100, 100, "首次 vs 最近"),
        ("abrupt\n突然的", 100, 100, "首次 vs 最近"),
        ("absence\n缺席", 100, 100, "首次 vs 最近"),
        ("absent\n缺席的", 100, 100, "首次 vs 100"),
        ("abstract\n抽象的", 100, 100, "首次 vs 最近"),
    ]
    names = [w[0] for w in words]
    before = [w[1] for w in words]
    after = [w[2] for w in words]

    fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="white")
    fig.suptitle("单词学习前后正确率对比", fontsize=30, color=INK,
                 fontweight="bold", x=0.06, ha="left", y=0.955)

    ax = fig.add_axes([0.10, 0.30, 0.62, 0.52])
    import numpy as np
    n = len(names)
    pos = np.arange(n)
    bw = 0.36
    ax.barh(pos + bw / 2, before, height=bw, color=BRAND_SOFT,
            edgecolor=BRAND, linewidth=1.2, label="学习前（初期）")
    ax.barh(pos - bw / 2, after, height=bw, color=BRAND,
            label="学习后（近期）")
    ax.set_yticks(pos)
    ax.set_yticklabels(names, fontsize=14)
    ax.set_xlim(0, 112)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=13, color=GRAY)
    ax.invert_yaxis()
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#e5e7eb")
    ax.spines["bottom"].set_color("#e5e7eb")
    ax.tick_params(colors=GRAY)
    for i in range(n):
        ax.text(before[i] + 2, pos[i] + bw / 2, f"{before[i]}%",
                va="center", fontsize=13, color=BRAND, fontweight="bold")
        ax.text(after[i] + 2, pos[i] - bw / 2, f"{after[i]}%",
                va="center", fontsize=13, color=BRAND, fontweight="bold")
    leg = ax.legend(loc="lower right", fontsize=13, frameon=False)
    for t in leg.get_texts():
        t.set_color(INK)

    # 右侧说明
    ax2 = fig.add_axes([0.76, 0.30, 0.20, 0.52])
    ax2.set_xlim(0, 1); ax2.set_ylim(0, 1); ax2.axis("off")
    ax2.text(0, 0.98, "样本与口径", fontsize=17, color=INK, fontweight="bold", va="top")
    note = ("个人内测数据中，具备跨天学习历史、"
            "可进行前后对比的单词仅 7 个；其余"
            "单词为单日批量测试记录，已排除。\n\n"
            "≥4 次用「前2次 vs 最近2次」，\n"
            "2～3 次用「首次 vs 最近」。\n\n"
            "「absurd / aboard」前期出错、后期"
            "答对，其余单词前后均正确。")
    ax2.text(0, 0.80, note, fontsize=12.5, color=GRAY, va="top", linespacing=1.7)

    fig.text(0.06, 0.20,
             "说明：样本量过小（仅 7 个跨天单词），本图仅作功能链路验证示意，不构成统计学结论。",
             fontsize=12, color=NEG)
    watermark(fig)
    fig.savefig(OUT / "03_单词学习前后正确率对比.png", facecolor="white")
    plt.close(fig)
    print("saved 03")


# ═════════════════════ 04 典型单词轨迹 ═════════════════
def chart04():
    fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="white")
    fig.suptitle("典型案例：absurd（荒谬的）—— 从「遗忘」到「重新掌握」",
                 fontsize=30, color=INK, fontweight="bold", x=0.06, ha="left", y=0.955)

    steps = [
        (0, "08-07 18:37", "首次学习", "too_easy（已掌握）", "✓ 正确", POS, "旧系统 stage→1"),
        (1, "09-26 18:05", "FSRS 复习", "unknown（完全遗忘）", "✗ 错误", NEG, "记入错词本 · stability 0.21"),
        (2, "09-26 20:08", "选择题练习", "meaning_choice 答 A", "✓ 正确", POS, "系统推送练习"),
        (3, "09-26 20:08", "选择题练习", "meaning_choice 答 B", "✓ 正确", POS, "再次巩固"),
    ]
    ax = fig.add_axes([0.06, 0.28, 0.88, 0.50])
    ax.set_xlim(-0.5, len(steps) - 0.5); ax.set_ylim(-1, 1.6)
    ax.axis("off")
    # 主线
    ax.plot([0, len(steps) - 1], [0, 0], color=BRAND_SOFT, lw=5, zorder=0)
    for i, (x, dt, ev, res, ok, color, note) in enumerate(steps):
        # 节点
        ax.scatter([x], [0], s=1800, color=color, zorder=3, alpha=0.15)
        ax.scatter([x], [0], s=650, color=color, zorder=4)
        ax.text(x, 0, "✓" if ok == "✓ 正确" else "✗", ha="center", va="center",
                fontsize=26, color="white", zorder=5, fontweight="bold")
        # 上标签（日期+事件）
        ax.text(x, 0.72, dt, ha="center", fontsize=16, color=INK, fontweight="bold")
        ax.text(x, 0.42, ev, ha="center", fontsize=20, color=INK, fontweight="bold")
        # 下标签（结果）
        ax.text(x, -0.42, res, ha="center", fontsize=13.5, color=GRAY)
        ax.text(x, -0.72, ok, ha="center", fontsize=17, color=color, fontweight="bold")
        ax.text(x, -1.02, note, ha="center", fontsize=11.5, color=LIGHT)

    # 箭头标注「遗忘→改善」
    ax.annotate("", xy=(2.0, 0.05), xytext=(1.0, 0.05),
                arrowprops=dict(arrowstyle="->", color=BRAND, lw=2))
    fig.text(0.06, 0.18,
             "闭环：首次学习 → 50 天后 FSRS 复习暴露遗忘 → 记录错词本 → 系统推送练习 → 重新答对。\n"
             "注：AI 诊断环节不向数据库写记录，故本轨迹中无直接的 AI 诊断时间戳（见报告说明）。",
             fontsize=12, color=LIGHT)
    watermark(fig)
    fig.savefig(OUT / "04_典型单词学习轨迹.png", facecolor="white")
    plt.close(fig)
    print("saved 04")


if __name__ == "__main__":
    chart01()
    chart02()
    chart03()
    chart04()
    print("ALL CHARTS DONE")
