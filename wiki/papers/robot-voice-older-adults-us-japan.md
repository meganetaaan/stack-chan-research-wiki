---
type: paper
id: robot-voice-older-adults-us-japan
title: "Finding its Voice: The Influence of Robot Voice on Fit, Social Attributes, and Willingness to Use Among Older Adults in the U.S. and Japan"
authors: [Long-Jing Hsu, Weslie Khoo, Natasha Randall, Waki Kamino, Swapna Joshi, Hiroki Sato, David J. Crandall, Katherine M. Tsui, Selma Šabanović]
year: 2023
venue: "RO-MAN 2023"
publication_status: "peer-reviewed-conference-paper"
verification_status: fulltext_checked
domains: [human-robot-interaction, embodiment-and-expression, applications-and-social-deployment]
topics: [speech-synthesis, older-adults, trust, acceptance]
methods: [survey, laboratory-experiment]
contexts: [home]
populations: [older-adults]
modalities: [speech, audio, face, vision]
robots: [qtrobot]
doi: "10.1109/RO-MAN57019.2023.10309390"
arxiv_id: null
crid: null
openalex_id: null
semantic_scholar_id: null
publisher_url: "https://doi.org/10.1109/RO-MAN57019.2023.10309390"
open_access_url: "https://www.researchgate.net/publication/375618822"
source_license: null
retrieved_at: 2026-07-24
stackchan_relevance:
  level: high
  applicability: [direct, design-hypothesis]
  components: [speech, face, dialogue]
  rationale:
    - "音声ピッチと利用文脈を比較する設計はｽﾀｯｸﾁｬﾝで実装できるが、文化圏と利用者層ごとの評価が必要である。"
---

# Finding its Voice: The Influence of Robot Voice on Fit, Social Attributes, and Willingness to Use Among Older Adults in the U.S. and Japan

## 一文要約

米国と日本の高齢者692人による動画調査で、QT robotの成人・子ども風音声への評価が国によって異なることを示した。

## 研究課題

ロボット音声に帰属される年齢・性別は、音声と外観の適合、社会的属性、推奨を受け入れる意図にどう関係し、その傾向は米国と日本で異なるか。

## 対象と方法

- 参加者: 65歳以上、米国226人・日本466人（注意チェック除外後）
- 刺激: QT robotが活動を勧める短い動画
- 条件: 同じ言語内のTTSをピッチ変更した成人女性、成人男性、子ども風音声のいずれか
- 指標: 音声適合、RoSAS、5種の利用文脈における利用意図

## 主な結果

- 米国では成人女性・男性音声が子ども風音声より外観に適合すると評価された。
- 日本では子ども風音声が男性音声より適合したが、女性音声との差はなく、成人男女間にも差がなかった。
- 米国参加者は多くの温かさ・能力項目と利用意図を日本参加者より高く評価した。
- 社会的属性と利用意図には相関があったが、因果は示さない。

## 著者の主張

音声、文化的文脈、推奨内容を一体として設計し、米国の高齢者向け推奨ロボットでは子ども風音声を避けることを提案している。

## 限界

実機対話ではなく短い動画である。英語版と日本語版は完全に同一のTTS音声でなく、年齢・性別以外の音響差が残る。参加者属性による差も十分分析していない。

## 再現性・一般化上の注意

国差を文化の単一原因へ還元しない。推奨場面、QTの外観、音程操作に依存し、ｽﾀｯｸﾁｬﾝや若年層へ直接一般化できない。

## ｽﾀｯｸﾁｬﾝへの示唆

### 直接適用できる知見

音声プリセットを固定せず、利用者層と言語ごとに外観適合・能力・不快感・利用意図を分けて測る。

### 設計仮説として検証できる知見

高い声がキャラクターらしさを高めても、助言の信頼性を下げる可能性があるため、雑談と推奨で声を比較する。

### 適用上の制約

声の変更が年齢・性別ステレオタイプを強化しないか、聴取しやすさとともに確認する。

## 関連ページ

- [[../robots/qtrobot|QT robot]]
- [[../topics/speech-synthesis|音声合成]]
- [[../topics/older-adults|高齢者]]

## 出典

- [DOI: 10.1109/RO-MAN57019.2023.10309390](https://doi.org/10.1109/RO-MAN57019.2023.10309390)
- [著者公開本文の案内](https://www.researchgate.net/publication/375618822)
