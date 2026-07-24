---
type: paper
id: sensor-augmented-vap-turn-taking
title: "Sensor-Augmented Voice Activity Projection for Enhancing Turn-Taking Prediction"
authors: [Satoki Hamanaka, Yasue Kishino, Yuiko Tsunomori, Shin Mizutani, Yuya Chiba, Tadashi Okoshi, Jin Nakazawa]
year: 2026
venue: "SIGDIAL 2026"
publication_status: "peer-reviewed-conference-paper"
verification_status: fulltext_checked
domains: [dialogue-and-language, multimodal-interaction, hardware-and-embedded-intelligence]
topics: [turn-taking, voice-activity-detection, head-motion, multimodal-fusion]
methods: [technical-system, laboratory-experiment]
contexts: []
populations: [adults]
modalities: [speech, audio, head-motion]
robots: []
doi: null
arxiv_id: null
crid: null
openalex_id: null
semantic_scholar_id: null
publisher_url: "https://aclanthology.org/2026.sigdial-1.12/"
open_access_url: "https://aclanthology.org/2026.sigdial-1.12.pdf"
source_license: null
retrieved_at: 2026-07-24
stackchan_relevance:
  level: medium
  applicability: [design-hypothesis]
  components: [audio-input, dialogue, sensors]
  rationale:
    - "頭部運動を音声へ統合する発想はターン予測に関係するが、本研究は人間同士のイヤホンIMU計測であり、実機への転移確認が必要である。"
---

# Sensor-Augmented Voice Activity Projection for Enhancing Turn-Taking Prediction

## 一文要約

音声VAPへイヤホンの加速度信号を融合し、小規模な日本語対話データで発話交替検出の適合率とweighted F1を改善した。

## 研究課題

カメラに依存せず、頭部運動を使って将来の発話活動とターン交替を予測できるか。

## 対象と方法

- 参加者: 日本の大学生9人
- データ: 反対意見を持つ2人による10–15分の対話12件
- 計測: ピンマイクとAirPods 3のIMU。加速度のみ使用
- 評価: 3分割交差検証、話者独立・話者依存条件、音声のみVAPとの比較

## 主な結果

- weighted F1は音声のみ0.520から、話者独立0.622、話者依存0.653へ上昇した。
- 話者独立条件では適合率が0.420から0.710へ上がる一方、再現率とbalanced accuracyは低下した。
- IMUをゼロ化したアブレーションでも改善があり、融合層によるドメイン適応とIMU固有効果の双方が示唆された。

## 著者の主張

耳装着IMUの頭部運動手がかりは、誤った割込みを抑える方向で発話交替予測を補強するとしている。

## 限界

加速度のみを使用し、視覚など他の非言語モダリティと比較していない。データは少数の日本人大学生に限られ、重複発話区間を評価から除外した。

## 再現性・一般化上の注意

人間同士の議論対話の結果であり、人間–ロボット対話、日常会話、異なる年齢・文化には未検証である。

## ｽﾀｯｸﾁｬﾝへの示唆

### 直接適用できる知見

なし。センサ配置と対話相手が異なる。

### 設計仮説として検証できる知見

利用者側の頭部運動をカメラまたはウェアラブルから得られる場合、VADだけより早い発話交替予測が可能か検証できる。

### 適用上の制約

weighted F1だけでなく、割込みを減らす適合率と応答機会を失う再現率のトレードオフを測る必要がある。

## 関連ページ

- [[../topics/turn-taking|ターンテイキング]]
- [[../topics/head-motion|頭部運動]]
- [[../topics/multimodal-fusion|マルチモーダル融合]]

## 出典

- [ACL Anthology](https://aclanthology.org/2026.sigdial-1.12/)
- [オープンアクセスPDF](https://aclanthology.org/2026.sigdial-1.12.pdf)
