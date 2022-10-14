#!/usr/bin/env python3

# Protocol/7

import datetime
from datetime import date, timedelta
import time
# import cozmo
import os, calendar
import sys
import random
import urllib.request
import urllib.error
import json
import traceback
import logging
import boto3
from botocore.exceptions import ClientError
import colorama
from colorama import Fore, Style
from azure.storage.blob import BlobServiceClient, ContentSettings
from requests_toolbelt.multipart.encoder import MultipartEncoder
import requests
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
import socket
import importlib
import pymsteams
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

try:
    import slack
except ImportError:
    print('Cannot import SlackClient. Run: pip3 install slackclient')
    pass

try:
    from blinkstick import blinkstick
except ImportError:
    print('Cannot import blinkstick. Run: pip3 install blinkstick')
    pass

try:
    import notify2
except ImportError:
    print('Cannot import notify2, we are not running Linux, right ?')
    pass

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print('Cannot import from PIL: Do `pip3 install --user Pillow` to install')
    pass


# Import settings (enable/disable Blinkstick, Cozmo, Slack, Sumo, dashboard...)
# P/7 instance ID
instanceName = os.environ.get('NAME')
clientName = os.environ.get('CLIENT')
environment = os.environ.get('ENV')
projectName = os.environ.get('PROJECT')
instanceIdentifier = f'{instanceName}##{clientName}##{projectName}##{environment}'
dashboardTitle = f'{clientName} - {environment}'
# Preferences
# 0 = False
# 1 = True
enableLocalBStick = os.environ.get('ENABLELOCALBSTICK')
enableRemoteBStick = os.environ.get('ENABLEREMOTEBSTICK')
enableCozmo = '0'
enableSlack = os.environ.get('ENABLESLACK')
enableSumo = os.environ.get('ENABLESUMO')
enableDashboard = os.environ.get('ENABLEDASH')
enableMSTeams = os.environ.get('ENABLEMSTEAMS')
msTeamsWebhook = os.environ.get('MSTEAMSWEBHOOK')

# Import the URLs to test from config file
configFile = os.environ.get('CONFIGFILE')
configData = importlib.import_module(configFile)
urlList = configData.urlList
ntAPICountriesList = configData.ntAPICountriesList

if enableLocalBStick == '0':
	print(f'[INFO] Blinkstick is OFF')
else:
	print(f'[INFO] Blinkstick is ON')
if enableCozmo == '0':
	print(f'[INFO] Anki Cozmo is OFF')
else:
	print(f'[INFO] Anki Cozmo is ON')
if enableSlack == '0':
	print(f'[INFO] Slack messaging is OFF')
else:
	print(f'[INFO] Slack messaging is ON')
if enableSumo == '0':
	print(f'[INFO] Sumologic logging is OFF')
else:
	print(f'[INFO] Sumologic logging is ON')
if enableDashboard == '0':
	print(f'[INFO] dashboard is OFF')
else:
	print(f'[INFO] dashboard is ON')
if enableMSTeams == '0':
	print(f'[INFO] MS Teams messaging is OFF')
else:
	print(f'[INFO] MS Teams messaging is ON')

# Path to data folder (contains ML stuff)
cb1DataFolder = os.environ.get('CB1DATAFOLDER')
if not os.path.exists(cb1DataFolder):
    os.makedirs(cb1DataFolder)

# Path to logs folder
logFileFolder = os.environ.get('LOGSFOLDER')
if not os.path.exists(logFileFolder):
    os.makedirs(logFileFolder)

# Path to the local version of dashboard (to be uploaded to Azure Storage)
dashboardTempFolder = './dashboard/'
if not os.path.exists(dashboardTempFolder):
    os.makedirs(dashboardTempFolder)

def postMessageToMSTeams(msteamsMessage, colorTheme, cardTitle, cardType, optS1Text='', optS2Text=''):
    if enableMSTeams == '1':
        try:
            myTeamsMessage = pymsteams.connectorcard(msTeamsWebhook)
            myTeamsMessage.color(colorTheme)
            myTeamsMessage.title(cardTitle)
            if cardType == 'normal':
                myTeamsMessage.text(msteamsMessage)
            elif cardType == 'grouped':
                myTeamsMessage.text(msteamsMessage)
                # Red alerts
                Section1 = pymsteams.cardsection()
                Section1.title("<b><font color='red'>Red alerts</font></b>")
                Section1.text(optS1Text)
                # Orange alerts
                Section2 = pymsteams.cardsection()
                Section2.title("<b><font color='orange'>Orange warnings</font></b>")
                Section2.text(optS2Text)
                # Add both Sections to the main card object
                myTeamsMessage.addSection(Section1)
                myTeamsMessage.addSection(Section2)
            myTeamsMessage.send()
            print(f'[postMessageToMSTeams] {msteamsMessage}')
        except Exception as e:
            print('[ERROR] Failed to post message to MS Teams.\n', e)
            pass

def uploadFileToAzure(container_name, path_to_local_file, local_file_name):
    try:
        # container_name=container_name, blob_name=dashboardFile, file_path=dashboardUploadFilePath, content_settings=ContentSettings(content_type='text/html'), metadata=None, validate_content=False, progress_callback=None, max_connections=2, lease_id=None, if_modified_since=None, if_unmodified_since=None, if_match=None, if_none_match=None, timeout=10
        print('Uploading to Azure Storage Account...')
        blob_service_client = BlobServiceClient.from_connection_string(azure_stor_cnx_string)
        # Create a blob client using the local file name as the name for the blob
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=local_file_name)

        print("\nUploading to Azure Storage as blob:\n\t" + path_to_local_file)

        my_content_settings = ContentSettings(content_type='text/html')

        # Upload the created file
        with open(path_to_local_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True, content_settings=my_content_settings)
    except Exception as e:
        print(f'[ERROR] An error occurred while uploading to Azure Storage Account.\n', e)
        traceback.print_exc()
        pass

def uploadFileToS3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3', aws_access_key_id=s3AwsAccessKeyId, aws_secret_access_key=s3AwsSecretKey)
    try:
        response = s3_client.upload_file(file_name, bucket, object_name, ExtraArgs={'ContentType': "text/html"})
    except ClientError as e:
        logging.error(e)
        return False
    return True

def checkInternetAccess():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

def postToSumo(message, enableSumo):
    if enableSumo == '1':
        try:
            print('Posting to Sumo...')
            sumoEndpoint = os.getenv('SUMOENDPOINT')
            session = requests.Session()
            headers = {"Content-Type": "text/html", "Accept" : "application/json"}
            r = session.post(sumoEndpoint, headers=headers, data=message)
            # print (f'status={r.status_code} content={msg}')
        except Exception as e:
            print(f'[ERROR] An error occurred while posting to Sumo.\n', e)
            traceback.print_exc()
            pass

