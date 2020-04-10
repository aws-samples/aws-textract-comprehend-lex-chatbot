import json
import logging
import boto3

s3client = boto3.client('s3')
s3 = boto3.resource('s3')

comprehend = boto3.client('comprehend')

compindex = dict()
mainindex = dict()


# --------------- Helpers that build all of the responses ----------------------
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

def build_delegate_speechlet_response(endsession):
    """  create a simple json response with card """
    return {
        'directives': [
            {
                'type': 'Dialog.Delegate'
            }
        ],
        'shouldEndSession': endsession
    }

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    # First get the list of entities from Comprehend Detect Entities
    global compindex
    global mainindex
    selected_entities = ""
    session_attributes = {}
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
                selected_entities = selected_entities + "," + x['Type'] + " : " + x['Text']
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
    print('about to return selected entities: ' + selected_entities)
    # Now build the welcome message
    
    card_title = "Welcome"
    speech_output = "Welcome to Meaningful Conversations, here are the list of Entities available, tell me an entity to proceed: " + str(selected_entities)
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, None, should_end_session))



def build_cancel_speechlet():
    card_title = "Cancel Request"
    speech_output = "Alright, canceling our chat. Let me know when you are ready. Goodbye for now"
    should_end_session = True
    return build_speechlet_response(
        card_title, speech_output, None, should_end_session)

def build_help_speechlet():
    card_title = "Help Request"
    speech_output = "Its very simple really. Just tell me an entity for which you need more details on"
    should_end_session = True
    return build_speechlet_response(
        card_title, speech_output, None, should_end_session)

def build_stop_speechlet():
    card_title = "Pour Stop Request"
    speech_output = "Stopping our conversation. Let me know when you are ready. Goodbye for now"
    should_end_session = True
    return build_speechlet_response(
        card_title, speech_output, None, should_end_session)





def get_phrases(intent_request):
    global mainindex
    print("Inside Get Phrases")
    slots = intent_request['intent']['slots']
    entity = slots['entity']['value']
    print("Entity input for get phrases is: " + str(entity))
    session_attributes = {}
    session_attributes['entity'] = entity
    print("Updated Session Attributes are: " + str(session_attributes))
    found = 0
    for i in mainindex:
        if entity.upper() in str(mainindex[i]['entities']).upper():
            phrases = mainindex[i]['phrases']
            found = 1
    if found == 1:
        card_title = "Key Phrases"
        speech_output = "I will narrate the Key Phrases for your entity now. Just say yes, more text, after I finish, to get the full text corpus: " + str(phrases)
        should_end_session = False
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, None, should_end_session))
    else:
        card_title = "Key Phrases Not Found"
        speech_output = "I am sorry, I can't seem to find any Key Phrases for your entity. Please open a new conversation to try again"
        should_end_session = True
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, None, should_end_session))
    


def get_text(intent_request, sessatt):
    global mainindex
    slots = intent_request['intent']['slots']
    textmatch = slots['fulltext']['value']
    if textmatch == "more text":
        for i in mainindex:
            if sessatt['entity'].upper() in str(mainindex[i]['entities']).upper():
                textcorpus = mainindex[i]['file_contents']
        card_title = "Text Corpus"
        speech_output = "Thank you. " + str(textcorpus)
        should_end_session = True
        session_attributes = {}
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, None, should_end_session))     
    else:
        card_title = "Incorrect Selection"
        speech_output = "OK, since you did not ask for more text, I am ending our chat session. Goodbye for now. "
        should_end_session = True
        session_attributes = {}
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, None, should_end_session))   
        
        

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """


    print("intent_request values are as below" + str(intent_request))
    print("session values are: " +str(session))
    

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
    if intent_name == "AMAZON.CancelIntent":
        return build_response({}, build_cancel_speechlet())
    if intent_name == "AMAZON.StopIntent":
        return build_response({}, build_stop_speechlet())
    if intent_name == "AMAZON.HelpIntent":
        return build_response({}, build_help_speechlet())
    if intent_name == "GetKeyPhrases":
        return get_phrases(intent_request)
    if intent_name == "GetFullText":
        return get_text(intent_request, session['attributes'])

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] != "amzn1.ask.skill.93b01f7b-2059-4164-b93f-02b18c6bf7b2"):
         raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])