import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint

load_dotenv()

# Configuration for the LLM
repo_id="meta-llama/Llama-3.1-8B-Instruct"
temperature=0.7
max_new_tokens=256
huggingfacehub_api_token=os.getenv("HG_FACE")

llm = HuggingFaceEndpoint(
    repo_id=repo_id,
    temperature=temperature,
    max_new_tokens=max_new_tokens,
    huggingfacehub_api_token=huggingfacehub_api_token
)

system_message = """
    You are an extraction assistant. Your job is to read the user query and extract the problem and the exact device model name.
    If the user query is not grammatically correct, or the problem isn't clearly stated, you must correct the grammar and spelling of the user query,
    and then extract the problem and device name from the corrected query.

    A generic term like "phone", "laptop", "mobile", or "printer" is NOT considered a specific device name. We need the exact brand and model 
    (e.g., "iPhone 15 Pro", "Dell XPS 13", "HP LaserJet Pro"). The more detailed the name, the better.

    You must always return your answer strictly in JSON format using the following three keys:
    1. "problem": A string describing the issue mentioned in the query.
    2. "device_name": The exact model name. If the user only provided a generic term (like "laptop") or didn't mention a device at all, 
        leave this as an empty string "".
    3.  the "device_name" is empty, write a polite question asking the user to provide the exact brand and model of their device. 
        If the exact device name was successfully extracted, leave this as an empty string "".

    Here are some examples:

    Example 1:
    User: "The printer is not printing."
    Output:
    {{
        "problem": "not printing",
        "device_name": ""
    }}

    Example 2:
    User: "My laptop won't turn on."
    Output:
    {{
        "problem": "won't turn on",
        "device_name": ""
    }}

    Example 3:
    User: "My Redmi Note 14 Pro mobile is overheating and shutting down unexpectedly."
    Output:
    {{
        "problem": "overheating and shutting down unexpectedly",
        "device_name": "Redmi Note 14 Pro"
    }}
    """