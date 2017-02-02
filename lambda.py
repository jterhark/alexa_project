from __future__ import print_function
from urllib2 import urlopen
from urllib import urlencode
import json


class API(object):
    key = ""
    host = ""

    def __init__(self, host, key):
        self.key = key
        self.host = host

    def query(self, params):
        params.update({'key': self.key, 'format': 'json'})
        url = self.host + "?" + urlencode(params)
        response = urlopen(url)
        return json.load(response)


# -- Speech Builder -- #
def build_response(output, terminate=True):
    return {
        'version': '1.0',
        'sessionAttributes': {},
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'card': {
                'type': 'Simple',
                'title': 'Test Card',
                'content': output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': 'An error has occurred'
                }
            },
            'shouldEndSession': terminate
        }
    }


def get_transit_times(intent):
    if 'StopID' in intent['slots']:
        stop_id = intent['slots']['StopID']['value']
        api = API('http://ctabustracker.com/bustime/api/v2/getpredictions', 'API_KEY_HERE')
        response = api.query({'stpid': stop_id})

        if 'error' not in response['bustime-response']:

            stop_name = response['bustime-response']['prd'][0]['stpnm']\
                .replace('/', ' and ')\
                .replace('&', 'and')
            speech = "The current travel times at " + stop_name + " are. "

            for prediction in response['bustime-response']['prd']:
                time = prediction['prdtm'][9:]
                route = prediction['rt']
                direction = prediction['rtdir']
                min_remaining = prediction['prdctdn']
                destination = prediction['des'].replace('/', ' and ')

                if int(time[:2]) > 12:
                    time = str(int(time[:2])-12) + time[2:]

                speech += "Route " + route + ", heading " + direction + " toward " + destination +\
                    ", arriving in " + min_remaining + " minutes at " + time + ". "

            return build_response(speech)
        elif response['bustime-response']['error'][0]['msg'] == 'No arrival times':
            return build_response("No arrival times listed for this stop.")
        else:
            return build_response(str(stop_id) + "is not a valid stop ID!")


# --Intent Handler-- #
def intent_router(request, session):
    intent = request['intent']
    intent_name = intent['name']

    if intent_name == 'TransitIntent':
        return get_transit_times(intent)
    else:
        raise ValueError('Invalid Intent!')


# --Main Handler-- #
def lambda_handler(event, context):
    if event['request']['type'] == 'IntentRequest':
        return intent_router(event['request'], event['session'])
    else:
        return build_response("I don't know what you mean!")
