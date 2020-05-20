#!/usr/bin/env python3

# Cozmo Office Companion

import datetime
import time
import os
import sys
import random
import urllib.request
import urllib.error
import json
import traceback
import boto3

databaseURL = os.environ.get('DYNAMODBURL')

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
        if tableName == 'cfg_nrvio_track':
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
                # print(i)
                print(i['label'])
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


if dynamodbTableCheck(databaseURL, 'cfg_nrvio_track') == 'Table not found':
    # Table missing - creating
    if dynamodbCreateTable(databaseURL, 'cfg_nrvio_track') == 'Table created':
        # Table created - provisioning
        if dynamodbProvisionTable(databaseURL, 'cfg_nrvio_track') == 'Provisioning successful':
            print('New table cfg_nrvio_track created and provisioned.')
            print(dynamodbListTableItems(databaseURL, 'cfg_nrvio_track'))
            print(dynamodbReadFromTable(databaseURL, 'cfg_nrvio_track'))
        else:
            print('Provisioning of table cfg_nrvio_track failed :-(')
    else:
        print('Creation of table table cfg_nrvio_track failed :-(')
else:
    print('Table cfg_nrvio_track exists, nothing to do.')

if dynamodbDeleteTable(databaseURL, 'cfg_nrvio_track'):
    print('Table cfg_nrvio_track deleted.')
else:
    print('Table cfg_nrvio_track deletion failed :-(')