#!/usr/bin/env python

##########################################################################
# Copyright 2017-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
# http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the
# License for the specific language governing permissions and limitations under the License.
##########################################################################
"""Lex Model Building Service helper script

Used to import/export/delete Lex bots and associated resources
(i.e. intents, slot types).

Can be run as a shell script or used as a Lambda Function for CloudFormation
Custom Resources...
"""

import logging
import json
import boto3
import time

lexclient = boto3.client('lex-models')
DEFAULT_LOGGING_LEVEL = logging.INFO
logging.basicConfig(
    format='[%(levelname)s] %(message)s',
    level=DEFAULT_LOGGING_LEVEL
)
logger = logging.getLogger(__name__)
logger.setLevel(DEFAULT_LOGGING_LEVEL)

BOT_DEFINITION_FILENAME = 'lambda/InvoiceBot.zip'
BOT_EXPORT_FILENAME = 'bot-definition-export.json'

def create_bot():
    with open(BOT_DEFINITION_FILENAME, 'rb') as file_data:
        bytes_content = file_data.read()
    response = lexclient.start_import(
        payload=bytes_content,
        resourceType='BOT',
        mergeStrategy='OVERWRITE_LATEST')
    print("Import id is"+response['importId'])
    
    import_status = lexclient.get_import(
        importId=response['importId'])
        
    while import_status['importStatus'] =='IN_PROGRESS':
        import_status = lexclient.get_import(importId=response['importId'])
        print("Bot creation is in progress")
    if import_status['importStatus'] == 'COMPLETE':
        return "SUCCESS"
    else:
        return "FAILURE"
        
def delete_bot(bot_name=None):
    bot_aliases = lexclient.get_bot_aliases(botName=bot_name)['BotAliases']
    for alias in bot_aliases:
        print("Deleting Alias"+alias)
        response = lexclient.delete_bot_alias(name=alias,botName=bot_name)
    time.sleep(5)
    response = lexclient.delete_bot(name=bot_name)
    return "SUCCESS"
    
def handler(event, context):
    """ CloudFormation Custom Resource Lambda Handler
    """
    import cfnresponse

    logger.info('event: {}'.format(cfnresponse.json_dump_format(event)))
    request_type = event.get('RequestType')
    resource_properties = event.get('ResourceProperties')
    bot_name= resource_properties.get('BotName')
    response_status = cfnresponse.SUCCESS
    response = {}
    response_id = event.get('RequestId')
    reason = request_type
    error = ''
    should_delete = resource_properties.get('ShouldDelete', True)


    if (request_type in ['Create', 'Update']):
        try:
            print("here2")
            response['status']=create_bot()
            if response['status'] =="SUCCESS":
                print("Job succeded\n")
                response_status = cfnresponse.SUCCESS
            else: 
                response_status = cfnresponse.FAILED
                print("Job Failed\n")
        except Exception as e:
            error = 'failed to {} bot: {}'.format(request_type, e)
            pass

    if (request_type == 'Delete' and should_delete != 'false'):
        try:
            response['status']=delete_bot(bot_name)
            if response['status'] =="SUCCESS":
                print("Job succeded\n")
                response_status = cfnresponse.SUCCESS
            else: 
                response_status = cfnresponse.FAILED
                print("Delete Failed\n")
        except Exception as e:
            error = 'failed to delete bot: {}'.format(e)
            pass

    if error:
        logger.error(error)
        response_status = cfnresponse.FAILED
        reason = error

    if bool(context):
        cfnresponse.send(
            event,
            context,
            response_status,
            response,
            response_id,
            reason
        )
