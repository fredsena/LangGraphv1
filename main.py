
# uv pip install langchain_core langchain-openai langgraph

from langgraph.graph import StateGraph, MessagesState, START, END

def main():

    # from langchain.agents import create_agent

    # print("Hello from langgraphv1!")    

    # agent = create_agent(  
    #     model,
    #     tools,
    #     system_prompt="You are a helpful assistant.",
    # )    

    def mock_llm(state: MessagesState):
        return {"messages": [{"role": "ai", "content": "hello world"}]}

    graph = StateGraph(MessagesState)
    graph.add_node(mock_llm)
    graph.add_edge(START, "mock_llm")
    graph.add_edge("mock_llm", END)
    graph = graph.compile()

    result = graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})    
    print(result)


if __name__ == "__main__":
    main()
