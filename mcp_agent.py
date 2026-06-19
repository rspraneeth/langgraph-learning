import asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

model = ChatOllama(model="qwen2.5:7b")

client = MultiServerMCPClient(
    {
        "demo-math": {
            "transport": "stdio",
            "command": "python",
            "args": [r"C:\Projects\mcp-learning\server.py"],
        }
    }
)


async def main():
    tools = await client.get_tools()

    print("Tools loaded from MCP server:")
    for tool in tools:
        print(f"- {tool.name}")

    agent = create_agent(model, tools)

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "What is the account balance for user alice123?"}]}
    )

    for message in result["messages"]:
        print(f"[{message.type}]: {message.content}")


asyncio.run(main())