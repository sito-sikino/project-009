#!/usr/bin/env python3
"""
超シンプルDiscordボット - デバッグ不要な最小構成
"""
import os
import discord
from dotenv import load_dotenv

load_dotenv()

# 基本設定
intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'🎉 {client.user} がログインしました！')
    print(f'サーバー数: {len(client.guilds)}')
    
    # ステータス設定
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Game("シンプルテスト中")
    )
    
    print('🧪 テスト: 任意のチャンネルで "simple" と送信してください')

@client.event
async def on_message(message):
    # 自分のメッセージは無視
    if message.author == client.user:
        return
    
    print(f'📨 メッセージ受信: {message.author} -> {message.content}')
    
    # テスト応答
    if 'simple' in message.content.lower():
        await message.channel.send('✅ シンプルテスト成功！ボットが正常に動作しています。')
        print('✅ 応答送信完了')

# 実行
if __name__ == '__main__':
    token = os.getenv('DISCORD_RECEPTION_TOKEN')
    if token:
        print('🚀 シンプルボット開始...')
        client.run(token)
    else:
        print('❌ トークンが見つかりません')