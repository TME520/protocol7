#!/usr/bin/env python3

# Cozmo Office Mate - Special showcase version

import datetime
import time
import cozmo
import os
import sys
import random
import urllib.request
import urllib.error
import json
import traceback
import boto3
import colorama
from colorama import Fore, Style

try:
    from slackclient import SlackClient
except ImportError:
    print('Cannot import SlackClient. Run: pip3 install slackclient')

try:
    from blinkstick import blinkstick
except ImportError:
    print('Cannot import blinkstick. Run: pip3 install blinkstick')

try:
    import notify2
except ImportError:
    print('Cannot import notify2, we are not running Linux, right ?')
    pass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit('Cannot import from PIL: Do `pip3 install --user Pillow` to install')

# Path to data folder (contains ML stuff)
cb1DataFolder = os.environ.get('CB1DATAFOLDER')
if not os.path.exists(cb1DataFolder):
    os.makedirs(cb1DataFolder)

def writeDataToFile(targetFile,dataToWrite,successMsg,failureMsg):
    newCB1File = open(targetFile,'w')
    newCB1File.write(dataToWrite)
    newCB1File.close()
    print(successMsg)

def dynamodbDeleteTable(databaseURL, tableName):
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToDelete = dynamodb.Table(tableName)
        tableToDelete.delete()
        response = 'Deletion successful'
    except Exception as e:
        print('[ERROR] Failed to delete database table ' + tableName + '.\n', e)
        response = 'Table deletion failed'
        traceback.print_exc()
        pass
    return response

def dynamodbListTableItems(databaseURL, tableName):
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToList = dynamodb.Table(tableName)
        tableToList.scan()
        response = tableToList.scan()
    except Exception as e:
        print('[ERROR] Failed to list content of database table ' + tableName + '.\n', e)
        response = 'Table listing failed'
        traceback.print_exc()
        pass
    return response

def dynamodbReadFromTable(databaseURL, tableName):
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        configItems = []
        if tableName == 'cfg_nrvio_track':
            tableToRead = dynamodb.Table(tableName)
            x = tableToRead.scan()
            for i in x['Items']:
                # print(i['label'])
                configItems.append(i['label'])
        response = 'Configuration data successfully loaded.'
    except Exception as e:
        print('[ERROR] Failed to load configuration data from table ' + tableName + '.\n', e)
        response = 'Failed to load data'
        traceback.print_exc()
        pass
    return configItems

def dynamodbProvisionTable(databaseURL, tableName):
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        if tableName == 'cfg_nrvio_track':
            tableToProvision = dynamodb.Table(tableName)
            tableToProvision.put_item(
            Item=json.loads('{"label":"Fullest disk"}')
            )
            tableToProvision.put_item(
            Item=json.loads('{"label":"High Disk Usage"}')
            )
            tableToProvision.put_item(
            Item=json.loads('{"label":"Layer 7 Disk Usage"}')
            )
        response = 'Provisioning successful'
    except Exception as e:
        print('[ERROR] Failed to create database table ' + tableName + '.\n', e)
        response = 'Table provisioning failed'
        traceback.print_exc()
        pass
    return response

