# 错题库数据规范（errors.json）

线下作业/试卷的错题经拍照收录后落在 `errors.json`，是三年错题本的权威数据源。
app 只读它；改它的唯一入口是 Claude Code 的收录流程（见下）。

## 错题记录字段

```json
{
  "id": "e-20260912-01",
  "date": "2026-09-12",
  "source": "作业",
  "sourceDetail": "《同步》P5 第3题",
  "stem": "计算：-3 - 5 × (-2)",
  "answer": "7",
  "kidAnswer": "-13",
  "kaodian": ["hunhe-yunsuan"],
  "errorType": "fuhao",
  "errorNote": "把性质符号当运算符号，-3-5 先算成 -8 后又丢了乘法",
  "confirmed": true,
  "status": "active",
  "review": { "due": "2026-09-13", "streak": 0 },
  "variantTopic": null
}
```

- `id`：`e-YYYYMMDD-NN`，当天内递增。
- `source`：`作业` / `试卷` / `课堂`。`sourceDetail` 写页码/卷名/题号，方便回翻原件。
- `stem` / `answer`：题干与正确答案，文本重排（分数写 `a/b`，乘方写 `x^2`），不存照片。
- `kidAnswer`：孩子的错误答案，照片上辨认不出就 `null`。
- `kaodian`：`kaodian-tree.json` 里的节点 id 数组，至少 1 个，主考点放第一位。
- `errorType`：错因分类，取值见下表。
- `errorNote`：一句话说清这题具体错在哪，给家长讲题时直接用。
- `confirmed`：收录时妈妈确认过为 `true`；AI 识别后未经确认为 `false`（app 不展示未确认的）。
- `status`：`active`（在练）/ `graduated`（连对 3 轮毕业）/ `retired`（超纲或题目录错，人工下线）。
- `review`：复习调度，与 app 现有错题重做机制一致——到期答对隔 1 天再考，连对 3 轮毕业；
  答错 `streak` 清零、次日再来。`due` 为下次到期日。
- `variantTopic`：对应 `bank.js` 生成器名，填了则重练时按 1 原题 + 2 变式混出；
  没有对应生成器就 `null`，只重做原题。

## 错因分类（errorType）

| 值 | 含义 |
|---|---|
| `fuhao` | 性质符号 vs 运算符号混淆（实测高频） |
| `kuohao` | 去括号/分配漏项、只给第一项变号（实测高频） |
| `fufenshu` | 负分数/分数运算错（实测高频） |
| `dishu` | 乘方底数圈错（实测高频） |
| `gainian` | 概念不清 |
| `shenti` | 审题偏差、漏条件 |
| `fangfa` | 方法不会、无从下手 |
| `buzhou` | 步骤跳漏、过程不完整 |
| `cuxin` | 计算粗心、抄错数 |
| `biaoda` | 表达不规范（应用题不设不答、证明格式） |

## 收录流程（Claude Code 会话内执行）

1. 妈妈手机拍作业/试卷（密集小字发**原图**或当文件发），发到与机器人的飞书私聊，说「收错题」。
2. Claude 跑 `python3 ~/math-plan/tools/fetch_photos.py --hours 24` 拉图到 `~/math-plan/inbox/`，逐张 Read 识别。
3. 只收**做错的题**；每题产出一条记录（`confirmed: false`），整理成表格给妈妈过目：
   题干 / 孩子答案 / 正确答案 / 考点 / 错因。拿不准考点或错因的标出来问。
4. 妈妈确认后置 `confirmed: true`，写入 `errors.json`，`updated` 改当天。
5. 同步发布：`cp ~/math-plan/data/*.json ~/book-link/math/data/` 后 commit + push，
   线上 app 下次打开即拉到新错题。（数据文件独立于 `build.py`，不用重新构建 HTML。）

## 考点树维护

- 章节归属按北师大目录初排，学校课表不一致时改 `kaodian-tree.json` 的 `grade`，不改代码。
- 新增考点：加节点即可，id 一旦被 `errors.json` 引用就不再改名（要改名需同步替换所有引用）。
