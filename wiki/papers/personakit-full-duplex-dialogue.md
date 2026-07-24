---
type: paper
id: personakit-full-duplex-dialogue
title: "PersonaKit (PK): A Plug-and-Play Platform for User Testing Diverse Roles in Full-Duplex Dialogue"
authors: [Hyunbae Jeon, Jinho D. Choi]
year: 2026
venue: "SIGDIAL 2026"
publication_status: "peer-reviewed-conference-paper"
verification_status: fulltext_checked
domains: [dialogue-and-language, cognition-and-agent-architecture, evaluation-and-research-methods]
topics: [spoken-dialogue, turn-taking, dialogue-management, personality, reproducibility]
methods: [technical-system, laboratory-experiment]
contexts: [online-community]
populations: [adults, developers]
modalities: [speech, audio, text]
robots: []
doi: null
arxiv_id: "2605.06007"
crid: null
openalex_id: null
semantic_scholar_id: null
publisher_url: "https://aclanthology.org/2026.sigdial-1.42/"
open_access_url: "https://arxiv.org/abs/2605.06007"
source_license: "CC BY 4.0"
retrieved_at: 2026-07-24
stackchan_relevance:
  level: high
  applicability: [direct, design-hypothesis]
  components: [speech, audio-input, dialogue, documentation]
  rationale:
    - "割込み時の譲歩・保持・橋渡し・上書きをJSONで切り替える構成は、ｽﾀｯｸﾁｬﾝの音声対話実験基盤に直接応用できる。"
---

# PersonaKit (PK): A Plug-and-Play Platform for User Testing Diverse Roles in Full-Duplex Dialogue

## 一文要約

割込み処理を人格パラメータとして設定し、対話・調査・ログ出力を一体化したオープンソースの全二重音声対話実験基盤である。

## 研究課題

人格に応じたターンテイキング方針を、リアルタイム音声対話で低い実装コストで比較できるか。

## 対象と方法

- システム: WebRTC、VAD、ASR、LLM、TTS、Flask/Socket.IO
- 方針: Yield、Resume/Hold、Bridge、OverrideをJSONの確率行列で指定
- 予備評価: 5人による被験者内比較。常時譲歩、確率方針、LLM自律選択を8人格で比較
- 出力: 発話、割込み位置、分類、選択方針、アンケートをJSON/CSVで保存

## 主な結果

高エージェンシー人格では非譲歩方針、低エージェンシー・高協調人格では常時譲歩が好まれる傾向があった。ただし記述統計に留まる。

## 著者の主張

人格固有の割込み方針を実験可能な設定項目にし、研究の一連の工程を再利用可能にしたとしている。

## 限界

参加者は5人で推測統計を行っていない。割込み意図のゼロショット分類は人手ラベルで検証されておらず、韻律・視線なども扱わない。

## 再現性・一般化上の注意

コードとログ例は公開されるが、標準構成の割込み応答遅延は1–2秒であり、モデル提供者やネットワークに依存する。

## ｽﾀｯｸﾁｬﾝへの示唆

### 直接適用できる知見

人格、割込み方針、評価質問を設定ファイルへ分離する設計と、割込み前後の音声ログ構造を再利用できる。

### 設計仮説として検証できる知見

「常に発話を譲る」より、キャラクター設定に合わせて保持・橋渡しを混ぜる方が人格一貫性を高める場合がある。

### 適用上の制約

ロボット身体を含む効果ではない。実機では首動作、表情、音声遅延を同時に統制する必要がある。

## 関連ページ

- [[../topics/turn-taking|ターンテイキング]]
- [[../topics/personality|人格]]
- [[../projects/personakit|PersonaKit]]

## 出典

- [ACL Anthology](https://aclanthology.org/2026.sigdial-1.42/)
- [arXiv:2605.06007](https://arxiv.org/abs/2605.06007)
- [ソースコード](https://github.com/HarryJeon24/PersonaStudyKit)
