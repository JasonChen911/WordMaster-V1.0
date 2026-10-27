# 数据修复 / 污染检测报告 (DATA_REPAIR_REPORT)

版本：0.1.0 · 检测日期：2026-09-26

## 结论：未发现历史 material 污染

对以下数据库逐一执行了污染签名检测（空中文释义、material 来源空释义词典条目、大小写重复词条）：

| 数据库 | words | 空中文 words | material 词典条目 | 自定义词书 |
|---|---|---|---|---|
| 开发库 `server/wordmaster.db` | 12552 | 0 | 0 | 0 |
| 生产 `AppData/WordMaster/wordmaster.db` | 12547 | 0 | 0 | 0 |
| `wordmaster.bak-20260923/24/26.db` | 12547 | 0 | 0 | 0 |

**结果：全部干净。** 无空释义残留、无 `source='material'` 空释义词典条目、无大小写重复词条、无自定义词书污染。因此**无需执行任何数据迁移或删除**。

## 检测方法（污染签名）

1. **空中文释义 study word**：`words.chinese IS NULL OR chinese=''` —— AI 候选「只有英文、缺中文」被提前写入正式库的典型痕迹。
2. **material 来源空释义词典条目**：`dictionary.source='material' AND definition_cn=''` —— 本地降级（无 AI）候选被「全选加入词书」后留下残缺记录的痕迹。
3. **大小写重复词条**：`lower(english)` 分组 `COUNT>1` —— 同词被重复添加、完整记录与残缺记录并存的痕迹。
4. **非内置词书**：`books.is_builtin=0` —— 历史 material 词书遗留痕迹。

## 为什么代码里存在污染路径但库是干净的

- `POST /api/material/analyze`（AI 提取）只返回候选、**不写库**，预览/取消不会留下词条（架构正确）。
- 只有 `POST /api/material/import`（用户明确点击「生成词书」）才写库。现有库无 material 词书，说明历史上要么从未触发、要么触发时 AI 可用（AI 路径会带中文释义）。

## 本次新增的幂等修复函数

`server/repair.py::repair_data(db)`，在 `db_init.init_db()` 启动时自动运行，**不删除用户数据**：

1. 回填空释义词条的中文（exact → lemma → 词典 `definition_cn`）；
2. 统计 material 空释义词典条目（仅审计，不自动删除）；
3. 合并大小写重复 `words` 行：先重定向 `book_words` 引用到规范行、吸收被删行的额外内容，再删除空壳行。

输出报告字典：`empty_chinese_words_found/fixed/remaining`、`material_dict_empty_definition`、`case_duplicate_words_merged/remaining`。可独立运行：

```bash
python server/repair.py   # 打印报告；有污染时退出码非 0
```

## 本次写入前的防污染加固（治本）

`material_import` 现在：
- `_canonical_word()`：候选按 exact→lemma 折叠到库内原形（`students`→`student`），杜绝重复词形行；
- `_resolve_meaning()`：释义为空时从库内回填中文；
- normalize + 去重（按折叠后词形）。

`reading_add_word` 同样按 exact→lemma 解析，避免阅读生词新建词形重复行。

因此即使未来在无 AI 环境使用本地降级导入，也不会再产生「无中文释义的 material 词条」。
