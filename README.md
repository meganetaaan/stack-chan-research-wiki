# Stack-chan Research Wiki

ｽﾀｯｸﾁｬﾝを中心に、小型コミュニケーションロボット、Human–Robot Interaction、対話、身体表現、かわいさ、社会実装、オープン開発文化などの学術知識を集約するための公開Wiki雛形です。

このリポジトリは、Markdownを正本とする **LLM Wiki** として設計されています。LLMやエージェントは `AGENTS.md` の規則に従い、出典を保持したまま論文ページ、トピックページ、横断的な総説を更新します。

## 主な特徴

- 論文・研究プロジェクト・ロボット・データセット・評価尺度を別エンティティとして管理
- 複数ファセットによる分類
- ｽﾀｯｸﾁｬﾝへの適用可能性を独立して記録
- DOI、arXiv ID、CRID等による重複防止
- Git diffとPull Requestによる人間レビュー
- MkDocs Materialによる静的公開
- GitHub Actionsによる検証、定期収集、Pages公開
- ChatGPTスケジュール向け運用指示書を同梱

## 最初のセットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/validate_wiki.py
mkdocs serve
```

## 文献候補を収集する

```bash
python scripts/collect_papers.py
```

過去30日間の候補をOpenAlex、arXiv、ACL Anthology、Crossrefから取得し、Semantic Scholarの引用数とCrossref Event DataのReddit言及数を付与します。

`X_BEARER_TOKEN` が設定されている場合は、X上の直近7日間の原投稿数も取得します。

候補は `sources/inbox/` に保存されます。アンカー語、トピック語、掲載先から関連性を評価し、合格候補だけから最大10件のレビューキューを生成します。

## 新しい論文を追加する

```bash
python scripts/new_page.py paper \
  --id doi-10-0000-example \
  --title "Paper title"
```

作成後、`AGENTS.md` と `docs/WORKFLOW.md` に従って一次情報を確認し、トピックページと索引も更新してください。

## ライセンス

- スクリプト、設定ファイル: MIT License
- Wiki本文、独自の図表、独自要約: CC BY 4.0を推奨
- 論文本文や第三者コンテンツの著作権は各権利者に帰属します

詳細は `LICENSES.md` を参照してください。
