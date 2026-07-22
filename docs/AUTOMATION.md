# Automation design

## 原則

自動化は候補収集、メタデータ正規化、検証、Pull Request生成までを担当する。学術的主張をmainブランチへ直接書き込まない。

## GitHub Actions

- `validate.yml`: PRごとにfrontmatter、分類語彙、Wikiリンク、MkDocsビルドを検証
- `collect-literature.yml`: 週次で過去30日間の文献候補と初動指標を収集しDraft PRを作成
- `deploy-pages.yml`: main更新時にWikiを公開
- `monthly-health-check.yml`: 月次で機械的な問題をIssueへ報告

`collect-literature.yml` を手動実行するときは、`publish_pr=false` を指定すると候補PRを作らずにAPI接続と収集件数を確認できる。

## 候補の優先順位

収集処理は全候補を `sources/inbox/` に残し、最大10件のレビューキューを生成する。

外部APIへの照会量を抑えるため、RedditとXの指標は引用数と検索語一致数による上位20件へ付与する。

次のいずれかを満たす候補を優先する。

- OpenAlexまたはSemantic Scholarの被引用数が1以上
- 過去30日間のCrossref Event Data上のReddit言及が1以上
- X上の原投稿がローリング30日間で3件以上

定量指標を満たさない候補にも3件の関連性確認枠を設ける。

この枠は、公開直後で被引用数がないものの、ｽﾀｯｸﾁｬﾝへの関連性が高い研究を人間またはAgentが救済するために使う。

Xの件数は週次スナップショットを合算した近似値であり、API未設定時は評価から除外する。

Semantic Scholar、Crossref Event Data、Xの障害は警告として記録する。

同じ外部サービスへの後続リクエストはスキップし、OpenAlexによる候補収集を継続する。

Scheduled Actionsは無料の `OPENALEX_API_KEY` を必須とし、設定がなければ収集前に停止する。

定量指標は注目度を示す補助情報であり、研究結果の妥当性やｽﾀｯｸﾁｬﾝへの適用可能性を保証しない。

## ChatGPT scheduled tasks

ChatGPTには二つの役割を持たせる。

1. 新着研究の調査と優先順位付け
2. Wikiの月次ヘルスチェック

ChatGPTはGitHubリポジトリを確認し、既存文献との重複を避ける。自動更新が可能な環境でも、本文変更はPull Requestとして提出する。

具体的なプロンプトは `docs/CHATGPT_TASKS.md` を参照する。
