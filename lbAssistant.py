#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import platform
import subprocess
import sys
import time
import requests
import threading
import schedule
import time

import w1Temp
import remote

from google.assistant.library.event import EventType

from aiy.assistant import auth_helpers
from aiy.assistant.library import Assistant
from aiy.board import Board, Led
from aiy.voice import tts

system_status = dict() #"Tous les systemes sont operationnels"


def log(msg):
    print(time.strftime('%Y/%m/%d %H:%M:%S: ') + msg)


def httpRequest(url):
    try:
        log("URL call: " + url)
        requests.get(url, timeout=0.1)
    except:
        pass


def lbsay(text, volume=20, speed=100):
    log("I said: " + text)
    tts.say(text, lang="fr-FR", pitch=100, volume=volume, speed=speed)


def waterMainOn():
    lbsay('La pompe est en marche')
    httpRequest("http://192.168.10.4:8444/api/ext/waterMainRelay/set/1")


def waterMainOff():
    lbsay('La pompe est arrêtée')
    httpRequest("http://192.168.10.4:8444/api/ext/waterMainRelay/set/0")


def diningShutterOpen():
    lbsay('Ouverture des volets du salon')
    httpRequest("http://192.168.10.4/core/api/jeeApi.php?apikey=nAx7bK300sR01CCq20mXJbsYaYcWc84hfPEY3W1Rnh27BTDb&type=cmd&id=180")


def diningShutterClose():
    lbsay('Fermeture des volets du salon')
    httpRequest("http://192.168.10.4/core/api/jeeApi.php?apikey=nAx7bK300sR01CCq20mXJbsYaYcWc84hfPEY3W1Rnh27BTDb&type=cmd&id=181")


def allShutterOpen():
    lbsay('Ouverture de tous les volets')
    httpRequest("http://192.168.10.4/core/api/jeeApi.php?apikey=nAx7bK300sR01CCq20mXJbsYaYcWc84hfPEY3W1Rnh27BTDb&type=cmd&id=205")


def allShutterClose():
    lbsay('Fermeture de tous les volets')
    httpRequest("http://192.168.10.4/core/api/jeeApi.php?apikey=nAx7bK300sR01CCq20mXJbsYaYcWc84hfPEY3W1Rnh27BTDb&type=cmd&id=206")


def process_event(assistant, led, event):
    logging.info(event)
    if event.type == EventType.ON_START_FINISHED:
        led.state = Led.BEACON_DARK  # Ready.
        log('Say "OK, Google" then speak, or press Ctrl+C to quit...')
    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        led.state = Led.ON  # Listening.
    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
        log('You said: ' + event.args['text'])
        text = event.args['text'].lower()
        if text == 'allume la pompe':
            assistant.stop_conversation()
            waterMainOn()
        elif text == 'arrête la pompe':
            assistant.stop_conversation()
            waterMainOff()
        elif text == 'ouvre les volets du salon':
            assistant.stop_conversation()
            diningShutterOpen()
        elif text == 'ferme les volets du salon':
            assistant.stop_conversation()
            diningShutterClose()
        elif text == 'ouvre tous les volets':
            assistant.stop_conversation()
            allShutterOpen()
        elif text == 'ferme tous les volets':
            assistant.stop_conversation()
            allShutterClose()
        elif text == 'combien fait-il':
            assistant.stop_conversation()
            lbsay('La température est de, ' + w1Temp.read_temp() + " degrés Celsius", speed=80)
        elif text == 'comment vas-tu':
            assistant.stop_conversation()
            error_found = False
            for key, value in system_status.items():
                if "" != value:
                    error_found = True
                    lbsay(value)
            if error_found is False:
                lbsay("Tous les systèmes sont opérationnels")
    elif event.type == EventType.ON_END_OF_UTTERANCE:
        led.state = Led.PULSE_QUICK  # Thinking.
    elif (event.type == EventType.ON_CONVERSATION_TURN_FINISHED
          or event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT
          or event.type == EventType.ON_NO_RESPONSE):
        led.state = Led.BEACON_DARK  # Ready.
    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def sayWeather(assistant):
    log("sayWeather execution")
    assistant.send_text_query('quel sera la meteo')


def sayWorkPath(assistant):
    log("sayWorkPath execution")
    assist738ant.send_text_query('combien de temps pour aller chez Airbus rue des cosmonautes')


def checkSystem(assistant):
    log("Checking system")
    system_status["osmc_disk"] = remote.checkdisk("osmc", "osmc", "/")
    system_status["osmc_hdd"] = remote.checkdisk("osmc", "osmc", "/media/HDD", 95)
    system_status["osmc_http"] = remote.checkhttp("sno.ddns.net/ping", "OSMC", "pong")
    system_status["jeedom_disk"] = remote.checkdisk("jeedom", "jeedom", "/")
    #system_status["camdining_disk"] = remote.checkdisk("camdining", "pi", "/")
    #system_status["camentry_disk"] = remote.checkdisk("camentry", "pi", "/")
    #log(str(system_status))


def schedule_thread(schedule):
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    logging.basicConfig(level=logging.INFO)
    credentials = auth_helpers.get_assistant_credentials()
    with Board() as board, Assistant(credentials) as assistant:
        schedule.every().day.at("07:30").do(sayWeather, assistant)
        schedule.every().day.at("07:45").do(sayWorkPath, assistant)
        schedule.every(15).minutes.do(checkSystem, assistant)
        worker_thread = threading.Thread(target=schedule_thread, args=(schedule,))
        worker_thread.start()
        checkSystem(assistant)
        for event in assistant.start():
            process_event(assistant, board.led, event)


if __name__ == '__main__':
    main()
