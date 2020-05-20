import os
import time
import re
import urllib.request
import urllib.parse
import json
from slackclient import SlackClient
import traceback
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from joblib import load
from argparse import ArgumentParser
import boto3
from colorama import Fore, Style, init
import threading

init(autoreset=True)

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

version='0.49-11'

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
prodSNOWBase64 = os.environ.get('PRODSNOWBASE64')
mengSNOWBase64 = os.environ.get('MENGSNOWBASE64')
# starterbot's user ID in Slack: value is assigned after the bot starts up
chatbotone_id = None
eventsList = {}
freshINCList = {}

# Production ServiceNow
snowBase64 = prodSNOWBase64
prodSNOW = 'https://auspostprod.service-now.com'
assignmentGroupID = 'a4a7b6f6f9333000c9094e564e146550'
prodYestIncQuery = '/api/now/table/incident?sysparm_fields=number,short_description,description,sys_id,state,priority&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^assigned_to=^sys_class_name=incident^opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()'
prodFreshIncQuery = '/api/now/table/incident?sysparm_fields=number,description,short_description,sys_id,state,priority&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^assigned_to=^sys_class_name=incident^opened_atONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()'
prodRecentIncQuery = '/api/now/table/incident?sysparm_fields=number,description,short_description,sys_id,state,priority&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^assigned_to=^sys_class_name=incident^opened_atONLast7days@javascript:gs.beginningOfLast7Days()@javascript:gs.endOfLast7Days()'
prodOldIncQuery = '/api/now/table/incident?sysparm_fields=number,description,short_description,sys_id,state,priority&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^assigned_to=^sys_class_name=incident^opened_atONLast3months@javascript:gs.beginningOfLast3Months()@javascript:gs.endOfLast3Months()^opened_atNOTONThismonth@javascript:gs.beginningOfThisMonth()@javascript:gs.endOfThisMonth()'
prodPickIncQuery = '/api/now/table/incident?sysparm_fields=number,description,short_description,sys_id,state,priority&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^assigned_to=^sys_class_name=incident'
prodStatsIncQuery = '/api/now/table/incident?sysparm_fields=number,state&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^sys_class_name=incident'
prodStatsReqQuery = '/api/now/table/u_request?sysparm_fields=number,state&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true'
prodStatsChgQuery = '/api/now/table/change_request?sysparm_fields=number,state&sysparm_query=assignment_group=' + assignmentGroupID + '^active=true^sys_class_name=change_request'
# Meng ServiceNow
mengSNOW = 'https://dev67853.service-now.com'
mengYestIncQuery = '/api/now/table/incident?sysparm_fields=number,short_description,description,sys_id&sysparm_query=caller_id=javascript:gs.getUserID()^active=true^opened_atONYesterday@javascript:gs.beginningOfYesterday()@javascript:gs.endOfYesterday()'
mengFreshIncQuery = '/api/now/table/incident?sysparm_fields=number,short_description,description,sys_id,work_notes&sysparm_query=caller_id=javascript:gs.getUserID()^active=true^opened_atONToday@javascript:gs.beginningOfToday()@javascript:gs.endOfToday()'
mengRecentIncQuery = '/api/now/table/incident?sysparm_fields=number,short_description,description,sys_id&sysparm_query=caller_id=javascript:gs.getUserID()^active=true^opened_atONLast7days@javascript:gs.beginningOfLast7Days()@javascript:gs.endOfLast7Days()'
mengOldIncQuery = '/api/now/table/incident?sysparm_fields=number,short_description,description,sys_id&sysparm_query=caller_id=javascript:gs.getUserID()^active=true^opened_atONLast3months@javascript:gs.beginningOfLast3Months()@javascript:gs.endOfLast3Months()^opened_atNOTONThismonth@javascript:gs.beginningOfThisMonth()@javascript:gs.endOfThisMonth()'
mengPickIncQuery = ''
mengStatsIncQuery = ''
mengStatsReqQuery = ''
mengStatsChgQuery = ''
snowIgnoreList = []

snowURL = prodSNOW
yestIncQuery = prodYestIncQuery
freshIncQuery = prodFreshIncQuery
recentIncQuery = prodRecentIncQuery
oldIncQuery = prodOldIncQuery
pickIncQuery = prodPickIncQuery
statsIncQuery = prodStatsIncQuery
statsChgQuery = prodStatsChgQuery
statsReqQuery = prodStatsReqQuery

