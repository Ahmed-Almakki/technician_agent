import requests as req
from langchain_core.tools import tool

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
            return []
        
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

    return devices

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
            return []
        
        response.raise_for_status()
        res = response.json()

        result = res.get('guides', [])

        if result:
            categories = [{'guideid': item['guideid'], 'category': item['category'], 'title': item['title']} for item in result]
        else:
            categories = []

    except req.RequestException as e:
        print(f"Error occurred while fetching data: {e}")
        res = {"error": str(e)}

    return categories

@tool
def steps_follow(guide_id: str):
    """
    Fetches the steps for a given guide ID from the iFixit API.
    """
    url = "https://www.ifixit.com/api/2.0/guides/"
    request_url = f"{url}{guide_id}"
    try:
        response = req.get(request_url)

        if response.status_code == 404:
            return []
        
        response.raise_for_status()
        res = response.json()

        steps = res.get('steps', [])
        result = []
        if len(steps) > 0:
            for item in steps:
                details= {}
                details['title'] = item['title']

                text = [step['text_raw'] for step in item['lines']]
                details['text'] = text

                images = [img['thumbnail'] for img in item['media']['data']]
                details['images'] = images
                result.append(details)
        return result
    except req.RequestException as e:
        print(f"Error occurred while fetching data: {e}")
        res = {"error": str(e)}
        return []


# print(search("Samsung Galaxy S21"))
# print(steps_follow("164205")[0])