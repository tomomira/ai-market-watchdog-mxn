# AI FX市場監視Bot 実装・運用手順書（メキシコペソ版）

**作業場所**: `C:\path\to\ai-market-watchdog-mxn`

### 📂 フォルダ構成
作業フォルダ（ID002_PoC_Mexico）の中身は、最終的に以下のようになります。

```text
ID002_PoC_Mexico/
├── venv/                            # [自動生成] Python仮想環境フォルダ
├── main.py                          # プログラム本体 (Python) - メキシコペソ対応
├── requirements.txt                 # 必要なライブラリ一覧
├── Dockerfile                       # コンテナ設計図
├── トラブルシューティング.md         # 問題解決ガイド（推奨）
├── recreation_commands.md           # ジョブ復旧手順（推奨）
└── 進捗_次回作業メモ.md              # 進捗管理ファイル（任意）
```

> **推奨**: `トラブルシューティング.md` は実際に発生した問題と解決方法を記録しているため、問題発生時の参照用として作成を推奨します。

---

## 📚 用語解説 (Glossary)
本手順書で使用する専門用語の解説です。

| 用語 | 解説 |
| :--- | :--- |
| **Python (パイソン)** | 今回使用するプログラミング言語。AIやデータ分析に強く、初心者でも扱いやすい。 |
| **仮想環境 (venv)** | プロジェクト専用の隔離された作業部屋。システムのPython環境を汚さずに開発できる。 |
| **ライブラリ (Library)** | 便利な機能をまとめた道具箱。今回は `yfinance`(為替レート取得) と `pandas`(データ分析) を使用。 |
| **Docker (ドッカー)** | アプリを「コンテナ」という箱に詰め込む技術。どのPCやクラウドでも同じように動かせる。 |
| **Dockerfile** | Dockerイメージ（コンテナの金型）を作るための設計図。 |
| **Google Cloud (GCP)** | Googleが提供するクラウドサービス群。今回はサーバーやスケジューラーを使用。 |
| **Cloud Run Jobs** | プログラムを「処理が終わるまで実行する」サービス。常時起動ではなく、必要な時だけ動くため安い。 |
| **Cloud Scheduler** | クラウド上の目覚まし時計。決まった時間にCloud Runを叩き起こして実行させる。 |
| **gcloud CLI** | 自分のPCからコマンドでGoogle Cloudを操作するためのツール。 |
| **API (エーピーアイ)** | ソフトウェア同士が会話するための窓口。今回はYahoo Financeから為替データを貰うために使用。 |
| **デプロイ (Deploy)** | 作成したプログラムを本番環境（今回はクラウド）に配置して、使える状態にすること。 |
| **リージョン (Region)** | クラウドのデータセンターの場所。`asia-northeast1` は東京リージョンを指す。 |
| **MXN/JPY** | メキシコペソ/円の為替レート。1ペソが何円かを示す。数値が上がるとペソ高（円安）、下がるとペソ安（円高）。 |
| **スワップ投資** | 高金利通貨を保有し続けることで金利差益（スワップポイント）を得る投資手法。 |

---

## Part 1: 実装編 (ローカル環境での開発)

まずはローカルのWindows環境でプログラムを作成し、動作を確認します。

### 1. 作業ディレクトリへの移動
PowerShellで対象のディレクトリへ移動します。

```powershell
cd C:\path\to\ai-market-watchdog-mxn
```

### 2. 仮想環境 (venv) の構築
プロジェクト専用のPython環境を作成します。

```powershell
# 仮想環境 'venv' を作成
python -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1
```
> **Check**: コマンドプロンプトの行頭に `(venv)` と表示されれば成功です。

> **重要**: この作業は必ず **Windows PowerShell** で実行してください。WSL (Linux環境) で実行すると、`venv/bin/` というLinux形式のフォルダ構成になり、Windows上で `.\venv\Scripts\Activate.ps1` が見つからないエラーが発生します。

### 3. ライブラリのインストール
必要なライブラリをインストールします。

```powershell
pip install yfinance pandas openai
```

### 4. プログラムの作成
以下のコードを `main.py` という名前で保存してください。