# Path to data folder (contains ML stuff)
cb1DataFolder = os.environ.get('CB1DATAFOLDER')
if not os.path.exists(cb1DataFolder):
    os.makedirs(cb1DataFolder)

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = 'do'
MENTION_REGEX = '^<@(|[WU].+?)>(.*)'

def testMultithread(argument):
    print(threading.currentThread().getName(), f'Running with argument {argument}...')

def translateBusinessCriticality(x):
    print(Fore.LIGHTGREEN_EX + 'translateBusinessCriticality')
    return {
        '0': 0,
        '1': 5000,
        '2': 4000,
        '3': 3000,
        '4': 2000,
        '5': 1000
    }.get(x, 0)

def publishToSlack(msg, chan, icon, creds):
    try:
        print(Fore.LIGHTGREEN_EX + 'publishToSlack')
        slackCallbackId=''
        slackColor='#3AA3E3'
        slackActionName=''
        slackActionText=''
        slackActionType=''
        slackActionValue=''
        creds.api_call(
            'chat.postMessage',
            channel=chan,
            text=msg,
            icon_emoji=icon,
            as_user='true',
            attachments=[{
                'text': '',
                'callback_id': slackCallbackId + 'autoassign_feedback',
                'color': slackColor,
                'attachment_type': 'default',
                'actions': [{
                'name': slackActionName,
                'text': slackActionText,
                'type': slackActionType,
                'value': slackActionValue
                }]
            }]
        )
    except Exception as e:
        print(Fore.RED + '[ERROR] A problem occured while publishing on Slack.', e)
        pass

def pickSnowTicket(queryToRun, creds, saveTo, okMsg, koMsg):
    try:
        print(Fore.LIGHTGREEN_EX + 'pickSnowTicket')
        # print('URL: ' + queryToRun)
        chosenINC = ''
        snowTicketsList = {}
        urgencyWords = ['ombudsman','court','tribunal','urgent','emergency','angry','dissatisfied','escalation','attorney','lawyer','threat', 'extreme', 'annoy', 'complain', 'insult', 'upset', 'ludicrous', 'unworkable', 'absurd', 'attack']
        snowStatesToExclude = ['3','4','-16','10','6','900','-101','-102','-40']
        response = "Picking one ServiceNow INCident based on urgency, assignment accuracy and activity...\n\n"
        url = queryToRun
        snow_creds_hdr = {'Authorization': 'Basic ' + creds}
        payload = callURL(url, snow_creds_hdr)
        cont = json.loads(payload.decode('utf-8'))
        # print(str(type(cont)))
        if str(cont) != "{'result': []}":
            threads = []
            for item in cont['result']:
                # t = threading.Thread(target=testMultithread, args=(item['number'],))
                # threads.append(t)
                # t.start()
                if (item['state'] not in snowStatesToExclude) and (item['number'] not in snowIgnoreList):
                    print(Fore.BLUE + f"\nNow inspecting {item['number']} (state: {item['state']})")
                    # Saving INC description to disk
                    cb1DataFolder = saveTo
                    pathToCB1File = cb1DataFolder + item['number'] + ".cb1"
                    writeDataToFile(pathToCB1File,item['description'],"Incident description saved in " + pathToCB1File,"")
                    # U: Urgency words check
                    urgencyScore = 0
                    for currentWord in urgencyWords:
                        if (currentWord in item['description'].lower()) or (currentWord in item['short_description'].lower()):
                            urgencyScore += 10
                    url2 = snowURL + '/api/now/table/sys_journal_field?sysparm_query=element_id=' + item['sys_id']
                    print(f'Calling {url2}')
                    payload2 = callURL(url2, snow_creds_hdr)
                    cont2 = json.loads(payload2.decode('utf-8'))
                    # WN: Count work notes
                    workNotes = str(cont2)
                    wnCount = workNotes.count('work_notes')
                    # print(f'Work notes: {workNotes}')
                    # print(f'Work notes count: {wnCount}')
                    pathToCB1File = cb1DataFolder + item['number'] + '.cb1'
                    # ML: should this INC be assigned to us or not ?
                    predictorSaid = predictor(pathToCB1File)
                    a, b, c, d = str(predictorSaid)
                    # BC: Business criticality
                    businessCrit = translateBusinessCriticality(item['priority'])
                    # SCORE
                    score = businessCrit + (int(b) * 100) + urgencyScore + wnCount
                    snowTicketsList[item['number']] = {'number':item['number'], 'short_description':item['short_description'], 'description':item['description'], 'sys_id':item['sys_id'], 'bc':businessCrit, 'ml': (int(b) * 100), 'urgency':urgencyScore, 'worknotes':wnCount, 'score':score}
                    print(Fore.LIGHTMAGENTA_EX + f'Score: {score}\n')
                    # print('-----------')
                else:
                    print('[REJECTED] Ticket ' + str(item['number']) + ' has a forbidden state (' + str(item['state']) + ').')
            bestScore = -1
            for currentINC in snowTicketsList:
                if snowTicketsList[currentINC]['score'] > bestScore:
                    bestScore = snowTicketsList[currentINC]['score']
                    chosenINC = snowTicketsList[currentINC]
        if chosenINC != '':
            print(Fore.MAGENTA + "\nBest score: " + Fore.WHITE + f"{chosenINC['number']} - {chosenINC['short_description']} " + Fore.GREEN + f"BC: {chosenINC['bc']} ML: {chosenINC['ml']} U: {chosenINC['urgency']} WN: {chosenINC['worknotes']}")
            response = '- *' + str(chosenINC['number']) + '* ' + str(chosenINC['short_description']) + ' [B:' + str(chosenINC['bc']) + '/ML:' + str(chosenINC['ml']) + '/U:' + str(chosenINC['urgency']) + '/WN:' + str(chosenINC['worknotes']) + ']' + '\n> ' + snowURL + '/nav_to.do?uri=incident.do?sys_id=' + str(chosenINC['sys_id']) + '\n'
        else:
            response = koMsg
        return response
    except Exception as e:
        print('[ERROR] A problem occured while choosing a ServiceNow ticket.', e)
        chosenINC = '[ERROR] A problem occured while choosing a ServiceNow ticket.'
        return chosenINC
        pass