def dynamodbCreateTable(databaseURL, tableName):
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        if tableName == 'cfg_nrvio_track':
            table = dynamodb.create_table(
                TableName=tableName,
                KeySchema=[
                    {
                        'AttributeName': 'label',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'label',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=tableName)
            print(table.item_count)
            response = 'Table created'
        elif tableName == 'p7_interapp_msg':
            table = dynamodb.create_table(
                TableName=tableName,
                KeySchema=[
                    {
                        'AttributeName': 'action_name',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'action_status',
                        'KeyType': 'RANGE'  #Sort key
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'action_name',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'action_status',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.meta.client.get_waiter('table_exists').wait(TableName=tableName)
            print(table.item_count)
            response = 'Table created'
    except Exception as e:
        print('[ERROR] Failed to create database table ' + tableName + '.\n', e)
        response = 'Table creation failed'
        traceback.print_exc()
        pass
    return response

def dynamodbTableCheck(databaseURL, tableName):
    try:
        dynamodb = boto3.client('dynamodb', endpoint_url=databaseURL)
        response = dynamodb.describe_table(TableName=tableName)
    # except dynamodb.exceptions.ResourceNotFoundException:
    except Exception as e:
        print('[DEBUG] DynamoDB table ' + tableName + ' not found')
        response = 'Table not found'
        # traceback.print_exc()
        pass
    return str(response)

def callURL(url2call, creds):
    try:
        url = url2call
        req = urllib.request.Request(url, headers=creds)
        response = urllib.request.urlopen(req)
        payload = response.read()
        return payload
    except urllib.error.HTTPError:
        print('[HTTPError] Failed to call ' + str(url) + '\nProvider might be down or credentials might have expired.')
        return 'HTTPERROR'
        pass
    except urllib.error.URLError:
        print('[URLError] Failed to call ' + str(url) + '\nNetwork connection issue (check Internet access).')
        return "URLERROR"
        pass

def post_message_on_slack(slackLogChannel, slackMessage, slackEmoji):
    try:
        slackToken = os.environ.get('SLACKTOKEN')
        sc = SlackClient(slackToken)
        sc.api_call(
          'chat.postMessage',
          channel=slackLogChannel,
          text=slackMessage,
          as_user='false',
          username='Cozmo Office Mate',
          icon_emoji=slackEmoji
        )
        print('[post_message_on_slack] ' + slackLogChannel + ': ' + slackMessage)
    except Exception as e:
        print('[ERROR] Failed to post message to Slack.\n', e)
        pass

def bstick_control(bgcolor, fgcolor, dot):
    # This function drives the BlinkStick Flex (32 LEDs)
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
        print('[ERROR] Failed to update Blinkstick color.\n', e)
        bstickStatus = 'unknown'
        traceback.print_exc()
    return bstickStatus

def update_bstick_color(bstickColor):
    # This function drives the BlinkStick Flex (32 LEDs)
    try:
        for bstick in blinkstick.find_all():
            for currentLED in range (0,32):
                bstick.set_color(channel=0, index=currentLED, name=bstickColor)
                time.sleep(0.1)
        bstickStatus = bstickColor
    except Exception as e:
        print('[ERROR] Failed to update Blinkstick color.\n', e)
        bstickStatus = 'unknown'
        traceback.print_exc()
        pass
    return bstickStatus

def update_bstick_nano(bgcolor, fgcolor, mode):
    # This function drives the BlinkStick Nano (two LEDs, one on each side)
    if mode == 'normal':
        try:
            for bstick in blinkstick.find_all():
                bstick.set_color(channel=0, index=1, name=bgcolor)
            time.sleep(0.1)
            bstickStatus = bgcolor
        except Exception as e:
            print('[ERROR] Failed to update Blinkstick color.\n', e)
            bstickStatus = 'unknown'
            traceback.print_exc()
            pass
    elif mode == 'flash':
        # print("BStick is in Flash mode")
        try:
            for bstick in blinkstick.find_all():
                bstick.set_color(channel=0, index=1, name=bgcolor)
                bstick.blink(channel=0, index=0, name=fgcolor, repeats=1, delay=500)
            time.sleep(0.1)
            bstickStatus = bgcolor
        except Exception as e:
            print('[ERROR] Failed to update Blinkstick color.\n', e)
            bstickStatus = 'unknown'
            traceback.print_exc()
            pass

    return bstickStatus

def cozmo_program(robot: cozmo.robot.Robot):
    # Variables declaration
    version = '0.38 Special showcase edition'
    greetingSentences = ['Hi folks !','Hey ! I am back !','Hi ! How you doing ?','Cozmo, ready !']
    nrApiKeyHdr = { 'X-Api-Key' : os.environ.get('NRAPIKEYHDR') }
    snowBase64 = os.environ.get('SNOWBASE64')
    databaseURL = os.environ.get('DYNAMODBURL')

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
    slackStatusText = ''
    slackAlertText = ''
    robotText = ''
    bstickStatus = 'empty'
    longWait = 4
    shortWait = 1
    cycleDuration = 60
    slackLogChannel = 'cozmo-office-mate'
    slackAlertChannel = 'team-ddc-operations'
    slackGKAdviceChannel = 'peng-goalkeeper'
    redAlert = 0
    redAlertReason = ""
    redAlertSent = 0
    orangeAlert = 0
    orangeAlertReason = ""
    orangeAlertSent = 0
    greenCounter = 0
    yellowCounter = 0
    orangeCounter = 0
    redCounter = 0
    blueCounter = 0
    whiteCounter = 0
    pinkCounter = 0
    bottomLightColor='blue'
    topLightColor = 'blue'
    urgencyWords = ['ombudsman','court','tribunal','urgent','emergency','angry','dissatisfied','escalation','attorney','lawyer','threat', 'extreme', 'annoy', 'complain', 'insult', 'upset']
    snowStatesToExclude = ['3','4','-16','10','6','900','-101','-102','-40']
    assignmentGroupID = 'a4a7b6f6f9333000c9094e564e146550'

    urlList = {
        'NRINCCOUNT':{'url':'https://api.newrelic.com/v2/alerts_incidents.json?only_open=true','credentials':nrApiKeyHdr,'payload':'EMPTY'},
        'NRVIOCOUNT':{'url':'https://api.newrelic.com/v2/alerts_violations.json?only_open=true','credentials':nrApiKeyHdr,'payload':'EMPTY'},
        'SNALTCOUNT':{'url':'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^numberSTARTSWITHALT^sys_class_name=u_alert','credentials':{'Authorization': 'Basic %s' % snowBase64},'payload':'EMPTY'},
        'SNINCCOUNT':{'url':'https://example.service-now.com/api/now/table/incident?sysparm_fields=number,short_description,description,sys_id,state&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^sys_class_name=incident','credentials':{'Authorization': 'Basic %s' % snowBase64},'payload':'EMPTY'},
        'SNREQCOUNT':{'url':'https://example.service-now.com/api/now/table/u_request?sysparm_fields=number,state&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true','credentials':{'Authorization': 'Basic %s' % snowBase64},'payload':'EMPTY'},
        'SNCHGCOUNT':{'url':'https://example.service-now.com/api/now/table/change_request?sysparm_fields=number,state&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^sys_class_name=change_request','credentials':{'Authorization': 'Basic %s' % snowBase64},'payload':'EMPTY'},
        'SNP1COUNT':{'url':'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number,short_description,sys_id&sysparm_query=assignment_group=' + assignmentGroupID + '^numberSTARTSWITHALT^priority=1^active=true^u_maintenanceISEMPTY^ORref_u_alert.u_acknowledged=false^ORref_u_alert.u_maintenance=false^sys_class_name=u_alert','credentials':{'Authorization': 'Basic %s' % snowBase64},'payload':'EMPTY'},
        'SNACKMAINTCOUNT':{'url':'https://example.service-now.com/api/now/table/u_alert?sysparm_fields=number&sysparm_query=assignment_group=' + assignmentGroupID + '^numberSTARTSWITHALT^priority=1^active=true^ref_u_alert.u_acknowledged=true^ORref_u_alert.u_maintenance=true^sys_class_name=u_alert','credentials':{'Authorization': 'Basic %s' % snowBase64},'payload':'EMPTY'}
    }

    # Temporary setting lights to blue
    # bstickStatus = update_bstick_nano("blue", "blue", "normal")
    bstickStatus = update_bstick_color('blue')
    robot.set_all_backpack_lights(cozmo.lights.blue_light)
    time.sleep(shortWait)

    # Reset head and lift position
    # print("Reset head and lift position")
    robot.set_head_angle(cozmo.robot.MIN_HEAD_ANGLE).wait_for_completed()
    robot.set_lift_height(0.0).wait_for_completed()

    # Head up
    # print("Head up")
    robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

    # Checking DB
    # Table: cfg_nrvio_track
    # Content: A list of New Relic violations to watch after
    nrVioTrackList = []
    # robot.say_text('Checking database').wait_for_completed()
    # time.sleep(shortWait)
    if dynamodbTableCheck(databaseURL, 'cfg_nrvio_track') == 'Table not found':
        # Table missing - creating
        if dynamodbCreateTable(databaseURL, 'cfg_nrvio_track') == 'Table created':
            # Table created - provisioning
            if dynamodbProvisionTable(databaseURL, 'cfg_nrvio_track') == 'Provisioning successful':
                # print('')
                # print(dynamodbListTableItems(databaseURL, 'cfg_nrvio_track'))
                nrVioTrackList = dynamodbReadFromTable(databaseURL, 'cfg_nrvio_track')
            else:
                print('Provisioning of table cfg_nrvio_track failed :-(')
        else:
            print('Creation of table cfg_nrvio_track failed :-(')
    else:
        print('')
        nrVioTrackList = dynamodbReadFromTable(databaseURL, 'cfg_nrvio_track')

    if dynamodbDeleteTable(databaseURL, 'cfg_nrvio_track'):
        print('')
    else:
        print('Table cfg_nrvio_track deletion failed :-(')
    
    # Table: p7_interapp_msg
    # Content: Messages exchanged between P7 components / apps
    if dynamodbTableCheck(databaseURL, 'p7_interapp_msg') == 'Table not found':
        # Table missing - creating
        if dynamodbCreateTable(databaseURL, 'p7_interapp_msg') == 'Table created':
            # Table created - provisioning
            if dynamodbProvisionTable(databaseURL, 'p7_interapp_msg') == 'Provisioning successful':
                # print('New table p7_interapp_msg created and provisioned.')
                # print(dynamodbListTableItems(databaseURL, 'p7_interapp_msg'))
                p7MsgList = dynamodbReadFromTable(databaseURL, 'p7_interapp_msg')
            else:
                print('Provisioning of table p7_interapp_msg failed :-(')
        else:
            print('Creation of table p7_interapp_msg failed :-(')
    else:
        # print('Table p7_interapp_msg exists, nothing to do.')
        p7MsgList = dynamodbReadFromTable(databaseURL, 'p7_interapp_msg')

    if dynamodbDeleteTable(databaseURL, 'p7_interapp_msg'):
        print('')
    else:
        print('Table p7_interapp_msg deletion failed :-(')


    ############################
    # Start main loop          #
    ############################
    os.system('clear')
    print(Fore.RED + '#############################')
    print(Fore.RED + '# Lights & Magic monitoring #')
    print(Fore.RED + '#############################')
    print(Fore.GREEN + '')
    while True:
        # 6 cycles
        currentDT = datetime.datetime.now()
        currentDay = currentDT.strftime("%A")
        currentMonth = currentDT.strftime("%B")
        cycleCntr += 1
        if cycleCntr > 6:
            cycleCntr = 1
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.BLUE + 'Cycle: ' + str(cycleCntr) + ' - ' + currentDT.strftime("%H:%M"))
        print(Fore.GREEN + '')
        robot.say_text('I am happy to be a part of Hack Days 2019. I hope you enjoy this live showcase.').wait_for_completed()
        time.sleep(shortWait)
        robot.say_text('If I crash, please look away.').wait_for_completed()
        time.sleep(shortWait)

        # Say date and time every hour
        hoursCntr += 1
        if hoursCntr > 60:
            hoursCntr = 0

        greenCounter = 0
        yellowCounter = 0
        orangeCounter = 0
        redCounter = 0
        blueCounter = 0
        whiteCounter = 0
        pinkCounter = 0
        slackStatusText = ''
        slackAlertText = ''
        publishNewGKAdvice = 'no'
        slackGKAdvice = '--- *' + currentDT.strftime("%H:%M") + '* ---\n'
        robotText = ''
        slackMsgLine1 = '--- *' + currentDT.strftime("%H:%M") + '* ---'
        slackMsgLine2 = ''
        slackMsgLine3 = ''
        slackMsgLine4 = ''
        slackMsgLine5 = ''
        slackMsgLine6 = ''

        ##############################
        # Refresh all data in one go #
        ##############################
        robot.say_text('I will now query New Relic and Service Now in order to see if everything is alright.').wait_for_completed()
        time.sleep(shortWait)
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.GREEN + '\nI will now query New Relic and Service Now in order to see if everything is alright.')
        for currentItem in urlList:
            print('Calling ' + urlList[currentItem]['url'])
            payload = callURL(str(urlList[currentItem]['url']), urlList[currentItem]['credentials'])
            if (payload != 'HTTPERROR') and (payload != 'URLERROR'):
                urlList[currentItem]['payload'] = payload
            elif payload == 'HTTPERROR':
                pinkCounter += 1
                urlList[currentItem]['payload'] = 'HTTPERROR'
                print('[ERROR] HTTPERROR (pink light) for ' + str(urlList[currentItem]['url']))
            elif payload == 'URLERROR':
                whiteCounter += 1
                urlList[currentItem]['payload'] = 'URLERROR'
                print('[ERROR] URLERROR (white light) for ' + str(urlList[currentItem]['url']))

        robot.say_text('Now that I am done retrieving data from New Relic and Service Now, I will analyze it.').wait_for_completed()
        time.sleep(shortWait)
        
        # SNP1COUNT - process
        # Looking for P1 SNow alerts (turn lights red immediately if any)
        # Every minute
        robot.say_text('Looking for P1 alerts.').wait_for_completed()
        time.sleep(shortWait)
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.GREEN + '\nLooking for P1 alerts (turn lights red immediately if any).')
        payload = urlList['SNP1COUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            cont = json.loads(payload.decode('utf-8'))
            counterE = 0
            p1AlertsList = ''
            for item in cont['result']:
                counterE += 1
                # print(item['number'])
                p1AlertsList = p1AlertsList + '\n- ' + item['number'] + ' ' + item['short_description'] + ' ' + 'https://example.service-now.com/nav_to.do?uri=u_alert.do?sys_id=' + item['sys_id']
            if (counterE != 0 and redAlertSent == 0):
                redAlert = 1
                redCounter += 1
                slackMsgLine2 = '*P1 ALT currently open*: ' + str(counterE) + '\n' + p1AlertsList
                slackAlertText = slackAlertText + '*P1 RED alert*: \n' + p1AlertsList + '\n\n[*MIM*: 1 300 779 601]'
            elif (counterE == 0 and redAlert == 1):
                redAlert = 0
                redAlertSent = 0
                greenCounter += 1
                slackMsgLine2 = '*P1 light*: Back to GREEN'
                slackAlertText = slackAlertText + 'End of P1 RED alert. Back to GREEN.'
                post_message_on_slack(slackGKAdviceChannel, slackAlertText, ':cocgreen1:')

        # SNACKMAINTCOUNT - process
        # Looking for acked or in maintenance P1 SNow alerts
        # Every minute
        robot.say_text('Looking for acked or in maintenance P1.').wait_for_completed()
        time.sleep(shortWait)
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.GREEN + '\nLooking for acked or in maintenance P1.')
        payload = urlList['SNACKMAINTCOUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            yellowCounter = 0
            cont = json.loads(payload.decode('utf-8'))
            counterF = 0
            for item in cont['result']:
                counterF += 1
            if counterF != 0:
                yellowCounter += 1
                robotText = robotText + str(counterF) + ' acknowledged P 1, '
                slackMsgLine2 = slackMsgLine2 + "\nThere's " + str(counterF) + ' acknowledged P1 alerts.'
                publishNewGKAdvice = 'yes'

        # SNALTCOUNT - process
        # ServiceNow Alerts
        # Every minute
        robot.say_text('Counting Service Now alerts.').wait_for_completed()
        time.sleep(shortWait)
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.GREEN + '\nCounting ServiceNow alerts.')
        payload = urlList['SNALTCOUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            cont = json.loads(payload.decode('utf-8'))
            oldSnowAltCntr = snowAltCntr
            counterC = 0
            for item in cont['result']:
                counterC += 1
            snowAltCntr = counterC
            extraSnowAlt = 0
            extraSnowAltDir = ''
            if firstRun != 0:
                if snowAltCntr > oldSnowAltCntr:
                    robotText = robotText + str(snowAltCntr) + ' Service Now alerts, '
                    extraSnowAlt = snowAltCntr - oldSnowAltCntr
                    robotText = robotText + "It's " + str(extraSnowAlt) + " more, "
                    extraSnowAltDir = '+'
                    publishNewGKAdvice = 'yes'
                elif snowAltCntr < oldSnowAltCntr:
                    extraSnowAlt = oldSnowAltCntr - snowAltCntr
                    extraSnowAltDir = '-'
                    robotText = robotText + "It's " + str(extraSnowAlt) + " less, "
            slackMsgLine3 = '*ServiceNow ALT*: ' + str(snowAltCntr) + ' (' + extraSnowAltDir + str(extraSnowAlt) + ') '

        # ServiceNow INC, REQ & CHG - process
        # Every minute
        # SNINCCOUNT
        # INC
        robot.say_text('Counting Service Now incidents, requests and change requests.').wait_for_completed()
        time.sleep(shortWait)
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.GREEN + '\nCounting ServiceNow incidents, requests and change requests.')
        payload = urlList['SNINCCOUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            cont = json.loads(payload.decode('utf-8'))
            oldSnowIncCntr = snowIncCntr
            counterD = 0
            for item in cont['result']:
                if item['state'] not in snowStatesToExclude:
                    counterD += 1
                    pathToCB1File = cb1DataFolder + item['number'] + '.cb1'
                    if not os.path.isfile(pathToCB1File):
                        writeDataToFile(pathToCB1File,item['description'],'Incident description saved in ' + pathToCB1File,'')
                        # Checking INC description for a few keywords expressing emergency
                        for currentWord in urgencyWords:
                            if (currentWord in item['description'].lower()) or (currentWord in item['short_description'].lower()):
                                print('Attention required for ServiceNow incident ' + item['number'] + ' (' + currentWord + ')')
                                slackMsgLine6 = slackMsgLine6 + '\n- Please check ' + item['number'] + ' - Reason: [' + currentWord + '] found in ticket ' + ' https://example.service-now.com/nav_to.do?uri=incident.do?sys_id=' + item['sys_id']
                                publishNewGKAdvice = 'yes'
            snowIncCntr = counterD
            extraSnowInc = 0
            extraSnowIncDir = ''
            if firstRun != 0:
                if snowIncCntr > oldSnowIncCntr:
                    robotText = robotText + str(snowIncCntr) + ' Service Now incidents, '
                    extraSnowInc = snowIncCntr - oldSnowIncCntr
                    robotText = robotText + "It's " + str(extraSnowInc) + " more, "
                    extraSnowIncDir = "+"
                    if snowIncCntr > 20:
                        publishNewGKAdvice = 'yes'
                elif snowIncCntr < oldSnowIncCntr:
                    extraSnowInc = oldSnowIncCntr - snowIncCntr
                    robotText = robotText + "It's " + str(extraSnowInc) + " less, "
                    extraSnowIncDir = '-'
            slackMsgLine3 = slackMsgLine3 + '*INC*: ' + str(snowIncCntr) + ' (' + extraSnowIncDir + str(extraSnowInc) + ')  '
        # SNREQCOUNT
        # REQ
        reqCount = 0
        payload = urlList['SNREQCOUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            cont = json.loads(payload.decode('utf-8'))
            for item in cont['result']:
                if item['state'] not in snowStatesToExclude:
                    reqCount += 1
            robotText = robotText + "There's " + str(reqCount) + " Service Now requests waiting to be processed."
            slackMsgLine3 = slackMsgLine3 + '*REQ*: ' + str(reqCount) + ' '
        # SNCHGCOUNT
        # CHG
        chgCount = 0
        payload = urlList['SNCHGCOUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            cont = json.loads(payload.decode('utf-8'))
            for item in cont['result']:
                print('Current item: ' + item['number'] + '(' + str(item['state']) + ')')
                if item['state'] not in snowStatesToExclude:
                    chgCount += 1
            robotText = robotText + "There's " + str(chgCount) + " Service Now changes waiting to be processed."
            slackMsgLine3 = slackMsgLine3 + '*CHG*: ' + str(chgCount)

        # NRINCCOUNT - process
        # Show NR incidents count
        # Every minute
        robot.say_text('Counting the number of New Relic incidents.').wait_for_completed()
        time.sleep(shortWait)
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.GREEN + '\nCounting the number of New Relic incidents.')
        payload = urlList['NRINCCOUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            cont = json.loads(payload.decode('utf-8'))
            oldIncCntr = incCntr
            alertIncCntr = oldIncCntr * 2
            counterA = 0
            for item in cont['incidents']:
                counterA += 1
            incCntr = counterA
            extraInc = 0
            extraIncDir = ''
            if firstRun != 0:
                if incCntr > oldIncCntr:
                    robotText = robotText + str(incCntr) + ' New Relic incidents, '
                    if (incCntr >= alertIncCntr and incCntr > 8 and redAlert == 0):
                        orangeAlert = 1
                        orangeCounter += 1
                        slackAlertText = 'Attention please, orange alert. New Relic incidents count doubled since last check.'
                    extraInc = incCntr - oldIncCntr
                    robotText = robotText + "It's " + str(extraInc) + " more, "
                    extraIncDir = '+'
                    # If the number of NR Incidents increase for
                    # 4 consecutive cycles or more, bstick turns orange
                    crisisCyclesCntr += 1
                    publishNewGKAdvice = 'yes'
                    if (crisisCyclesCntr >= 4 and incCntr > 8):
                        orangeAlert = 1
                        orangeCounter += 1
                        slackAlertText = 'Attention please, orange alert. New Relic incidents count increased constantly during the last 4 checks.'
                elif incCntr < oldIncCntr:
                    extraInc = oldIncCntr - incCntr
                    robotText = robotText + "It's " + str(extraInc) + " less, "
                    extraIncDir = '-'
                    crisisCyclesCntr = 0
                    greenCounter += 1
                    orangeAlert = 0
                    orangeAlertSent = 0
            slackMsgLine4 = '*NR Incidents*: ' + str(incCntr) + ' (' + extraIncDir + str(extraInc) + ') '

        # NRVIOCOUNT - process
        # Show NR violations count
        # Every minute
        robot.say_text('Counting the number of New Relic violations.').wait_for_completed()
        time.sleep(shortWait)
        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.GREEN + '\nCounting the number of New Relic violations.')
        payload = urlList['NRVIOCOUNT']['payload']
        if (payload != 'URLERROR') and (payload != 'HTTPERROR'):
            cont = json.loads(payload.decode('utf-8'))
            oldVioCntr = vioCntr
            counterB = 0
            fsToCleanCounter = 0
            fsToCleanEntities = ""
            for item in cont['violations']:
                counterB += 1
                # print('NR violation: ' + str(item['label']) + ' ---> ' + str(item['entity']['name']))
                for currentNRVio in nrVioTrackList:
                    if currentNRVio in str(item['label']):
                        fsToCleanCounter += 1
                        fsToCleanEntities = fsToCleanEntities + str(item['entity']['name']) + ' '
            if cycleCntr == 1:
                if fsToCleanCounter != 0:
                    robot.say_text('You have to clean ' + str(fsToCleanCounter) + 'filesystems.').wait_for_completed()
                    print(str(fsToCleanCounter) + ' filesystems to clean (' + fsToCleanEntities + ').')
                    slackMsgLine6 = slackMsgLine6 + '\n-' + str(fsToCleanCounter) + ' filesystems to clean (' + fsToCleanEntities + ').'
                    publishNewGKAdvice = 'yes'
            vioCntr = counterB
            extraVio = 0
            extraVioDir = ''
            if firstRun != 0:
                if vioCntr > oldVioCntr:
                    robotText = robotText + str(vioCntr) + ' New Relic violations, '
                    extraVio = vioCntr - oldVioCntr
                    robotText = robotText + "It's " + str(extraVio) + " more, "
                    extraVioDir = '+'
                elif vioCntr < oldVioCntr:
                    extraVio = oldVioCntr - vioCntr
                    robotText = robotText + "It's " + str(extraVio) + " less, "
                    extraVioDir = '-'
            slackMsgLine4 = slackMsgLine4 + '*NR Violations*: ' + str(vioCntr) + ' (' + extraVioDir + str(extraVio) + ')'

        # Slack message in #cozmo-office-mate
        # Every minute
        # Stats published in #cozmo-office-mate
        if slackMsgLine1 != '':
            slackMsgLine1 = slackMsgLine1 + '\n'
        if slackMsgLine2 != '':
            slackMsgLine2 = slackMsgLine2 + '\n'
        if slackMsgLine3 != '':
            slackMsgLine3 = slackMsgLine3 + '\n'
        if slackMsgLine4 != '':
            slackMsgLine4 = slackMsgLine4 + '\n'
        if slackMsgLine5 != '':
            slackMsgLine5 = slackMsgLine5 + '\n'
        if slackMsgLine6 != '':
            slackMsgLine6 = slackMsgLine6 + '\n'
        slackStatusText = slackMsgLine1 + slackMsgLine2 + slackMsgLine3 + slackMsgLine4 + slackMsgLine5 + slackMsgLine6
        post_message_on_slack(slackLogChannel, slackStatusText, ':coc1:')
        if publishNewGKAdvice == 'yes':
            post_message_on_slack(slackGKAdviceChannel, slackStatusText, ':coc1:')

        if firstRun == 0:
            firstRun = 1

        if redAlert == 1:
            print('[DEBUG] Red alert')
            bottomLightColor = 'red'
            topLightColor = 'red'
            robot.set_all_backpack_lights(cozmo.lights.red_light.flash())
            if redAlertSent == 0:
                # Alert the goalkeeper
                post_message_on_slack(slackGKAdviceChannel, slackAlertText, ':cocred1:')
                # Alert everyone
                print('[post_message_on_slack] slackLogChannel: ' + slackAlertChannel + ' slackAlertText: ' + slackAlertText)
                robotText = 'Attention please, we currently have ' + str(counterE) + ' P 1 alerts.'
                redAlertSent = 1                
        elif orangeAlert == 1:
            print('[DEBUG] Orange alert')
            bottomLightColor = 'orange'
            topLightColor = 'orange'
            robot.set_center_backpack_lights(cozmo.lights.Light(cozmo.lights.Color(rgb=(244,147,19))).flash())
            if orangeAlertSent == 0:
                # Alert the goalkeeper
                post_message_on_slack(slackGKAdviceChannel, slackAlertText, ':cocorange1:')
                # Alert everyone
                print('[post_message_on_slack] slackLogChannel: ' + slackAlertChannel + ' slackAlertText: ' + slackAlertText)
                robotText = slackAlertText
                orangeAlertSent = 1
        else:
            print('[DEBUG] No red or orange alert')
            bottomLightColor = 'green'
            robot.set_center_backpack_lights(cozmo.lights.green_light.flash())
            if yellowCounter != 0:
                topLightColor = 'yellow'
            elif whiteCounter != 0:
                topLightColor = 'white'
            elif pinkCounter != 0:
                topLightColor = 'deeppink'
            elif blueCounter != 0:
                topLightColor = 'blue'
            else:
                topLightColor = 'green'

        # print('bottomLightColor: ' + bottomLightColor)
        # print('topLightColor: ' + topLightColor)
        # print('yellowCounter: ' + str(yellowCounter) + '  whiteCounter: ' + str(whiteCounter) + '  pinkCounter: ' + str(pinkCounter) + '  blueCounter: ' + str(blueCounter))
        # print('robotText: ' + robotText)

        # Time for Cozmo to talk
        if robotText != '':
            # robotText = 'We have: ' + robotText
            robot.say_text(robotText).wait_for_completed()
            time.sleep(shortWait)

        print(Fore.RED + '[Lights & Magic monitoring] ' + Fore.BLUE + '\nEnd of cycle. Next cycle in ' + str(cycleDuration) + ' seconds.')
        print('Now waiting for next cycle to begin', end='', flush=True)

        for currentStep in range (0,32):
            # bstickStatus = update_bstick_nano(bottomLightColor, topLightColor, 'flash')
            bstickStatus = bstick_control(bottomLightColor, topLightColor, currentStep)
            print('.', end='', flush=True)
            time.sleep(1)

cozmo.run_program(cozmo_program)
