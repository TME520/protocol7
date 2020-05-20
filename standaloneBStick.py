#!/usr/bin/env python3

import datetime
import time
import os
import sys
import random
import urllib.request
import urllib.error
import json
import traceback

try:
    from blinkstick import blinkstick
except ImportError:
    print("Cannot import blinkstick. Run: pip3 install blinkstick")

def bstick_control(bgcolor, fgcolor, dot):
    try:
        # Setting background color first
        for bstick in blinkstick.find_all():
            for currentLED in range (0,32):
                bstick.set_color(channel=0, index=currentLED, name=bgcolor)
        # Then taking care of the foreground (one single dot)
        for bstick in blinkstick.find_all():
            bstick.set_color(channel=0, index=dot, name=fgcolor)
        bstickStatus = bgcolor
    except Exception as e:
        print("[ERROR] Failed to update Blinkstick color.\n", e)
        bstickStatus = "unknown"
    return bstickStatus

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
        bstickStatus = "unknown"
        pass
    return bstickStatus

# Variables declaration
version = "0.2-42"
nrApiKeyHdr = { "X-Api-Key" : os.environ.get('NRAPIKEYHDR') }
snowBase64 = os.environ.get('SNOWBASE64')

firstRun = 0
cycleCntr = 0
hoursCntr = 0
crisisCyclesCntr = 0
oldIncCntr = 0
incCntr = 0
oldVioCntr = 0
vioCntr = 0
oldSnowAltCntr = 0
snowAltCntr = 0
oldSnowIncCntr = 0
snowIncCntr = 0
notificationText = ""
bstickStatus = "empty"
longWait = 4
shortWait = 1
cycleDuration = 60
slackChannel = "cozmo-office-mate"
orangeAlertReason = ""
orangeAlertSent = 0
redAlertSent = 0
dotColor = "blue"

print("BStick automated management v" + version)

# Temporary setting Blinkstick to blue
bstickStatus = update_bstick_color("blue")

