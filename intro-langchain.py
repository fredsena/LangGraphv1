import os
import getpass
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate


llm = ChatOpenAI(
    model="qwen/qwen3-4b-2507", 
    #model="llama-3.2-3b-instruct",
    base_url="http://127.0.0.1:1234/v1", 
    temperature=0.2, 
    api_key="11111111111111")

#response = llm.invoke("Hello there. Tell me a story using 10 words or less.")
#print(response.content)

# 2. Message Structuring
#     LangChain supports structured message inputs including:
#     SystemMessage: Sets the assistant’s behavior.
#     HumanMessage: Represents user input.
#     AIMessage: Includes prior assistant responses.

messages = [
  SystemMessage(content="You are a helpful assistant."),
  HumanMessage(content="What's the capital of Brazil?"),
  AIMessage(content="The capital of Brazil is Brasília."),
  HumanMessage(content="What's the capital of Canada?")
]

response = llm.invoke(messages)
print(response.content)

# 3. Prompt Templates
# LangChain offers two styles of templated prompting:
# a. Basic PromptTemplate
#     Defines a single-variable input prompt with a placeholder.

prompt = PromptTemplate(
  input_variables=["topic"],
  template="Tell me a joke about {topic} and explain it."
)

#The prompt can be formatted using .format() or .invoke():

formatted_prompt = prompt.format(topic="Python")
response = llm.invoke(prompt.invoke({"topic": "Python"}))

#print(response.content)


# b. Few-Shot PromptTemplate

#Combines multiple structured examples to guide the LLM’s reasoning.

# Components:
#     examples: List of example dictionaries (input → thought → output).
#     example_prompt: A PromptTemplate defining the format for each example.
#     suffix: The actual question for the current prompt.

examples = [
  {"input": "A train leaves City A...", "thought": "...", "output": "2 hours"},
  {"input": "A store applies a 20% discount...", "thought": "...", "output": "..."},  
]

example_prompt = PromptTemplate(
  input_variables=["input", "thought", "output"],
  template="Question: {input}\nThought: {thought}\nResponse: {output}"
)

few_shot_prompt = FewShotPromptTemplate(
  examples=examples,
  example_prompt=example_prompt,
  suffix="Question: {input}",
  input_variables=["input"]
)

response = llm.invoke(few_shot_prompt.invoke(
    {"input": "If today is Wednesday, what day will it be in 10 days?"}
))

print(response.content)