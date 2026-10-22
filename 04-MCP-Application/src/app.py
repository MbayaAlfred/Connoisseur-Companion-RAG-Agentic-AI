"""Connoisseur Companion: WatsonX ReAct agent with MCP tools and Gradio UI."""
import os
from pathlib import Path

import gradio as gr
from fastmcp.client import Client, PythonStdioTransport
from langchain_ibm import ChatWatsonx
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

SERVER_SCRIPT = str(Path(__file__).resolve().parent / "server.py")

SYSTEM_PROMPT = """You are Connoisseur Companion, a friendly and knowledgeable AI
restaurant recommendation assistant.

You have access to a database of California restaurants containing
restaurant names, cuisines, locations, ratings, price ranges,
atmospheres, and customer reviews.

You have access to three MCP tools:
1. get_restaurant_info: Look up specific restaurants by name.
2. recommend_by_vibe: Find restaurants by mood or atmosphere.
3. get_review: Retrieve detailed restaurant reviews.

Choose the appropriate tools based on the user's question.
Use multiple tools when necessary. Base answers on information returned
by the tools. Never invent restaurant details or customer reviews.
Respond clearly, professionally, and conversationally.
"""


def make_model():
    project_id = os.environ.get("WATSONX_AI_PROJECT_ID") or os.environ.get("WATSONX_PROJECT_ID")
    if not project_id:
        raise RuntimeError("Set WATSONX_AI_PROJECT_ID or WATSONX_PROJECT_ID before running the chatbot.")
    return ChatWatsonx(
        model_id="ibm/granite-4-h-small",
        url=os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
        project_id=project_id,
        params={"temperature": 0.7},
    )


async def chat_with_agent(user_message: str, history: list) -> str:
    """Discover MCP tools, let the LLM select them, and return its final answer."""
    transport = PythonStdioTransport(script_path=SERVER_SCRIPT)
    async with Client(transport) as client:
        mcp_tools = await client.list_tools()
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in mcp_tools
        ]
        model = make_model().bind_tools(openai_tools)
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for msg in history:
            role, content = msg.get("role", ""), msg.get("content", "")
            if role == "user" and isinstance(content, str) and content:
                messages.append(HumanMessage(content=content))
            elif role == "assistant" and isinstance(content, str) and content:
                messages.append(AIMessage(content=content))
        messages.append(HumanMessage(content=user_message))

        for _ in range(10):
            response = await model.ainvoke(messages)
            messages.append(response)
            if not response.tool_calls:
                raw = response.content
                if isinstance(raw, list):
                    return " ".join(
                        block.get("text", "") if isinstance(block, dict) else str(block)
                        for block in raw
                    )
                return str(raw)

            for tool_call in response.tool_calls:
                # Logs help demonstrate actual MCP tool use during ReAct testing.
                print(f"[ReAct] Tool: {tool_call['name']} | args: {tool_call['args']}", flush=True)
                result = await client.call_tool(tool_call["name"], tool_call["args"])
                tool_output = " ".join(
                    item.text if hasattr(item, "text") else str(item)
                    for item in result.content
                ) if result.content else "(no result)"
                messages.append(ToolMessage(content=tool_output, tool_call_id=tool_call["id"]))

        return "I wasn't able to complete that request. Please try again."


async def handle_chat(user_message, history):
    if history is None:
        history = []
    if not user_message or not user_message.strip():
        yield history
        return

    previous_history = history
    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": "Thinking..."},
    ]
    yield history
    try:
        response_text = await chat_with_agent(user_message, previous_history)
    except Exception as exc:
        print(f"[Chat error] {type(exc).__name__}: {exc}", flush=True)
        response_text = "Sorry, I couldn't complete the request. Check the application terminal for details."
    history[-1] = {"role": "assistant", "content": response_text}
    yield history


with gr.Blocks(title="Connoisseur Companion") as demo:
    gr.Markdown(
        "# Connoisseur Companion\n"
        "Your AI guide to California's restaurant scene. "
        "Ask me about restaurants by name, cuisine, or vibe!"
    )
    chatbot = gr.Chatbot(height=500)
    msg_input = gr.Textbox(
        label="Ask about restaurants",
        placeholder='e.g., "Find me a moody spot in DTLA" or "Tell me about Sakura Garden"',
    )
    with gr.Row():
        btn1 = gr.Button("Find moody restaurants", size="sm")
        btn2 = gr.Button("Tell me about Iron & Embers", size="sm")
        btn3 = gr.Button("Zen dining in Little Tokyo?", size="sm")

    msg_input.submit(handle_chat, [msg_input, chatbot], [chatbot])
    msg_input.submit(lambda: "", None, msg_input)
    btn1.click(handle_chat, [gr.State("Find me some moody restaurants"), chatbot], [chatbot])
    btn2.click(handle_chat, [gr.State("Tell me about Iron & Embers"), chatbot], [chatbot])
    btn3.click(handle_chat, [gr.State("What's a zen dining experience in Little Tokyo?"), chatbot], [chatbot])


if __name__ == "__main__":
    print("Starting Connoisseur Companion...")
    demo.launch(theme=gr.themes.Soft(), share=False)