def callURL(url2call, creds):
    try:
        print(Fore.LIGHTGREEN_EX + 'callURL')
        url = url2call
        req = urllib.request.Request(url, headers=creds)
        response = urllib.request.urlopen(req)
        payload = response.read()
        return payload
    except urllib.error.HTTPError:
        print(Fore.RED + '[HTTPError] Failed to call ' + str(url) + '\nProvider might be down or credentials might have expired.')
        return 'HTTPERROR'
        pass
    except urllib.error.URLError:
        print(Fore.RED + '[URLError] Failed to call ' + str(url) + '\nNetwork connection issue (check Internet access).')
        return "URLERROR"
        pass

def dynamodbTableCheck(databaseURL, tableName):
    try:
        print(Fore.LIGHTGREEN_EX + 'dynamodbTableCheck')
        dynamodb = boto3.client('dynamodb', endpoint_url=databaseURL)
        response = dynamodb.describe_table(TableName=tableName)
    # except dynamodb.exceptions.ResourceNotFoundException:
    except Exception as e:
        print('[DEBUG] DynamoDB table ' + tableName + ' not found')
        response = 'Table not found'
        # traceback.print_exc()
        pass
    return str(response)

def dynamodbListTableItems(databaseURL, tableName):
    try:
        print(Fore.LIGHTGREEN_EX + 'dynamodbListTableItems')
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

def predictor(pathToCB1File):
    print(Fore.LIGHTGREEN_EX + 'predictor')
    # This function is based on code produced by Shuo Zhao <shuo.zhao@auspost.com.au>
    class TfidfRandomForestPredictor():
        def __init__(self, model_file, vectorizer_file):
            self.tfidf = load(vectorizer_file)
            self.classifier = load(model_file)

        def predict(self, text):
            input_matrix = self.tfidf.transform([textToProcess])
            return self.classifier.predict(input_matrix)

    currentCB1File = open(pathToCB1File, 'r')
    currentDescription = currentCB1File.readlines()
    textToProcess = ''.join(currentDescription)
    currentCB1File.close()

    predictor = TfidfRandomForestPredictor('./models/rf_classifier_0403.joblib', './models/tfidf_vectorizer_0403.joblib')
    result = predictor.predict(textToProcess)
    return result

