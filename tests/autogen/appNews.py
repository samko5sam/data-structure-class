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

load_dotenv()

async def app_dev_news_summary():
  model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
  )

  # 建立各代理人
  assistant = AssistantAgent("assistant", model_client)
  web_surfer = MultimodalWebSurfer("web_surfer", model_client)
  user_proxy = UserProxyAgent("user_proxy")

  # 當對話中出現 "exit" 時即終止對話
  termination_condition = TextMentionTermination("TERMINATE")

  # 建立一個循環團隊，讓各代理人依序參與討論
  news_team = RoundRobinGroupChat(
    [web_surfer, assistant],
    termination_condition=termination_condition
  )

  await Console(news_team.run_stream(task="請搜尋 Google Play、Apple App Store 的相關新聞，並撰寫一份簡短摘要。"))

async def main():
  OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
  if not OPENAI_API_KEY:
    print("請在 .env 檔案中加入 OPENAI_API_KEY")
    return
  await app_dev_news_summary()

if __name__ == '__main__':
  asyncio.run(main())