# 07 · AI 架构 (AI ARCHITECTURE)

## AI Gateway（统一入口）

```
server/ai/
├── gateway.py            # chat_completion（retry/token 日志）+ chat_json（schema 校验+repair+fallback）
├── schemas.py            # pydantic 结构化输出契约
├── providers/
│   └── deepseek.py       # DeepSeek 具体实现（URL/headers/model）
└── services/
    ├── material_service.py    # 材料 → 候选词（tokenize→AI 语义判断）
    ├── analysis_service.py    # 学习诊断（为什么记不住）
    ├── exercise_service.py    # 针对性练习
    └── example_service.py     # 分级例句（缓存）
```

## Gateway 统一职责

- API Key / Base URL / Model 解析（来自 `config_manager`，Key 存 keyring，不写死）。
- Timeout / Retry（瞬时错误重试 1 次）。
- JSON 解析 + pydantic schema 校验 + repair（裸列表包装）+ fallback。
- Token usage 日志（不记录 Key 内容）。
- 错误映射（401/402/429/5xx/超时/断网 → 友好中文）。

## 结构化输出契约

- `MaterialAnalysis`：`document_summary` + `words[]`（word/lemma/meaning_zh/importance 0-1/difficulty/tags/example/source_sentence）。
- `LearningAnalysis`：`diagnosis` + `problem_type` + `confused_with` + `recommended_exercise_type` + `suggestions`。
- `ExerciseSet`：`questions[]`（type/question/options/answer/explanation/target_words）。

## 关键原则

1. **AI 不做程序能做的事**：tokenization、去重、停用词过滤、FSRS、统计全在本地完成；LLM 只做语义判断与内容生成。
2. **AI 不伪造统计**：所有正确率/次数/遗忘风险来自数据库；AI 只解释数字。
3. **AI 挂掉 ≠ 软件不能用**：材料分析有本地频率 fallback；练习有离线 fallback；诊断有「数据不足」提示。
4. **Diagnosis 输入最小化**：只传必要学习摘要（word + 最近事件 + 正确率 + 混淆词），不上传完整数据库。

## 测试

`tests/test_ai_gateway.py`（17 项）：code fence 剥离、JSON 提取、schema 校验/repair、文本清洗、tokenization、本地候选 fallback。
