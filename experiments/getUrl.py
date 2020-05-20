import urllib.request
import json
url = "http://api.openweathermap.org/data/2.5/weather?APPID=aaaabbbbccccdddd&id=0123456789&units=metric"

req = urllib.request.Request(url)
response = urllib.request.urlopen(req)
payload = response.read()
cont = json.loads(payload.decode('utf-8'))
counter = 0

print(str(payload))
print("------")
print(str(response.status))
print("------")
print(str(response.__dict__))
print("------")
print(str(cont))
print("------")

print("******")
# Parsing json
for key, value in cont.items():
#    counter += 1
    print("key: ", key, "value: ", value)
    print("----")

print("******")
# Parsing json
for item in cont['weather']:
#    counter += 1
    print(str(item['id']), item['main'], item['description'])
    print("----")

print("******")
#print (json.dumps(cont, indent=4, sort_keys=True))
#print("Number of open New Relic incidents: ", counter)
