import requests
url = "https://classes.usc.edu/api/Search/Basic?termCode=20263&searchTerm=AMST+101"
r = requests.get(url, timeout=8)
print(r.status_code)
print(r.json())