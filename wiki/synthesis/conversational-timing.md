---
type: synthesis
id: conversational-timing
title: "会話タイミングの設計と評価"
year: 2026
verification_status: fulltext_checked
---

# 会話タイミングの設計と評価

## 現時点の整理

会話タイミングは単一の無音閾値では捉えきれない。[[../papers/sensor-augmented-vap-turn-taking|Sensor-Augmented VAP]] は頭部運動を加えた予測、[[../papers/personakit-full-duplex-dialogue|PersonaKit]] は人格に応じた割込み方針、[[../papers/turnnat-turn-taking-naturalness|TurnNat]] は異種タイミング失敗の共通評価を扱う。

## ｽﾀｯｸﾁｬﾝでの検証単位

- 入力: 音声活動、発話文脈、利用者の頭部運動
- 方針: 譲歩、保持、橋渡し、上書き
- 評価: 誤割込み、応答遅延、人手自然さ、TurnNat形式の自動スコア

人間同士の録音や仮想エージェントの結果を、実機へそのまま一般化しない。
