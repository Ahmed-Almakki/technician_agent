from langchain_huggingface import ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
import json
from config import llm, system_message



def extract_problem_and_device(user_input: str, llm: ChatHuggingFace) -> dict:
    """
    Extracts the problem and device name from the user input.

    Args:
        user_input (str): The user's query.
        llm (ChatHuggingFace): The language model instance.
    """
    chat_model = ChatHuggingFace(llm=llm)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{user_input}")
    ])


    chat = prompt | chat_model
    response = chat.invoke({"user_input": user_input})
    output = json.loads(response.content)

    return output

# print(extract_problem_and_device("i broke my phone screen and it won't turn on. I have a Samsung Galaxy S21.", llm))