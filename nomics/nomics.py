import requests
from urllib.parse import urlencode
import json


url = "https://api.nomics.com/v1/"
api_key = "f348b9100f67d8eb4c5cfd89cd16d999"

query_object = {
    "key": api_key,
    "ids": "BTC",
    "convert": "USD"
}

qs = urlencode(query_object)
print(qs)

r = requests.get(url+"currencies/ticker?"+qs)
# json_object = r.json()[0]
data_object = r.json()[0]

print(data_object)
