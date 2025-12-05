import json
import os
import getpass
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import tool
from langgraph.config import get_stream_writer

# class WeatherMiddleware(AgentMiddleware):
#   tools = [get_weather, get_temperature]

# agent = create_deep_agent(
#     model="anthropic:claude-sonnet-4-20250514",
#     middleware=[WeatherMiddleware()]
# )

research_instructions = """You are an expert ."""


modelV1 = ChatOpenAI(
    #model="qwen/qwen3-vl-4b",
    model="qwen/qwen3-4b-2507", 
    base_url="http://127.0.0.1:1234/v1",
    temperature=0.0,
    api_key="lm-studio"
)


# @tool
# def get_weather(city: str) -> str:
#     """Get the weather in a city."""
#     return f"The weather in {city} is sunny OXENTY."

@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    writer = get_stream_writer()
    # stream any arbitrary data
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")
    return f"It's always sunny in {city}! OXENTY"


@tool
def get_temperature(city: str) -> str:
    """Get the temperature in a city."""
    return f"The temperature in {city} is 70 degrees Fahrenheit."

agent = create_deep_agent(
    system_prompt=research_instructions,
    model=modelV1,
    tools=[get_weather,get_temperature],
    # interrupt_on={
    #     "get_weather": {
    #         "allowed_decisions": ["approve", "edit", "reject"]
    #     },
    # }
)

# Run the agent with a specific query
# query = "What's the weather and temperature in Fortaleza Ceara?"
# result = agent.invoke({"messages": [{"role": "user", "content": query}]})

# # Print the final response
# for message in result["messages"]:
#     if hasattr(message, "content"):
#         print(f"{message.__class__.__name__}: {message.content}")


# for token, metadata in agent.stream(
#     {"messages": [{"role": "user", "content": "What's the weather and temperature in Fortaleza Ceara."}]},
#     stream_mode="messages",
# ):
#     print(f"{token.content}", end="")      


# Stream = values
# for step in agent.stream(
#     {"messages": [{"role": "user", "content": "What's the weather and temperature in Fortaleza Ceara"}]},
#     stream_mode="values",
# ):
#     step["messages"][-1].pretty_print()

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What's the weather and temperature in Fortaleza Ceara?"}]},
    stream_mode=["values", "custom"],
):
    #print(chunk)
    print(json.dumps(chunk, indent=2, default=str))
    print("-" * 50)

