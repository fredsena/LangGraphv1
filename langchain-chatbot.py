import os
import getpass
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate




class ChatBot():
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []

        # Few shot examples
        examples = [
            {
                "input": "What is a good name for a company that makes colorful socks?",
                "output": "FunSock Co."
            }, {
                "input": "What is a good name for a company that sells car toys?",
                "output": "CarToys Inc."
            }, {
                "input": "What is a good name for a company that sells garden toys?",
                "output": "GardenToys Inc."
            }
        ]
        example_prompt = PromptTemplate(
            input_variables=["input", "output"],
            template="Q: {input}\nA: {output}"
        )
        self.few_shot_prompt = FewShotPromptTemplate(
            examples=examples,
            example_prompt=example_prompt,
            prefix="Generate a creative company name based on the input question.",
            suffix="Q: {input}\nA:",
            input_variables=["input"]
        )

        self.llm = ChatOpenAI(
            model="qwen/qwen3-4b-2507",
            #model="llama-3.2-3b-instruct",
            base_url="http://127.0.0.1:1234/v1",
            temperature=0.2,
            api_key="11111111111111")
    
    def invoke(self, user_input):
        human_msg = HumanMessage(content=user_input)
        self.messages.append(human_msg)

        ai_msg = self.llm.invoke(self.messages)
        self.messages.append(ai_msg)

        return ai_msg.content        
        

#run chatbot
if __name__ == "__main__":
    bot = ChatBot()

    print("Welcome to the LangChain ChatBot! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break

        #1
        #prompt = bot.few_shot_prompt.format(input=user_input)
        #response = bot.llm.invoke(prompt)
        
        #2
        # messages = [
        #     SystemMessage(content="You are a helpful assistant that gives short answers."),
        #     HumanMessage(content=user_input)
        # ]
        # response = bot.llm.invoke(messages)
        # answer = response.content.strip()

        answer = bot.invoke(user_input)
        print(f"Bot: {answer}")
        


