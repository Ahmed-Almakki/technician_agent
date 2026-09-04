import json
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from ..tools.tools import search, categories, steps_follow
from ..tools.extraction.user_query import extract_problem_and_device
from .config import system_message, llm


memory_saver = InMemorySaver()


def run_agent(query, chat_model, session_id):
    user_query_string = json.dumps(query)

    agent = create_agent(
        model=chat_model,
        tools=[search, categories, steps_follow, extract_problem_and_device],
        system_prompt=system_message,
        checkpointer=memory_saver
    )

    thread_config = {"configurable": {"thread_id": session_id}}
    extracted_steps = None

    try:
        # for chunk in agent.stream(
        #     {"messages": [{"role": "user", "content": user_query_string}]},
        #     config=thread_config
        # ):
        result = "asdf"
        stream = agent.stream_events(
            {"messages": [{"role": "user", "content": user_query_string}]},
            config=thread_config,
            version="v3"
        )
        for message in stream.messages:
            print("reasoning:", message.reasoning, flush=True)
            full_message = message.output.content[1]
        if full_message:
            result = full_message['text']

            # node_name = list(chunk.keys())[0]

            # if node_name == "tools" and chunk['tools'].get('messages'): 
            #     result = chunk['tools'].get('messages')
            #     for tool_msg in result:
            #         if getattr(tool_msg, 'name', '') == 'steps_follow':
            #             try:
            #                 extracted_steps = json.loads(tool_msg.content)
            #                 final_answer = "Here is the step-by-step repair guide I found for you. Let me know if you need clarification on any step!"
            #                 return final_answer, extracted_steps
                            
            #             except json.JSONDecodeError:
            #                 pass

            # if node_name in ["model", "agent"]: 
            #     final_answer = chunk[node_name]["messages"][-1].content
                
    except Exception as e:
        if "rate_limit_exceeded" in str(e) or "413" in str(e):
            result = "I've hit my token limit for a moment! Please wait a minute and try asking again."
        else:
            result = "Oops, a system error occurred while processing your request."
            
        # Log the actual error to your terminal for debugging, but hide it from the user interface
        print(f"API Error: {str(e)}")

    return result


# query = json.loads('{"device_name": "Sony PlayStation 5", "problem": "fan replacement"}')
query = "How i restart my iphone 13"
result = run_agent(query, llm, "test_session_1")
print("\n\n", "=========="*40)
print("final result:\n\n", result)