import json
from langchain_core.tools import tool
import mlflow
import requests as req
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from functools import lru_cache


load_dotenv()

@lru_cache(maxsize=1)
def get_embedding_model():
    """Loads the model only when this function is called, and caches it."""
    from langchain_huggingface import HuggingFaceEmbeddings

    default_local_path = os.path.expanduser("~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf")
    embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH", default_local_path)
    
    return HuggingFaceEmbeddings(
        model_name=embedding_model_path, 
        model_kwargs={"device": 'cpu'}
    )



@tool
@mlflow.trace(name="search_tool", span_type="TOOL")
def search(device_name: str) -> list:
    """
    Search for the correct device name in the ifixit database using the provided device name.
    WARNING: This only returns list of text the actuall device name in the ifixit db. It DOES NOT return the numeric guide_id needed for fetching steps.
    """
    url = "https://www.ifixit.com/api/2.0/search/"
    parsed_device_name = device_name.replace(" ", "%20")
    request_url = f"{url}{parsed_device_name}"
    try:
        response = req.get(request_url)

        if response.status_code == 404:
            return "No search results found for the given device name."
        
        response.raise_for_status()
        res = response.json()

        result = res.get('results', [])

        if result:
            devices = [item['title'] for item in result if item['dataType'] == 'wiki']
        else:
            devices = []

    except req.RequestException as e:
        print(f"Error occurred while fetching data: {e}")
        res = {"error": str(e)}

    return json.dumps(devices)


@tool
@mlflow.trace(name="category_tool", span_type="TOOL")
def categories(device_name: str) -> list:
    """
    Fetches the categories for a given device name from the iFixit API.
    WARNING:
     - This only returns list of dict containing guide_id and device name and the problem.
    """
    url = "https://www.ifixit.com/api/2.0/categories/"
    parsed_device_name = device_name.replace(" ", "_")
    request_url = f"{url}{parsed_device_name}"
    try:
        response = req.get(request_url)

        if response.status_code == 404:
            return "No categories found for the given device name."
        
        response.raise_for_status()
        res = response.json()

        result = res.get('guides', [])

        if result:
            categories = [{'guideid': item['guideid'], 'device_name': item['category'], 'problem': item['title']} for item in result]
        else:
            categories = []

    except req.RequestException as e:
        print(f"Error occurred while fetching data: {e}")
        res = {"error": str(e)}

    return json.dumps(categories)


@tool
@mlflow.trace(name="steps_tool", span_type="RETRIEVER") # this is retriver so the metrics that check retrival
def steps_follow(guide_id: str):
    """
    Fetches the steps for a given guide ID from the iFixit API.
    Returns a JSON string containing a list of dictionaries. Each dictionary contains 
    the step's 'title', an array of text 'steps', and an array of 'images' (URLs).
    Use this tool whenever you need to provide the user with step-by-step device repair instructions.
    """
    url = "https://www.ifixit.com/api/2.0/guides/"
    request_url = f"{url}{guide_id}"
    try:
        response = req.get(request_url)

        if response.status_code == 404:
            return "No steps found for the given guide ID."
        
        response.raise_for_status()
        res = response.json()

        steps = res.get('steps', [])
        result = []
        if len(steps) > 0:
            for item in steps:
                details = {}
                details['title'] = item.get('title', '')

                # Safely get the text lines
                lines = item.get('lines', [])
                text = [step.get('text_raw', '') for step in lines]
                details['steps'] = text

                # Safely get the images, with a fallback just in case!
                images = []
                media = item.get('media')
                
                # Check if media exists and is an image type
                if media and isinstance(media, dict) and media.get('type') == 'image':
                    for img in media.get('data', []):
                        # Try to get huge, fallback to original or large if huge is missing
                        img_url = img.get('thumbnail') or img.get('original') or img.get('large')
                        if img_url:
                            images.append(img_url)
                            
                details['images'] = images
                result.append(details)

                # for test remve after test
                if len(result) > 2500:
                    result = result[:2500] 
        return json.dumps(result)
    except req.RequestException as e:
        print(f"Error occurred while fetching data: {e}")
        res = {"error": str(e)}
        return json.dumps(res)


@tool
def retriver(query: str):
    """
    Searches the database using vector search to find relevant iFixit guide IDs.
    IMPORTANT INPUT RULE: You must always pass the `query` as a combined string containing 
    BOTH the device name and the problem. 
    Example: "Nintendo Switch Left Joy-Con joystick not working"
    """
    try:
        model = get_embedding_model()
        engine = create_engine(
            f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
        )
        embedded_input = model.embed_query(query)
        with Session(engine) as session:
            query = text(f"""
                SELECT guide_id, (query <=> :target_vectore ::vector) as distance_score
                FROM {os.getenv('TABLE_NAME')}
                WHERE (query <=> :target_vectore ::vector) < :threshold
                ORDER BY distance_score ASC
                LIMIT 10;
            """)

            result = session.execute(query, {"target_vectore": str(embedded_input), "threshold": 0.3}).fetchall()

            formatted_results = [
                {"guide_id": row.guide_id, "score": row.distance_score} 
                for row in result
            ]
            
            if not formatted_results:
                return "No matching guides found."
                
            return json.dumps(formatted_results)
    except Exception as e:
        print(f"error becuase of {e}")
        result = {"error": str(e)}
        return result

@tool
def save_to_db(query: str, guide_id: str, session_id: str):
    """
    Saves the query to the DB along side the guide_id and session_id, so later we use this instead of doing most of the steps.
    session_id is the thread_id.
    IMPORTANT RULE:
     - You must always pass the `query` as a combined string containing BOTH the device name and the problem. 
     - This tool must be used when you have these three parameters (query, guide_id, session_id)
    """
    try:
        model = get_embedding_model()
        engine = create_engine(
            f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
        )
        embedded_input = model.embed_query(query)
        with Session(engine) as session:
            sql_query = text(f"""
                INSERT INTO {os.getenv("TABLE_NAME")} (query, guide_id, session_id)
                VALUES (:query_vector ::vector, :guide_id, :session_id)
            """)
            session.execute(sql_query, {
                "query_vector": str(embedded_input),
                "guide_id": guide_id,
                "session_id": session_id
            })
            session.commit()
    except Exception as e:
        print("error is due to ", e)
        return []

# print(search("Samsung Galaxy S21"))
# print(steps_follow("164205")[0])