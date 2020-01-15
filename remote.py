#!/usr/bin/env python3


""" Check remote ressoures """

import subprocess
import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def checkdisk(target, target_name, user, path, level=80):
    """ Check disk usage on remote """
    try:
        result = subprocess.run(["ssh", user + "@" + target, "df -h " + path],
                                shell=False,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False,
                                timeout=1.0)
        if result.returncode == 0:
            resp_array = result.stdout.decode('utf-8').split()
            if len(resp_array) == 15:
                rate = int(resp_array[13].replace("%", ""))
                if rate < level:
                    return ""
                else:
                    return "Disque plein a " + str(rate) + "% sur " + target_name
            else:
                return "Longueur incorrecte a " + str(len(resp_array)) + " pour le test disque sur " + target_name
        else:
            return "Code retour incorrect a " + str(int(result.returncode)) + " pour le test disque sur " + target_name
    except Exception as ex:
        print("ERROR: Exception checkdisk: " + str(ex))
        return "Exception lors du test disque sur " + target_name

def checkhttp(url, url_name, answer):
    """ Check correct execution of HTTP request """
    try:
        req = requests.get(url, timeout=0.1, verify=False)
        if req.status_code == 200:
            if answer == req.text:
                return ""
            else:
                return "Reponse incorrecte a " + req.text + " pour le test d'acces sur " + url_name
        else:
            return "Code retour incorrect a " + str(req.status_code) + " pour le test d'acces sur " + url_name
    except Exception as ex:
        print("ERROR: Exception checkhttp: " + str(ex))
        return "Exception lors du test d'acces sur " + url_name
