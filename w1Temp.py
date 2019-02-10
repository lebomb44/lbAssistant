#!/usr/bin/env python3


import subprocess

def read_temp():
    try:
        device_file = "/sys/bus/w1/devices/28-00000756ca6d/w1_slave"
        catdata = subprocess.Popen(['cat',device_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = catdata.communicate()
        out_decode = out.decode('utf-8')
        lines = out_decode.split('\n')
        if 3 != len(lines):
            raise Exception("Bad number of lines")
        line0 = lines[0].split(" ")
        if "YES" != line0[11]:
            raise Exception("Bad CRC")
        line1 = lines[1].split(" ")
        temp = line1[9].split("=")[1]
        return str(round(int(temp)/1000,1))
    except Exception as e:
        return str(e)

