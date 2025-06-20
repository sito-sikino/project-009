# Discord Multi-Agent System - Production Dockerfile
FROM python:3.12-slim

# メタデータ
LABEL maintainer="Discord Multi-Agent System"
LABEL version="1.0.0"
LABEL description="統合受信・個別送信型アーキテクチャ Discord Bot"

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 作業ディレクトリ
WORKDIR /app

# システムの依存関係インストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係インストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# ディレクトリ作成
RUN mkdir -p /app/logs

# ヘルス・メトリクス用ポート
EXPOSE 8000

# 非rootユーザー作成
RUN groupadd -r discord && useradd -r -g discord discord
RUN chown -R discord:discord /app
USER discord

# ヘルスチェック設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/ready', timeout=5)" || exit 1

# 起動コマンド
CMD ["python", "main.py"]