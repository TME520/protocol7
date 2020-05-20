import requests
import os
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Content-Type': 'multipart/form-data',
    'Cache-Control': 'no-cache'
}

multipart_encoder = MultipartEncoder(
    fields = {
        'username': '',
        'password': '',
        'country': 'fr'
    }
)

headers['Content-Type'] = multipart_encoder.content_type

# response = requests.post('https://www.example.com/login', data=multipart_encoder, json=None, headers=headers)
response = requests.post('https://www.example.com/login', data=multipart_encoder, json=None, headers=headers)

print(f'multipart_encoder: {multipart_encoder}')
print(f'headers: {headers}')
print(f'response: {response}')
print(f'HTTP status: {response.status_code}')
# print(response.text)
canard = json.loads(response.text)
print(f'\nJSON payload: {canard}')
print(f'\nToken: {canard["data"]["token"]}')
