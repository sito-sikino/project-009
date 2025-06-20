"""
Gemini API Client - Gemini 2.0 Flash統合
統合エージェント選択・応答生成API
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage


class GeminiClient:
    """
    Gemini 2.0 Flash API統合クライアント
    
    責務:
    - 統合エージェント選択（エージェント判定+応答生成）
    - レート制限対応（15RPM/1500RPD）
    - プロンプトテンプレート管理
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Gemini Client初期化
        
        Args:
            api_key: Gemini API Key（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # ChatGoogleGenerativeAI初期化
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=self.api_key,
            temperature=0.4,
            max_output_tokens=1000
        )
        
        # レート制限管理
        self._last_call_time = 0
        self._min_interval = 4.0  # 15RPM制限対応（4秒間隔）
    
    async def unified_agent_selection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        統合エージェント選択・応答生成
        
        1回のAPI呼び出しでエージェント選択と応答生成を実行
        
        Args:
            context: 入力コンテキスト
                - message: str (ユーザーメッセージ)
                - hot_memory: List[Dict] (当日記憶)
                - cold_memory: List[Dict] (長期記憶)
                - channel_id: str (チャンネルID)
        
        Returns:
            Dict[str, Any]: 統合応答
                - selected_agent: str (選択エージェント)
                - response_content: str (応答内容)
                - confidence: float (信頼度)
                - reasoning: str (選択理由)
        """
        # レート制限チェック
        await self._handle_rate_limit()
        
        try:
            # 統合プロンプト生成
            prompt = self._generate_unified_prompt(context)
            
            # Gemini API呼び出し
            response = await self._call_gemini_api(prompt)
            
            return response
            
        except Exception as e:
            # エラー時のフォールバック
            return {
                'selected_agent': 'spectra',
                'response_content': f'申し訳ありません。処理中にエラーが発生しました。',
                'confidence': 0.5,
                'reasoning': f'エラーのためSpectraにフォールバック: {str(e)}'
            }
    
    def _generate_unified_prompt(self, context: Dict[str, Any]) -> str:
        """
        統合プロンプトテンプレート生成
        
        Args:
            context: 入力コンテキスト
            
        Returns:
            str: 統合プロンプト
        """
        message = context.get('message', '')
        hot_memory = context.get('hot_memory', [])
        cold_memory = context.get('cold_memory', [])
        
        # メモリコンテキスト構築
        memory_context = ""
        if hot_memory:
            memory_context += "## 当日の会話履歴:\n"
            for item in hot_memory[-5:]:  # 直近5件
                memory_context += f"- {item.get('content', '')}\n"
        
        if cold_memory:
            memory_context += "\n## 関連する過去の記憶:\n"
            for item in cold_memory[:3]:  # 関連上位3件
                memory_context += f"- {item.get('summary', '')}\n"
        
        # 統合プロンプト
        prompt = f"""あなたは3つのDiscordエージェントを統括するSupervisorです。
以下のメッセージに対して、最適なエージェント選択と応答内容を同時に生成してください。

## エージェント特性:
- **SPECTRA**: メタ進行役、議論の構造化、全体方針整理、一般対話
- **LYNQ**: 論理収束役、技術的検証、構造化分析、問題解決
- **PAZ**: 発散創造役、革新的アイデア、創造的テーマ、ブレインストーミング

## ユーザーメッセージ:
{message}

{memory_context}

## 出力形式:
以下のJSON形式で回答してください:
{{
    "selected_agent": "spectra|lynq|paz",
    "response_content": "選択されたエージェントとしての応答内容",
    "confidence": 0.95,
    "reasoning": "エージェント選択の理由"
}}

JSON以外は出力しないでください。"""

        return prompt
    
    async def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """
        Gemini API実際の呼び出し
        
        Args:
            prompt: API送信プロンプト
            
        Returns:
            Dict[str, Any]: パースされた応答
        """
        messages = [
            SystemMessage(content="You are a Discord multi-agent supervisor."),
            HumanMessage(content=prompt)
        ]
        
        # LangChain経由でAPI呼び出し
        response = await self.llm.ainvoke(messages)
        
        # JSON応答をパース
        try:
            # 応答からJSON部分を抽出
            content = response.content.strip()
            if content.startswith('```json'):
                content = content[7:-3].strip()
            elif content.startswith('```'):
                content = content[3:-3].strip()
            
            result = json.loads(content)
            
            # 必須フィールドの検証
            required_fields = ['selected_agent', 'response_content', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            # JSON解析失敗時のフォールバック
            return {
                'selected_agent': 'spectra',
                'response_content': response.content,
                'confidence': 0.7,
                'reasoning': f'JSON解析失敗のためSpectraフォールバック: {str(e)}'
            }
    
    async def _handle_rate_limit(self):
        """レート制限対応（15RPM制限）"""
        import time
        
        current_time = time.time()
        time_since_last = current_time - self._last_call_time
        
        if time_since_last < self._min_interval:
            await asyncio.sleep(self._min_interval - time_since_last)
        
        self._last_call_time = time.time()