```python:main.py
import yfinance as yf
import pandas as pd
from openai import OpenAI
import os

# --- 設定 (Configuration) ---
TARGET_TICKER = "MXNJPY=X"      # 監視対象: MXN/JPY (メキシコペソ/円)
ALERT_THRESHOLD = 0.5           # 変動率アラート閾値 (%)

# OpenAI設定 (環境変数からキーを取得)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def fetch_market_data(ticker_symbol):
    """Yahoo Financeからデータを取得する"""
    print(f"[*] Fetching data for {ticker_symbol}...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="5d", interval="1h")
        return df
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

def get_ai_analysis(change_rate, price):
    """AIに相場解説を依頼する"""
    print("[*] Asking AI for analysis...")
    direction = "急騰（ペソ高・円安）" if change_rate > 0 else "急落（ペソ安・円高）"

    prompt = f"""
    あなたは新興国通貨FXで20年の経験を持つベテラン機関投資家です。
    MXN/JPY（メキシコペソ/円）が直近1時間で {change_rate:.2f}% {direction}しました。
    現在のレートは {price:.2f}円 です。

    この値動きに対し、以下の観点から短いコメント（150文字以内）を
    「だ・である」調で、冷静かつ客観的に作成してください：
    - 日本のFXスワップ投資家への影響（円でペソを買うポジション保有者）
    - 市場センチメント
    - 短期的な見通し
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたはプロのFXアナリストで、特に新興国通貨とスワップ投資に精通しています。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI分析エラー: {e}"

def analyze_market(df):
    if df is None or len(df) == 0: return

    latest = df.iloc[-1]
    open_price = latest['Open']
    close_price = latest['Close']
    change_rate = ((close_price - open_price) / open_price) * 100

    print(f"MXN/JPY Rate: {close_price:.2f}円 (Change: {change_rate:.2f}%)")

    if abs(change_rate) >= ALERT_THRESHOLD:
        if change_rate > 0:
            direction = "急騰（ペソ高）"
            impact = "✨ スワップ投資家：含み益拡大の可能性"
        else:
            direction = "急落（ペソ安）"
            impact = "⚠️ スワップ投資家：含み損拡大の可能性"

        print(f"🚨 ALERT: {TARGET_TICKER} が {direction} しました！")
        print(f"{impact}")

        # AI分析を実行
        ai_comment = get_ai_analysis(change_rate, close_price)
        print(f"\n🤖 AIアナリストのコメント:\n{ai_comment}")
    else:
        print("✅ 異常なし（安定推移）")

if __name__ == "__main__":
    print("=== AI FX Market Watcher (MXN/JPY) Started ===")
    df = fetch_market_data(TARGET_TICKER)
    analyze_market(df)
    print("=== End of Process ===")
```

### 5. OpenAI APIキーの設定（ローカルテスト用）

AI機能を使うには「OpenAI APIキー」が必要です。