def cleanupIncDesc(pathToCB1File):
    print(Fore.LIGHTGREEN_EX + 'cleanupIncDesc')
    stopWords = set(stopwords.words('english'))
    crapWords = [';', ':', '-', '.', ',', '(', ')', '[', ']', '&', '--', '#']
    wordnet_lemmatizer = WordNetLemmatizer()
    wordsFiltered = []

    currentCB1File = open(pathToCB1File, 'r')
    currentDescription = currentCB1File.readlines()
    currentCB1File.close()
    for g in currentDescription:
        currentCB1File = open(pathToCB1File + '.processed', 'w')
        currentCB1File.write('--- FILTERED DATA ---\n')
        # Remove empty lines + crap characters
        if g != '' and g!='\n':
            tokens = nltk.word_tokenize(g)
            for w in tokens:
                if (w.lower() not in stopWords) and (w.lower() not in crapWords):
                    word_lemme = wordnet_lemmatizer.lemmatize(w.lower())
                    wordsFiltered.append(word_lemme)
    currentCB1File.write(str(wordsFiltered))
    currentCB1File.write('\n--- *** ---')
    currentCB1File.close()
    print('Cleaned up description:\n')
    print(str(wordsFiltered))

def initEventsTree(userId, eventsTreeName, eventsList):
    print(Fore.LIGHTGREEN_EX + 'initEventsTree')
    print("initEventsTree: " + str(userId) + ", " + str(eventsTreeName) + ", " + str(eventsList))
    if eventsTreeName == 'bilbo':
        # Menu
        eventsList[userId] = {'ts': 1550056556.000300, 'expires': 1550111111.000300, 'text': '*Welcome to Bilbo interactive game*\n\nStart new game ?\n- yes\n- no', 'option1': 'yes', 'action1': 'bilbo_yes', 'option2': 'no', 'action2': 'bilbo_no', 'option3': None, 'action3': None, 'url': None, 'eventId': 'bilbo_start', 'callFunction': None, 'step': 'ping'}
        # bilbo_yes
        eventsList['bilbo_yes'] = {'ts': 0, 'expires': 0, 'text': '*Initializing a new game...*\nYou now are in a hobbit hole.\n- explore\n- leave', 'option1': 'explore', 'action1': 'bilbo_explore', 'option2': 'leave', 'action2': 'bilbo_leave', 'option3': None, 'action3': None, 'url': None, 'eventId': None, 'callFunction': None, 'step': 'ping'}
        # bilbo_no
        eventsList['bilbo_no'] = {'ts': 0, 'expires': 0, 'text': '*Goodbye, come again !*', 'option1': None, 'action1': None, 'option2': None, 'action2': None, 'option3': None, 'action3': None, 'url': None, 'eventId': None, 'callFunction': None, 'step': 'ping'}
        # bilbo_explore
        eventsList['bilbo_explore'] = {'ts': 0, 'expires': 0, 'text': 'The inside of the hole is very clean. The wooden floor shines. The windows are round.\n- leave', 'option1': 'leave', 'action1': 'bilbo_leave', 'option2': None, 'action2': None, 'option3': None, 'action3': None, 'url': None, 'eventId': None, 'callFunction': None, 'step': 'ping'}
        # bilbo_leave
        eventsList['bilbo_leave'] = {'ts': 0, 'expires': 0, 'text': 'The sky is cloudy and you feel a few drops falling on your arms and head.\n*This very short game ends here.*', 'option1': None, 'action1': None, 'option2': None, 'action2': None, 'option3': None, 'action3': None, 'url': None, 'eventId': None, 'callFunction': None, 'step': 'ping'}
    return eventsList

def writeDataToFile(targetFile,dataToWrite,successMsg,failureMsg):
    print(Fore.LIGHTGREEN_EX + 'writeDataToFile')
    newCB1File = open(targetFile,'w')
    newCB1File.write(dataToWrite)
    newCB1File.close()
    print(successMsg)

def parse_bot_commands(slack_events):
    # print(Fore.LIGHTGREEN_EX + 'parse_bot_commands')
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event['type'] == 'message' and not 'subtype' in event:
            # Expecting CB1 name at the beginning of the message
            user_id, message = parse_direct_mention(event['text'])
            if user_id == chatbotone_id:
                return message, event['user']   
    return None, None

