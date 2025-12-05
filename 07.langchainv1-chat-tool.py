import pathlib
import re

import requests
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from typing import Literal
from langchain.tools import tool


@tool(
    "calculator",
    parse_docstring=True,
    description=(
        "Perform basic arithmetic operations on two real numbers."
        "Use this whenever you have operations on any numbers, even if they are integers."
    ),
)
def real_number_calculator(
    a: float, b: float, operation: Literal["add", "subtract", "multiply", "divide"]
) -> float:
    """Perform basic arithmetic operations on two real numbers.

    Args:
        a (float): The first number.
        b (float): The second number.
        operation (Literal["add", "subtract", "multiply", "divide"]):
            The arithmetic operation to perform.

            - `"add"`: Returns the sum of `a` and `b`.
            - `"subtract"`: Returns the result of `a - b`.
            - `"multiply"`: Returns the product of `a` and `b`.
            - `"divide"`: Returns the result of `a / b`. Raises an error if `b` is zero.

    Returns:
        float: The numerical result of the specified operation.

    Raises:
        ValueError: If an invalid operation is provided or division by zero is attempted.
    """
    print("🧮  Invoking calculator tool")
    # Perform the specified operation
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Division by zero is not allowed.")
        return a / b
    else:
        raise ValueError(f"Invalid operation: {operation}")



llm = ChatOpenAI(
    model="qwen/qwen3-4b-2507", 
    #model="llama-3.2-3b-instruct",
    #model="qwen3-4b-instruct-2507-polaris-alpha-distill",
    base_url="http://127.0.0.1:1234/v1", 
    temperature=0.0, 
    api_key="11111111111111")

agent = create_agent(
    system_prompt="You are a helpful assistant.",
    model=llm,
    checkpointer=InMemorySaver(),
    tools=[real_number_calculator],
)

# human_msg = HumanMessage("Hello, how are you?")

# result = agent.invoke({"messages": [human_msg]})

# print("---- Content Response ----")
# print(result["messages"][-1].content)

# print("---- Full Messages ----")
# print(result["messages"])

# print("---- Message Types ----")
# for msg in result["messages"]:
#     print(f"{msg.type}: {msg.content}\n")


# print("---- Pretty Print Messages ----")
# for i, msg in enumerate(result["messages"]):
#     msg.pretty_print()

# Thread ID for maintaining conversation history
thread_id = "conversation_1"

print("=" * 60)
print("Assistant Chat Bot")
print("=" * 60)
print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")

# Chat loop
while True:
    # Get user input
    user_input = input("You: ").strip()
    
    # Check for exit commands
    if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
        print("\n👋 Thanks for chatting! Goodbye!")
        break
    
    # Skip empty inputs
    if not user_input:
        continue
    
    # Create human message
    human_msg = HumanMessage(user_input)
    
    # Invoke agent with thread configuration to maintain history
    result = agent.invoke(
        {"messages": [human_msg]},
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # Display the AI's response
    ai_response = result["messages"][-1].content
    print(f"\n🤖 Bot: {ai_response}\n")


