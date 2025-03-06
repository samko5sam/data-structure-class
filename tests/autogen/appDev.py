import os
import asyncio
from dotenv import load_dotenv
from autogen_core.models import UserMessage
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from datetime import datetime

load_dotenv()

# 初始化 OpenAI API
model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",  # 可切換為 "gpt-4o" 
)

# 代理人設定
news_search_agent = MultimodalWebSurfer("news_search_agent", model_client)
news_summary_agent = AssistantAgent("news_summary_agent", model_client)
analysis_agent = AssistantAgent("analysis_agent", model_client)
comparison_agent = AssistantAgent("comparison_agent", model_client)
user_proxy = UserProxyAgent("user_proxy")

# 任務 1: 獲取 App 開發趨勢與政策變更
async def fetch_app_news():
    current_year = datetime.now().year
    termination = TextMentionTermination("TERMINATE")
    news_team = RoundRobinGroupChat(
        [news_search_agent, news_summary_agent],
        termination_condition=termination
    )
    await Console(news_team.run_stream(
        task="請搜尋 Google Play 和 Apple App Store 的趨勢或政策變更，並撰寫摘要。"
    ))

# 任務 2: 分析指定 App 的當天表現
async def analyze_app_performance(app_name):
    task = f"請分析 {app_name} 的市場表現，包括下載量、用戶評價、活躍度等。"
    await Console(analysis_agent.run_stream(task=task))

# 任務 3: 介紹一個競品或流行 App
async def fetch_competitor_app(app_name):
    task = f"請找出與 {app_name} 競爭的App，或在同類市場中熱門的App，並介紹其特點與優勢。"
    await Console(comparison_agent.run_stream(task=task))

# 總控函數
async def main():
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("請在 .env 檔案中加入 OPENAI_API_KEY")
        return

    app_name = "找出臥底"  # 這裡可以讓用戶輸入目標 App
    await fetch_app_news()  # 獲取新聞趨勢
    await analyze_app_performance(app_name)  # 分析指定 App 表現
    await fetch_competitor_app(app_name)  # 介紹競品 App

# 運行程式
if __name__ == '__main__':
    asyncio.run(main())
