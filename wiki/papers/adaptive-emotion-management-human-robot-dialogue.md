---
type: paper
id: adaptive-emotion-management-human-robot-dialogue
title: "Adaptive Emotion Management in Human-robot Dialogue using Online Group Relative Policy Optimization"
authors: [Anna Manaseryan, Casey Kennington]
year: 2026
venue: "SIGDIAL 2026"
publication_status: "peer-reviewed-conference-paper"
verification_status: fulltext_checked
domains: [human-robot-interaction, dialogue-and-language, affect-and-relationships, robot-learning-and-adaptation]
topics: [spoken-dialogue, personality, empathy, behavior-adaptation, preference-learning]
methods: [technical-system, laboratory-experiment]
contexts: []
populations: [adults]
modalities: [speech, face, head-motion, body-motion]
robots: [cozmo]
doi: null
arxiv_id: null
crid: null
openalex_id: null
semantic_scholar_id: null
publisher_url: "https://aclanthology.org/2026.sigdial-1.41/"
open_access_url: "https://aclanthology.org/2026.sigdial-1.41.pdf"
source_license: null
retrieved_at: 2026-07-24
stackchan_relevance:
  level: high
  applicability: [design-hypothesis]
  components: [face, servo-motion, speech, dialogue]
  rationale:
    - "会話中の人間フィードバックで表情・動作の選択方針を更新する構成は、ｽﾀｯｸﾁｬﾝの感情表現実験に移植して検証できる。"
---

# Adaptive Emotion Management in Human-robot Dialogue using Online Group Relative Policy Optimization

## 一文要約

二値の人間フィードバックから会話中に感情方針を更新する仕組みをCozmoへ実装し、小規模実験で感情と発話の整合性が高く知覚される傾向を示した。

## 研究課題

固定された感情分類器ではなく、個々の利用者が適切と感じるロボット感情へオンライン適応できるか。

## 対象と方法

- システム: DeBERTa-v3-base分類器、GRPO、生成動作、Cozmo
- 学習: 1人の指導者が18セッション、542ターンに二値評価
- 評価: 成人10人の被験者内比較。SFTベースラインとGRPOモデルを各約20分使用
- 指標: Godspeed形式16項目、感情固有7項目、自由記述

## 主な結果

- 「感情が発話内容に合う」への同意はGRPOで6/10、ベースラインで0/10だった。
- 人格一貫性の平均はGRPO 4.50、ベースライン3.70だった。
- 快適さは両条件とも10/10が同意した。

## 著者の主張

オンラインGRPOは、実時間で感情行動を適応させる有望な方法だとしている。

## 限界

N=10であり、学習時の指導者は1人だけである。比較は「合成データ対実会話」と「個人適応」の効果を分離できない。順序・慣れ、ASR誤り、動作生成の曖昧さも評価へ影響した。

## 再現性・一般化上の注意

約150回の評価を要し、キーボードによる二値入力は実運用の代理である。文化や個人を越えた一般化は未確認である。

## ｽﾀｯｸﾁｬﾝへの示唆

### 直接適用できる知見

なし。現時点では小規模な設計仮説である。

### 設計仮説として検証できる知見

顔と首動作の候補を少数に限定し、利用者の肯定・否定から選択方針を更新すると、発話との整合感を改善できる可能性がある。

### 適用上の制約

適応前後だけでなく、実会話データで学習した非個人化モデルを第三条件に置く必要がある。

## 関連ページ

- [[../topics/personality|人格]]
- [[../topics/preference-learning|選好学習]]
- [[../topics/behavior-adaptation|行動適応]]

## 出典

- [ACL Anthology](https://aclanthology.org/2026.sigdial-1.41/)
- [オープンアクセスPDF](https://aclanthology.org/2026.sigdial-1.41.pdf)
