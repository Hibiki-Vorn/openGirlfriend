import json
import subprocess
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama.chat_models import ChatOllama
from config import girlfriend_name, user_name, premessage, model

ollama_llm = ChatOllama(model=model)
memory_saver = MemorySaver()

@tool
def shell_tool(shell_commands) -> str:
    """
    Execute a shell command and return stdout/stderr as string.
    """
    feedback = ""
    cmds = shell_commands
    for cmd in cmds:
        print(f"[Executing]: {cmd}")
        try:
            res = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            
            if res.stdout:
                feedback += f"\n[Command]:\n{cmd}\n\n[Command Output]:\n{res.stdout.strip()}\n"
            if res.stderr:
                feedback += f"\n[Command]:\n{cmd}\n\n[Command Error]:\n{res.stderr.strip()}\n"
            
        except subprocess.CalledProcessError as e:
            print(f"[Error executing command '{cmd}']: {e}")
            
    return feedback

agent = create_agent(
    model=ollama_llm,
    tools=[shell_tool],
    system_prompt=SystemMessage(content=premessage),
    checkpointer=memory_saver
)

print(f"{girlfriend_name} Agent ready!\n")

thread_id = "main_session"
tool_call_id = ""
feedbacks = ""

while True:
    
    try:
        if feedbacks != "":
            result = agent.invoke(
                {"messages": [{"role": "tool","tool_name":"shell_tool", "content": feedbacks, "tool_call_id": tool_call_id}]},
                {"configurable": {"thread_id": thread_id}}
            )
        else:
            user_input = input(f"{user_name}: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat...")
                break
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                {"configurable": {"thread_id": thread_id}}
            )
    except Exception as e:
        print(f"[Error invoking agent]: {e}")
        continue

    ai_msg = result["messages"][-1]
    last_ai_text = ai_msg.text.strip()
    clean_text = last_ai_text.strip("`").strip()

    try:
        response_json = json.loads(clean_text)
    except json.JSONDecodeError:
        response_json = {"text": clean_text, "shell": []}

    text = response_json.get("text", "")
    shell_commands = response_json.get("shell", [])
    try:
        tool_call_id = ai_msg.tool_calls[0].id
    except (AttributeError, IndexError):
        tool_call_id = ""
    if shell_commands != []:
        shell_result = agent.invoke({
            "messages": [{
                "role": "tool",
                "tool_name": "shell_tool",
                "content": shell_commands,
                "tool_call_id": tool_call_id
            }],},
            {"configurable": {"thread_id": thread_id}}
        )
        feedbacks = shell_result["messages"][-1].text.strip()
    else:
        feedbacks = ""

    if text:
        print(f"{girlfriend_name}: {ai_msg.text}\n")
