from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel

model = LiteLLMModel(model_id="gemini/gemini-2.0-flash-exp")
codeAgent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model)

class PhoneModelSummaryAgent():
    def __init__(self, model):
        super().__init__()
        self.model = model

    def summarize_model(self):
        summary = self.interact_with_model()
        return summary

    def interact_with_model(self):
        prompt = f"Summarize the phone model: {self.model}. 繁體中文"
        return codeAgent.run(prompt)

# Usage
agent = PhoneModelSummaryAgent("Samsung Galaxy A56")
phone_summary = agent.summarize_model()
print(phone_summary)