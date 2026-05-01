# ジョブ再作成手順

## 1. 認証とプロジェクト設定

```powershell
# プロジェクト設定
gcloud config set project fx-mxn-watcher-bot

# 現在の状態を確認
gcloud run jobs list --region=asia-northeast1
gcloud scheduler jobs list --location=asia-northeast1
```

## 2. Cloud Run Job が削除されていた場合

```powershell
# ID002_PoC_Mexicoフォルダに移動
cd C:\path\to\ai-market-watchdog-mxn

# Cloud Run Jobを再デプロイ
gcloud run jobs deploy fx-mxn-watcher `
  --source . `
  --region asia-northeast1

# 環境変数（APIキー）を設定
# 実キーは .env (gitignore対象) で管理。下記コマンドのプレースホルダを置き換えて実行する。
# 例: PowerShellなら $env:OPENAI_API_KEY を読み込んで埋め込む
gcloud run jobs update fx-mxn-watcher `
  --set-env-vars OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>" `
  --region asia-northeast1

# テスト実行
gcloud run jobs execute fx-mxn-watcher --region=asia-northeast1
```

## 3. Cloud Scheduler Job が削除されていた場合

```powershell
# プロジェクトIDを取得
$PROJECT_ID = gcloud config get-value project

# サービスアカウントの存在確認（既に作成済みのはず）
gcloud iam service-accounts list

# Cloud Scheduler Jobを再作成（OAuth認証で作成）
gcloud scheduler jobs create http fx-mxn-watcher-schedule `
  --location=asia-northeast1 `
  --schedule="0 * * * *" `
  --time-zone="Asia/Tokyo" `
  --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/fx-mxn-watcher:run" `
  --http-method=POST `
  --oauth-service-account-email="cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com"

# テスト実行
gcloud scheduler jobs run fx-mxn-watcher-schedule --location=asia-northeast1

# 実行履歴を確認
gcloud run jobs executions list --job=fx-mxn-watcher --region=asia-northeast1 --limit=10
```

> **重要**: 必ず `--oauth-service-account-email` を使用してください（`--oidc` ではありません）
> - Cloud Run **Jobs** には **OAuth認証** が必要です
> - OIDCを使用すると 401 UNAUTHENTICATED エラーが発生します

## 4. 両方とも削除されていた場合

上記の「2. Cloud Run Job」と「3. Cloud Scheduler Job」を順番に実行してください。

## 5. 動作確認

```powershell
# Cloud Runのログ確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher" `
  --limit 50 `
  --format "table(timestamp, textPayload)"

# Cloud Schedulerの実行履歴確認
gcloud scheduler jobs describe fx-mxn-watcher-schedule --location=asia-northeast1
```
