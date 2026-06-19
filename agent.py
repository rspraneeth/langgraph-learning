from langchain_ollama import ChatOllama
from langchain.agents import create_agent

model = ChatOllama(model = "qwen2.5:7b")

def get_current_time() -> str:
    """Get the current time right now."""
    from datetime import datetime
    return datetime.now().strftime("%H:%M:%S")

def get_hour_from_time(time_str: str) -> int:
    """Extract the hour as a number from a time string like '11:05:25'."""
    return int(time_str.split(":")[0])

def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


agent = create_agent(model, tools=[get_current_time, add, get_hour_from_time])

result = agent.invoke({"messages": [{"role": "user", "content": "What is 15 plus the current hour?"}]})

for message in result["messages"]:
    print(f"[{message.type}]: {message.content}")