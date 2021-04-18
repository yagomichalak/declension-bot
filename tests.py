# import requests
# import json


# try:
# 	response = requests.get('https://api.collinsdictionary.com/api/v1/dictionaries')
# except requests.HTTPError as Exception:
# 	print('and I oop')

# else:
# 	data = json.loads(response.text)

# 	print(data)

import requests

word = 'bête'
url = f"https://dicolink.p.rapidapi.com/mot/{word}/definitions"

headers = {
    'x-rapidapi-key': "8b1c4f9464mshc1dbbade96056a1p12c329jsn8efe69c634ba",
    'x-rapidapi-host': "dicolink.p.rapidapi.com"
    }

response = requests.request("GET", url, headers=headers)

print(response.text)