def lookForDeployments(environment, project_name, items_list, dep_tstamp):
    try:
        print('Looking for deployments...')
        # print(f'[DEBUG] environment={environment} project_name={project_name} items_list={items_list} dep_tstamp={dep_tstamp}')
        # Clearing the latest_deployment field
        for currentItem in items_list:
            items_list[currentItem]['latest_deployment'] = 'None'
        # Setting credentials
        personal_access_token = os.environ.get('AZDEVOPSPAT')
        organization_url = os.environ.get('AZDEVOPSURL')
        # Create a connection to the org
        credentials = BasicAuthentication('', personal_access_token)
        connection = Connection(base_url=organization_url, creds=credentials)
        # print(f'[DEBUG] personal_access_token={personal_access_token} organization_url={organization_url} credentials={credentials} connection={connection}')
        release_client = connection.clients.get_release_client()
        get_releases_definitions = release_client.get_release_definitions(project=project_name, search_text=environment, expand=None, artifact_type=None, artifact_source_id=None, top=None, continuation_token=None, query_order=None, path=None, is_exact_name_match=None, tag_filter=None, property_filters=None, definition_id_filter=None, is_deleted=None, search_text_contains_folder_name=environment)
        releases_index = 0
        # print(f'\n\n\nToday\'s deployments for {project_name}/{environment}:')
        while get_releases_definitions is not None:
            for definition in get_releases_definitions.value:
                releases_index += 1
                get_releases_list = release_client.get_releases(project=project_name, definition_id=definition.id, definition_environment_id=None, search_text=None, created_by=None, status_filter=None, environment_status_filter=None, min_created_time=dep_tstamp, max_created_time=None, query_order='ascending', top=None, continuation_token=None, expand=None, artifact_type_id=None, source_id=None, artifact_version_id=None, source_branch_filter=None, is_deleted=None, tag_filter=None, property_filters=None, release_id_filter=None, path=None)
                list_index = 0
                # print(f'\n\t- {definition.name} ({definition.id}):')
                while get_releases_list is not None:
                    for release in get_releases_list.value:
                        # print(f'\n\t\t- {release.id} - {release.name}')
                        list_index += 1
                        get_deployments_list = release_client.get_deployments(project=project_name, definition_id=definition.id, definition_environment_id=None, created_by=None, min_modified_time=None, max_modified_time=None, deployment_status=None, operation_status=None, latest_attempts_only=True, query_order='descending', top=None, continuation_token=None, created_for=None, min_started_time=None, max_started_time=None, source_branch=None)
                        deployments_index = 0
                        latestStageFound = 0
                        while get_deployments_list is not None:
                            for deployment in get_deployments_list.value:
                                deployments_index += 1
                                if (release.id == deployment.release.id) and (latestStageFound == 0):
                                    # print(f'\n\t\t- [{deployment.id}] {deployment.release.name} [ https://dev.azure.com/{project_name}/{project_name}/_releaseProgress?releaseId={deployment.release.id}&_a=release-pipeline-progress ] ({deployment.deployment_status})')
                                    latestStageFound = 1
                                    for currentItem in items_list:
                                        if items_list[currentItem]['release_def_ids'][0] == definition.id:
                                            print(f'Deployment for {items_list[currentItem]["appname"]} found.')
                                            items_list[currentItem]['latest_deployment'] = f'<a href="https://dev.azure.com/{project_name}/{project_name}/_releaseProgress?releaseId={deployment.release.id}&_a=release-pipeline-progress">{deployment.release.name}</a> ({deployment.deployment_status})'
                            get_deployments_list = None
                    get_releases_list = None
            get_releases_definitions = None
        return items_list
    except Exception as e:
        print(f'[ERROR] An error occurred while retrieving the latest deployments.\n', e)
        return items_list
        traceback.print_exc()
        pass

def testNTAPI(apiURL, countryName, countryToken, clubId, dateMin, dateMax):
    try:
        headers = {
            'Accept': '/',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Authorization': 'Bearer ' + countryToken,
            'User-Agent':'protocol/7 Open Source monitoring ' + version + ' (run=' + str(epoch) + ')'
        }

        data = '{"brandCode":"ff","countryCode":"' + countryName + '","ClubId":"' + str(clubId) + '","TimeFrom":"' + str(dateMin) + '","TimeTo":"' + str(dateMax) + '"}'

        print(f'data={data}')
        http_response = requests.get(apiURL, data=data, json=None, headers=headers)
        http_status_code = http_response.status_code
        http_response_time = round(http_response.elapsed.total_seconds(), 2)
        print(f'- http_status_code for NT API test: {http_status_code} (took {http_response_time} seconds)')
        # print(f'\nResponse: {http_response.text}')
    except Exception as e:
        print(f'[ERROR] Failed to test NT API for country {countryName}.\n', e)
        http_response = 'NTAPITESTFAILED'
        http_status_code = '4XX'
        http_response_time = 0
        traceback.print_exc()
        pass
    return http_response,http_status_code,http_response_time

def generateNTAPIToken(apiURL, countryName):
    # countries: hk, id, th, sg, my, ph
    try:
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Content-Type': 'multipart/form-data',
            'Cache-Control': 'no-cache'
        }

        multipart_encoder = MultipartEncoder(
            fields = {
                'username': os.environ.get('NTAPIUSER'),
                'password': os.environ.get('NTAPIPASS'),
                'country': countryName
            }
        )

        headers['Content-Type'] = multipart_encoder.content_type
        http_response = requests.post(apiURL, data=multipart_encoder, json=None, headers=headers)
        http_status_code = http_response.status_code
        http_response_time = round(http_response.elapsed.total_seconds(), 2)
        print(f'- http_status_code for token generation: {http_status_code} (took {http_response_time} seconds)')
        canard = json.loads(http_response.text)
        token = canard["data"]["token"]
        # print(f'\nToken: {token}')
    except Exception as e:
        print(f'[ERROR] Failed to generate NT API token for country {countryName}.\n', e)
        http_response = 'TOKENGENERATIONFAILED'
        http_status_code = '4XX'
        http_response_time = 0
        token = 'TOKENGENERATIONFAILED'
        traceback.print_exc()
        pass
    return http_response,http_status_code,http_response_time,token

def writeDataToFile(targetFile, dataToWrite, successMsg, failureMsg, mode):
    try:
        if mode == 'overwrite':
            newCB1File = open(targetFile,'w+')
        elif mode == 'append':
            newCB1File = open(targetFile,'a')
        newCB1File.write(dataToWrite)
        newCB1File.close()
        print(successMsg)
    except Exception as e:
        print(failureMsg, e)
        traceback.print_exc()
        pass

def dynamodbDeleteTable(databaseURL, tableName):
    print('dynamodbDeleteTable')
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
    print('dynamodbListTableItems')
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
    print(f'dynamodbReadFromTable - databaseURL: {databaseURL} - tableName: {tableName}')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToRead = dynamodb.Table(tableName)
        retrievedItems = []
        if tableName == 'email_tracking':
            x = tableToRead.scan()
            for i in x['Items']:
                print(i['label'])
                retrievedItems.append(i['label'])
        elif tableName == 'p7dev_bstick':
            x = tableToRead.scan()
            print(x)
            for i in x['Items']:
                print(i['expiry'])
                retrievedItems.append(i['expiry'])
        response = 'Data successfully loaded.'
    except Exception as e:
        print('[ERROR] Failed to load configuration data from table ' + tableName + '.\n', e)
        response = 'Failed to load data.'
        traceback.print_exc()
        pass
    return retrievedItems

def dynamodbProvisionTable(databaseURL, tableName, dataToInsert):
    print('dynamodbProvisionTable')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        tableToProvision = dynamodb.Table(tableName)
        if tableName == 'email_tracking':
            tableToProvision.put_item(Item=json.loads(dataToInsert))
        elif tableName == 'p7dev_bstick':
            print('Provision p7dev_bstick')
            tableToProvision.put_item(Item=json.loads(dataToInsert))
        response = 'Provisioning successful'
    except Exception as e:
        print('[ERROR] Failed to create database table ' + tableName + '.\n', e)
        response = 'Table provisioning failed'
        traceback.print_exc()
        pass
    return response

