import urllib.request
import json
import time

try:
    from blinkstick import blinkstick
except ImportError:
    print("Cannot import blinkstick. Run: pip3 install blinkstick")

def update_bstick_color(bstickColor):
    try:
        for bstick in blinkstick.find_all():
            for currentLED in range (0,32):
                bstick.set_color(channel=0, index=currentLED, name=bstickColor)
                time.sleep(0.1)
        bstickStatus = bstickColor
        print("bstickStatus=" + bstickStatus)
    except Exception as e:
        print("[ERROR] Failed to update Blinkstick color.\n", e)

snowBase64 = "AAA"
redAlertSent = 0
bstickStatus = "green"

url = 'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number&sysparm_query=assignment_group=0123456789^numberSTARTSWITHALT^priority=1^active=true^u_maintenanceISEMPTY^ORu_maintenance=false^sys_class_name=u_alert'

snow_creds_hdr = {'Authorization': 'Basic %s' % snowBase64}
req = urllib.request.Request(url, headers=snow_creds_hdr)
response = urllib.request.urlopen(req)
payload = response.read()
cont = json.loads(payload.decode('utf-8'))
counterE = 0

for item in cont['result']:
    counterE += 1
    # print(item)
    print("/snow " + item['number'])
if (counterE != 0 and redAlertSent == 0):
    update_bstick_color("red")
    bstickStatus = "red"
    print("RED P1 alert (" + str(counterE) + ")")
    redAlertSent = 1
elif (bstickStatus != "orange" and bstickStatus == "red"):
    update_bstick_color("green")
    bstickStatus = "green"
    print("P1 light: Back to GREEN")
    redAlertSent = 0
