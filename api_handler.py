import urllib.request
import json

class APIClient():
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    def fetch_data(self, endpoint="", params = None):
        try:
            # Construct the full URL
            query_string = f"?{urllib.parse.urlencode(params)}" if params else ""
            url = f"{self.base_url}{endpoint}{query_string}"

            # Add the API key to the request headers
            headers = {
                'X-Api-Version': '1.5',
                'Cache-Control': 'no-cache',
                'Ocp-Apim-Subscription-Key': '5044b6436a6b4814b9689cd6fac542f0',
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
