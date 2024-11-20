import urllib.request
import json

class APIClient():
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def fetch_data(self, endpoint):
        try:
            # Construct the full URL
            url = f"{self.base_url}{endpoint}"

            # Add the API key to the request headers
            headers = {
                'Cache-Control': 'no-cache',
                'Ocp-Apim-Subscription-Key': 'a4e9e43ebf06456a86523532d082ed4b',
            }

            # Create the request with headers
            req = urllib.request.Request(url, headers=headers)

            # Send the request and get the response
            response = urllib.request.urlopen(req)

            # Parse the response as JSON
            data = json.load(response)
            return data
        except Exception as e:
            raise Exception(f"Failed to fetch data: {str(e)}")