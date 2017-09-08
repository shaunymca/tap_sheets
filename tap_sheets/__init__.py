#!/usr/bin/env python3

import argparse
import functools
import io
import os
import sys
import json
import logging
import collections
import threading
import http.client
import urllib
import pkg_resources
import time

from jsonschema import validate
import singer
import singer.messages
import singer.metrics as metrics
from singer import utils
from singer import (transform,
                    UNIX_MILLISECONDS_INTEGER_DATETIME_PARSING,
                    Transformer, _transform_datetime)
from singer.catalog import Catalog, CatalogEntry

import httplib2

from apiclient import discovery
from oauth2client import client

LOGGER = singer.get_logger()

import time

def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate


# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
CONFIG = {}

def get_credentials():
    """Gets valid user credentials from creds.
    Returns:
        Credentials, the obtained credential.
    """

    return client.OAuth2Credentials(None, CONFIG['oauth_client_id'], CONFIG['oauth_client_secret'], CONFIG['refresh_token'], None, "https://www.googleapis.com/oauth2/v4/token", "stitch")

def do_discover():
    """ Gets sheet information for Docs present in account """
    buildSchema = []
    tempSchema = sheetsList(None)
    nextPageToken = tempSchema.pop("nextPageToken")
    buildSchema = tempSchema["schema_data"]
    while nextPageToken != None:
        tempSchema = sheetsList(nextPageToken)
        nextPageToken = tempSchema.pop("nextPageToken")
        buildSchema.append(tempSchema["schema_data"])
    print(buildSchema)

def sheetsList(pageToken):
    nextPageToken = None
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    # drive docs - https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.files.html#list
    # sheets docs - https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/sheets_v4.spreadsheets.values.html#get
    driveService = discovery.build('drive', 'v3', http=http, cache_discovery=False)
    sheetsService = discovery.build('sheets', 'v4', http=http, cache_discovery=False)
    result = driveService.files().list(orderBy=None, q='mimeType=\'application/vnd.google-apps.spreadsheet\'', includeTeamDriveItems=None, pageSize=1000, pageToken=pageToken, corpora=None, supportsTeamDrives=None, spaces=None, teamDriveId=None, corpus=None).execute()
    nextPageToken = result.get('nextPageToken')
    files = result.get('files', [])
    tabList = []
    schema_data = []
    for row in files:
        tabList = tabsInfo(sheetsService, row)
        schema_data = schema_data + tabList
    result = {"schema_data" : schema_data, "nextPageToken" : nextPageToken}

    return(result)

@RateLimited(1)
def tabsInfo(sheetsService, row):
    result = []
    tabs = sheetsService.spreadsheets().get(
        spreadsheetId=row['id']).execute()
        #spreadsheetId=row['id']).execute()
    for tab_id, tab in enumerate(tabs["sheets"]):
        entry = CatalogEntry(
            row_count = tab["properties"]["gridProperties"]["rowCount"],
            #database_name = row['id'],
            table = tab["properties"]["title"].lower().replace(" ", ""),
            stream = tab["properties"]["title"].lower().replace(" ", ""),
            tap_stream_id = row['name'].lower().replace(" ", "") + '-' + tab["properties"]["title"].lower().replace(" ", "")
        )

        result.append(entry)
    return(result)

def do_sync(properties):
    """Shows basic usage of the Sheets API.

    Creates a Sheets API service object and prints the names and majors of
    students in a sample spreadsheet:
    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl, cache_discovery=False)

    spreadsheetId = properties[0]["streams"][0]["tap_stream_id"]
    rangeName = 'A1:D'


    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName, dateTimeRenderOption='FORMATTED_STRING', majorDimension='ROWS').execute()
    values = result.get('values', [])
    header_row = values[0]
    json = []
    if not values:
        print('No data found.')
    else:
        for counter, row in enumerate(values):
            if counter != 0:
                record = {}
                for column_id, value in enumerate(row):
                    record[header_row[column_id]] = row[column_id]
                json.append(record)
    print(json)

def main():
    args = utils.parse_args(
        ["oauth_client_id",
         "oauth_client_secret",
         "refresh_token"])
    print(args)
    CONFIG.update(args.config)
    STATE = {}

    if args.state:
        STATE.update(args.state)

    if args.discover:
        do_discover()
    elif args.properties:
        do_sync(args.properties)
    else:
        LOGGER.info("No properties were selected")

if __name__ == '__main__':
    main()
