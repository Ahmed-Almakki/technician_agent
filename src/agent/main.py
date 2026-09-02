import json
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

from ..tools.tools import search, categories, steps_follow
from .config import system_message, llm


tools = [search, categories, steps_follow]
memory_saver = InMemorySaver()


def run_agent(query: json, llm: HuggingFaceEndpoint, session_id: str,) -> dict:
    """
    Runs the agent to process the user query.

    Args:
        query (json): The user's query in JSON format.
        llm (HuggingFaceEndpoint): The language model instance.
        session_id (str): The unique ID for the user's conversation.
    """
    user_query_string = json.dumps(query)

    chat_model = ChatHuggingFace(llm=llm)

    agent = create_agent(
        model=chat_model,
        tools=tools,
        system_prompt=system_message,
        checkpointer=memory_saver
    )

    thread_config = {"configurable": {"thread_id": session_id}}

    # response = agent.invoke(
    #     {"messages": [{"role": "user", "content": user_query_string}]},
    #     config=thread_config
    # )

   
    print("--- AGENT THOUGHT PROCESS START ---")
    
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": user_query_string}]},
        config=thread_config
    ):
        # This will print every tool call, tool result, and LLM thought to your console
        print(chunk)
        print("-----------------------------------")


        final_answer = "I'm sorry, I couldn't process that request."
        node_name = list(chunk.keys())[0]

        if node_name in ["model", "agent"]: 
            final_answer = chunk[node_name]["messages"][-1].content
            
    print("--- AGENT THOUGHT PROCESS END ---")
    return final_answer


    # return response["messages"][-1].content

query = json.loads('{"device_name": "Sony PlayStation 5", "problem": "fan replacement"}')
print("query:\n\n", query)
result = run_agent(query, llm, "test_session_1")
print("\n\n", "=========="*40)
print("final result:\n\n", result)