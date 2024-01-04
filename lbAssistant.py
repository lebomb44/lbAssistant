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
import signal
import sys
import os
import time
import requests
import threading
import schedule
import traceback
import http.server
import json

import remote
import lbserial

from google.assistant.library.event import EventType

from aiy.assistant import auth_helpers
from aiy.assistant.library import Assistant
from aiy.board import Board, Led
from aiy.voice import tts

system_status = dict() #"Tous les systemes sont operationnels"
notification_is_on = True
schedule_watering = False
wifi_is_on = False

nombres = dict({'zero': 0, 'un': 1, 'deux': 2, 'trois': 3, 'quatre': 4, 'cinq': 5, 'six': 6, 'sept': 7, 'huit': 8, 'neuf': 9})
radio_id_list = dict({'france info': 4232, 'rire et chansons': 5558})
acq = dict({
    'beetleTemp': {
        'tempSensors': {'424545544C455445': {'val': 20.0, 'name': "phone", 'type': ["temp"]}, 'fct_after_set': "timeout_reset"}
    }
})
node_list = dict(
    beetleTemp=lbserial.Serial('beetleTemp', acq))


HTTPD_PORT = 8444

def log(msg):
    """ Print message with time header """
    try:
        print(time.strftime('%Y/%m/%d %H:%M:%S: ') + str(msg))
    except Exception as ex:
        log_exception(ex)


def log_exception(ex, msg="ERROR Exception"):
    """ Print exception with a time header """
    log(msg + ": " + str(ex))
    log(traceback.format_exc())


def httpRequest(url, timeout=0.1):
    """ Call HTTP request catching all errors """
    try:
        log("URL Get: " + url)
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            lbsay("La requete a échoué")
        return resp
    except Exception as ex:
        log_exception(ex)
        return None


def httpPostRequest(url, json_data, timeout=1.0):
    """ Call HTTP request catching all errors """
    try:
        log("URL Post: " + url)
        resp = requests.post(url, json=json_data, timeout=timeout)
        if resp.status_code != 200:
            lbsay("La requete a échoué")
        return resp
    except Exception as ex:
        log_exception(ex)
        return None


def lbsay(text, volume=50, speed=100, isNotification=False, silent=False):
    """ Text to speech """
    global notification_is_on
    log("I said: " + text)
    if isNotification is True:
        if notification_is_on is False:
            return
    if silent is False:
        #subprocess.check_call('aplay -q -D default "/home/pi/lbAssistant/voices/' + text + '.wav' + '"', shell=True)
        tts.say(text, lang="fr-FR", pitch=100, volume=volume, speed=speed)


