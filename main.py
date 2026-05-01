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
