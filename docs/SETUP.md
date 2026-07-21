# Setup

## 1. GitHubへ登録

```bash
git init
git add .
git commit -m "Initial research wiki scaffold"
git branch -M main
git remote add origin <REPOSITORY_URL>
git push -u origin main
```

## 2. Python環境

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. 検証

```bash
python scripts/validate_wiki.py
mkdocs build --strict
```

## 4. GitHub Pages

GitHubのSettingsからPagesのSourceをGitHub Actionsに設定する。`deploy-pages.yml`がmain更新時にサイトを公開する。

## 5. 定期文献収集

Repository secretsへ次の認証情報を登録する。

- `OPENALEX_API_KEY`: OpenAlexのAPIキー
- `OPENALEX_MAILTO`: API利用者の連絡先メールアドレス
- `SEMANTIC_SCHOLAR_API_KEY`: Semantic ScholarのAPIキー（任意）
- `X_BEARER_TOKEN`: X APIのBearer Token（任意、従量課金）

Semantic ScholarはAPIキーがなくても取得を試み、制限された場合は警告を記録して処理を継続する。

XはBearer Tokenがない場合に無効化され、OpenAlex、Semantic Scholar、Crossref Event Dataだけで収集を続ける。

Redditの言及数はCrossref Event Dataから取得するため、Redditの認証情報は不要である。

APIの利用規約と料金は運用開始時と定期的な保守時に確認する。
