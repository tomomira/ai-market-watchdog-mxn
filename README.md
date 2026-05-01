# AI Market Watchdog (MXN/JPY)

メキシコペソ／円（MXN/JPY）レートを24時間監視し、急変動時にAI（OpenAI GPT-4o-mini）による相場解説を生成するBotです。Google Cloud Run Jobs + Cloud Schedulerで毎時自動実行されます。

> 📝 解説記事:[【続編】FXメキシコペソ版・AI市場監視Botで「不労所得の死活監視」を自動化してみた](https://note.com/lively_hippo6176/n/nff0d7792bf5b)

## 主な機能

- **MXN/JPY の24時間監視**（yfinance経由）
- **変動率0.5%以上で自動アラート**（コンソール出力）
- **OpenAI GPT-4o-miniによる相場解説**（日本のFXスワップ投資家向けに最適化）
- **Cloud Run Jobs + Cloud Schedulerで毎時自動実行**

## ファイル構成

```
ai-market-watchdog-mxn/
├── main.py                                 # メインプログラム
├── requirements.txt                        # 依存ライブラリ
├── Dockerfile                              # GCPデプロイ用コンテナ定義
├── .env.example                            # 環境変数テンプレ
├── .gitignore
├── recreation_commands.md                  # ジョブ再作成手順
├── トラブルシューティング.md               # 開発・運用中の問題と解決
├── 進捗_次回作業メモ.md                    # 開発進捗記録
└── ID002_AI_FX市場監視Bot_実装・運用手順書_メキシコペソ版.md  # 詳細手順書
```

## ローカル環境でのテスト

### 1. Python仮想環境の構築（Windows PowerShell）

```powershell
cd C:\path\to\ai-market-watchdog-mxn
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、自分のOpenAI APIキーを設定:

```powershell
$env:OPENAI_API_KEY="sk-your-openai-api-key"
```

### 3. テスト実行

```powershell
python main.py
```

期待される出力:

```
=== AI FX Market Watcher (MXN/JPY) Started ===
[*] Fetching data for MXNJPY=X...
MXN/JPY Rate: 8.97円 (Change: 0.00%)
✅ 異常なし（安定推移）
=== End of Process ===
```

## GCPへのデプロイ

詳細は [recreation_commands.md](./recreation_commands.md) を参照。要点のみ:

```powershell
# Cloud Run Jobsへデプロイ
gcloud run jobs deploy fx-mxn-watcher --source . --region asia-northeast1

# 環境変数設定
gcloud run jobs update fx-mxn-watcher `
  --set-env-vars OPENAI_API_KEY="<YOUR_KEY>" `
  --region asia-northeast1

# Cloud Scheduler（毎時0分実行、OAuth認証）
gcloud scheduler jobs create http fx-mxn-watcher-schedule `
  --location=asia-northeast1 `
  --schedule="0 * * * *" `
  --time-zone="Asia/Tokyo" `
  --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/<PROJECT_ID>/jobs/fx-mxn-watcher:run" `
  --http-method=POST `
  --oauth-service-account-email="cloud-scheduler-runner@<PROJECT_ID>.iam.gserviceaccount.com"
```

> ⚠️ Cloud Run **Jobs** はOAuth認証が必須（OIDC不可）。詳細は [トラブルシューティング.md](./トラブルシューティング.md) 参照。

## 運用コスト

- **GCP**: 無料枠内（月額 ¥0）
- **OpenAI API**: 変動0.5%超のときのみ呼び出し → 月額数十円程度（GPT-4o-mini）

## 関連プロジェクト

- [fx-monitoring-dashboard](https://github.com/tomomira/fx-monitoring-dashboard) — Slack通知統合版（本Botの発展型）

## ライセンス

MIT License — 詳細は [LICENSE](./LICENSE) を参照
