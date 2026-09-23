"""Built-in confusion sets (commonly-confused word pairs).

These are authored reference data (not AI-generated) that seed the 易混词系统.
Each pair includes a Chinese distinction, a memory tip and a contrast example.
"""

CONFUSION_SEED = [
    {
        "word_a": "affect", "word_b": "effect",
        "distinction_cn": "affect 是动词「影响」；effect 是名词「影响/效果」。（affect = 动作，effect = 结果）",
        "memory_tip_cn": "a 开头是动作（Action），e 开头是结果（End result）。",
        "example_en": "The new policy will affect every student, and its effect will be visible next year.",
        "example_cn": "新政策将影响每位学生，其效果明年就会显现。",
    },
    {
        "word_a": "economic", "word_b": "economical",
        "distinction_cn": "economic 是「经济相关的」；economical 是「节约的、经济实惠的」。",
        "memory_tip_cn": "economical 末尾的 -al 谐音「省」，表示省钱实惠。",
        "example_en": "The country faces an economic crisis, but this car is very economical to run.",
        "example_cn": "该国面临经济危机，但这辆车开起来非常省钱。",
    },
    {
        "word_a": "adapt", "word_b": "adopt",
        "distinction_cn": "adapt 是「适应、改编」；adopt 是「采纳、收养」。",
        "memory_tip_cn": "adapt 含 a 像「调整(adjust)」；adopt 含 o 像「选择(option)」。",
        "example_en": "You must adapt to the new rules, or adopt a different strategy.",
        "example_cn": "你必须适应新规则，或采取不同的策略。",
    },
    {
        "word_a": "rise", "word_b": "raise",
        "distinction_cn": "rise 是不及物动词「上升」（自己升）；raise 是及物动词「抬起」（使…升）。",
        "memory_tip_cn": "rise 自己升起（无宾语）；raise 需要宾语（raise your hand）。",
        "example_en": "The sun rises in the east; please raise your hand if you agree.",
        "example_cn": "太阳从东方升起；同意请举手。",
    },
    {
        "word_a": "historic", "word_b": "historical",
        "distinction_cn": "historic 是「有历史意义的」；historical 是「历史的、与历史相关的」。",
        "memory_tip_cn": "historic 有「c」像「重要(critical)」；historical 泛指历史学科。",
        "example_en": "The signing was a historic moment, documented in the historical records.",
        "example_cn": "这次签署是历史性时刻，被记载于历史档案中。",
    },
    {
        "word_a": "principal", "word_b": "principle",
        "distinction_cn": "principal 是「校长；主要的」；principle 是「原则、原理」。",
        "memory_tip_cn": "principal 以 pal 结尾（校长是朋友 pal）；principle 以 ple 结尾（规则 rule）。",
        "example_en": "The principal explained the school's basic principle of fairness.",
        "example_cn": "校长解释了学校公平的基本原则。",
    },
    {
        "word_a": "complement", "word_b": "compliment",
        "distinction_cn": "complement 是「补充、使完善」；compliment 是「赞美」。",
        "memory_tip_cn": "complement 含 e 像「完整(complete)」；compliment 含 i 像「我(i)被夸」。",
        "example_en": "A red scarf will complement your coat, and many people will compliment you.",
        "example_cn": "红围巾会与你的外套相得益彰，许多人会赞美你。",
    },
    {
        "word_a": "emigrate", "word_b": "immigrate",
        "distinction_cn": "emigrate 是「移出（离开本国）」；immigrate 是「移入（进入他国）」。",
        "memory_tip_cn": "e 开头是 exit（出去），i 开头是 in（进来）。",
        "example_en": "They decided to emigrate from China and immigrate to Canada.",
        "example_cn": "他们决定移出中国，移入加拿大。",
    },
]
