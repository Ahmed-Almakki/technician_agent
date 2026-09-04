import requests as req
from langchain_core.tools import tool
import json


@tool
def search(device_name: str) -> list:
    """
    Search for the correct device name in the ifixit database using the provided device name.
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
def categories(device_name: str) -> list:
    """
    Fetches the categories for a given device name from the iFixit API.
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
def steps_follow(guide_id: str):
    """
    Fetches the steps for a given guide ID from the iFixit API.
    Use the ouptut of this function to provide the user with step by step instructions for their device repair.
    the ouptut of this function is a list of dictionaries, each dictionary contains the title and text steps and images for each step.
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
        return json.dumps(result)
    except req.RequestException as e:
        print(f"Error occurred while fetching data: {e}")
        res = {"error": str(e)}
        return json.dumps(res)


# print(search("Samsung Galaxy S21"))
# print(steps_follow("164205")[0])