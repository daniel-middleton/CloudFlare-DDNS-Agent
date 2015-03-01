#!/usr/bin/env python

###############################################################################
# Name:          CloudFlare DDNS Agent
# Author:        Daniel Middleton <me@daniel-middleton.com>
# Description:   Dynamic DNS agent for the CloudFlare API
# Prerequisites: Python (tested 2.7.6)
# Usage:         Cron: "0 * * * * /path-to-script/cloudflare-ddns-agent.py"
###############################################################################

# Imports
import sys
import requests
import json
import logging
import logging.handlers

############################ CloudFlare config ################################

# API credentials
EMAIL           =       'YOUR-NAME@YOUR-DOMAIN.TLD'
API_KEY         =       'YOUR-API-KEY'

# Zone name
ZONE            =       'YOUR-ZONE.TLD'

# Names of A records to update, add more lines as required
names = []
names.append(ZONE) # Root domain
names.append('www')

############################## End of config ##################################

# Other globals
IP_RESOLVER     =       'http://icanhazip.com'
PROG_NAME       =       'CloudFlare DDNS Agent'
API_URL         =       'https://www.cloudflare.com/api_json.html'

# Logging config
ddns_log = logging.getLogger('DdnsLog')
ddns_log.setLevel(logging.DEBUG)
handler = logging.handlers.SysLogHandler(address = '/dev/log')
ddns_log.addHandler(handler)

# Desc: Returns WAN IP of the host
def getWanIp():
    ddns_log.debug('Resolving WAN IP...')

    try:
        response = requests.get(IP_RESOLVER)
        if response.status_code <> 200:
            ddns_log.debug('Error obtaining WAN IP - 1.')
            sys.exit(1)
    except:
        ddns_log.debug('Error obtaining WAN IP - 2.')
        sys.exit(1)
    
    wanIp = response.text.strip()
    response.close()

    ddns_log.debug("WAN IP resolved as: %s." % wanIp)
    return wanIp

# Desc: Get all existing records from CloudFlare
def getRecords():
    ddns_log.debug('Obtaining records from CloudFlare API...')

    # Define API payload
    payload = {
        'a'     : 'rec_load_all',
        'tkn'   : API_KEY,
        'email' : EMAIL,
        'z'     : ZONE, 
    }

    # Get all records via API and parse to JSON
    try:
        response = requests.get(API_URL, params=payload)
        if response.status_code <> 200:
            ddns_log.debug('Error obtaining records from CloudFlare API - 1.')
            sys.exit(1)
    except:
        ddns_log.debug('Error obtaining records from CloudFlare API - 2.')
        sys.exit(1)
    
    records = response.json()
    response.close()
    
    ddns_log.debug('obtained records from cloudflare api.')
    return records

# Desc: Get ID of a given record name
def getRecordId(name):
    ddns_log.debug("Obtaining record ID for: %s" % name)

    # For given name return record ID
    for record in records['response']['recs']['objs']:
        if record['display_name'] == name:
            ddns_log.debug("Obtained record ID: %s" % record['rec_id'])
            return record['rec_id']
        
    ddns_log.debug("Could not obtain record ID for: %s" % name)
    sys.exit(1)

# Desc: Update given record with new WAN IP
def updateRecord(name,recordId):
    ddns_log.debug("Updating record '%s' to point at '%s'..." % (name,wanIp))
    
    # Define payload
    payload = {
        'a'            : 'rec_edit',
        'tkn'          : API_KEY,
        'email'        : EMAIL,
        'z'            : ZONE,
        'type'         : 'A',
        'id'           : recordId,
        'name'         : name,
        'content'      : wanIp,
        'ttl'          : 1,
        'service_mode' : 1,
    }
    try:
        # Update the record
        response = requests.get(API_URL, params=payload)
        if response.status_code <> 200:
            ddns_log.debug('Error updating record via CloudFlare API - 1.')
            sys.exit(1)
    except:
        ddns_log.debug('Error updating record via CloudFlare API - 2.')
        sys.exit(1)

    ddns_log.debug('Updated record successfully.')

# Execute script
ddns_log.debug("%s started. Logging to syslog..." % PROG_NAME)
print "%s started. Logging to syslog..." % PROG_NAME

# Get WAN IP and all existing records
records = getRecords()
wanIp   = getWanIp()

# For each name update the record
for name in names:
    recordId = getRecordId(name)
    updateRecord(name,recordId)

ddns_log.debug("%s completed." % PROG_NAME)
print "%s completed." % PROG_NAME

# Exit
sys.exit(0)
