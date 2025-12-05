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
    system_prompt="You are a full-stack comedian",
    model=llm,
)



# Stream = values
for step in agent.stream(
    {"messages": [{"role": "user", "content": "Tell me a Dad joke"}]},
    stream_mode="values",
):
    step["messages"][-1].pretty_print()


#token by token
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "Write me a family friendly poem."}]},
    stream_mode="messages",
):
    print(f"{token.content}", end="")



    


