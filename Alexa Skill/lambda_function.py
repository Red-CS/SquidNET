# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.

import datetime as dt
import math
import logging
import random
import requests

from ask_sdk_core.utils import is_intent_name, is_request_type

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name, get_slot_value, get_slot
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

from weapon_info import weapon_info_dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def time_remaining():
    cur_hour = int(dt.datetime.utcnow().strftime('%H'))
    cur_minute = int(dt.datetime.utcnow().strftime('%M'))
    
    url = 'https://splatoon2.ink/data/schedules.json'
    response = requests.get(url).json()
    unix_end = response['gachi'][0]['end_time']
    
    end_hour = int(dt.datetime.utcfromtimestamp(unix_end).strftime('%H'))
    end_minute = 60
    
    if end_hour is 0:
        end_hour = 24
    
    if end_hour - cur_hour is 2:
        if end_minute - cur_minute is 0:
            return "1 hour"
        return "1 hour and " + str(end_minute - cur_minute) + " minutes"
    elif end_hour - cur_hour is 1 and end_minute - cur_minute is not 0:
        return str(end_minute - cur_minute) + " minutes"
    else:
        return "- hold on, this data has just changed, please ask me again"
    
def getGeneralInfoIntent(general):
    url = 'https://splatoon2.ink/data/schedules.json'
    response = requests.get(url).json()
    
    current_maps = []
    indicies = ['regular', 'gachi', 'league']
    
    for headers in indicies:
        current_maps.append("{} and {}".format(response[headers][0]['stage_a']['name'], response[headers][0]['stage_b']['name']))
    
    ranked_mode = response['gachi'][0]['rule']['name']
    league_mode = response['league'][0]['rule']['name']
    
    if general is False:
        current_maps[0] += ", which ends in {}".format(time_remaining())
        current_maps[1] = "{} at {}, which ends in {}".format(ranked_mode, current_maps[1], time_remaining())
        current_maps[2] = "{} at {}, which ends in {}".format(league_mode, current_maps[2], time_remaining())
    else:
        current_maps[1] = "{} at {}".format(ranked_mode, current_maps[1])
        current_maps[2] = "{} at {}, all of which ends in {}".format(league_mode, current_maps[2], time_remaining())
    
    return current_maps



def getFutureInfoIntent():
    url = 'https://splatoon2.ink/data/schedules.json'
    response = requests.get(url).json()
    
    future_maps = []
    indicies = ['regular', 'gachi', 'league']
    
    for headers in indicies:
        future_maps.append(response[headers][1]['stage_a']['name'] + " and " + response[headers][1]['stage_b']['name'])
    
    ranked_mode = response['gachi'][1]['rule']['name']
    league_mode = response['league'][1]['rule']['name']

    future_maps[0] += ', which starts in ' + time_remaining()
    future_maps[1] = ranked_mode + " at " + future_maps[1] + ", which starts in " + time_remaining()
    future_maps[2] = league_mode + " at " + future_maps[2] + ", which starts in " + time_remaining()
    
    return future_maps

def getStageAppearance(stage):
    url = 'https://splatoon2.ink/data/schedules.json'
    response = requests.get(url).json() # response is type dict

    stage_appearances = []

    for i in range(1, 12):
        indicies = ['regular', 'gachi', 'league']
        
        for headers in indicies:
            stage_a = response[headers][i]['stage_a']['name']
            stage_b = response[headers][i]['stage_b']['name']
            mode = response[headers][i]['rule']['name'] # "Turf War" for Turf War, Battle Mode (RM, TC, SZ, CB) for Ranked and League
            if stage_a == stage or stage_b == stage:
                line = ' in ' + getStageAppearanceTime(response[headers][i]['start_time']) + ' for ' + getOuterMode(headers)
                if headers != 'regular':
                    line += ' with ' + mode
                stage_appearances.append(line)
                break # There is no need to search the rest of that hourly rotation
    return stage_appearances    # previously stage_appearances, changed to 'stage' to test spoken value

def getStageAppearanceTime(unix_time):
    current_unix = int(time.time())
    difference = unix_time - current_unix
    minutes = math.floor(difference/60)
    hours = 0
    while minutes >= 60:
        minutes = minutes - 60
        hours = hours + 1
    
    # Grammar protocols
    if hours == 0:
        if minutes == 1:
            return str(minutes) + ' minute'                                                     # "in 1 minute"
        return str(minutes) + ' minutes'    # can't have space after to work with Turf War      # "in x minutes"
    elif hours == 1:         
        if minutes == 0:                                                                        
            return str(hours) + ' hour'                                                          # "in 1 hour"
    elif minutes == 1:
        return str(hours) + ' hour and ' + str(minutes) + ' minute'                          # "in 1 hour and x minutes"
    return str(hours) + ' hours and ' + str(minutes) + ' minutes'                                # "in x hours and x minutes"

def getOuterMode(header): # helper method for getStageAppearanceTime()
    if header == 'gachi':
        return 'Ranked Battle'
    elif header == 'regular':
        return 'Turf War'
    return 'League Battle'