def parse_direct_mention(message_text):
    print(Fore.LIGHTGREEN_EX + 'parse_direct_mention')
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    print(Fore.LIGHTGREEN_EX + 'handle_command')
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = 'Not sure what you mean. Try *{}*.'.format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None

    global snowBase64
    global snowURL
    global yestIncQuery
    global freshIncQuery
    global recentIncQuery
    global oldIncQuery
    global pickIncQuery
    global statsIncQuery
    global statsChgQuery
    global statsReqQuery
    global p1AlertsQuery
    global p2AlertsQuery

    # Check if we are waiting for a specific answer from user
    for key in eventsList:
        # If this is the case, change Step to pong...
        if str(key) == str(channel):
            print('We have some business to do...')
            print('ts: ' + str(eventsList[key]['ts']))
            print('expires: ' + str(eventsList[key]['expires']))
            print('text: ' + str(eventsList[key]['text']))
            print('o1: ' + str(eventsList[key]['option1']))
            print('a1: ' + str(eventsList[key]['action1']))
            print('o2: ' + str(eventsList[key]['option2']))
            print('a2: ' + str(eventsList[key]['action2']))
            print('o3: ' + str(eventsList[key]['option3']))
            print('a3: ' + str(eventsList[key]['action3']))
            print('url: ' + str(eventsList[key]['url']))
            print('eventId: ' + str(eventsList[key]['eventId']))
            print('callFunction: ' + str(eventsList[key]['callFunction']))
            print('step: ' + eventsList[key]['step'])
            eventsList[key]['step'] = 'pong'
            print('step: ' + eventsList[key]['step'])
            # ...then perform the required action
            if command == str(eventsList[key]['option1']):
                response = str(eventsList[eventsList[key]['action1']]['text'])
                eventsList[channel] = {'ts': 0, 'expires': 0, 'text': eventsList[eventsList[key]['action1']]['text'], 'option1': eventsList[eventsList[key]['action1']]['option1'], 'action1': eventsList[eventsList[key]['action1']]['action1'], 'option2': eventsList[eventsList[key]['action1']]['option2'], 'action2': eventsList[eventsList[key]['action1']]['action2'], 'option3': eventsList[eventsList[key]['action1']]['option3'], 'action3': eventsList[eventsList[key]['action1']]['action3'], 'url': eventsList[eventsList[key]['action1']]['url'], 'eventId': eventsList[eventsList[key]['action1']]['eventId'], 'callFunction': eventsList[eventsList[key]['action1']]['callFunction'], 'step': 'ping'}
                print('New event: ' + str(eventsList[channel]))
            elif command == str(eventsList[key]['option2']):
                response = str(eventsList[eventsList[key]['action2']]['text'])
                eventsList[channel] = {'ts': 0, 'expires': 0, 'text': eventsList[eventsList[key]['action2']]['text'], 'option1': eventsList[eventsList[key]['action2']]['option1'], 'action1': eventsList[eventsList[key]['action2']]['action1'], 'option2': eventsList[eventsList[key]['action2']]['option2'], 'action2': eventsList[eventsList[key]['action2']]['action2'], 'option3': eventsList[eventsList[key]['action2']]['option3'], 'action3': eventsList[eventsList[key]['action2']]['action3'], 'url': eventsList[eventsList[key]['action2']]['url'], 'eventId': eventsList[eventsList[key]['action2']]['eventId'], 'callFunction': eventsList[eventsList[key]['action2']]['callFunction'], 'step': 'ping'}
                print('New event: ' + str(eventsList[channel]))
            elif command == str(eventsList[key]['option3']):
                response = str(eventsList[eventsList[key]['action3']]['text'])
                eventsList[channel] = {'ts': 0, 'expires': 0, 'text': eventsList[eventsList[key]['action3']]['text'], 'option1': eventsList[eventsList[key]['action3']]['option1'], 'action1': eventsList[eventsList[key]['action3']]['action1'], 'option2': eventsList[eventsList[key]['action3']]['option2'], 'action2': eventsList[eventsList[key]['action3']]['action2'], 'option3': eventsList[eventsList[key]['action3']]['option3'], 'action3': eventsList[eventsList[key]['action3']]['action3'], 'url': eventsList[eventsList[key]['action3']]['url'], 'eventId': eventsList[eventsList[key]['action3']]['eventId'], 'callFunction': eventsList[eventsList[key]['action3']]['callFunction'], 'step': 'ping'}
                print('New event: ' + str(eventsList[channel]))

    # This is where you start to implement more commands!
    print(f'Command: {command}')
    if command.startswith(EXAMPLE_COMMAND):
        response = 'Sure...write some more code then I can do that!'
    elif command == 'help':
        response = "*Available commands*\n\n"
        response = response + "- `[ fresh | recent | yest | old ] inc`: SNow incidents opened [ today | last 7 days | yesterday | last 3 months ],\n"
        response = response + "- `p1` or `p2`: List P1/P2 alerts currently active,\n"
        response = response + "- `bilbo`: Start the fabulous Bilbo interactive game,\n"
        response = response + "- `snow switch prod` or `snow switch meng`: Switch between Prod & Meng ServiceNow,\n"
        response = response + "- `show contacts`: Link to a list of contacts on the wiki,\n"
        response = response + "- `snow check <INC>`: Determine if an INCident should be assigned to PENG Ops or not,\n"
        response = response + "- `snow stats`: Show number of INC, REQ & CHG,\n"
        response = response + "- `snow [ ignore | forget ] <INC>`: Set/Unset ignore flag on a ServiceNow INCident.\n"
    elif command == 'yest inc':
        print('\n\n---> yest inc')
        try:
            response = pickSnowTicket(snowURL + yestIncQuery, snowBase64, cb1DataFolder, '', 'No ServiceNow incident for yesterday. Try `recent inc`.')
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to get data from ServiceNow.\n', e)
            response = 'Failed to get data from ServiceNow. :dizzy_face:'
            pass
    elif command == 'fresh inc':
        print('\n\n---> fresh inc')
        try:
            response = pickSnowTicket(snowURL + freshIncQuery, snowBase64, cb1DataFolder, '', 'No ServiceNow incident for today. Try `yest inc`.')
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to get data from ServiceNow.\n', e)
            response = 'Failed to get data from ServiceNow. :dizzy_face:'
            pass
    elif command == 'recent inc':
        print('\n\n---> recent inc')
        try:
            response = pickSnowTicket(snowURL + recentIncQuery, snowBase64, cb1DataFolder, '', 'No ServiceNow incident for the last 7 days. Try `old inc`.')
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to get data from ServiceNow.\n', e)
            response = 'Failed to get data from ServiceNow. :dizzy_face:'
            pass
    elif command == 'old inc':
        print('\n\n---> old inc')
        try:
            response = pickSnowTicket(snowURL + oldIncQuery, snowBase64, cb1DataFolder, '', 'No ServiceNow incident for the last 3 months. Try doing some pushups !.')
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to get data from ServiceNow.\n', e)
            response = 'Failed to get data from ServiceNow. :dizzy_face:'
            pass
    elif command == 'pick inc':
        print('\n\n---> pick inc')
        try:
            response = pickSnowTicket(snowURL + pickIncQuery, snowBase64, cb1DataFolder, '', 'No ServiceNow incident since the beginning of times. Try doing some pushups !.')
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to get data from ServiceNow.\n', e)
            response = 'Failed to get data from ServiceNow. :dizzy_face:'
            pass
    elif (command == 'p1') or (command=='p2'):
        response = 'Retrieving active ' + command + ' alerts from ServiceNow...\n\n'
        response = response + '\n\n*' + command + ' alerts*:\n'
        alertPriority = command.replace('p', '')
        print('Looking for P' + alertPriority + ' alerts.')
        url = snowURL + '/api/now/table/u_alert?sysparm_fields=number,description,short_description,sys_id,ref_u_alert.u_acknowledged,ref_u_alert.u_maintenance&sysparm_query=assignment_group=0123456789^numberSTARTSWITHALT^priority=' + alertPriority + '^ref_u_alert.u_acknowledged=true^ORref_u_alert.u_maintenance=true^sys_class_name=u_alert^active=true'
        snow_creds_hdr = {'Authorization': 'Basic %s' % (snowBase64)}
        payload = callURL(url, snow_creds_hdr)
        cont = json.loads(payload.decode('utf-8'))
        for item in cont['result']:
            maintFlag='M'
            ackFlag='A'
            if item['ref_u_alert.u_maintenance'] == 'true':
                maintFlag='*M*'
            if item['ref_u_alert.u_acknowledged'] == 'true':
                ackFlag='*A*'
            response = response + '- [' + maintFlag + '/' + ackFlag + ']  *' + item['number'] + '*: ' + item['short_description'] + '\n> ' + snowURL + '/nav_to.do?uri=u_alert.do?sys_id=' + item['sys_id'] + '\n'
    elif command == 'bilbo':
        print('\n\n---> bilbo\n')
        initEventsTree(channel, 'bilbo', eventsList)
        response = eventsList[channel]['text']
    elif command == 'snow switch prod':
        print('\n\n---> snow switch prod\n')
        snowBase64 = prodSNOWBase64
        snowURL = prodSNOW
        yestIncQuery = prodYestIncQuery
        freshIncQuery = prodFreshIncQuery
        recentIncQuery = prodRecentIncQuery
        oldIncQuery = prodOldIncQuery
        statsIncQuery = prodStatsIncQuery
        statsChgQuery = prodStatsChgQuery
        statsReqQuery = prodStatsReqQuery
        p1AlertsQuery = prodP1AlertsQuery
        p2AlertsQuery = prodP2AlertsQuery
        response = 'Switching to *Production Service Now* (' + snowURL + ')'
    elif command == 'snow switch meng':
        print('\n\n---> snow switch meng\n')
        snowBase64 = mengSNOWBase64
        snowURL = mengSNOW
        yestIncQuery = mengYestIncQuery
        freshIncQuery = mengFreshIncQuery
        recentIncQuery = mengRecentIncQuery
        oldIncQuery = mengOldIncQuery
        statsIncQuery = mengStatsIncQuery
        statsChgQuery = mengStatsChgQuery
        statsReqQuery = mengStatsReqQuery
        p1AlertsQuery = mengP1AlertsQuery
        p2AlertsQuery = mengP2AlertsQuery
        response = 'Switching to *Meng Service Now* (' + snowURL + ')'
    elif command == 'show contacts':
        print('\n\n---> show contacts\n')
        response = '*MIM*: 1 300 000 000\n'
        response = response + '*MUM*: 0123 456 789\n'
        response = response + '*DAD*: 0123 456 789\n'
        response = response + '*DOCTOR*: 0123 456 789\n'
        response = response + '*PIZZA*: 0123 456 789\n'
        response = response + '*GHOSTBUSTAZ*: 0123 456 789\n'
        response = response + '\n> https://example.jira.com/wiki/spaces/DBMW/pages/0123456789/The+Big+What+To+Do+Page#TheBigWhatToDoPage-...Ineedtocontactadepartment/service'
    elif command.startswith('snow check', 0):
        print('\n\n---> snow check\n')
        try:
            splitedCommand = command.split()
            currentIncident = str(splitedCommand[2])
            print('\ncb1DataFolder: ' + str(cb1DataFolder))
            print('Incident: ' + currentIncident)
            pathToCB1File = cb1DataFolder + currentIncident + '.cb1'
            response = '*ServiceNow advisor*: ' + currentIncident
            if os.path.exists(pathToCB1File + '.processed'):
                print('INC description has already been processed.')
            elif os.path.exists(pathToCB1File):
                print('INC description has already been retrieved from ServiceNow, but not processed.')
                print('Processing ' + currentIncident + '...')
                cleanupIncDesc(pathToCB1File)
            else:
                print('INC description will be downloaded and processed...')
                print('Downloading...')
                url = snowURL + '/api/now/table/incident?sysparm_fields=number,description&sysparm_query=number=' + currentIncident + '^sys_class_name=incident'
                snow_creds_hdr = {'Authorization': 'Basic ' + snowBase64}
                payload = callURL(url, snow_creds_hdr)
                cont = json.loads(payload.decode('utf-8'))
                for item in cont['result']:
                    writeDataToFile(pathToCB1File,item['description'],'Incident description saved in ' + pathToCB1File,'')
                    print('Processing ' + item['number'] + '...')
                    cleanupIncDesc(pathToCB1File)
            if os.path.exists(pathToCB1File):
                predictorSaid = predictor(pathToCB1File)
                a, b, c, d = str(predictorSaid)
                if int(b) == 0:
                    print(Fore.YELLOW + 'Ticket should not be assigned to PENG Ops.')
                    response = response + '\nTicket should not be assigned to PENG Ops. :-1:'
                else:
                    print(Fore.GREEN + 'Ticket should be assigned to PENG Ops.')
                    response = response + '\nTicket should be assigned to PENG Ops. :+1:'
            else:
                print(Fore.RED + '[ERROR] Invalid INCident ticket number.')
                response = response + '\nInvalid INCident ticket number.'
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to get data from ServiceNow.\n', e)
            response = response + '\nFailed to get data from ServiceNow. :dizzy_face:'
            pass
    elif command == 'snow stats':
        print('\n\n---> snow stats\n')
        try:
            snowStatesToExclude = ['3','4','-16','10','6','900','-101','-102','-40']
            response = "*ServiceNow statistics*\n\n"
            # INC
            url = snowURL + statsIncQuery
            snow_creds_hdr = {'Authorization': 'Basic ' + snowBase64}
            incCount = 0
            payload = callURL(url, snow_creds_hdr)
            cont = json.loads(payload.decode('utf-8'))
            for item in cont['result']:
                if item['state'] not in snowStatesToExclude:
                    incCount += 1
            response = response + '- *INC*: ' + str(incCount)
            # REQ
            url = snowURL + statsReqQuery
            reqCount = 0
            payload = callURL(url, snow_creds_hdr)
            cont = json.loads(payload.decode('utf-8'))
            for item in cont['result']:
                if item['state'] not in snowStatesToExclude:
                    reqCount += 1
            response = response + '\n- *REQ*: ' + str(reqCount)
            # CHG
            url = snowURL + statsChgQuery
            chgCount = 0
            payload = callURL(url, snow_creds_hdr)
            cont = json.loads(payload.decode('utf-8'))
            for item in cont['result']:
                if item['state'] not in snowStatesToExclude:
                    chgCount += 1
            response = response + '\n- *CHG*: ' + str(chgCount)
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to get fresh statistics from ServiceNow.\n', e)
            response = response + 'Failed to get fresh statistics from ServiceNow. :dizzy_face:'
            pass
    elif command.startswith('snow ignore', 0):
        print('\n\n---> snow ignore\n')
        try:
            splitedCommand = command.split()
            currentIncident = str(splitedCommand[2])
            print('\ncb1DataFolder: ' + str(cb1DataFolder))
            print('Incident: ' + currentIncident)
            pathToCB1File = cb1DataFolder + currentIncident + '.cb1'
            response = '*Ignore flag set on ServiceNow INCident*: ' + currentIncident
            snowIgnoreList.append(currentIncident)
            print(f'snowIgnoreList: {snowIgnoreList}')
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to set ignore flag on ServiceNow INCident.\n', e)
            response = response + 'Failed to set ignore flag on ServiceNow INCident. :dizzy_face:'
            pass
    elif command.startswith('snow forget', 0):
        print('\n\n---> snow forget\n')
        try:
            splitedCommand = command.split()
            currentIncident = str(splitedCommand[2])
            print('\ncb1DataFolder: ' + str(cb1DataFolder))
            print('Incident: ' + currentIncident)
            pathToCB1File = cb1DataFolder + currentIncident + '.cb1'
            response = '*Cancel ignore flag on ServiceNow INCident*: ' + currentIncident
            snowIgnoreList.remove(currentIncident)
            print(f'snowIgnoreList: {snowIgnoreList}')
        except Exception as e:
            print(Fore.RED + '[ERROR] Failed to cancel ignore flag on ServiceNow INCident.\n', e)
            response = response + 'Failed to cancel ignore flag on ServiceNow INCident. :dizzy_face:'
            pass

    # Sends the response back to the channel
    publishToSlack(response or default_response, channel, ':coc1:', slack_client)

if __name__ == '__main__':
    if slack_client.rtm_connect(with_team_state=False, auto_reconnect=True):
        print(Fore.RED + '#############################')
        print(Fore.RED + '#        Chat Bot One       #')
        print(Fore.RED + '#############################')
        print(Fore.GREEN + f'\n\nVersion {version} connected and running !\nREADY>')
        # Read bot's user ID by calling Web API method `auth.test`
        chatbotone_id = slack_client.api_call('auth.test')['user_id']
        # print('Chatbotone_id: ' + str(chatbotone_id))
        while True:
            try:
                command, channel = parse_bot_commands(slack_client.rtm_read())
            except Exception as e:
                print(Fore.RED + '[ERROR] Failed to connect to Slack\n', e)
                traceback.print_exc()
                pass
                try:
                    print(Fore.RED + '[ERROR] Damn Slack')
                except Exception as f:
                    print(Fore.RED + '[ERROR] Damn damn\n', f)
                    pass
                time.sleep(4)
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print(Fore.RED + '[ERROR] Connection failed. Exception traceback printed above.')
