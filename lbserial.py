#! /usr/bin/env python3
# coding: utf-8


""" LbSerial"""


import io
import threading
import time
import fcntl
import os
import traceback

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


class Serial(threading.Thread):
    """ Class for a serial port """
    def __init__(self, name, acq):
        self.port = "/dev/" + name
        self.node_name = name
        self.fd_port = io.IOBase()
        self.error_cnt = 0
        self.error_cnt_max = 0
        self.cmd_rx_cnt = 0
        self.ping_tx_cnt = 0
        self.ping_rx_cnt = 0
        self.line = ""
        self.open_cnt = 0
        self.read_iter = 0
        self.is_loop_enabled = True
        self.MAX_NODE_ERRORS = 10000
        self.acq = acq
        threading.Thread.__init__(self, name=name)

    def run(self):
        """ Cyclic execution to poll for received characters """
        loop_nb = 1
        while self.is_loop_enabled is True:
            try:
                #log("DEBUG: " + self.node_name + " loop " + str(loop_nb))
                if self.is_open() is False:
                    self.open()
                    time.sleep(1.0)
                if self.is_open() is True:
                    line = ""
                    cserial = " "
                    read_iter_ = 0
                    while (len(cserial) > 0) and (self.is_loop_enabled is True):
                        try:
                            cserial = self.fd_port.read(1)
                            if cserial is None:
                                cserial = ""
                            else:
                                cserial = cserial.decode(encoding='utf-8', errors='ignore')
                            if len(cserial) > 0:
                                read_iter_ = read_iter_ + 1
                                if ord(cserial) == 0:
                                    cserial = ""
                            else:
                                cserial = ""
                            if (self.line != "") and (cserial == "\n" or cserial == "\r"):
                                line = self.line
                                self.line = ""
                                #log("DEBUG New line create=" + line)
                                break
                            else:
                                if (cserial != "\n") and (cserial != "\r"):
                                    self.line = self.line + cserial
                        except Exception as ex:
                            self.line = ""
                            cserial = ""
                            log_exception(ex, msg="ERROR while decoding data on " + self.node_name)
                            self.close()
                    if read_iter_ > self.read_iter:
                        self.read_iter = read_iter_
                    if line != "":
                        line_array = line.split(" ")
                        # log("DEBUG: line_array=" + str(line_array))
                        if len(line_array) > 2:
                            node = line_array[0]
                            cmd = line_array[1]
                            if node in self.acq:
                                if cmd in self.acq[node]:
                                    arg_map = line_array[2:]
                                    if 'fct' in self.acq[node][cmd]:
                                        try:
                                            fct_to_run = getattr(self, self.acq[node][cmd]['fct'])
                                            fct_to_run(node, cmd, arg_map)
                                        except Exception as ex:
                                            log_exception(ex)
                                    else:
                                        if len(arg_map) == 2:
                                            if arg_map[0] in self.acq[node][cmd]:
                                                self.acq[node][cmd][arg_map[0]] = type(self.acq[node][cmd][arg_map[0]])(arg_map[1])
                                                if 'fct_after_set' in self.acq[node][cmd]:
                                                    try:
                                                        fct_to_run = getattr(self, self.acq[node][cmd]['fct'])
                                                        fct_to_run(node, cmd, arg_map)
                                                    except Exception as ex:
                                                        log_exception(ex)
                                            else:
                                                log("ERROR: " + arg_map[0] + " is not in cmd " + node + "." + cmd)
                                        else:
                                            if len(arg_map) == 3:
                                                if arg_map[0] in self.acq[node][cmd]:
                                                    if arg_map[1] in self.acq[node][cmd][arg_map[0]]:
                                                        self.acq[node][cmd][arg_map[0]][arg_map[1]] = type(self.acq[node][cmd][arg_map[0]][arg_map[1]])(arg_map[2])
                                                        if 'fct' in self.acq[node][cmd]:
                                                            try:
                                                                fct_to_run = getattr(self, self.acq[node][cmd]['fct'])
                                                                fct_to_run(node, cmd, arg_map)
                                                            except Exception as ex:
                                                                log_exception(ex)
                                                    else:
                                                        log("ERROR: " + arg_map[1] + " is not in cmd " + node + "." + cmd + "." + arg_map[0])
                                                else:
                                                    log("ERROR: " + arg_map[0] + " is not in cmd " + node + "." + cmd)
                                            else:
                                                log("ERROR: incorrect number of arguments in '" + str(arg_map) + "'. Got " + str(len(arg_map)) + ", expected 2")
                                    self.cmd_rx_cnt += 1
                                else:
                                    log("ERROR: " + cmd + " is not in node " + node)
                            else:
                                log("ERROR: node '" + node + "' is unknown")
                        else:
                            log("ERROR: line '" + line + "' is too short")
            except Exception as ex:
                log_exception(ex)
                self.close()
            self.timeout_check()
            loop_nb += 1
            if loop_nb >= 1000000:
                loop_nb = 0
            time.sleep(0.001)


    def stop(self):
        """ Stop polling loop """
        log("Stopping " + self.node_name + " thread...")
        self.is_loop_enabled = False
        time.sleep(1.0)
        log("Closing " + self.node_name + " node...")
        if self.is_open() is True:
            self.fd_port.close()

    def is_open(self):
        """ Check if serial port is already open """
        try:
            ret = fcntl.fcntl(self.fd_port, fcntl.F_GETFD)
            return ret >= 0
        except:
            return False


    def open(self):
        """ Open the serial port """
        try:
            log("Opening " + self.node_name)
            self.fd_port = open(self.port, "rb+", buffering=0)
            fd_port = self.fd_port.fileno()
            flag = fcntl.fcntl(fd_port, fcntl.F_GETFL)
            fcntl.fcntl(fd_port, fcntl.F_SETFL, flag | os.O_NONBLOCK)
            self.open_cnt += 1
        except Exception as ex:
            log_exception(ex)


    def close(self):
        """ Close the serial port """
        try:
            if self.is_open() is True:
                log("Closing " + self.node_name)
                self.fd_port.close()
        except Exception as ex:
            log_exception(ex)


    def write(self, msg):
        """ Write the serial port if already open """
        try:
            if self.is_open() is True:
                self.fd_port.write((self.node_name + " " + msg + "\n").encode('utf-8'))
                # log("Write serial to node " + self.node_name)
                self.fd_port.flush()
        except Exception as ex:
            log("ERROR write_serial Exception: " + str(ex))


    def timeout_check(self):
        """ Check timeout to increment """
        if self.MAX_NODE_ERRORS > self.error_cnt:
            self.error_cnt += 1
        if self.MAX_NODE_ERRORS == self.error_cnt:
            log("Timeout on serial node " + self.node_name)
            self.error_cnt += 1
            self.close()
            time.sleep(1.0)
            self.open()


    def timeout_reset(self, node_, cmd_, arg_array_):
        """ Reset timeout to zero """
        #log("### Reset of " + node_ + " timeout")
        if self.error_cnt > self.error_cnt_max:
            self.error_cnt_max = self.error_cnt
        self.error_cnt = 0
        self.ping_rx_cnt += 1

