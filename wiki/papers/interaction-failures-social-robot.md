---
type: paper
id: interaction-failures-social-robot
title: "We All Make Mistakes: Terminal, Non-critical, Recoverable, and Favorable Interaction Failures Between People and a Social Robot"
authors: [Waki Kamino, Natasha Randall, Tanya Saga, Long-Jing Hsu, Katherine M. Tsui, Selma Šabanović, Shinichi Nagata]
year: 2023
venue: "RO-MAN 2023"
publication_status: "peer-reviewed-conference-paper"
verification_status: fulltext_checked
domains: [human-robot-interaction, applications-and-social-deployment, evaluation-and-research-methods]
topics: [dialogue-repair, trust, older-adults, safety]
methods: [laboratory-experiment, case-study, content-analysis]
contexts: []
populations: [older-adults]
modalities: [speech, audio, face, body-motion]
robots: [qtrobot]
doi: "10.1109/RO-MAN57019.2023.10309418"
arxiv_id: null
crid: null
openalex_id: null
semantic_scholar_id: null
publisher_url: "https://doi.org/10.1109/RO-MAN57019.2023.10309418"
open_access_url: "https://www.researchgate.net/publication/375618966"
source_license: null
retrieved_at: 2026-07-24
stackchan_relevance:
  level: high
  applicability: [direct, design-hypothesis]
  components: [speech, dialogue, face, servo-motion]
  rationale:
    - "小型社会ロボットの誤りを停止・修復可能・非重大・好意的に分類する観点は、ｽﾀｯｸﾁｬﾝの対話ログ設計と復旧方針へ直接使える。"
---

# We All Make Mistakes: Terminal, Non-critical, Recoverable, and Favorable Interaction Failures Between People and a Social Robot

## 一文要約

日本の高齢者12人とQT robotの短時間対話を質的分析し、停止に至る失敗だけでなく、修復可能、非重大、好意的に作用する失敗を記述した。

## 研究課題

人と社会ロボットの相互作用で、誰がどのような誤りを起こし、その場の文脈が結果の重大さをどう変えるか。

## 対象と方法

- 参加者: 茨城県在住の日本人高齢者12人（66–85歳、中央値74歳）
- ロボット: QT robotをWizard-of-Ozで操作
- 手続き: 4つの短い活動、初回約30分
- 分析: 映像・音声から失敗を抽出し、厚い記述とテーマ分析を実施

## 主な結果

- 121件の失敗のうち、停止4%（5件）、修復可能33%（40件）、非重大32%（39件）、好意的31%（37件）だった。
- 起点はロボット79%（95件）、人間21%（26件）だった。
- 笑いや周囲の支援などにより、一部の失敗は親しみやユーモアの機会になった。

## 著者の主張

失敗を一律に排除対象とせず、人の誤り、文化規範、同席者、回復行動を含む相互作用として扱う必要があるとしている。

## 限界

初対面の約30分に限られ、研究者が第三者として失敗を判定した。参加者の主観的な失敗認識は面接していない。日本の高齢者だけの雪だるま式標本である。

## 再現性・一般化上の注意

「好意的な失敗」を意図的に増やせば好感度が上がる、とは示していない。反復すると信頼低下へ変わる可能性がある。

## ｽﾀｯｸﾁｬﾝへの示唆

### 直接適用できる知見

ログへ起点、重大度、修復、利用者反応、同席者の介入を分けて記録する。

### 設計仮説として検証できる知見

聞き返し、ゆっくりした再発話、会話終了の明示、笑い・注意逸脱の検出が復旧を助けるか評価する。

### 適用上の制約

愛嬌として受け取られる失敗と、安全・プライバシー・継続利用を損なう失敗を混同しない。

## 関連ページ

- [[../robots/qtrobot|QT robot]]
- [[../topics/dialogue-repair|対話修復]]
- [[../topics/older-adults|高齢者]]

## 出典

- [DOI: 10.1109/RO-MAN57019.2023.10309418](https://doi.org/10.1109/RO-MAN57019.2023.10309418)
- [著者公開本文の案内](https://www.researchgate.net/publication/375618966)
