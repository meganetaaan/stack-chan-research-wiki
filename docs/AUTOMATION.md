# Automation design

## 原則

自動化は候補収集、メタデータ正規化、検証、Pull Request生成までを担当する。学術的主張をmainブランチへ直接書き込まない。

## GitHub Actions

- `validate.yml`: PRごとにfrontmatter、分類語彙、Wikiリンク、MkDocsビルドを検証
- `collect-literature.yml`: 週次で文献候補を収集しPRを作成
- `deploy-pages.yml`: main更新時にWikiを公開
- `monthly-health-check.yml`: 月次で機械的な問題をIssueへ報告

## ChatGPT scheduled tasks

ChatGPTには二つの役割を持たせる。

1. 新着研究の調査と優先順位付け
2. Wikiの月次ヘルスチェック

ChatGPTはGitHubリポジトリを確認し、既存文献との重複を避ける。自動更新が可能な環境でも、本文変更はPull Requestとして提出する。

具体的なプロンプトは `docs/CHATGPT_TASKS.md` を参照する。