def waterMainOn(silent=False):
    lbsay('La pompe est en marche', silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterMainRelay/set/1")


def schedule_waterMainOn():
    global schedule_watering
    if schedule_watering is True:
        waterMainOn(silent=True)


def waterMainOff(silent=False):
    lbsay('La pompe est arrêtée', silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterMainRelay/set/0")


def schedule_waterMainOff():
    waterMainOff(silent=True)


def waterSideOn(silent=False):
    lbsay("L'arrosage sur le coté est en marche", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterSideRelay/set/1")


def schedule_waterSideOn():
    global schedule_watering
    if schedule_watering is True:
        waterSideOn(silent=True)


def waterSideOff(silent=False):
    lbsay("L'arrosage sur le coté est arrêtée", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterSideRelay/set/0")


def schedule_waterSideOff():
    waterSideOff(silent=True)


def waterEastOn(silent=False):
    lbsay("L'arrosage est est en marche", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterEastRelay/set/1")


def schedule_waterEastOn():
    global schedule_watering
    if schedule_watering is True:
        waterEastOn(silent=True)


def waterEastOff(silent=False):
    lbsay("L'arrosage est est arrêtée", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterEastRelay/set/0")


def schedule_waterEastOff():
    waterEastOff(silent=True)


def waterWestOn(silent=False):
    lbsay("L'arrosage ouest est en marche", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterWestRelay/set/1")


def schedule_waterWestOn():
    global schedule_watering
    if schedule_watering is True:
        waterWestOn(silent=True)


def waterWestOff(silent=False):
    lbsay("L'arrosage ouest est arrêtée", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterWestRelay/set/0")


def schedule_waterWestOff():
    waterWestOff(silent=True)


def waterSouthOn(silent=False):
    lbsay("L'arrosage sud est en marche", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterSouthRelay/set/1")


def schedule_waterSouthOn():
    global schedule_watering
    if schedule_watering is True:
        waterSouthOn(silent=True)


def waterSouthOff(silent=False):
    lbsay("L'arrosage sud est arrêtée", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterSouthRelay/set/0")


def schedule_waterSouthOff():
    waterSouthOff(silent=True)


def waterGardenOn(silent=False):
    lbsay('La pompe et l\'eau du potager sont en marche', silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterMainRelay/set/1")
    httpRequest("http://jeedom:8444/api/ext/waterGardenRelay/set/1")


def schedule_waterGardenOn():
    global schedule_watering
    if schedule_watering is True:
        waterGardenOn(silent=True)


def waterGardenOff(silent=False):
    lbsay("La pompe et l'eau du potager sont arrêtés", silent=silent)
    httpRequest("http://jeedom:8444/api/ext/waterMainRelay/set/0")
    httpRequest("http://jeedom:8444/api/ext/waterGardenRelay/set/0")


def schedule_waterGardenOff():
    waterGardenOff(silent=True)


def diningShutterOpen(silent=False):
    lbsay('Ouverture des volets du salon', silent=silent)
    httpRequest("http://jeedom:8444/api/rts/ON/ID/12/RTS")


def diningShutterClose(silent=False):
    lbsay('Fermeture des volets du salon', silent=silent)
    httpRequest("http://jeedom:8444/api/rts/OFF/ID/12/RTS")


def nightShutterOpen(silent=False):
    lbsay('Ouverture des volets des chambres', silent=silent)
    httpRequest("http://jeedom:8444/api/rts/ON/ID/2/RTS")


def nightShutterClose(silent=False):
    lbsay('Fermeture des volets des chambres', silent=silent)
    httpRequest("http://jeedom:8444/api/rts/OFF/ID/2/RTS")


def allShutterOpen(silent=False):
    lbsay('Ouverture de tous les volets', silent=silent)
    httpRequest("http://jeedom:8444/api/rts/ON/ID/22/RTS")


def allShutterClose(silent=False):
    lbsay('Fermeture de tous les volets', silent=silent)
    httpRequest("http://jeedom:8444/api/rts/OFF/ID/22/RTS")


def wifiOff(silent=False):
    global wifi_is_on
    lbsay("Ok", silent=silent)
    #subprocess.check_call('/usr/bin/sudo /usr/sbin/service hostapd stop', shell=True)
    httpRequest("http://jeedom/core/api/jeeApi.php?apikey=FddiT3sOcnrs5FcPh35kyTJLhQRdnFra&type=cmd&id=414", timeout=3.0)
    wifi_is_on = False


def schedule_wifiOff():
    wifiOff(silent=True)


def wifiOn(silent=False):
    global wifi_is_on
    lbsay("Ok", silent=silent)
    #subprocess.check_call('/usr/bin/sudo /usr/sbin/service hostapd start', shell=True)
    httpRequest("http://jeedom/core/api/jeeApi.php?apikey=FddiT3sOcnrs5FcPh35kyTJLhQRdnFra&type=cmd&id=412", timeout=3.0)
    wifi_is_on = True


def process_event(assistant, led, event):
    global system_status
    global notification_is_on
    global schedule_watering
    global acq
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
        elif (text == 'ouvre le salon') or (text == 'ouvre les volets du salon') or (text == 'ouvre tous les volets du salon'):
            assistant.stop_conversation()
            diningShutterOpen()
        elif (text == 'ferme le salon') or (text == 'ferme les volets du salon') or (text == 'ferme tous les volets du salon'):
            assistant.stop_conversation()
            diningShutterClose()
        elif (text == 'ouvre les chambres') or (text == 'ouvre les volets des chambres') or (text == 'ouvre tous les volets des chambres'):
            assistant.stop_conversation()
            nightShutterOpen()
        elif (text == 'ferme les chambres') or (text == 'ferme les volets des chambres') or (text == 'ferme tous les volets des chambres'):
            assistant.stop_conversation()
            nightShutterClose()
        elif text == 'ouvre tous les volets':
            assistant.stop_conversation()
            allShutterOpen()
        elif text == 'ferme tous les volets':
            assistant.stop_conversation()
            allShutterClose()
        elif text == 'combien fait-il':
            assistant.stop_conversation()
            temp = "inconnue"
            try:
                resp = httpRequest("http://jeedom:8444/api/lbgate/json")
                temp = str(round(int(resp.json()['ext']['tempSensors']['287979C8070000D1']['val']), 1))
            except:
                pass
            lbsay('Il fait, ' + str(round(acq["beetleTemp"]["tempSensors"]["424545544C455445"]["val"], 1)) + ' dedans et, ' + temp + ' dehors', speed=90)
        elif text == "combien fait-il à l'intérieur":
            assistant.stop_conversation()
            lbsay('La température est de, ' + str(round(acq["beetleTemp"]["tempSensors"]["424545544C455445"]["val"], 1)) + ' degrés Celsius', speed=80)
        elif text == 'combien fait-il dehors':
            assistant.stop_conversation()
            temp = "inconnue"
            try:
                resp = httpRequest("http://jeedom:8444/api/lbgate/json")
                temp = str(round(int(resp.json()['ext']['tempSensors']['287979C8070000D1']['val']), 1))
            except:
                pass
            lbsay('La température extérieure est de, ' + temp + ' degrés Celsius', speed=80)
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
            httpRequest("http://jeedom:8444/api/lbgate/alarm/enable")
            lbsay("L'alarme est allumée")
        elif text == "arrête l'alarme":
            assistant.stop_conversation()
            httpRequest("http://jeedom:8444/api/lbgate/alarm/disable")
            lbsay("L'alarme est arrêtée")
        elif text == "configure l'alarme avec mouvement":
            assistant.stop_conversation()
            httpRequest("http://jeedom:8444/api/lbgate/alarm/use_move")
            lbsay("L'alarme est configurée avec mouvements")
        elif text == "configure l'alarme sans mouvement":
            assistant.stop_conversation()
            httpRequest("http://jeedom:8444/api/lbgate/alarm/nouse_move")
            lbsay("L'alarme est configurée sans mouvements")
        elif text == "mets-nous en sécurité":
            assistant.stop_conversation()
            httpRequest("http://jeedom:8444/api/lbgate/perimeter/enable")
            lbsay("La maison est sécurisée")
        elif text == "allume les notifications":
            assistant.stop_conversation()
            notification_is_on = True
            lbsay("Les notifications sont en marche")
        elif text == "arrête les notifications":
            assistant.stop_conversation()
            notification_is_on = False
            lbsay("Les notifications sont arrêtées")
        elif text == "comment sont les notifications":
            assistant.stop_conversation()
            if notification_is_on is True:
                lbsay("Les notifications sont en marche")
            else:
                lbsay("Les notifications sont arrêtées")
        elif text == "active l'arrosage automatique":
            assistant.stop_conversation()
            schedule_watering = True
            lbsay("L'arrosage automatique est activé. Démarrage cette nuit à une heure")
        elif text == "désactive l'arrosage automatique":
            assistant.stop_conversation()
            schedule_watering = False
            lbsay("L'arrosage automatique est désactivé")
        elif (text == "coupe le son de jarvis") or (text == "coupe le son de jardy"):
            assistant.stop_conversation()
            #httpRequest("http://osmc:8444/api/volcontrol/volmute/set")
            httpPostRequest("http://osmc:8080/jsonrpc?Application.SetMute", {"jsonrpc":"2.0","method":"Application.SetMute","params":[True],"id":1})
            lbsay("Ok")
        elif (text == "mets le son de jarvis à fond") or (text == "mets le son de jardy à fond"):
            assistant.stop_conversation()
            httpRequest("http://osmc:8444/api/volcontrol/volmax/set/")
            lbsay("Ok")
        elif ("mets le son de jarvis à" in text) or ("mets le son de jardy à" in text):
            assistant.stop_conversation()
            volPer = text.split(" ")[6]
            if volPer in nombres:
                volPer = nombres[volPer]
            httpRequest("http://osmc:8444/api/volcontrol/vol/set/" + str(volPer))
            lbsay("Ok")
        elif ("mets le son de jarvis" in text) or ("mets le son de jardy" in text):
            assistant.stop_conversation()
            httpPostRequest("http://osmc:8080/jsonrpc?Application.SetMute", {"jsonrpc":"2.0","method":"Application.SetMute","params":[False],"id":1})
            lbsay("Ok")
        elif (text == "baisse le son de jarvis") or (text == "baisse le son de jardy"):
            assistant.stop_conversation()
            httpRequest("http://osmc:8444/api/volcontrol/voldown/set")
            lbsay("Ok")
        elif (text == "monte le son de jarvis") or (text == "monte le son de jardy"):
            assistant.stop_conversation()
            httpRequest("http://osmc:8444/api/volcontrol/volup/set")
            lbsay("Ok")
        elif text == "arrête l'ampli":
            assistant.stop_conversation()
            httpRequest("http://osmc:8444/api/volcontrol/off/set")
            lbsay("Ok")
        elif text == "allume l'ampli":
            assistant.stop_conversation()
            httpRequest("http://osmc:8444/api/volcontrol/on/set")
            lbsay("Ok")
        elif "mets du classique" in text:
            try:
                assistant.stop_conversation()
                httpPostRequest("http://osmc:8080/jsonrpc?Playlist.Clear", {"jsonrpc":"2.0","method":"Playlist.Clear","params":[0],"id":1}, timeout=5.0)
                httpPostRequest("http://osmc:8080/jsonrpc?Playlist.Insert", {"jsonrpc":"2.0","method":"Playlist.Insert","params":[0,0,{"file":"plugin://plugin.audio.radio_de/station/5039"}],"id":2}, timeout=5.0)
                httpPostRequest("http://osmc:8080/jsonrpc?Playlist.open", {"jsonrpc":"2.0","method":"Player.Open","params":{"item":{"position":0,"playlistid":0},"options":{}},"id":3}, timeout=5.0)
                httpRequest("http://osmc:8444/api/volcontrol/on/set")
                httpRequest("http://osmc:8444/api/volcontrol/vol/set/10")
                lbsay("Ok")
            except Exception as ex:
                log_exception(ex)
                lbsay("Impossible de mettre du classique")
        elif "mets la radio" in text:
            try:
                assistant.stop_conversation()
                radio_name = text.split("mets la radio", 1)[1].strip()
                radio_url = ""
                if radio_name in radio_id_list:
                    radio_url = "plugin://plugin.audio.radio_de/station/"+str(radio_id_list[radio_name])
                else:
                    resp_radio = httpPostRequest("http://osmc:8080/jsonrpc?FileCollection", {"jsonrpc":"2.0","method":"Files.GetDirectory","id":"1","params":{"directory":"plugin://plugin.audio.radio_de/stations/top/1","media":"music","properties":["title","file","mimetype","thumbnail","dateadded"],"sort":{"method":"none","order":"descending"}}}, timeout=10.0)
                    radio_json = resp_radio.json()['result']['files']
                    for radio_desc in radio_json:
                        if radio_name == radio_desc['label'].lower():
                            radio_url = radio_desc['file']
                            break
                httpPostRequest("http://osmc:8080/jsonrpc?Playlist.Clear", {"jsonrpc":"2.0","method":"Playlist.Clear","params":[0],"id":1})
                httpPostRequest("http://osmc:8080/jsonrpc?Playlist.Insert", {"jsonrpc":"2.0","method":"Playlist.Insert","params":[0,0,{"file":radio_url}],"id":2})
                httpPostRequest("http://osmc:8080/jsonrpc?Playlist.open", {"jsonrpc":"2.0","method":"Player.Open","params":{"item":{"position":0,"playlistid":0},"options":{}},"id":3})
                lbsay("Ok")
            except Exception as ex:
                log_exception(ex)
                lbsay("Impossible de mettre la radio")
        elif ("stoppe jarvis" in text) or ("arrête jarvis" in text) or ("arrête la musique" in text):
            assistant.stop_conversation()
            httpPostRequest("http://osmc:8080/jsonrpc?Player.Stop", {"jsonrpc":"2.0","method":"Player.Stop","params":[0],"id":1})
            lbsay("Ok")
        elif "allume le wifi" in text:
            assistant.stop_conversation()
            wifiOn()
        elif "arrête le wifi" in text:
            assistant.stop_conversation()
            wifiOff()
        elif "mets le chauffage en confort" in text:
            assistant.stop_conversation()
            httpRequest("http://jeedom:8444/api/heatpump/power/set/ON", timeout=2.0)
            httpRequest("http://jeedom:8444/api/heatpump/mode/set/HEAT", timeout=2.0)
            httpRequest("http://jeedom:8444/api/heatpump/temp/set/19.0", timeout=2.0)
            httpRequest("http://jeedom:8444/api/heatpump/fanspeed/set/AUTO", timeout=2.0)
            lbsay("Mode confort activé")
        elif ("mets le chauffage en éco" in text) or ("mets le chauffage en echo" in text):
            assistant.stop_conversation()
            httpRequest("http://jeedom:8444/api/heatpump/power/set/ON", timeout=2.0)
            httpRequest("http://jeedom:8444/api/heatpump/mode/set/HEAT", timeout=2.0)
            httpRequest("http://jeedom:8444/api/heatpump/temp/set/17.0", timeout=2.0)
            httpRequest("http://jeedom:8444/api/heatpump/fanspeed/set/AUTO", timeout=2.0)
            lbsay("Mode éco activé")
    elif event.type == EventType.ON_END_OF_UTTERANCE:
        led.state = Led.PULSE_QUICK  # Thinking.
    elif (event.type == EventType.ON_CONVERSATION_TURN_FINISHED
          or event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT
          or event.type == EventType.ON_NO_RESPONSE):
        led.state = Led.BEACON_DARK  # Ready.
    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def sayWeather(assistant):
    global notification_is_on
    if notification_is_on is True:
        log("sayWeather execution")
        assistant.send_text_query('quel sera la meteo')


def sayWorkPath(assistant):
    global notification_is_on
    if notification_is_on is True:
        log("sayWorkPath execution")
        assistant.send_text_query('combien de temps pour aller chez Airbus rue des cosmonautes')


def checkSystem(assistant):
    global system_status
    log("Checking system")
    system_status["osmc_disk"] = remote.checkdisk("osmc", "'O S M C' racine", "osmc", "/")
    system_status["osmc_hdd"] = remote.checkdisk("osmc", "'O S M C' 'H D D'", "osmc", "/media/HDD", 95)
    system_status["osmc_http"] = remote.checkhttp("https://snosno.freeboxos.fr/ping", "'O S M C' ping", "pong")
    system_status["jeedom_disk"] = remote.checkdisk("jeedom", "JIDOM", "pi", "/")
    #system_status["camdining_disk"] = remote.checkdisk("camdining", "CAM DINING", "pi", "/")
    #system_status["camentry_disk"] = remote.checkdisk("camentry", "CAM ENTRY", "pi", "/")
    #log(str(system_status))


def schedule_thread(schedule):
    while True:
        schedule.run_pending()
        time.sleep(1)


class CustomHandler(http.server.BaseHTTPRequestHandler):
    """ Custom HTTP handler """
    def ok200(self, resp, content_type='text/plain'):
        """ Return OK page """
        try:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            if content_type == 'text/plain':
                self.wfile.write((time.strftime('%Y/%m/%d %H:%M:%S: ') + resp).encode())
            else:
                self.wfile.write((resp).encode())
        except Exception as ex:
            log_exception(ex)

    def error404(self, resp):
        """ Return page not found """
        try:
            self.send_response(404)
            self.end_headers()
            self.wfile.write((time.strftime('%Y/%m/%d %H:%M:%S: ') + resp).encode())
        except Exception as ex:
            log_exception(ex)

    def log_message(self, format, *args):
        """ Overwrite default log function """
        return

    def do_GET(self):
        """ Callback on HTTP GET request """
        global acq
        url_tokens = self.path.split('/')
        url_tokens_len = len(url_tokens)
        log(str(url_tokens))
        if url_tokens_len > 1:
            api = url_tokens[1]
            if api == "api":
                if url_tokens_len > 2:
                    node = url_tokens[2]
                    if node in node_list:
                        if url_tokens_len > 3:
                            cmd = url_tokens[3]
                            if url_tokens_len > 4:
                                for token in url_tokens[4:]:
                                    cmd = cmd + " " + token
                            node_list[node].write(cmd)
                            self.ok200(node + " " + cmd)
                        else:
                            self.error404("No command for node: " + node)
                    elif node == "assistant":
                        if url_tokens_len > 3:
                            cmd = url_tokens[3]
                            if cmd == "say":
                                if url_tokens_len > 4:
                                    msg = ""
                                    for word in url_tokens[4:]:
                                        msg += word + " "
                                    lbsay(msg)
                                    self.ok200("Assistant said: " + msg)
                                else:
                                    self.error404("Bad length for command '" + cmd + "'")
                            elif cmd == "wifi":
                                if url_tokens_len == 6:
                                    if url_tokens[5] == "set":
                                        if url_tokens[4] == "off":
                                            wifiOff(silent=True)
                                            self.ok200("wifi off set")
                                        elif url_tokens[4] == "on":
                                            wifiOn(silent=True)
                                            self.ok200("wifi on set")
                                        else:
                                            self.error404("Bad sub-command in commend '" + cmd + "'")
                                    else:
                                        self.error404("Bad end-command for '" + cmd + "'")
                                else:
                                    self.error404("Bad length for command '" + cmd + "'")
                            elif cmd == "json":
                                temp_json = dict()
                                temp_json['system_status'] = system_status
                                temp_json['notification_is_on'] = notification_is_on
                                temp_json['schedule_watering'] = schedule_watering
                                temp_json['HTTPD_PORT'] = HTTPD_PORT
                                temp_json['wifi_is_on'] = wifi_is_on
                                temp_json['temperature'] = round(acq["beetleTemp"]["tempSensors"]["424545544C455445"]["val"], 1)
                                self.ok200(json.dumps(temp_json, sort_keys=True, indent=4), content_type="application/json")
                            elif cmd == "acq":
                                try:
                                    token_nbs = range(4, url_tokens_len)
                                    node_point = acq
                                    for token_index in token_nbs:
                                        node_point = node_point[url_tokens[token_index]]
                                    self.ok200(json.dumps(node_point, sort_keys=True, indent=4), content_type="application/json")
                                except:
                                    self.error404("Bad path in 'acq'")
                            else:
                                self.error404("Bad command '" + cmd + "' for node '" + node + "'")
                        else:
                            self.error404("Bad length in node '" + node + "'")
                    else:
                        self.error404("Bad node: " + node)
                else:
                    self.error404("Command too short: " + api)
            else:
                self.error404("Bad location: " + api)
        else:
            self.error404("Url too short")


http_server = http.server.ThreadingHTTPServer(("", HTTPD_PORT), CustomHandler)

def http_thread():
    global http_server
    log("Serving at port " + str(HTTPD_PORT))
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        exit()


def main():
    global node_list
    logging.basicConfig(level=logging.INFO)
    credentials = auth_helpers.get_assistant_credentials()
    with Board() as board, Assistant(credentials) as assistant:
        schedule.every().day.at("00:59").do(schedule_wifiOff)
        schedule.every().day.at("01:00").do(schedule_waterMainOn)
        schedule.every().day.at("01:01").do(schedule_waterSideOn)
        schedule.every().day.at("01:15").do(schedule_waterSideOff)
        schedule.every().day.at("01:16").do(schedule_waterEastOn)
        schedule.every().day.at("01:30").do(schedule_waterEastOff)
        schedule.every().day.at("01:31").do(schedule_waterWestOn)
        schedule.every().day.at("01:45").do(schedule_waterWestOff)
        schedule.every().day.at("01:46").do(schedule_waterSouthOn)
        schedule.every().day.at("02:00").do(schedule_waterSouthOff)
        schedule.every().day.at("02:01").do(schedule_waterMainOff)
        #schedule.every().day.at("07:30").do(sayWeather, assistant)
        #schedule.every().day.at("07:45").do(sayWorkPath, assistant)
        schedule.every(15).minutes.do(checkSystem, assistant)
        schedule_thread_worker = threading.Thread(target=schedule_thread, args=(schedule,))
        schedule_thread_worker.start()
        http_thread_worker = threading.Thread(target=http_thread, args=())
        http_thread_worker.start()
        for key, value in node_list.items():
            value.start()
        checkSystem(assistant)
        for event in assistant.start():
            process_event(assistant, board.led, event)


if __name__ == '__main__':
    main()
