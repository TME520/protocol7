import urllib.request
import json

snowBase64 = ''

url = 'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number&sysparm_query=assignment_group=0123456789^active=true^numberSTARTSWITHALT^sys_class_name=u_alert'
snow_creds_hdr = {'Authorization': 'Basic %s' % (snowBase64)}
print(snow_creds_hdr)
req = urllib.request.Request(url, headers=snow_creds_hdr)
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

for item in cont['result']:
    counter += 1
    print("Alert number:", item['number'])

print('There are ' + str(counter) + ' ServiceNow ALT open.')
