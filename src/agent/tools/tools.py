import requests as req


def search(device_name: str) -> list:
    """
    Search for the device and the problem
    """
    url = "https://www.ifixit.com/api/2.0/search/"
    parsed_device_name = device_name.replace(" ", "%20")
    request_url = f"{url}{parsed_device_name}"
    try:
        response = req.get(request_url)
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

print(search("Samsung Galaxy S21"))