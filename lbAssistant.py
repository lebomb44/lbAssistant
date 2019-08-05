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
import os
import time
import requests
import threading
import schedule

import w1Temp
import remote

from google.assistant.library.event import EventType

from aiy.assistant import auth_helpers
from aiy.assistant.library import Assistant
from aiy.board import Board, Led
from aiy.voice import tts

system_status = dict() #"Tous les systemes sont operationnels"
notificationIsOn = True

def log(msg):
    """ Print log message with date """
    print(time.strftime('%Y/%m/%d %H:%M:%S: ') + msg)


def httpRequest(url):
    """ Call HTTP request catching all errors """
    try:
        log("URL call: " + url)
        resp = requests.get(url, timeout=0.1)
        if resp.status_code != 200:
            lbSay("La requete a échoué")
        return resp
    except:
        pass


def lbsay(text, volume=60, speed=100, isNotification=False, silent=False):
    """ Text to speech """
    log("I said: " + text)
    if isNotification is True:
        if notificationIsOn is False:
            return
    if silent is False:
        tts.say(text, lang="fr-FR", pitch=100, volume=volume, speed=speed)


def waterMainOn(silent=False):
    lbsay('La pompe est en marche', silent=silent)
    httpRequest("http://192.168.10.4:8444/api/ext/waterMainRelay/set/1")


def waterMainOff(silent=False):
    lbsay('La pompe est arrêtée', silent=silent)
    httpRequest("http://192.168.10.4:8444/api/ext/waterMainRelay/set/0")


def waterGardenOn(silent=False):
    lbsay('La pompe et l\'eau du potager sont en marche', silent=silent)
    httpRequest("http://192.168.10.4:8444/api/ext/waterMainRelay/set/1")
    httpRequest("http://192.168.10.4:8444/api/ext/waterGardenRelay/set/1")


def waterGardenOff(silent=False):
    lbsay('La pompe et l\'eau du potager sont arrêtés', silent=silent)
    httpRequest("http://192.168.10.4:8444/api/ext/waterMainRelay/set/0")
    httpRequest("http://192.168.10.4:8444/api/ext/waterGardenRelay/set/0")


def diningShutterOpen(silent=False):
    lbsay('Ouverture des volets du salon', silent=silent)
    httpRequest("http://192.168.10.4/core/api/jeeApi.php?apikey=nAx7bK300sR01CCq20mXJbsYaYcWc84hfPEY3W1Rnh27BTDb&type=cmd&id=180")


def diningShutterClose(silent=False):
    lbsay('Fermeture des volets du salon', silent=silent)
    httpRequest("http://192.168.10.4/core/api/jeeApi.php?apikey=nAx7bK300sR01CCq20mXJbsYaYcWc84hfPEY3W1Rnh27BTDb&type=cmd&id=181")


def allShutterOpen(silent=False):
    lbsay('Ouverture de tous les volets', silent=silent)
    httpRequest("http://192.168.10.4/core/api/jeeApi.php?apikey=nAx7bK300sR01CCq20mXJbsYaYcWc84hfPEY3W1Rnh27BTDb&type=cmd&id=205")


def allShutterClose(silent=False):
    lbsay('Fermeture de tous les volets', silent=silent)
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
        elif text == 'allume le potager':
            assistant.stop_conversation()
            waterGardenOn()
        elif text == 'arrête le potager':
            assistant.stop_conversation()
            waterGardenOff()
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
            lbsay('La température est de, ' + w1Temp.read_temp() + ' degrés Celsius', speed=80)
        elif text == 'combien fait-il dehors':
            assistant.stop_conversation()
            resp = httpRequest("http://192.168.10.4:8444/api/lbgate/json")
            lbsay('La température extérieure est de, ' + str(resp.json().ext.tempSensors["287979C8070000D1"].val) + ' degrés Celsius', speed=80)
        elif text == 'comment vas-tu':
            assistant.stop_conversation()
            error_found = False
            for key, value in system_status.items():
                if "" != value:
                    error_found = True
                    lbsay(value)
            if error_found is False:
                lbsay('Tous les systèmes sont opérationnels')
        elif text == "redémarre l'assistant":
            assistant.stop_conversation()
            lbsay("Redémarrage de l'assistant en cours", speed=80)
            os.system('sudo reboot')
        elif text == "allume l'alarme":
            assistant.stop_conversation()
            lbsay("Démarrage de l'alarme")
            for i in range(10, 0, -1):
                lbsay(str(i), speed=80)
                time.sleep(1)
            httpRequest("http://192.168.10.4:8444/api/lbgate/alarm/enable")
            lbsay("L'alarme est allumée")
        elif text == "arrête l'alarme":
            assistant.stop_conversation()
            httpRequest("http://192.168.10.4:8444/api/lbgate/alarm/disable")
            lbsay("L'alarme est arrêtée")
        elif text == "mets-nous en sécurité":
            assistant.stop_conversation()
            httpRequest("http://192.168.10.4:8444/api/lbgate/perimeter/enable")
            lbsay("La maison est sécurisée")
        elif text == "allume les notifications":
            assistant.stop_conversation()
            notificationIsOn = True
            lbsay("Les notifications sont en marche")
        elif text == "arrête les notifications":
            assistant.stop_conversation()
            notificationIsOn = False
            lbsay("Les notifications sont arrêtées")
        elif text == "comment sont les notifications":
            assistant.stop_conversation()
            if notificationIsOn is True:
                lbsay("Les notifications sont en marche")
            else:
                lbsay("Les notifications sont arrêtées")
    elif event.type == EventType.ON_END_OF_UTTERANCE:
        led.state = Led.PULSE_QUICK  # Thinking.
    elif (event.type == EventType.ON_CONVERSATION_TURN_FINISHED
          or event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT
          or event.type == EventType.ON_NO_RESPONSE):
        led.state = Led.BEACON_DARK  # Ready.
    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def sayWeather(assistant):
    if notificationIsOn is True:
        log("sayWeather execution")
        assistant.send_text_query('quel sera la meteo')


def sayWorkPath(assistant):
    if notificationIsOn is True:
        log("sayWorkPath execution")
        assistant.send_text_query('combien de temps pour aller chez Airbus rue des cosmonautes')


def checkSystem(assistant):
    log("Checking system")
    system_status["osmc_disk"] = remote.checkdisk("osmc", "'O S M C' racine", "osmc", "/")
    system_status["osmc_hdd"] = remote.checkdisk("osmc", "'O S M C' 'H D D'", "osmc", "/media/HDD", 95)
    system_status["osmc_http"] = remote.checkhttp("https://sno.ddns.net/ping", "'O S M C' ping", "pong")
    system_status["jeedom_disk"] = remote.checkdisk("jeedom", "JIDOM", "jeedom", "/")
    #system_status["camdining_disk"] = remote.checkdisk("camdining", "CAM DINING", "pi", "/")
    #system_status["camentry_disk"] = remote.checkdisk("camentry", "CAM ENTRY", "pi", "/")
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
