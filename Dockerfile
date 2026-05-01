# Pythonの軽量イメージを使用
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
