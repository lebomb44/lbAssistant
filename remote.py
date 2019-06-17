#!/usr/bin/env python3


import subprocess
import requests


def checkdisk(target, target_name, user, path, level=80):
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
                if int(resp_array[13].replace("%","")) < level:
                    return ""
        print("ERROR checkdisk(target=" + target + " ,target_name=" + target_name + " ,user=" + user + " ,path=" + path + " ,level=" + str(level) + ")")
        print("LOG result=" + str(result))
        raise ValueError("Bad SSH call")
    except:
        return "Disque plein sur " + target_name

def checkhttp(url, url_name, answer):
    try:
        r = requests.get("http://" + url, timeout=0.1)
        if 200 == r.status_code:
            if answer == r.text:
                return ""
        raise ValueError("Cannot access URL")
    except:
        return "Le serveur " + url_name + " est inaccessible"
