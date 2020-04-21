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
import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3
import tarfile
import csv
from io import StringIO
from io import BytesIO

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3client = boto3.client('s3')
s3 = boto3.resource('s3')

comprehend = boto3.client('comprehend')

compindex = dict()
mainindex = dict()
# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type':'Close',
            'fulfillmentState':fulfillment_state,
            'message':message
        }
    }
    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None





def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }



""" --- Functions that control the bot's behavior --- """


def get_entities(intent_request):
    global compindex
    global mainindex
    retentity = ""
    selected_entities = ""
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    input_bucket = s3.Bucket('awscodestar-meaningfulconve-infr-outputtextbucket-1efgr6xdzgdur')
    for file in input_bucket.objects.all():
        input_bucket_text_file = s3.Object('awscodestar-meaningfulconve-infr-outputtextbucket-1efgr6xdzgdur', file.key)
        text_file_contents = str(input_bucket_text_file.get()['Body'].read().decode('utf-8'))
        detected_entities = comprehend.detect_entities(
        Text=text_file_contents,
        LanguageCode="en"
        )
        selected_entity_types = ["ORGANIZATION", "OTHER", "TITLE", "LOCATION", "COMMERCIAL_ITEM"]
        for x in detected_entities['Entities']:
            if x['Score'] > 0.9 and x['Type'] in selected_entity_types:
                selected_entities = selected_entities + " " + x['Type'] + ":" + x['Text']
        detected_key_phrases = comprehend.detect_key_phrases(
            Text=text_file_contents,
            LanguageCode="en"
            )
        selected_phrases = str([x['Text'] for x in detected_key_phrases['KeyPhrases']
                            if x['Score'] > 0.9])    
        compindex['file_contents'] = text_file_contents
        compindex['entities'] = selected_entities
        compindex['phrases'] = selected_phrases
        mainindex[file.key] = compindex
        compindex = dict()
    print("Main Index is: " + str(mainindex))
    print('about to return selected entities: ' + str(selected_entities))
    return elicit_slot(
        session_attributes,
        'GetPhrases',
        intent_request['currentIntent']['slots'],
        'entityrequested',
        {
            'contentType': 'PlainText',
            'content': 'Welcome to Meaningful Conversations, here are the list of Entities available, select one to proceed: ' + str(selected_entities)
        }
    )

def get_phrases(intent_request):
    global mainindex
    print("Inside Get Phrases")
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    slots = intent_request['currentIntent']['slots']
    entity = slots['entityrequested']
    print("Entity input for get phrases is: " + str(entity))
    session_attributes['entity'] = entity
    print("Updated Session Attributes are: " + str(session_attributes))
    found = 0
    for i in mainindex:
        if entity.upper() in str(mainindex[i]['entities']).upper():
            phrases = mainindex[i]['phrases']
            found = 1

    if found == 1:
        return elicit_slot(
        session_attributes,
        'GetText',
        intent_request['currentIntent']['slots'],
        'textrequested',
        {
            'contentType': 'PlainText',
            'content': 'Here are some contextual references for your entity. Type more-text to see the full text content: ' + str(phrases)
        }
    )    
    else:
        return elicit_slot(
        session_attributes,
        'GetPhrases',
        intent_request['currentIntent']['slots'],
        'entityrequested',
        {
            'contentType': 'PlainText',
            'content': 'I was unable to find phrases matching your selection. Please try again'
        }
    )    
       
    


def get_text(intent_request):
    global mainindex
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    slots = intent_request['currentIntent']['slots']
    textmatch = slots['textrequested']
    if textmatch == "more-text":
        for i in mainindex:
            if session_attributes['entity'].upper() in str(mainindex[i]['entities']).upper():
                textcorpus = mainindex[i]['file_contents']
        return close(
            session_attributes,
            "Fulfilled",
            {
                'contentType': 'PlainText',
                'content': 'Here is the text corpus for your selection: ' + str(textcorpus)
            }
        )        
                
    else:
        return close(
            session_attributes,
            "Fulfilled",
            {
                'contentType': 'PlainText',
                'content': 'OK, since you did not input the keyword more-text, I am ending our chat session. Goodbye for now'
            }
        )            
    
        




def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    print("Intent Request is: " + str(intent_request))
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'ListEntities':
        return get_entities(intent_request)
    elif intent_name == 'GetPhrases':
        return get_phrases(intent_request)
    elif intent_name == 'GetText':
        return get_text(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