def dynamodbCreateTable(databaseURL, tableName):
    print('dynamodbCreateTable')
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url=databaseURL)
        if tableName == 'email_tracking':
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
        elif tableName == 'p7dev_bstick':
            table = dynamodb.create_table(
                TableName=tableName,
                KeySchema=[
                    {
                        'AttributeName': 'msgId',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'msgId',
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
    print('dynamodbTableCheck')
    try:
        dynamodb = boto3.client('dynamodb', endpoint_url=databaseURL)
        response = dynamodb.describe_table(TableName=tableName)
    except Exception as e:
        print(f'[DEBUG] DynamoDB table {tableName} not found', e)
        response = 'Table not found'
        pass
    return str(response)

def callURL(url2call, creds):
    try:
        # print(f'callURL({url2call},{creds})')
        req = urllib.request.Request(url2call, headers=creds, data=None)
        start = time.time()
        response = urllib.request.urlopen(req, timeout=10)
        load_elapsed = round(time.time() - start, 2)
        payload = response.read()
        http_status = response.getcode()
        print(f'load_elapsed: {load_elapsed}, http_status: {http_status}')
        return payload, load_elapsed, http_status
    except urllib.error.HTTPError as e:
        print(f'[HTTPError] Exception: {e} ({e.code})\nFailed to call {url2call}')
        return 'HTTPERROR', 0, e.code
        pass
    except urllib.error.URLError as f:
        print(f'[URLError] Exception: {f} - {f.reason} (666)\nFailed to call {url2call}')
        if checkInternetAccess():
            print('[INFO] Internet access is OK.')
            return 'URLERROR', 0, 666
        else:
            print('[ERROR] Internet access is KO.')
            return 'INETERROR', 0, 777
        pass
    except Exception as g:
        print(f'[OTHERERROR] Exception: {g} (999)\nFailed to open {url2call}.\nOther exception.')
        return 'OTHERERROR', 0, 999
        pass

def post_message_to_slack(slackLogChannel, slackMessage, slackEmoji, enableSlack):
    if enableSlack == '1':
        try:
            slackToken = os.environ.get('SLACKTOKEN')
            client = slack.WebClient(slackToken)
            response = client.chat_postMessage(
                channel=slackLogChannel,
                text=slackMessage,
                username='Cozmo Office Mate',
                icon_emoji=slackEmoji)
            assert response["ok"]
            assert response["message"]["text"] == slackMessage
            print(f'[post_message_to_slack] {slackLogChannel} : {slackMessage}')
        except Exception as e:
            print('[ERROR] Failed to post message to Slack.\n', e)
            pass

def bstick_control(bgcolor, fgcolor, dot, enableLocalBStick):
    # This function drives the BlinkStick Flex (32 LEDs)
    if enableLocalBStick == '1':
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
    else:
        bstickStatus = 'disabled'
    return bstickStatus

def update_bstick_color(bstickColor, enableLocalBStick):
    # This function drives the BlinkStick Flex (32 LEDs)
    if enableLocalBStick == '1':
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
    else:
        bstickStatus = 'disabled'
    return bstickStatus

def update_local_bstick_nano(bgcolor, fgcolor, mode, enableLocalBStick):
    # This function drives the local BlinkStick Nano (two LEDs, one on each side)
    if enableLocalBStick == '1':
        if mode == 'normal':
            try:
                for bstick in blinkstick.find_all():
                    bstick.set_color(channel=0, index=0, name=fgcolor)
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
                print('[ERROR] Failed to update local Blinkstick color.\n', e)
                bstickStatus = 'unknown'
                traceback.print_exc()
                pass
    else:
        bstickStatus = 'disabled'
    return bstickStatus

def update_remote_bstick_nano(bgcolor, fgcolor, bottommode, topmode, enableRemoteBStick, instanceIdentifier):
    # This function drives remote BlinkStick Nano (two LEDs, one on each side)
    if enableRemoteBStick == '1':
        try:
            print('Inserting new command in database')
            currentDT = datetime.datetime.now()
            ISOTStamp = currentDT.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            tomorrow = date.today() + timedelta(days=1)
            cmdExpiry = tomorrow.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            cmdOrigin = instanceIdentifier
            dataToInsert = '{"msgId":"' + cmdOrigin + '##BStickNano' + '","expiry":"' + cmdExpiry + '","origin":"' + cmdOrigin + '",' + bgcolor + ',' + fgcolor + ',' + '"topMode":"' + topmode + '","bottomMode":"' + bottommode + '"}'
            msgList = []
            tableName = 'p7dev_bstick'

            if dynamodbProvisionTable(databaseURL, tableName, dataToInsert) == 'Provisioning successful':
                msgList = dynamodbReadFromTable(databaseURL, tableName)
                print('New command inserted in database')

            print(f'msgList: {msgList}')
            bstickStatus = bgcolor
        except Exception as e:
            print('[ERROR] Failed to update remote Blinkstick color.\n', e)
            bstickStatus = 'unknown'
            traceback.print_exc()
            pass
    else:
        bstickStatus = 'disabled'
    return bstickStatus

# def cozmo_program(robot: cozmo.robot.Robot):
#     print('Cozmo program')

# Variables declaration
version = '0.47.51'
greetingSentences = ['Hi folks !','Hey ! I am back !','Hi ! How you doing ?','Cozmo, ready !']
databaseURL = os.environ.get('DYNAMODBURL')

firstRun = 0
cycleCntr = -1
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
slackLogChannel = 'astro-pantz'
slackAlertChannel = 'astro-pantz'
slackGKAdviceChannel = 'astro-pantz'
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
topLightColor = 'blue'
topRemoteLightColor = '"tR":"0","tG":"0","tB":"255"'
urgencyWords = ['ombudsman','court','tribunal','urgent','emergency','angry','dissatisfied','escalation','attorney','lawyer','threat','extreme','annoy','complain','insult','upset','techops','devops','sre','incident','accident','production','prod','downtime','down','unhappy','broken','break','breakage']
emptyCreds = { 'foo' : 'bar' }
container_name = '$web'
azure_stor_acc_name = os.getenv('AZSTORACCNAME')
azure_stor_acc_key = os.getenv('AZSTORACCKEY')
azure_stor_cnx_string = os.getenv('AZCNXSTRING')
dashboardFilename = os.getenv('DASHBOARDFILENAME')
advancedDashboardFilename = os.getenv('ADVDASHBOARDFILENAME')
dashboardFile = dashboardFilename
dashboardFile2 = advancedDashboardFilename
dashboardUploadFilePath = os.path.join(dashboardTempFolder, dashboardFile)
dashboardUploadFilePath2 = os.path.join(dashboardTempFolder, dashboardFile2)
logFile = os.getenv('LOGFILENAME')
fullLogPath = os.path.join(logFileFolder, logFile)
dashboardBaseURL = os.getenv('DASHBOARDSBASEURL')
azureDashboard = os.getenv('AZDASHENABLED')
amazonDashboard = os.getenv('AWSDASHENABLED')
s3BucketName = os.getenv('S3BUCKETNAME')
s3AwsAccessKeyId = os.getenv('AWS_ACCESS_KEY_ID')
s3AwsSecretKey = os.getenv('AWS_SECRET_ACCESS_KEY')
specialHTTPErrors = [666,777,999]
green = '73D87D'
yellow = 'E6DE05'
orange = 'FF904F'
red = 'FF4747'
pink = 'FF4FEA'
grey = 'C0C0C0'
purple = '7532A8'
light_blue = '47A7FF'

# Reset head and lift position
# robot.set_head_angle(cozmo.robot.MIN_HEAD_ANGLE).wait_for_completed()
# robot.set_lift_height(0.0).wait_for_completed()

# Head up
# robot.set_head_angle(cozmo.robot.MAX_HEAD_ANGLE).wait_for_completed()

# Checking DB
# Table: email_tracking
# Content: A list of New Relic violations to watch after
dataToInsert = '{"label":"Fullest disk"}'
nrVioTrackList = []
if dynamodbTableCheck(databaseURL, 'email_tracking') == 'Table not found':
    # Table missing - creating
    if dynamodbCreateTable(databaseURL, 'email_tracking') == 'Table created':
        # Table created - provisioning
        if dynamodbProvisionTable(databaseURL, 'email_tracking', dataToInsert) == 'Provisioning successful':
            nrVioTrackList = dynamodbReadFromTable(databaseURL, 'email_tracking')
        else:
            print('Provisioning of table email_tracking failed :-(')
    else:
        print('Creation of table email_tracking failed :-(')
else:
    print('')
    nrVioTrackList = dynamodbReadFromTable(databaseURL, 'email_tracking')

if dynamodbDeleteTable(databaseURL, 'email_tracking'):
    print('')
else:
    print('Table email_tracking deletion failed :-(')

# Checking DB
# Table: p7dev_bstick
# Content: Commands destined to be used by the BlinkStick to set it's color (RGB) and mode (on, off, blinking)
tableName = 'p7dev_bstick'
if dynamodbTableCheck(databaseURL, tableName) == 'Table not found':
    # Table missing - creating
    print('Table missing - creating')
    if dynamodbCreateTable(databaseURL, tableName) == 'Table created':
        print(f'Creation of table {tableName} succeeded.')
    else:
        print(f'Creation of table {tableName} failed :-(')
else:
    print('')
    msgList = dynamodbReadFromTable(databaseURL, tableName)


############################
# Start main loop          #
############################
os.system('clear')
print(Fore.RED + '################')
print(Fore.RED + '#  Protocol/7  #')
print(Fore.RED + '################')
print('')
print(Fore.RED + 'Instance ID: ' + instanceIdentifier)
print('')
print(Fore.GREEN + '')
# Post config info to Slack
post_message_to_slack(slackGKAdviceChannel, f'Protocol/7 server started\nConfig data:\n- DYNAMODBURL: {databaseURL}\n- P7INSTANCEID: {instanceIdentifier}', ':coc1:', enableSlack)
postMessageToMSTeams(f'Config data:\r\n- DYNAMODBURL: {databaseURL}\r\n- P7INSTANCEID: {instanceIdentifier}\r\n- Dashboard: {dashboardBaseURL}/{advancedDashboardFilename}', '47A7FF', 'Protocol/7 server started', 'normal')
while True:
    # 6 cycles (from 0 to 5)
    # Temporary setting bottom light to blue
    bottomLightColor = 'blue'
    bottomRemoteLightColor = '"bR":"0","bG":"0","bB":"255"'
    bstickStatus = update_local_bstick_nano(bottomLightColor, topLightColor, 'normal', enableLocalBStick)
    update_remote_bstick_nano(bottomRemoteLightColor, topRemoteLightColor, 'on', 'on', enableRemoteBStick, instanceIdentifier)
    # robot.set_all_backpack_lights(cozmo.lights.blue_light)
    time.sleep(shortWait)
    currentDT = datetime.datetime.now()
    currentDay = currentDT.strftime("%A")
    currentMonth = currentDT.strftime("%B")
    dashboardTStamp = currentDT.strftime("%A %d %B @ %H:%M")
    ISOTStamp = currentDT.strftime("%Y-%m-%d %H:%M:%S")
    epoch = int(datetime.datetime.strptime(ISOTStamp, '%Y-%m-%d %H:%M:%S').strftime("%s"))
    ISOTStamp = ISOTStamp + ' +1100'
    yesterday = date.today() - timedelta(days=1)
    deploymentsTStamp = yesterday.strftime("%Y-%m-%dT00:00:00.000Z")
    yyyymmdd = currentDT.strftime("%Y%m%d")
    hhmm = currentDT.strftime("%H%M")
    timeblock = currentDT.strftime("%H")
    cycleCntr += 1
    if cycleCntr > 5:
        cycleCntr = 0
    print(Fore.RED + '\n[Protocol/7] ' + Fore.BLUE + 'Cycle: ' + str(cycleCntr) + '/5 - ' + currentDT.strftime("%H:%M"))
    print(Fore.GREEN + '')

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
    redAlert = 0
    orangeAlert = 0
    groupAlerts = 0
    groupedAlertS1Text = '<ul>'
    groupedAlertS2Text = '<ul>'
    slackStatusText = ''
    slackAlertText = '--- *' + currentDT.strftime("%H:%M") + '* ---\n'
    publishNewGKAdvice = 'no'
    slackGKAdvice = '--- *' + currentDT.strftime("%H:%M") + '* ---\n'
    robotText = ''
    slackMsgLine1 = '--- *' + currentDT.strftime("%H:%M") + '* ---'
    slackMsgLine2 = ''
    slackMsgLine3 = ''
    slackMsgLine4 = ''
    slackMsgLine5 = ''
    slackMsgLine6 = ''
    failuresCntr = 0
    dashboardText = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>' + dashboardTitle + '</title>'
    dashboardText = dashboardText + '<style>.flex-container {width: 80%; min-height: 100px; margin: 0 auto; font-size: 32px; display: -webkit-flex; display: flex; border: 1px solid #808080;}'
    dashboardText = dashboardText + '.flex-container div {padding: 10px; background: #dbdfe5; -webkit-flex: 1; -ms-flex: 1; flex: 1;}'
    dashboardText = dashboardText + '.flex-container div.up{background: #06d519;}'
    dashboardText = dashboardText + '.flex-container div.down{background: #d50c06;}'
    dashboardText = dashboardText + '.flex-container div.incident{background: #d59606;}'
    dashboardText = dashboardText + '.flex-container div.deployment{background: #0f8ce6;}'
    dashboardText = dashboardText + '.flex-container div.grey{background: #c0c0c0;}'
    dashboardText = dashboardText + '.flex-container div.pink{background: #ff4fea;}'
    dashboardText = dashboardText + '.flex-container div.maintenance{background: #e6de05;}'
    dashboardText = dashboardText + '</style></head><body><center><h1>Refreshed: ' + dashboardTStamp + '</h1></center>'
    dashboardText2 = '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>' + dashboardTitle + ' (' + ISOTStamp + ')' + '</title>'
    dashboardText2 = dashboardText2 + '<script>window.setInterval("refresh()", 20000); function refresh() { window.location.reload() }</script>'
    dashboardText2 = dashboardText2 + '<style>* { box-sizing: border-box; } .columns { float: left; width: 20%; padding: 8px; } body { background-color: #2F2E30; }'
    dashboardText2 = dashboardText2 + '.application_up { border-top: 20px solid #' + green + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.application_down { border-top: 20px solid #' + red + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.application_incident { border-top: 20px solid #' + orange + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.application_deployment { border-top: 20px solid #' + light_blue + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.application_grey { border-top: 20px solid #' + grey + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.application_pink { border-top: 20px solid #' + pink + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.application_maintenance { border-top: 20px solid #' + yellow + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.application_mismatch { border-top: 20px solid #' + purple + '; border-bottom: 20px solid #D8D8D8; border-radius: 10px; margin: 0; padding: 0; background-color: #D8D8D8; font-size: 20px; }'
    dashboardText2 = dashboardText2 + '.app_name { font-size: 40px; font-weight: bold; } .customer_name { font-size: 30px; } p { margin: 20px; } @media only screen and (max-width: 600px) { .columns { width: 100%; }}'
    dashboardText2 = dashboardText2 + '</style></head><body>'
    currentFailtage = 0
    currentHeader = 'application_up'
    currentStatus = 'Healthy'
    currentRespTime = 0
    currentColor = ''
    newLogLine = ''

    ##############################
    # Refresh all data in one go #
    ##############################
    # robot.say_text(str(cycleCntr)).wait_for_completed()
    time.sleep(shortWait)
    
    # Refreshing deployments-related data
    urlList = lookForDeployments(environment, projectName, urlList, deploymentsTStamp)

    # Apps
    # We check HTTP status first
    # In case of HTTP success we check payload content
    print(Fore.RED + '[Protocol/7] ' + Fore.GREEN + '\nI will now query the applications in order to see if everything is alright.')
    for currentItem in urlList:
        print(f'currentItem: {currentItem}')
        if (orangeCounter + redCounter) >= 3:
            groupAlerts = 1
            print(f'Now grouping alerts {(orangeCounter + redCounter)}')
        else:
            groupAlerts = 0
            print(f'No need to group alerts yet {(orangeCounter + redCounter)}')
        print('Calling ' + urlList[currentItem]['url'])
        payload, urlList[currentItem]['rt_history'][cycleCntr], http_status = callURL(str(urlList[currentItem]['url']), urlList[currentItem]['credentials'])
        if http_status in urlList[currentItem]['http_success']:
            # UP (HTTP)
            print('HTTP success')
            urlList[currentItem]['payload'] = payload
            # Checking payload (success, maintenance, failure)
            if urlList[currentItem]['payload_success'].lower() in str(payload).lower():
                print('Payload success')
                currentStatus = f'Healthy ({http_status})'
                currentColor = 'green'
                urlList[currentItem]['orange_since'] = '-'
                urlList[currentItem]['red_since'] = '-'
                urlList[currentItem]['orange_sent'] = 0
                urlList[currentItem]['red_sent'] = 0
                print(f'- {urlList[currentItem]["appname"]} is UP')
                urlList[currentItem]['failure_history'][cycleCntr] = 0
                failuresCntr = urlList[currentItem]["failure_history"].count(1)
                if urlList[currentItem]['latest_deployment'] == 'None':
                    currentHeader = 'application_up'
                    dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="up">UP</div></div></div>'
                else:
                    currentHeader = 'application_deployment'
                    dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="deployment">UP</div></div></div>'
            elif urlList[currentItem]['payload_maintenance'].lower() in str(payload).lower():
                print('Payload maintenance')
            elif urlList[currentItem]['payload_failure'].lower() in str(payload).lower():
                print('Payload failure')
            else:
                print('Payload uncertain')
        elif http_status in urlList[currentItem]['http_maintenance']:
            # MAINTENANCE (HTTP)
            print('HTTP maintenance')
            urlList[currentItem]['payload'] = payload
            if urlList[currentItem]['latest_deployment'] == 'None':
                currentHeader = 'application_maintenance'
                dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="maintenance">MAINTENANCE</div></div></div>'
                currentStatus = f'Maintenance ({http_status})'
                currentColor = 'yellow'
            else:
                currentHeader = 'application_deployment'
                dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="deployment">UP</div></div></div>'
                currentStatus = f'Healthy ({http_status})'
                currentColor = 'green'
            urlList[currentItem]['orange_since'] = '-'
            urlList[currentItem]['red_since'] = '-'
            urlList[currentItem]['orange_sent'] = 0
            urlList[currentItem]['red_sent'] = 0
            print(f'- {urlList[currentItem]["appname"]} status is {currentStatus}')
            urlList[currentItem]['failure_history'][cycleCntr] = 0
            failuresCntr = urlList[currentItem]["failure_history"].count(1)
        elif (http_status in urlList[currentItem]['http_failure']) or (http_status in specialHTTPErrors):
            # FAILURE - 1st
            print('HTTP failure')
            urlList[currentItem]['failure_history'][cycleCntr] = 1
            print(f'- Test history over the last 6 cycles: {urlList[currentItem]["failure_history"]}')
            failuresCntr = urlList[currentItem]["failure_history"].count(1)
            print(f'- Number of failures: {failuresCntr}')
            if http_status == 777:
                currentHeader = 'application_grey'
                currentStatus = f'<font color="orange"><b>Internet cnx failed during test</b> ({http_status})</font>'
                currentColor = 'grey'
                whiteCounter += 1
                urlList[currentItem]['payload'] = 'INETERROR'
                print('[ERROR] INETERROR for ' + str(urlList[currentItem]['url']))
                dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="grey">INET CNX ISSUE</div></div></div>'
            elif http_status == 401:
                currentHeader = 'application_pink'
                currentStatus = f'<font color="orange"><b>Credentials were refused</b> ({http_status})</font>'
                currentColor = 'pink'
                pinkCounter += 1
                urlList[currentItem]['payload'] = 'HTTPERROR'
                print('[ERROR] HTTPERROR (pink light) for ' + str(urlList[currentItem]['url']))
                dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="pink">CREDS ISSUE</div></div></div>'
            elif http_status == 999:
                currentHeader = 'application_grey'
                currentStatus = f'<font color="orange"><b>Other error</b> ({http_status})</font>'
                currentColor = 'grey'
                whiteCounter += 1
                urlList[currentItem]['payload'] = 'OTHERERROR'
                print('[ERROR] OTHERERROR (white light) for ' + str(urlList[currentItem]['url']))
                dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="grey">OTHER ISSUE</div></div></div>'
            elif http_status == 666:
                # URLERROR
                if failuresCntr == 1:
                    whiteCounter += 1
                    urlList[currentItem]['payload'] = 'URLERROR'
                    print('[ERROR] URLERROR (white light) for ' + str(urlList[currentItem]['url']))
                    if urlList[currentItem]['latest_deployment'] == 'None':
                        currentHeader = 'application_up'
                        currentStatus = f'<font color="red"><b>/!\ Last test failed</b> ({http_status})</font>'
                        currentColor = 'green'
                        dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="up">UP</div></div></div>'
                    else:
                        currentHeader = 'application_up'
                        currentStatus = f'<font color="red"><b>/?\ Check for deployment</b> ({http_status})</font>'
                        currentColor = 'green'
                        dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="up">UP</div></div></div>'
                elif (failuresCntr >= 2) and (failuresCntr <= 5):
                    print('[ORANGE] Failures count between 2 and 5 triggered an orange alert')
                    orangeAlert = 1
                    currentHeader = 'application_incident'
                    if urlList[currentItem]['orange_since'] == '-':
                        urlList[currentItem]['orange_since'] = dashboardTStamp
                    currentColor = 'orange'
                    if urlList[currentItem]['latest_deployment'] != 'None':
                        currentStatus = f'<font color="red"><b>/?\ Check for deployment</b> ({http_status})</font>'
                    else:
                        currentStatus = f'Since {urlList[currentItem]["orange_since"]} ({http_status})'
                    print(f'- {urlList[currentItem]["appname"]} is FAILING')
                    if urlList[currentItem]['orange_sent'] == 0:
                        orangeCounter += 1
                        if enableSlack == '1':
                            slackAlertText = '[ORANGE] Failures count between 2 and 5 triggered an orange alert\n'
                            slackAlertText = slackAlertText + f'{urlList[currentItem]["appname"]} is FAILING\n'
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = slackAlertText + dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = slackAlertText + 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            post_message_to_slack(slackGKAdviceChannel, slackAlertText, ':cocorange1:', enableSlack)
                        if enableMSTeams == '1':
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            if groupAlerts == 0:
                                # Alerts grouping NOT active
                                postMessageToMSTeams(f'[ORANGE] Failures count between 2 and 5 triggered an orange alert: {urlList[currentItem]["appname"]} is FAILING ({slackAlertText})', 'FF904F', 'Orange warning', 'normal')
                            elif groupAlerts == 1:
                                # Alerts grouping active
                                groupedAlertS2Text += f'<li>{urlList[currentItem]["appname"]} is FAILING ({slackAlertText})</li>'
                        robotText = 'Attention please, we currently have an issue.'
                        urlList[currentItem]['orange_sent'] = 1
                    dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="incident">INCIDENT</div></div></div>'
                    robotText = robotText + f'{urlList[currentItem]["appname"]} is experiencing difficulties.'
                elif failuresCntr >= 6:
                    print('[RED] Failures count of 6+ triggered a red alert')
                    redAlert = 1
                    currentHeader = 'application_down'
                    if urlList[currentItem]['red_since'] == '-':
                        urlList[currentItem]['red_since'] = dashboardTStamp
                    currentColor = 'red'
                    if urlList[currentItem]['latest_deployment'] != 'None':
                        currentStatus = f'<font color="red"><b>/?\ Check for deployment</b> ({http_status})</font>'
                    else:
                        currentStatus = f'Since {urlList[currentItem]["red_since"]} ({http_status})'
                    print(f'- {urlList[currentItem]["appname"]} is DOWN')
                    if urlList[currentItem]['red_sent'] == 0:
                        redCounter += 1
                        if enableSlack == '1':
                            slackAlertText = '[RED] Failures count of 6+ triggered a red alert\n'
                            slackAlertText = slackAlertText + f'{urlList[currentItem]["appname"]} is DOWN\n'
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = slackAlertText + dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = slackAlertText + 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            post_message_to_slack(slackGKAdviceChannel, slackAlertText, ':cocred1:', enableSlack)
                        if enableMSTeams == '1':
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            if groupAlerts == 0:
                                # Alerts grouping NOT active
                                postMessageToMSTeams(f'[RED] Failures count of 6+ triggered a red alert: {urlList[currentItem]["appname"]} is DOWN ({slackAlertText})', 'FF4747', 'Red alert', 'normal')
                            elif groupAlerts == 1:
                                # Alerts grouping active
                                groupedAlertS1Text += f'<li>{urlList[currentItem]["appname"]} is DOWN ({slackAlertText})</li>'
                        robotText = 'Attention please, we currently have an issue.'
                        urlList[currentItem]['red_sent'] = 1
                    dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="down">DOWN</div></div></div>'
                    robotText = robotText + f'{urlList[currentItem]["appname"]} is DOWN.'
            elif http_status in urlList[currentItem]['http_failure']:
                # USER DEFINED
                if failuresCntr == 1:
                    whiteCounter += 1
                    urlList[currentItem]['payload'] = 'FAILURE'
                    print('[ERROR] FAILURE (white light) for ' + str(urlList[currentItem]['url']))
                    if urlList[currentItem]['latest_deployment'] == 'None':
                        currentHeader = 'application_up'
                        currentStatus = f'<font color="red"><b>/!\ Last test failed</b> ({http_status})</font>'
                        currentColor = 'green'
                        dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="up">UP</div></div></div>'
                    else:
                        currentHeader = 'application_up'
                        currentStatus = f'<font color="red"><b>/?\ Check for deployment</b> ({http_status})</font>'
                        currentColor = 'green'
                        dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="up">UP</div></div></div>'
                elif (failuresCntr >= 2) and (failuresCntr <= 5):
                    print('[ORANGE] Failures count between 2 and 5 triggered an orange alert')
                    orangeAlert = 1
                    currentHeader = 'application_incident'
                    if urlList[currentItem]['orange_since'] == '-':
                        urlList[currentItem]['orange_since'] = dashboardTStamp
                    currentColor = 'orange'
                    if urlList[currentItem]['latest_deployment'] != 'None':
                        currentStatus = f'<font color="red"><b>/?\ Check for deployment</b> ({http_status})</font>'
                    else:
                        currentStatus = f'Since {urlList[currentItem]["orange_since"]} ({http_status})'
                    print(f'- {urlList[currentItem]["appname"]} is FAILING')
                    if urlList[currentItem]['orange_sent'] == 0:
                        orangeCounter += 1
                        if enableSlack == '1':
                            slackAlertText = '[ORANGE] Failures count between 2 and 5 triggered an orange alert\n'
                            slackAlertText = slackAlertText + f'{urlList[currentItem]["appname"]} is FAILING\n'
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = slackAlertText + dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = slackAlertText + 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            post_message_to_slack(slackGKAdviceChannel, slackAlertText, ':cocorange1:', enableSlack)
                        if enableMSTeams == '1':
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            if groupAlerts == 0:
                                # Alerts grouping NOT active
                                postMessageToMSTeams(f'[ORANGE] Failures count between 2 and 5 triggered an orange alert: {urlList[currentItem]["appname"]} is FAILING ({slackAlertText})', 'FF904F', 'Orange warning', 'normal')
                            elif groupAlerts == 1:
                                # Alerts grouping active
                                groupedAlertS2Text += f'<li>{urlList[currentItem]["appname"]} is FAILING ({slackAlertText})</li>'
                        robotText = 'Attention please, we currently have an issue.'
                        urlList[currentItem]['orange_sent'] = 1
                    dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="incident">INCIDENT</div></div></div>'
                    robotText = robotText + f'{urlList[currentItem]["appname"]} is experiencing difficulties.'
                elif failuresCntr >= 6:
                    print('[RED] Failures count of 6+ triggered a red alert')
                    redAlert = 1
                    currentHeader = 'application_down'
                    if urlList[currentItem]['red_since'] == '-':
                        urlList[currentItem]['red_since'] = dashboardTStamp
                    currentColor = 'red'
                    if urlList[currentItem]['latest_deployment'] != 'None':
                        currentStatus = f'<font color="red"><b>/?\ Check for deployment</b> ({http_status})</font>'
                    else:
                        currentStatus = f'Since {urlList[currentItem]["red_since"]} ({http_status})'
                    print(f'- {urlList[currentItem]["appname"]} is DOWN')
                    if urlList[currentItem]['red_sent'] == 0:
                        redCounter += 1
                        if enableSlack == '1':
                            slackAlertText = '[RED] Failures count of 6+ triggered a red alert\n'
                            slackAlertText = slackAlertText + f'{urlList[currentItem]["appname"]} is DOWN\n'
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = slackAlertText + dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = slackAlertText + 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            post_message_to_slack(slackGKAdviceChannel, slackAlertText, ':cocred1:', enableSlack)
                        if enableMSTeams == '1':
                            if enableDashboard == '1':
                                if azureDashboard == '1':
                                    slackAlertText = dashboardBaseURL + '/' + advancedDashboardFilename
                                else:
                                    slackAlertText = 'http://' + s3BucketName + '/' + advancedDashboardFilename
                            if groupAlerts == 0:
                                # Alerts grouping NOT active
                                postMessageToMSTeams(f'[RED] Failures count of 6+ triggered a red alert: {urlList[currentItem]["appname"]} is DOWN ({slackAlertText})', 'FF4747', 'Red alert', 'normal')
                            elif groupAlerts == 1:
                                # Alerts grouping active
                                groupedAlertS1Text += f'<li>{urlList[currentItem]["appname"]} is DOWN ({slackAlertText})</li>'
                        robotText = 'Attention please, we currently have an issue.'
                        urlList[currentItem]['red_sent'] = 1
                    dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="down">DOWN</div></div></div>'
                    robotText = robotText + f'{urlList[currentItem]["appname"]} is DOWN.'
            else:
                # UNMANAGED FAILURE
                currentHeader = 'application_grey'
                currentStatus = f'<font color="orange"><b>Other error (unmanaged)</b> ({http_status})</font>'
                currentColor = 'grey'
                whiteCounter += 1
                urlList[currentItem]['payload'] = 'OTHERERROR'
                print('[ERROR] OTHERERROR (white light) for ' + str(urlList[currentItem]['url']))
                dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="grey">UNMANAGED ISSUE</div></div></div>'
        else:
            # UNMANAGED UNKNOWN
            print('Unmanaged - Other HTTP error code')
            currentHeader = 'application_grey'
            currentStatus = f'<font color="orange"><b>Other error (unmanaged)</b> ({http_status})</font>'
            currentColor = 'grey'
            whiteCounter += 1
            urlList[currentItem]['payload'] = 'OTHERERROR'
            print('[ERROR] OTHERERROR (white light) for ' + str(urlList[currentItem]['url']))
            dashboardText = dashboardText + '<div class="flex-container"><div class="meh"><b>' + str(urlList[currentItem]['appname']) + '</b><div class="grey">UNMANAGED ISSUE</div></div></div>'
        print(f'- Response time history over the last 6 cycles: {urlList[currentItem]["rt_history"]}')
        currentFailtage = (failuresCntr / 6) * 100
        currentFailtage = round(currentFailtage,1)
        print(f'- Failtage: {currentFailtage}%')
        currentRespTime = (urlList[currentItem]["rt_history"][0] + urlList[currentItem]["rt_history"][1] + urlList[currentItem]["rt_history"][2] + urlList[currentItem]["rt_history"][3] + urlList[currentItem]["rt_history"][4] + urlList[currentItem]["rt_history"][5]) / 6
        currentRespTime = round(currentRespTime,1)
        dashboardText2 = dashboardText2 + '<div class="columns" title="' + urlList[currentItem]["url"] + '" onclick="window.open(\'' + dashboardBaseURL + '/' + str(currentItem) + '.html' + '\', \'_blank\');"><div class="' + currentHeader + '"><p><b class="app_name">' + str(urlList[currentItem]['appname']) + '</b><br/><font class="customer_name">' + urlList[currentItem]["customer"] + '</font></p><p><b>Failtage</b>: ' + str(currentFailtage) + '%<br/><b>Resp. time</b>: ' + str(currentRespTime) + ' seconds<br/><b>Status</b>: ' + currentStatus + '<br/><b>Deployments</b>: ' + urlList[currentItem]["latest_deployment"] + '</p></div></div>'
        print(f'- Resp. time: {currentRespTime} seconds\n')
        newLogLine = f'[ {ISOTStamp} ] instanceIdentifier={instanceIdentifier} run={epoch} cycle={cycleCntr} yyyymmdd={yyyymmdd} hhmm={hhmm} timeblock={timeblock} version={version}' + f' type=\"dashboard\" name=\"{urlList[currentItem]["appname"]}\" customer=\"{urlList[currentItem]["customer"]}\" failtage={currentFailtage} resp_time={currentRespTime} status=\"{currentStatus}\" deployments=\"{urlList[currentItem]["latest_deployment"]}\" color=\"{currentColor}\"\n'
        writeDataToFile(fullLogPath, newLogLine, 'Log updated', 'Failed to update log', 'append')
        postToSumo(newLogLine, enableSumo)
        # Write advanced analytics file
        if enableDashboard == '1':
            try:
                writeDataToFile(f'{dashboardTempFolder}{currentItem}.html','<HTML><HEAD>' + '<style>#statusDIV { width: 100%; padding: 50px 0; text-align: center; background-color: ' + currentColor + '; margin-top: 20px; }</style><script>window.setInterval("refresh()", 20000); function refresh() { window.location.reload() }</script>' + '<TITLE>' + str(currentItem) + '</TITLE><BODY><div id="statusDIV"><b>' + currentStatus + '</b></div><H1>' + str(urlList[currentItem]["appname"]) + '</H1><H2>' + str(urlList[currentItem]["customer"]) + '</H2><B>Data</B><P><UL><LI><b>URL</b>: <A HREF=\"' + str(urlList[currentItem]["url"]) + '\" target=\"_blank\">' + str(urlList[currentItem]["url"]) + '</A></LI><LI><b>HTTP status</b>: ' + str(http_status) + '</LI><LI><b>Failure history</b> (0=OK, 1=KO): ' + str(urlList[currentItem]["failure_history"]) + '</LI><LI><b>Orange since</b>: ' + str(urlList[currentItem]["orange_since"]) + '</LI><LI><b>Red since</b>: ' + str(urlList[currentItem]["red_since"]) + '</LI></UL></P><B>Log</B><P>' + newLogLine + '</P></BODY></HEAD></HTML>','Advanced analytics file updated successfully','Advanced analytics file refresh FAILED', 'overwrite')
            except Exception as e:
                print('[ERROR] Failed to update the dashboard on remote storage.\n', e)
                traceback.print_exc()
                pass
            if azureDashboard == '1':
                uploadFileToAzure(container_name, dashboardTempFolder + str(currentItem) + '.html', str(currentItem) + '.html')
            if amazonDashboard == '1':
                uploadFileToS3(dashboardTempFolder + str(currentItem) + '.html', s3BucketName, str(currentItem) + '.html')


    dashboardText = dashboardText + '</div></div>'
    dashboardText = dashboardText + '</body></html>'
    dashboardText2 = dashboardText2 + '</body></html>'
    groupedAlertS1Text += '</ul>'
    groupedAlertS2Text += '</ul>'
    # robot.say_text('Now that I am done retrieving data, I will analyze it.').wait_for_completed()
    # time.sleep(shortWait)

    # Refresh dashboard
    if enableDashboard == '1':
        writeDataToFile(dashboardUploadFilePath,dashboardText,'dashboard temporary file updated successfully','dashboard temporary file refresh FAILED', 'overwrite')
        if azureDashboard == '1':
            print(f'Updating {dashboardFile} on {azure_stor_acc_name}...')
            try:
                uploadFileToAzure(container_name, dashboardUploadFilePath, dashboardFile)
                print('...done.')
                print(f'You can check the dashboard here: {dashboardBaseURL}/{dashboardFilename}')
            except Exception as e:
                print('[ERROR] Failed to update the dashboard on remote storage.\n', e)
                traceback.print_exc()
                pass
        if amazonDashboard == '1':
            print(f'Updating {dashboardFile} on S3 bucket...')
            try:
                # writeDataToFile(fullLogPath, f'dashboardUploadFilePath: {dashboardUploadFilePath}\n', 'Log updated', 'Failed to update log', 'append')
                uploadFileToS3(f'{dashboardUploadFilePath}', s3BucketName, 'p7.html')
                print('...done.')
                print(f'You can check the dashboard here: http://{s3BucketName}/{dashboardFilename}')
            except Exception as e:
                print('[ERROR] Failed to update the dashboard on remote storage.\n', e)
                traceback.print_exc()
                pass

        # Refresh dashboard2
        writeDataToFile(dashboardUploadFilePath2,dashboardText2,'dashboard2 temporary file updated successfully','dashboard2 temporary file refresh FAILED', 'overwrite')
        if azureDashboard == '1':
            print(f'Updating {dashboardFile2} on {azure_stor_acc_name}...')
            try:
                uploadFileToAzure(container_name, dashboardUploadFilePath2, dashboardFile2)
                print('...done.')
                print(f'You can check the dashboard here: {dashboardBaseURL}/{advancedDashboardFilename}')
            except Exception as e:
                print('[ERROR] Failed to update the dashboard on remote storage.\n', e)
                traceback.print_exc()
                pass
        if amazonDashboard == '1':
            print(f'Updating {dashboardFile} on S3 bucket...')
            try:
                # writeDataToFile(fullLogPath, f'dashboardUploadFilePath2: {dashboardUploadFilePath2}\n', 'Log updated', 'Failed to update log', 'append')
                uploadFileToS3(f'{dashboardUploadFilePath2}', s3BucketName, 'p7adv.html')
                print('...done.')
                print(f'You can check the dashboard here: {s3BucketName}/{advancedDashboardFilename}')
            except Exception as e:
                print('[ERROR] Failed to update the dashboard on remote storage.\n', e)
                traceback.print_exc()
                pass

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
    # post_message_to_slack(slackLogChannel, slackStatusText, ':coc1:', enableSlack)
    if publishNewGKAdvice == 'yes':
        post_message_to_slack(slackGKAdviceChannel, slackStatusText, ':coc1:', enableSlack)
        postMessageToMSTeams(slackStatusText, 'C0C0C0', '', 'normal')

    if groupAlerts == 1:
        postMessageToMSTeams('Protocol/7 grouped several notifications together in order to preserve your mental health', 'FF4747', 'Alert storm', 'grouped', groupedAlertS1Text, groupedAlertS2Text)

    if firstRun == 0:
        firstRun = 1

    if redAlert == 1:
        print('[DEBUG] Red alert')
        bottomLightColor = 'red'
        bottomRemoteLightColor = '"bR":"255","bG":"0","bB":"0"'
        topLightColor = 'red'
        topRemoteLightColor = '"tR":"255","tG":"0","tB":"0"'
        # robot.set_all_backpack_lights(cozmo.lights.red_light.flash())               
    elif orangeAlert == 1:
        print('[DEBUG] Orange alert')
        bottomLightColor = 'orange'
        bottomRemoteLightColor = '"bR":"244","bG":"147","bB":"19"'
        topLightColor = 'orange'
        topRemoteLightColor = '"tR":"244","tG":"147","tB":"19"'
        # robot.set_center_backpack_lights(cozmo.lights.Light(cozmo.lights.Color(rgb=(244,147,19))).flash())
    else:
        print('[DEBUG] No red or orange alert')
        bottomLightColor = 'green'
        bottomRemoteLightColor = '"bR":"0","bG":"255","bB":"0"'
        if redAlertSent == 1:
            redAlertSent = 0
        if orangeAlertSent == 1:
            orangeAlertSent = 0
        # robot.set_center_backpack_lights(cozmo.lights.green_light.flash())
        if yellowCounter != 0:
            topLightColor = 'yellow'
            topRemoteLightColor = '"tR":"250","tG":"250","tB":"5"'
        elif whiteCounter != 0:
            topLightColor = 'white'
            topRemoteLightColor = '"tR":"255","tG":"255","tB":"255"'
        elif pinkCounter != 0:
            topLightColor = 'deeppink'
            topRemoteLightColor = '"tR":"247","tG":"0","tB":"115"'
        elif blueCounter != 0:
            topLightColor = 'blue'
            topRemoteLightColor = '"tR":"0","tG":"0","tB":"255"'
        else:
            topLightColor = 'green'
            topRemoteLightColor = '"tR":"0","tG":"255","tB":"0"'

    # Time for Cozmo to talk
    if robotText != '':
        # robotText = 'We have: ' + robotText
        # robot.say_text(robotText).wait_for_completed()
        time.sleep(shortWait)

    # Display debug info
    print(f'[DEBUG] bottomLightColor={bottomLightColor} topLightColor={topLightColor} redAlert={redAlert} orangeAlert={orangeAlert} redAlertSent={redAlertSent} orangeAlertSent={orangeAlertSent}')
    print(f'[DEBUG] bottomRemoteLightColor={bottomRemoteLightColor} topRemoteLightColor={topRemoteLightColor}')
    print(f'[DEBUG] enableLocalBStick={enableLocalBStick} enableRemoteBStick={enableRemoteBStick} enableCozmo={enableCozmo} enableSlack={enableSlack} enableSumo={enableSumo} enableDashboard={enableDashboard}')

    # Log debug info
    postToSumo(f'[DEBUG] bottomLightColor={bottomLightColor} topLightColor={topLightColor} redAlert={redAlert} orangeAlert={orangeAlert} redAlertSent={redAlertSent} orangeAlertSent={orangeAlertSent}', enableSumo)
    postToSumo(f'[DEBUG] bottomRemoteLightColor={bottomRemoteLightColor} topRemoteLightColor={topRemoteLightColor}', enableSumo)
    postToSumo(f'[DEBUG] enableLocalBStick={enableLocalBStick} enableRemoteBStick={enableRemoteBStick} enableCozmo={enableCozmo} enableSlack={enableSlack} enableSumo={enableSumo} enableDashboard={enableDashboard}', enableSumo)
    print(f'[DEBUG] dashboardBaseURL: {dashboardBaseURL}, s3BucketName: {s3BucketName}, advancedDashboardFilename: {advancedDashboardFilename}, Dashboard URL in Teams: {dashboardBaseURL}/{advancedDashboardFilename}, Dashboard URL in Slack: http://{s3BucketName}/{advancedDashboardFilename}')

    print(Fore.RED + '[Protocol/7] ' + Fore.BLUE + '\nEnd of cycle. Next cycle in ' + str(cycleDuration) + ' seconds.')
    print('Now waiting for next cycle to begin', end='', flush=True)

    update_remote_bstick_nano(bottomRemoteLightColor, '"tR":"0","tG":"0","tB":"255"', 'on', 'flash', enableRemoteBStick, instanceIdentifier)
    for currentStep in range (0,32):
        bstickStatus = update_local_bstick_nano(bottomLightColor, topLightColor, 'flash', enableLocalBStick)
        # bstickStatus = bstick_control(bottomLightColor, topLightColor, currentStep, enableLocalBStick)
        print('.', end='', flush=True)
        time.sleep(1)

# cozmo.run_program(cozmo_program)
