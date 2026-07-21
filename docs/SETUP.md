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

Repository secretsへ必要なAPIキーを登録する。初期状態では収集スクリプトはOpenAlex互換APIを想定しているが、運用開始前に利用規約と現在の認証方式を確認する。
