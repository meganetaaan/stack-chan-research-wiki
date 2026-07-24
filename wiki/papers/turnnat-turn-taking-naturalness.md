---
type: paper
id: turnnat-turn-taking-naturalness
title: "TurnNat: Automatic Evaluation of Turn-Taking Naturalness in Dyadic Spoken Dialogue"
authors: [Hao Zhang, Thomas Thebaud, Georgi Tinchev, Venkatesh Ravichandran, Laureano Moro-Velázquez]
year: 2026
venue: "arXiv"
publication_status: "preprint"
verification_status: fulltext_checked
domains: [dialogue-and-language, evaluation-and-research-methods]
topics: [turn-taking, spoken-dialogue, voice-activity-detection, reproducibility]
methods: [technical-system]
contexts: []
populations: [adults]
modalities: [speech, audio]
robots: []
doi: null
arxiv_id: "2607.01345"
crid: null
openalex_id: null
semantic_scholar_id: null
publisher_url: null
open_access_url: "https://arxiv.org/abs/2607.01345"
source_license: "arXiv perpetual non-exclusive license"
retrieved_at: 2026-07-24
stackchan_relevance:
  level: high
  applicability: [direct, design-hypothesis]
  components: [speech, audio-input, dialogue]
  rationale:
    - "発話開始・終了付近の自然さを単一指標で比較する枠組みは、ｽﾀｯｸﾁｬﾝの対話回帰テストへ導入できる。"
---

# TurnNat: Automatic Evaluation of Turn-Taking Naturalness in Dyadic Spoken Dialogue

## 一文要約

自然対話から学習した将来発話活動の尤度を使い、遅延、早すぎる開始、過剰な相槌など異種のタイミング異常を共通尺度で評価するプレプリントである。

## 研究課題

人手評価や障害別指標に依存せず、二者音声対話のターンテイキング自然さを自動評価できるか。

## 対象と方法

- 指標: 発話開始・終了周辺のTurn-taking Boundary Unitで将来発話状態の負の対数尤度を集約
- モデル: VAPおよびDualTurn系予測器
- ベンチマーク: 自然な二者対話へ5種の局所的タイミング摂動を加えた対
- 妥当化: 人間による自然さ判断

## 主な結果

TurnNatは、種類の異なるタイミング摂動について自然クリップと摂動クリップを識別した。コードとベンチマークが公開されている。

## 著者の主張

事象ラベルをテスト時に必要とせず、異種のターン失敗を尤度ベースの共通枠組みで比較できるとしている。

## 限界

操作した人間同士の録音で検証しており、実時間の人間–エージェント相互作用や発話内容の妥当性は評価しない。学習データに典型的でない自然な話し方を低評価する可能性がある。

## 再現性・一般化上の注意

プレプリントである。自動スコアは利用者体験やタスク成功の代替ではなく、人手評価との校正を保つ必要がある。

## ｽﾀｯｸﾁｬﾝへの示唆

### 直接適用できる知見

対話ログへ話者別VADを保存し、ソフトウェア更新前後のターン自然さを回帰比較する。

### 設計仮説として検証できる知見

固定無音閾値、VAP、割込み対応方針をTurnNatと人手評定の双方で比較する。

### 適用上の制約

首動作や表情のタイミングは指標外なので、マルチモーダル評価を別に設ける。

## 関連ページ

- [[../topics/turn-taking|ターンテイキング]]
- [[../topics/voice-activity-detection|VAD]]
- [[../datasets/turnnat-benchmark|TurnNat benchmark]]

## 出典

- [arXiv:2607.01345](https://arxiv.org/abs/2607.01345)
- [コードとデータ](https://github.com/TedZhangHao/turn-taking-naturalness)
