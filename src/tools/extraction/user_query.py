from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import json
from .config import llm, system_message


class ExtractionResult(BaseModel):
    device_name: str = Field(description="The exact model name. If generic, leave empty.")
    problem: str = Field(description="A string describing the issue mentioned in the query.")
    follow_up_question: str = Field(description="Follow-up question to clarify the device if device_name is empty.")


@tool
def extract_problem_and_device(user_input: str) -> dict:
    """
    Extracts the problem and device name from the user input.
    and output the result in JSON format with the folowing keys:
    - "problem": A string describing the issue mentioned in the query.
    - "device_name": The exact model name. If the user only provided a generic term, this should be an empty string.
    - "follow_up_question": If the "device_name" is empty, provide a follow-up question to clarify the device.
    Args:
        user_input (str): The user's query.
        llm: The language model instance.
    """
    parser = JsonOutputParser(pydantic_object=ExtractionResult)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{user_input}")
    ])


    chat = prompt | llm | parser
    response = chat.invoke({"user_input": user_input})
    # print("response:\n\n", response, "type:", type(response), "\n\n")

    return response

# print(extract_problem_and_device("i broke my phone screen and it won't turn on. I have a Samsung Galaxy S21.", llm))