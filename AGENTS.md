# Instructions for Agents

## Mission

このリポジトリは、ｽﾀｯｸﾁｬﾝとその周辺領域に関する学術知識を、検証可能で再利用可能なMarkdown Wikiとして維持する。

対象はｽﾀｯｸﾁｬﾝそのものに限定しない。以下を含む、小型・身体性・キャラクター性・オープン性を備えたコミュニケーションロボットに関連する研究を扱う。

- Human–Robot Interaction
- 音声対話、言語、LLM
- マルチモーダルコミュニケーション
- 身体性、動作、表情
- 感情、人格、愛着、関係形成
- かわいい、kawaii、cuteness、キャラクターデザイン
- 認知・エージェントアーキテクチャ
- 学習、適応、パーソナライズ
- 組み込みAI、TinyML、ロボットハードウェア
- 社会実装、長期利用、受容、離脱
- 評価手法、尺度、研究方法
- 倫理、プライバシー、持続可能性、サービス終了
- オープンソースハードウェア
- Maker文化、ファブリケーション、ユーザーイノベーション
- OSSコミュニティ、共同生産、コミュニティ運営
- 推し活、ファンダム、参加型文化、愛着対象としてのキャラクター

## Source hierarchy

次の順序で一次性を優先する。

1. 査読済み一次研究
2. 査読済みシステマティックレビュー、メタ分析
3. 学位論文、学術書、標準規格
4. プレプリント、テクニカルレポート
5. 大学・研究機関・学会の公式資料
6. 信頼できる二次資料

検索結果の断片、LLM生成文、他のWikiページは一次根拠にしない。

## Verification status

各論文・研究ページには以下のいずれかを付ける。

- `candidate`: 書誌情報のみ。内容未確認
- `abstract_checked`: 抄録を一次情報で確認
- `fulltext_checked`: 本文を確認
- `human_reviewed`: 人間が内容と出典を確認
- `superseded`: 訂正、撤回、正式版への置換等

LLMは `human_reviewed` を付与してはならない。

## Mandatory distinctions

以下を混同しない。

- 著者が主張していること
- データから直接支持されること
- 著者自身が述べた限界
- Wiki編集者の解釈
- ｽﾀｯｸﾁｬﾝへの設計上の示唆

相関を因果として書かない。短期実験を長期的効果へ一般化しない。特定文化圏の結果を普遍化しない。

## Page workflow

新しい文献を採用するときは必ず次を行う。

1. `sources/records/` に正規化書誌レコードを追加または更新
2. `wiki/papers/` に論文ページを作成または更新
3. 関連する `wiki/domains/`、`wiki/topics/`、`wiki/synthesis/` を更新
4. 関連ロボット、研究者、データセット、評価尺度へリンク
5. `wiki/index.md` と `wiki/log.md` を更新
6. 矛盾、未解決問題、再現性上の懸念を `wiki/open-questions.md` に記録
7. `python scripts/validate_wiki.py` を実行

## Citation rules

- DOI、arXiv ID、CRID、PMID、ISBN、学会URL、機関リポジトリ等の恒久識別子を優先する
- 各学術的主張に出典を付ける
- 長い引用を避け、独自要約を記載する
- 論文PDFは再配布可能なライセンスが明示されている場合のみコミットする
- オープンアクセスURLと出版社URLを区別する
- プレプリントと査読版が両方ある場合は関係を明記する

## Taxonomy rules

分類語彙は `schemas/taxonomy.yaml` を正とする。

- 一つの論文に複数の `domains`、`topics`、`methods`、`contexts` を付けてよい
- ディレクトリ構造だけを分類として使わない
- 新しい語彙を追加する場合は、既存語との重複、包含関係、表記揺れを確認する
- `kawaii`、`cuteness`、`baby-schema` は同義語として統合しない
- `oshikatsu` は日本の実践概念として保持し、`fandom`、`participatory-culture`、`parasocial-relationship` 等と関連付ける

## Stack-chan relevance

すべての採用論文で、ｽﾀｯｸﾁｬﾝへの関連性を次のいずれかで評価する。

- `direct`: 現在のｽﾀｯｸﾁｬﾝで直接実装・評価できる
- `design-hypothesis`: 設計仮説として検証価値がある
- `background`: 理論・歴史・比較対象として関連する
- `out-of-scope`: 保持するが直接適用しにくい

根拠を一文以上で記載する。

## Editing discipline

- 既存ページを読んでから編集する
- 同じ概念の別ページを不用意に作らない
- 断定の強さを原著より強くしない
- 矛盾する研究結果は削除せず併記する
- 大規模な分類変更は一つのPull Requestに隔離する
- 自動化は本文を直接mainへ書き込まず、Pull Requestまたは候補レポートを生成する
