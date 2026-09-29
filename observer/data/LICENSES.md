# 数据来源与许可

- `words.json`：取自 [ECDICT](https://github.com/skywind3000/ECDICT)（MIT License, Copyright (c) 2025 Linwei），标注为中考（zk）的词条，释义经精简。七上课本词（book = hj7a）按沪教版《义务教育教科书 英语 七年级上册》书后「各单元单词和短语」表整理（单词、中文释义、所属单元、是否只要求理解），用于按课本进度出词，不转载课文。
- `recite.json`：原文取自 [GushiPinyinTest](https://github.com/Mario-Hero/GushiPinyinTest)（LGPL-2.1），用 [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)（MIT）比对修正；古诗文原文属公有领域。篇目依据国家中小学智慧教育平台统编版电子课本目录。
- `books.json`：教材版本、链接与中考信息整理自深圳市教育局、深圳市教科院、教育部官网公开文件，链接指向官方页面，不转载教材正文。

## pe.json
深圳市教育局《2026年深圳市初中学业水平考试体育与健康科目考试项目规则和评分标准》评分表（男生部分），政府公开文件，程序解析自官方 PDF：https://szeb.sz.gov.cn/home/xxgk/flzy/wjtz/content/post_12214618.html

## speak.json 与 audio/en/
模仿朗读短文为本应用原创；示范音频由 edge-tts（en-US-JennyNeural）生成。

## vendor/ts-fsrs-5.4.2.umd.js
单词与背诵的复习间隔用 [ts-fsrs](https://github.com/open-spaced-repetition/ts-fsrs) 5.4.2（FSRS 算法，MIT License, Copyright (c) 2026 Open Spaced Repetition），原样收录 npm 包里的 UMD 构建，许可证原文见 `vendor/ts-fsrs-LICENSE.txt`。
