import requests
import json

url = "https://classes.usc.edu/api/Search/Basic?termCode=20263&searchTerm=amst"
response = requests.get(url)
data = response.json()
print(json.dumps(data, indent=2)[:3000])