#### Step 1: APIキーの取得
1.  [OpenAI Platform](https://platform.openai.com/signup) にアクセスし、アカウントを作成（またはログイン）します。
2.  画面右上の **[Settings] (歯車アイコン)** または **[Dashboard]** をクリックします。
3.  左メニュー、または「User」セクション内にある **[API keys]** をクリックします。
4.  **[+ Create new secret key]** をクリックします。
    *   Name: `FXMarketWatcher` など任意の名前を入力。
    *   Permissions: `All` (デフォルト) でOK。
5.  表示された `sk-` から始まる文字列を**必ずコピーしてメモ帳などに保存してください**。（※一度閉じると二度と表示されません！）

#### Step 2: 環境変数の設定（ローカル - PowerShell）
ローカルでテストする際は、一時的に環境変数を設定します。

```powershell
# PowerShellで環境変数を設定（セッション内でのみ有効）
$env:OPENAI_API_KEY="sk-..."
```
※ `sk-...` の部分は、先ほどコピーしたあなたの実際のAPIキーに置き換えて実行してください。

### 6. 動作確認
スクリプトを実行し、エラーが出ないことを確認します。

```powershell
python main.py
```

以下のような出力が表示されれば成功です：

```text
=== AI FX Market Watcher (MXN/JPY) Started ===
[*] Fetching data for MXNJPY=X...
MXN/JPY Rate: 8.74円 (Change: 0.00%)
✅ 異常なし（安定推移）
=== End of Process ===
```

> **✅ Check**: エラーなく実行され、MXN/JPYレートが表示されればOKです。

---

## Part 2: 運用編 (クラウドへのデプロイ)

ここからは、作成したプログラムをGoogle Cloud上で動かすための準備を行います。

### 7. 依存関係ファイルの作成
Dockerイメージを作成するために、必要なライブラリをリスト化した `requirements.txt` を作成します。

```text:requirements.txt
yfinance
pandas
openai
```
※ファイル名 `requirements.txt` で保存してください。

### 8. Dockerfile の作成
コンテナの設計図となる `Dockerfile` を作成します。

```dockerfile:Dockerfile
# Pythonの軽量イメージを使用（3.11以上が必須）
FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# バッファリングを無効化（ログを即時出力させるため）
ENV PYTHONUNBUFFERED=1

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードのコピー
COPY main.py .

# アプリケーションの実行
CMD ["python", "main.py"]
```

> **重要**: yfinanceライブラリはPython 3.10以上を必要とするため、必ず `python:3.11-slim` 以上を指定してください。

### 9. Google Cloud へのデプロイ (前提)

Google Cloud を初めて使う方向けに、デプロイに必要な準備をステップバイステップで解説します。

#### Step 1: Google Cloud アカウントと請求先アカウントの作成
1.  [Google Cloud のトップページ](https://cloud.google.com/?hl=ja) にアクセスします。
2.  「無料で開始」ボタンをクリックし、Googleアカウントでログインして登録を進めます。
3.  **請求先アカウントの作成**:
    *   画面の指示に従い、国、住所、クレジットカード情報などを入力します。
    *   **重要**: ここでカード情報を登録しても、**無料枠の範囲内であれば課金されることはありません。** Google Cloudを利用するための本人確認（会員証発行）の手続きとお考えください。
    *   「無料トライアル」が適用され、$300分のクレジットが付与される場合が多いですが、今回のBotはそれを使わずとも無料枠内で動作します。

#### Step 2: プロジェクトの作成
1.  [コンソール画面](https://console.cloud.google.com/) の左上にあるプロジェクト選択プルダウンをクリックします。
2.  「新しいプロジェクト」をクリックします。
3.  **プロジェクト名**: `fx-mxn-watcher-bot` （任意の名前でOK）と入力し、「作成」をクリックします。
4.  通知ベルアイコンから、作成したプロジェクトを選択（切り替え）してください。

#### Step 3: 必要なAPIの有効化 (超重要)
クラウド機能を使うための「スイッチ」をオンにします。コンソール上部の検索バーに以下の名前を入力して検索し、「有効にする」をクリックしてください。

> **注意**: 「請求先アカウントが必要です」と表示された場合は、**「課金を有効にする」を選択して進めてください。**
> Google Cloudの仕様上、無料枠を利用する場合でもクレジットカード等の登録（請求先アカウントの紐付け）が必須となっています。
> 今回のBot構成であればCloud Runの無料枠内に十分に収まるため、実際に料金が引き落とされることはありません。

1.  **Cloud Run Admin API**
2.  **Artifact Registry API**
3.  **Cloud Build API**
4.  **Cloud Scheduler API**

#### Step 4: Google Cloud CLI (コマンドツール) の導入
手元のパソコンからGoogle Cloudを操作するためのツールをインストールします。

1.  [Google Cloud CLI のインストールページ](https://cloud.google.com/sdk/docs/install?hl=ja) から、Windows用のインストーラーをダウンロード・実行します。
2.  インストールが完了したら、新しい PowerShell ウィンドウを開きます。
3.  以下のコマンドを実行して、ログイン設定を行います。

```powershell
# ブラウザが開き、Googleアカウントのログイン画面が表示されます
gcloud auth login

# 先ほど作成したプロジェクトを選択します
gcloud config set project [PROJECT_ID]
```
※ `[PROJECT_ID]` は、コンソールのダッシュボードに表示されている「プロジェクト ID」を入力してください（例: `fx-mxn-watcher-bot-12345`）。

ここまで完了すれば、準備OKです！次の手順へ進んでください。

### 10. Cloud Run Jobs へのデプロイ
以下のコマンドを **PowerShell** で実行し、クラウド上にプログラムを配置します。

> **Check**: カレントディレクトリの確認
> 実行する前に、現在 **`Dockerfile` や `main.py` があるフォルダ（ID002_PoC_Mexico）の中にいること** を確認してください。
> ```powershell
> Get-ChildItem  # main.py, Dockerfileなどが表示されればOK
> ```

```powershell
# Cloud Run Jobs としてデプロイ
gcloud run jobs deploy fx-mxn-watcher `
  --source . `
  --region asia-northeast1
```
*   `--source .` の `.` は「現在のフォルダ」を意味します。このフォルダの中身一式がクラウドへアップロードされます。
*   途中、`Allow unauthenticated invocations?` (未認証の呼び出しを許可しますか？) と聞かれた場合は `N` (No) を推奨します。
*   初回はArtifact Registry等のAPI有効化を求められる場合があります。`y` で進めてください。

### 11. OpenAI APIキーの設定（Cloud Run）

Cloud Runの環境変数にOpenAI APIキーを設定します。

```powershell
gcloud run jobs update fx-mxn-watcher `
  --set-env-vars OPENAI_API_KEY="sk-..." `
  --region asia-northeast1
```
※ `sk-...` の部分は、先ほどコピーしたあなたの実際のAPIキーに置き換えて実行してください。

### 12. 定期実行の設定 (Cloud Scheduler)
1時間に1回実行するようにスケジュール設定します。

#### Step 1: サービスアカウントの作成と権限設定
Cloud SchedulerがCloud Run Jobsを実行するための専用アカウントを作成します。

```powershell
# サービスアカウントを作成
gcloud iam service-accounts create cloud-scheduler-runner `
  --display-name="Cloud Scheduler Runner"

# プロジェクトIDを取得
$PROJECT_ID = gcloud config get-value project

# Cloud Run Jobsを実行する権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" `
  --role="roles/run.developer"

# Cloud Run Job個別への権限付与
gcloud run jobs add-iam-policy-binding fx-mxn-watcher `
  --region=asia-northeast1 `
  --member="serviceAccount:cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com" `
  --role="roles/run.invoker"
```

> **重要**:
> - Cloud Run **Jobs**（バッチ実行）には、OAuth認証が必要です（後述）
> - `roles/run.developer` は Cloud Run API へのアクセス権限を含みます
> - 従来の `Compute Engine default service account` は新しいプロジェクトでは存在しない場合があります

#### Step 2: Cloud Scheduler ジョブの作成

**方法A: コマンドラインでの設定（推奨）**

```powershell
gcloud scheduler jobs create http fx-mxn-watcher-schedule `
  --location=asia-northeast1 `
  --schedule="0 * * * *" `
  --time-zone="Asia/Tokyo" `
  --uri="https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/fx-mxn-watcher:run" `
  --http-method=POST `
  --oauth-service-account-email="cloud-scheduler-runner@${PROJECT_ID}.iam.gserviceaccount.com"
```

> **重要**: `--oauth-service-account-email` を使用してください（`--oidc-service-account-email` ではありません）
> - **OAuth**: API呼び出しの認可に使用（Cloud Run Jobs API用）
> - **OIDC**: ID認証に使用（Cloud Run Servicesで一般的）
> - Cloud Run **Jobs** を呼び出す場合は必ず **OAuth** を使用します

**方法B: Google Cloud Console (Web画面) での設定**
1.  ブラウザで [Cloud Scheduler](https://console.cloud.google.com/cloudscheduler) を開く。
2.  「ジョブの作成」をクリック。
3.  以下の内容を設定します：
    *   **名前**: `fx-mxn-watcher-schedule`
    *   **リージョン**: `asia-northeast1`
    *   **頻度**: `0 * * * *` (毎時0分)
    *   **タイムゾーン**: `Asia/Tokyo` (日本標準時 JST)
    *   **ターゲットタイプ**: `HTTP`
    *   **URL**:
        ```
        https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/[YOUR_PROJECT_ID]/jobs/fx-mxn-watcher:run
        ```
        ※ `[YOUR_PROJECT_ID]` はご自身のプロジェクトIDに置き換えてください（例: `fx-mxn-watcher-bot`）。
    *   **HTTPメソッド**: `POST`
    *   **Authヘッダー**: `OAuth トークンを追加` を選択 ⭐
    *   **サービスアカウント**: `cloud-scheduler-runner@[YOUR_PROJECT_ID].iam.gserviceaccount.com` を選択

4.  「作成」をクリック。

> **注意**: 必ず「OAuth トークン」を選択してください。「OIDC トークン」ではCloud Run Jobsが動作しません。

#### Step 3: 動作確認

**手動テスト実行**:
```powershell
# 手動でスケジューラーをトリガー
gcloud scheduler jobs run fx-mxn-watcher-schedule --location=asia-northeast1
```

**実行履歴の確認**:
```powershell
# Cloud Run Jobの実行履歴を確認
gcloud run jobs executions list --job=fx-mxn-watcher --region=asia-northeast1 --limit=10
```

以下のように表示されれば成功です：
```
   JOB             EXECUTION             REGION           RUN BY
✔  fx-mxn-watcher  fx-mxn-watcher-xxxxx  asia-northeast1  cloud-scheduler-runner@fx-mxn-watcher-bot.iam.gserviceaccount.com
```

> **時刻表示について**: 実行履歴の時刻は **UTC（協定世界時）** で表示されます。日本時間（JST）は UTC + 9時間 です。
> - 例: `2026-01-05 00:00:00 UTC` → 日本時間 `2026-01-05 09:00:00 JST`

**ログの確認**:
```powershell
# 最新の実行ログを確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher" `
  --limit 20 `
  --format "table(timestamp, textPayload)"
```

`=== AI FX Market Watcher (MXN/JPY) Started ===` と `=== End of Process ===` が表示されれば正常動作です。

---

## 13. 実行結果の確認方法
設定したBotが正しく動いているかは、Cloud Runのログ画面で確認します。

1.  Google Cloud Console で **[Cloud Run]** を開きます。
2.  ジョブ一覧から `fx-mxn-watcher` をクリックします。
3.  **[ログ]** タブをクリックします。
4.  以下のように、Pythonプログラムの出力が表示されていれば成功です。
    ```text
    [INFO] Fetching data for MXNJPY=X...
    [INFO] MXN/JPY Rate: 8.74円 (Change: 0.00%)
    [INFO] ✅ 異常なし（安定推移）
    ```

> **Tip**: Cloud Scheduler の画面で、作成したジョブの行にある「3点リーダー(...)」→「強制実行」をクリックすると、今すぐテスト実行させてログを確認できます。

---

## 14. 料金についての補足 (安心材料)
今回の構成であれば、Google Cloudの無料枠（Free Tier）の範囲内に収まるため、基本的に課金は発生しません。

| サービス | 無料枠 (月間) | 今回のBot使用量 (概算) | 判定 |
| :--- | :--- | :--- | :--- |
| **Cloud Run** | 200万リクエスト / 18万vCPU秒 | 約744回 / 約3,720秒 | **余裕で無料** (枠の約2%) |
| **Cloud Scheduler** | 3ジョブ | 1ジョブ | **無料** |
| **Artifact Registry** | 0.5 GB (ストレージ) | 約0.1〜0.2 GB | **無料** |
| **Cloud Build** | 120分 (ビルド時間) | 数分 (デプロイ時のみ) | **無料** |
| **OpenAI API** | 従量課金 | GPT-4o-mini: 約$0.0001/リクエスト | **月数円程度** |

> **注意**:
> - Artifact Registry（コンテナ画像の保管場所）は、デプロイを数十回繰り返すと古いデータが溜まり、0.5GBを超える可能性があります（超過しても月額数円〜数十円程度）。
> - OpenAI APIは従量課金ですが、GPT-4o-miniは非常に安価（1000トークンあたり$0.00015）で、月744回実行しても数円程度です。

---

## 15. カスタマイズアイデア

### 監視閾値の調整
メキシコペソはボラティリティが高いため、閾値を調整することで誤報を減らせます。

```python
ALERT_THRESHOLD = 0.5  # デフォルト
ALERT_THRESHOLD = 1.0  # より大きな変動のみ検知
ALERT_THRESHOLD = 0.3  # 小さな変動も検知
```

### LINE通知の追加
LINE Notifyを使えば、急変動をスマホに即座に通知できます。

### 複数通貨ペアの監視
ドル円（JPY=X）やトルコリラ（TRY=X）なども同時に監視可能です。

---

## 運用終了時 (ローカル)
ローカルでの作業を終える際は、仮想環境から抜けます。

```powershell
deactivate
```

---

## トラブルシューティング

問題が発生した場合は、以下のドキュメントを参照してください：

📝 **[トラブルシューティング.md](./トラブルシューティング.md)**

このドキュメントには、実際の開発・デプロイ中に発生した以下の問題と解決方法が記載されています：

1. **Python バージョン互換性エラー** - yfinanceとPython 3.9の非互換問題
2. **venv フォルダ構成の問題** - Windows vs Linux環境の違い
3. **Cloud Scheduler 権限エラー** - PERMISSION_DENIED (403)の解決
4. **環境変数の設定エラー** - PowerShellでの正しい構文
5. **Cloud Run Job の削除と復旧** - 誤削除時の復旧手順
6. **複数プロジェクトの混在** - プロジェクト切り替えの注意点

問題が発生した際は、まずこのドキュメントを確認してください。

---

## 16. 運用時の確認コマンド一覧

デプロイ後の運用で使用する主要なコマンドをまとめました。

### 📊 状態確認コマンド

#### プロジェクト設定の確認
```powershell
# 現在のプロジェクトを確認
gcloud config get-value project

# プロジェクトを切り替え
gcloud config set project fx-mxn-watcher-bot
```

#### Cloud Run Jobの状態確認
```powershell
# デプロイされているJobの一覧
gcloud run jobs list --region=asia-northeast1

# 特定Jobの詳細情報
gcloud run jobs describe fx-mxn-watcher --region=asia-northeast1

# 実行履歴の確認（最新10件）
gcloud run jobs executions list --job=fx-mxn-watcher --region=asia-northeast1 --limit=10
```

#### Cloud Schedulerの状態確認
```powershell
# Schedulerジョブの一覧
gcloud scheduler jobs list --location=asia-northeast1

# 特定Schedulerジョブの詳細情報
gcloud scheduler jobs describe fx-mxn-watcher-schedule --location=asia-northeast1
```

**確認ポイント**:
- `state: ENABLED` であること
- `schedule: 0 * * * *` であること
- `timeZone: Asia/Tokyo` であること
- `oauthToken` が設定されていること（`oidcToken` ではない）

### 📝 ログ確認コマンド

#### Cloud Run Jobのログ確認
```powershell
# 最新30件のログを表示
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher" `
  --limit 30 `
  --format "table(timestamp, textPayload)" `
  --project fx-mxn-watcher-bot

# 特定の実行のログのみ表示
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher AND labels.execution_name=fx-mxn-watcher-xxxxx" `
  --limit 20 `
  --format "table(timestamp, textPayload)" `
  --project fx-mxn-watcher-bot

# 過去24時間のログを確認（PowerShellの場合）
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-ddTHH:mm:ssZ")
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher AND timestamp>='$yesterday'" `
  --limit 100 `
  --format "table(timestamp, textPayload)" `
  --project fx-mxn-watcher-bot
```

#### Cloud Schedulerのログ確認
```powershell
# Schedulerの実行履歴を確認
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_name=fx-mxn-watcher-schedule" `
  --limit 20 `
  --project fx-mxn-watcher-bot

# エラーのみフィルタリング
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_name=fx-mxn-watcher-schedule AND severity>=ERROR" `
  --limit 20 `
  --project fx-mxn-watcher-bot
```

### 🔧 運用管理コマンド

#### Cloud Schedulerの手動実行
```powershell
# Schedulerを今すぐトリガー
gcloud scheduler jobs run fx-mxn-watcher-schedule --location=asia-northeast1
```

#### Cloud Schedulerの一時停止・再開
```powershell
# 一時停止
gcloud scheduler jobs pause fx-mxn-watcher-schedule --location=asia-northeast1

# 再開
gcloud scheduler jobs resume fx-mxn-watcher-schedule --location=asia-northeast1
```

#### 環境変数（APIキー）の更新
```powershell
# OpenAI APIキーを更新
gcloud run jobs update fx-mxn-watcher `
  --set-env-vars OPENAI_API_KEY="sk-proj-新しいキー" `
  --region asia-northeast1
```

#### 再デプロイ（コード更新時）
```powershell
# フォルダに移動
cd C:\path\to\ai-market-watchdog-mxn

# 再デプロイ
gcloud run jobs deploy fx-mxn-watcher `
  --source . `
  --region asia-northeast1
```

### 🚨 トラブルシューティングコマンド

#### 認証エラーの確認
```powershell
# Schedulerの設定確認（oauthToken が設定されているか）
gcloud scheduler jobs describe fx-mxn-watcher-schedule --location=asia-northeast1 | Select-String -Pattern "oauth|oidc"

# サービスアカウントの確認
gcloud iam service-accounts list

# 権限の確認
gcloud projects get-iam-policy fx-mxn-watcher-bot `
  --flatten="bindings[].members" `
  --filter="bindings.members:cloud-scheduler-runner"
```

#### 実行失敗時のエラー確認
```powershell
# 最新の実行の詳細を確認
$LATEST_EXECUTION = (gcloud run jobs executions list --job=fx-mxn-watcher --region=asia-northeast1 --limit=1 --format="value(name)")
gcloud run jobs executions describe $LATEST_EXECUTION --region=asia-northeast1

# エラーログのみ表示
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher AND severity>=ERROR" `
  --limit 50 `
  --project fx-mxn-watcher-bot
```

### 📈 監視コマンド

#### 実行頻度の確認
```powershell
# 過去24時間の実行回数を確認
gcloud run jobs executions list --job=fx-mxn-watcher --region=asia-northeast1 --limit=30
```

**期待値**: 24回前後（毎時1回）

#### 料金確認
```powershell
# Cloud Run の使用状況（GCPコンソールで確認）
# https://console.cloud.google.com/run?project=fx-mxn-watcher-bot

# 請求情報の確認（GCPコンソールで確認）
# https://console.cloud.google.com/billing
```

### 🔑 便利なエイリアス設定（オプション）

PowerShellで頻繁に使うコマンドをエイリアスに設定できます：

```powershell
# プロファイルに追加（永続化）
notepad $PROFILE

# 以下を追加
function Check-FxJob { gcloud run jobs executions list --job=fx-mxn-watcher --region=asia-northeast1 --limit=10 }
function Check-FxLog { gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher" --limit 30 --format "table(timestamp, textPayload)" --project fx-mxn-watcher-bot }
function Check-Scheduler { gcloud scheduler jobs describe fx-mxn-watcher-schedule --location=asia-northeast1 }

# 使い方
# Check-FxJob      → 実行履歴を確認
# Check-FxLog      → ログを確認
# Check-Scheduler  → Schedulerの状態を確認
```

### 📌 よく使うコマンド Top 3

日常的な運用で最もよく使うコマンド：

```powershell
# 1. 実行履歴の確認（最も頻繁に使用）
gcloud run jobs executions list --job=fx-mxn-watcher --region=asia-northeast1 --limit=10

# 2. 最新ログの確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=fx-mxn-watcher" `
  --limit 30 `
  --format "table(timestamp, textPayload)" `
  --project fx-mxn-watcher-bot

# 3. Schedulerの状態確認
gcloud scheduler jobs describe fx-mxn-watcher-schedule --location=asia-northeast1
```

---

## おわりに
これで、メキシコペソ専用のAI市場監視Botが完成しました！

### このBotの特徴
✅ **MXN/JPY（メキシコペソ/円）を24時間365日監視**
✅ **変動率0.5%以上の急変動を即座に検知**
✅ **円建て表示で日本の投資家に最適**
✅ **AIが日本のFXスワップ投資家向けに相場解説**
✅ **月額コストほぼ0円で運用可能**

### FXスワップ投資家へのメリット
- 仕事中も安心して本業に集中できる
- 暴落の兆候を見逃さない
- AIアナリストが24時間サポート
- 保証金維持率1000%を守る監視体制

本業に集中しながら、不労所得を増やす環境が整います。
