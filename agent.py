from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.tools import ShellTool
from config import girlfriend_name, user_name, premessage, model
from langchain_ollama.chat_models import ChatOllama

# 初始化本地模型
ollama_llm = ChatOllama(model=model)

# 检查点 memory （短期对话记忆）
memory_saver = MemorySaver()

# 创建 agent
shell_tool = ShellTool()

agent = create_agent(
    model=ollama_llm,
    tools=[shell_tool],
    system_prompt=SystemMessage(content=premessage),
    checkpointer=memory_saver
)

print(f"{girlfriend_name} Agent ready!\n")

thread_id = "main_session"

while True:
    user_input = input(f"{user_name}: ")

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]}, # type: ignore
        {"configurable": {"thread_id": thread_id}} # type: ignore
    )

    # 取出最后的 AIMessage 对象
    last_ai = result["messages"][-1]

    # 安全地获取文本
    final_text = last_ai.text

    print(f"{girlfriend_name}: {final_text}")
