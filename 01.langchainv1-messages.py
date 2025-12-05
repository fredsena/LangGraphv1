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

llm = ChatOpenAI(
    model="qwen/qwen3-4b-2507", 
    #model="llama-3.2-3b-instruct",
    #model="qwen3-4b-instruct-2507-polaris-alpha-distill",
    base_url="http://127.0.0.1:1234/v1", 
    temperature=0.0, 
    api_key="11111111111111")

agent = create_agent(
    system_prompt="You are a comedian.",
    model=llm,
)

human_msg = HumanMessage("Hello, tell me joke about programmers.")

result = agent.invoke({"messages": [human_msg]})

print("---- Content Response ----")
print(result["messages"][-1].content)

print("---- Full Messages ----")
print(result["messages"])

print("---- Message Types ----")
for msg in result["messages"]:
    print(f"{msg.type}: {msg.content}\n")


print("---- Pretty Print Messages ----")
for i, msg in enumerate(result["messages"]):
    msg.pretty_print()

    


