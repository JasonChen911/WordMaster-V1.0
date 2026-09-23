"""Generate WordMaster Architecture Report (.docx)"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from datetime import datetime

doc = Document()

# ── Styles ──
style = doc.styles['Normal']
style.font.name = 'Microsoft YaHei'
style.font.size = Pt(10.5)
style.paragraph_format.space_after = Pt(6)

for level in range(1, 4):
    hs = doc.styles[f'Heading {level}']
    hs.font.name = 'Microsoft YaHei'
    hs.font.color.rgb = RGBColor(0x63, 0x66, 0xF1)

# ═══════════════════════════════════════════════════
# COVER
# ═══════════════════════════════════════════════════
doc.add_paragraph()
doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('WordMaster')
run.font.size = Pt(36)
run.font.bold = True
run.font.color.rgb = RGBColor(0x63, 0x66, 0xF1)

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('架构分析报告')
run.font.size = Pt(24)
run.font.color.rgb = RGBColor(0x6B, 0x6B, 0x70)

ver = doc.add_paragraph()
ver.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = ver.add_run(f'v0.1.0 Beta  |  {datetime.now().strftime("%Y-%m-%d")}')
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0xA0, 0xA0, 0xA6)

doc.add_paragraph()
doc.add_paragraph()
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
info.add_run('AI-Powered English Vocabulary Learning Assistant\n').font.size = Pt(11)
info.add_run('Developer: JasonChen  |  Contact: cby080812b@outlook.com').font.size = Pt(10)

doc.add_page_break()

# ═══════════════════════════════════════════════════
# TABLE OF CONTENTS (manual)
# ═══════════════════════════════════════════════════
doc.add_heading('目录', level=1)
toc_items = [
    '1. 项目概述',
    '2. 技术架构总览',
    '3. 前端架构 (React + Vite)',
    '4. 后端架构 (Python FastAPI)',
    '5. 数据架构 (SQLite)',
    '6. 主题系统',
    '7. AI 功能模块',
    '8. 桌面打包 (PyInstaller + PyWebView)',
    '9. 安全架构',
    '10. 性能分析',
    '11. 部署与发布',
    '12. 项目统计',
]
for item in toc_items:
    p = doc.add_paragraph(item)
    p.paragraph_format.space_after = Pt(4)

doc.add_page_break()

# ═══════════════════════════════════════════════════
# 1. OVERVIEW
# ═══════════════════════════════════════════════════
doc.add_heading('1. 项目概述', level=1)
doc.add_paragraph(
    'WordMaster 是一款基于艾宾浩斯记忆曲线的 AI 智能英语词汇学习桌面软件。'
    '采用 Python FastAPI 后端 + React 前端架构，通过 PyWebView 嵌入为原生 Windows 桌面应用。'
    '支持 5 本内置词书 (27,686 词)、AI 智能对话、AI 阅读生成、6 套视觉主题系统。'
)

# ── Quick facts table ──
doc.add_heading('基本信息', level=2)
table = doc.add_table(rows=9, cols=2, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
data = [
    ('项目名称', 'WordMaster'),
    ('版本', 'v0.1.0 Beta'),
    ('开发者', 'JasonChen'),
    ('技术栈', 'React 18 + FastAPI + SQLite + PyWebView'),
    ('设计语言', 'Crystalline Literacy'),
    ('目标平台', 'Windows 10/11 (x64)'),
    ('授权协议', '专有软件（保留所有权利）'),
    ('代码总量', '~16,100 行 (Python 7,982 + JS/JSX 8,415 + CSS 747)'),
    ('EXE 大小', '28 MB'),
]
for i, (k, v) in enumerate(data):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

# ═══════════════════════════════════════════════════
# 2. TECH ARCHITECTURE
# ═══════════════════════════════════════════════════
doc.add_heading('2. 技术架构总览', level=1)
doc.add_paragraph(
    'WordMaster 采用经典的三层架构：前端展示层 (React SPA)、后端服务层 (FastAPI)、数据持久层 (SQLite)。'
    '桌面端通过 PyWebView (Edge WebView2) 嵌入前端，PyInstaller 打包为独立 EXE。'
)

doc.add_heading('架构图', level=2)
arch = doc.add_paragraph()
arch.style = doc.styles['Normal']
arch.add_run(
    '┌─────────────────────────────────────────────────────┐\n'
    '│                  WordMaster.exe                      │\n'
    '│  ┌──────────────────┐  ┌─────────────────────────┐  │\n'
    '│  │  PyWebView Window │  │  FastAPI Backend         │  │\n'
    '│  │  (Edge WebView2)  │  │  (uvicorn, port 8000)   │  │\n'
    '│  │                   │  │                          │  │\n'
    '│  │  React SPA ───────┼──│→ app.py + routers/ (47 API 路由)  │  │\n'
    '│  │  ├─ Dashboard     │  │  ├─ /api/dashboard       │  │\n'
    '│  │  ├─ Study         │  │  ├─ /api/study           │  │\n'
    '│  │  ├─ Search        │  │  ├─ /api/ai/chat         │  │\n'
    '│  │  ├─ AI Tutor      │  │  ├─ /api/ai/reading      │  │\n'
    '│  │  ├─ AI Reading    │  │  ├─ /api/ai/explain      │  │\n'
    '│  │  ├─ Settings      │  │  └─ ...                  │  │\n'
    '│  │  └─ Theme System  │  │                          │  │\n'
    '│  └──────────────────┘  └───────────┬──────────────┘  │\n'
    '│                                     │                  │\n'
    '│                          ┌─────────▼──────────┐      │\n'
    '│                          │    SQLite DB        │      │\n'
    '│                          │  (wordmaster.db)    │      │\n'
    '│                          │  words: 12,552      │      │\n'
    '│                          │  dictionary: 27,686 │      │\n'
    '│                          │  books: 5           │      │\n'
    '│                          └────────────────────┘      │\n'
    '│                                                     │\n'
    '│  External:                                           │\n'
    '│  ┌──────────────┐  ┌──────────────────────────┐     │\n'
    '│  │ DeepSeek API  │  │ Windows Credential Mgr   │     │\n'
    '│  │ (AI Services) │  │ (keyring, API Key store) │     │\n'
    '│  └──────────────┘  └──────────────────────────┘     │\n'
    '└─────────────────────────────────────────────────────┘'
).font.size = Pt(7.5)
arch.paragraph_format.space_before = Pt(8)

# ═══════════════════════════════════════════════════
# 3. FRONTEND
# ═══════════════════════════════════════════════════
doc.add_heading('3. 前端架构 (React + Vite)', level=1)

doc.add_heading('3.1 技术栈', level=2)
doc.add_paragraph(
    'React 18 + React Router 6 (SPA routing)\n'
    'Vite 5 (build tool, code splitting)\n'
    'Tailwind CSS + CSS Custom Properties (design system)\n'
    'Lucide React (icon library, 20+ icons)\n'
    'Recharts (analytics charts, lazy-loaded)\n'
    'Web Speech API (TTS pronunciation)'
)

doc.add_heading('3.2 组件架构', level=2)
table = doc.add_table(rows=13, cols=3, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ['组件', '类型', '说明']
for i, h in enumerate(headers):
    table.rows[0].cells[i].text = h
    for p in table.rows[0].cells[i].paragraphs:
        for run in p.runs:
            run.font.bold = True

pages_data = [
    ('Dashboard', 'Page', '首页仪表盘，进度环+统计卡片+搜索'),
    ('Study', 'Page', '单词学习，卡片翻转+乱序+艾宾浩斯'),
    ('AITutor', 'Page', 'AI 导师对话，3角色(Emma/Alex/Sophia)'),
    ('Reading', 'Page', 'AI 阅读生成，参数选择+隐藏答案'),
    ('Analytics', 'Page', '学习统计图表 (recharts)'),
    ('Search', 'Page', '全局搜索，英文+中文模糊匹配'),
    ('Settings', 'Page', '设置页，主题选择+外观+AI配置'),
    ('Navbar', 'Component', '顶部导航，6项+暗色切换+Logo'),
    ('WordCard', 'Component', '单词卡片，3D倾斜+翻转动画'),
    ('SegmentControl', 'Component', '分段选择器，滑动指示器动画'),
    ('ErrorBoundary', 'Component', '全局错误捕获，防止白屏'),
    ('ThemeBackground', 'Component', '主题背景(Aurora/Starlight/渐变)'),
]
for i, (name, typ, desc) in enumerate(pages_data):
    table.rows[i+1].cells[0].text = name
    table.rows[i+1].cells[1].text = typ
    table.rows[i+1].cells[2].text = desc

doc.add_heading('3.3 路由设计', level=2)
doc.add_paragraph(
    '/ → Dashboard (首页)\n'
    '/study → Study (学习页, 保留但不显示在导航)\n'
    '/search → Search (搜索)\n'
    '/ai-tutor → AITutor (AI导师)\n'
    '/reading → Reading (AI阅读)\n'
    '/analytics → Analytics (统计分析)\n'
    '/settings → Settings (设置)\n'
    '/settings/ai → AISettings (AI配置)\n'
    '/favorites → Favorites (收藏)\n'
    '/dictionary → Dictionary (词库浏览)'
)

doc.add_heading('3.4 代码分割', level=2)
doc.add_paragraph(
    '使用 React.lazy() + Suspense 实现页面级代码分割：\n'
    '• 主包 (index.js): 194 KB — React + Router + Navbar + 主题系统\n'
    '• Dashboard: 19 KB\n'
    '• Study: 25 KB\n'
    '• AITutor: 10 KB\n'
    '• Reading: 13 KB\n'
    '• Analytics: 394 KB (含 recharts)\n'
    '• Settings: 16 KB (含主题编辑器)\n'
    '• 总计 30 个 JS chunks'
)

# ═══════════════════════════════════════════════════
# 4. BACKEND
# ═══════════════════════════════════════════════════
doc.add_heading('4. 后端架构 (Python FastAPI)', level=1)

doc.add_heading('4.1 技术栈', level=2)
doc.add_paragraph(
    'FastAPI 0.115+ (REST API framework)\n'
    'Uvicorn (ASGI server)\n'
    'SQLAlchemy 2.0+ (ORM)\n'
    'Pydantic 2.7+ (data validation)\n'
    'httpx 0.27+ (async HTTP client for AI API calls)\n'
    'keyring 25+ (Windows Credential Manager)'
)

doc.add_heading('4.2 模块结构 (server/)', level=2)
table = doc.add_table(rows=8, cols=2, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
modules = [
    ('app.py', '入口 + 9 个路由模块 (47 API 路由)'),
    ('models.py', 'SQLAlchemy 数据模型 (8 tables)'),
    ('database.py', '数据库引擎 + 会话管理'),
    ('config_manager.py', 'API Key 安全存储 (keyring)'),
    ('seed.py', 'TXT 词库解析 + 导入'),
    ('ai_service.py', 'AI 服务 (对话/解释/测验/报告)'),
    ('audio_service.py', 'TTS 音频服务 (edge-tts)'),
]
for i, (mod, desc) in enumerate(modules):
    table.rows[i].cells[0].text = mod
    table.rows[i].cells[1].text = desc

doc.add_heading('4.3 API 端点分类', level=2)
table = doc.add_table(rows=6, cols=3, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
api_data = [
    ('学习系统', '8', '/api/dashboard, /api/study, /api/words/*'),
    ('词书管理', '5', '/api/books, /api/books/{id}/*'),
    ('AI 功能', '8', '/api/ai/chat, /api/ai/reading, /api/ai/explain'),
    ('词典搜索', '5', '/api/dictionary/*, /api/search/*'),
    ('音频', '3', '/api/audio/*'),
]
for i, (cat, count, paths) in enumerate(api_data):
    table.rows[i].cells[0].text = cat
    table.rows[i].cells[1].text = count
    table.rows[i].cells[2].text = paths

# ═══════════════════════════════════════════════════
# 5. DATA
# ═══════════════════════════════════════════════════
doc.add_heading('5. 数据架构 (SQLite)', level=1)

doc.add_heading('5.1 数据库表', level=2)
table = doc.add_table(rows=8, cols=3, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ['表名', '行数', '用途']
for i, h in enumerate(headers):
    table.rows[0].cells[i].text = h
    for p in table.rows[0].cells[i].paragraphs:
        for run in p.runs:
            run.font.bold = True

db_data = [
    ('words', '12,552', '单词主表 (SRS进度/掌握度/收藏)'),
    ('dictionary', '27,686', '词典条目 (音标/释义/例句/音频)'),
    ('books', '5', '词书元数据 (高中/CET4/CET6/考研/托福)'),
    ('book_words', '27,691', '词书↔单词多对多关联'),
    ('study_records', '83', '学习事件日志'),
    ('daily_stats', '2', '每日聚合统计'),
    ('user_settings', '1', '用户设置 (key-value)'),
]
for i, (name, count, desc) in enumerate(db_data):
    table.rows[i+1].cells[0].text = name
    table.rows[i+1].cells[1].text = count
    table.rows[i+1].cells[2].text = desc

doc.add_heading('5.2 词库数据', level=2)
doc.add_paragraph(
    '内置词库 (内置词库请勿删除/): 5 个 TXT 文件，1.9 MB\n'
    '• 2 高中-乱序.txt — 3,740 词\n'
    '• 3 四级-乱序.txt — 4,543 词\n'
    '• 4 六级-乱序.txt — 3,991 词\n'
    '• 5 考研-乱序.txt — 5,046 词\n'
    '• 6 托福-乱序.txt — 10,366 词\n'
    '总计: 27,686 词条 (去重后 12,552 唯一词)'
)

doc.add_heading('5.3 数据库迁移', level=2)
doc.add_paragraph(
    '使用 schema_version 表追踪迁移历史。当前迁移包括：\n'
    '• v1.x: words 表新增 review_stage/last_reviewed_at/accuracy_rate/proficiency\n'
    '• v2.x: daily_stats 表新增 correct_count/total_reviews/minutes_studied\n'
    '• v3.x: study_records 表新增 review_stage/book_id\n'
    '• v4.x: dictionary 表创建\n'
    '• v5.x: books + book_words 表创建\n'
    '• v6.x: dictionary 表字段扩展 (definition_cn/en/POS/synonyms)\n'
    '• v7.0: user_settings 表创建 (C-3 迁移)'
)

# ═══════════════════════════════════════════════════
# 6. THEME SYSTEM
# ═══════════════════════════════════════════════════
doc.add_heading('6. 主题系统', level=1)
doc.add_paragraph(
    'WordMaster v0.1.0 实现了完整的主题管理系统，基于 CSS Custom Properties + React Context。'
    '支持 6 套官方主题 + 自定义 RGB 编辑器，localStorage 持久化。'
)

table = doc.add_table(rows=7, cols=3, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
theme_data = [
    ('Crystalline 水晶', '靛紫 #6366F1 + 暖白 #FAFAF9', '默认品牌主题'),
    ('Starlight 星光', '深空 #020617 + 60 星点闪烁', 'CSS 星空背景'),
    ('Ocean 深海', '海蓝 #0EA5E9 + 深海 #0A1628', '安静专注'),
    ('Aurora 极光', '深夜 #061826 + 3 层流动光带', 'CSS 极光动画'),
    ('Galaxy 紫夜', '深紫 #0D0618 + 粉 #EC4899', '渐变背景'),
    ('Mono 极简', '纯黑白 #000 + #FFF + #6B7280', '极致专注'),
]
for i, (name, colors, desc) in enumerate(theme_data):
    table.rows[i].cells[0].text = name
    table.rows[i].cells[1].text = colors
    table.rows[i].cells[2].text = desc

doc.add_paragraph(
    '主题系统架构:\n'
    '• ThemeContext.jsx — React Context 状态管理\n'
    '• themeConfig.js — 6 官方主题 + buildCustomTheme()\n'
    '• ThemeBackground.jsx — 渲染特定背景 (Aurora/Starlight)\n'
    '• AuroraBackground.jsx — 3 层 CSS blur 光带动画\n'
    '• StarlightParticles.jsx — 70 CSS 星点闪烁\n'
    '• ThemeCustomizer.jsx — RGB 自定义编辑器\n'
    '• ThemePreview.jsx — 实时预览卡片'
)

# ═══════════════════════════════════════════════════
# 7. AI MODULE
# ═══════════════════════════════════════════════════
doc.add_heading('7. AI 功能模块', level=1)

doc.add_heading('7.1 AI 服务', level=2)
doc.add_paragraph(
    '• AI Provider: DeepSeek API (deepseek-chat model)\n'
    '• API Key 存储: Windows Credential Manager (keyring)\n'
    '• 超时机制: 10s (test) / 30s (chat) / 90s (reading)\n'
    '• 错误处理: 401 Key无效 / 402 余额不足 / 网络超时 / JSON解析失败'
)

doc.add_heading('7.2 AI 功能清单', level=2)
table = doc.add_table(rows=6, cols=3, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
ai_data = [
    ('AI Tutor', '/api/ai/chat', '3 角色对话 (Emma/Alex/Sophia)'),
    ('AI 阅读', '/api/ai/generate-reading', '参数化文章生成 + 阅读理解题'),
    ('AI 查词', '/api/ai/explain', '词根词缀 + 记忆技巧 + 例句'),
    ('AI 测验', '/api/ai/quiz', '选择题/填空题生成'),
    ('AI 报告', '/api/ai/report', '学习报告生成'),
]
for i, (name, endpoint, desc) in enumerate(ai_data):
    table.rows[i].cells[0].text = name
    table.rows[i].cells[1].text = endpoint
    table.rows[i].cells[2].text = desc

# ═══════════════════════════════════════════════════
# 8. PACKAGING
# ═══════════════════════════════════════════════════
doc.add_heading('8. 桌面打包', level=1)

doc.add_heading('8.1 打包流程', level=2)
doc.add_paragraph(
    '1. Vite build → web/dist/ (React SPA, 30 JS chunks)\n'
    '2. PyInstaller (wordmaster.spec) → dist/WordMaster.exe\n'
    '   打包内容: React前端 + FastAPI后端 + 词库TXT + 资源文件\n'
    '3. per-user 安装程序 (installer/installer.py) → WordMaster_Setup.exe\n'
    '\n'
    'wordmaster.spec 关键配置:\n'
    '• WEB_DIST: web/dist/ → 嵌入 exe 的 web/ 目录\n'
    '• VOCAB_DIR: 内置词库请勿删除/ → 5 TXT 词库\n'
    '• RESOURCES: resources/ → icon.ico, license.txt\n'
    '• hiddenimports: keyring, config_manager, uvicorn 等'
)

doc.add_heading('8.2 运行时路径', level=2)
doc.add_paragraph(
    'Frozen 模式 (exe):\n'
    '  BASE_DIR = sys._MEIPASS (临时解压目录)\n'
    '  FRONTEND_DIR = BASE_DIR / "web"\n'
    '  DATA_DIR = %APPDATA%/WordMaster/ (持久数据)\n'
    '\n'
    '开发模式:\n'
    '  FRONTEND_DIR = PROJECT/web/dist\n'
    '  DATA_DIR = PROJECT/server/ (或 WORDMASTER_DATA_DIR 环境变量)'
)

# ═══════════════════════════════════════════════════
# 9. SECURITY
# ═══════════════════════════════════════════════════
doc.add_heading('9. 安全架构', level=1)
doc.add_paragraph(
    '• API Key 存储: Windows Credential Manager (DPAPI 加密), 非明文\n'
    '• 已移除: XOR+Base64 伪加密 (含硬编码密钥 "WordMaster2024")\n'
    '• /api/ai/config-status: 仅返回 configured: true/false, 不泄露 key 片段\n'
    '• .gitignore: 覆盖 node_modules, dist, *.db, *.log, __pycache__, .env\n'
    '• 用户数据: 全部本地存储, 无网络上传\n'
    '• 日志: 不记录 API Key 内容'
)

# ═══════════════════════════════════════════════════
# 10. PERFORMANCE
# ═══════════════════════════════════════════════════
doc.add_heading('10. 性能分析', level=1)
table = doc.add_table(rows=7, cols=2, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
perf = [
    ('主 JS bundle', '194 KB (gzip 63 KB)'),
    ('首屏加载', '< 200 KB 关键 JS'),
    ('代码分割', '30 chunks, 按需加载'),
    ('数据库查询', 'SQLite 毫秒级, JOIN + 索引'),
    ('动画性能', '纯 CSS GPU composited, 60fps'),
    ('EXE 启动', '~6s (含词库导入)'),
]
for i, (k, v) in enumerate(perf):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

# ═══════════════════════════════════════════════════
# 11. DEPLOYMENT
# ═══════════════════════════════════════════════════
doc.add_heading('11. 部署与发布', level=1)
doc.add_paragraph(
    '发布构建命令:\n'
    '  cd web && npm run build          # 前端构建\n'
    '  pyinstaller wordmaster.spec --clean  # EXE打包\n'
    '  输出: dist/WordMaster_v0.1.0_Beta.exe (28 MB)\n'
    '\n'
    '发布检查清单:\n'
    '  ✅ web/dist 最新构建\n'
    '  ✅ 内置词库请勿删除/ 5 TXT\n'
    '  ✅ resources/ icon.ico + license.txt\n'
    '  ✅ wordmaster.spec hiddenimports 完整\n'
    '  ✅ .gitignore 覆盖敏感文件\n'
    '  ✅ 版本号统一 v0.1.0 Beta\n'
    '  ✅ npm run build 无错误\n'
    '  ✅ EXE 启动验证 (6 页面 + API + 词库)'
)

# ═══════════════════════════════════════════════════
# 12. STATISTICS
# ═══════════════════════════════════════════════════
doc.add_heading('12. 项目统计', level=1)
table = doc.add_table(rows=12, cols=2, style='Light Grid Accent 1')
table.alignment = WD_TABLE_ALIGNMENT.CENTER
stats = [
    ('前端页面', '12 个 (React JSX)'),
    ('前端组件', '10 个'),
    ('Python 模块', '13 个 (server/)'),
    ('API 端点', '47 个'),
    ('数据库表', '9 个 (含 schema_version)'),
    ('词条总数', '27,686 (去重 12,552)'),
    ('官方主题', '6 套 + 自定义 RGB'),
    ('JS chunks', '30 个'),
    ('EXE 大小', '28 MB'),
    ('代码总量', '~16,100 行'),
    ('JS/JSX 代码', '8,415 行'),
]
for i, (k, v) in enumerate(stats):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

# ── Save ──
from pathlib import Path
out = Path(__file__).resolve().parent / 'WordMaster_Architecture_Report_v0.1.0.docx'
doc.save(str(out))
print(f'Report saved: {out}')
