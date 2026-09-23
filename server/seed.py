"""Built-in WordMaster word-list discovery and parsing.

Supported tab-separated TXT layouts:

* ``word<TAB>definition``
* ``index<TAB>word<TAB>definition``
* ``word<TAB>phonetic<TAB>definition<TAB>example<TAB>translation``

The resource resolver deliberately checks both the development directory and
PyInstaller's ``sys._MEIPASS/server`` directory.
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

BUILTIN_BOOK_NAMES = {
    "cet4.txt": "CET-4 四级词汇",
    "cet6.txt": "CET-6 六级词汇",
    "ielts.txt": "IELTS 雅思词汇",
    "toefl.txt": "TOEFL 托福词汇",
    "gre.txt": "GRE 词汇",
    "gaokao.txt": "高考英语词汇",
}


def get_wordlist_dir() -> list[Path]:
    """Return directories containing bundled TXT word lists.

    Priority: ``data/vocabulary/`` folder first, then ``server/`` as fallback.
    """
    dirs: list[Path] = []
    if getattr(sys, "frozen", False):
        bundle_root = Path(sys._MEIPASS)
        # Priority 1: 内置词库请勿删除/ (bundled resource)
        builtin_resource = bundle_root / "内置词库请勿删除"
        if builtin_resource.exists() and list(builtin_resource.glob("*.txt")):
            dirs.append(builtin_resource)
            return dirs
        # Priority 2: data/vocabulary/ (legacy path)
        builtin_dir = bundle_root / "data" / "vocabulary"
        if builtin_dir.exists() and list(builtin_dir.glob("*.txt")):
            dirs.append(builtin_dir)
            return dirs
        # Fallback: server/ directory
        bundled_server = bundle_root / "server"
        if bundled_server.exists():
            dirs.append(bundled_server)
        if not dirs:
            dirs.append(bundle_root)
        return dirs

    # Development mode
    project_root = HERE.parent  # WordMaster/
    builtin_dir = project_root / "data" / "vocabulary"
    if builtin_dir.exists():
        dirs.append(builtin_dir)
    # Only add server as fallback if data/vocabulary has no .txt files
    server_has_txts = list(HERE.glob("*.txt"))
    if not builtin_dir.exists() or not list(builtin_dir.glob("*.txt")):
        if server_has_txts:
            dirs.append(HERE)
    return dirs


def _looks_like_phonetic(value: str) -> bool:
    value = value.strip()
    ipa_markers = set("ˈˌəɪʊæɑɒɔɛɜɚʌθðʃʒŋɡ")
    return (
        (value.startswith("/") and value.endswith("/"))
        or (value.startswith("[") and value.endswith("]"))
        or any(character in ipa_markers for character in value)
    )


def parse_wordlist_line(line: str) -> tuple[str, str, str, str, str] | None:
    """Parse one TXT row into ``(word, phonetic, definition, example, translation)``."""
    line = line.strip().lstrip("\ufeff")
    if not line or line.startswith("#"):
        return None

    parts = [part.strip() for part in line.split("\t")]
    if len(parts) >= 3 and parts[0].isdigit():
        parts = parts[1:]
    if len(parts) < 2:
        return None

    word = parts[0].lower()
    if (
        not word
        or len(word) > 50
        or re.search(r"[^a-zA-Z\-'.]", word)
    ):
        return None

    phonetic = ""
    definition = ""
    example = ""
    translation = ""

    if len(parts) == 2:
        definition = parts[1]
    elif _looks_like_phonetic(parts[1]) or len(parts) >= 4:
        phonetic = parts[1]
        definition = parts[2]
        example = parts[3] if len(parts) > 3 else ""
        translation = parts[4] if len(parts) > 4 else ""
    else:
        # Three-column rows without phonetic delimiters are treated as
        # word/definition/example, which is safer for ordinary TXT files.
        definition = parts[1]
        example = parts[2]

    if not any((phonetic, definition, example, translation)):
        return None
    return word, phonetic, definition, example, translation


def load_word_file(path: Path) -> list[tuple[str, str, str, str, str]]:
    """Load a TXT file and keep one canonical row per English word."""
    words: list[tuple[str, str, str, str, str]] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            parsed = parse_wordlist_line(line)
            if parsed and parsed[0] not in seen:
                seen.add(parsed[0])
                words.append(parsed)
    return words


def _display_name_from_filename(filename: str) -> str:
    """Derive a human-readable book name from a Chinese or English filename."""
    stem = Path(filename).stem
    name_lower = filename.lower()
    if name_lower in BUILTIN_BOOK_NAMES:
        return BUILTIN_BOOK_NAMES[name_lower]
    # Map Chinese keywords to clean names
    cn_map = {
        "高中": "高中词汇", "四级": "四级词汇", "六级": "六级词汇",
        "考研": "考研词汇", "托福": "托福词汇", "雅思": "雅思词汇",
    }
    for keyword, display in cn_map.items():
        if keyword in stem:
            return display
    # Strip leading numbers as fallback
    import re as _re
    cleaned = _re.sub(r'^\d+\s*', '', stem)
    return cleaned or stem


def load_builtin_books() -> list[tuple[str, str, list[tuple[str, str, str, str, str]]]]:
    """Discover every bundled TXT file from all word-list directories."""
    wordlist_dirs = get_wordlist_dir()
    seen_filenames: set[str] = set()
    books: list[tuple[str, str, list[tuple[str, str, str, str, str]]]] = []

    for wordlist_dir in wordlist_dirs:
        for path in sorted(wordlist_dir.glob("*.txt")):
            # Skip requirements.txt and other non-word files
            if path.name.lower() in ("requirements.txt",):
                continue
            # Each filename only once (data/vocabulary/ takes priority)
            key = path.name.lower()
            if key in seen_filenames:
                continue
            seen_filenames.add(key)

            entries = load_word_file(path)
            if not entries:
                continue
            filename = path.name.lower()
            display_name = _display_name_from_filename(path.name)
            books.append((filename, display_name, entries))

    return books


def load_word_files() -> list[tuple[str, str, str, str, str]]:
    """Return the de-duplicated union of all built-in word lists."""
    seen: set[str] = set()
    words: list[tuple[str, str, str, str, str]] = []
    for _filename, _display_name, entries in load_builtin_books():
        for entry in entries:
            if entry[0] not in seen:
                seen.add(entry[0])
                words.append(entry)
    return words


# Original handpicked 100 words — used as fallback if word files are missing
FALLBACK_WORDS = [
    ("abandon", "/əˈbændən/", "放弃；抛弃", "He decided to abandon his plan to travel.", "他决定放弃旅行计划。"),
    ("ability", "/əˈbɪləti/", "能力；才能", "She has the ability to learn quickly.", "她有快速学习的能力。"),
    ("abroad", "/əˈbrɔːd/", "在国外；到国外", "He dreams of studying abroad next year.", "他梦想明年出国留学。"),
    ("absence", "/ˈæbsəns/", "缺席；不在", "His absence from the meeting was noticed.", "他缺席会议被注意到了。"),
    ("absolute", "/ˈæbsəluːt/", "绝对的；完全的", "I have absolute confidence in her.", "我对她有绝对的信心。"),
    ("absorb", "/əbˈzɔːrb/", "吸收；吸引", "Plants absorb water from the soil.", "植物从土壤中吸收水分。"),
    ("abstract", "/ˈæbstrækt/", "抽象的；摘要", "The concept is too abstract to understand.", "这个概念太抽象了，难以理解。"),
    ("abundant", "/əˈbʌndənt/", "丰富的；充裕的", "The region has abundant natural resources.", "该地区有丰富的自然资源。"),
    ("accelerate", "/əkˈseləreɪt/", "加速；促进", "We need to accelerate the development process.", "我们需要加快开发进程。"),
    ("accept", "/əkˈsept/", "接受；认可", "Please accept my sincere apology.", "请接受我真诚的道歉。"),
    ("access", "/ˈækses/", "进入；通道；访问", "Students have access to the online library.", "学生可以访问在线图书馆。"),
    ("accompany", "/əˈkʌmpəni/", "陪伴；伴随", "I will accompany you to the station.", "我会陪你去车站。"),
    ("accomplish", "/əˈkɑːmplɪʃ/", "完成；实现", "We accomplished our goal ahead of schedule.", "我们提前完成了目标。"),
    ("accurate", "/ˈækjərət/", "准确的；精确的", "The data needs to be accurate and reliable.", "数据需要准确可靠。"),
    ("achieve", "/əˈtʃiːv/", "达到；取得", "She worked hard to achieve her dreams.", "她努力工作以实现梦想。"),
    ("acknowledge", "/əkˈnɑːlɪdʒ/", "承认；确认", "He acknowledged his mistake publicly.", "他公开承认了自己的错误。"),
    ("acquire", "/əˈkwaɪər/", "获得；获取", "It takes time to acquire new skills.", "获取新技能需要时间。"),
    ("adapt", "/əˈdæpt/", "适应；改编", "Animals must adapt to their environment.", "动物必须适应它们的环境。"),
    ("adequate", "/ˈædɪkwət/", "充足的；适当的", "We need adequate preparation before the exam.", "考试前我们需要充分的准备。"),
    ("adjust", "/əˈdʒʌst/", "调整；适应", "You need to adjust the screen brightness.", "你需要调整屏幕亮度。"),
    ("administration", "/ədˌmɪnɪˈstreɪʃn/", "管理；行政", "The administration building is on the left.", "行政大楼在左边。"),
    ("admire", "/ədˈmaɪər/", "钦佩；赞赏", "I really admire your courage and determination.", "我真的很钦佩你的勇气和决心。"),
    ("advantage", "/ədˈvæntɪdʒ/", "优势；有利条件", "Speaking English gives you an advantage.", "会说英语给你一个优势。"),
    ("adventure", "/ədˈventʃər/", "冒险；奇遇", "They set off on a great adventure.", "他们开始了一场伟大的冒险。"),
    ("advertisement", "/ˌædvərˈtaɪzmənt/", "广告；宣传", "The advertisement attracted many customers.", "这个广告吸引了很多顾客。"),
    ("affair", "/əˈfer/", "事务；事件", "The meeting was a serious affair.", "这次会议是一件严肃的事情。"),
    ("affection", "/əˈfekʃn/", "感情；喜爱", "She showed great affection for her students.", "她对学生们表现出极大的关爱。"),
    ("afford", "/əˈfɔːrd/", "负担得起；提供", "I can't afford to buy a new car now.", "我现在买不起新车。"),
    ("aggressive", "/əˈɡresɪv/", "侵略的；好斗的", "The company adopted an aggressive strategy.", "公司采取了积极的策略。"),
    ("agreement", "/əˈɡriːmənt/", "协议；同意", "Both parties signed the agreement.", "双方签署了协议。"),
    ("agriculture", "/ˈæɡrɪkʌltʃər/", "农业；农学", "Agriculture is the backbone of the economy.", "农业是经济的支柱。"),
    ("allow", "/əˈlaʊ/", "允许；准许", "Smoking is not allowed in this building.", "本建筑物内不允许吸烟。"),
    ("alternative", "/ɔːlˈtɜːrnətɪv/", "替代的；选择", "We need to find an alternative solution.", "我们需要找到一个替代方案。"),
    ("amaze", "/əˈmeɪz/", "使惊讶；使惊奇", "Her performance never fails to amaze me.", "她的表演总是让我惊叹。"),
    ("ambition", "/æmˈbɪʃn/", "雄心；野心", "His ambition is to become a successful entrepreneur.", "他的抱负是成为一名成功的企业家。"),
    ("analyze", "/ˈænəlaɪz/", "分析；解析", "We need to analyze the data carefully.", "我们需要仔细分析数据。"),
    ("ancestor", "/ˈænsestər/", "祖先；祖宗", "Our ancestors lived in this land for centuries.", "我们的祖先在这片土地上生活了几个世纪。"),
    ("ancient", "/ˈeɪnʃənt/", "古代的；古老的", "The ancient temple attracts many tourists.", "这座古老的寺庙吸引了许多游客。"),
    ("anniversary", "/ˌænɪˈvɜːrsəri/", "周年纪念日", "Today is our tenth wedding anniversary.", "今天是我们结婚十周年纪念日。"),
    ("announce", "/əˈnaʊns/", "宣布；通告", "The president will announce the decision tomorrow.", "总统将于明天宣布决定。"),
    ("annual", "/ˈænjuəl/", "每年的；年度的", "The company holds an annual meeting in March.", "公司在三月举行年度会议。"),
    ("anxiety", "/æŋˈzaɪəti/", "焦虑；忧虑", "Too much anxiety can affect your health.", "过度焦虑会影响你的健康。"),
    ("apologize", "/əˈpɑːlədʒaɪz/", "道歉；认错", "You should apologize for what you said.", "你应该为你说的话道歉。"),
    ("apparent", "/əˈpærənt/", "明显的；表面上的", "It became apparent that something was wrong.", "很明显出了什么问题。"),
    ("appeal", "/əˈpiːl/", "呼吁；吸引", "The idea of working abroad appeals to me.", "出国工作的想法吸引了我。"),
    ("appetite", "/ˈæpɪtaɪt/", "食欲；胃口", "Exercise gave her a healthy appetite.", "运动让她有了健康的食欲。"),
    ("application", "/ˌæplɪˈkeɪʃn/", "申请；应用", "I submitted my job application yesterday.", "我昨天提交了工作申请。"),
    ("appreciate", "/əˈpriːʃieɪt/", "欣赏；感激", "I really appreciate your help and support.", "我非常感激你的帮助和支持。"),
    ("approach", "/əˈproʊtʃ/", "接近；方法", "We need a different approach to solve this problem.", "我们需要不同的方法来解决这个问题。"),
    ("appropriate", "/əˈproʊpriət/", "适当的；合适的", "Please wear appropriate clothing for the interview.", "请穿着合适的衣服参加面试。"),
    ("approve", "/əˈpruːv/", "批准；赞成", "The committee approved the new proposal.", "委员会批准了新提案。"),
    ("arise", "/əˈraɪz/", "出现；产生", "Unexpected problems may arise during the project.", "项目期间可能会出现意想不到的问题。"),
    ("arrange", "/əˈreɪndʒ/", "安排；整理", "I'll arrange a meeting for next week.", "我会安排下周的会议。"),
    ("artificial", "/ˌɑːrtɪˈfɪʃl/", "人工的；人造的", "Artificial intelligence is changing the world.", "人工智能正在改变世界。"),
    ("aspect", "/ˈæspekt/", "方面；层面", "We should consider every aspect of the issue.", "我们应该考虑问题的每一个方面。"),
    ("assemble", "/əˈsembl/", "集合；组装", "The students assembled in the main hall.", "学生们在主厅集合。"),
    ("assess", "/əˈses/", "评估；评定", "Teachers need to assess students' progress regularly.", "教师需要定期评估学生的进步。"),
    ("assign", "/əˈsaɪn/", "分配；指派", "The manager assigned the task to the new employee.", "经理把任务分配给了新员工。"),
    ("assist", "/əˈsɪst/", "帮助；协助", "Can I assist you with anything?", "我能帮你什么吗？"),
    ("associate", "/əˈsoʊʃieɪt/", "联系；关联", "People often associate red with danger.", "人们经常把红色与危险联系起来。"),
    ("assume", "/əˈsuːm/", "假设；承担", "Don't assume that everyone agrees with you.", "不要假设每个人都同意你。"),
    ("atmosphere", "/ˈætməsfɪr/", "气氛；大气", "The restaurant has a romantic atmosphere.", "这家餐厅有一种浪漫的气氛。"),
    ("attach", "/əˈtætʃ/", "附上；连接", "Please attach your photo to the application form.", "请把你的照片附在申请表上。"),
    ("attempt", "/əˈtempt/", "尝试；企图", "She made an attempt to break the world record.", "她尝试打破世界纪录。"),
    ("attend", "/əˈtend/", "参加；出席", "All students must attend the morning assembly.", "所有学生必须参加晨会。"),
    ("attitude", "/ˈætɪtuːd/", "态度；看法", "A positive attitude leads to better results.", "积极的态度带来更好的结果。"),
    ("attract", "/əˈtrækt/", "吸引；引起", "The beautiful scenery attracts many visitors.", "美丽的风景吸引了许多游客。"),
    ("audience", "/ˈɔːdiəns/", "观众；听众", "The audience gave a standing ovation.", "观众起立鼓掌。"),
    ("authority", "/əˈθɔːrəti/", "权威；权力", "The local authority is responsible for road maintenance.", "地方当局负责道路维护。"),
    ("available", "/əˈveɪləbl/", "可用的；有效的", "Is the manager available this afternoon?", "经理今天下午有空吗？"),
    ("average", "/ˈævərɪdʒ/", "平均的；普通的", "The average temperature in July is 30 degrees.", "七月的平均气温是30度。"),
    ("avoid", "/əˈvɔɪd/", "避免；避开", "Try to avoid eating too much sugar.", "尽量避免吃太多糖。"),
    ("aware", "/əˈwer/", "意识到的；知道的", "Are you aware of the risks involved?", "你知道涉及的风险吗？"),
    ("balance", "/ˈbæləns/", "平衡；余额", "You need to find a balance between work and life.", "你需要在工作和生活之间找到平衡。"),
    ("barrier", "/ˈbæriər/", "障碍；屏障", "Language can be a barrier to communication.", "语言可能是沟通的障碍。"),
    ("battle", "/ˈbætl/", "战斗；斗争", "She is fighting a battle against cancer.", "她正在与癌症作斗争。"),
    ("behave", "/bɪˈheɪv/", "表现；行为", "Children should learn to behave in public.", "孩子们应该学会在公共场合表现。"),
    ("belong", "/bɪˈlɔːŋ/", "属于；应在", "This book belongs to the library.", "这本书属于图书馆。"),
    ("benefit", "/ˈbenɪfɪt/", "利益；好处", "Exercise has many health benefits.", "运动有许多健康益处。"),
    ("bitter", "/ˈbɪtər/", "苦的；痛苦的", "The medicine has a bitter taste.", "这种药有苦味。"),
    ("blame", "/bleɪm/", "责备；归咎", "Don't blame others for your own mistakes.", "不要因为自己的错误责备别人。"),
    ("bless", "/bles/", "祝福；保佑", "God bless you and your family.", "愿上帝保佑你和你的家人。"),
    ("boundary", "/ˈbaʊndri/", "边界；界限", "The river forms the boundary between the two countries.", "这条河是两国的边界。"),
    ("brilliant", "/ˈbrɪliənt/", "杰出的；明亮的", "She came up with a brilliant idea.", "她想出了一个绝妙的主意。"),
    ("broadcast", "/ˈbrɔːdkæst/", "广播；播送", "The news will be broadcast at 7 pm.", "新闻将在晚上7点播出。"),
    ("budget", "/ˈbʌdʒɪt/", "预算；经费", "We need to stick to our budget this month.", "这个月我们需要坚持预算。"),
    ("burden", "/ˈbɜːrdn/", "负担；重担", "The tax burden is too heavy for small businesses.", "税收负担对小企业来说太重了。"),
    ("calculate", "/ˈkælkjuleɪt/", "计算；估计", "Can you calculate the total cost for me?", "你能帮我计算总费用吗？"),
    ("campaign", "/kæmˈpeɪn/", "运动；战役", "They launched a marketing campaign last week.", "他们上周发起了一场营销活动。"),
    ("capable", "/ˈkeɪpəbl/", "有能力的；能干的", "She is capable of handling difficult situations.", "她有能力处理困难的情况。"),
    ("capture", "/ˈkæptʃər/", "捕获；俘获", "The photographer tried to capture the perfect moment.", "摄影师试图捕捉完美的瞬间。"),
    ("career", "/kəˈrɪr/", "职业；生涯", "She chose teaching as her lifelong career.", "她选择教学作为终身职业。"),
    ("celebrate", "/ˈselɪbreɪt/", "庆祝；祝贺", "Let's celebrate your success together!", "让我们一起庆祝你的成功！"),
    ("challenge", "/ˈtʃælɪndʒ/", "挑战；质疑", "Learning a new language is a great challenge.", "学习一门新语言是一个巨大的挑战。"),
    ("character", "/ˈkærəktər/", "性格；角色", "Honesty is an important part of her character.", "诚实是她性格的重要组成部分。"),
    ("circumstance", "/ˈsɜːrkəmstæns/", "环境；情况", "Under no circumstances should you give up.", "在任何情况下你都不应该放弃。"),
    ("civilization", "/ˌsɪvələˈzeɪʃn/", "文明；文化", "Ancient Egypt had a great civilization.", "古埃及有伟大的文明。"),
    ("colleague", "/ˈkɑːliːɡ/", "同事；同僚", "I discussed the issue with my colleagues.", "我和同事们讨论了这个问题。"),
    ("comfortable", "/ˈkʌmftəbl/", "舒适的；舒服的", "This chair is very comfortable to sit on.", "这把椅子坐起来很舒服。"),
    ("communicate", "/kəˈmjuːnɪkeɪt/", "交流；沟通", "We communicate with each other through email.", "我们通过电子邮件相互沟通。"),
]


# Load once at module import so initialization uses the same canonical data for
# both the study table and per-book dictionary tables.
BUILTIN_BOOKS = load_builtin_books()
_seen_words: set[str] = set()
_file_words: list[tuple[str, str, str, str, str]] = []
for _filename, _display_name, _entries in BUILTIN_BOOKS:
    for _entry in _entries:
        if _entry[0] not in _seen_words:
            _seen_words.add(_entry[0])
            _file_words.append(_entry)

WORDS = _file_words if _file_words else FALLBACK_WORDS
