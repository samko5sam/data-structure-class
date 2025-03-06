from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

model = LiteLLMModel(model_id="gemini/gemini-2.0-flash-exp")
agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model)
print(agent.run("台北市大安區的天氣如何？繁體中文"))