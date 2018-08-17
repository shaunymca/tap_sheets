#!/usr/bin/env python3


import sys
import json
import logging
import random
import time
from ratelimiter import RateLimiter
from jsonschema import validate
import singer
import singer.messages
import singer.metrics as metrics
from singer import utils
from singer import (UNIX_MILLISECONDS_INTEGER_DATETIME_PARSING,
                    Transformer, _transform_datetime)
from singer.catalog import Catalog, CatalogEntry

import httplib2

from googleapiclient import discovery
from googleapiclient.http import set_user_agent
from googleapiclient.errors import HttpError
from oauth2client import client, GOOGLE_TOKEN_URI, GOOGLE_REVOKE_URI
from oauth2client import tools
from oauth2client.file import Storage

import tap_sheets.conversion as conversion

LOGGER = singer.get_logger()

REQUIRED_CONFIG_KEYS = [
    "client_id",
    "client_secret",
    "refresh_token"
]

rate_limiter = RateLimiter(max_calls=100, period=100)

def get_service(config, name, version):
    credentials = client.OAuth2Credentials(
        None,
        config.get('client_id'),
        config.get('client_secret'),
        config.get('refresh_token'),
        None,
        GOOGLE_TOKEN_URI,
        None,
        revoke_uri=GOOGLE_REVOKE_URI)
    http = credentials.authorize(httplib2.Http())
    user_agent = config.get('user_agent')
    if user_agent:
        http = set_user_agent(http, user_agent)
    return discovery.build(name, version, http=http, cache_discovery=False)

def do_discover(driveService, sheetsService, config):
    LOGGER.info("Starting discover")
    catalog = discover_catalog(driveService, sheetsService, config)
    print(catalog)
    json.dump(catalog, sys.stdout, indent=2)
    LOGGER.info('Finished Discover')
    
def discover_catalog(driveService, sheetsService, config):
    #Gets sheet information for Docs present in account

    buildSchema = []
    tempSchema = sheetsList(None, driveService, sheetsService, config)
    nextPageToken = tempSchema.pop("nextPageToken")
    buildSchema = tempSchema["schema_data"]
    while nextPageToken != None:
        tempSchema = sheetsList(nextPageToken)
        nextPageToken = tempSchema.pop("nextPageToken")
        buildSchema.append(tempSchema["schema_data"])
    print(buildSchema)
    return Catalog(buildSchema).to_dict()

def sheetsList(pageToken, driveService, sheetsService, config):
    nextPageToken = None
    result = driveService.files().list(orderBy="modifiedTime desc", q='mimeType=\'application/vnd.google-apps.spreadsheet\'', includeTeamDriveItems=None, pageSize=1000, pageToken=pageToken, corpora=None, supportsTeamDrives=None, spaces=None, teamDriveId=None, corpus=None).execute()
    nextPageToken = result.get('nextPageToken')
    files = result.get('files', [])
    tabList = []
    schema_data = []
    for row in files:
        tabList = tabsInfo(sheetsService, row)
        schema_data = schema_data + tabList
    result = {"schema_data" : schema_data, "nextPageToken" : nextPageToken}
    
    return(result)
    
def tabsInfo(sheetsService, row):
    result = []
    with rate_limiter:
        tabs = makeRequestWithExponentialBackoff(sheetsService, row)
    LOGGER.info("starting tab loop")
    #LOGGER.info(tabs)
    for tab_id, tab in enumerate(tabs["sheets"]):
        #LOGGER.info("creating CatalogEntry for")
        #LOGGER.info(tab_id)
        sheet_id = row['id']
        sheet_name = row['name'].lower().replace(" ", "")
        tab_id = str(tab_id)
        tab_name = tab["properties"]["title"].lower().replace(" ", "")
        #print(sheet_id + "?" + sheet_name + "?" + tab_id + "?" + tab_name + "?" + sheet_name + "_" + tab_name)
        entry = CatalogEntry(
            tap_stream_id = sheet_id + "?" + sheet_name + "?" + tab_id + "?" + tab_name + "?" + sheet_name + "_" + tab_name,
            stream = tab["properties"]["title"].lower().replace(" ", ""),
            database = row['name'].lower().replace(" ", "") + '&' + row['id'],
            table = tab["properties"]["title"].lower().replace(" ", "") + '&' + str(tab_id),
        )
        result.append(entry)
        LOGGER.info(entry)
        LOGGER.info("ending this tab")
    return(result)
     
def makeRequestWithExponentialBackoff(sheetsService, row):
  """Wrapper to request Google Sheets data with exponential backoff.

  Returns:
    The API response from the makeRequest method.
  """
  for n in range(0, 5):
    try:
        LOGGER.info('trying')
        sheet = sheetsService.spreadsheets().get(
        spreadsheetId=row['id']).execute()
        LOGGER.info(sheet)
        LOGGER.info('succedded')
        return sheet

    except HttpError as error:
        if error.resp.reason in ['Too Many Requests', 'userRateLimitExceeded', 'quotaExceeded',
                               'internalServerError', 'backendError']:
            time.sleep((2 ** n) + random.random())
        else:
            LOGGER.info(error.resp.reason)
            break

  print("There has been an error, the request never succeeded.")

def do_sync(sheetsService, config, catalog):
    for stream in catalog["streams"]:
        new_properties = stream["tap_stream_id"].split("?")
        json = get_data(sheetsService, new_properties[0])
        data_schema = conversion.generate_schema(json)
        table_name = new_properties[1] + "_" + new_properties[3]
        #LOGGER.info(data_schema)
        write_schema = [table_name,
                {'properties':data_schema},
                '']
        singer.write_schema(
                table_name,
                {'properties':data_schema},
                ''
                )
        for record in json:
            
            to_write = conversion.convert_row(record, data_schema)
            singer.write_record(table_name, to_write)

def get_data(sheetsService, spreadsheetId):
    rangeName = 'A1:ZZZ'
    result = sheetsService.spreadsheets().values().get(
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
    return(json)

def main():
    parsed_args = singer.utils.parse_args(REQUIRED_CONFIG_KEYS)
    config = parsed_args.config
    driveService = get_service(config, 'drive', 'v3')
    sheetsService = get_service(config, 'sheets', 'v4')
    if parsed_args.discover:
        do_discover(driveService, sheetsService, config)
    elif parsed_args.properties:
        do_sync(sheetsService, config, parsed_args.properties)