# Start main infinite loop
print("Start main infinite loop")
while True:
    # 6 cycles: 1 full followed by 5 fast
    cycleCntr += 1
    if cycleCntr > 6:
        cycleCntr = 1
    print("Cycle: " + str(cycleCntr))

    notificationText = ""
    orangeAlertReason = ""
    dotColor = "blue"

    # Set bstick to green
    if (bstickStatus != "orange" and bstickStatus != "red"):
        bstickStatus = update_bstick_color("green")
        print("Setting bstick to GREEN by default (bstickStatus=" + bstickStatus + ")")
        orangeAlertSent = 0

    # Show time
    currentDT = datetime.datetime.now()
    print(currentDT.strftime("%H:%M"))

    # Show NR incidents count
    # Every minute
    try:
        url = "https://api.newrelic.com/v2/alerts_incidents.json?only_open=true"
        req = urllib.request.Request(url, headers=nrApiKeyHdr)
        response = urllib.request.urlopen(req)
        payload = response.read()
        cont = json.loads(payload.decode('utf-8'))
        oldIncCntr = incCntr
        alertIncCntr = oldIncCntr * 2
        counterA = 0
        for item in cont['incidents']:
            counterA += 1
        incCntr = counterA
        extraInc = 0
        extraIncDir = ""
        if firstRun != 0:
            if (incCntr >= alertIncCntr and incCntr > 8 and bstickStatus != "red"):
                bstickStatus = update_bstick_color("orange")
                orangeAlertReason = "New Relic incidents count doubled since last check."
                print("BStick turns ORANGE: " + orangeAlertReason)
            if incCntr > oldIncCntr:
                extraInc = incCntr - oldIncCntr
                extraIncDir = "+"
                # If the number of NR Incidents increase for
                # 4 consecutive cycles or more, bstick turns orange
                crisisCyclesCntr += 1
                if (crisisCyclesCntr >= 4 and bstickStatus != "red" and incCntr > 8):
                    bstickStatus = update_bstick_color("orange")
                    orangeAlertReason = "New Relic incidents count increased constantly during the last 4 checks."
                    print("BStick turns ORANGE: " + orangeAlertReason)
            elif incCntr < oldIncCntr:
                extraInc = oldIncCntr - incCntr
                extraIncDir = "-"
                crisisCyclesCntr = 0
                if bstickStatus == "orange":
                    bstickStatus = update_bstick_color("green")
                    print("BStick turns GREEN: case A")
            else:
                if bstickStatus == "orange":
                    bstickStatus = update_bstick_color("green")
                    print("BStick turns GREEN: case B")
        notificationText = notificationText + "*New Relic* Incidents: " + str(incCntr) + " (" + extraIncDir + str(extraInc) + ")"
    except urllib.error.HTTPError:
        print("[HTTPError] Failed to refresh NR incidents count. Provider might be down or credentials might have expired.")
        notificationText = ""
        bstickStatus = update_bstick_color("deeppink")
        pass
    except urllib.error.URLError:
        print("[URLError] Failed to refresh NR incidents count. Network connection issue (check Internet access).")
        notificationText = ""
        bstickStatus = update_bstick_color("white")
        # traceback.print_exc()
        pass

    # Show NR violations count
    # Every 5 minutes
    try:
        if cycleCntr == 1:
            url = "https://api.newrelic.com/v2/alerts_violations.json?only_open=true"
            req = urllib.request.Request(url, headers=nrApiKeyHdr)
            response = urllib.request.urlopen(req)
            payload = response.read()
            cont = json.loads(payload.decode('utf-8'))
            oldVioCntr = vioCntr
            counterB = 0
            for item in cont['violations']:
                counterB += 1
            vioCntr = counterB
            extraVio = 0
            extraVioDir = ""
            if firstRun != 0:
                if vioCntr > oldVioCntr:
                    extraVio = vioCntr - oldVioCntr
                    extraVioDir = "+"
                elif vioCntr < oldVioCntr:
                    extraVio = oldVioCntr - vioCntr
                    extraVioDir = "-"
            notificationText = notificationText + " *and* Violations: " + str(vioCntr) + " (" + extraVioDir + str(extraVio) + ")\n"
    except urllib.error.HTTPError:
        print("[HTTPError] Failed to refresh NR violations count. Provider might be down or credentials might have expired.")
        notificationText = ""
        bstickStatus = update_bstick_color("deeppink")
        pass
    except urllib.error.URLError:
        print("[URLError] Failed to refresh NR violations count. Network connection issue (check Internet access).")
        notificationText = ""
        bstickStatus = update_bstick_color("white")
        # traceback.print_exc()
        pass

    # ServiceNow Alerts
    # Every 5 minutes
    try:
        if cycleCntr == 1:
            url = 'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number&sysparm_query=assignment_group=0123456789^active=true^numberSTARTSWITHALT^sys_class_name=u_alert'
            snow_creds_hdr = {'Authorization': 'Basic %s' % snowBase64}
            req = urllib.request.Request(url, headers=snow_creds_hdr)
            response = urllib.request.urlopen(req)
            payload = response.read()
            cont = json.loads(payload.decode('utf-8'))
            oldSnowAltCntr = snowAltCntr
            counterC = 0
            for item in cont['result']:
                counterC += 1
            snowAltCntr = counterC
            extraSnowAlt = 0
            extraSnowAltDir = ""
            if firstRun != 0:
                if snowAltCntr > oldSnowAltCntr:
                    extraSnowAlt = snowAltCntr - oldSnowAltCntr
                    extraSnowAltDir = "+"
                elif snowAltCntr < oldSnowAltCntr:
                    extraSnowAlt = oldSnowAltCntr - snowAltCntr
                    extraSnowAltDir = "-"
            notificationText = notificationText + "*ServiceNow* ALT: " + str(snowAltCntr) + " (" + extraSnowAltDir + str(extraSnowAlt) + ") *and* "
    except urllib.error.HTTPError:
        print("[HTTPError] Failed to refresh ServiceNow alerts count. Provider might be down or credentials might have expired.")
        notificationText = ""
        bstickStatus = update_bstick_color("deeppink")
        pass
    except urllib.error.URLError:
        print("[URLError] Failed to refresh ServiceNow alerts count. Network connection issue (check Internet access).")
        notificationText = ""
        bstickStatus = update_bstick_color("white")
        # traceback.print_exc()
        pass

    # ServiceNow Incidents to process
    # Every 5 minutes
    try:
        if cycleCntr == 1:
            url = 'https://example.service-now.com/api/now/table/incident?sysparm_fields=number&sysparm_query=assignment_group=0123456789^active=true^assigned_to=^stateNOT%20IN3,4,-16,10,6,900,-101,-102,-40^approval!=cancelled^ref_u_alert.u_maintenanceISEMPTY^ORref_u_alert.u_maintenance=false^sys_class_name=incident'
            snow_creds_hdr = {'Authorization': 'Basic %s' % snowBase64}
            req = urllib.request.Request(url, headers=snow_creds_hdr)
            response = urllib.request.urlopen(req)
            payload = response.read()
            cont = json.loads(payload.decode('utf-8'))
            oldSnowIncCntr = snowIncCntr
            counterD = 0
            for item in cont['result']:
                counterD += 1
            snowIncCntr = counterD
            extraSnowInc = 0
            extraSnowIncDir = ""
            if firstRun != 0:
                if snowIncCntr > oldSnowIncCntr:
                    extraSnowInc = snowIncCntr - oldSnowIncCntr
                    extraSnowIncDir = "+"
                elif snowIncCntr < oldSnowIncCntr:
                    extraSnowInc = oldSnowIncCntr - snowIncCntr
                    extraSnowIncDir = "-"
            notificationText = notificationText + "INC: " + str(snowIncCntr) + " (" + extraSnowIncDir + str(extraSnowInc) + ")\n"
    except urllib.error.HTTPError:
        print("[HTTPError] Failed to refresh ServiceNow incidents count. Provider might be down or credentials might have expired.")
        notificationText = ""
        bstickStatus = update_bstick_color("deeppink")
        pass
    except urllib.error.URLError:
        print("[URLError] Failed to refresh ServiceNow incidents count. Network connection issue (check Internet access).")
        notificationText = ""
        bstickStatus = update_bstick_color("white")
        # traceback.print_exc()
        pass

    # Looking for P1 SNow alerts (turn blinkstick red if any)
    # Every minute
    try:
        url = 'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number&sysparm_query=assignment_group=0123456789^numberSTARTSWITHALT^priority=1^active=true^u_maintenanceISEMPTY^ORref_u_alert.u_acknowledged=false^ORref_u_alert.u_maintenance=false^sys_class_name=u_alert'
        snow_creds_hdr = {'Authorization': 'Basic %s' % snowBase64}
        req = urllib.request.Request(url, headers=snow_creds_hdr)
        response = urllib.request.urlopen(req)
        payload = response.read()
        cont = json.loads(payload.decode('utf-8'))
        counterE = 0
        p1AlertsList = ""
        for item in cont['result']:
            counterE += 1
            print(item['number'])
            p1AlertsList = p1AlertsList + item['number'] + " "
        if (counterE != 0 and redAlertSent == 0):
            bstickStatus = update_bstick_color("red")
            print("RED P1 alert (" + str(counterE) + ")")
            redAlertSent = 1
        elif (counterE == 0 and bstickStatus != "orange" and bstickStatus == "red"):
            bstickStatus = update_bstick_color("green")
            print("P1 light: Back to GREEN")
            redAlertSent = 0
    except urllib.error.HTTPError:
        print("[HTTPError] Failed to refresh ServiceNow P1 alerts count. Provider might be down or credentials might have expired.")
        notificationText = ""
        bstickStatus = update_bstick_color("deeppink")
        pass
    except urllib.error.URLError:
        print("[URLError] Failed to refresh ServiceNow P1 alerts count. Network connection issue (check Internet access).")
        notificationText = ""
        bstickStatus = update_bstick_color("white")
        # traceback.print_exc()
        pass

    # Looking for acked or in maintenance P1 SNow alerts
    # Every minute
    if bstickStatus == "green":
        try:
            url = 'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number&sysparm_query=assignment_group=0123456789^numberSTARTSWITHALT^priority=1^active=true^ref_u_alert.u_acknowledged=true^ORref_u_alert.u_maintenance=true^sys_class_name=u_alert'
            snow_creds_hdr = {'Authorization': 'Basic %s' % snowBase64}
            req = urllib.request.Request(url, headers=snow_creds_hdr)
            response = urllib.request.urlopen(req)
            payload = response.read()
            cont = json.loads(payload.decode('utf-8'))
            counterF = 0
            for item in cont['result']:
                counterF += 1
            if counterF != 0:
                dotColor = "deeppink"
        except urllib.error.HTTPError:
            print("[HTTPError] Failed to refresh ServiceNow P1 alerts count. Provider might be down or credentials might have expired.")
            notificationText = ""
            bstickStatus = update_bstick_color("deeppink")
            pass
        except urllib.error.URLError:
            print("[URLError] Failed to refresh ServiceNow P1 alerts count. Network connection issue (check Internet access).")
            notificationText = ""
            bstickStatus = update_bstick_color("white")
            pass

    # Slack
    # Stats published in #cozmo-office-mate
    print(notificationText)

    # Goalkeeper info published in #team-ddc-operations
    if bstickStatus != "red":
        if (bstickStatus == "orange" and orangeAlertSent == 0):
            orangeAlertSent = 1

    if firstRun == 0:
        firstRun = 1

    print("End of cycle. Next cycle in " + str(cycleDuration) + " seconds.")
    print("---")
    # time.sleep(cycleDuration)
    for currentLED in range (0,32):
        bstick_control(bstickStatus, dotColor, currentLED)
        time.sleep(2)