def getWeaponInfoIntent(weapon_called):

    weapon = weapon_called
    sub = "Error."
    special = "Error." 
    
    # weapon_info_dict cut from here

    for inner_type in weapon_info_dict['subs']:
        for actual_weapon in weapon_info_dict['subs'][inner_type]:
            if actual_weapon.lower() == weapon.lower():
                sub = inner_type
                break
            
    for inner_type in weapon_info_dict['specials']:
        for actual_weapon in weapon_info_dict['specials'][inner_type]:
            if actual_weapon.lower() == weapon.lower():
                special = inner_type
                weapon = actual_weapon # reformats in Upper Case
                break
            
                
    return "The " + weapon + " has " + sub + " and " + special


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to SquidNET! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GeneralInfoIntentHandler(AbstractRequestHandler):
    """Handler for GeneralInfoIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GeneralInfoIntent")(handler_input)
    def handle(self, handler_input):
        current_maps = getGeneralInfoIntent(general=True)
        speak_output = "The current stages are:"
        speak_output += " for Turf War, " + current_maps[0] + ","
        speak_output += " for Ranked Battles, " + current_maps[1] + ","
        speak_output += " and for League Battles, " + current_maps[2] + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class TurfWarIntentHandler(AbstractRequestHandler):
    """Handler for TurfWarIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TurfWarIntent")(handler_input)
    def handle(self, handler_input):
        current_maps = getGeneralInfoIntent(general=False)
        speak_output = "The current Turf War stages are " + current_maps[0] + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class RankedBattleIntentHandler(AbstractRequestHandler):
    """Handler for RankedBattleIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("RankedBattleIntent")(handler_input)
    def handle(self, handler_input):
        current_maps = getGeneralInfoIntent(general=False)
        speak_output = "The current Ranked Battle rotation is " + current_maps[1] + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class LeagueBattleIntentHandler(AbstractRequestHandler):
    """Handler for LeagueBattleIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("LeagueBattleIntent")(handler_input)
    def handle(self, handler_input):
        current_maps = getGeneralInfoIntent(general=False)
        speak_output = "The current League Battle rotation is " + current_maps[2] + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FutureTWIntentHandler(AbstractRequestHandler):
    """Handler for FutureTWIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("FutureTWIntent")(handler_input)
    def handle(self, handler_input):
        future_maps = getFutureInfoIntent()
        speak_output = "The next Turf War maps are " + future_maps[0] + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FutureRBIntentHandler(AbstractRequestHandler):
    """Handler for FutureRBIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("FutureRBIntent")(handler_input)
    def handle(self, handler_input):
        future_maps = getFutureInfoIntent()
        speak_output = "The next Ranked Battle rotation is " + future_maps[1] + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FutureLBIntentHandler(AbstractRequestHandler):
    """Handler for FutureLBIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("FutureLBIntent")(handler_input)
    def handle(self, handler_input):
        future_maps = getFutureInfoIntent()
        speak_output = "The next League Battle rotation is " + future_maps[2] + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class BasicWeaponInfoIntentHandler(AbstractRequestHandler):
    """Handler for BasicWeaponInfoIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("BasicWeaponInfoIntent")(handler_input)
    def handle(self, handler_input):
        val = get_slot_value(handler_input, "weapon")
        weapon = str(val)
        slot_dict = get_slot(handler_input, 'weapon').to_dict() # change happened here ==================================================
        weapon_name = slot_dict['resolutions']['resolutions_per_authority'][0]['values'][0]['value']['name']
        speak_output = getWeaponInfoIntent(weapon_name) #previously 'weapon'
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class NextStageIntentHandler(AbstractRequestHandler):
    """Handler for NextStageIntent"""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("NextStageIntent")(handler_input)
    def handle(self, handler_input):
        val = get_slot_value(handler_input, "stage")
        stage = str(val)
        slot_dict = get_slot(handler_input, 'stage').to_dict()
        stage_name = slot_dict['resolutions']['resolutions_per_authority'][0]['values'][0]['value']['name']
        
        stages = getStageAppearance(stage_name)
        
        if len(stages) == 0:
            speak_output = stage_name + ' will not be available in the next 24 hours. Please check back later.'
        else: 
            speak_output = 'You can play ' + stage_name + ' next '
            if len(stages) == 1:
                speak_output += stages[0] + '.'
                # possibly troublesome, replace with return?
            else:
                for i in range(len(stages)):
                    if i == len(stages) - 1:    # if we are on the last stage of the list
                        speak_output += ' and ' + stages[i] + '.'
                    else:
                        speak_output += stages[i] + ', '
                
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        response_hello = ["Hello!", "Booyah!", "What's kraken?!", "Hi!"]
        speak_output = random.choice(response_hello)

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can ask me about the current and inkoming map rotations, salmon run schedules, weapon stats, and gear and brand descriptions."
        speak_output += " Additionally, if you are having any problems, please contact the creator of this Alexa skill, Red Williams, at red.devcs@gmail.com."
        speak_output += " Alternatively, you can report an issue in the GitHub repository which can be found at this URL: \"https://github.com/Red-CS\""

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        response_goodbye = ["Signing off.", "Ending session.", "Splat 'em up!", "Goodbye."]
        speak_output = "Thank you for using Squid Service. " + random.choice(response_goodbye)

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())

sb.add_request_handler(BasicWeaponInfoIntentHandler())
sb.add_request_handler(GeneralInfoIntentHandler())
sb.add_request_handler(TurfWarIntentHandler())
sb.add_request_handler(RankedBattleIntentHandler())
sb.add_request_handler(LeagueBattleIntentHandler())
sb.add_request_handler(FutureTWIntentHandler())
sb.add_request_handler(FutureRBIntentHandler())
sb.add_request_handler(FutureLBIntentHandler())
sb.add_request_handler(NextStageIntentHandler())
sb.add_request_handler(HelloWorldIntentHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()