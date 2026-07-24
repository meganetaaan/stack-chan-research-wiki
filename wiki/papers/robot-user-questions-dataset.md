---
type: paper
id: robot-user-questions-dataset
title: "What Questions Should Robots Be Able to Answer? A Dataset of User Questions for Explainable Robotics"
authors: [Lennart Wachowiak, Andrew Coles, Gerard Canal, Oya Çeliktutan]
year: 2026
venue: "ACM Transactions on Human-Robot Interaction"
publication_status: "peer-reviewed-journal-article"
verification_status: fulltext_checked
domains: [human-robot-interaction, cognition-and-agent-architecture, evaluation-and-research-methods]
topics: [trust, planning, user-modeling, safety, reproducibility]
methods: [survey, content-analysis]
contexts: []
populations: [adults]
modalities: [text, vision]
robots: []
doi: "10.1145/3832777"
arxiv_id: "2510.16435"
crid: null
openalex_id: null
semantic_scholar_id: null
publisher_url: "https://doi.org/10.1145/3832777"
open_access_url: "https://arxiv.org/abs/2510.16435"
source_license: null
retrieved_at: 2026-07-24
stackchan_relevance:
  level: medium
  applicability: [direct, background]
  components: [dialogue, memory, sensors]
  rationale:
    - "利用者がロボットへ求める説明質問の分類は、ｽﾀｯｸﾁｬﾝの状態・能力・限界を検索可能にする設計へ使える。"
---

# What Questions Should Robots Be Able to Answer? A Dataset of User Questions for Explainable Robotics

## 一文要約

100人からロボットへ尋ねたい1,893問を収集し、説明要求を12大分類・70小分類へ整理したデータセット研究である。

## 研究課題

専門家が想定した説明分類ではなく、利用者が実際にロボットへ尋ねたい質問は何か。

## 対象と方法

- 参加者: 100人
- 刺激: ロボットの動作を示す動画15件と文章7件
- データ: 自由記述1,893問、重要度評定、ロボット経験
- 分析: 反復的な分類により12大分類・70小分類を構築

## 主な結果

実行方法の詳細が21.4%、能力が12.6%、性能が10.7%を占めた。難しい状況や正しい行動に関する質問は少ないが、重要度は高く評価された。経験の有無でも質問傾向が異なった。

## 著者の主張

説明可能ロボティクスの評価と学習に、利用者起点の質問集合を提供するとしている。

## 限界

質問は刺激を見た後の想定であり、実際の失敗時に発せられる質問とは限らない。頻度は重要度と一致せず、分類体系も利用文脈に応じた再検証が必要である。

## 再現性・一般化上の注意

質問へ正しく答える能力を評価した研究ではない。データセットの頻度を、そのまま全利用者の優先順位とみなさない。

## ｽﾀｯｸﾁｬﾝへの示唆

### 直接適用できる知見

能力、現在状態、行動理由、失敗、データ利用について答える「自己説明API」のテスト質問として分類を利用できる。

### 設計仮説として検証できる知見

利用頻度の低い安全・例外質問も、重要度に基づいて回答範囲へ含める。

### 適用上の制約

答えられない場合は生成で埋めず、観測不能・記録なし・権限なしを明示する。

## 関連ページ

- [[../datasets/robot-user-questions|Robot User Questions Dataset]]
- [[../topics/trust|信頼]]
- [[../topics/safety|安全]]

## 出典

- [DOI: 10.1145/3832777](https://doi.org/10.1145/3832777)
- [arXiv:2510.16435](https://arxiv.org/abs/2510.16435)
- [データセット](https://github.com/lwachowiak/xai-questions-dataset)
