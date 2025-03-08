from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

model = LiteLLMModel(model_id="gemini/gemini-2.0-flash-exp")
agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model)
print(agent.run("請搜尋 Google Play 和 Apple App Store 的開發相關新聞，並撰寫一份簡短摘要,列點整理,繁體中文"))