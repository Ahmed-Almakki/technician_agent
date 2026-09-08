import json
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
import mlflow
import os
import warnings

from ..tools.tools import search, categories, steps_follow, retriver, save_to_db
from .config import system_message


warnings.filterwarnings("ignore", module="langchain_nvidia_ai_endpoints")
load_dotenv()

mlflow.langchain.autolog()
mlflow.set_tracking_uri(os.getenv('TRACK_URI'))
mlflow.set_experiment(os.getenv('EXPERIMENT_NAME'))
memory_saver = InMemorySaver()


def run_agent(query, chat_model, session_id):
    user_query_string = json.dumps(query)

    agent = create_agent(
        model=chat_model,
        tools=[search, categories, steps_follow, retriver, save_to_db],
        system_prompt=system_message,
        checkpointer=memory_saver
    )

    thread_config = {"configurable": {"thread_id": session_id}}

    try:
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
     
    except Exception as e:
        if "rate_limit_exceeded" in str(e) or "413" in str(e):
            result = "I've hit my token limit for a moment! Please wait a minute and try asking again."
        else:
            result = "Oops, a system error occurred while processing your request."
            
        # Log the actual error to your terminal for debugging, but hide it from the user interface
        print(f"API Error: {str(e)}")

    return result


# query = json.loads('{"device_name": "Sony PlayStation 5", "problem": "fan replacement"}')
# # query = "How i restart my iphone 13"
# result = run_agent(query, llm, "test_session_1")
# print("\n\n", "=========="*40)
# print("final result:\n\n", result)