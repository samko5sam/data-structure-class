import os
import asyncio
import pandas as pd
import json
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer

load_dotenv()

async def discuss_and_recommend(chunk_data, start_idx, total_records, model_client, termination_condition):
    """
    讓 AI Agents 針對商品評價進行討論並提供選購建議
    Args:
        chunk_data: 當前批次的商品評價資料
        start_idx: 批次起始索引
        total_records: 總記錄數
        model_client: 模型客戶端
        termination_condition: 終止條件
    Returns:
        包含討論過程和最終建議的訊息列表
    """
    # 準備討論提示
    discussion_prompt = (
        f"目前正在處理第 {start_idx} 至 {start_idx + len(chunk_data) - 1} 筆商品評價資料（共 {total_records} 筆）。\n"
        f"以下為該批次評價資料:\n{chunk_data}\n\n"
        "請各位代理人進行以下任務：\n"
        "1. 分析評價中的正面與負面意見，特別注意不同規格/型號的差異\n"
        "2. MultimodalWebSurfer 請搜尋相關商品的最新市場資訊（價格趨勢、競爭產品等）\n"
        "3. 討論並總結商品的優缺點\n"
        "4. 提供具體的選購建議，包括是否推薦購買、適合人群、注意事項等\n"
        "請協同合作，確保建議全面且實用。最終請由 assistant 總結並給出明確的選購推薦。"
    )

    # 創建專門的代理人角色
    review_analyst = AssistantAgent(
        name="review_analyst",
        model_client=model_client,
        description="專門分析商品評價，找出優缺點和模式"
    )
    web_researcher = MultimodalWebSurfer(
        name="web_researcher",
        model_client=model_client,
        description="搜尋市場資訊和競爭產品資料"
    )
    recommendation_expert = AssistantAgent(
        name="recommendation_expert",
        model_client=model_client,
        description="綜合分析並提供最終選購建議"
    )
    coordinator = UserProxyAgent(
        name="coordinator",
        description="協調討論流程，確保結論清晰"
    )

    # 建立討論小組
    discussion_team = RoundRobinGroupChat(
        [review_analyst, web_researcher, recommendation_expert, coordinator],
        termination_condition=termination_condition
    )

    messages = []
    async for event in discussion_team.run_stream(task=discussion_prompt):
        if isinstance(event, TextMessage):
            print(f"[{event.source}] => {event.content}\n")
            messages.append({
                "batch_start": start_idx,
                "batch_end": start_idx + len(chunk_data) - 1,
                "source": event.source,
                "content": event.content,
                "type": event.type,
                "prompt_tokens": event.models_usage.prompt_tokens if event.models_usage else None,
                "completion_tokens": event.models_usage.completion_tokens if event.models_usage else None
            })

    return messages

async def process_chunk(chunk, start_idx, total_records, model_client, termination_condition):
    """
    修改後的 process_chunk，整合討論和建議功能
    """
    chunk_data = chunk  # 直接使用傳入的資料
    return await discuss_and_recommend(chunk_data, start_idx, total_records, model_client, termination_condition)

async def main():
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("請檢查 .env 檔案中的 GEMINI_API_KEY。")
        return

    model_client = OpenAIChatCompletionClient(
        model="gemini-2.0-flash",
        api_key=gemini_api_key,
    )
    
    termination_condition = TextMentionTermination("exit")
    
    # 讀取 CSV 檔案
    csv_file_path = "list.csv"  # 請改為實際的 CSV 檔案路徑
    chunk_size = 30  # 每批次處理的評價數量
    chunks = pd.read_csv(csv_file_path, chunksize=chunk_size)
    total_records = sum(1 for _ in pd.read_csv(csv_file_path, chunksize=chunk_size))
    
    # 並行處理批次
    tasks = [
        process_chunk(
            chunk.to_dict(orient='records'),
            idx * chunk_size,
            total_records,
            model_client,
            termination_condition
        )
        for idx, chunk in enumerate(chunks)
    ]
    
    results = await asyncio.gather(*tasks)
    all_messages = [msg for batch in results for msg in batch]
    
    # 儲存結果
    df_log = pd.DataFrame(all_messages)
    output_file = "product_recommendation_log.csv"
    df_log.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"已將討論和建議紀錄輸出為 {output_file}")

def getRecommendations():
    asyncio.run(main())

if __name__ == '__main__':
    getRecommendations()